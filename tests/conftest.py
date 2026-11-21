"""Shared fixtures. The sentence reranker never loads its real cross-encoder in tests."""
from __future__ import annotations

from collections.abc import Iterator

import pytest

from src.rag import rerank


class _NoModel:
    """Stands in for an unavailable cross-encoder, so the pipeline takes its old chunk-quote fallback."""

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        raise RuntimeError("no cross-encoder in tests")


@pytest.fixture(autouse=True)
def _no_real_cross_encoder() -> Iterator[None]:
    rerank.set_scorer(_NoModel())
    yield
    rerank.set_scorer(None)
