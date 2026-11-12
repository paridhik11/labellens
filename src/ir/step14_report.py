"""Step 14 reports on the LLM-assessed qrels (data/eval/qrels_t1_llm.tsv).

Usage (repo root):
  python -m src.ir.step14_report --part results   # results/step14_results.md
  python -m src.ir.step14_report --part types     # results/step14_by_type.md
  python -m src.ir.step14_report --part all

Every table is built from LLM grades, not human grades. Systems are built per
module (device queries search device chunks, medicine queries search medicine
chunks), the same way the pool was made. Bootstrap resamples queries, 10000
times, seed 42.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.eval import (
    METRIC_NAMES,
    build_systems,
    evaluate,
    evaluate_no_answer,
    find_corpus_gaps,
    load_chunks,
    load_qrels,
    load_query_rows,
    mean_top1_score,
    no_answer_to_markdown,
    split_no_answer,
)

BASELINE = "bm25"
LABEL = "LLM-assessed qrels (claude-sonnet-5-5), not human grades"
METRIC_TITLES = {"ndcg": "nDCG@10", "recall": "Recall@20", "mrr": "MRR", "map": "MAP"}
QTYPES = ("direct", "vocab_mismatch", "symbol", "field_req", "change_impact")
SMALL_N = 5

PerQuery = dict[str, dict[str, list[float]]]  # system -> metric -> values aligned to qids


def paired_bootstrap_ci(
    a: list[float], b: list[float], n: int = 10000, seed: int = 42, level: float = 0.95
) -> tuple[float, float, float, float]:
    """Two-sided paired bootstrap of the mean per-query difference a - b.

    Resamples the queries with replacement n times and takes the mean difference
    of each resample. Returns (mean_diff, low, high, p). The interval is the
    percentile interval of those means. The p-value is twice the smaller tail
    share of the resampled means on either side of 0, capped at 1, so its
    smallest nonzero value is about 2/n. This is a percentile bootstrap p-value,
    not a permutation test. Identical inputs give diff 0 and p 1.
    Returns NaNs when there are no queries.
    """
    if len(a) != len(b):
        raise ValueError("a and b must have the same length")
    m = len(a)
    if m == 0:
        nan = float("nan")
        return nan, nan, nan, nan
    diffs = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    means = diffs[rng.integers(0, m, size=(n, m))].mean(axis=1)
    lo, hi = np.quantile(means, [(1 - level) / 2, (1 + level) / 2])
    p_le = float((means <= 0).mean())
    p_ge = float((means >= 0).mean())
    p = min(1.0, 2 * min(p_le, p_ge))
    return float(diffs.mean()), float(lo), float(hi), p


def holm_adjust(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in the input order.

    Sort the m p-values ascending. The adjusted value for the j-th smallest
    (j = 1..m) is (m - j + 1) * p, capped at 1, and never lower than the
    adjusted value before it, so the adjusted p-values keep the same order.
    Controls the chance of any false positive in the family at the stated level.
    """
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def holm_family(data: dict[str, dict]) -> list[dict]:
    """The nDCG@10 comparisons vs bm25 as one family (module x level x system).

    Uses the main query set (corpus gaps excluded). With 2 modules, 2 levels
    and 3 non-baseline systems the family has 12 members. Each row has the mean
    difference, 95% interval, raw p and the Holm-adjusted p.
    """
    rows: list[dict] = []
    for mod in sorted(data):
        d = data[mod]
        kept = [q for q in d["qids"] if q not in set(d["gaps"])]
        for level in ("chunk", "section"):
            sub = select(d[level], d["qids"], kept)
            for s in sub:
                if s == BASELINE:
                    continue
                diff, lo, hi, p = paired_bootstrap_ci(sub[s]["ndcg"], sub[BASELINE]["ndcg"])
                rows.append(
                    {"module": mod, "level": level, "system": s, "n": len(kept),
                     "diff": diff, "lo": lo, "hi": hi, "p": p}
                )
    for r, adj in zip(rows, holm_adjust([r["p"] for r in rows]), strict=True):
        r["p_holm"] = adj
    return rows


