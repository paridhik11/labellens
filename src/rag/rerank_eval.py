"""Rerank evaluation (reports/rag_rerank_plan.md). Commands: dev-run, units, record, tune, run, report.

Relevance grades are LLM grades in a separate file, never human grades. T is tuned on the dev half only and frozen
in data/rag/rag_rerank_config.json (committed) before the held-out run. Each system is run once on the held-out half.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import random
import statistics
from pathlib import Path
from typing import Any

from src.rag import rerank
from src.rag.evaluate import fmt, pct
from src.rag.provider import NullProvider
from src.rag.service import RagService, frozen_threshold
from src.rag.settings import RagSettings

ROOT = Path(__file__).resolve().parents[2]
QUERIES = ROOT / "data" / "eval" / "fresh_rag_rerank.tsv"
SPLIT = ROOT / "data" / "eval" / "split_rag_rerank.json"
CONFIG = ROOT / "data" / "rag" / "rag_rerank_config.json"
RESULTS = ROOT / "results"
GRADES = RESULTS / "rag_rerank_grades_llm.csv"
GRID = list(range(-10, 9))
MAX_WRONG_DEV = 0.20
GATE = {"median_s_lt": 3.0, "wrong_le": 0.20}
SYSTEMS = ("extractive", "rerank")


def sha(path: Path) -> str:
    """sha256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_queries(half: str) -> list[dict[str, Any]]:
    """Queries of one half ('dev' or 'heldout'): qid, text, module, answerable."""
    split = json.loads(SPLIT.read_text(encoding="utf8"))
    with open(QUERIES, encoding="utf8", newline="") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t") if r and r[0] != "qid"]
    return [{"qid": r[0], "text": r[1], "module": r[2], "answerable": r[3] == "1"} for r in rows
            if split[r[0]] == half]


def run_path(name: str) -> Path:
    """Run file: 'dev' (rerank, no threshold) or a system name (held-out)."""
    return RESULTS / f"rag_rerank_run_{name}.jsonl"


def make_service(system: str, threshold: float | None) -> RagService:
    """Service for one system. Both use the frozen E5b retrieval and gate, no language model."""
    if system == "extractive":
        settings = RagSettings(rerank_display=False)  # the old display, as in the frozen comparison
    else:
        settings = RagSettings(output="rerank", rerank_threshold=threshold)
    return RagService(provider=NullProvider(), settings=settings, threshold=frozen_threshold())


def execute(name: str, system: str, half: str, threshold: float | None, force: bool) -> None:
    """Run every query of a half through one system once, writing its run file."""
    out = run_path(name)
    if out.exists() and not force:
        raise SystemExit(f"{out} exists; each run happens once (--force only after a crash)")
    service = make_service(system, threshold)
    service.ask("What must the principal display panel show?", "device")  # warm-up, not scored
    RESULTS.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf8") as fh:
        for q in load_queries(half):
            r = service.ask(q["text"], q["module"])
            fh.write(json.dumps({**q, "system": system, **dataclasses.asdict(r)}) + "\n")
            fh.flush()
            print(q["qid"], r.outcome, r.cause, r.latency_s, flush=True)


def read_run(name: str) -> list[dict[str, Any]]:
    """Rows of one finished run."""
    return [json.loads(line) for line in open(run_path(name), encoding="utf8")]


def shown_units(row: dict[str, Any]) -> list[str]:
    """What the user sees: quotes for extractive, answer sentences for rerank. Dev rows: the stored top 3."""
    if row.get("system") == "extractive":
        return [s["quote"] for s in row["sources"]]
    if row["outcome"] != "answered":
        return []
    return [s["text"] for s in row["sentences"]]


def rel_key(qid: str, text: str) -> str:
    """Relevance unit id: identical text for one query is graded once."""
    return f"{qid}:{hashlib.sha1(text.encode()).hexdigest()[:8]}"


def rel_units() -> list[dict[str, str]]:
    """Distinct (query, text) units of answerable queries over all finished runs, shuffled with seed 42."""
    seen: dict[str, dict[str, str]] = {}
    for name in ("dev", *SYSTEMS):
        if not run_path(name).exists():
            continue
        for row in read_run(name):
            if row["answerable"]:
                for t in shown_units(row):
                    seen.setdefault(rel_key(row["qid"], t),
                                    {"key": rel_key(row["qid"], t), "question": row["text"], "text": t})
    units = sorted(seen.values(), key=lambda u: u["key"])
    random.Random(42).shuffle(units)
    return units


