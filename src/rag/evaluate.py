"""Step 23 evaluation (docs/RAG_SPEC.md section 7). Commands: queries, fit, run, faith-units, faith-record, metrics.

All faithfulness grades are LLM grades (separate `_llm` file), never human grades. Rubric and targets are frozen
in the spec before `run`. `fit` writes data/rag/rag_config.json (threshold fitted on the dev half only).
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any

from src.rag.prompt import PROMPT_VERSION
from src.rag.provider import NullProvider, OllamaProvider, Provider
from src.rag.service import CONFIG_PATH, RagService
from src.rag.settings import RagSettings

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "data" / "eval"
RESULTS = ROOT / "results"
ADVICE = ROOT / "data" / "rag" / "advice_queries.tsv"
SPLIT = EVAL / "abstain_split.json"
FAITH_CSV = RESULTS / "step23_faithfulness_llm.csv"
CONDITIONS: dict[str, tuple[str, str | None]] = {  # name -> (label, ollama tag)
    "A1": ("1.5b", "qwen2.5:1.5b-instruct-q4_K_M"),
    "A2": ("3b", "qwen2.5:3b-instruct-q4_K_M"),
    "B": ("off", None),
}
PRIMARY = "A1"  # chosen by the frozen acceptance rule: median answer under 30 s (3b measured about 36 s)
TARGETS = {"citation_validity_answer": 0.95, "faith_supported_sentence": 0.80, "wrong_answer_no_answer_max": 0.20,
           "answered_rate_answerable": 0.60}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Rate with the 95 percent Wilson interval. n = 0 gives nan."""
    if n == 0:
        return (math.nan, math.nan, math.nan)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def fmt(k: int, n: int) -> str:
    """'k/n = rate [lo, hi]'."""
    p, lo, hi = wilson(k, n)
    return "n/a (n=0)" if n == 0 else f"{k}/{n} = {p:.3f} [{lo:.3f}, {hi:.3f}]"


def _rows(name: str, module_col: int, text_col: int = 1) -> list[tuple[str, str, str, str]]:
    with open(EVAL / name, encoding="utf8", newline="") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t") if r and r[0] != "qid"]
    return [(r[0], r[text_col], r[module_col], r[3] if name != "fresh_web_faq.tsv" else r[2]) for r in rows]


def load_queries() -> list[dict[str, Any]]:
    """The frozen evaluation query list: set, module, answerable flag, dev or test half for abstention."""
    split = json.loads(SPLIT.read_text(encoding="utf8"))
    half = {q: h for h in ("dev", "test") for key in ("answerable", "no_answer") for q in split[h][key]}
    out: list[dict[str, Any]] = []

    def add(qid: str, text: str, module: str, kind: str, answerable: bool) -> None:
        out.append({"qid": qid, "text": text, "module": module, "set": kind, "answerable": answerable,
                    "half": half.get(qid, "")})

    for qid, text, module, _ in _rows("fresh_web_faq.tsv", 3):
        add(qid, text, module, "web_faq_" + module, True)
    for qid, text, module, _kind in _rows("queries_t1.tsv", 2):
        n = int(qid[1:])
        if 45 <= n <= 61:
            add(qid, text, module, "q45_q61", True)
        if 41 <= n <= 44:
            add(qid, text, module, "q41_q44", False)
    for qid, text, module, kind in _rows("queries_t1_abstain.tsv", 2):
        if kind == "no_answer":
            add(qid, text, module, "ab_no_answer", False)
    with open(ADVICE, encoding="utf8", newline="") as fh:
        for qid, text in (r for r in csv.reader(fh, delimiter="\t") if r and r[0] != "qid"):
            add(qid, text, "medicine", "advice", False)
    return out


def make_provider(cond: str) -> Provider:
    """Provider for a condition name."""
    tag = CONDITIONS[cond][1]
    return OllamaProvider(tag) if tag else NullProvider()


def auroc(pos: list[float], neg: list[float]) -> float:
    """P(random answerable scores above random no_answer), ties one half."""
    gt = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return gt / (len(pos) * len(neg))


