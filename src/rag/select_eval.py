"""Selection mode evaluation (reports/rag_select_plan.md). Commands: freeze, run, units, record, regrade-sample, report.

Relevance and faithfulness grades are LLM grades in a separate file, never human grades. The config is written and
committed before `run`. Each mode is run once.
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

from src.rag import selection
from src.rag.evaluate import fmt, pct
from src.rag.provider import NullProvider, OllamaProvider, Provider
from src.rag.service import RagService, frozen_threshold
from src.rag.settings import AI_MODEL, AI_SETTINGS, RagSettings

ROOT = Path(__file__).resolve().parents[2]
QUERIES = ROOT / "data" / "eval" / "fresh_rag_select.tsv"
CONFIG = ROOT / "data" / "rag" / "rag_select_config.json"
RESULTS = ROOT / "results"
GRADES = RESULTS / "rag_select_grades_llm.csv"
REGRADE_IDS = RESULTS / "rag_select_regrade_ids.json"
SELECT_SETTINGS = RagSettings(output="select", max_tokens=60, timeout_s=90.0)
EXTRACTIVE_SETTINGS = RagSettings()
MODES = ("extractive", "select", "generative")
MAX_MEDIAN_S, MIN_ANSWERED, MAX_WRONG, MIN_FAITH = 30.0, 0.60, 0.20, 0.80


def sha(path: Path) -> str:
    """sha256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_queries() -> list[dict[str, Any]]:
    """The fresh queries (qid, text, module, answerable)."""
    with open(QUERIES, encoding="utf8", newline="") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t") if r and r[0] != "qid"]
    return [{"qid": r[0], "text": r[1], "module": r[2], "answerable": r[3] == "1"} for r in rows]


def mode_setup(mode: str) -> tuple[Provider, RagSettings]:
    """Provider and settings of one mode."""
    if mode == "extractive":
        return NullProvider(), EXTRACTIVE_SETTINGS
    settings = SELECT_SETTINGS if mode == "select" else AI_SETTINGS
    return OllamaProvider(AI_MODEL, settings), settings


def run_path(mode: str) -> Path:
    """Run file of one mode."""
    return RESULTS / f"rag_select_run_{mode}.jsonl"


def cmd_freeze(_: argparse.Namespace) -> None:
    """Write the frozen config (before any run) and print its hash."""
    import dataclasses as dc

    cfg = {
        "frozen_before_run": True, "plan": "reports/rag_select_plan.md",
        "queries_file": "data/eval/fresh_rag_select.tsv", "queries_sha256": sha(QUERIES),
        "model": AI_MODEL, "temperature": 0, "seed": 42, "num_ctx": 4096,
        "select_prompt_sha256": selection.prompt_hash(), "select_schema": selection.SELECT_SCHEMA,
        "select_settings": SELECT_SETTINGS.echo(), "generative_settings": AI_SETTINGS.echo(),
        "extractive_settings": EXTRACTIVE_SETTINGS.echo(), "threshold": frozen_threshold(),
        "rag_config_sha256": sha(ROOT / "data" / "rag" / "rag_config.json"),
        "e5b_settings_sha256": json.loads((ROOT / "data" / "eval" / "step18_config.json").read_text())[
            "settings_sha256"],
        "max_selected": selection.MAX_SELECTED, "max_candidates": selection.MAX_CANDIDATES,
        "rule": {"median_s_lt": MAX_MEDIAN_S, "answered_ge": MIN_ANSWERED, "wrong_le": MAX_WRONG,
                 "faith_supported_ge": MIN_FAITH, "hit_rate_ge_extractive": True,
                 "unit_precision_ge1_ge_extractive": True},
    }
    del dc
    CONFIG.write_text(json.dumps(cfg, indent=1), encoding="utf8")
    print("wrote", CONFIG, "sha256", sha(CONFIG))


