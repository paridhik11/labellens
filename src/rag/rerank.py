"""Sentence reranker display (reports/rag_rerank_plan.md): no language model, only a small cross-encoder.

The retrieved chunks are split into sentences (`selection.build_candidates`). A cross-encoder scores each sentence
against the question; the answer is the top sentences whose raw score reaches a threshold, each cited to its chunk.
Every shown sentence is copied from a retrieved chunk.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.common.schemas import Chunk
from src.rag import selection

CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "rag" / "rag_rerank_config.json"

MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MAX_LENGTH = 512
TOP = 3
SCORE_NAME = "rerank_logit"


class Scorer(Protocol):
    """Anything that scores (question, sentence) pairs, higher is more relevant."""

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        """One raw score per pair."""
        ...


class CrossEncoderScorer:
    """MiniLM cross-encoder from the local cache (never downloads). Raw logits, no sigmoid."""

    def __init__(self, model_name: str = MODEL, max_length: int = MAX_LENGTH) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self._model: object | None = None

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        """Raw logits for the pairs (loads the model on first use)."""
        if self._model is None:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, max_length=self.max_length)
        import torch

        raw = self._model.predict(pairs, batch_size=32, activation_fn=torch.nn.Identity())  # type: ignore[attr-defined]
        return [float(s) for s in raw]


_SCORER: Scorer | None = None


def get_scorer() -> Scorer:
    """The shared scorer (tests replace it with `set_scorer`)."""
    global _SCORER
    if _SCORER is None:
        _SCORER = CrossEncoderScorer()
    return _SCORER


def set_scorer(scorer: Scorer | None) -> None:
    """Replace the shared scorer, or reset it with None."""
    global _SCORER
    _SCORER = scorer


@dataclass(frozen=True)
class Scored:
    """A candidate sentence with its cross-encoder score."""

    candidate: selection.Candidate
    score: float


def rank_sentences(question: str, chunks: list[Chunk], scorer: Scorer | None = None) -> list[Scored]:
    """All candidate sentences of the chunks scored against the question, best first (ties keep retrieval order)."""
    candidates = selection.build_candidates(chunks)
    if not candidates:
        return []
    scores = (scorer or get_scorer()).score([(question, c.text) for c in candidates])
    ranked = sorted(zip(candidates, scores, strict=True), key=lambda p: (-p[1], p[0].num))
    return [Scored(c, float(s)) for c, s in ranked]


def top_sentences(ranked: list[Scored], threshold: float, top: int = TOP) -> list[Scored]:
    """The best `top` sentences whose score is at least the threshold, in score order."""
    return [s for s in ranked[:top] if s.score >= threshold]


def frozen_threshold(path: Path = CONFIG_PATH) -> float | None:
    """The threshold T written at freeze time (tuned on the dev half), or None when no config exists."""
    if not path.exists():
        return None
    return float(json.loads(path.read_text(encoding="utf-8"))["threshold_T"])
