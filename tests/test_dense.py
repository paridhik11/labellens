"""Tests for DenseRetriever (sentence-transformers + FAISS)."""
from __future__ import annotations

from pathlib import Path

from src.common.schemas import Chunk, Hit
from src.ir.dense import DenseRetriever, _corpus_fingerprint


def _make_chunks(n: int = 5) -> list[Chunk]:
    return [
        Chunk(
            chunk_id=f"chunk_{i}",
            source="FDA",
            text=f"Regulatory text about labeling requirement number {i}.",
        )
        for i in range(n)
    ]


def test_corpus_fingerprint_stable() -> None:
    ids = ["a", "b", "c"]
    assert _corpus_fingerprint(ids) == _corpus_fingerprint(ids)


def test_corpus_fingerprint_differs_on_change() -> None:
    assert _corpus_fingerprint(["a", "b"]) != _corpus_fingerprint(["a", "c"])


def test_dense_retriever_from_chunks_returns_hits(tmp_path) -> None:
    chunks = _make_chunks(10)
    retriever = DenseRetriever.from_chunks(chunks, cache_dir=tmp_path)
    hits = retriever.search("labeling requirement", k=3)
    assert len(hits) == 3
    for h in hits:
        assert isinstance(h, Hit)
        assert h.score >= 0.0
        assert h.rank >= 1


def test_dense_retriever_cache_hit(tmp_path) -> None:
    chunks = _make_chunks(5)
    r1 = DenseRetriever.from_chunks(chunks, cache_dir=tmp_path)
    # Second call must load from cache without recomputing.
    r2 = DenseRetriever.from_chunks(chunks, cache_dir=tmp_path)
    hits1 = r1.search("labeling", k=2)
    hits2 = r2.search("labeling", k=2)
    assert [h.doc_id for h in hits1] == [h.doc_id for h in hits2]


def test_dense_retriever_scores_decreasing() -> None:
    chunks = _make_chunks(10)
    hits = DenseRetriever.from_chunks(chunks, cache_dir=None).search("labeling requirement number 2", k=5)
    # We just check that scores are non-increasing.
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_dense_retriever_from_jsonl_and_cache_files(tmp_path: Path) -> None:
    chunks = _make_chunks(4)
    jsonl_path = tmp_path / "mini.jsonl"
    jsonl_path.write_text("\n".join(c.model_dump_json() for c in chunks) + "\n", encoding="utf-8")

    cache_dir = tmp_path / "cache"
    retriever = DenseRetriever.from_jsonl(jsonl_path, cache_dir=cache_dir)
    hits = retriever.search("labeling requirement", k=2)
    assert len(hits) == 2
    assert list(cache_dir.glob("dense_cache_*.npy"))
    assert list(cache_dir.glob("dense_cache_*.json"))