def cmd_run(args: argparse.Namespace) -> None:
    """Run every fresh query through one mode, once, writing results/rag_select_run_<mode>.jsonl."""
    cfg = json.loads(CONFIG.read_text(encoding="utf8"))
    assert cfg["queries_sha256"] == sha(QUERIES), "queries changed after freeze"
    assert cfg["select_prompt_sha256"] == selection.prompt_hash(), "prompt changed after freeze"
    out = run_path(args.mode)
    if out.exists() and not args.force:
        raise SystemExit(f"{out} exists; each mode is run once (--force only after a crash)")
    provider, settings = mode_setup(args.mode)
    service = RagService(provider=provider, settings=settings, threshold=cfg["threshold"])
    service.ask("What must the principal display panel show?", "device")  # loads retrieval, warms the model
    with open(out, "w", encoding="utf8") as fh:
        for q in load_queries():
            result = service.ask(q["text"], q["module"])
            fh.write(json.dumps({**q, "mode": args.mode, **dataclasses.asdict(result)}) + "\n")
            fh.flush()
            print(q["qid"], result.outcome, result.cause, result.checks.get("failed", ""), result.latency_s,
                  flush=True)


def read_run(mode: str) -> list[dict[str, Any]]:
    """Rows of one finished run."""
    return [json.loads(line) for line in open(run_path(mode), encoding="utf8")]


def shown_units(row: dict[str, Any]) -> list[str]:
    """What the user sees as the answer: quotes for extractive, answer sentences when answered, else nothing."""
    if row["mode"] == "extractive":
        return [s["quote"] for s in row["sources"]]
    return [s["text"] for s in row["sentences"]] if row["outcome"] == "answered" else []


def rel_key(qid: str, text: str) -> str:
    """Relevance unit id: identical text for one query is graded once, whatever the mode."""
    return f"{qid}:{hashlib.sha1(text.encode()).hexdigest()[:8]}"


def faith_units(mode: str) -> list[dict[str, str]]:
    """Selected or generated sentences with the text of the chunk they cite."""
    from src.checker.retrieval import module_chunks

    out = []
    for row in read_run(mode):
        if row["outcome"] != "answered":
            continue
        chunks = module_chunks(row["module"])
        for i, s in enumerate(row["sentences"], start=1):
            cited = "\n".join(f"[{c}] {chunks[c].text}" for c in s["chunk_ids"])
            out.append({"key": f"{mode}:{row['qid']}:{i}", "question": row["text"], "text": s["text"],
                        "cited": cited})
    return out


def rel_units() -> list[dict[str, str]]:
    """Distinct (query, text) units over all finished modes, answerable queries only, shuffled with seed 42."""
    seen: dict[str, dict[str, str]] = {}
    for mode in MODES:
        if not run_path(mode).exists():
            continue
        for row in read_run(mode):
            if row["answerable"]:
                for t in shown_units(row):
                    seen.setdefault(rel_key(row["qid"], t), {"key": rel_key(row["qid"], t),
                                                              "question": row["text"], "text": t})
    units = sorted(seen.values(), key=lambda u: u["key"])
    random.Random(42).shuffle(units)
    return units


def graded() -> dict[tuple[str, str], dict[str, str]]:
    """Grades by (kind, key) then pass."""
    out: dict[tuple[str, str], dict[str, str]] = {}
    if GRADES.exists():
        for r in csv.DictReader(open(GRADES, encoding="utf8")):
            out.setdefault((r["kind"], r["key"]), {})[r["pass"]] = r["grade"]
    return out


def cmd_units(args: argparse.Namespace) -> None:
    """Print the next ungraded units of a kind (rel, or faith for one mode)."""
    done = graded()
    if args.kind == "rel":
        todo = [u for u in rel_units() if args.pass_no not in done.get(("rel", u["key"]), {})]
    else:
        todo = [u for u in faith_units(args.mode) if args.pass_no not in done.get(("faith", u["key"]), {})]
        if args.pass_no == "2":
            ids = set(json.loads(REGRADE_IDS.read_text()))
            todo = [u for u in todo if u["key"] in ids]
    print(f"{len(todo)} ungraded; showing {min(args.n, len(todo))}")
    for u in todo[: args.n]:
        extra = f"\nCITED:\n{u['cited']}" if args.kind == "faith" else ""
        print(f"\n### {u['key']}\nQUESTION: {u['question']}\nTEXT: {u['text']}{extra}")


