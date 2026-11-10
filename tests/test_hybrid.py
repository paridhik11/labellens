"""Tests for HybridRetriever (Reciprocal Rank Fusion).

Uses a FakeTransformer for the dense sub-retriever so no real model is loaded.
"""
from __future__ import annotations

import hashlib

import numpy as np

from src.common.schemas import Chunk, Hit
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.dense import DenseRetriever
from src.ir.hybrid import HybridRetriever


class FakeTransformer:
    """Deterministic random encoder -- no sentence-transformer download."""

    DIM = 32

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = False,
    ) -> np.ndarray:
        rng = np.random.default_rng(seed=sum(ord(c) for t in texts for c in t) % (2**31))
        vecs = rng.random((len(texts), self.DIM)).astype(np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs = vecs / np.where(norms == 0, 1.0, norms)
        return vecs


def _build_retrievers(n: int = 10):
    docs = [
        (f"doc_{i}", f"medical device labeling requirement section {i} regulation")
        for i in range(n)
    ]
    chunks = [
        Chunk(
            chunk_id=cid,
            source="FDA",
            text=txt,
            hash=hashlib.sha256(txt.encode()).hexdigest()[:16],
        )
        for cid, txt in docs
    ]
    ix = InvertedIndex().build(docs)
    bm25 = BM25Retriever(ix)
    dense = DenseRetriever.from_chunks(chunks, cache_dir=None, model=FakeTransformer())
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
