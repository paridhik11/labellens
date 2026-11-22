# ruff: noqa: E501  (report table lines)
"""Score the live DailyMed lookup once on the fixed set (protocol: reports/live_dailymed_protocol.md).

    python scripts/live_dailymed_eval.py --out results/live_dailymed

Runs the same code as the API (local matcher, search, fetch, index, extractive answer, citation checks) for every
item of data/eval/live_dailymed_set.json. Uses the real network (DailyMed) and the real E5b models. Run once.
Writes <out>.jsonl (one row per item) and <out>.md (the table and the gate decision).
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import statistics
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.live_dailymed import LiveService, unverified_sources  # noqa: E402
from src.api.medicine import MedicineService  # noqa: E402
from src.common.schemas import Chunk  # noqa: E402
from src.rag.provider import NullProvider  # noqa: E402
from src.rag.settings import RagSettings  # noqa: E402


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def pct(k: int, n: int) -> str:
    """'k/n (xx%, Wilson 95% lo to hi)'."""
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%, Wilson 95% {100 * lo:.0f} to {100 * hi:.0f}%)" if n else "0/0"


def independent_citation_check(body: dict, label, picked_setid: str) -> list[str]:
    """Citation problems found without the service's own helper: id belongs to the label, quote verbatim, set id matches."""
    problems = []
    by_id = {c.chunk_id: c for c in label.chunks}
    if body.get("live", {}).get("setid") != picked_setid or ("based_on" in body and picked_setid not in body["based_on"]):
        problems.append("answer does not name the picked set id")
    for src in body.get("sources", []):
        chunk: Chunk | None = by_id.get(src["chunk_id"])
        if chunk is None:
            problems.append(f"{src['chunk_id']} not in the picked label")
        elif src["quote"] not in chunk.text:
            problems.append(f"{src['chunk_id']} quote not verbatim")
        elif picked_setid not in src["chunk_id"]:
            problems.append(f"{src['chunk_id']} is from another set id")
    return problems