def holm_table(rows: list[dict]) -> list[str]:
    """Markdown table for the Holm family, with the raw and adjusted p-values."""
    lines = [
        "| Module | Level | System vs bm25 | n | nDCG@10 diff [95% CI] | raw p | Holm-adjusted p |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['module']} | {r['level']} | {r['system']} | {r['n']} "
            f"| {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] "
            f"| {fmt_p(r['p'])[2:]} | {fmt_p(r['p_holm'])[2:]} |"
        )
    return lines


def fmt_p(p: float) -> str:
    """Formats a bootstrap p-value as 'p=0.123'; below the resolution it is 'p<0.0002'."""
    if p != p:
        return "p n/a"
    return "p<0.0002" if p < 0.0002 else f"p={p:.3f}"


def mean(values: list[float]) -> float:
    """Mean of a list, NaN when empty."""
    return sum(values) / len(values) if values else float("nan")


def select(per_query: PerQuery, qids: list[str], keep: list[str]) -> PerQuery:
    """Restricts per-query metric lists (aligned to qids) to the qids in keep."""
    pos = [i for i, q in enumerate(qids) if q in set(keep)]
    return {
        s: {m: [vals[i] for i in pos] for m, vals in rows.items()}
        for s, rows in per_query.items()
    }


def means_table(per_query: PerQuery) -> list[str]:
    """Markdown table of mean metrics per system."""
    lines = [
        "| System | nDCG@10 | Recall@20 | MRR | MAP |",
        "|---|---|---|---|---|",
    ]
    for s, rows in per_query.items():
        cells = " | ".join(f"{mean(rows[m]):.3f}" for m in METRIC_NAMES)
        lines.append(f"| {s} | {cells} |")
    return lines


def diff_table(per_query: PerQuery, baseline: str = BASELINE) -> list[str]:
    """Paired bootstrap difference vs the baseline: diff [95% CI] and p, per metric."""
    lines = [
        "| System vs " + baseline + " | " + " | ".join(METRIC_TITLES[m] for m in METRIC_NAMES) + " |",
        "|---|---|---|---|---|",
    ]
    for s, rows in per_query.items():
        if s == baseline:
            continue
        cells = []
        for m in METRIC_NAMES:
            d, lo, hi, p = paired_bootstrap_ci(rows[m], per_query[baseline][m])
            cells.append(f"{d:+.3f} [{lo:+.3f}, {hi:+.3f}] {fmt_p(p)}")
        lines.append(f"| {s} | " + " | ".join(cells) + " |")
    return lines


def module_data(
    chunks: list[Chunk],
    systems: list[Retriever],
    rows: list,
    qrels: dict[str, dict[str, int]],
) -> dict:
    """Runs all systems on one module's answerable graded queries (gaps kept in).

    Returns a dict with the query lists, the gap qids and per-query metrics at
    chunk and section level, each aligned to data['qids'].
    """
    answerable, no_answer = split_no_answer(rows)
    queries = {r.qid: r.query for r in answerable if r.qid in qrels}
    qids = list(queries)
    c2s = {c.chunk_id: (c.section or c.chunk_id) for c in chunks}
    _, chunk_pq = evaluate(systems, queries, qrels)
    _, sec_pq = evaluate(systems, queries, qrels, chunk_to_section=c2s)
    na_queries = {r.qid: r.query for r in no_answer if r.qid in qrels}
    return {
        "qids": qids,
        "queries": queries,
        "gaps": find_corpus_gaps(qids, qrels),
        "chunk": chunk_pq,
        "section": sec_pq,
        "na_queries": na_queries,
        "systems": systems,
    }


