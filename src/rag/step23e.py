"""Step 23e: structured (JSON) answers on fresh queries. Commands: freeze, run, faith-units, faith-record,
regrade-sample, report. Faithfulness grades are LLM grades in a separate file, never human grades.

The frozen config (data/rag/step23e_config.json) is written and committed before `run`.
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

from src.rag.evaluate import fmt, pct
from src.rag.prompt import ANSWER_SCHEMA, PROMPTS
from src.rag.provider import OllamaProvider
from src.rag.service import RagService, frozen_threshold
from src.rag.settings import RagSettings

ROOT = Path(__file__).resolve().parents[2]
QUERIES = ROOT / "data" / "eval" / "fresh_rag_e.tsv"
CONFIG = ROOT / "data" / "rag" / "step23e_config.json"
RESULTS = ROOT / "results"
FAITH_CSV = RESULTS / "step23e_faithfulness_llm.csv"
REGRADE_IDS = RESULTS / "step23e_regrade_ids.json"
SETTINGS = RagSettings(output="json", prompt="v3", max_tokens=300)
MIN_ANSWERED, MAX_WRONG, MIN_FAITH, MAX_MEDIAN_S = 0.60, 0.20, 0.80, 30.0


def sha(path: Path) -> str:
    """sha256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_queries() -> list[dict[str, Any]]:
    """The fresh query list (qid, text, module, answerable)."""
    with open(QUERIES, encoding="utf8", newline="") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t") if r and r[0] != "qid"]
    return [{"qid": r[0], "text": r[1], "module": r[2], "answerable": r[3] == "1"} for r in rows]


def slug(tag: str) -> str:
    """File-name safe model tag."""
    return tag.replace(":", "_").replace("/", "_")


def run_path(tag: str) -> Path:
    """Run file for one model."""
    return RESULTS / f"step23e_run_{slug(tag)}.jsonl"


def cmd_freeze(args: argparse.Namespace) -> None:
    """Write the frozen config. Run before any evaluation run and commit it."""
    cfg = {
        "frozen_before_run": True,
        "queries_file": "data/eval/fresh_rag_e.tsv", "queries_sha256": sha(QUERIES),
        "n_answerable": sum(q["answerable"] for q in load_queries()),
        "n_no_answer": sum(not q["answerable"] for q in load_queries()),
        "models": args.models, "temperature": 0, "seed": 42, "num_ctx": 4096,
        "prompt_version": "v3", "prompt_sha256": hashlib.sha256("".join(PROMPTS["v3"]).encode()).hexdigest()[:12],
        "schema": ANSWER_SCHEMA, "settings": SETTINGS.echo(), "threshold": frozen_threshold(),
        "rag_config_sha256": sha(ROOT / "data" / "rag" / "rag_config.json"),
        "e5b_settings_sha256": json.loads((ROOT / "data" / "eval" / "step18_config.json").read_text())[
            "settings_sha256"],
        "pilot": args.pilot,
        "rule": {
            "eligible": f"median latency over all queries < {MAX_MEDIAN_S} s AND answered rate on answerable >= "
                        f"{MIN_ANSWERED} AND wrong-answer rate on no_answer <= {MAX_WRONG}",
            "grade": "faithfulness is graded only for eligible models, every sentence of every answered response",
            "qualified": f"supported (grade 2) sentence rate >= {MIN_FAITH} (point estimate)",
            "choose": "among qualified: highest answered rate on answerable, then higher supported rate, then lower "
                      "median latency. If none qualifies the extractive default stays.",
            "second_pass": "random 20 percent of graded sentences (seed 42) graded again, agreement reported",
            "intervals": "Wilson 95 percent",
        },
    }
    CONFIG.write_text(json.dumps(cfg, indent=1), encoding="utf8")
    print("wrote", CONFIG, "sha256", sha(CONFIG))


def cmd_run(args: argparse.Namespace) -> None:
    """Run every fresh query through one model, once, and write results/step23e_run_<tag>.jsonl."""
    cfg = json.loads(CONFIG.read_text(encoding="utf8"))
    assert args.model in cfg["models"], "model not in the frozen config"
    assert cfg["queries_sha256"] == sha(QUERIES), "queries changed after freeze"
    out = run_path(args.model)
    if out.exists() and not args.force:
        raise SystemExit(f"{out} exists; each model is run once (--force only after a crash)")
    service = RagService(provider=OllamaProvider(args.model, SETTINGS), settings=SETTINGS, threshold=cfg["threshold"])
    with open(out, "w", encoding="utf8") as fh:
        for q in load_queries():
            result = service.ask(q["text"], q["module"])
            fh.write(json.dumps({**q, "model": args.model, **dataclasses.asdict(result)}) + "\n")
            fh.flush()
            print(q["qid"], result.outcome, result.cause, result.checks.get("failed", ""), result.latency_s, flush=True)