def graded() -> dict[str, int]:
    """Relevance grade by unit key."""
    if not GRADES.exists():
        return {}
    return {r["key"]: int(r["grade"]) for r in csv.DictReader(open(GRADES, encoding="utf8"))}


def cmd_units(args: argparse.Namespace) -> None:
    """Print the next ungraded units."""
    done = graded()
    todo = [u for u in rel_units() if u["key"] not in done]
    print(f"{len(todo)} ungraded; showing {min(args.n, len(todo))}")
    for u in todo[: args.n]:
        print(f"\n### {u['key']}\nQUESTION: {u['question']}\nTEXT: {u['text']}")


def cmd_record(args: argparse.Namespace) -> None:
    """Append key=grade pairs (0, 1 or 2). LLM grades only."""
    new = not GRADES.exists()
    with open(GRADES, "a", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["key", "grade", "grader"])
        for pair in args.pairs:
            key, grade = pair.rsplit("=", 1)
            assert grade in ("0", "1", "2"), pair
            w.writerow([key, grade, "LLM:" + args.grader])
    print(f"recorded {len(args.pairs)} grades")


def dev_outcome(row: dict[str, Any], t: float, done: dict[str, int]) -> tuple[bool, bool | None]:
    """(answered at T, hit at T) of a dev row. hit is None for no_answer queries."""
    scored = row["checks"].get("scored", []) if row["outcome"] == "answered" else []
    shown = [s["text"] for s in scored if s["score"] >= t]
    if not row["answerable"]:
        return bool(shown), None
    return bool(shown), any(done[rel_key(row["qid"], x)] == 2 for x in shown)


def tune_table(rows: list[dict[str, Any]], done: dict[str, int]) -> list[dict[str, float]]:
    """Dev hit rate and no_answer wrong rate for every T of the grid."""
    out = []
    for t in GRID:
        res = [dev_outcome(r, float(t), done) for r in rows]
        ans = [h for (_, h), r in zip(res, rows, strict=True) if r["answerable"]]
        non = [a for (a, _), r in zip(res, rows, strict=True) if not r["answerable"]]
        out.append({"T": t, "hit": sum(bool(h) for h in ans), "n_ans": len(ans), "wrong": sum(non), "n_non": len(non)})
    return out


def pick_threshold(table: list[dict[str, float]]) -> int:
    """Frozen rule: highest dev hit count with wrong rate <= 0.2, ties to the higher T."""
    ok = [e for e in table if e["wrong"] / e["n_non"] <= MAX_WRONG_DEV]
    best = max(e["hit"] for e in ok)
    return int(max(e["T"] for e in ok if e["hit"] == best))


def cmd_tune(_: argparse.Namespace) -> None:
    """Pick T on the dev half by the frozen rule and write the config."""
    rows = read_run("dev")
    done = graded()
    missing = [rel_key(r["qid"], s["text"]) for r in rows if r["answerable"] and r["outcome"] == "answered"
               for s in r["checks"]["scored"] if rel_key(r["qid"], s["text"]) not in done]
    if missing:
        raise SystemExit(f"{len(missing)} dev units ungraded")
    table = tune_table(rows, done)
    for e in table:
        print(e)
    t = pick_threshold(table)
    cfg = {"frozen_before_heldout_run": True, "plan": "reports/rag_rerank_plan.md", "model": rerank.MODEL,
           "max_length": rerank.MAX_LENGTH, "top": rerank.TOP, "threshold_T": t, "dev_table": table,
           "queries_sha256": sha(QUERIES), "split_sha256": sha(SPLIT), "gate_threshold": frozen_threshold(),
           "rag_config_sha256": sha(ROOT / "data" / "rag" / "rag_config.json"), "gate": GATE}
    CONFIG.write_text(json.dumps(cfg, indent=1), encoding="utf8")
    print("chosen T", t, "wrote", CONFIG, "sha256", sha(CONFIG))


def frozen_config() -> dict[str, Any]:
    """The frozen config, checked against the current query and split files."""
    cfg = json.loads(CONFIG.read_text(encoding="utf8"))
    assert cfg["queries_sha256"] == sha(QUERIES) and cfg["split_sha256"] == sha(SPLIT), "inputs changed"
    return cfg


