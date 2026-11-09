"""Interactive BM25 search over processed regulatory chunks.

Builds an inverted index over data/processed/regs.jsonl and returns the top k
matching chunks with scores, section IDs, and passage snippets.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.common.schemas import Chunk, Hit
from src.ir.bm25 import BM25Retriever, InvertedIndex


def load_chunks(path: str | Path) -> dict[str, Chunk]:
    """Loads a JSONL file of Chunk objects into a dictionary keyed by chunk_id."""
    chunks: dict[str, Chunk] = {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Corpus file not found: {path}")

    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                chunk = Chunk.model_validate_json(line_str)
                chunks[chunk.chunk_id] = chunk
    return chunks


def build_bm25_searcher(chunks: dict[str, Chunk]) -> tuple[InvertedIndex, BM25Retriever]:
    """Constructs an InvertedIndex and BM25Retriever from a dictionary of Chunk objects."""
    docs = [(chunk_id, chunk.text) for chunk_id, chunk in chunks.items()]
    index = InvertedIndex().build(docs)
    retriever = BM25Retriever(index)
    return index, retriever


def search_chunks(
    retriever: BM25Retriever,
    chunks: dict[str, Chunk],
    query: str,
    k: int = 5,
) -> list[tuple[Hit, Chunk]]:
    """Runs a query through the BM25 retriever and returns ranked (Hit, Chunk) pairs."""
    hits = retriever.search(query, k=k)
    results: list[tuple[Hit, Chunk]] = []
    for hit in hits:
        if hit.doc_id in chunks:
            results.append((hit, chunks[hit.doc_id]))
    return results


def format_search_results(results: list[tuple[Hit, Chunk]]) -> str:
    """Formats ranked search results for terminal display."""
    if not results:
        return "No matching chunks found."

    lines: list[str] = []
    for hit, chunk in results:
        lines.append(f"Rank {hit.rank} | Score: {hit.score:.4f} | Section: {chunk.section} | ID: {chunk.chunk_id}")
        if chunk.title:
            lines.append(f"  Title: {chunk.title}")
        clean_text = " ".join(chunk.text.split())
        snippet = clean_text[:160] + "..." if len(clean_text) > 160 else clean_text
        lines.append(f"  Text: {snippet}")
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Search regulatory chunks using BM25.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument(
        "--corpus",
        default="data/processed/regs.jsonl",
        help="Path to processed regulatory JSONL corpus",
    )
    parser.add_argument("-k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    chunks = load_chunks(args.corpus)
    _, retriever = build_bm25_searcher(chunks)
    results = search_chunks(retriever, chunks, args.query, k=args.k)

    print(f"Query: \"{args.query}\" (Top {len(results)} of {len(chunks)} chunks)")
    print("-" * 70)
    print(format_search_results(results))


if __name__ == "__main__":
    main()
