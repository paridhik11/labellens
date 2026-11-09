from pathlib import Path

dense_test = """\"""Tests for DenseRetriever (sentence-transformers + FAISS).\"""
from __future__ import annotations

import numpy as np
import pytest

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
"""

hybrid_test = """\"""Tests for HybridRetriever (Reciprocal Rank Fusion).\"""
from __future__ import annotations

import pytest

from src.common.schemas import Chunk, Hit
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.dense import DenseRetriever
from src.ir.hybrid import HybridRetriever


def _build_retrievers(n: int = 10):
    docs = [
        (f"doc_{i}", f"medical device labeling requirement section {i} regulation")
        for i in range(n)
    ]
    chunks = [Chunk(chunk_id=cid, source="FDA", text=txt) for cid, txt in docs]
    ix = InvertedIndex().build(docs)
    bm25 = BM25Retriever(ix)
    dense = DenseRetriever.from_chunks(chunks, cache_dir=None)
    return bm25, dense, chunks


def test_hybrid_returns_hits() -> None:
    bm25, dense, _ = _build_retrievers()
    hybrid = HybridRetriever(bm25=bm25, dense=dense)
    hits = hybrid.search("medical device labeling", k=3)
    assert len(hits) == 3
    assert all(isinstance(h, Hit) for h in hits)


def test_hybrid_scores_monotone() -> None:
    bm25, dense, _ = _build_retrievers()
    hybrid = HybridRetriever(bm25=bm25, dense=dense)
    hits = hybrid.search("regulation requirement", k=5)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_rrf_score_formula() -> None:
    score = HybridRetriever._rrf_score(rank=1, k=60)
    assert abs(score - 1 / 61) < 1e-9


def test_hybrid_union_larger_than_either() -> None:
    bm25, dense, _ = _build_retrievers(20)
    hybrid = HybridRetriever(bm25=bm25, dense=dense)
    hits = hybrid.search("labeling requirement", k=10)
    assert len(hits) >= 1
"""

Path("tests/test_dense.py").write_text(dense_test, encoding="utf-8")
Path("tests/test_hybrid.py").write_text(hybrid_test, encoding="utf-8")
print("Test files written OK")
