"""One-shot scoring of the web_faq fresh set (Step 18f).

Scores plain hybrid, hybrid+stem+prefix and the frozen E5b on the 30 web_faq fresh queries, using the LLM
grades in data/eval/qrels_fresh_llm.tsv (claude-sonnet-5-5, not human grades). chunk_derived queries were
not graded and are not scored. The script checks the frozen config first and refuses to run if its output
already exists, so the fresh set is scored once.

    python -m src.ir.step18_final
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.ir.eval import load_chunks, load_qrels
from src.ir.metrics import recall_at_k
from src.ir.step14_report import paired_bootstrap_ci
from src.ir.step17_report import query_metrics
from src.ir.step18_config import CORPUS, check_config, e5b, load_config
from src.ir.step18_systems import PLAIN_HYBRID, STEM_PREFIX_HYBRID, Context18, Sys18

CANDIDATES = "data/eval/fresh_candidates.csv"
QRELS = "data/eval/qrels_fresh_llm.tsv"
OUT_MD = Path("results/step18_fresh_web.md")
OUT_JSON = Path("results/step18_fresh_web.json")
DEPTH = 50
LABEL = "LLM-assessed qrels (claude-sonnet-5-5), not human grades"
SYSTEMS: dict[str, Sys18] = {"plain hybrid": PLAIN_HYBRID, "hybrid+stem+prefix": STEM_PREFIX_HYBRID, "E5b": e5b()}


def score(ranked: list[str], rels: dict[str, int]) -> dict[str, float]:
    """nDCG@10 (unjudged 0), condensed nDCG@10, unjudged@10, Recall@20."""
    m = query_metrics(ranked, rels)
    m["recall20"] = recall_at_k(ranked, rels, 20)
    return m


def mean(xs: list[float]) -> float:
    """Mean, 0 for an empty list."""
    return sum(xs) / len(xs) if xs else 0.0


def table(runs: dict, qids: list[str]) -> list[str]:
    """Absolute-number table for one set of queries."""
    out = ["| system | nDCG@10 | nDCG@10 condensed | Recall@20 (pool-based) | unjudged@10 |", "|---|---|---|---|---|"]
    for name, per in runs.items():
        v = {k: mean([per[q][k] for q in qids]) for k in ("ndcg", "cond", "recall20", "unj")}
        out.append(f"| {name} | {v['ndcg']:.3f} | {v['cond']:.3f} | {v['recall20']:.3f} | {v['unj']:.3f} |")
    return out


def gain_rows(runs: dict, qids: list[str], target: str) -> list[str]:
    """Paired bootstrap gains of `target` over each baseline, per metric."""
    out = ["| vs | metric | mean gain | 95% CI | p (two-sided, unadjusted) |", "|---|---|---|---|---|"]
    for base in ("plain hybrid", "hybrid+stem+prefix"):
        for key, label in (("ndcg", "nDCG@10"), ("cond", "nDCG@10 condensed"), ("recall20", "Recall@20")):
            d, lo, hi, p = paired_bootstrap_ci([runs[target][q][key] for q in qids], [runs[base][q][key] for q in qids])
            out.append(f"| {base} | {label} | {d:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {p:.3f} |")
    return out


def main() -> None:
    """Checks the frozen config, scores once and writes the report."""
    if OUT_MD.exists():
        raise SystemExit(f"{OUT_MD} exists; the fresh set is scored once")
    cfg = load_config()
    bad = check_config(cfg)
    if bad:
        raise SystemExit("frozen config does not match: " + "; ".join(bad))
    rows = [r for r in csv.DictReader(open(CANDIDATES, encoding="utf-8")) if r["qid"].startswith("fw")]
    qrels = load_qrels(QRELS)
    chunks = load_chunks(CORPUS)
    ctx = {m: Context18([c for c in chunks if c.module == m]) for m in ("device", "medicine")}
    runs: dict[str, dict[str, dict[str, float]]] = {n: {} for n in SYSTEMS}
    ranked_all: dict[str, dict[str, list[str]]] = {n: {} for n in SYSTEMS}
    for r in rows:
        for name, system in SYSTEMS.items():
            ranked = [h.doc_id for h in ctx[r["module"]].build(system).search(r["text"], k=DEPTH)]
            ranked_all[name][r["qid"]] = ranked
            runs[name][r["qid"]] = score(ranked, qrels.get(r["qid"], {}))
    gaps = [r["qid"] for r in rows if not any(g >= 1 for g in qrels.get(r["qid"], {}).values())]
    answerable = [r["qid"] for r in rows if r["qid"] not in gaps]
    by_module = {m: [r["qid"] for r in rows if r["module"] == m and r["qid"] in answerable]
                 for m in ("device", "medicine")}
    no_two = [r["qid"] for r in rows if r["qid"] in answerable and not any(g == 2 for g in qrels[r["qid"]].values())]
    md = [
        "# Step 18f: web_faq fresh set, scored once", "",
        f"**{LABEL}.** Config `data/eval/step18_config.json` (settings_sha256 `{cfg['settings_sha256'][:16]}...`), "
        "checked before scoring. 30 web_faq queries rewritten from real FDA Q&A (source URLs in "
        "`data/eval/fresh_candidates.csv`). chunk_derived queries (written by the same model that grades) were "
        "not graded and are NOT scored here.", "",
        "Caveats: the pool is the top 10 of the three systems, so nDCG@10 is fully judged (unjudged@10 shows 0) "
        "but Recall@20 only counts relevant chunks that were pooled, so it is optimistic. A system that ranks a "
        "relevant chunk at 11 to 20 that nobody graded gets no credit and the denominator ignores it. Grades "
        "come from one LLM that is stricter than humans at the 0/1 boundary.", "",
        f"Queries: {len(rows)}; corpus gaps (no chunk graded >= 1, excluded from averages): "
        f"{', '.join(gaps) or 'none'}; answerable with no grade-2 chunk: {', '.join(no_two) or 'none'}. "
        f"Scored: {len(answerable)} (device {len(by_module['device'])}, medicine {len(by_module['medicine'])}).", "",
        "## Absolute numbers, all answerable queries", "", *table(runs, answerable), "",
        "## Gains of E5b with paired bootstrap (10,000 resamples, seed 42)", "",
        *gain_rows(runs, answerable, "E5b"), "",
        "Also hybrid+stem+prefix over plain hybrid:", "",
        "| metric | mean gain | 95% CI | p |", "|---|---|---|---|",
    ]
    for key, label in (("ndcg", "nDCG@10"), ("cond", "nDCG@10 condensed"), ("recall20", "Recall@20")):
        d, lo, hi, p = paired_bootstrap_ci([runs["hybrid+stem+prefix"][q][key] for q in answerable],
                                           [runs["plain hybrid"][q][key] for q in answerable])
        md.append(f"| {label} | {d:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {p:.3f} |")
    for m in ("device", "medicine"):
        md += ["", f"## {m} ({len(by_module[m])} queries)", "", *table(runs, by_module[m]), "",
               *gain_rows(runs, by_module[m], "E5b")]
    md += ["", "## Per query nDCG@10 (unjudged = 0)", "", "| qid | module | type | plain | h+s+p | E5b |",
           "|---|---|---|---|---|---|"]
    for r in rows:
        q = r["qid"]
        if q in answerable:
            md.append(f"| {q} | {r['module']} | {r['type']} | {runs['plain hybrid'][q]['ndcg']:.2f} | "
                      f"{runs['hybrid+stem+prefix'][q]['ndcg']:.2f} | {runs['E5b'][q]['ndcg']:.2f} |")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"runs": runs, "gaps": gaps}, indent=1), encoding="utf-8")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