def read_run(tag: str) -> list[dict[str, Any]]:
    """Rows of one finished run."""
    return [json.loads(line) for line in open(run_path(tag), encoding="utf8")]


def stats(tag: str) -> dict[str, Any]:
    """Selection numbers of one model (all queries pooled, modules also reported separately in the report)."""
    rows = read_run(tag)
    ans = [r for r in rows if r["answerable"]]
    non = [r for r in rows if not r["answerable"]]
    lat = [r["latency_s"] for r in rows]
    return {
        "answered": sum(r["outcome"] == "answered" for r in ans), "n_ans": len(ans),
        "wrong": sum(r["outcome"] == "answered" for r in non), "n_non": len(non),
        "median_s": statistics.median(lat), "p90_s": pct(lat, 0.9),
    }


def eligible(s: dict[str, Any]) -> bool:
    """The frozen eligibility rule."""
    return (s["median_s"] < MAX_MEDIAN_S and s["answered"] / s["n_ans"] >= MIN_ANSWERED
            and s["wrong"] / s["n_non"] <= MAX_WRONG)


def faith_units(tag: str) -> list[dict[str, str]]:
    """One row per sentence of an answered response: id, sentence, text of the passages it cites."""
    from src.checker.retrieval import module_chunks

    units = []
    for row in read_run(tag):
        if row["outcome"] != "answered":
            continue
        chunks = module_chunks(row["module"])
        for i, s in enumerate(row["sentences"], start=1):
            cited = "\n".join(f"[{c}] {chunks[c].text}" for c in s["chunk_ids"])
            units.append({"unit": f"{slug(tag)}:{row['qid']}:{i}", "sentence": s["text"], "cited": cited})
    return units


def graded() -> dict[str, dict[str, str]]:
    """Existing grades by unit id and pass."""
    out: dict[str, dict[str, str]] = {}
    if FAITH_CSV.exists():
        for r in csv.DictReader(open(FAITH_CSV, encoding="utf8")):
            out.setdefault(r["unit"], {})[r["pass"]] = r["grade"]
    return out


def cmd_faith_units(args: argparse.Namespace) -> None:
    """Print the next ungraded units of a model."""
    done = graded()
    todo = [u for u in faith_units(args.model) if args.pass_no not in done.get(u["unit"], {})]
    if args.pass_no == "2":
        ids = set(json.loads(REGRADE_IDS.read_text()))
        todo = [u for u in todo if u["unit"] in ids]
    print(f"{len(todo)} ungraded units; showing {min(args.n, len(todo))}")
    for u in todo[: args.n]:
        print(f"\n### {u['unit']}\nSENTENCE: {u['sentence']}\nCITED:\n{u['cited']}")


def cmd_faith_record(args: argparse.Namespace) -> None:
    """Append unit=grade pairs (0, 1 or 2). LLM grades only."""
    new = not FAITH_CSV.exists()
    with open(FAITH_CSV, "a", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["unit", "pass", "grade", "grader"])
        for pair in args.pairs:
            unit, grade = pair.rsplit("=", 1)
            assert grade in ("0", "1", "2"), pair
            w.writerow([unit, args.pass_no, grade, "LLM:" + args.grader])
    print(f"recorded {len(args.pairs)} grades (pass {args.pass_no})")


def cmd_regrade_sample(_: argparse.Namespace) -> None:
    """Pick a random 20 percent of pass-1 graded units (seed 42) for the second pass."""
    ids = sorted(u for u, g in graded().items() if "1" in g)
    random.Random(42).shuffle(ids)
    pick = sorted(ids[: max(1, round(0.2 * len(ids)))])
    REGRADE_IDS.write_text(json.dumps(pick))
    print(f"{len(pick)} of {len(ids)} units selected for pass 2")


