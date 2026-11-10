"""Compare retrieval systems side by side on the 5 Step 6 benchmark queries.

Usage:
  python -m src.ir.query_compare
  python -m src.ir.query_compare --systems bm25 dense
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.common.schemas import Chunk, Hit
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.dense import DenseRetriever

QUERIES = [
    "unique device identifier on label",
    "sterile symbol",
    "expiration date",
    "prescription use only statement",
    "manufacturer name and address",
]

CORPUS_PATH = Path("data/processed/regs.jsonl")
TOP_K = 5


def load_corpus(path: Path) -> tuple[list[tuple[str, str]], dict[str, Chunk]]:
    """Loads a JSONL corpus into (doc_id, text) pairs and a chunk lookup dictionary."""
    docs: list[tuple[str, str]] = []
    chunk_map: dict[str, Chunk] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            c = Chunk.model_validate_json(line)
            docs.append((c.chunk_id, c.text))
            chunk_map[c.chunk_id] = c
    return docs, chunk_map


def compare_queries(
    systems: list[tuple[str, Retriever]],
    chunk_map: dict[str, Chunk],
    queries: list[str] = QUERIES,
    k: int = TOP_K,
) -> dict[str, dict[str, list[Hit]]]:
    """Runs each query across all provided retrievers and returns ranked hits per system."""
    results: dict[str, dict[str, list[Hit]]] = {}
    for query in queries:
        results[query] = {}
        for sys_name, retriever in systems:
            results[query][sys_name] = retriever.search(query, k=k)
    return results


def format_comparison(
    results: dict[str, dict[str, list[Hit]]],
    chunk_map: dict[str, Chunk],
) -> str:
    """Formats side-by-side comparison output across queries and retrieval systems."""
    lines: list[str] = []
    for query, sys_hits in results.items():
        lines.append("\n" + "=" * 78)
        lines.append(f"QUERY: {query}")
        lines.append("=" * 78)
        for sys_name, hits in sys_hits.items():
            lines.append(f"\n  [{sys_name}]")
            for h in hits:
                c = chunk_map.get(h.doc_id)
                sec = c.section if c else "?"
                mod = c.module if c else "?"
                title = (c.title or "")[:65] if c else ""
                snippet = " ".join(h.text.split())[:110]
                lines.append(
                    f"    #{h.rank} score={h.score:.4f} | {h.doc_id} (sec {sec}, {mod})"
                )
                if title:
                    lines.append(f"       Title: {title}")
                lines.append(f"       Text:  {snippet}...")
    return "\n".join(lines)


def main() -> None:
    """CLI entrypoint to run Step 6 benchmark queries across selected systems."""
    parser = argparse.ArgumentParser(description="Compare retrieval systems on benchmark queries.")
    parser.add_argument(
        "--systems",
        nargs="+",
        choices=["tfidf", "bm25", "dense", "hybrid"],
        default=["bm25", "dense"],
        help="Systems to compare (default: bm25 dense)",
    )
    parser.add_argument("--corpus", default=str(CORPUS_PATH), help="Path to regs.jsonl")
    parser.add_argument("--k", type=int, default=TOP_K, help="Number of top hits to display.")
    parser.add_argument(
        "--module",
        choices=["device", "medicine", "all"],
        default="all",
        help="Restrict retrieval to a module: device, medicine, or all (default)",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    corpus_path = Path(args.corpus)
    print(f"Loading corpus from {corpus_path} ...")
    docs, chunk_map = load_corpus(corpus_path)

    # Apply module filter before building indexes.
    if args.module != "all":
        chunk_map = {k: v for k, v in chunk_map.items() if v.module == args.module}
        docs = [(cid, txt) for cid, txt in docs if cid in chunk_map]
        print(f"[query_compare] Module filter '{args.module}': {len(docs)} chunks retained.")

    chunks = list(chunk_map.values())
    print(f"  {len(docs)} chunks loaded.")

    ix = InvertedIndex().build(docs)
    bm25 = BM25Retriever(ix)
    systems: list[tuple[str, Retriever]] = []

    dense: DenseRetriever | None = None
    if "dense" in args.systems or "hybrid" in args.systems:
        dense = DenseRetriever.from_chunks(chunks)

    for name in args.systems:
        if name == "tfidf":
            from src.ir.bm25 import TfidfRetriever

            systems.append(("TF-IDF", TfidfRetriever(ix)))
        elif name == "bm25":
            systems.append(("BM25", bm25))
        elif name == "dense" and dense is not None:
            systems.append(("Dense", dense))
        elif name == "hybrid" and dense is not None:
            from src.ir.hybrid import HybridRetriever

            systems.append(("Hybrid", HybridRetriever(bm25=bm25, dense=dense)))

    results = compare_queries(systems, chunk_map, queries=QUERIES, k=args.k)
    print(format_comparison(results, chunk_map))


if __name__ == "__main__":
    main()
