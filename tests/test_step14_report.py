"""Tests for src.ir.step14_report (bootstrap, selection, tables)."""
from __future__ import annotations

import math

import pytest

from src.ir.eval import QueryRow
from src.ir.step14_report import (
    diff_table,
    fmt_p,
    means_table,
    paired_bootstrap_ci,
    select,
    type_table,
)


def test_identical_systems_give_zero_diff_and_p_one() -> None:
    d, lo, hi, p = paired_bootstrap_ci([0.2, 0.5, 0.9], [0.2, 0.5, 0.9])
    assert d == 0 and lo == 0 and hi == 0 and p == 1.0


def test_clear_winner_has_small_p_and_positive_interval() -> None:
    a = [0.9] * 20
    b = [0.1] * 20
    d, lo, hi, p = paired_bootstrap_ci(a, b)
    assert d == pytest.approx(0.8)
    assert lo > 0 and hi >= lo
    assert p < 0.001


def test_bootstrap_is_reproducible_and_two_sided() -> None:
    a = [0.1, 0.9, 0.4, 0.6, 0.2, 0.8]
    b = [0.3, 0.5, 0.4, 0.5, 0.3, 0.6]
    assert paired_bootstrap_ci(a, b) == paired_bootstrap_ci(a, b)
    # swapping the systems flips the sign of the diff and keeps the p-value
    d1, lo1, hi1, p1 = paired_bootstrap_ci(a, b)
    d2, lo2, hi2, p2 = paired_bootstrap_ci(b, a)
    assert d1 == pytest.approx(-d2)
    assert lo1 == pytest.approx(-hi2)
    assert p1 == pytest.approx(p2)


def test_bootstrap_empty_and_length_mismatch() -> None:
    assert all(math.isnan(x) for x in paired_bootstrap_ci([], []))
    with pytest.raises(ValueError):
        paired_bootstrap_ci([0.1], [0.1, 0.2])


def test_fmt_p() -> None:
    assert fmt_p(0.0) == "p<0.0002"
    assert fmt_p(0.0314) == "p=0.031"
    assert fmt_p(float("nan")) == "p n/a"


def _pq(ndcg_a: list[float], ndcg_b: list[float]) -> dict:
    def block(v: list[float]) -> dict:
        return {"ndcg": v, "recall": v, "mrr": v, "map": v}

    return {"bm25": block(ndcg_a), "dense": block(ndcg_b)}


def test_select_keeps_aligned_subset() -> None:
    pq = _pq([0.1, 0.2, 0.3], [0.4, 0.5, 0.6])
    sub = select(pq, ["q1", "q2", "q3"], ["q1", "q3"])
    assert sub["bm25"]["ndcg"] == [0.1, 0.3]
    assert sub["dense"]["ndcg"] == [0.4, 0.6]


def test_tables_render_baseline_only_in_means() -> None:
    pq = _pq([0.0, 1.0], [1.0, 1.0])
    means = "\n".join(means_table(pq))
    assert "| bm25 | 0.500 |" in means
    diffs = "\n".join(diff_table(pq))
    assert "| dense |" in diffs
    assert "| bm25 |" not in diffs


def test_type_table_counts_flags_small_n_and_leaves_gaps_out() -> None:
    rows = [
        QueryRow("q1", "a", "device", "direct"),
        QueryRow("q2", "b", "device", "direct"),
        QueryRow("q3", "c", "device", "symbol"),
        QueryRow("q4", "d", "device", "symbol"),
    ]
    qids = ["q1", "q2", "q3", "q4"]
    pq = _pq([1.0, 0.0, 0.5, 0.0], [0.0, 0.0, 0.5, 0.0])
    lines = type_table(rows, ["q1", "q2", "q3"], pq, qids, ["q4"])
    text = "\n".join(lines)
    assert "| direct | 2 | 0 | 0.500 | 0.000 | n<5, descriptive only |" in text
    assert "| symbol | 1 | 1 | 0.500 | 0.500 | n<5, descriptive only |" in text
    assert "| vocab_mismatch | 0 | 0 | n/a | n/a | no queries |" in text


def test_holm_adjust_known_values_and_order() -> None:
    from src.ir.step14_report import holm_adjust

    # sorted p: 0.01, 0.02, 0.04 -> 3*0.01, 2*0.02, 1*0.04 = 0.03, 0.04, 0.04
    adj = holm_adjust([0.04, 0.01, 0.02])
    assert adj == pytest.approx([0.04, 0.03, 0.04])
    # never below raw, capped at 1, monotone in the sorted order
    adj2 = holm_adjust([0.5, 0.6, 0.9])
    assert adj2 == pytest.approx([1.0, 1.0, 1.0])
    assert all(a >= p for a, p in zip(holm_adjust([0.001, 0.2]), [0.001, 0.2], strict=True))
    assert holm_adjust([]) == []


