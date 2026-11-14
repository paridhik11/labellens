"""Tests for src/ir/step16_abstain.py (abstention evaluation helpers)."""
from __future__ import annotations

import pytest

from src.common.schemas import Hit
from src.ir.eval import load_query_rows
from src.ir.step16_abstain import (
    AbstainQuery,
    auroc,
    best_threshold,
    bootstrap_auroc,
    evaluate_feature,
    features,
    listing_rows,
    load_abstain_queries,
    loo_abstain,
    no_answer_with_grade2,
    pos_neg,
    precision_recall_abstain,
    write_query_tsv,
)


def _queries() -> list[AbstainQuery]:
    """Six queries: three answerable, two hard and one easy no_answer."""
    return [
        AbstainQuery("a1", "alpha", "answerable"),
        AbstainQuery("a2", "beta", "answerable"),
        AbstainQuery("a3", "gamma", "answerable"),
        AbstainQuery("n1", "delta", "no_answer", "hard"),
        AbstainQuery("n2", "eps", "no_answer", "hard"),
        AbstainQuery("n3", "zeta", "no_answer", "easy"),
    ]


def test_auroc_worked_example() -> None:
    """The docstring example: pos [0.9, 0.5], neg [0.5, 0.1] gives 0.875."""
    assert auroc([0.9, 0.5], [0.5, 0.1]) == pytest.approx(0.875)


def test_auroc_perfect_inverted_and_ties() -> None:
    """Perfect separation is 1, the reverse is 0, all ties is 0.5."""
    assert auroc([3.0, 4.0], [1.0, 2.0]) == 1.0
    assert auroc([1.0, 2.0], [3.0, 4.0]) == 0.0
    assert auroc([1.0, 1.0], [1.0, 1.0]) == 0.5
    with pytest.raises(ValueError):
        auroc([], [1.0])


def test_bootstrap_is_reproducible_and_brackets_estimate() -> None:
    """Same seed gives the same interval, the interval lies in [0, 1] and brackets AUROC."""
    pos = [0.9, 0.8, 0.7, 0.4, 0.95]
    neg = [0.5, 0.3, 0.6, 0.2, 0.45]
    a = bootstrap_auroc(pos, neg, n=500, seed=42)
    b = bootstrap_auroc(pos, neg, n=500, seed=42)
    assert a == b
    lo, hi = a
    assert 0.0 <= lo <= auroc(pos, neg) <= hi <= 1.0


def test_best_threshold_separates_clean_data() -> None:
    """With clean separation the threshold falls between the classes."""
    scores = [0.1, 0.2, 0.8, 0.9]
    labels = [0, 0, 1, 1]
    t = best_threshold(scores, labels)
    assert 0.2 < t < 0.8


def test_loo_abstain_on_separable_data() -> None:
    """Leave-one-out abstains exactly on the low-score (no_answer) queries."""
    scores = [0.1, 0.2, 0.15, 0.8, 0.9, 0.85]
    labels = [0, 0, 0, 1, 1, 1]
    assert loo_abstain(scores, labels) == [True, True, True, False, False, False]


def test_precision_recall_abstain() -> None:
    """no_answer (label 0) is the positive class; precision is None if never abstaining."""
    prec, rec = precision_recall_abstain([True, True, False, False], [0, 1, 0, 1])
    assert prec == 0.5
    assert rec == 0.5
    prec, rec = precision_recall_abstain([False, False], [0, 1])
    assert prec is None
    assert rec == 0.0


def test_pos_neg_difficulty_filter() -> None:
    """difficulty keeps only the no_answer queries of that difficulty."""
    scores = {q.qid: float(i) for i, q in enumerate(_queries())}
    pos, neg = pos_neg(scores, _queries())
    assert pos == [0.0, 1.0, 2.0]
    assert neg == [3.0, 4.0, 5.0]
    assert pos_neg(scores, _queries(), "easy")[1] == [5.0]
    assert pos_neg(scores, _queries(), "hard")[1] == [3.0, 4.0]


def test_evaluate_feature_perfect_split() -> None:
    """A perfectly separating score gives AUROC 1 and perfect LOO abstention."""
    qs = _queries()
    scores = {"a1": 0.9, "a2": 0.8, "a3": 0.85, "n1": 0.1, "n2": 0.2, "n3": 0.15}
    r = evaluate_feature(scores, qs, n_boot=200)
    assert r["all"]["auroc"] == 1.0  # type: ignore[index]
    assert r["precision"] == 1.0
    assert r["recall"] == 1.0
    assert r["recall_hard"] == 1.0
    assert r["recall_easy"] == 1.0


def test_features_top_and_margin() -> None:
    """top is the rank-1 score, margin is rank 1 minus rank 2 (0 for missing hits)."""
    runs = {
        "s": {
            "q": [Hit(doc_id="a", score=0.9, rank=1), Hit(doc_id="b", score=0.6, rank=2)],
            "one": [Hit(doc_id="a", score=0.5, rank=1)],
            "none": [],
        }
    }
    f = features(runs, "q", "s")
    assert f["top"] == 0.9
    assert f["margin"] == pytest.approx(0.3)
    assert features(runs, "one", "s") == {"top": 0.5, "margin": 0.5}
    assert features(runs, "none", "s") == {"top": 0.0, "margin": 0.0}


def test_listing_rows_depth() -> None:
    """listing_rows keeps only the top `depth` hits per query and system."""
    hits = [Hit(doc_id=f"d{i}", score=1.0 - i / 10, rank=i + 1) for i in range(5)]
    rows = listing_rows({"bm25": {"q": hits}}, depth=3)
    assert [r["chunk_id"] for r in rows] == ["d0", "d1", "d2"]
    assert rows[0]["system"] == "bm25"
    assert rows[0]["rank"] == "1"


def test_no_answer_with_grade2_lists_only_no_answer() -> None:
    """Only no_answer queries with a grade >= 2 chunk are listed, with sorted chunk ids."""
    qrels = {"a1": {"c1": 2}, "n1": {"c2": 2, "c1": 2, "c3": 1}, "n2": {"c4": 1}}
    assert no_answer_with_grade2(_queries(), qrels) == {"n1": ["c1", "c2"]}


def test_load_abstain_queries_validation(tmp_path) -> None:
    """Unknown labels and a missing difficulty on no_answer rows are rejected."""
    good = tmp_path / "good.csv"
    good.write_text(
        "qid,text,label,difficulty,rationale\n"
        "a1,one,answerable,,r\n"
        "n1,two,no_answer,hard,r\n",
        encoding="utf-8",
    )
    qs = load_abstain_queries(good)
    assert [q.qid for q in qs] == ["a1", "n1"]
    assert qs[1].difficulty == "hard"
    bad = tmp_path / "bad.csv"
    bad.write_text("qid,text,label,difficulty,rationale\nn1,two,no_answer,,r\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_abstain_queries(bad)
    worse = tmp_path / "worse.csv"
    worse.write_text("qid,text,label,difficulty,rationale\nx,two,maybe,,r\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_abstain_queries(worse)


def test_write_query_tsv_roundtrip(tmp_path) -> None:
    """The TSV is readable by the existing query loader and marks module and type."""
    out = tmp_path / "q.tsv"
    write_query_tsv(_queries(), out)
    rows = load_query_rows(out)
    assert len(rows) == 6
    assert rows[0].module == "medicine"
    assert rows[3].qtype == "no_answer"
