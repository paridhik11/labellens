"""Part-aware boost: favour chunks from the CFR parts that match the query's topic (Step 17c).

THE IDEA (resource selection, borrowed from distributed IR)
The corpus is organised by CFR part: 21cfr801 is general device labeling, 21cfr830 is
the unique device identifier rule, 21cfr803 is adverse event reporting, and so on.
Many failures put a good chunk from the right part at rank 5 to 20 under chunks
from a neighbouring part. So first decide WHICH PARTS the query is about, then
nudge chunks from those parts upward.

HOW PARTS ARE CHOSEN (no hand-written topic list)
Every part becomes one big pseudo-document: all its chunk texts glued together.
The query is scored against these ~6 to 8 pseudo-documents with ordinary BM25.
The top `top_parts` parts are the query's "topic parts".

HOW THE BOOST WORKS
The base system (bm25 or hybrid) gives a ranked list. Each rank r gets a score
1 / (rrf_k + r), the same scale reciprocal rank fusion uses. A chunk from a topic
part has its score multiplied by (1 + beta). Then the list is re-sorted.

Worked example (rrf_k = 60, beta = 0.25):
  rank 1, other part:  1/61 = 0.01639
  rank 6, topic part:  1/66 * 1.25 = 0.01894   -> now ahead of rank 1
  rank 30, topic part: 1/90 * 1.25 = 0.01389   -> still behind rank 1
So beta decides how far a topic-part chunk may climb. beta = 0 changes nothing.

The boost never adds chunks: it only reorders the base system's top fetch_k.
"""
from __future__ import annotations

from collections import defaultdict

from src.common.schemas import Hit
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex


def part_of(chunk_id: str) -> str:
    """CFR part of a chunk id such as fda_21cfr801_s801.1_c1 -> '21cfr801'."""
    bits = chunk_id.split("_")
    return bits[1] if len(bits) > 1 else chunk_id


def build_part_index(docs: list[tuple[str, str]]) -> InvertedIndex:
    """Builds an index with one pseudo-document per CFR part.

    Args:
        docs: (chunk_id, text) pairs of the module being searched.
    """
    texts: dict[str, list[str]] = defaultdict(list)
    for chunk_id, text in docs:
        texts[part_of(chunk_id)].append(text)
    return InvertedIndex().build([(p, " ".join(t)) for p, t in sorted(texts.items())])


class PartBoostRetriever:
    """Wraps a retriever and boosts chunks from the query's topic parts."""

    def __init__(
        self,
        base: Retriever,
        part_index: InvertedIndex,
        top_parts: int = 1,
        beta: float = 0.25,
        fetch_k: int = 50,
        rrf_k: int = 60,
        name: str = "partboost",
    ) -> None:
        """Args:
            base: the retriever whose ranking is adjusted.
            part_index: output of build_part_index.
            top_parts: how many best-matching parts count as topic parts.
            beta: boost factor; topic-part scores are multiplied by 1 + beta.
            fetch_k: how deep into the base ranking the boost can reach.
            rrf_k: smoothing constant of the rank score 1 / (rrf_k + rank).
            name: system name shown in tables.
        """
        self.base = base
        self.part_search = BM25Retriever(part_index)
        self.top_parts = top_parts
        self.beta = beta
        self.fetch_k = fetch_k
        self.rrf_k = rrf_k
        self.name = name

    def rank_parts(self, query: str) -> list[tuple[str, float]]:
        """All parts that share a query word, best first, as (part, BM25 score)."""
        hits = self.part_search.search(query, k=self.part_search.ix.n_docs)
        return [(h.doc_id, h.score) for h in hits]

    def topic_parts(self, query: str) -> list[str]:
        """The top_parts best-matching parts (empty if no part matches any query word)."""
        return [p for p, _ in self.rank_parts(query)[: self.top_parts]]

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Top-k chunks of the base ranking after the topic-part boost."""
        hits = self.base.search(query, k=max(k, self.fetch_k))
        topics = set(self.topic_parts(query))
        scored = []
        for h in hits:
            s = 1.0 / (self.rrf_k + h.rank)
            if part_of(h.doc_id) in topics:
                s *= 1.0 + self.beta
            scored.append((s, h))
        scored.sort(key=lambda t: (-t[0], t[1].rank))
        return [
            Hit(doc_id=h.doc_id, score=s, rank=i + 1, text=h.text)
            for i, (s, h) in enumerate(scored[:k])
        ]
