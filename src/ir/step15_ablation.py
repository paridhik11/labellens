"""Step 15 ablations: build the retrieval variants and list their unjudged top-10 results.

Usage (repo root):
  python -m src.ir.step15_ablation --part ranks11_20
    -> results/step15_unjudged_ranks11_20.csv and .md (ranks 11 to 20, not in the pool)
  python -m src.ir.step15_ablation --part unjudged
    -> results/step15_unjudged.csv          (qid, chunk_id, variant)
    -> results/step15_unjudged_summary.md   (counts per variant)

Sensitivity analysis, not tuning: every variant changes ONE thing from the default
settings, and the grid below is fixed in advance.

  Default: BM25 (k1=1.5, b=0.75, no stemming), dense (bge-small-en-v1.5, no query prefix),
  hybrid = RRF of those two with k=60 and weights 1:1.

  rrf_k10, rrf_k30, rrf_k100      hybrid with another RRF smoothing constant
  w_bm25_A_dense_B                hybrid (k=60) with bm25:dense weights A:B
  bm25_stem                       BM25 on a light-stemmed index
  hybrid_stem                     hybrid whose BM25 half is the stemmed one
  dense_prefix                    dense with the BGE retrieval instruction on queries
  hybrid_prefix                   hybrid whose dense half uses that prefix

This module reads the LLM qrels and never writes to any qrels, pool or grade file.
A chunk is 'unjudged' for a query when it is absent from the qrels of that query.
The metrics treat unjudged chunks as grade 0, so a variant that retrieves many of
them can only be understated, not overstated.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.dense import BGE_QUERY_PREFIX, CACHE_DIR, DenseRetriever
from src.ir.eval import (
    aggregate_hits_by_section,
    load_chunks,
    load_qrels,
    load_query_rows,
)
from src.ir.hybrid import HybridRetriever

DEFAULTS = ("default_bm25", "default_dense", "default_hybrid")
RRF_KS = (10, 30, 100)
WEIGHTS = ((2, 1), (3, 1), (1, 2), (1, 3))  # (bm25, dense), fixed before looking at results
TOP_K = 10
# Depths below are the ones eval.evaluate() uses, because HybridRetriever over-fetches
# max(3k, 50) from each ranker, so its top 10 depends on the k it is called with.
# Using another depth would list chunks the evaluation never sees.
CHUNK_FETCH_K = 20  # chunk level: max(k_ndcg=10, k_recall=20), top 10 of this list is nDCG@10
SECTION_FETCH_K = 100  # section level: 5 x 20, chunks are then aggregated to sections
CSV_HEADER = ("qid", "chunk_id", "variant")


def weight_name(wb: int, wd: int) -> str:
    """Variant name for a bm25:dense weight pair, e.g. w_bm25_2_dense_1."""
    return f"w_bm25_{wb}_dense_{wd}"


def variant_names() -> list[str]:
    """All variant names in report order, defaults first."""
    names = list(DEFAULTS)
    names += [f"rrf_k{k}" for k in RRF_KS]
    names += [weight_name(wb, wd) for wb, wd in WEIGHTS]
    names += ["bm25_stem", "hybrid_stem", "dense_prefix", "hybrid_prefix"]
    return names


def build_variants(
    chunks: list[Chunk], model: object | None = None, cache_dir: Path | None = CACHE_DIR
) -> dict[str, Retriever]:
    """Builds every variant for one module's chunks.

    The dense embeddings come from the existing cache (passages never get the prefix,
    so default and prefixed dense share the same cached vectors). Pass model and a
    temporary cache_dir to use a fake encoder in tests.
    """
    docs = [(c.chunk_id, c.text) for c in chunks]
    bm25 = BM25Retriever(InvertedIndex().build(docs))
    bm25_stem = BM25Retriever(InvertedIndex(stem=True).build(docs))
    dense = DenseRetriever.from_chunks(chunks, cache_dir=cache_dir, model=model)
    dense_prefix = DenseRetriever.from_chunks(
        chunks, cache_dir=cache_dir, model=model, query_prefix=BGE_QUERY_PREFIX
    )
    out: dict[str, Retriever] = {
        "default_bm25": bm25,
        "default_dense": dense,
        "default_hybrid": HybridRetriever(bm25, dense),
    }
    for k in RRF_KS:
        out[f"rrf_k{k}"] = HybridRetriever(bm25, dense, k=k)
    for wb, wd in WEIGHTS:
        out[weight_name(wb, wd)] = HybridRetriever(bm25, dense, bm25_weight=wb, dense_weight=wd)
    out["bm25_stem"] = bm25_stem
    out["hybrid_stem"] = HybridRetriever(bm25_stem, dense)
    out["dense_prefix"] = dense_prefix
    out["hybrid_prefix"] = HybridRetriever(bm25, dense_prefix)
    return out


def unjudged_chunks(
    ranked: list[str], judged: dict[str, int] | set[str]
) -> list[str]:
    """Chunk ids in ranked (in order, no repeats) that are absent from judged."""
    seen: set[str] = set()
    out: list[str] = []
    for d in ranked:
        if d not in judged and d not in seen:
            seen.add(d)
            out.append(d)
    return out


def unjudged_sections(
    ranked_sections: list[str], judged_sections: set[str]
) -> list[str]:
    """Section ids in ranked_sections that contain no judged chunk for the query."""
    return [s for s in ranked_sections if s not in judged_sections]


def collect_unjudged(
    variants_by_module: dict[str, dict[str, Retriever]],
    chunks_by_module: dict[str, list[Chunk]],
    queries_by_module: dict[str, dict[str, str]],
    qrels: dict[str, dict[str, int]],
    k: int = TOP_K,
    start: int = 0,
) -> tuple[list[tuple[str, str, str]], dict[str, dict[str, int]]]:
    """Lists unjudged chunks at ranks start+1..k per variant, and counts section-level gaps.

    The default (start=0, k=10) is the top 10. start=10, k=20 gives ranks 11 to 20, which
    feed Recall@20, MRR and MAP; the section-level count is only computed for start=0.

    Returns (rows, stats). rows is a list of (qid, chunk_id, variant) in variant order,
    then qid, then rank. The chunk list is search(k=CHUNK_FETCH_K)[:k]. stats[variant]
    has 'chunk_rows' (unjudged chunks in the top k), 'slots' (queries x k) and
    'section_rows' (top-k sections, built from the top
    SECTION_FETCH_K chunks, that contain no judged chunk; informational only).
    """
    rows: list[tuple[str, str, str]] = []
    stats: dict[str, dict[str, int]] = defaultdict(
        lambda: {"chunk_rows": 0, "slots": 0, "section_rows": 0}
    )
    per_variant: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for mod, variants in variants_by_module.items():
        c2s = {c.chunk_id: (c.section or c.chunk_id) for c in chunks_by_module[mod]}
        for qid, query in queries_by_module[mod].items():
            q_rels = qrels.get(qid, {})
            judged_secs = {c2s.get(d, d) for d in q_rels}
            for name, system in variants.items():
                top = [h.doc_id for h in system.search(query, k=CHUNK_FETCH_K)[start:k]]
                stats[name]["slots"] += k - start
                for d in unjudged_chunks(top, q_rels):
                    per_variant[name].append((qid, d, name))
                    stats[name]["chunk_rows"] += 1
                if start:
                    continue
                sec_hits = system.search(query, k=SECTION_FETCH_K)
                secs = aggregate_hits_by_section(sec_hits, c2s)[:k]
                stats[name]["section_rows"] += len(unjudged_sections(secs, judged_secs))
    for name in variant_names():
        rows.extend(per_variant.get(name, []))
    return rows, dict(stats)


def ranks_markdown(
    rows: list[tuple[str, str, str]],
    stats: dict[str, dict[str, int]],
    already_listed: set[tuple[str, str]],
) -> str:
    """Counts of unjudged chunks at ranks 11 to 20 and the pairs not yet in the top-10 listing."""
    unique = {(q, c) for q, c, _ in rows}
    extra = unique - already_listed
    out = [
        "# Step 15a (addendum): unjudged chunks at ranks 11 to 20",
        "",
        "**Judged means present in the LLM qrels (claude-sonnet-5-5).** Ranks 11 to 20 of the",
        "chunk-level ranking feed Recall@20, MRR and MAP (nDCG@10 does not use them). Nothing was",
        "graded and these pairs are **not** in `data/eval/pool_t1_extra.csv`.",
        "",
        "| Variant | Unjudged chunks at ranks 11-20 | Share of those slots |",
        "|---|---|---|",
    ]
    for name in variant_names():
        s = stats.get(name, {"chunk_rows": 0, "slots": 0})
        share = s["chunk_rows"] / s["slots"] if s["slots"] else 0.0
        out.append(f"| {name} | {s['chunk_rows']} | {share:.1%} |")
    out += [
        "",
        f"- Rows in `results/step15_unjudged_ranks11_20.csv` (one per qid, chunk, variant): {len(rows)}",
        f"- Unique (qid, chunk) pairs at ranks 11 to 20: {len(unique)}",
        f"- Of those, already in the top-10 listing ({len(already_listed)} pairs): "
        f"{len(unique & already_listed)}",
        f"- **Extra pairs not in the top-10 listing: {len(extra)}**",
        f"- Pool size if added: {len(already_listed)} + {len(extra)} = "
        f"{len(already_listed) + len(extra)}",
        "",
    ]
    return "\n".join(out)


def read_pairs(path: str | Path) -> set[tuple[str, str]]:
    """Unique (qid, chunk_id) pairs of a CSV with qid and chunk_id columns."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {(r["qid"], r["chunk_id"]) for r in csv.DictReader(f)}


