"""NDC scan evaluation (protocol: results/ndc_scan/protocol.md).

    python -m scripts.ndc_scan.evaluate read positives unused_decoy new_set   # OCR cache (reading is not scoring)
    python -m scripts.ndc_scan.evaluate dev                                    # choose TAU on dev, write the config
    python -m scripts.ndc_scan.evaluate score                                  # frozen version, ONCE, all gate sets
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from scripts.public_scan.evaluate import wilson
from src.ndc.barcode import read_payloads
from src.ndc.codes import printed_ndcs
from src.ndc.package_text import load_texts, make_retriever
from src.ndc.scan import CONFIG_PATH, decide, load_config
from src.ndc.table import load_table

OUT = Path("results/ndc_scan")
OLD = Path("../labellens-publicscan")
CONFIG_E = Path("src/api/public_scan_config.json")
WORKERS = int(os.environ.get("NDC_WORKERS", "1"))
READ_TIMEOUT_S = float(os.environ.get("NDC_READ_TIMEOUT", "150"))  # generous: the reader still stops itself at 44 s
GRID = [float(x) for x in range(0, 42, 2)]


def photos_of(name: str) -> list[dict[str, Any]]:
    """Photo records of one gate set: id, path, role, condition, product, setid, expected product name."""
    if name == "positives":
        data = json.loads(Path("results/public_scan/photos_v2.json").read_text("utf-8"))["photos"]
        rows = [p for p in data if p["set"] == "fresh_real" and p["role"] == "positive"]
        base = OLD
    elif name == "unused_decoy":
        rows = json.loads(Path("results/public_scan/photos_v4.json").read_text("utf-8"))["photos"]
        base = OLD
    elif name == "new_set":
        rows = json.loads((OUT / "new_set.json").read_text("utf-8"))["photos"]
        base = Path(".")
    elif name == "dev":
        data = json.loads(Path("results/public_scan/photos_v2.json").read_text("utf-8"))["photos"]
        rows = [p for p in data if p["set"] == "dev_real"]
        base = OLD
    else:
        raise SystemExit(f"unknown set {name}")
    return [{"id": p["id"], "set": name, "path": str(base / p["file"]), "role": p["role"], "condition": p["condition"],
             "product": p["product_name"], "setid": p["setid"], "expected_setid": p["setid"] if p["role"] == "positive"
             else None} for p in rows]


def cmd_read(names: list[str]) -> None:
    """OCR every photo once with the unchanged reader (3 at a time), append lines to lines_<set>.jsonl."""
    from src.api import public_scan

    lock = threading.Lock()
    for name in names:
        target = OUT / f"lines_{name}.jsonl"
        done = {json.loads(r)["id"] for r in target.read_text("utf-8").splitlines()} if target.exists() else set()
        todo = [p for p in photos_of(name) if p["id"] not in done]

        def one(item: dict[str, Any], target: Path = target, name: str = name) -> None:
            started = time.monotonic()
            reading = public_scan.read_lines(Path(item["path"]), timeout_s=READ_TIMEOUT_S)
            row = {**item, "lines": reading["lines"], "complete": reading["complete"], "killed": reading["killed"],
                   "ocr_seconds": round(time.monotonic() - started, 2)}
            with lock, target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
            print(name, item["id"], len(row["lines"]), row["ocr_seconds"], flush=True)

        with ThreadPoolExecutor(WORKERS) as pool:
            list(pool.map(one, todo))


class Engine:
    """Everything one scoring pass needs: table, BM25 text ranking, method E replay."""

    def __init__(self, with_e: bool = True) -> None:
        self.table = load_table()
        self.texts = load_texts()
        self.bm25 = make_retriever(self.texts)
        self.name_of = {s: v["name"] for s, v in self.texts.items()}
        self.service = None
        if with_e:
            from src.api import medicine, public_scan

            self.public_scan = public_scan
            self.service = medicine.MedicineService()
            self.service.matcher.match("warm up")
            public_scan.memoise_queries(self.service.matcher)
            self.config_e = public_scan.load_config()
            self.inputs = public_scan.scan_inputs(self.service.catalog, self.config_e)

    def text_rank(self, text: str) -> list[tuple[str, float]]:
        """BM25 ranking of all 30 products for all OCR tokens (the whole OCR text is the query)."""
        return [(h.doc_id, round(h.score, 3)) for h in self.bm25.search(text, k=len(self.texts)) if h.score > 0]

    def run_e(self, row: dict[str, Any]) -> dict[str, Any]:
        """Method E replayed on the cached lines: outcome, reason, set ids, seconds spent matching."""
        started = time.monotonic()
        result = self.public_scan.identify(
            row["lines"], self.service.matcher.match, self.inputs.vocab, self.config_e, start=time.monotonic(),
            cut_short=not row["complete"], distinct=self.inputs.distinct, other=self.inputs.other)
        cands = result["best"]["found"]["candidates"] if result["best"] else []
        setids = [self.service.catalog.products[pid].setid for pid, _ in cands]
        return {"outcome": result["outcome"], "reason": result["reason"], "setids": setids,
                "match_seconds": round(time.monotonic() - started, 2)}


def category(outcome: str, reason: str | None, setids: list[str], expected: str | None) -> str:
    """correct, wrong, review, not_identified or timeout (as in the public scan)."""
    if outcome == "no_reference_match":
        return "timeout" if reason == "timeout" else "not_identified"
    if outcome == "matched":
        return "correct" if expected is not None and setids and setids[0] == expected else "wrong"
    return "review"


def score_row(engine: Engine, row: dict[str, Any], config: Any, barcodes: list[dict[str, Any]] | None = None,
              barcode_seconds: float | None = None) -> dict[str, Any]:
    """New method and E replay on one photo (cached OCR lines, barcode read live unless given)."""
    if barcodes is None:
        started = time.monotonic()
        barcodes = read_payloads(Path(row["path"]))
        barcode_seconds = time.monotonic() - started
    text = " ".join(x["text"] for x in row["lines"])
    ndcs = [c for b in barcodes for c in b["ndcs"]]
    e_cache: dict[str, Any] = {}

    def run_e() -> dict[str, Any]:
        e_cache.update(engine.run_e(row))
        return e_cache

    out = decide(ndcs, text, engine.table, engine.text_rank(text), run_e, config)
    if not e_cache:
        e_cache.update(engine.run_e(row))  # the E baseline needs its own result on every photo
    e = {**e_cache}
    e_cat = category(e["outcome"], e["reason"], e["setids"], row["expected_setid"])
    decided_by_ndc = out["source"].startswith("ndc")
    if out["source"] == "ndc_barcode":
        new_seconds = barcode_seconds or 0.0
    elif decided_by_ndc:
        new_seconds = (barcode_seconds or 0.0) + row["ocr_seconds"]
    else:
        new_seconds = (barcode_seconds or 0.0) + row["ocr_seconds"] + e["match_seconds"]
    reason = e.get("reason") if out["source"] in ("e", "e_none") else None
    new_cat = category(out["outcome"], reason, out["setids"], row["expected_setid"])
    printed = printed_ndcs(text)
    return {"id": row["id"], "set": row["set"], "role": row["role"], "condition": row["condition"],
            "product": row["product"], "setid": row["setid"], "expected_setid": row["expected_setid"],
            "barcode_payloads": [b["payload"] for b in barcodes], "barcode_ndcs": ndcs,
            "barcode_in_table": [c for c in ndcs if c in engine.table],
            "printed_ndc_shaped": bool(printed), "printed_in_table": [c for c in printed if c in engine.table],
            "ocr_complete": row["complete"], "ocr_seconds": row["ocr_seconds"],
            "new": {"outcome": out["outcome"], "source": out["source"], "setids": out["setids"], "category": new_cat,
                    "seconds": round(new_seconds, 1)},
            "e": {"outcome": e["outcome"], "setids": e["setids"], "category": e_cat,
                  "seconds": round(row["ocr_seconds"] + e["match_seconds"], 1)},
            "text_top": engine.text_rank(text)[:3]}


def cmd_dev() -> None:
    """Choose TAU on the dev photos only (cached lines, cached E outcomes), print dev numbers, write the config."""
    engine = Engine(with_e=False)
    tuned = json.loads(Path("results/public_scan/dev_configs.json").read_text("utf-8"))
    dev_e = {r["id"]: r for r in tuned["E"]["rows"]}
    rows = [json.loads(r) for r in Path("results/public_scan/lines_dev_real.jsonl").read_text("utf-8").splitlines()]
    scored = []
    for row in rows:
        e = dev_e[row["id"]]
        text = " ".join(x["text"] for x in row["lines"])
        rank = engine.text_rank(text)
        photo = OLD / "data" / "public_scan_real" / "photos" / "dev_real" / Path(row["path"]).name
        started = time.monotonic()
        barcodes = read_payloads(photo)
        scored.append({"id": row["id"], "kind": row["kind"], "condition": row["condition"], "e_cat": e["category"],
                       "top_score": rank[0][1] if rank else 0.0,
                       "top_name": engine.name_of.get(rank[0][0]) if rank else "",
                       "expected": row["expected"], "text": text, "ndcs": [c for b in barcodes for c in b["ndcs"]],
                       "barcode_seconds": time.monotonic() - started})
    pool = [s for s in scored if s["e_cat"] == "not_identified" and not any(
        c in engine.table for c in s["ndcs"]) and not any(c in engine.table for c in printed_ndcs(s["text"]))]
    chosen = None
    for tau in GRID:
        if not any(s["kind"] == "decoy" and s["top_score"] >= tau for s in pool):
            chosen = tau
            break
    print("dev photos E not_identified without NDC:", len(pool), "decoys among them:",
          sum(s["kind"] == "decoy" for s in pool))
    for tau in GRID[::5]:
        hit = [s for s in pool if s["top_score"] >= tau]
        print(f"tau {tau}: suggestions {len(hit)} (decoy {sum(s['kind'] == 'decoy' for s in hit)}, positive-correct "
              f"{sum(s['kind'] == 'positive' and s['top_name'] == s['expected'] for s in hit)})")
    print("chosen tau:", chosen)
    pos = [s for s in scored if s["kind"] == "positive"]
    ndc_hit = [s for s in pos if any(c in engine.table for c in s["ndcs"] + printed_ndcs(s["text"]))]
    e_correct = sum(s["e_cat"] == "correct" for s in pos)
    both = sum(s["e_cat"] == "correct" or s in ndc_hit for s in pos)
    print(f"dev positives {len(pos)}: E correct {e_correct}, NDC decides {len(ndc_hit)}, either {both}")
    CONFIG_PATH.write_text(json.dumps({"tau": chosen, "top": 3}) + "\n", encoding="utf-8")
    (OUT / "dev_selection.json").write_text(json.dumps(
        {"grid": GRID, "chosen_tau": chosen, "pool_size": len(pool),
         "rows": [{k: v for k, v in s.items() if k != "text"} for s in scored]}, indent=1), encoding="utf-8")


def summarise(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Counts, Wilson intervals, latency and timeouts of one method (key "new" or "e") over rows."""
    n = len(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r[key]["category"]] = counts.get(r[key]["category"], 0) + 1
    seconds = sorted(r[key]["seconds"] for r in rows)
    out: dict[str, Any] = {"photos": n, "counts": counts}
    if n:
        k = counts.get("correct", 0)
        out["correct_interval"] = wilson(k, n)
        out["wrong_interval"] = wilson(counts.get("wrong", 0), n)
        out["seconds"] = {"median": round(statistics.median(seconds), 1), "max": round(seconds[-1], 1)}
    return out


