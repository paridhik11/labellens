"""Builds the retriever the checker (and /search) uses, from one ``RetrievalSettings``.

There was no public retrieval entry point in ``src/ir``, so this wrapper only composes
public pieces (``load_chunks``, ``InvertedIndex``, ``BM25Retriever``, ``DenseRetriever``,
``HybridRetriever``). It does not edit ``src/ir``. Modules never mix: only chunks of
``settings.module`` are indexed.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from src.checker.settings import RETRIEVAL, RetrievalSettings
from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex, TfidfRetriever
from src.ir.search import load_chunks

CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "regs.jsonl"
METHODS = ("hybrid_rrf", "bm25", "tfidf", "dense")


@lru_cache(maxsize=4)
def module_chunks(module: str, corpus: str | Path = CORPUS_PATH) -> dict[str, Chunk]:
    """Chunks of one module, keyed by chunk id. Read once per process; callers must not modify the dict."""
    return {cid: c for cid, c in load_chunks(corpus).items() if c.module == module}


def build_retriever(
    settings: RetrievalSettings, chunks: dict[str, Chunk], *, model: object | None = None,
    cache_dir: Path | None = None,
) -> Retriever:
    """Build the retriever described by ``settings`` over ``chunks``.

    ``model`` and ``cache_dir`` exist so tests can pass a fake encoder. Dense and hybrid
    need sentence-transformers; bm25 and tfidf do not.
    """
    if settings.method not in METHODS:
        raise ValueError(f"unknown retrieval method {settings.method!r}")
    docs = [(c.chunk_id, c.text) for c in chunks.values()]
    index = InvertedIndex(stem=settings.stem).build(docs)
    if settings.method == "tfidf":
        return TfidfRetriever(index)
    bm25 = BM25Retriever(index)
    if settings.method == "bm25":
        return bm25
    from src.ir.dense import BGE_QUERY_PREFIX, CACHE_DIR, DenseRetriever
    from src.ir.hybrid import HybridRetriever

    dense = DenseRetriever.from_chunks(
        list(chunks.values()), model=model, cache_dir=CACHE_DIR if cache_dir is None else cache_dir,
        query_prefix=BGE_QUERY_PREFIX if settings.prefix else "",
    )
    if settings.method == "dense":
        return dense
    return HybridRetriever(bm25=bm25, dense=dense, k=settings.rrf_k)


@lru_cache(maxsize=4)
def default_retriever(settings: RetrievalSettings = RETRIEVAL) -> Retriever:
    """Process-wide retriever for ``settings`` (built once; the first call loads the model)."""
    return build_retriever(settings, module_chunks(settings.module))
