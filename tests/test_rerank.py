"""Tests for src.ir.rerank (a fake scorer stands in for the real model)."""
from __future__ import annotations

import pytest

from src.common.schemas import Hit
from src.ir.rerank import CrossEncoderReranker


class FixedBase:
    name = "fixed"

    def __init__(self, n: int) -> None:
        self.n = n

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=f"d{i}", score=1.0, rank=i, text=f"text d{i}")
                for i in range(1, min(k, self.n) + 1)]


class FakeScorer:
    """Scores d<i> by a table; counts the pairs it was asked about."""

    def __init__(self, table: dict[str, float]) -> None:
        self.table = table
        self.calls = 0

    def predict(self, pairs, **kwargs):
        self.calls += len(pairs)
        return [self.table[text.split()[1]] for _, text in pairs]


TABLE = {"d1": 0.1, "d2": 0.9, "d3": 0.5, "d4": 0.0}


def test_replace_orders_by_cross_encoder_score():
    r = CrossEncoderReranker(FixedBase(4), model=FakeScorer(TABLE), top_n=4)
    assert [h.doc_id for h in r.search("q", k=4)] == ["d2", "d3", "d1", "d4"]


def test_rrf_blends_base_rank_and_cross_encoder_rank():
    r = CrossEncoderReranker(FixedBase(4), model=FakeScorer(TABLE), top_n=4, mode="rrf")
    ids = [h.doc_id for h in r.search("q", k=4)]
    # d1: base 1, ce 3; d2: base 2, ce 1 -> d2 first; d4 is last in both lists
    assert ids[0] == "d2" and ids[-1] == "d4"


def test_only_top_n_are_reranked_and_tail_keeps_order():
    scorer = FakeScorer({**TABLE, "d5": 99.0})
    r = CrossEncoderReranker(FixedBase(5), model=scorer, top_n=4)
    ids = [h.doc_id for h in r.search("q", k=5)]
    assert ids[:4] == ["d2", "d3", "d1", "d4"] and ids[4] == "d5"
    assert scorer.calls == 4


def test_scores_are_cached_across_modes_and_calls():
    scorer = FakeScorer(TABLE)
    r = CrossEncoderReranker(FixedBase(4), model=scorer, top_n=4)
    r.search("q", k=4)
    r.mode = "rrf"
    r.search("q", k=4)
    assert scorer.calls == 4


def test_bad_mode_is_rejected():
    with pytest.raises(ValueError):
        CrossEncoderReranker(FixedBase(1), model=FakeScorer(TABLE), mode="x")
