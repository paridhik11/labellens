"""Tests for BM25 search CLI and utilities."""
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.search import (
    build_bm25_searcher,
    format_search_results,
    load_chunks,
    search_chunks,
)


def test_search_chunks_and_format(tmp_path: Path) -> None:
    c1 = Chunk(
        chunk_id="c1",
        source="FDA",
        title="Prescription use",
        section="801.109",
        text="Prescription device statement for licensed practitioner.",
    )
    c2 = Chunk(
        chunk_id="c2",
        source="FDA",
        title="UDI labeling",
        section="830.20",
        text="A unique device identifier must be on the label.",
    )
    test_jsonl = tmp_path / "test_regs.jsonl"
    test_jsonl.write_text(f"{c1.model_dump_json()}\n{c2.model_dump_json()}\n", encoding="utf-8")

    chunks = load_chunks(test_jsonl)
    assert len(chunks) == 2

    _, retriever = build_bm25_searcher(chunks)
    results = search_chunks(retriever, chunks, "unique device identifier", k=2)

    assert len(results) == 2
    top_hit, top_chunk = results[0]
    assert top_hit.doc_id == "c2"
    assert top_chunk.section == "830.20"
    assert top_hit.score > results[1][0].score

    formatted = format_search_results(results)
    assert "Section: 830.20" in formatted
    assert "Title: UDI labeling" in formatted


def test_query_compare_pipeline(tmp_path: Path) -> None:
    """Verifies load_corpus, compare_queries, and format_comparison."""
    from src.ir.bm25 import BM25Retriever, InvertedIndex
    from src.ir.query_compare import compare_queries, format_comparison
    from src.ir.query_compare import load_corpus as qc_load_corpus

    c1 = Chunk(
        chunk_id="c1",
        source="FDA",
        title="Expiration date format",
        section="801.18",
        module="device",
        text="Device expiration date must follow YYYY-MM-DD format.",
    )
    c2 = Chunk(
        chunk_id="c2",
        source="FDA",
        title="Sterile symbol",
        section="801.15",
        module="device",
        text="Symbols such as sterile may appear on medical device labels.",
    )
    corpus_file = tmp_path / "regs.jsonl"
    corpus_file.write_text(f"{c1.model_dump_json()}\n{c2.model_dump_json()}\n", encoding="utf-8")

    docs, chunk_map = qc_load_corpus(corpus_file)
    assert len(docs) == 2
    assert set(chunk_map.keys()) == {"c1", "c2"}

    ix = InvertedIndex().build(docs)
    bm25 = BM25Retriever(ix)
    results = compare_queries([("BM25", bm25)], chunk_map, queries=["expiration date"], k=1)
    assert results["expiration date"]["BM25"][0].doc_id == "c1"

    text_out = format_comparison(results, chunk_map)
    assert "QUERY: expiration date" in text_out
    assert "Title: Expiration date format" in text_out