def model_section(tag: str) -> list[str]:
    """Markdown lines for one model, public and professional apart, plus pooled selection numbers."""
    rows = read_run(tag)
    s = stats(tag)
    lines = [f"## {tag}", ""]
    for module, label in (("medicine", "Public (medicine)"), ("device", "Professional (device)")):
        sub = [r for r in rows if r["module"] == module]
        ans = [r for r in sub if r["answerable"]]
        non = [r for r in sub if not r["answerable"]]
        causes: dict[str, int] = {}
        for r in ans:
            if r["outcome"] != "answered":
                key = f"{r['cause']}" + (f"/{r['checks'].get('failed')}" if r["checks"].get("failed") else "")
                causes[key] = causes.get(key, 0) + 1
        lines.append(f"- {label}: verified answers on answerable {fmt(sum(r['outcome'] == 'answered' for r in ans), len(ans))}; "  # noqa: E501
                     f"not answered by cause {causes or 'none'}; wrong answers on no_answer "
                     f"{fmt(sum(r['outcome'] == 'answered' for r in non), len(non))}")
    gen = [r for r in rows if r["raw"].strip()]
    bad = sum(r["checks"].get("failed") == "bad_json" for r in gen)
    lines.append(f"- reached the model: {len(gen)} of {len(rows)} (the rest stopped at the scope rule or score gate); "
                 f"unparseable JSON: {bad}")
    fails: dict[str, int] = {}
    for r in gen:
        f = r["checks"].get("failed", "")
        if f:
            fails[f] = fails.get(f, 0) + 1
    lines.append(f"- first failed check among model replies: {fails or 'none'}")
    lines.append(f"- pooled: verified-answer rate {fmt(s['answered'], s['n_ans'])}; wrong-answer rate "
                 f"{fmt(s['wrong'], s['n_non'])}; latency median {s['median_s']:.1f} s, p90 {s['p90_s']:.1f} s")
    lines.append(f"- eligible under the frozen rule: {eligible(s)}")
    return lines + [""]


def faith_section(tag: str) -> tuple[list[str], float | None]:
    """Faithfulness lines and the supported rate (None when not graded)."""
    done = graded()
    units = [u["unit"] for u in faith_units(tag)]
    g1 = {u: int(done[u]["1"]) for u in units if "1" in done.get(u, {})}
    lines = [f"### Faithfulness, {tag} (LLM-graded, not human)", ""]
    if not g1:
        return lines + ["- not graded (not eligible, or no answered responses)", ""], None
    n = len(g1)
    sup = sum(v == 2 for v in g1.values())
    lines.append(f"- sentences graded {n}: supported (2) {fmt(sup, n)}; supported or partly (>= 1) "
                 f"{fmt(sum(v >= 1 for v in g1.values()), n)}")
    byq: dict[str, list[int]] = {}
    for u, v in g1.items():
        byq.setdefault(u.split(":")[1], []).append(v)
    lines.append(f"- query level, every sentence supported: {fmt(sum(all(x == 2 for x in v) for v in byq.values()), len(byq))}")  # noqa: E501
    pairs = [(g1[u], int(done[u]["2"])) for u in g1 if "2" in done.get(u, {})]
    if pairs:
        same = sum(a == b for a, b in pairs)
        strict = sum((a == 2) == (b == 2) for a, b in pairs)
        lines.append(f"- second pass, random 20 percent ({len(pairs)} units): exact agreement {fmt(same, len(pairs))}, "
                     f"supported vs not {fmt(strict, len(pairs))}")
    return lines + [""], sup / n


def cmd_report(_: argparse.Namespace) -> None:
    """Write results/step23e_structured.md and print the selection."""
    cfg = json.loads(CONFIG.read_text(encoding="utf8"))
    lines = ["# Step 23e structured output evaluation", "",
             f"Fresh queries: {cfg['n_answerable']} answerable, {cfg['n_no_answer']} no_answer, written by the "
             "assistant, not used in any earlier selection. Frozen config `data/rag/step23e_config.json`. "
             "Faithfulness grades are LLM grades, not human. Each model run once.", ""]
    qualified: list[tuple[float, float, float, str]] = []
    for tag in cfg["models"]:
        if not run_path(tag).exists():
            lines += [f"## {tag}", "", "- not run", ""]
            continue
        lines += model_section(tag)
        s = stats(tag)
        if eligible(s):
            fl, rate = faith_section(tag)
            lines += fl
            if rate is not None and rate >= MIN_FAITH:
                qualified.append((s["answered"] / s["n_ans"], rate, -s["median_s"], tag))
    chosen = max(qualified)[3] if qualified else None
    lines += ["## Selection by the frozen rule", "", f"- chosen: {chosen or 'none, the extractive default stays'}", ""]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "step23e_structured.md").write_text("\n".join(lines), encoding="utf8")
    print("\n".join(lines))


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--pilot", type=json.loads, default={})
    p.set_defaults(fn=cmd_freeze)
    p = sub.add_parser("run")
    p.add_argument("model")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("faith-units")
    p.add_argument("model")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--pass-no", default="1")
    p.set_defaults(fn=cmd_faith_units)
    p = sub.add_parser("faith-record")
    p.add_argument("pairs", nargs="+")
    p.add_argument("--pass-no", default="1")
    p.add_argument("--grader", required=True)
    p.set_defaults(fn=cmd_faith_record)
    sub.add_parser("regrade-sample").set_defaults(fn=cmd_regrade_sample)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