def system_numbers(name: str, done: dict[str, int], module: str | None = None) -> dict[str, Any]:
    """Held-out metrics of one system, optionally for one module."""
    rows = [r for r in read_run(name) if module in (None, r["module"])]
    ans = [r for r in rows if r["answerable"]]
    non = [r for r in rows if not r["answerable"]]
    grades = [[done.get(rel_key(r["qid"], t)) for t in shown_units(r)] for r in ans]
    flat = [g for gs in grades for g in gs]
    lat = [r["latency_s"] for r in rows]
    return {
        "n_ans": len(ans), "n_non": len(non), "hit": sum(any(g == 2 for g in gs) for gs in grades),
        "units": len(flat), "unit_ge1": sum(g is not None and g >= 1 for g in flat),
        "unit_2": sum(g == 2 for g in flat), "ungraded": sum(g is None for g in flat),
        "answered": sum(bool(shown_units(r)) for r in ans), "wrong": sum(bool(shown_units(r)) for r in non),
        "median_s": statistics.median(lat), "p90_s": pct(lat, 0.9),
    }


def cmd_report(_: argparse.Namespace) -> None:
    """Write results/rag_rerank.md with held-out metrics and the frozen decision."""
    cfg = frozen_config()
    done = graded()
    lines = ["# RAG sentence reranker, held-out evaluation", "",
             f"Plan and rule: `reports/rag_rerank_plan.md`, config `data/rag/rag_rerank_config.json` (T = "
             f"{cfg['threshold_T']}, tuned on the 20 dev queries). 20 held-out queries (15 answerable, 5 no_answer), "
             "each system run once. Relevance grades are LLM grades (not human), graded blind with systems pooled. "
             "Gated and abstained queries count as misses.", ""]
    nums: dict[str, dict[str, Any]] = {}
    for name in SYSTEMS:
        n = nums[name] = system_numbers(name, done)
        lines += [f"## {name}", ""]
        for module in (None, "medicine", "device"):
            m = n if module is None else system_numbers(name, done, module)
            label = {None: "All", "medicine": "Medicine", "device": "Device"}[module]
            lines.append(f"- {label}: direct hit rate {fmt(m['hit'], m['n_ans'])}; units {m['units']}, graded >= 1 "
                         f"{fmt(m['unit_ge1'], m['units'])}, graded 2 {fmt(m['unit_2'], m['units'])}; shows units on "
                         f"answerable {fmt(m['answered'], m['n_ans'])}; shows units on no_answer "
                         f"{fmt(m['wrong'], m['n_non'])}; ungraded {m['ungraded']}")
        lines += [f"- latency over 20: median {n['median_s']:.2f} s, p90 {n['p90_s']:.2f} s", ""]
    r, e = nums["rerank"], nums["extractive"]
    checks = [("direct hit rate rerank >= extractive", r["hit"] / r["n_ans"], e["hit"] / e["n_ans"], ">="),
              ("wrong rate on no_answer", r["wrong"] / r["n_non"], GATE["wrong_le"], "<="),
              ("median latency over 20 (s)", r["median_s"], GATE["median_s_lt"], "<")]
    lines += ["## Decision by the frozen rule", ""]
    ok_all = True
    for name, value, bound, op in checks:
        ok = {">=": value >= bound, "<": value < bound, "<=": value <= bound}[op]
        ok_all &= ok
        lines.append(f"- {name}: {value:.3f} {op} {bound:.3f}: {'met' if ok else 'NOT met'}")
    verdict = "rerank becomes the default extractive display" if ok_all else "nothing is merged"
    lines += ["", f"- **{verdict}**", ""]
    (RESULTS / "rag_rerank.md").write_text("\n".join(lines), encoding="utf8")
    print("\n".join(lines))


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("dev-run")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=lambda a: execute("dev", "rerank", "dev", None, a.force))
    p = sub.add_parser("run")
    p.add_argument("system", choices=SYSTEMS)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=lambda a: execute(a.system, a.system, "heldout", frozen_config()["threshold_T"], a.force))
    p = sub.add_parser("units")
    p.add_argument("--n", type=int, default=25)
    p.set_defaults(fn=cmd_units)
    p = sub.add_parser("record")
    p.add_argument("pairs", nargs="+")
    p.add_argument("--grader", required=True)
    p.set_defaults(fn=cmd_record)
    sub.add_parser("tune").set_defaults(fn=cmd_tune)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
