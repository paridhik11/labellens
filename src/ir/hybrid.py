"""Hybrid retrieval with Reciprocal Rank Fusion (RRF) of BM25 and dense results.

WHAT IS RECIPROCAL RANK FUSION (RRF)?
RRF is a simple, parameter-light way to merge two (or more) ranked lists into
one combined ranking. For every document d and ranker r, it contributes a score
of 1 / (k + rank_r(d)) where k is a smoothing constant (usually 60). Then all
per-ranker contributions for the same document are summed to get a final score.

Worked example (k=60):
  BM25 ranking:   doc_A rank 1, doc_B rank 2, doc_C rank 10
  Dense ranking:  doc_B rank 1, doc_A rank 3, doc_D rank 5

  doc_A: 1/(60+1) + 1/(60+3) = 0.0164 + 0.0156 = 0.0320
  doc_B: 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325  <- winner (ranked in both)
  doc_C: 1/(60+10)            = 0.0143
  doc_D: 1/(60+5)             = 0.0154

  Final order: doc_B, doc_A, doc_D, doc_C

Key insight: a document that appears high in BOTH lists beats one that appears
very high in only one list. This tolerates the fact that BM25 and dense often
disagree on exact ordering, while both being partially right.
"""
from __future__ import annotations

from collections import defaultdict

from src.common.schemas import Chunk, Hit
from src.ir.base import Retriever


class HybridRetriever:
    """Combines BM25 and dense retrievers using Reciprocal Rank Fusion.

    Satisfies the Retriever protocol defined in src.ir.base.
    """

    name = "hybrid"

    def __init__(
        self,
        bm25: Retriever,
        dense: Retriever,
        k: int = 60,
        bm25_weight: float = 1.0,
        dense_weight: float = 1.0,
    ) -> None:
        """Stores two retrievers and the RRF hyperparameter k.

        Args:
            bm25: A BM25Retriever (or any Retriever) for lexical search.
            dense: A DenseRetriever (or any Retriever) for semantic search.
            k: RRF smoothing constant. Higher values reduce the influence of rank
               differences. The standard value is 60.
            bm25_weight: Multiplicative weight for BM25 RRF scores.
            dense_weight: Multiplicative weight for dense RRF scores.
        """
        self._bm25 = bm25
        self._dense = dense
        self._k = k
        self._bm25_weight = bm25_weight
        self._dense_weight = dense_weight

    @staticmethod
    def _rrf_score(rank: int, k: int) -> float:
        """Computes the RRF score for a document at the given rank."""
        return 1.0 / (k + rank)

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Returns top-k chunks by RRF-fused BM25 and dense scores.

        Over-fetches (fetch_k = k * 3 or 50, whichever is larger) from each
        ranker so that documents unique to one list are still considered.
        """
        fetch_k = max(k * 3, 50)
        bm25_hits = self._bm25.search(query, k=fetch_k)
        dense_hits = self._dense.search(query, k=fetch_k)

        scores: dict[str, float] = defaultdict(float)
        texts: dict[str, str] = {}

        for hit in bm25_hits:
            scores[hit.doc_id] += self._bm25_weight * self._rrf_score(hit.rank, self._k)
            texts[hit.doc_id] = hit.text

        for hit in dense_hits:
            scores[hit.doc_id] += self._dense_weight * self._rrf_score(hit.rank, self._k)
            if hit.doc_id not in texts:
                texts[hit.doc_id] = hit.text

        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
        return [
            Hit(doc_id=doc_id, score=score, rank=r + 1, text=texts.get(doc_id, ""))
            for r, (doc_id, score) in enumerate(ranked)
        ]

    @classmethod
    def from_corpus(
        cls,
        docs: list[tuple[str, str]],
        chunks: list[Chunk] | None = None,
        bm25_weight: float = 1.0,
        dense_weight: float = 1.0,
        k_rrf: int = 60,
    ) -> "HybridRetriever":
        """Convenience builder for use in eval.py.

        Args:
            docs: list of (chunk_id, text) tuples for BM25 index construction.
            chunks: list of Chunk objects for dense index (can share same data).
                    If None, Chunk objects are reconstructed from docs.
            bm25_weight: Weight for BM25 component.
            dense_weight: Weight for dense component.
            k_rrf: RRF smoothing constant.
        """
        from src.ir.bm25 import BM25Retriever, InvertedIndex
        from src.ir.dense import DenseRetriever

        ix = InvertedIndex().build(docs)
        bm25 = BM25Retriever(ix)

        if chunks is None:
            chunks = [Chunk(chunk_id=cid, source="", text=txt) for cid, txt in docs]

        dense = DenseRetriever.from_chunks(chunks)

        return cls(bm25=bm25, dense=dense, k=k_rrf,
                   bm25_weight=bm25_weight, dense_weight=dense_weight)
