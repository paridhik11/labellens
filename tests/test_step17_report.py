"""Tests for the pure parts of src.ir.step17_report (no models are loaded)."""
from __future__ import annotations

import csv

from src.ir.eval import QueryRow
from src.ir.step17_report import (
    Run,
    Spec,
    best_of,
    is_gain,
    query_metrics,
    unjudged_rows,
    votes_specs,
    write_unjudged,
)

RELS = {"a": 2, "b": 1, "c": 0}


def test_unjudged_counts_as_zero_but_condensed_skips_it():
    m = query_metrics(["x", "a", "y", "b"], RELS)  # x, y have no grade
    assert abs(m["unj"] - 0.5) < 1e-12
    assert m["cond"] > m["ndcg"]  # a, b move up once x, y are removed
    assert abs(m["cond"] - 1.0) < 1e-12  # a (2) then b (1) is the ideal order


def test_fully_judged_list_gives_equal_numbers_and_zero_unjudged():
    m = query_metrics(["b", "a", "c"], RELS)
    assert m["ndcg"] == m["cond"] and m["unj"] == 0.0


def test_gain_needs_both_numbers_above_the_minimum():
    assert is_gain(0.02, 0.02)
    assert not is_gain(0.02, 0.005)
    assert not is_gain(0.01, 0.05)


def _run(name_w: float, ndcg: float) -> Run:
    return Run(Spec("bm25", exp=(name_w, "all", False)), ["q1"],
               {"ndcg": [ndcg], "cond": [ndcg], "unj": [0.0]}, {"q1": []})


def test_best_of_prefers_higher_and_keeps_earlier_on_ties():
    a, b, c = _run(0.3, 0.5), _run(0.5, 0.5), _run(1.0, 0.6)
    assert best_of([a, b], "ndcg") is a
    assert best_of([a, b, c], "ndcg") is c


def test_spec_names_and_families():
    assert Spec("bm25").name == "bm25" and Spec("bm25").family == "baseline"
    s = Spec("hybrid", exp=(0.5, "cfr", True), pb=(2, 0.25, "rrf_top3"), rr="rrf")
    assert s.name == "hybrid+exp(w=0.5,cfr,dense)+pb(top=2,beta=0.25,votes)+rr(rrf)"
    assert s.family == "combo" and Spec("hybrid", rr="rrf").family == "rr"
    assert len(votes_specs("bm25")) == 8


def test_unjudged_rows_lists_only_ungraded_top10_and_csv_round_trips(tmp_path):
    rows = [QueryRow("q1", "the query", "device", "direct")]
    run = Run(Spec("bm25"), ["q1"], {"ndcg": [0.0], "cond": [0.0], "unj": [0.5]},
              {"q1": ["a", "x", "c", "y"]})
    out = unjudged_rows(run, rows, {"q1": RELS}, {"x": "text  x", "y": "text y"}, "dev")
    assert [(r["chunk_id"], r["rank"]) for r in out] == [("x", 2), ("y", 4)]
    assert out[0]["text"] == "text x"
    path = tmp_path / "u.csv"
    write_unjudged(path, out)
    back = list(csv.DictReader(path.open(encoding="utf-8")))
    assert [r["chunk_id"] for r in back] == ["x", "y"] and back[0]["split"] == "dev"


def test_stem_and_prefix_specs_have_names_and_families():
    assert Spec("bm25", stem=True).name == "bm25+stem"
    assert Spec("hybrid", stem=True, prefix=True).name == "hybrid+stem+prefix"
    assert Spec("dense", prefix=True).name == "dense+prefix"
    assert Spec("hybrid", prefix=True).family == "basemod"
    assert Spec("dense").family == "baseline"
    assert Spec("hybrid", stem=True, rr="rrf").family == "combo"


def test_combination_specs_use_only_the_chosen_components():
    from src.ir.step17_report import combo_spec

    comps = {"basemod": Spec("hybrid", stem=True), "exp": Spec("hybrid", exp=(0.3, "all", True)),
             "pb": Spec("hybrid", pb=(1, 0.1, "bm25")), "rr": Spec("hybrid", rr="replace")}
    only_exp_pb = combo_spec("hybrid", comps, ["exp", "pb"])
    assert only_exp_pb == Spec("hybrid", exp=(0.3, "all", True), pb=(1, 0.1, "bm25"))
    boosted_rerank = combo_spec("hybrid", comps, ["pb", "rr"])
    assert boosted_rerank.rr == "rrf" and boosted_rerank.stem is False
    assert combo_spec("hybrid", comps, ["basemod", "rr"]) == Spec("hybrid", stem=True, rr="replace")
