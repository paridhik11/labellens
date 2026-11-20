"""Tests for src.ir.step18_abstain (the statistics, no model is loaded)."""
from __future__ import annotations

import numpy as np

from src.ir.step18_abstain import (
    abstain_precision_recall,
    auroc,
    best_threshold,
    bootstrap_auroc,
    coverage,
    evaluate,
    halves,
    loo_logreg_abstain,
    loo_threshold_abstain,
    make_split,
    zscorer,
)


def test_split_is_stratified_disjoint_deterministic():
    pos = [f"q{i}" for i in range(17)]
    neg = [f"ab{i}" for i in range(10)]
    s = make_split(pos, neg)
    assert (len(s["dev"]["answerable"]), len(s["test"]["answerable"])) == (9, 8)
    assert (len(s["dev"]["no_answer"]), len(s["test"]["no_answer"])) == (5, 5)
    assert not set(s["dev"]["answerable"]) & set(s["test"]["answerable"])
    assert sorted(s["dev"]["answerable"] + s["test"]["answerable"]) == sorted(pos)
    assert make_split(pos, neg) == s and halves(pos)[0] == s["dev"]["answerable"]


def test_auroc_known_values():
    assert auroc([3, 4], [1, 2]) == 1.0
    assert auroc([1, 2], [3, 4]) == 0.0
    assert auroc([1, 3], [2, 2]) == 0.5
    assert auroc([2], [2]) == 0.5  # a tie counts one half


def test_bootstrap_interval_contains_the_estimate_and_separates_classes():
    pos, neg = [0.9, 0.8, 0.85, 0.7, 0.95], [0.2, 0.3, 0.75, 0.1]
    lo, hi = bootstrap_auroc(pos, neg, n_boot=2000)
    assert lo <= auroc(pos, neg) <= hi and 0 <= lo <= hi <= 1
    assert bootstrap_auroc(pos, neg, n_boot=2000) == (lo, hi)  # seeded
    assert bootstrap_auroc([5.0, 6.0], [1.0, 2.0], n_boot=500) == (1.0, 1.0)


def test_threshold_and_loo_abstention_on_separable_scores():
    s = [0.9, 0.8, 0.7, 0.2, 0.1, 0.3]
    y = [1, 1, 1, 0, 0, 0]
    assert 0.3 < best_threshold(s, y) < 0.7
    dec = loo_threshold_abstain(s, y)
    assert dec == [0, 0, 0, 1, 1, 1]
    assert abstain_precision_recall(dec, y) == (1.0, 1.0)


def test_precision_is_none_when_nothing_is_abstained_and_counts_correctly():
    assert abstain_precision_recall([0, 0, 0], [1, 0, 0]) == (None, 0.0)
    assert abstain_precision_recall([1, 1, 0, 0], [0, 1, 0, 1]) == (0.5, 0.5)


def test_logreg_loo_learns_a_clean_signal():
    rng = np.random.default_rng(0)
    pos = rng.normal(2.0, 0.3, size=(8, 4))
    neg = rng.normal(-2.0, 0.3, size=(6, 4))
    x = np.vstack([pos, neg])
    y = [1] * 8 + [0] * 6
    assert loo_logreg_abstain(x, y) == [0] * 8 + [1] * 6


def test_coverage_and_zscore_and_evaluate():
    assert coverage("tamper evident packaging", "The package must be tamper-evident and packaged") > 0
    assert coverage("zzz", "nothing here") == 0.0
    z = zscorer([1.0, 2.0, 3.0])
    assert abs(z(2.0)) < 1e-12 and z(3.0) > 0
    feat = {f"p{i}": {"bm25": 10 + i, "dense": 0.8, "ce_top": 0.9 - 0.01 * i, "ce_margin": 0.3, "coverage": 0.9}
            for i in range(5)}
    feat |= {f"n{i}": {"bm25": 3 + i, "dense": 0.5, "ce_top": 0.1 + 0.01 * i, "ce_margin": 0.05, "coverage": 0.3}
             for i in range(4)}
    labels = {q: int(q.startswith("p")) for q in feat}
    rows = evaluate(feat, labels, z_from=sorted(feat))
    by = {r["score"]: r for r in rows}
    assert by["ce_top"]["auroc"] == 1.0 and by["ce_top"]["precision"] == 1.0
    assert len(rows) == 4 and rows[-1]["auroc"] is None