def write_csv(rows: list[tuple[str, str, str]], path: str | Path) -> None:
    """Writes the unjudged rows (qid, chunk_id, variant) as CSV."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CSV_HEADER)
        w.writerows(rows)


def summary_markdown(
    rows: list[tuple[str, str, str]], stats: dict[str, dict[str, int]]
) -> str:
    """Counts per variant, unique pairs, and how many pairs the defaults already cover."""
    default_pairs = {(q, c) for q, c, v in rows if v in DEFAULTS}
    unique = {(q, c) for q, c, _ in rows}
    out = [
        "# Step 15a: unjudged top-10 results per ablation variant",
        "",
        "**Judged means present in the LLM qrels (`data/eval/qrels_t1_llm.tsv`, model",
        "claude-sonnet-5-5); there are no human grades for most queries.** Nothing was graded",
        "in this step and no qrels, pool or grade file was written.",
        "",
        "A chunk is unjudged for a query when it is absent from that query's qrels. The metrics",
        "treat unjudged chunks as grade 0, so a variant with many of them is understated, and",
        "differences vs the default are provisional until these rows are graded.",
        "",
        "Each variant changes one thing from the default (bm25 k1=1.5 b=0.75 unstemmed, dense",
        "without query prefix, hybrid RRF k=60 with weights 1:1). The grid was fixed in advance.",
        "All 62 queries are searched, each in its own module's chunks, top 10 chunks of the same",
        "ranked list the evaluation uses (search depth 20 at chunk level). Ranks 11 to 20 also",
        "feed Recall@20, MRR and MAP and are not listed here.",
        "",
        "| Variant | Unjudged chunks in top 10 | Share of top-10 slots | "
        "Section-level top-10 sections with no judged chunk |",
        "|---|---|---|---|",
    ]
    for name in variant_names():
        s = stats.get(name, {"chunk_rows": 0, "slots": 0, "section_rows": 0})
        share = s["chunk_rows"] / s["slots"] if s["slots"] else 0.0
        out.append(f"| {name} | {s['chunk_rows']} | {share:.1%} | {s['section_rows']} |")
    out += [
        "",
        f"- Rows in `results/step15_unjudged.csv` (one per qid, chunk, variant): {len(rows)}",
        f"- Unique (qid, chunk) pairs over all variants: {len(unique)}",
        f"- Of those, also unjudged under a default system: {len(unique & default_pairs)}",
        "- Unique pairs per module: "
        + ", ".join(f"{m} {n}" for m, n in sorted(_pairs_by_module(unique).items())),
        "",
        "The section-level column is informational: a section counts as judged when any of its",
        "chunks is in the qrels, so a judged section can still hide a better unjudged chunk.",
        "Those chunks are not in the CSV, which lists chunk-level top-10 results only.",
        "",
    ]
    return "\n".join(out)


def _pairs_by_module(pairs: set[tuple[str, str]]) -> dict[str, int]:
    """Counts unique pairs per module, read from the chunk id (device vs medicine part)."""
    medicine_parts = {"21cfr201", "21cfr208", "21cfr211"}
    counts: dict[str, int] = defaultdict(int)
    for _, cid in pairs:
        bits = cid.split("_")
        part = bits[1] if len(bits) > 1 else ""
        counts["medicine" if part in medicine_parts else "device"] += 1
    return dict(counts)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 15 ablation variants.")
    ap.add_argument("--part", choices=["unjudged", "ranks11_20"], default="unjudged")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()

    all_chunks = load_chunks(a.corpus)
    qrels = load_qrels(a.qrels)
    rows_q = load_query_rows(a.queries)
    variants: dict[str, dict[str, Retriever]] = {}
    chunks_by_module: dict[str, list[Chunk]] = {}
    queries_by_module: dict[str, dict[str, str]] = {}
    for mod in sorted({c.module for c in all_chunks if c.module}):
        chunks = [c for c in all_chunks if c.module == mod]
        chunks_by_module[mod] = chunks
        variants[mod] = build_variants(chunks)
        queries_by_module[mod] = {r.qid: r.query for r in rows_q if r.module == mod}
    out_dir = Path(a.out_dir)
    if a.part == "ranks11_20":
        rows, stats = collect_unjudged(
            variants, chunks_by_module, queries_by_module, qrels, k=2 * TOP_K, start=TOP_K
        )
        write_csv(rows, out_dir / "step15_unjudged_ranks11_20.csv")
        listed = read_pairs(out_dir / "step15_unjudged.csv")
        text = ranks_markdown(rows, stats, listed)
        (out_dir / "step15_unjudged_ranks11_20.md").write_text(text + "\n", encoding="utf-8")
        print(text)
        return
    rows, stats = collect_unjudged(variants, chunks_by_module, queries_by_module, qrels)
    write_csv(rows, out_dir / "step15_unjudged.csv")
    text = summary_markdown(rows, stats)
    (out_dir / "step15_unjudged_summary.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
