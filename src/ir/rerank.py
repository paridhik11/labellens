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

Three ways to use its scores (`mode`):
  replace  sort the candidates by cross-encoder score alone
  rrf      fuse the base rank and the cross-encoder rank with 1/(rrf_k + rank)
  blend    alpha * minmax(cross-encoder score) + (1 - alpha) * minmax(first-stage score); each
           list is scaled to 0..1 over the candidates first, alpha defaults to 0.5

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


def _minmax(values: list[float]) -> list[float]:
    """Scales values to [0, 1]; all-equal values become 0.5 so neither list dominates."""
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def _blend(ce: list[float], head: list[Hit], alpha: float) -> list[tuple[float, Hit]]:
    """Orders hits by alpha * minmax(cross-encoder) + (1 - alpha) * minmax(first-stage score)."""
    ce_n, base_n = _minmax(ce), _minmax([h.score for h in head])
    out = [(alpha * c + (1 - alpha) * b, h) for c, b, h in zip(ce_n, base_n, head, strict=True)]
    out.sort(key=lambda t: (-t[0], t[1].rank))
    return out


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
        score_cache: dict[tuple[str, str], float] | None = None,
        alpha: float = 0.5,
    ) -> None:
        """Args:
            base: retriever supplying the candidates (for example hybrid).
            model: a loaded scorer; if None, model_name is loaded on first use.
            model_name: Hugging Face id, loaded from the local cache only.
            top_n: how many base results are reranked.
            mode: 'replace', 'rrf' or 'blend' (see module docstring).
            rrf_k: smoothing constant for mode 'rrf'.
            max_length: tokens kept per (query, chunk) pair.
            batch_size: pairs per model call.
            name: system name shown in tables.
            score_cache: optional dict shared between rerankers so the same
                (query, chunk) pair is never scored twice.
            alpha: weight of the cross-encoder in mode 'blend' (the first-stage score gets 1 - alpha).
        """
        if mode not in {"replace", "rrf", "blend"}:
            raise ValueError(f"mode must be 'replace', 'rrf' or 'blend', got {mode!r}")
        self.alpha = alpha
        self.base = base
        self._model = model
        self.model_name = model_name
        self.top_n = top_n
        self.mode = mode
        self.rrf_k = rrf_k
        self.max_length = max_length
        self.batch_size = batch_size
        self.name = name
        self._cache: dict[tuple[str, str], float] = {} if score_cache is None else score_cache

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
        elif self.mode == "blend":
            ordered = _blend(ce, head, self.alpha)
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
