"""Cross-encoder reranking of a base system's top results (Step 17d).

BI-ENCODER VS CROSS-ENCODER
Dense retrieval (bge-small) encodes the query and each chunk SEPARATELY, so chunk
vectors can be pre-computed and searched fast, but query and chunk never "see"
each other. A cross-encoder reads the query and ONE chunk together in a single
pass and outputs a relevance score. It is more accurate but too slow to run on
the whole corpus, so it only re-orders a short list (here the top 50 of hybrid).

Model: cross-encoder/ms-marco-MiniLM-L-6-v2 (22M parameters, 87 MB, already in the
local Hugging Face cache). It was trained on web search questions, not on
regulations, so it may not transfer; that is what the dev half will tell us.

Two ways to use its scores (`mode`):
  replace  sort the 50 by cross-encoder score alone
  rrf      fuse the base rank and the cross-encoder rank with 1/(rrf_k + rank)

Scores are cached per (query, chunk) so trying both modes costs one model pass.
"""
from __future__ import annotations

from typing import Protocol

from src.common.schemas import Hit
from src.ir.base import Retriever

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class PairScorer(Protocol):
    """Anything with predict(list of (query, text)) -> scores, like CrossEncoder."""

    def predict(self, pairs: list[tuple[str, str]], **kwargs: object) -> object:
        ...


class CrossEncoderReranker:
    """Reranks the top_n hits of a base retriever with a cross-encoder."""

    def __init__(
        self,
        base: Retriever,
        model: PairScorer | None = None,
        model_name: str = DEFAULT_MODEL,
        top_n: int = 50,
        mode: str = "replace",
        rrf_k: int = 60,
        max_length: int = 512,
        batch_size: int = 32,
        name: str = "rerank",
    ) -> None:
        """Args:
            base: retriever supplying the candidates (for example hybrid).
            model: a loaded scorer; if None, model_name is loaded on first use.
            model_name: Hugging Face id, loaded from the local cache only.
            top_n: how many base results are reranked.
            mode: 'replace' or 'rrf' (see module docstring).
            rrf_k: smoothing constant for mode 'rrf'.
            max_length: tokens kept per (query, chunk) pair.
            batch_size: pairs per model call.
            name: system name shown in tables.
        """
        if mode not in {"replace", "rrf"}:
            raise ValueError(f"mode must be 'replace' or 'rrf', got {mode!r}")
        self.base = base
        self._model = model
        self.model_name = model_name
        self.top_n = top_n
        self.mode = mode
        self.rrf_k = rrf_k
        self.max_length = max_length
        self.batch_size = batch_size
        self.name = name
        self._cache: dict[tuple[str, str], float] = {}

    def _scorer(self) -> PairScorer:
        if self._model is None:
            import os

            # Never download: fail loudly if the model is not already cached.
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, max_length=self.max_length)
        return self._model

    def scores(self, query: str, hits: list[Hit]) -> list[float]:
        """Cross-encoder scores for the hits, computing only pairs not yet cached."""
        todo = [h for h in hits if (query, h.doc_id) not in self._cache]
        if todo:
            raw = self._scorer().predict(
                [(query, h.text) for h in todo], batch_size=self.batch_size
            )
            for h, s in zip(todo, list(raw), strict=True):
                self._cache[(query, h.doc_id)] = float(s)
        return [self._cache[(query, h.doc_id)] for h in hits]

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Top-k after reranking the base top_n; deeper base hits keep their order."""
        hits = self.base.search(query, k=max(k, self.top_n))
        head, tail = hits[: self.top_n], hits[self.top_n:]
        ce = self.scores(query, head)
        if self.mode == "replace":
            ordered = list(zip(ce, head, strict=True))
            ordered.sort(key=lambda t: (-t[0], t[1].rank))
        else:
            ce_rank = {
                h.doc_id: r + 1
                for r, (_, h) in enumerate(
                    sorted(zip(ce, head, strict=True), key=lambda t: (-t[0], t[1].rank))
                )
            }
            fused = [
                (1.0 / (self.rrf_k + h.rank) + 1.0 / (self.rrf_k + ce_rank[h.doc_id]), h)
                for h in head
            ]
            fused.sort(key=lambda t: (-t[0], t[1].rank))
            ordered = fused
        out = [Hit(doc_id=h.doc_id, score=s, rank=i + 1, text=h.text)
               for i, (s, h) in enumerate(ordered)]
        low = min((h.score for h in out), default=0.0)
        out += [Hit(doc_id=h.doc_id, score=low, rank=len(out) + j + 1, text=h.text)
                for j, h in enumerate(tail)]
        return out[:k]
