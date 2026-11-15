"""Tests for the pure parts of src.ir.step18_finetune (no model is loaded)."""
from __future__ import annotations

import pytest

from src.common.schemas import Hit
from src.ir.step18_finetune import build_groups, group_pairs, hard_negatives, split_by_section


class Listed:
    def __init__(self, ids):
        self.ids = ids

    def search(self, query, k=10):
        return [Hit(doc_id=d, score=1.0, rank=i + 1, text="") for i, d in enumerate(self.ids[:k])]


SECTION = {"p": "1.1", "sib": "1.1", "a": "2.1", "b": "3.1", "c": "4.1", "x": "9.9", "d": "5.1"}


def test_hard_negatives_skip_positive_same_section_and_excluded_and_interleave():
    bm25 = Listed(["p", "sib", "a", "x", "c"])
    dense = Listed(["b", "p", "a", "d", "c"])
    got = hard_negatives("q", "p", "1.1", bm25, dense, SECTION, excluded={"x"}, n=3)
    # position 0: bm25 p (the positive, skipped), dense b; position 2: bm25 a; position 3: bm25 x (excluded), dense d
    assert got == ["b", "a", "d"]
    assert "p" not in got and "sib" not in got and "x" not in got
    assert hard_negatives("q", "p", "1.1", Listed([]), Listed([]), SECTION, set()) == []


def test_build_groups_and_pairs_and_exclusion_guard():
    rows = [{"qid": "sq001", "query": "a query", "module": "device", "source_chunk": "p", "source_section": "1.1"}]
    groups = build_groups(rows, {"device": (Listed(["a", "b", "c"]), Listed(["c", "d"]))}, SECTION, set())
    assert groups[0]["pos"] == "p" and len(groups[0]["negs"]) == 3 and "p" not in groups[0]["negs"]
    texts = {c: f"text {c}" for c in SECTION}
    pairs = group_pairs(groups[0], texts)
    assert pairs[0] == ("a query", "text p") and len(pairs) == 4
    with pytest.raises(ValueError):
        build_groups(rows, {"device": (Listed([]), Listed([]))}, SECTION, {"p"})


def test_section_split_never_shares_a_section_and_is_deterministic():
    groups = [{"qid": f"q{i}", "section": f"s{i % 12}", "negs": []} for i in range(60)]
    tr, va = split_by_section(groups, frac=0.2, seed=42)
    assert {g["section"] for g in tr}.isdisjoint({g["section"] for g in va})
    assert len(tr) + len(va) == 60 and 10 <= len(va) <= 20
    assert split_by_section(groups, 0.2, 42) == (tr, va)