def results_report(data: dict[str, dict], qrels: dict[str, dict[str, int]]) -> str:
    """Builds the 14a markdown: main tables with and without corpus gaps, no_answer."""
    out = [
        "# Step 14a: results table",
        "",
        f"**All tables below use {LABEL}.** They are not human relevance grades. In Step 13 the",
        "LLM was stricter than the humans at the 0/1 boundary and agreed with Pari at weighted kappa",
        "0.746 (linear), measured on a 15-query human sample, so absolute scores here may differ",
        "from human-graded scores. Compare systems with each other, not with other papers.",
        "",
        "## How to read this",
        "- Systems: tfidf, bm25, dense (bge-small-en-v1.5 + FAISS), hybrid (RRF of bm25 and dense).",
        "- Device and medicine are separate tables (separate corpora, separate queries).",
        "- Chunk level ranks chunks. Section level takes the best chunk score per section and the",
        "  best grade per section.",
        "- no_answer queries are excluded from every average here and reported at the end.",
        "- Corpus gaps are answerable queries where no chunk has an LLM grade >= 1. Every system",
        "  scores 0 on them. Each table is shown without them (the main table) and with them.",
        "- Each difference vs bm25 is a paired bootstrap over queries (10000 resamples, seed 42):",
        "  mean difference, 95% percentile interval, and a two-sided percentile bootstrap p-value.",
        "  p-values below 0.0002 are the resolution limit of 10000 resamples, not exact zeros.",
        "  When most per-query differences are exactly 0, many resamples have a mean of exactly 0.",
        "  Those ties count in both tails, so p is conservative and an interval can end at +0.000",
        "  while p is large.",
        "",
        "## Multiple comparisons",
        "Each table has 12 comparisons against bm25 (3 systems x 4 metrics). With 2 modules x 2",
        "levels that is 48 comparisons in this file. **The p-values in the module tables are not",
        "corrected for multiple comparisons.** **nDCG@10 is the primary metric**; Recall@20, MRR and MAP are",
        "secondary and should be read as supporting detail. With only 17 to 40 queries per table,",
        "an uncorrected p just under 0.05 is weak evidence.",
        "",
        "The module tables further down keep the raw p-values. The table below treats the 12",
        "nDCG@10 comparisons vs bm25 (2 modules x 2 levels x 3 systems) as one family and adds a",
        "Holm step-down adjusted p. Holm controls the chance of any false positive across those 12",
        "and is never smaller than the raw p. The 36 secondary-metric comparisons stay uncorrected.",
        "",
        f"## nDCG@10 vs bm25, Holm-adjusted over 12 comparisons. {LABEL}",
        "",
    ]
    out += holm_table(holm_family(data)) + [""]
    for mod in sorted(data):
        d = data[mod]
        gaps = d["gaps"]
        qids = d["qids"]
        kept = [q for q in qids if q not in set(gaps)]
        out += [f"## {mod.capitalize()} module", ""]
        out += [
            f"- Answerable graded queries: {len(qids)}",
            f"- Corpus-gap queries ({len(gaps)}): {', '.join(gaps) if gaps else 'none'}",
            f"- Queries in the main table (gaps excluded): {len(kept)}",
        ]
        if not gaps:
            out.append(
                "- There are no gap queries in this module, so the with-gaps table would be "
                "identical to the main table and is not repeated."
            )
        out.append("")
        for level in ("chunk", "section"):
            pq = d[level]
            variants = [("gaps excluded, main", kept)]
            if gaps:
                variants.append(("gaps included", qids))
            for tag, keep in variants:
                sub = select(pq, qids, keep)
                out += [
                    f"### {mod.capitalize()}, {level} level, {tag} "
                    f"({len(keep)} queries). {LABEL}",
                    "",
                ]
                out += means_table(sub) + [""]
                out += diff_table(sub) + [""]
    out += ["## no_answer queries (reported separately, not in any average above)", ""]
    out += [
        "Share of no_answer queries with a grade >= 1 chunk in the top 10 (related context is",
        "expected and not an error) and with a grade 2 chunk (which would suggest a mislabelled",
        f"query). Scores are comparable within one system only. {LABEL}.",
        "",
    ]
    for mod in sorted(data):
        d = data[mod]
        if not d["na_queries"]:
            out += [f"### {mod.capitalize()}: no graded no_answer queries", ""]
            continue
        res = evaluate_no_answer(d["systems"], d["na_queries"], qrels)
        ans_top1 = mean_top1_score(d["systems"], {q: d["queries"][q] for q in d["qids"]})
        out += [
            f"### {mod.capitalize()} ({len(d['na_queries'])} queries: "
            f"{', '.join(d['na_queries'])})",
            "",
            no_answer_to_markdown(res, ans_top1),
            "",
        ]
    return "\n".join(out)


