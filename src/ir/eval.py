"""Evaluate every registered retrieval system. One command, one markdown table.

Usage:
  python -m src.ir.eval --corpus data/processed/regs.jsonl \
      --queries data/eval/queries_t1.tsv --qrels data/eval/qrels_t1.tsv --out results/t1.md

queries file: qid<TAB>query text     qrels file (TREC): qid 0 doc_id relevance
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex, TfidfRetriever
from src.ir.metrics import average_precision, mrr, ndcg_at_k, paired_bootstrap, recall_at_k


def load_corpus(path: str) -> list[tuple[str, str]]:
    docs = []
    for line in Path(path).read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            docs.append((d["chunk_id"], d["text"]))
    return docs


def load_queries(path: str) -> dict[str, str]:
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.strip():
            qid, q = line.split("\t", 1)
            out[qid] = q
    return out


def load_qrels(path: str) -> dict[str, dict[str, int]]:
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for line in Path(path).read_text().splitlines():
        if line.strip():
            qid, _, doc, rel = line.split()
            qrels[qid][doc] = int(rel)
    return qrels


def build_systems(
    docs: list[tuple[str, str]],
    with_dense: bool = True,
) -> list[Retriever]:
    """Register new systems here so they appear in the eval table.

    Systems: tfidf, bm25, dense (sentence-transformer + FAISS), hybrid (RRF).
    Set with_dense=False to skip the two slow systems for a quick BM25-only run.
    """
    ix = InvertedIndex().build(docs)
    tfidf = TfidfRetriever(ix)
    bm25 = BM25Retriever(ix)

    if not with_dense:
        return [tfidf, bm25]

    from src.common.schemas import Chunk
    from src.ir.dense import DenseRetriever
    from src.ir.hybrid import HybridRetriever

    chunks = [Chunk(chunk_id=cid, source="", text=txt) for cid, txt in docs]
    dense = DenseRetriever.from_chunks(chunks)
    hybrid = HybridRetriever(bm25=bm25, dense=dense)
    return [tfidf, bm25, dense, hybrid]


def evaluate(systems, queries, qrels, k_ndcg=10, k_recall=20):
    results, per_query = {}, {}
    for s in systems:
        rows = defaultdict(list)
        for qid, q in queries.items():
            if qid not in qrels:
                continue
            ranked = [h.doc_id for h in s.search(q, k=max(k_ndcg, k_recall))]
            rows["ndcg"].append(ndcg_at_k(ranked, qrels[qid], k_ndcg))
            rows["recall"].append(recall_at_k(ranked, qrels[qid], k_recall))
            rows["mrr"].append(mrr(ranked, qrels[qid]))
            rows["map"].append(average_precision(ranked, qrels[qid]))
        per_query[s.name] = rows
        results[s.name] = {m: sum(v) / max(len(v), 1) for m, v in rows.items()}
    return results, per_query


def to_markdown(results, per_query, baseline: str | None = None) -> str:
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--qrels", required=True)
    ap.add_argument("--out", default="results/results.md")
    ap.add_argument("--baseline", default="bm25")
    ap.add_argument(
        "--no-dense",
        action="store_true",
        help="Skip dense and hybrid systems (faster, BM25+TF-IDF only)",
    )
    a = ap.parse_args()
    systems = build_systems(load_corpus(a.corpus), with_dense=not a.no_dense)
    results, per_query = evaluate(systems, load_queries(a.queries), load_qrels(a.qrels))
    md = to_markdown(results, per_query, a.baseline)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