def cmd_fit(_: argparse.Namespace) -> None:
    """Fit the score-gate threshold on the dev half only and write the frozen config."""
    service = RagService(provider=NullProvider())
    dev = [q for q in load_queries() if q["half"] == "dev" and q["set"] in ("q45_q61", "ab_no_answer")]
    scores = {}
    for q in dev:
        hits = service._load()[q["module"]].search(q["text"], k=RagSettings().k)
        scores[q["qid"]] = hits[0].score
    pos = [scores[q["qid"]] for q in dev if q["answerable"]]
    neg = [scores[q["qid"]] for q in dev if not q["answerable"]]
    above = sorted(s for s in scores.values() if s > max(neg))
    threshold = above[0] if above else None
    abstained = sum(s < threshold for s in pos) if threshold is not None else None
    usable = threshold is not None and abstained is not None and abstained <= len(pos) / 2
    cfg = {
        "frozen_before_final_run": True, "score_name": "e5b_top_score", "dev_scores": scores,
        "dev_auroc": auroc(pos, neg), "dev_answerable": len(pos), "dev_no_answer": len(neg),
        "threshold_candidate": threshold, "dev_answerable_abstained": abstained, "gate_usable": usable,
        "threshold": threshold if usable else None, "primary_condition": PRIMARY,
        "conditions": {k: v[1] for k, v in CONDITIONS.items()}, "prompt_version": PROMPT_VERSION,
        "settings": RagSettings().echo(), "targets": TARGETS,
        "e5b_settings_sha256": json.loads((EVAL / "step18_config.json").read_text())["settings_sha256"],
        "advice_queries_sha256": hashlib.sha256(ADVICE.read_bytes()).hexdigest(),
        "rule": "threshold = smallest dev score strictly above every dev no_answer score; gate off if it would "
                "abstain on more than half of the dev answerable queries",
    }
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=1), encoding="utf8")
    print(json.dumps({k: cfg[k] for k in ("dev_auroc", "threshold_candidate", "dev_answerable_abstained",
                                          "gate_usable", "threshold")}, indent=1))


def cmd_run(args: argparse.Namespace) -> None:
    """Run every frozen query through one condition and write results/step23_run_<cond>.jsonl (once)."""
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf8"))
    assert cfg["prompt_version"] == PROMPT_VERSION, "prompt changed after freeze"
    out_path = RESULTS / f"step23_run_{args.cond}.jsonl"
    if out_path.exists() and not args.force:
        raise SystemExit(f"{out_path} exists; the final run is made once (use --force only for a crash)")
    service = RagService(provider=make_provider(args.cond), threshold=cfg["threshold"])
    with open(out_path, "w", encoding="utf8") as fh:
        for q in load_queries():
            result = service.ask(q["text"], q["module"])
            row = {**q, "condition": args.cond, **dataclasses.asdict(result)}
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            print(q["qid"], result.outcome, result.cause, result.latency_s, flush=True)


def read_run(cond: str) -> list[dict[str, Any]]:
    """Rows of one finished run."""
    return [json.loads(line) for line in open(RESULTS / f"step23_run_{cond}.jsonl", encoding="utf8")]


def faith_units(cond: str) -> list[dict[str, str]]:
    """One row per generated sentence of an answered response: id, sentence, the text of its cited chunks."""
    from src.checker.retrieval import module_chunks

    units = []
    for row in read_run(cond):
        if row["outcome"] != "answered":
            continue
        chunks = module_chunks(row["module"])
        for i, s in enumerate(row["sentences"], start=1):
            cited = "\n".join(f"[{c}] {chunks[c].text}" for c in s["chunk_ids"])
            units.append({"unit": f"{cond}:{row['qid']}:{i}", "sentence": s["text"], "cited": cited})
    return units


def graded() -> dict[str, dict[str, str]]:
    """Existing faithfulness grades by unit id (pass 1 and pass 2 kept apart)."""
    out: dict[str, dict[str, str]] = {}
    if FAITH_CSV.exists():
        for r in csv.DictReader(open(FAITH_CSV, encoding="utf8")):
            out.setdefault(r["unit"], {})[r["pass"]] = r["grade"]
    return out


def cmd_faith_units(args: argparse.Namespace) -> None:
    """Print the next ungraded units of a condition for in-session grading."""
    done = graded()
    todo = [u for u in faith_units(args.cond) if args.pass_no not in done.get(u["unit"], {})]
    if args.pass_no == "2":
        ids = set(json.loads((RESULTS / "step23_regrade_ids.json").read_text()))
        todo = [u for u in todo if u["unit"] in ids]
    print(f"{len(todo)} ungraded units; showing {min(args.n, len(todo))}")
    for u in todo[: args.n]:
        print(f"\n### {u['unit']}\nSENTENCE: {u['sentence']}\nCITED:\n{u['cited']}")


