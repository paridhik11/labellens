"""Evaluate every registered retrieval system. One command, one markdown table.

Usage:
  python -m src.ir.eval --corpus data/processed/regs.jsonl \
      --queries data/eval/queries_t1.tsv --qrels data/eval/qrels_t1.tsv --out results/t1.md

queries file:
  2-col: qid<TAB>query text
  4-col: qid<TAB>query text<TAB>module<TAB>type (optional header row allowed)
qrels file (TREC):
  qid 0 doc_id relevance
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.common.schemas import Chunk, Hit
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex, TfidfRetriever
from src.ir.metrics import average_precision, mrr, ndcg_at_k, paired_bootstrap, recall_at_k


@dataclass(frozen=True)
class QueryRow:
    """Structured query entry loaded from a TSV file."""

    qid: str
    query: str
    module: str = ""
    qtype: str = ""


def load_chunks(path: str | Path) -> list[Chunk]:
    """Loads Chunk objects (preserving hash, section, and module) from JSONL."""
    chunks: list[Chunk] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(Chunk.model_validate_json(line))
    return chunks


def load_corpus(path: str | Path) -> list[tuple[str, str]]:
    """Loads (chunk_id, text) tuples from a JSONL corpus."""
    docs: list[tuple[str, str]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            docs.append((d["chunk_id"], d["text"]))
    return docs


def load_query_rows(path: str | Path) -> list[QueryRow]:
    """Loads queries from either a 2-column or 4-column TSV (with optional header)."""
    rows: list[QueryRow] = []
    for idx, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        parts = line.split("\t")
        if idx == 0 and parts[0].strip().lower() == "qid":
            continue
        qid = parts[0].strip()
        query = parts[1].strip()
        module = parts[2].strip() if len(parts) > 2 else ""
        qtype = parts[3].strip() if len(parts) > 3 else ""
        rows.append(QueryRow(qid=qid, query=query, module=module, qtype=qtype))
    return rows


def load_queries(path: str | Path) -> dict[str, str]:
    """Loads qid -> query text mapping from a TSV file."""
    return {row.qid: row.query for row in load_query_rows(path)}


def load_qrels(path: str | Path) -> dict[str, dict[str, int]]:
    """Loads TREC-format qrels into qid -> {doc_id: grade}."""
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            qid, _, doc, rel = line.split()
            qrels[qid][doc] = int(rel)
    return qrels


def build_systems(
    docs: list[tuple[str, str]],
    with_dense: bool = True,
    chunks: list[Chunk] | None = None,
    cache_dir: Path | None = None,
    model: object | None = None,
) -> list[Retriever]:
    """Register retrieval systems so they appear in the eval table.

    Systems: tfidf, bm25, dense (sentence-transformer + FAISS), hybrid (RRF).
    Pass chunks directly so Chunk.hash is preserved for DenseRetriever caching.
    Set with_dense=False to skip dense and hybrid for a quick lexical-only run.
    """
    ix = InvertedIndex().build(docs)
    tfidf = TfidfRetriever(ix)
    bm25 = BM25Retriever(ix)

    if not with_dense:
        return [tfidf, bm25]

    from src.ir.dense import CACHE_DIR, DenseRetriever
    from src.ir.hybrid import HybridRetriever

    dense_chunks = chunks if chunks is not None else [
        Chunk(chunk_id=cid, source="", text=txt) for cid, txt in docs
    ]
    resolved_cache = CACHE_DIR if cache_dir is None else cache_dir
    dense = DenseRetriever.from_chunks(
        dense_chunks,
        cache_dir=resolved_cache,
        model=model,
    )
    hybrid = HybridRetriever(bm25=bm25, dense=dense)
    return [tfidf, bm25, dense, hybrid]


def aggregate_hits_by_section(
    hits: list[Hit],
    chunk_to_section: dict[str, str],
) -> list[str]:
    """Aggregates ranked chunk hits to section IDs by maximum score."""
    sec_scores: dict[str, float] = {}
    for hit in hits:
        sec = chunk_to_section.get(hit.doc_id, hit.doc_id)
        if sec not in sec_scores or hit.score > sec_scores[sec]:
            sec_scores[sec] = hit.score
    ranked = sorted(sec_scores.items(), key=lambda kv: -kv[1])
    return [sec for sec, _ in ranked]


def aggregate_qrels_by_section(
    qrels: dict[str, dict[str, int]],
    chunk_to_section: dict[str, str],
) -> dict[str, dict[str, int]]:
    """Aggregates chunk-level relevance grades to section IDs by maximum grade."""
    sec_qrels: dict[str, dict[str, int]] = {}
    for qid, doc_rels in qrels.items():
        agg: dict[str, int] = {}
        for doc_id, rel in doc_rels.items():
            sec = chunk_to_section.get(doc_id, doc_id)
            if sec not in agg or rel > agg[sec]:
                agg[sec] = rel
        sec_qrels[qid] = agg
    return sec_qrels


def evaluate(
    systems: list[Retriever],
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    k_ndcg: int = 10,
    k_recall: int = 20,
    chunk_to_section: dict[str, str] | None = None,
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, list[float]]]]:
    """Evaluates each system against qrels.

    When chunk_to_section is None, evaluates chunk-level rankings directly.
    When chunk_to_section is provided, aggregates chunk scores to section IDs
    by max score and chunk qrels by max grade before computing metrics.
    """
    is_section = chunk_to_section is not None
    active_qrels = (
        aggregate_qrels_by_section(qrels, chunk_to_section)
        if chunk_to_section is not None
        else qrels
    )
    fetch_k = max(k_ndcg, k_recall) * (5 if is_section else 1)

    results, per_query = {}, {}
    for s in systems:
        rows: dict[str, list[float]] = defaultdict(list)
        for qid, q in queries.items():
            if qid not in active_qrels:
                continue
            hits = s.search(q, k=fetch_k)
            if chunk_to_section is not None:
                ranked = aggregate_hits_by_section(hits, chunk_to_section)
            else:
                ranked = [h.doc_id for h in hits]
            rows["ndcg"].append(ndcg_at_k(ranked, active_qrels[qid], k_ndcg))
            rows["recall"].append(recall_at_k(ranked, active_qrels[qid], k_recall))
            rows["mrr"].append(mrr(ranked, active_qrels[qid]))
            rows["map"].append(average_precision(ranked, active_qrels[qid]))
        per_query[s.name] = rows
        results[s.name] = {m: sum(v) / max(len(v), 1) for m, v in rows.items()}
    return results, per_query


def to_markdown(results, per_query, baseline: str | None = None) -> str:
    """Formats evaluation results and paired bootstrap p-values as a markdown table."""
    lines = [
        "| System | nDCG@10 | Recall@20 | MRR | MAP | p vs baseline |",
        "|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        p = ""
        if baseline and name != baseline and baseline in per_query:
            p = f"{paired_bootstrap(per_query[name]['ndcg'], per_query[baseline]['ndcg']):.3f}"
        lines.append(f"| {name} | {r['ndcg']:.3f} | {r['recall']:.3f} | {r['mrr']:.3f} | {r['map']:.3f} | {p} |")
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="Evaluate retrieval systems.")
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--qrels", required=True)
    ap.add_argument("--out", default="results/results.md")
    ap.add_argument("--baseline", default="bm25")
    ap.add_argument(
        "--module",
        choices=["device", "medicine", "all"],
        default="all",
        help="Filter corpus and module-tagged queries before ranking (default: all)",
    )
    ap.add_argument(
        "--no-dense",
        action="store_true",
        help="Skip dense and hybrid systems (faster, BM25+TF-IDF only)",
    )
    ap.add_argument(
        "--section-level",
        action="store_true",
        help="Also report section-level metrics by aggregating chunk scores by max",
    )
    a = ap.parse_args()

    chunks = load_chunks(a.corpus)
    if a.module != "all":
        chunks = [c for c in chunks if c.module == a.module]

    docs = [(c.chunk_id, c.text) for c in chunks]
    systems = build_systems(docs, with_dense=not a.no_dense, chunks=chunks)

    query_rows = load_query_rows(a.queries)
    if a.module != "all":
        # Keep untagged queries (no module column) and queries matching --module.
        query_rows = [r for r in query_rows if not r.module or r.module == a.module]
    queries = {r.qid: r.query for r in query_rows}
    qrels = load_qrels(a.qrels)

    chunk_results, chunk_per_query = evaluate(systems, queries, qrels)
    chunk_md = to_markdown(chunk_results, chunk_per_query, a.baseline)

    sections_out: list[str] = []
    if a.section_level:
        chunk_to_section = {c.chunk_id: (c.section or c.chunk_id) for c in chunks}
        sec_results, sec_per_query = evaluate(
            systems, queries, qrels, chunk_to_section=chunk_to_section
        )
        sec_md = to_markdown(sec_results, sec_per_query, a.baseline)
        sections_out.append("### Chunk-level\n\n" + chunk_md)
        sections_out.append("### Section-level\n\n" + sec_md)
        output_md = "\n\n".join(sections_out)
    else:
        output_md = chunk_md

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(output_md + "\n", encoding="utf-8")
    print(output_md)


if __name__ == "__main__":
    main()