def by_condition(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """summarise() per condition."""
    return {c: summarise([r for r in rows if r["condition"] == c], key) for c in ("artwork", "moderate", "hard")}


def per_product(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One line per product: photos, new and E categories, product-level wrong."""
    out = []
    for product in sorted({r["product"] for r in rows}):
        group = [r for r in rows if r["product"] == product]
        def cats(key: str, group: list[dict[str, Any]] = group) -> list[str]:
            return [r[key]["category"] for r in group]

        out.append({"product": product, "role": group[0]["role"], "photos": len(group), "new": cats("new"),
                    "e": cats("e"), "new_wrong": "wrong" in cats("new"), "e_wrong": "wrong" in cats("e"),
                    "sources": [r["new"]["source"] for r in group]})
    return out


def cmd_score() -> None:
    """The frozen version on the gate photos, once. Refuses an uncommitted config or an existing output."""
    committed = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(CONFIG_PATH)], capture_output=True,
                               text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", str(CONFIG_PATH), "src/ndc"], capture_output=True,
                           text=True).stdout.strip()
    if not committed or dirty:
        raise SystemExit("the frozen config and src/ndc must be committed before the final run")
    target = OUT / "final_rows.jsonl"
    if target.exists():
        raise SystemExit(f"{target} exists: the frozen version is scored once")
    config = load_config()
    engine = Engine()
    rows: list[dict[str, Any]] = []
    with target.open("x", encoding="utf-8") as handle:
        for name in ("positives", "unused_decoy", "new_set"):
            seen: set[str] = set()
            for line in (OUT / f"lines_{name}.jsonl").read_text("utf-8").splitlines():
                cached = json.loads(line)
                if cached["id"] in seen:  # two readers may have read the same photo: the first reading counts
                    continue
                seen.add(cached["id"])
                result = score_row(engine, cached, config)
                rows.append(result)
                handle.write(json.dumps(result) + "\n")
                handle.flush()
                print(name, result["id"], result["new"]["category"], result["e"]["category"], flush=True)
    summary = build_summary(rows, committed, config.__dict__)
    (OUT / "final_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary["gate"], indent=1))


def build_summary(rows: list[dict[str, Any]], commit: str, config: dict[str, Any]) -> dict[str, Any]:
    """Summaries, coverage, per-product table and the three gate checks."""
    pos = [r for r in rows if r["set"] == "positives"]
    unused = [r for r in rows if r["set"] == "unused_decoy"]
    new = [r for r in rows if r["set"] == "new_set"]
    decoys = unused + new

    def coverage(group: list[dict[str, Any]]) -> dict[str, Any]:
        n = len(group)
        return {"photos": n, "barcode_ndc_read": sum(bool(r["barcode_ndcs"]) for r in group),
                "barcode_in_table": sum(bool(r["barcode_in_table"]) for r in group),
                "printed_ndc_shaped": sum(r["printed_ndc_shaped"] for r in group),
                "printed_in_table": sum(bool(r["printed_in_table"]) for r in group),
                "either_in_table": sum(bool(r["barcode_in_table"] or r["printed_in_table"]) for r in group),
                "ndc_decided": sum(r["new"]["source"].startswith("ndc") for r in group)}

    def product_wrong(group: list[dict[str, Any]], key: str) -> int:
        return len({r["product"] for r in group if r[key]["category"] == "wrong"})

    def any_shown(group: list[dict[str, Any]], key: str) -> int:
        return sum(bool(r[key]["setids"]) for r in group)

    e_timeouts_recorded = 13
    timeouts = lambda g, k: sum(r[k]["category"] == "timeout" for r in g)  # noqa: E731
    gate = {
        "1_wrong_products_unused_decoys_new_method": product_wrong(decoys, "new"),
        "1_wrong_products_unused_decoys_E_replay": product_wrong(decoys, "e"),
        "1_decoy_products": len({r["product"] for r in decoys}),
        "1_decoy_photos_with_any_product_shown_new": any_shown(decoys, "new"),
        "1_decoy_photos_with_any_product_shown_E": any_shown(decoys, "e"),
        "2_timeouts_unused_new": timeouts(unused, "new"), "2_timeouts_unused_E_replay": timeouts(unused, "e"),
        "2_timeouts_unused_E_recorded": e_timeouts_recorded,
        "2_timeouts_positives_new": timeouts(pos, "new"), "2_timeouts_positives_E_replay": timeouts(pos, "e"),
        "3_correct_positives_new": sum(r["new"]["category"] == "correct" for r in pos),
        "3_correct_positives_E_replay": sum(r["e"]["category"] == "correct" for r in pos),
        "3_positive_photos": len(pos)}
    gate["pass_1"] = gate["1_wrong_products_unused_decoys_new_method"] == 0
    gate["pass_2"] = (gate["2_timeouts_unused_new"] <= min(gate["2_timeouts_unused_E_replay"], e_timeouts_recorded)
                      and gate["2_timeouts_positives_new"] <= gate["2_timeouts_positives_E_replay"])
    gate["pass_3"] = gate["3_correct_positives_new"] > gate["3_correct_positives_E_replay"]
    gate["pass_all"] = gate["pass_1"] and gate["pass_2"] and gate["pass_3"]
    sets = {"positives": pos, "unused_decoy": unused, "new_set": new, "all_decoys": decoys}
    return {"config_commit": commit, "config": config, "gate": gate,
            "coverage": {k: coverage(v) for k, v in sets.items()} | {
                f"positives/{c}": coverage([r for r in pos if r["condition"] == c])
                for c in ("artwork", "moderate", "hard")},
            "new": {k: summarise(v, "new") for k, v in sets.items()},
            "e_replay": {k: summarise(v, "e") for k, v in sets.items()},
            "new_by_condition": {k: by_condition(v, "new") for k, v in sets.items()},
            "e_by_condition": {k: by_condition(v, "e") for k, v in sets.items()},
            "per_product": per_product(rows)}


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "read":
        cmd_read(sys.argv[2:])
    elif command == "dev":
        cmd_dev()
    elif command == "score":
        cmd_score()
    else:
        raise SystemExit(__doc__)