def test_bootstrap_mean_interval_and_by_type_interval_threshold() -> None:
    from src.ir.step14_report import bootstrap_mean_interval

    m, lo, hi = bootstrap_mean_interval([0.5] * 10)
    assert m == lo == hi == 0.5
    m, lo, hi = bootstrap_mean_interval([0.0, 1.0] * 5)
    assert lo < m < hi and bootstrap_mean_interval([0.0, 1.0] * 5) == (m, lo, hi)
    assert all(math.isnan(x) for x in bootstrap_mean_interval([]))

    rows = [QueryRow(f"q{i}", "x", "device", "direct") for i in range(8)] + [
        QueryRow(f"s{i}", "x", "device", "symbol") for i in range(7)
    ]
    qids = [r.qid for r in rows]
    vals = [0.0, 1.0] * 4 + [0.5] * 7
    pq = {"bm25": {"ndcg": vals, "recall": vals, "mrr": vals, "map": vals}}
    text = "\n".join(type_table(rows, qids, pq, qids, []))
    assert "| direct | 8 | 0 | 0.500 [" in text  # n=8 gets an interval
    assert "| symbol | 7 | 0 | 0.500 |" in text  # n=7 does not


def test_part_section_and_overlap_helpers() -> None:
    from src.ir.step14_report import first_relevant_rank, part_of, section_of, term_overlap

    assert part_of("fda_21cfr801_s801.1_c1") == "21cfr801"
    assert section_of("fda_21cfr801_s801.1_c1") == "s801.1"
    assert first_relevant_rank(["a", "b", "c"], {"c": 1, "b": 0}) == 3
    assert first_relevant_rank(["a"], {"a": 0}) is None
    assert term_overlap("label of the device", "the device label text") == pytest.approx(1.0)
    assert term_overlap("", "anything") == 0.0


def test_hypotheses_flags_wrong_part_boundary_rank_and_vocabulary() -> None:
    from src.ir.step14_report import hypotheses

    text_of = {"fda_21cfr801_s801.1_c2": "name and place of business"}
    rels = {"fda_21cfr801_s801.1_c2": 2, "fda_21cfr801_s801.1_c1": 0, "fda_21cfr803_s803.1": 0}
    ranked = ["fda_21cfr803_s803.1", "fda_21cfr803_s803.2", "fda_21cfr803_s803.3",
              "fda_21cfr801_s801.1_c2"]
    out = " ".join(hypotheses("maker address on box", ranked, rels, text_of))
    assert "rank 4" in out and "wrong part" in out and "vocabulary" in out
    ranked2 = ["fda_21cfr801_s801.1_c1", "fda_21cfr801_s801.1_c2"]
    out2 = " ".join(hypotheses("name and place of business", ranked2, rels, text_of))
    assert "chunk boundary" in out2 and "wrong part" not in out2
    assert hypotheses("q", ["x"], {"x": 0}, {}) == ["no chunk graded >= 1 for this query (corpus gap)"]


def test_zero_ties_counts_per_system_and_all_zero() -> None:
    from src.ir.step14_report import zero_ties

    fd = {
        "names": ["a", "b"],
        "rows": [
            {"module": "device", "ndcg": {"a": 0.0, "b": 0.0}},
            {"module": "device", "ndcg": {"a": 0.0, "b": 0.4}},
            {"module": "medicine", "ndcg": {"a": 0.2, "b": 0.0}},
        ],
    }
    text = "\n".join(zero_ties(fd))
    assert "| device | 2 | 2 | 1 | 1 |" in text
    assert "| medicine | 1 | 0 | 1 | 0 |" in text
    assert "| both | 3 | 2 | 2 | 1 |" in text


def test_cluster_bootstrap_agreement_resamples_queries() -> None:
    from src.ir.step14_report import cluster_bootstrap_agreement

    # perfect agreement everywhere -> every interval collapses on 1.0
    h = {("q1", "a"): 0, ("q1", "b"): 2, ("q2", "a"): 1, ("q2", "b"): 0, ("q3", "a"): 2}
    res = cluster_bootstrap_agreement(h, dict(h), n=200)
    assert res["n_rows"] == 5 and res["n_queries"] == 3
    assert res["point"]["exact"] == 1.0
    assert res["ci"]["exact"] == (1.0, 1.0)
    # one query disagrees fully: exact agreement can only be 1, 2/3-ish or lower, and
    # the interval must include values below the point estimate but stay in [0, 1]
    llm = dict(h)
    llm[("q3", "a")] = 0
    res2 = cluster_bootstrap_agreement(h, llm, n=500)
    lo, hi = res2["ci"]["exact"]
    assert 0.0 <= lo < res2["point"]["exact"] <= hi <= 1.0
    # reproducible with the fixed seed
    assert cluster_bootstrap_agreement(h, llm, n=500) == res2
    with pytest.raises(ValueError):
        cluster_bootstrap_agreement({}, {})
