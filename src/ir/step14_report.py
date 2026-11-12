"""Step 14 reports on the LLM-assessed qrels (data/eval/qrels_t1_llm.tsv).

Usage (repo root):
  python -m src.ir.step14_report --part results   # results/step14_results.md
  python -m src.ir.step14_report --part types     # results/step14_by_type.md
  python -m src.ir.step14_report --part failures  # results/step14_failures.md
  python -m src.ir.step14_report --part kappa     # results/step14_kappa_ci.md
  python -m src.ir.step14_report --part all

Every table is built from LLM grades, not human grades. Systems are built per
module (device queries search device chunks, medicine queries search medicine
chunks), the same way the pool was made. Bootstrap resamples queries, 10000
times, seed 42.
"""
from __future__ import annotations

import argparse
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.eval import (
    METRIC_NAMES,
    NO_ANSWER,
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
from src.ir.grade_compare import (
    HUMAN_PATHS,
    LLM_PATH,
    agreement_report,
    load_human_grades,
    load_llm_grades,
    merge_human,
)
from src.ir.tokenizer import tokenize

BASELINE = "bm25"
LABEL = "LLM-assessed qrels (claude-sonnet-5-5), not human grades"
METRIC_TITLES = {"ndcg": "nDCG@10", "recall": "Recall@20", "mrr": "MRR", "map": "MAP"}
QTYPES = ("direct", "vocab_mismatch", "symbol", "field_req", "change_impact")
SMALL_N = 5
CI_MIN_N = 8  # by-type cells with at least this many queries get a bootstrap interval

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


def bootstrap_mean_interval(
    values: list[float], n: int = 10000, seed: int = 42, level: float = 0.95
) -> tuple[float, float, float]:
    """Mean of per-query values with a percentile bootstrap interval over queries.

    Returns (mean, low, high). NaNs when values is empty.
    """
    m = len(values)
    if m == 0:
        nan = float("nan")
        return nan, nan, nan
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = arr[rng.integers(0, m, size=(n, m))].mean(axis=1)
    lo, hi = np.quantile(means, [(1 - level) / 2, (1 + level) / 2])
    return float(arr.mean()), float(lo), float(hi)


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
        "chunks": chunks,
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
        cell_list = []
        for s in names:
            if len(tq) >= CI_MIN_N:
                m_, lo, hi = bootstrap_mean_interval(sub[s]["ndcg"])
                cell_list.append(f"{m_:.3f} [{lo:.3f}, {hi:.3f}]")
            else:
                cell_list.append(f"{mean(sub[s]['ndcg']):.3f}")
        cells = " | ".join(cell_list)
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
        "  which system is better. Rows with n of 5 to 7 are also noisy and have no interval.",
        f"- Rows with n>={CI_MIN_N} show the mean with a bootstrap 95% interval in brackets (10000",
        "  resamples of the queries in that row, seed 42). The intervals are for each system's own",
        "  mean, not for a difference between systems: overlapping intervals do not mean 'no",
        "  difference' and non-overlapping ones are not a significance test, because all systems",
        "  are scored on the same queries.",
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


DEEP_K = 100  # depth used to find the first relevant chunk of a failed query
SNIPPET = 110


def part_of(chunk_id: str) -> str:
    """CFR part of a chunk id such as fda_21cfr801_s801.1_c1 -> '21cfr801'."""
    bits = chunk_id.split("_")
    return bits[1] if len(bits) > 1 else chunk_id


def section_of(chunk_id: str) -> str:
    """Section token of a chunk id such as fda_21cfr801_s801.1_c1 -> 's801.1'."""
    bits = chunk_id.split("_")
    return bits[2] if len(bits) > 2 else chunk_id


def term_overlap(query: str, text: str) -> float:
    """Share of the unique query terms (stopwords removed, light stemming) found in text."""
    q = set(tokenize(query, stem=True))
    if not q:
        return 0.0
    return len(q & set(tokenize(text, stem=True))) / len(q)


def first_relevant_rank(ranked: list[str], rels: dict[str, int]) -> int | None:
    """1-based rank of the first chunk with grade >= 1, or None if absent."""
    for i, d in enumerate(ranked, start=1):
        if rels.get(d, 0) >= 1:
            return i
    return None


def hypotheses(
    query: str,
    ranked: list[str],
    rels: dict[str, int],
    text_of: dict[str, str],
) -> list[str]:
    """Likely causes of a poor ranking, derived only from checks on the data.

    These are hypotheses, not verified causes. Checks, each reported with its numbers:
      not retrieved / ranked low: where the first chunk graded >= 1 sits in the top DEEP_K.
      wrong part: the top 3 chunks all come from CFR parts that hold no relevant chunk.
      chunk boundary: a top-3 chunk graded 0 shares a section with a relevant chunk.
      vocabulary: share of query terms present in the best-matching top-grade chunk.
    """
    out: list[str] = []
    top = max(rels.values(), default=0)
    best = [d for d, g in rels.items() if g == top and top >= 1]
    rel_all = [d for d, g in rels.items() if g >= 1]
    if not rel_all:
        return ["no chunk graded >= 1 for this query (corpus gap)"]
    r = first_relevant_rank(ranked[:DEEP_K], rels)
    top3 = ranked[:3]
    if r is None:
        out.append(f"relevant chunks not retrieved in the top {DEEP_K}")
    elif r > 3:
        out.append(f"first relevant chunk is at rank {r}, below the top 3 shown")
    rel_parts = {part_of(d) for d in rel_all}
    top_parts = {part_of(d) for d in top3}
    if top3 and not (top_parts & rel_parts):
        out.append(
            f"wrong part: top 3 come from {', '.join(sorted(top_parts))}; relevant chunks are in "
            f"{', '.join(sorted(rel_parts))}"
        )
    rel_secs = {(part_of(d), section_of(d)) for d in rel_all}
    near = [d for d in top3 if rels.get(d, 0) == 0 and (part_of(d), section_of(d)) in rel_secs]
    if near:
        out.append(
            f"chunk boundary: {', '.join(near)} is graded 0 but shares a section with a relevant chunk"
        )
    if best:
        ov = max(term_overlap(query, text_of[d]) for d in best if d in text_of)
        if ov < 0.5:
            out.append(
                f"vocabulary: only {ov:.0%} of the query terms occur in the best relevant chunk"
            )
    return out or ["no cause identified by these checks (query terms and sections look compatible)"]


def failure_data(data: dict[str, dict], qrels: dict[str, dict[str, int]], rows_by_module: dict[str, list]) -> dict:
    """Per-system per-query nDCG@10 (chunk level, gaps excluded) with module and type labels.

    Returns {'rows': list of dicts (qid, module, qtype, query, ndcg {system: value})},
    and the system names in order.
    """
    rows: list[dict] = []
    names: list[str] = []
    for mod in sorted(data):
        d = data[mod]
        qtype = {r.qid: r.qtype for r in rows_by_module[mod]}
        names = list(d["chunk"])
        for i, qid in enumerate(d["qids"]):
            if qid in set(d["gaps"]):
                continue
            rows.append(
                {
                    "qid": qid,
                    "module": mod,
                    "qtype": qtype.get(qid, ""),
                    "query": d["queries"][qid],
                    "ndcg": {s: d["chunk"][s]["ndcg"][i] for s in names},
                }
            )
    return {"rows": rows, "names": names}


def zero_ties(fd: dict) -> list[str]:
    """Table of how many answerable queries score exactly 0 nDCG@10 per system."""
    names = fd["names"]
    lines = [
        "| Scope | queries | " + " | ".join(names) + " | all four 0 |",
        "|---|---|" + "---|" * len(names) + "---|",
    ]
    for scope in ("device", "medicine", "both"):
        rows = [r for r in fd["rows"] if scope == "both" or r["module"] == scope]
        counts = [sum(1 for r in rows if r["ndcg"][s] == 0) for s in names]
        all_zero = sum(1 for r in rows if all(r["ndcg"][s] == 0 for s in names))
        lines.append(
            f"| {scope} | {len(rows)} | " + " | ".join(str(c) for c in counts) + f" | {all_zero} |"
        )
    return lines


def failures_report(
    data: dict[str, dict], qrels: dict[str, dict[str, int]], rows_by_module: dict[str, list]
) -> str:
    """Builds the 14c markdown: ties at 0, all-four-zero queries, worst 5 per system."""
    fd = failure_data(data, qrels, rows_by_module)
    names = fd["names"]
    sys_by_mod = {m: {s.name: s for s in data[m]["systems"]} for m in data}
    text_of: dict[str, str] = {}
    for m in data:
        text_of.update({c.chunk_id: c.text for c in data[m]["chunks"]})

    def ranked(system: str, mod: str, qid: str, k: int) -> list[str]:
        hits = sys_by_mod[mod][system].search(data[mod]["queries"][qid], k=k)
        return [h.doc_id for h in hits]

    out = [
        "# Step 14c: failure analysis",
        "",
        f"**All tables use {LABEL}.** Chunk level, nDCG@10, answerable queries only (no_answer",
        "queries and corpus gaps left out; there are no gaps). Device and medicine systems are built",
        "per module, so each query is searched in its own module's chunks.",
        "",
        "## How to read this",
        "- Worst queries are ranked by nDCG@10 ascending, ties broken by qid. The tie table below",
        "  gives the number of queries at exactly 0 per system. When a system has fewer than 5 such",
        "  queries, the list continues with the lowest non-zero scores, so some entries are poor",
        "  rather than failed. If a system had 5 or more zeros, the 5 shown would be the first 5 in",
        "  qid order and would not rank how badly they failed.",
        "- Grades come from the LLM qrels. 'unjudged' means the chunk is not in the pool and is",
        "  treated as grade 0 by the metrics.",
        "- **Every cause is a hypothesis**, produced by simple checks on the ranked list and the",
        "  qrels (rank of the first relevant chunk, CFR part, section, query-term overlap), not a",
        "  verified explanation. The vocabulary check counts query words in a passage, so it",
        "  says little about the dense system, which matches meaning, not words. A hypothesis can be",
        "  wrong, and the LLM grade behind it can be wrong too (the LLM is stricter than humans).",
        "",
        "## Queries tied at 0 nDCG@10",
        "",
    ]
    out += zero_ties(fd) + [""]
    zero_counts = {s: sum(1 for r in fd["rows"] if r["ndcg"][s] == 0) for s in names}
    out += [
        "Each system column counts queries where that system scored exactly 0 (no chunk graded >= 1",
        "in its top 10). 'all four 0' counts queries where every system scored 0.",
        "",
        "## Queries where all four systems score 0",
        "",
    ]
    allz = [r for r in fd["rows"] if all(r["ndcg"][s] == 0 for s in names)]
    if allz:
        out += [
            f"| qid | module | type | query | chunks graded >=1 (of which 2) | first relevant rank (max {DEEP_K}) |",
            "|---|---|---|---|---|---|",
        ]
        for r in allz:
            rels = qrels[r["qid"]]
            n1 = sum(1 for g in rels.values() if g >= 1)
            n2 = sum(1 for g in rels.values() if g >= 2)
            ranks = []
            for s in names:
                rk = first_relevant_rank(ranked(s, r["module"], r["qid"], DEEP_K), rels)
                ranks.append(f"{s} {rk if rk else f'>{DEEP_K}'}")
            out.append(
                f"| {r['qid']} | {r['module']} | {r['qtype']} | {r['query']} | {n1} ({n2}) "
                f"| {', '.join(ranks)} |"
            )
        out.append("")
    else:
        out += ["No query scores 0 under all four systems.", ""]

    out += ["## Five lowest queries per system, with top 3 results", ""]
    for s in names:
        worst = sorted(fd["rows"], key=lambda r: (r["ndcg"][s], r["qid"]))[:5]
        out += [
            f"### {s} ({zero_counts[s]} of {len(fd['rows'])} queries score 0; showing 5 by "
            f"nDCG@10 then qid)",
            "",
        ]
        for r in worst:
            rels = qrels[r["qid"]]
            rk = ranked(s, r["module"], r["qid"], DEEP_K)
            out.append(
                f"- **{r['qid']}** ({r['module']}, {r['qtype']}), nDCG@10 {r['ndcg'][s]:.3f}: "
                f"\"{r['query']}\""
            )
            for i, d in enumerate(rk[:3], start=1):
                g = rels.get(d)
                grade = "unjudged" if g is None else f"grade {g}"
                snip = text_of[d][:SNIPPET].replace("|", "/").replace("\n", " ")
                out.append(f"  - {i}. `{d}` ({grade}): {snip}...")
            hyps = hypotheses(r["query"], rk, rels, text_of)
            out.append("  - Hypothesis: " + "; ".join(hyps))
        out.append("")
    return "\n".join(out)


KAPPA_METRICS = (
    ("exact", "exact agreement"),
    ("kappa_linear", "weighted kappa (linear)"),
    ("kappa_quadratic", "weighted kappa (quadratic)"),
    ("binary_agreement", "binary agreement"),
    ("binary_kappa", "binary kappa"),
)


def cluster_bootstrap_agreement(
    human: dict[tuple[str, str], int],
    llm: dict[tuple[str, str], int],
    n: int = 10000,
    seed: int = 42,
    level: float = 0.95,
) -> dict:
    """Percentile bootstrap intervals for LLM-vs-human agreement, resampling queries.

    Rows of one query are not independent (same query, same pool), so the unit of
    resampling is the query: draw the queries with replacement, keep all graded rows of
    each drawn query (a query drawn twice counts twice), and recompute agreement_report
    on the rows of the resample. Only rows graded by both are used.
    Returns {'n_rows', 'n_queries', 'point': {metric: value}, 'ci': {metric: (lo, hi)},
    'constant_resamples': resamples where one rater gave one grade to every row}.
    """
    keys = sorted(set(human) & set(llm))
    if not keys:
        raise ValueError("no overlapping rows")
    by_q: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for k in keys:
        by_q[k[0]].append(k)
    qids = sorted(by_q)
    point = agreement_report({k: human[k] for k in keys}, {k: llm[k] for k in keys})
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {m: [] for m, _ in KAPPA_METRICS}
    constant = 0
    for _ in range(n):
        h: dict[tuple[str, str], int] = {}
        g: dict[tuple[str, str], int] = {}
        for j in range(len(qids)):
            q = qids[rng.randrange(len(qids))]
            for k in by_q[q]:
                key = (f"{q}#{j}", k[1])
                h[key], g[key] = human[k], llm[k]
        if len(set(h.values())) == 1 or len(set(g.values())) == 1:
            constant += 1
        rep = agreement_report(h, g)
        for m, _ in KAPPA_METRICS:
            samples[m].append(rep[m])
    lo_q, hi_q = (1 - level) / 2, (1 + level) / 2
    ci = {
        m: tuple(float(x) for x in np.quantile(np.asarray(v), [lo_q, hi_q]))
        for m, v in samples.items()
    }
    return {
        "n_rows": len(keys),
        "n_queries": len(qids),
        "point": {m: float(point[m]) for m, _ in KAPPA_METRICS},
        "ci": ci,
        "constant_resamples": constant,
    }


def kappa_report(
    human_files: dict[str, dict[tuple[str, str], int]],
    llm: dict[tuple[str, str], int],
    no_answer_qids: set[str],
) -> str:
    """Builds the 14d markdown: Step 13 agreement numbers with query-level bootstrap intervals."""
    names = list(human_files)
    merged = merge_human(list(human_files.values()))
    slices = {f"{names[0]} only (headline)": human_files[names[0]], "all human rows (merged)": merged}
    out = [
        "# Step 14d: bootstrap intervals on LLM-vs-human agreement",
        "",
        "**Agreement of the LLM grades (claude-sonnet-5-5) with human grades on the human sample.**",
        "This part compares the LLM-assessed qrels with human grades, so the human sample is the",
        "only reference and it is small: 15 queries in total.",
        "",
        "## Method",
        "- Same agreement numbers as Step 13 (`agreement_report`), here with 95% percentile bootstrap",
        "  intervals, 10000 resamples, seed 42.",
        "- **The queries are resampled, not the rows.** Rows from one query share the query and the",
        "  pool, so they are not independent, and resampling rows would give intervals that are too",
        "  narrow. A resample draws as many queries as the slice has, with replacement, and keeps all",
        "  graded rows of each drawn query.",
        "- With 8 to 15 queries per slice, a percentile bootstrap is itself rough: the intervals may be",
        "  too narrow, and a few queries with unusual grade mixes dominate them.",
        "- 'Excluding no_answer' removes q44, whose rows are nearly all 0 and easy to agree on.",
        "- Pari only (9 queries) is the cleanest single-annotator set. The merged set uses Pari's",
        "  grade where both humans graded a row (Parth's file adds 6 queries of his own).",
        "",
    ]
    for title, drop in (("All rows", False), ("Excluding no_answer queries", True)):
        out += [f"## {title}", ""]
        out += [
            "| Slice | rows | queries | "
            + " | ".join(label for _, label in KAPPA_METRICS)
            + " |",
            "|---|---|---|" + "---|" * len(KAPPA_METRICS),
        ]
        notes = []
        for name, grades in slices.items():
            h = {k: v for k, v in grades.items() if not (drop and k[0] in no_answer_qids)}
            res = cluster_bootstrap_agreement(h, llm)
            cells = " | ".join(
                f"{res['point'][m]:.3f} [{res['ci'][m][0]:.3f}, {res['ci'][m][1]:.3f}]"
                for m, _ in KAPPA_METRICS
            )
            out.append(f"| {name} | {res['n_rows']} | {res['n_queries']} | {cells} |")
            notes.append(f"{name}: {res['constant_resamples']}")
        out += [
            "",
            "Format: point estimate [95% interval]. Resamples where one rater gave a single grade to",
            "every row (kappa is then degenerate): " + "; ".join(notes) + ".",
            "",
        ]
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
    ap.add_argument("--part", choices=["results", "types", "failures", "kappa", "all"], default="all")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--no-dense", action="store_true")
    ap.add_argument("--llm", default=str(LLM_PATH))
    ap.add_argument("--human", nargs="+", default=list(HUMAN_PATHS))
    a = ap.parse_args()

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.part in ("kappa", "all"):
        human_files = {
            Path(p).stem.replace("sample_", ""): load_human_grades(p) for p in a.human
        }
        na = {r.qid for r in load_query_rows(a.queries) if r.qtype == NO_ANSWER}
        text = kappa_report(human_files, load_llm_grades(a.llm), na)
        (out_dir / "step14_kappa_ci.md").write_text(text + "\n", encoding="utf-8")
        print(text)
    if a.part == "kappa":
        return
    data, rows_by_module, qrels = build_all(a.corpus, a.queries, a.qrels, not a.no_dense)
    if a.part in ("results", "all"):
        text = results_report(data, qrels)
        (out_dir / "step14_results.md").write_text(text + "\n", encoding="utf-8")
        print(text)
    if a.part in ("types", "all"):
        text = types_report(data, rows_by_module)
        (out_dir / "step14_by_type.md").write_text(text + "\n", encoding="utf-8")
        print(text)
    if a.part in ("failures", "all"):
        text = failures_report(data, qrels, rows_by_module)
        (out_dir / "step14_failures.md").write_text(text + "\n", encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
