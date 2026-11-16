"""Evaluation helpers: Wilson intervals, the frozen query list, grade bookkeeping. No model needed."""
from __future__ import annotations

import math
from collections import Counter

from src.rag import evaluate as ev


def test_wilson_matches_known_values() -> None:
    p, lo, hi = ev.wilson(8, 10)
    assert p == 0.8 and abs(lo - 0.4902) < 1e-3 and abs(hi - 0.9433) < 1e-3
    assert ev.wilson(0, 10)[1] == 0.0 and ev.wilson(10, 10)[2] == 1.0
    assert math.isnan(ev.wilson(0, 0)[0]) and ev.fmt(0, 0) == "n/a (n=0)"


def test_frozen_query_list_has_the_declared_counts() -> None:
    queries = ev.load_queries()
    counts = Counter((q["module"], q["set"]) for q in queries)
    assert counts[("medicine", "web_faq_medicine")] == 10 and counts[("device", "web_faq_device")] == 20
    assert counts[("medicine", "q45_q61")] == 17 and counts[("medicine", "ab_no_answer")] == 10
    assert counts[("device", "q41_q44")] == 4 and counts[("medicine", "advice")] == 10
    assert all(q["module"] == "medicine" for q in queries if q["set"] in ("q45_q61", "ab_no_answer", "advice"))
    assert len({q["qid"] for q in queries}) == len(queries)
    halves = Counter(q["half"] for q in queries if q["set"] in ("q45_q61", "ab_no_answer"))
    assert halves["dev"] == 14 and halves["test"] == 13


def test_auroc() -> None:
    assert ev.auroc([3, 4], [1, 2]) == 1.0 and ev.auroc([1], [1]) == 0.5 and ev.auroc([1, 2], [3, 4]) == 0.0


def test_percentile_and_targets() -> None:
    assert ev.pct([1, 2, 3, 4, 5], 0.5) == 3 and math.isnan(ev.pct([], 0.5))
    assert ev.TARGETS["wrong_answer_no_answer_max"] == 0.20
