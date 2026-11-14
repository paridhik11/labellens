"""Tests for src/ir/step16_secondary.py."""
from __future__ import annotations

import pytest

from src.common.schemas import Hit
from src.ir.step16_abstain import AbstainQuery
from src.ir.step16_secondary import (
    build_scores,
    distinct_values,
    rank_gap,
    top_score,
    zscores,
)


def _hits(*scores: float) -> list[Hit]:
    return [Hit(doc_id=f"d{i}", score=s, rank=i + 1) for i, s in enumerate(scores)]


def test_zscores_mean_zero_and_constant() -> None:
    """Z-scores average to 0; a constant map gives zeros."""
    z = zscores({"a": 1.0, "b": 2.0, "c": 3.0})
    assert sum(z.values()) == pytest.approx(0.0)
    assert zscores({"a": 2.0, "b": 2.0}) == {"a": 0.0, "b": 0.0}


def test_top_score_and_rank_gap() -> None:
    """Gap is rank 1 minus rank 5, or the last hit when fewer than 5; empty gives 0."""
    h = _hits(1.0, 0.9, 0.8, 0.7, 0.6, 0.5)
    assert top_score(h) == 1.0
    assert rank_gap(h) == pytest.approx(0.4)
    assert rank_gap(_hits(1.0, 0.25)) == pytest.approx(0.75)
    assert rank_gap([]) == 0.0 and top_score([]) == 0.0


def test_distinct_values_rounds() -> None:
    """Values equal after rounding count once."""
    assert distinct_values({"a": 0.1234561, "b": 0.1234562, "c": 0.5}) == 2


def test_build_scores_keys_and_length_norm() -> None:
    """bm25 top is divided by the number of query terms (stopwords removed)."""
    qs = [AbstainQuery("a", "sunscreen labeling testing", "answerable"),
          AbstainQuery("n", "dietary supplement", "no_answer", "hard")]
    runs = {
        "bm25": {"a": _hits(6.0, 1.0), "n": _hits(2.0, 1.0)},
        "dense": {"a": _hits(0.8, 0.7), "n": _hits(0.5, 0.4)},
        "hybrid": {"a": _hits(0.03, 0.02), "n": _hits(0.02, 0.01)},
    }
    s = build_scores(runs, qs)
    assert set(s) == {
        "hybrid top RRF", "bm25 top", "bm25 top / query length", "dense top cosine",
        "dense gap rank1-rank5", "z-avg(bm25 top, dense top)",
    }
    assert s["bm25 top / query length"]["a"] == pytest.approx(2.0)
    assert s["z-avg(bm25 top, dense top)"]["a"] > s["z-avg(bm25 top, dense top)"]["n"]
