"""Tests for src.ir.fusion."""
from __future__ import annotations

import pytest

from src.common.schemas import Hit
from src.ir.fusion import FusionRetriever
from src.ir.hybrid import HybridRetriever


class Listed:
    """Returns a fixed ranking whatever the query."""

    def __init__(self, ids: list[str], name: str = "x") -> None:
        self.ids, self.name = ids, name

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=d, score=1.0, rank=i + 1, text=f"t {d}") for i, d in enumerate(self.ids[:k])]


A = ["a", "b", "c", "d", "e"]
B = ["c", "a", "f", "b", "g"]
C = ["g", "f", "e", "d", "c"]


def test_two_lists_match_hybrid_exactly():
    fused = FusionRetriever([Listed(A), Listed(B)]).search("q", k=7)
    hybrid = HybridRetriever(Listed(A), Listed(B)).search("q", k=7)
    assert [h.doc_id for h in fused] == [h.doc_id for h in hybrid]
    assert [round(h.score, 12) for h in fused] == [round(h.score, 12) for h in hybrid]


def test_three_lists_sum_reciprocal_ranks():
    out = FusionRetriever([Listed(A), Listed(B), Listed(C)]).search("q", k=3)
    score_c = 1 / 63 + 1 / 61 + 1 / 65  # rank 3 in A, rank 1 in B, rank 5 in C
    top = {h.doc_id: h.score for h in FusionRetriever([Listed(A), Listed(B), Listed(C)]).search("q", k=10)}
    assert abs(top["c"] - score_c) < 1e-12
    assert [h.rank for h in out] == [1, 2, 3]


def test_weights_change_the_order_and_bad_arguments_fail():
    heavy = FusionRetriever([Listed(A), Listed(B)], weights=[10.0, 1.0]).search("q", k=2)
    assert heavy[0].doc_id == "a"
    with pytest.raises(ValueError):
        FusionRetriever([])
    with pytest.raises(ValueError):
        FusionRetriever([Listed(A)], weights=[1.0, 2.0])
