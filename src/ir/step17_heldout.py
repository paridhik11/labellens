"""Step 17f: the one held-out run of the frozen Step 17 config.

Reads qrels, never writes them. Refuses to run if the config, its data hashes or the
qrels hash do not match, and refuses to overwrite an existing report, so the held-out
half is scored once.

WHAT IS REPORTED
  - Primaries P1, P2, P3 (declared before the run): mean nDCG@10 of the variant and of its
    baseline, the paired difference with a 95% bootstrap interval, the raw two-sided p
    and the Holm-adjusted p over the three. Wins, losses and ties per query.
  - The same three again without q15, q24 and q55, the held-out queries that motivated
    failure-derived synonym groups (sensitivity check).
  - Secondary variants: descriptive differences and intervals, no p-values.
  - Expansion both ways (all groups vs CFR-definition groups only vs none).
  - The same frozen variants on the dev half, for contrast (tuned there, so optimistic).
  - The unjudged top-10 pairs of every variant, written to a separate CSV.

Run:  python -m src.ir.step17_heldout
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.ir.eval import load_chunks, load_qrels, load_query_rows
from src.ir.split import load_split
from src.ir.step14_report import holm_adjust, paired_bootstrap_ci
from src.ir.step17_config import check_config, file_sha256, load_config, spec_from_dict
from src.ir.step17_report import (
    LABEL,
    ModuleContext,
    Run,
    load_ce_model,
    run_spec,
    unjudged_rows,
    write_unjudged,
)

OUT = "results/step17_heldout.md"
UNJUDGED_OUT = "results/step17_unjudged_heldout.csv"


def fmt(x: float) -> str:
    return f"{x:.3f}"


def compare(run: Run, base: Run, qids: list[str]) -> dict:
    """Paired comparison of run against base on the given queries (nDCG@10, unjudged as 0)."""
    a, b = run.values("ndcg", qids), base.values("ndcg", qids)
    diff, lo, hi, p = paired_bootstrap_ci(a, b)
    cond = [x - y for x, y in zip(run.values("cond", qids), base.values("cond", qids), strict=True)]
    eps = 1e-9
    return {"mean": sum(a) / len(a), "base": sum(b) / len(b), "diff": diff, "lo": lo, "hi": hi,
            "p": p, "cond_diff": sum(cond) / len(cond),
            "wins": sum(x - y > eps for x, y in zip(a, b, strict=True)),
            "losses": sum(y - x > eps for x, y in zip(a, b, strict=True)),
            "ties": sum(abs(x - y) <= eps for x, y in zip(a, b, strict=True))}


def primary_table(cfg: dict, runs: dict[str, Run], qids: list[str]) -> tuple[list[str], list[dict]]:
    """Primary comparison table with raw and Holm-adjusted p over P1..P3."""
    prim = [v for v in cfg["variants"] if v["role"] == "primary"]
    res = [compare(runs[v["name"]], runs[v["vs"]], qids) for v in prim]
    holm = holm_adjust([r["p"] for r in res])
    lines = ["| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff "
             "| raw p | Holm p | wins / losses / ties |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for v, r, hp in zip(prim, res, holm, strict=True):
        lines.append(f"| {v['id']} | {v['name']} | {v['vs']} | {len(qids)} | {fmt(r['mean'])} "
                     f"| {fmt(r['base'])} | {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] "
                     f"| {r['cond_diff']:+.3f} | {r['p']:.4f} | {hp:.4f} "
                     f"| {r['wins']} / {r['losses']} / {r['ties']} |")
        r["holm"] = hp
    return lines, res


def descriptive_table(cfg: dict, runs: dict[str, Run], qids: list[str],
                      mod_qids: dict[str, list[str]], roles: tuple[str, ...]) -> list[str]:
    """Descriptive table (no p-values) for the variants whose role is in roles."""
    lines = ["| variant | vs | nDCG@10 | condensed | unjudged@10 | device | medicine "
             "| diff [95% CI] | wins / losses |", "|---|---|---|---|---|---|---|---|---|"]
    for v in cfg["variants"]:
        if v["role"] not in roles:
            continue
        r = runs[v["name"]]
        d, wl = "", ""
        if v["vs"]:
            c = compare(r, runs[v["vs"]], qids)
            d = f"{c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]"
            wl = f"{c['wins']} / {c['losses']}"
        lines.append(f"| {v['name']} | {v['vs'] or ''} | {fmt(r.mean('ndcg', qids))} "
                     f"| {fmt(r.mean('cond', qids))} | {fmt(r.mean('unj', qids))} "
                     f"| {fmt(r.mean('ndcg', mod_qids['device']))} "
                     f"| {fmt(r.mean('ndcg', mod_qids['medicine']))} | {d} | {wl} |")
    return lines


def movers(cfg: dict, runs: dict[str, Run], rows: list, motivating: set[str]) -> list[str]:
    """Per primary: the three biggest gains and losses by query."""
    info = {r.qid: r for r in rows}
    qids = [r.qid for r in rows]
    out = []
    for v in cfg["variants"]:
        if v["role"] != "primary":
            continue
        a, b = runs[v["name"]].values("ndcg", qids), runs[v["vs"]].values("ndcg", qids)
        diffs = sorted(zip(qids, (x - y for x, y in zip(a, b, strict=True)), strict=True),
                       key=lambda t: t[1])
        pick = [t for t in diffs[:3] if t[1] < 0] + [t for t in diffs[-3:][::-1] if t[1] > 0]
        out.append(f"- **{v['id']}** " + "; ".join(
            f"{q} ({info[q].qtype}, {info[q].module}{', motivating' if q in motivating else ''}) {d:+.3f}"
            for q, d in pick))
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 17f: the one held-out run.")
    ap.add_argument("--config", default="data/eval/step17_config.json")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--unjudged", default=UNJUDGED_OUT)
    a = ap.parse_args()
    t0 = time.time()

    cfg = load_config(a.config)
    problems = check_config(cfg)
    qpath = cfg["qrels"]["path"]
    if cfg["main_commit"] is None or cfg["qrels"]["sha256"] is None:
        problems.append("main_commit and qrels are not recorded in the config")
    elif file_sha256(qpath) != cfg["qrels"]["sha256"]:
        problems.append(f"{qpath} does not match the recorded hash")
    if Path(a.out).exists():
        problems.append(f"{a.out} exists: the held-out half is scored once")
    if problems:
        raise SystemExit("refusing to run:\n  " + "\n  ".join(problems))

    split = load_split("data/eval/split_t1.json")
    all_rows = {r.qid: r for r in load_query_rows("data/eval/queries_t1.tsv")}
    held = [all_rows[q] for q in split["heldout"]]
    dev = [all_rows[q] for q in split["dev"]]
    qrels = load_qrels(qpath)
    chunks = load_chunks("data/processed/regs.jsonl")
    texts = {c.chunk_id: c.text for c in chunks}
    ce_model, ce_cache = load_ce_model(), {}
    ctxs = {m: ModuleContext([c for c in chunks if c.module == m], ce_model, ce_cache)
            for m in ("device", "medicine")}

    specs = {v["name"]: spec_from_dict(v["spec"]) for v in cfg["variants"]}
    held_runs = {n: run_spec(s, held, ctxs, qrels) for n, s in specs.items()}
    dev_runs = {n: run_spec(s, dev, ctxs, qrels) for n, s in specs.items()}

    hq = [r.qid for r in held]
    dq = [r.qid for r in dev]

    def mod(rows: list) -> dict[str, list[str]]:
        return {m: [r.qid for r in rows if r.module == m] for m in ("device", "medicine")}

    sens = set(cfg["params"]["sensitivity_exclude_heldout"])
    hq_sens = [q for q in hq if q not in sens]
    motivating = sens

    prim, _ = primary_table(cfg, held_runs, hq)
    prim_s, _ = primary_table(cfg, held_runs, hq_sens)
    def name_of(pid: str) -> str:
        return next(v["name"] for v in cfg["variants"] if v["id"] == pid)

    p2 = name_of("P2")
    both_ways = ["| system | none | all groups | CFR groups only |", "|---|---|---|---|"]
    p2_none = "hybrid+stem+prefix+pb(top=1,beta=0.1,bm25)"
    p2_cfr = "hybrid+stem+prefix+exp(w=0.3,cfr,dense)+pb(top=1,beta=0.1,bm25)"
    for label, none, allg, cfr, base in (
            ("bm25 (w=0.5)", "bm25", name_of("P1"), "bm25+exp(w=0.5,cfr)", "bm25"),
            ("hybrid, BM25 half only (w=0.3)", "hybrid", None, "hybrid+exp(w=0.3,cfr,bm25side)", "hybrid"),
            ("P2 combination", p2_none, p2, p2_cfr, "hybrid")):
        def cell(n: str | None, base: str = base) -> str:
            if n is None or n not in held_runs:
                return "not in config"
            c = compare(held_runs[n], held_runs[base], hq)
            return f"{fmt(c['mean'])} ({c['diff']:+.3f} vs {base})"
        both_ways.append(f"| {label} | {cell(none)} | {cell(allg)} | {cell(cfr)} |")

    unj: list[dict] = []
    for r in held_runs.values():
        unj += unjudged_rows(r, held, qrels, texts, "heldout")
    write_unjudged(a.unjudged, unj)
    unique = sorted({(u["qid"], u["chunk_id"]) for u in unj})
    per_variant = {n: sum(1 for u in unj if u["variant"] == n) for n in held_runs}

    md = [
        "# Step 17f: held-out results of the frozen configuration", "",
        f"**{LABEL}.** Held-out half only: {len(hq)} answerable queries "
        f"({len(mod(held)['device'])} device, {len(mod(held)['medicine'])} medicine), seed 42 split. "
        "Settings were frozen on the dev half (`data/eval/step17_config.json`, "
        f"settings hash {cfg['settings_sha256'][:12]}) and scored here once. "
        f"Qrels: `{qpath}`, {cfg['qrels']['rows']} rows, main commit `{cfg['main_commit'][:10]}`. "
        "Depth 50, nDCG@10, chunk level, each query searched in its own module.", "",
        "## Read this first", "",
        "- **These are LLM grades, not human grades.** The LLM is stricter than humans at the 0/1 boundary "
        "(Step 13), and all numbers inherit that.",
        f"- **n = {len(hq)}.** Intervals are wide; a difference whose interval contains 0 is not evidence of a "
        "gain. Medicine has too few queries to say anything on its own.",
        "- **Held-out was not entirely unseen for stemming and the BGE prefix.** The Step 15b ablation had "
        "already evaluated bm25_stem, hybrid_stem, dense_prefix and hybrid_prefix on all 62 queries, "
        "including this half. Their settings were not tuned on it (stemming and the prefix have no "
        "parameters), but P3 and the stem and prefix parts of P2 were chosen with that knowledge in "
        "the project, so treat them as less independent than P1.",
        f"- **Failure-derived synonym groups.** {', '.join(sorted(sens))} are held-out queries that "
        "motivated groups in the lexicon, so P1 and P2 may be favoured on them. Every primary is therefore also "
        "reported without these three queries.",
        "- The config was frozen against the 2531-pair qrels of the dev run; held-out is scored on the "
        f"final {cfg['qrels']['rows']}-pair qrels. The variants and settings are the same.",
        "- Holm adjusts over the three declared primaries only; secondary rows have no p-values.", "",
        f"## Primaries (Holm over P1, P2, P3), all {len(hq)} held-out queries", ""] + prim + [
        "", f"## Primaries without q15, q24 and q55 ({len(hq_sens)} queries)", ""] + prim_s + [
        "", "Biggest query-level changes (nDCG@10 difference), all held-out queries:", ""] + movers(
        cfg, held_runs, held, motivating) + [
        "", "## Secondary variants and baselines (descriptive, no p-values)", ""] + descriptive_table(
        cfg, held_runs, hq, mod(held), ("baseline", "secondary")) + [
        "", "## Expansion both ways (nDCG@10, held-out)", ""] + both_ways + [
        "", "The P2 combination has the CFR-only version and the no-expansion version as secondaries; the "
        "CFR-only P2 structure was not run on dev.", "",
        f"## The same frozen variants on the dev half ({len(dq)} queries; tuned there, so optimistic)", ""
    ] + descriptive_table(cfg, dev_runs, dq, mod(dev), ("baseline", "primary", "secondary")) + [
        "", "## Unjudged pairs on held-out", "",
        f"`{a.unjudged}`: {len(unj)} rows, **{len(unique)} unique (query, chunk) pairs** unjudged in the "
        "final qrels, over all config variants. Nothing was graded and the config was not changed.", ""]
    md += [f"- {n}: {c} rows" for n, c in per_variant.items() if c]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\n[{len(specs)} variants x 2 halves, {time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
