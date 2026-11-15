"""N-way reciprocal rank fusion (Step 18).

HybridRetriever fuses exactly two lists (BM25 and one dense model). The ensembles in Step 18
fuse three: BM25 plus two embedders. RRF works the same for any number of lists: a chunk
scores the sum over lists of weight / (k + rank in that list), and the sums are sorted.

With two lists, equal weights, k=60 and the same fetch depth, this gives the same ranking as
HybridRetriever (a test checks that), so a baseline built here is the same baseline as before.
"""
from __future__ import annotations

from collections import defaultdict

from src.common.schemas import Hit
from src.ir.base import Retriever


class FusionRetriever:
    """Reciprocal rank fusion of any number of retrievers."""

    def __init__(self, parts: list[Retriever], k: int = 60, weights: list[float] | None = None,
                 name: str = "fusion") -> None:
        """Args:
            parts: the retrievers whose rankings are fused.
            k: RRF smoothing constant (60 is the usual value).
            weights: one weight per retriever, 1.0 each by default.
            name: system name shown in tables.
        """
        if not parts:
            raise ValueError("need at least one retriever")
        self.parts = parts
        self.k = k
        self.weights = weights or [1.0] * len(parts)
        if len(self.weights) != len(parts):
            raise ValueError("one weight per retriever")
        self.name = name

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Top-k chunks by fused score. Fetches max(3k, 50) from every retriever, as HybridRetriever does."""
        fetch_k = max(k * 3, 50)
        scores: dict[str, float] = defaultdict(float)
        texts: dict[str, str] = {}
        for part, w in zip(self.parts, self.weights, strict=True):
            for hit in part.search(query, k=fetch_k):
                scores[hit.doc_id] += w / (self.k + hit.rank)
                texts.setdefault(hit.doc_id, hit.text)
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
        return [Hit(doc_id=d, score=s, rank=i + 1, text=texts.get(d, "")) for i, (d, s) in enumerate(ranked)]