def main() -> int:
    """Run the fixed set once and write the table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", type=Path, default=ROOT / "data/eval/live_dailymed_set.json")
    ap.add_argument("--out", type=Path, default=ROOT / "results/live_dailymed")
    ap.add_argument("--cache", type=Path, default=ROOT / "data/api/live_dailymed_eval")
    args = ap.parse_args()
    spec = json.loads(args.set.read_text(encoding="utf-8"))
    if args.cache.exists():
        shutil.rmtree(args.cache)  # cold cache: every fetch is a real download
    live = LiveService(cache_dir=args.cache)
    medicine = MedicineService()
    settings = RagSettings()
    print("warm-up: loading the matcher and the E5b models (not timed)", flush=True)
    medicine.matcher.match("warm up")
    live._factory(  # noqa: SLF001  build once so the model load is not in the first fetch time
        [Chunk(chunk_id="w1", source="x", title="t", section="s", text="warm up text for the model", module="medicine")])
    rows = []
    for item in spec["items"]:
        name = item["typed_name"]
        row: dict = {"id": item["id"], "kind": item["kind"], "class": item["class"], "typed_name": name}
        local = medicine.matcher.match(name)
        row["local_outcome"] = local["outcome"]
        row["local_score"] = local["score"]
        row["local_false_accept"] = local["outcome"] == "matched"
        search = live.search(name)
        row["search_outcome"] = search["outcome"]
        row["n_candidates"] = len(search.get("candidates", []))
        row["total_matches"] = search.get("total_matches")
        row["reason"] = search.get("reason")
        if item["kind"] == "decoy":
            row["rejected"] = search["outcome"] == "no_candidates" and not row["local_false_accept"]
            row["wrong_product_shown"] = row["local_false_accept"]
            rows.append(row)
            print(item["id"], name, "decoy ->", search["outcome"], "local", local["outcome"], flush=True)
            continue
        token = item["expected_ingredient"].lower()
        picked = next((c for c in search.get("candidates", []) if token in c["title"].lower()), None)
        row["found"] = picked is not None
        row["picked_title"] = picked["title"] if picked else None
        row["wrong_product_shown"] = row["local_false_accept"]
        row.update({"fetched": False, "answered": False, "citations_verified": None})
        if picked:
            t0 = time.perf_counter()
            try:
                label = live.fetch(picked["setid"], picked["version"])
                row["fetch_s"] = round(time.perf_counter() - t0, 2)
                row["fetched"] = True
                ident = f"{label.name} {picked['title']} {' '.join(label.active_ingredients)}".lower()
                row["label_has_expected_ingredient"] = token in ident
                if not row["label_has_expected_ingredient"]:
                    row["wrong_product_shown"] = True
                answers, problems, first_s = [], [], None
                for template in spec["questions"]:
                    q = template.format(name=name)
                    result, loaded = live.ask(q, label.product_id, NullProvider(), settings)
                    body = live.wire(result, loaded)
                    if first_s is None:
                        first_s = round(time.perf_counter() - t0, 2)
                    problems += independent_citation_check(body, loaded, picked["setid"])
                    problems += unverified_sources(body.get("sources", []), loaded)
                    answers.append({"q": q, "abstained": body["abstained"], "n_sources": len(body.get("sources", []))})
                row["fetch_to_answer_s"] = first_s
                row["answers"] = answers
                row["answered"] = any(a["n_sources"] >= 1 for a in answers)  # passages shown with a citation
                row["citation_problems"] = problems
                row["citations_verified"] = not problems
            except Exception as error:  # a failure is a result: report it, do not retry
                row["error"] = f"{type(error).__name__}: {error}"
        rows.append(row)
        print(item["id"], name, "found" if picked else "NOT FOUND", row.get("fetch_to_answer_s"), row.get("error", ""), flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    products = [r for r in rows if r["kind"] == "product"]
    decoys = [r for r in rows if r["kind"] == "decoy"]
    n = len(products)
    found = sum(r["found"] for r in products)
    fetched = sum(r["fetched"] for r in products)
    answered = sum(r["answered"] for r in products)
    wrong = sum(r["wrong_product_shown"] for r in rows)
    bad_cites = sum(1 for r in products if r.get("citations_verified") is False)
    cites_checked = sum(1 for r in products if r.get("citations_verified") is not None)
    rejected = sum(r["rejected"] for r in decoys)
    times = [r["fetch_to_answer_s"] for r in products if "fetch_to_answer_s" in r]
    g1, g2, g3 = wrong == 0, bad_cites == 0, rejected == len(decoys)
    lines = [
        "# Live DailyMed lookup: fresh-set result (scored once)", "",
        f"Run date {date.today().isoformat()}. Protocol: `reports/live_dailymed_protocol.md` (committed before scoring). "
        "Other jobs (a docs session and a scan re-run) were running on this machine, so the timings are not clean.", "",
        "| Measure | Result |", "|---|---|",
        f"| Right label in the candidate list (found) | {pct(found, n)} |",
        f"| Fetched, parsed and indexed | {pct(fetched, n)} |",
        f"| Answered with at least one citation | {pct(answered, n)} |",
        f"| Wrong-product answers shown as correct (all 40 queries) | {wrong} |",
        f"| Products with a citation that failed verification | {bad_cites} of {cites_checked} checked |",
        f"| Decoys rejected (empty list, no local accept) | {pct(rejected, len(decoys))} |",
        f"| Median fetch-to-answer (cold, products that were answered) | "
        f"{statistics.median(times):.1f} s (min {min(times):.1f}, max {max(times):.1f}, n={len(times)}) |" if times else
        "| Median fetch-to-answer | no product was answered |", "",
        "## Gate", "",
        f"- G1 zero wrong-product answers shown as correct: **{'PASS' if g1 else 'FAIL'}** ({wrong})",
        f"- G2 every shown citation verified: **{'PASS' if g2 else 'FAIL'}** ({bad_cites} products with a failure)",
        f"- G3 decoys rejected 10 of 10: **{'PASS' if g3 else 'FAIL'}** ({rejected}/{len(decoys)})",
        f"- G4 median fetch-to-answer reported: {'yes' if times else 'no data'}", "",
        f"**Gate decision: {'PASSED' if g1 and g2 and g3 else 'NOT PASSED'}**", "", "## Per item", "",
        "| id | typed | class | local | list | found | answered | fetch-to-answer s | note |", "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        note = r.get("error") or ("; ".join(r.get("citation_problems", [])) if r.get("citation_problems") else "")
        if r["kind"] == "decoy":
            lines.append(f"| {r['id']} | {r['typed_name']} | {r['class']} | {r['local_outcome']} | {r['search_outcome']} "
                         f"({r['n_candidates']}) | - | rejected={r['rejected']} | - | {r.get('reason') or ''} |")
        else:
            lines.append(f"| {r['id']} | {r['typed_name']} | {r['class']} | {r['local_outcome']} | {r['search_outcome']} "
                         f"({r['n_candidates']}/{r['total_matches']}) | {r['found']} | {r['answered']} | "
                         f"{r.get('fetch_to_answer_s', '')} | {note} |")
    args.out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:22]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