def cmd_record(args: argparse.Namespace) -> None:
    """Append key=grade pairs (0, 1 or 2). LLM grades only."""
    new = not GRADES.exists()
    with open(GRADES, "a", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["kind", "key", "pass", "grade", "grader"])
        for pair in args.pairs:
            key, grade = pair.rsplit("=", 1)
            assert grade in ("0", "1", "2"), pair
            w.writerow([args.kind, key, args.pass_no, grade, "LLM:" + args.grader])
    print(f"recorded {len(args.pairs)} {args.kind} grades (pass {args.pass_no})")


def cmd_regrade_sample(_: argparse.Namespace) -> None:
    """Random 20 percent (seed 42) of pass-1 faithfulness units for a second pass."""
    ids = sorted(k for (kind, k), g in graded().items() if kind == "faith" and "1" in g)
    random.Random(42).shuffle(ids)
    pick = sorted(ids[: max(1, round(0.2 * len(ids)))])
    REGRADE_IDS.write_text(json.dumps(pick))
    print(f"{len(pick)} of {len(ids)} units selected for pass 2")


def mode_numbers(mode: str, done: dict[tuple[str, str], dict[str, str]], module: str | None = None) -> dict[str, Any]:
    """All plan metrics of one mode, optionally for one module."""
    rows = [r for r in read_run(mode) if module in (None, r["module"])]
    ans = [r for r in rows if r["answerable"]]
    non = [r for r in rows if not r["answerable"]]
    rel_grades: list[list[int | None]] = []
    for r in ans:
        rel_grades.append([int(done[("rel", rel_key(r["qid"], t))]["1"]) if ("rel", rel_key(r["qid"], t)) in done
                           else None for t in shown_units(r)])
    flat = [g for gs in rel_grades for g in gs]
    lat = [r["latency_s"] for r in rows]
    reached = [r["latency_s"] for r in rows if r["raw"].strip() or mode == "extractive" and r["sources"]]
    faith = [int(done[("faith", f["key"])]["1"]) for f in faith_units(mode)
             if ("faith", f["key"]) in done and f["key"].split(":")[1] in {r["qid"] for r in rows}]
    return {
        "n_ans": len(ans), "n_non": len(non),
        "hit": sum(any(g == 2 for g in gs) for gs in rel_grades),
        "units": len(flat), "unit_ge1": sum(g is not None and g >= 1 for g in flat),
        "unit_2": sum(g == 2 for g in flat), "ungraded": sum(g is None for g in flat),
        "answered": sum(r["outcome"] == "answered" for r in ans),
        "shows": sum(bool(shown_units(r)) for r in ans),
        "wrong": sum(r["outcome"] == "answered" for r in non),
        "shows_non": sum(bool(r["sources"]) or r["outcome"] == "answered" for r in non),
        "median_s": statistics.median(lat), "p90_s": pct(lat, 0.9),
        "median_reached_s": statistics.median(reached) if reached else float("nan"),
        "faith_n": len(faith), "faith_2": sum(g == 2 for g in faith), "faith_ge1": sum(g >= 1 for g in faith),
    }


