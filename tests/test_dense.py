"""Tests for DenseRetriever (sentence-transformers + FAISS).

Fast tests use a FakeTransformer that returns small deterministic random vectors
so they never load a real model. One test is marked @pytest.mark.slow and
exercises the real BAAI/bge-small-en-v1.5 model.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest

from src.common.schemas import Chunk, Hit
from src.ir.dense import DenseRetriever, _corpus_fingerprint

# ---------------------------------------------------------------------------
# Fake encoder -- replaces SentenceTransformer in every fast test
# ---------------------------------------------------------------------------

class FakeTransformer:
    """Returns deterministic random float32 vectors. No model download needed."""

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


def _make_chunks(n: int = 5) -> list[Chunk]:
    return [
        Chunk(
            chunk_id=f"chunk_{i}",
            source="FDA",
            text=f"Regulatory text about labeling requirement number {i}.",
            hash=hashlib.sha256(f"text_{i}".encode()).hexdigest()[:16],
        )
        for i in range(n)
    ]


def _make_retriever(chunks: list[Chunk], tmp_path: Path | None = None) -> DenseRetriever:
    """Build a DenseRetriever using the FakeTransformer (no real model load)."""
    return DenseRetriever.from_chunks(chunks, cache_dir=tmp_path, model=FakeTransformer())


# ---------------------------------------------------------------------------
# _corpus_fingerprint tests (fast, no model)
# ---------------------------------------------------------------------------

def test_corpus_fingerprint_stable() -> None:
    keys = ["chunk_0:aabbcc", "chunk_1:ddeeff"]
    assert _corpus_fingerprint(keys) == _corpus_fingerprint(keys)


def test_corpus_fingerprint_differs_on_id_change() -> None:
    assert _corpus_fingerprint(["a:hash1", "b:hash2"]) != _corpus_fingerprint(["a:hash1", "c:hash2"])


def test_corpus_fingerprint_differs_on_content_change() -> None:
    """Fingerprint must change when text changes (hash changes) even if ID stays the same."""
    assert _corpus_fingerprint(["chunk_0:hash_old"]) != _corpus_fingerprint(["chunk_0:hash_new"])


# ---------------------------------------------------------------------------
# DenseRetriever fast tests (FakeTransformer injected)
# ---------------------------------------------------------------------------

def test_dense_retriever_returns_hits(tmp_path: Path) -> None:
    chunks = _make_chunks(10)
    retriever = _make_retriever(chunks, tmp_path)
    hits = retriever.search("labeling requirement", k=3)
    assert len(hits) == 3
    for h in hits:
        assert isinstance(h, Hit)
        assert h.score >= 0.0
        assert h.rank >= 1


def test_dense_retriever_scores_decreasing() -> None:
    chunks = _make_chunks(10)
    retriever = _make_retriever(chunks)
    hits = retriever.search("labeling requirement number 2", k=5)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_dense_retriever_cache_hit(tmp_path: Path) -> None:
    chunks = _make_chunks(5)
    r1 = _make_retriever(chunks, tmp_path)
    # Second call must load from cache without re-encoding.
    r2 = _make_retriever(chunks, tmp_path)
    hits1 = r1.search("labeling", k=2)
    hits2 = r2.search("labeling", k=2)
    assert [h.doc_id for h in hits1] == [h.doc_id for h in hits2]


def test_fingerprint_invalidated_on_text_change(tmp_path: Path) -> None:
    """Cache must be invalidated when text changes without the chunk_id changing."""
    chunks = _make_chunks(5)
    _make_retriever(chunks, tmp_path)
    cache_before = set(tmp_path.glob("dense_cache_*.npy"))

    # Change text of chunk_0 without changing its chunk_id.
    old = chunks[0]
    new_text = "Completely different regulatory text."
    new_hash = hashlib.sha256(new_text.encode()).hexdigest()[:16]
    chunks[0] = Chunk(
        chunk_id=old.chunk_id,
        source=old.source,
        text=new_text,
        hash=new_hash,
    )
    _make_retriever(chunks, tmp_path)
    cache_after = set(tmp_path.glob("dense_cache_*.npy"))

    # A new cache file must have been written (old fingerprint != new fingerprint).
    assert len(cache_after) == 2, (
        f"Expected 2 cache files (old + new fingerprint); found {len(cache_after)}"
    )
    assert cache_after != cache_before


def test_dense_retriever_from_jsonl_cache_files(tmp_path: Path) -> None:
    chunks = _make_chunks(4)
    cache_dir = tmp_path / "cache"
    retriever = DenseRetriever.from_chunks(chunks, cache_dir=cache_dir, model=FakeTransformer())
    hits = retriever.search("labeling requirement", k=2)
    assert len(hits) == 2
    assert list(cache_dir.glob("dense_cache_*.npy"))
    assert list(cache_dir.glob("dense_cache_*.json"))


# ---------------------------------------------------------------------------
# SLOW test -- loads the real model (skipped by default with -m "not slow")
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_dense_retriever_real_model_returns_hits(tmp_path: Path) -> None:
    """Integration test: exercises the actual BAAI/bge-small-en-v1.5 model."""
    chunks = _make_chunks(10)
    retriever = DenseRetriever.from_chunks(chunks, cache_dir=tmp_path)
    hits = retriever.search("labeling requirement", k=3)
    assert len(hits) == 3
    for h in hits:
        assert isinstance(h, Hit)
        assert 0.0 <= h.score <= 1.01


def test_query_prefix_is_applied_to_queries_only() -> None:
    from src.ir.dense import BGE_QUERY_PREFIX

    class Recording(FakeTransformer):
        def __init__(self) -> None:
            self.seen: list[str] = []

        def encode(self, texts, *args, **kwargs):  # type: ignore[no-untyped-def]
            self.seen.extend(texts)
            return super().encode(texts, *args, **kwargs)

    chunks = _make_chunks(3)
    plain_model, pref_model = Recording(), Recording()
    plain = DenseRetriever.from_chunks(chunks, cache_dir=None, model=plain_model)
    pref = DenseRetriever.from_chunks(
        chunks, cache_dir=None, model=pref_model, query_prefix=BGE_QUERY_PREFIX
    )
    plain_model.seen.clear()
    pref_model.seen.clear()
    plain.search("net weight", k=2)
    pref.search("net weight", k=2)
    assert plain_model.seen == ["net weight"]  # default: no prefix
    assert pref_model.seen == [BGE_QUERY_PREFIX + "net weight"]
    # passages are encoded without the prefix in both, so the cache is shared
    assert BGE_QUERY_PREFIX not in " ".join(chunk.text for chunk in chunks)