def cmd_faith_record(args: argparse.Namespace) -> None:
    """Append grades given as unit=grade pairs (0, 1 or 2). Never writes a human grade column."""
    new = not FAITH_CSV.exists()
    with open(FAITH_CSV, "a", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["unit", "pass", "grade", "grader"])
        for pair in args.pairs:
            unit, grade = pair.rsplit("=", 1)
            assert grade in ("0", "1", "2"), pair
            w.writerow([unit, args.pass_no, grade, "LLM:" + args.model])
    print(f"recorded {len(args.pairs)} grades (pass {args.pass_no})")


def cmd_regrade_sample(args: argparse.Namespace) -> None:
    """Pick a random 20 percent of graded units (seed 42) for the second pass."""
    ids = sorted(u for u, g in graded().items() if "1" in g)
    random.Random(42).shuffle(ids)
    pick = sorted(ids[: max(1, round(0.2 * len(ids)))])
    (RESULTS / "step23_regrade_ids.json").write_text(json.dumps(pick))
    print(f"{len(pick)} of {len(ids)} units selected for pass 2")


def citation_relevance(rows: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Cited chunks with qrels grade >= 1, judged cited chunks, unjudged cited chunks (existing LLM qrels only)."""
    qrels: dict[tuple[str, str], int] = {}
    for name in ("qrels_t1_llm.tsv", "qrels_fresh_llm.tsv"):
        for line in open(EVAL / name, encoding="utf8"):
            qid, _, cid, g = line.split()
            qrels[(qid, cid)] = int(g)
    rel = judged = unjudged = 0
    for r in rows:
        if r["outcome"] != "answered":
            continue
        for s in r["sources"]:
            g = qrels.get((r["qid"], s["chunk_id"]))
            if g is None:
                unjudged += 1
            else:
                judged += 1
                rel += g >= 1
    return rel, judged, unjudged


def pct(values: list[float], q: float) -> float:
    """Simple percentile of a list."""
    v = sorted(values)
    return v[min(len(v) - 1, int(q * len(v)))] if v else math.nan


def condition_section(cond: str) -> list[str]:
    """Markdown lines for one condition, public and professional kept apart."""
    rows = read_run(cond)
    lines = [f"## Condition {cond} ({CONDITIONS[cond][1] or 'provider off, extractive'})", ""]
    for module, label in (("medicine", "Public (medicine)"), ("device", "Professional (device)")):
        sub = [r for r in rows if r["module"] == module and r["set"] != "advice"]
        ans = [r for r in sub if r["answerable"]]
        non = [r for r in sub if not r["answerable"]]
        lines += [f"### {label}", ""]
        lines.append(f"- answered rate on answerable: {fmt(sum(r['outcome'] == 'answered' for r in ans), len(ans))}")
        causes: dict[str, int] = {}
        for r in ans:
            if r["outcome"] != "answered":
                causes[f"{r['outcome']}:{r['cause']}"] = causes.get(f"{r['outcome']}:{r['cause']}", 0) + 1
        lines.append(f"  - not answered, by cause: {causes or 'none'}")
        wrong = [r for r in non if r["outcome"] == "answered"]
        lines.append(f"- wrong-answer rate on no_answer (answered): {fmt(len(wrong), len(non))}")
        lines.append("  - no_answer queries answered: " + (", ".join(r["qid"] for r in wrong) or "none"))
        shown = [r for r in non if r["mode"] == "extractive"]
        lines.append(f"  - no_answer queries that showed extractive quotes: {len(shown)} of {len(non)}")
        for half in ("dev", "test"):
            h = [r for r in non if r["half"] == half]
            if h:
                lines.append(f"  - {half} half: answered {sum(r['outcome'] == 'answered' for r in h)} of {len(h)}")
        gen = [r for r in sub if r["raw"].strip() and r["raw"].strip().rstrip(".") != "NO_ANSWER"]
        if gen:
            ok = sum(r["checks"].get("ok", False) for r in gen)
            sent = sum(r["checks"].get("n_sentences", 0) for r in gen)
            valid = sum(r["checks"].get("n_valid_sentences", 0) for r in gen)
            lines.append(f"- citation validity, answer level (all generated answers pass verification): {fmt(ok, len(gen))}")  # noqa: E501
            lines.append(f"- citation validity, sentence level (marker present and in the retrieved set): {fmt(valid, sent)}")  # noqa: E501
            fails: dict[str, int] = {}
            for r in gen:
                f = r["checks"].get("failed", "")
                if f:
                    fails[f] = fails.get(f, 0) + 1
            lines.append(f"  - first failed check among generated answers: {fails or 'none'}")
        rel, judged, unjudged = citation_relevance(sub)
        lines.append(f"- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): "
                     f"{fmt(rel, judged)}, unjudged cited chunks {unjudged}")
        lat = [r["latency_s"] for r in sub]
        lines.append(f"- latency seconds, median {pct(lat, .5):.1f}, 90th percentile {pct(lat, .9):.1f}")
        lines.append("")
    adv = [r for r in rows if r["set"] == "advice"]
    lines.append(f"### Scope rule (public)\n\n- recall on advice queries: {fmt(sum(r['outcome'] == 'out_of_scope' for r in adv), len(adv))}")  # noqa: E501
    missed = [r["qid"] for r in adv if r["outcome"] != "out_of_scope"]
    other = [r for r in rows if r["set"] != "advice"]
    false_trig = [r["qid"] for r in other if r["outcome"] == "out_of_scope"]
    lines.append(f"  - advice queries missed: {missed or 'none'}")
    lines.append(f"- false scope triggers on the other {len(other)} queries: {len(false_trig)} {false_trig or ''}")
    lines.append("")
    return lines


def faith_section(cond: str) -> list[str]:
    """Faithfulness lines for one condition from the LLM grades (pass 1) and the pass 2 agreement."""
    done = graded()
    units = [u["unit"] for u in faith_units(cond)]
    g1 = {u: int(done[u]["1"]) for u in units if "1" in done.get(u, {})}
    lines = [f"### Faithfulness, condition {cond} (LLM-graded, not human)", ""]
    if not units:
        return lines + ["- no answered responses, nothing to grade", ""]
    n = len(g1)
    lines.append(f"- units: {len(units)} sentences, graded {n}")
    lines.append(f"- supported (2): {fmt(sum(v == 2 for v in g1.values()), n)}")
    lines.append(f"- supported or partly (>= 1): {fmt(sum(v >= 1 for v in g1.values()), n)}")
    byq: dict[str, list[int]] = {}
    for u, v in g1.items():
        byq.setdefault(u.split(":")[1], []).append(v)
    allsup = sum(all(x == 2 for x in v) for v in byq.values())
    lines.append(f"- query level, every sentence supported: {fmt(allsup, len(byq))} (the honest interval: sentences of "
                 "one answer are not independent)")
    pairs = [(g1[u], int(done[u]["2"])) for u in g1 if "2" in done.get(u, {})]
    if pairs:
        same = sum(a == b for a, b in pairs)
        strict = sum((a == 2) == (b == 2) for a, b in pairs)
        lines.append(f"- second pass on a random 20 percent ({len(pairs)} units): exact agreement {fmt(same, len(pairs))}, "  # noqa: E501
                     f"agreement on supported vs not {fmt(strict, len(pairs))}")
    lines.append("")
    return lines


def cmd_metrics(args: argparse.Namespace) -> None:
    """Write results/step23_rag.md from the run files and the grades."""
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf8"))
    lines = ["# Step 23 RAG evaluation", "",
             "All faithfulness grades are LLM grades (claude-sonnet-5-5), not human grades. Frozen config: "
             "`data/rag/rag_config.json`. Retrieval: frozen E5b. Run once per condition. Not a fresh test: the ab "
             "queries and q45 to q61 were used in earlier abstention work and in selecting E5b.", "",
             f"Primary condition: {cfg['primary_condition']}. Threshold used: {cfg['threshold']} "
             f"(dev AUROC of the E5b top score {cfg['dev_auroc']:.3f}, gate usable: {cfg['gate_usable']}).", ""]
    for cond in CONDITIONS:
        if (RESULTS / f"step23_run_{cond}.jsonl").exists():
            lines += condition_section(cond)
            if cond != "B":
                lines += faith_section(cond)
    (RESULTS / "step23_rag.md").write_text("\n".join(lines), encoding="utf8")
    print("\n".join(lines))


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fit").set_defaults(fn=cmd_fit)
    p = sub.add_parser("run")
    p.add_argument("cond", choices=list(CONDITIONS))
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("faith-units")
    p.add_argument("cond", choices=["A1", "A2"])
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--pass-no", default="1")
    p.set_defaults(fn=cmd_faith_units)
    p = sub.add_parser("faith-record")
    p.add_argument("pairs", nargs="+")
    p.add_argument("--pass-no", default="1")
    p.add_argument("--model", required=True)
    p.set_defaults(fn=cmd_faith_record)
    sub.add_parser("regrade-sample").set_defaults(fn=cmd_regrade_sample)
    sub.add_parser("metrics").set_defaults(fn=cmd_metrics)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
