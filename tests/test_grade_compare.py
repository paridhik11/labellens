"""Tests for src.ir.grade_compare (agreement, Kendall tau, ranking, report)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.common.schemas import Hit
from src.ir.eval import QueryRow
from src.ir.grade_compare import (
    agreement_report,
    bootstrap_mean_ci,
    build_report,
    confusion,
    kendall_tau,
    load_human_grades,
    merge_human,
    rank_systems,
    to_qrels,
    top_k_grade_distribution,
    usable_queries,
    weighted_kappa,
)


class FakeSystem:
    """Returns a fixed ranking for every query."""

    def __init__(self, name: str, ranking: list[str]) -> None:
        self.name = name
        self.ranking = ranking

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=d, score=1.0, rank=i) for i, d in enumerate(self.ranking[:k])]


def test_weighted_kappa_perfect_and_known_values() -> None:
    assert weighted_kappa([0, 1, 2], [0, 1, 2]) == pytest.approx(1.0)
    a, b = [0, 1, 2, 2], [0, 1, 2, 1]
    # hand computed: observed 0.0625, expected 0.3125 -> 1 - 0.2 = 0.8
    assert weighted_kappa(a, b, "quadratic") == pytest.approx(0.8)
    # linear: observed 0.125, expected 0.4375 -> 1 - 0.2857...
    assert weighted_kappa(a, b, "linear") == pytest.approx(1 - 0.125 / 0.4375)


def test_weighted_kappa_big_miss_costs_more_than_small_miss() -> None:
    base = [0, 0, 1, 1, 2, 2]
    small = [0, 0, 1, 1, 2, 1]
    big = [0, 0, 1, 1, 2, 0]
    assert weighted_kappa(base, small) > weighted_kappa(base, big)


def test_weighted_kappa_validates_input() -> None:
    with pytest.raises(ValueError):
        weighted_kappa([], [])
    with pytest.raises(ValueError):
        weighted_kappa([0, 1], [0])
    with pytest.raises(ValueError):
        weighted_kappa([0, 1], [0, 1], "cubic")


def test_agreement_report_binary_numbers() -> None:
    a = {("q", "k1"): 0, ("q", "k2"): 1, ("q", "k3"): 2, ("q", "k4"): 2}
    b = {("q", "k1"): 0, ("q", "k2"): 0, ("q", "k3"): 2, ("q", "k4"): 1, ("q", "k5"): 2}
    r = agreement_report(a, b)  # k5 is not graded by a, so it is ignored
    assert r["n"] == 4
    assert r["exact"] == pytest.approx(0.5)
    assert r["binary_agreement"] == pytest.approx(0.75)
    # pa=0.75, pb=0.5, pe=0.5, kappa=(0.75-0.5)/0.5
    assert r["binary_kappa"] == pytest.approx(0.5)
    assert confusion(a, b)[(2, 1)] == 1


def test_agreement_report_needs_overlap() -> None:
    with pytest.raises(ValueError):
        agreement_report({("q", "a"): 1}, {("q", "b"): 1})


def test_kendall_tau_values() -> None:
    assert kendall_tau([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert kendall_tau([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert kendall_tau([1, 2, 3, 4], [1, 2, 4, 3]) == pytest.approx(4 / 6)
    # tau-b with a tie in x: 2 concordant, 1 tie in x -> 2 / sqrt(3 * 2)
    assert kendall_tau([1, 1, 2], [1, 2, 3]) == pytest.approx(2 / 6**0.5)
    with pytest.raises(ValueError):
        kendall_tau([1], [1])


def test_merge_human_first_file_wins() -> None:
    first = {("q", "a"): 2}
    second = {("q", "a"): 0, ("q", "b"): 1}
    assert merge_human([first, second]) == {("q", "a"): 2, ("q", "b"): 1}


def test_to_qrels_and_usable_queries() -> None:
    h = to_qrels({("q1", "a"): 2, ("q2", "a"): 0, ("q3", "a"): 1})
    llm = to_qrels({("q1", "a"): 1, ("q2", "a"): 1, ("q3", "a"): 0})
    # q1 ok; q2 gap under human; q3 gap under LLM; q4 not graded
    assert usable_queries([h, llm], ["q1", "q2", "q3", "q4"]) == ["q1"]


def test_rank_systems_orders_best_first() -> None:
    res = {"a": {"ndcg": 0.2}, "b": {"ndcg": 0.5}, "c": {"ndcg": 0.4}}
    assert rank_systems(res) == ["b", "c", "a"]


def test_top_k_grade_distribution_counts_ungraded_as_zero() -> None:
    sys_a = FakeSystem("a", ["d1", "d2", "d3", "d4"])
    grades = {("q1", "d1"): 2, ("q1", "d2"): 1, ("q1", "d3"): 0}
    d = top_k_grade_distribution([sys_a], {"q1": "text"}, grades, k=4)["a"]
    assert d["g2"] == pytest.approx(0.25)
    assert d["g1"] == pytest.approx(0.25)
    assert d["g0"] == pytest.approx(0.5)
    assert d["ungraded"] == 1 and d["total"] == 4


def test_load_human_grades_skips_blank_and_rejects_bad(tmp_path: Path) -> None:
    p = tmp_path / "h.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qid", "query", "chunk_id", "grade"])
        w.writerow(["q1", "x", "a", "2"])
        w.writerow(["q1", "x", "b", ""])
    assert load_human_grades(p) == {("q1", "a"): 2}
    bad = tmp_path / "bad.csv"
    bad.write_text("qid,query,chunk_id,grade\nq1,x,a,5\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_human_grades(bad)


def test_build_report_end_to_end_small() -> None:
    human_a = {("q1", "a"): 2, ("q1", "b"): 0, ("q1", "c"): 1}
    human_b = {("q1", "a"): 2, ("q1", "b"): 1, ("q1", "c"): 1}
    llm = {("q1", "a"): 2, ("q1", "b"): 0, ("q1", "c"): 0}
    systems = [FakeSystem("good", ["a", "c", "b"]), FakeSystem("bad", ["b", "c", "a"])]
    rows = [QueryRow("q1", "text", "device", "direct")]
    md = build_report({"pari": human_a, "parth": human_b}, llm, {"device": systems}, rows, "test-model")
    assert "LLM vs human agreement" in md
    assert "Human vs human (pari vs parth" in md
    assert "Kendall's tau" in md
    # the good system must be ranked 1 by the human qrels
    good_line = next(ln for ln in md.splitlines() if ln.startswith("| good |") and "nDCG" not in ln)
    assert good_line.split("|")[4].strip() == "1"


def test_bootstrap_mean_ci_basic_properties() -> None:
    mean, lo, hi = bootstrap_mean_ci([0.1, 0.1, 0.1, 0.1])
    assert mean == pytest.approx(0.1) and lo == pytest.approx(0.1) and hi == pytest.approx(0.1)
    vals = [-0.2, -0.1, 0.0, 0.1, -0.3, -0.05]
    m, lo, hi = bootstrap_mean_ci(vals, n=2000)
    assert lo <= m <= hi
    assert (m, lo, hi) == bootstrap_mean_ci(vals, n=2000)  # fixed seed, reproducible
    # all-negative values: the whole interval stays below zero
    assert bootstrap_mean_ci([-0.1, -0.2, -0.15, -0.12], n=2000)[2] < 0
    with pytest.raises(ValueError):
        bootstrap_mean_ci([])


def test_build_report_has_headline_no_answer_split_and_ci() -> None:
    human_a = {("q1", "a"): 2, ("q1", "b"): 0, ("q1", "c"): 1, ("q2", "x"): 0, ("q2", "y"): 0}
    human_b = {("q1", "a"): 2, ("q1", "b"): 1, ("q1", "c"): 1}
    llm = {("q1", "a"): 2, ("q1", "b"): 0, ("q1", "c"): 0, ("q2", "x"): 0, ("q2", "y"): 0}
    systems = [FakeSystem("good", ["a", "c", "b"]), FakeSystem("bad", ["b", "c", "a"])]
    rows = [QueryRow("q1", "t", "device", "direct"), QueryRow("q2", "t2", "device", "no_answer")]
    md = build_report({"pari": human_a, "parth": human_b}, llm, {"device": systems}, rows)
    assert "pari only (headline)" in md
    assert "Excluding no_answer queries (q2)" in md
    assert "bootstrap 95% interval" in md
    assert "Systems whose mean difference is negative" in md
    # headline row comes before the merged row
    assert md.index("pari only (headline)") < md.index("all human rows (merged)")
