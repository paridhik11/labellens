"""Tests for src.ir.split."""
from __future__ import annotations

from src.ir.eval import QueryRow
from src.ir.split import make_split


def _rows() -> list[QueryRow]:
    rows = []
    n = 0
    for qtype, counts in {"direct": (5, 2), "field_req": (3, 1), "symbol": (1, 0)}.items():
        for module, c in zip(("device", "medicine"), counts, strict=True):
            for _ in range(c):
                n += 1
                rows.append(QueryRow(f"q{n:02d}", f"text {n}", module, qtype))
    rows.append(QueryRow("q99", "nothing", "device", "no_answer"))
    return rows


def test_partition_is_complete_and_disjoint():
    rows = _rows()
    s = make_split(rows)
    dev, held = set(s["dev"]), set(s["heldout"])
    assert not dev & held
    assert dev | held == {r.qid for r in rows if r.qtype != "no_answer"}
    assert s["no_answer"] == ["q99"]


def test_same_seed_same_split_and_sizes_balanced():
    a, b = make_split(_rows(), 42), make_split(_rows(), 42)
    assert a == b
    assert abs(len(a["dev"]) - len(a["heldout"])) <= 1


def test_every_type_with_two_or_more_queries_is_in_both_halves():
    rows = _rows()
    s = make_split(rows)
    kind = {r.qid: r.qtype for r in rows}
    for qtype in ("direct", "field_req"):
        assert any(kind[q] == qtype for q in s["dev"])
        assert any(kind[q] == qtype for q in s["heldout"])