def type_table(
    rows: list,
    kept: list[str],
    pq: PerQuery,
    qids: list[str],
    gaps: list[str],
) -> list[str]:
    """nDCG@10 per query type x system with the query count in every cell.

    Only qids in kept (answerable, graded, not a gap) count. Types with fewer
    than SMALL_N queries are flagged because one query moves the mean a lot.
    """
    by_type: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        if r.qid in set(kept):
            by_type[r.qtype].append(r.qid)
    gap_by_type: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        if r.qid in set(gaps):
            gap_by_type[r.qtype].append(r.qid)
    names = list(pq)
    lines = [
        "| Query type | n | gaps left out | " + " | ".join(names) + " | note |",
        "|---|---|---|" + "---|" * len(names) + "---|",
    ]
    for t in QTYPES:
        tq = by_type.get(t, [])
        if not tq:
            lines.append(
                f"| {t} | 0 | {len(gap_by_type.get(t, []))} | " + " | ".join("n/a" for _ in names)
                + " | no queries |"
            )
            continue
        sub = select(pq, qids, tq)
        cells = " | ".join(f"{mean(sub[s]['ndcg']):.3f}" for s in names)
        note = f"n<{SMALL_N}, descriptive only" if len(tq) < SMALL_N else ""
        gl = gap_by_type.get(t, [])
        lines.append(f"| {t} | {len(tq)} | {len(gl)} | {cells} | {note} |")
    return lines


def types_report(data: dict[str, dict], rows_by_module: dict[str, list]) -> str:
    """Builds the 14b markdown: nDCG@10 by query type, chunk level, per module."""
    out = [
        "# Step 14b: results by query type",
        "",
        f"**All tables use {LABEL}.** Chunk level only, nDCG@10 only.",
        "",
        "## How to read this",
        "- Each cell is the mean nDCG@10 of one system over the queries of one type, and **n is the",
        "  number of queries behind the row**. Corpus-gap queries (no chunk graded >= 1) and",
        "  no_answer queries are left out, the same rule as the main table in step14_results.md.",
        "  'gaps left out' counts the gap queries removed from that row.",
        f"- Rows with n<{SMALL_N} are flagged. With so few queries one query moves the mean by up to",
        "  1/n (0.25 at n=4, 1.0 at n=1), so those rows are descriptive and say nothing about",
        "  which system is better. Rows with n of 5 to 11 are also noisy.",
        "- No significance tests are run per type: the cells are too small, and 4 systems x 5 types x",
        "  2 modules would add many more uncorrected comparisons.",
        "",
    ]
    for mod in sorted(data):
        d = data[mod]
        gaps = d["gaps"]
        kept = [q for q in d["qids"] if q not in set(gaps)]
        out += [
            f"## {mod.capitalize()} module ({len(kept)} queries after dropping "
            f"{len(gaps)} gap(s): {', '.join(gaps) if gaps else 'none'})",
            "",
        ]
        out += type_table(rows_by_module[mod], kept, d["chunk"], d["qids"], gaps) + [""]
    return "\n".join(out)


def build_all(
    corpus: str, queries: str, qrels_path: str, with_dense: bool
) -> tuple[dict[str, dict], dict[str, list], dict[str, dict[str, int]]]:
    """Builds systems per module and evaluates them. Returns (data, rows by module, qrels)."""
    all_chunks = load_chunks(corpus)
    qrels = load_qrels(qrels_path)
    all_rows = load_query_rows(queries)
    data: dict[str, dict] = {}
    rows_by_module: dict[str, list] = {}
    for mod in sorted({c.module for c in all_chunks if c.module}):
        chunks = [c for c in all_chunks if c.module == mod]
        systems = build_systems(
            [(c.chunk_id, c.text) for c in chunks], with_dense=with_dense, chunks=chunks
        )
        rows = [r for r in all_rows if r.module == mod]
        rows_by_module[mod] = rows
        data[mod] = module_data(chunks, systems, rows, qrels)
    return data, rows_by_module, qrels


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 14 reports on LLM-assessed qrels.")
    ap.add_argument("--part", choices=["results", "types", "all"], default="all")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--no-dense", action="store_true")
    a = ap.parse_args()

    data, rows_by_module, qrels = build_all(a.corpus, a.queries, a.qrels, not a.no_dense)
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.part in ("results", "all"):
        text = results_report(data, qrels)
        (out_dir / "step14_results.md").write_text(text + "\n", encoding="utf-8")
        print(text)
    if a.part in ("types", "all"):
        text = types_report(data, rows_by_module)
        (out_dir / "step14_by_type.md").write_text(text + "\n", encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