def cmd_report(_: argparse.Namespace) -> None:
    """Write results/rag_select.md with all metrics and the frozen decision."""
    done = graded()
    lines = ["# RAG selection mode, fresh 40-query evaluation", "",
             "Plan and rule: `reports/rag_select_plan.md`, config `data/rag/rag_select_config.json`. 30 answerable, "
             "10 no_answer, each mode run once. Relevance and faithfulness are LLM grades (not human), relevance "
             "graded blind with modes pooled. Abstentions and gated queries count as misses.", ""]
    nums: dict[str, dict[str, Any]] = {}
    for mode in MODES:
        if not run_path(mode).exists():
            lines += [f"## {mode}", "", "- not run", ""]
            continue
        n = nums[mode] = mode_numbers(mode, done)
        lines += [f"## {mode}", ""]
        for module in (None, "medicine", "device"):
            m = n if module is None else mode_numbers(mode, done, module)
            label = {None: "All", "medicine": "Public (medicine)", "device": "Professional (device)"}[module]
            lines.append(f"- {label}: direct hit rate {fmt(m['hit'], m['n_ans'])}; units shown {m['units']}, "
                         f"graded >= 1 {fmt(m['unit_ge1'], m['units'])}, graded 2 {fmt(m['unit_2'], m['units'])}; "
                         f"answered {fmt(m['answered'], m['n_ans'])}; wrong on no_answer "
                         f"{fmt(m['wrong'], m['n_non'])}; ungraded units {m['ungraded']}")
        lines.append(f"- latency over all 40: median {n['median_s']:.1f} s, p90 {n['p90_s']:.1f} s; median over "
                     f"queries that reached the model {n['median_reached_s']:.1f} s")
        if mode != "extractive":
            lines.append(f"- faithfulness, sentences graded {n['faith_n']}: supported (2) "
                         f"{fmt(n['faith_2'], n['faith_n'])}; supported or partly {fmt(n['faith_ge1'], n['faith_n'])}")
            pairs = [(int(g["1"]), int(g["2"])) for (k, key), g in done.items()
                     if k == "faith" and key.startswith(mode + ":") and "1" in g and "2" in g]
            if pairs:
                same = sum(a == b for a, b in pairs)
                lines.append(f"- second pass on {len(pairs)} units: exact agreement {fmt(same, len(pairs))}")
        else:
            lines.append(f"- shows quotes on answerable {fmt(n['shows'], n['n_ans'])}; shows quotes on no_answer "
                         f"{fmt(n['shows_non'], n['n_non'])} (irrelevant quotes shown)")
        lines.append("")
    lines += ["## Decision by the frozen rule", ""]
    if "select" in nums and "extractive" in nums:
        s, e = nums["select"], nums["extractive"]
        faith_rate = s["faith_2"] / s["faith_n"] if s["faith_n"] else float("nan")
        checks = [
            ("direct hit rate select >= extractive", s["hit"] / s["n_ans"], e["hit"] / e["n_ans"], ">="),
            ("unit precision (>= 1) select >= extractive", s["unit_ge1"] / max(1, s["units"]),
             e["unit_ge1"] / max(1, e["units"]), ">="),
            ("median latency over all 40 (s)", s["median_s"], MAX_MEDIAN_S, "<"),
            ("answered rate on answerable", s["answered"] / s["n_ans"], MIN_ANSWERED, ">="),
            ("wrong-answer rate on no_answer", s["wrong"] / s["n_non"], MAX_WRONG, "<="),
            ("supported sentence rate", faith_rate, MIN_FAITH, ">="),
        ]
        ok_all = True
        for name, value, bound, op in checks:
            ok = {">=": value >= bound, "<": value < bound, "<=": value <= bound}[op]
            ok_all &= ok
            lines.append(f"- {name}: {value:.3f} {op} {bound:.3f}: {'met' if ok else 'NOT met'}")
        verdict = "select becomes the optional AI mode" if ok_all else "current default and AI mode stay"
        lines += ["", f"- **{verdict}**", ""]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "rag_select.md").write_text("\n".join(lines), encoding="utf8")
    print("\n".join(lines))


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze").set_defaults(fn=cmd_freeze)
    p = sub.add_parser("run")
    p.add_argument("mode", choices=MODES)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("units")
    p.add_argument("kind", choices=("rel", "faith"))
    p.add_argument("--mode", default="select")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--pass-no", default="1")
    p.set_defaults(fn=cmd_units)
    p = sub.add_parser("record")
    p.add_argument("kind", choices=("rel", "faith"))
    p.add_argument("pairs", nargs="+")
    p.add_argument("--pass-no", default="1")
    p.add_argument("--grader", required=True)
    p.set_defaults(fn=cmd_record)
    sub.add_parser("regrade-sample").set_defaults(fn=cmd_regrade_sample)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
