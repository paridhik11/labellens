import math

from src.ir.metrics import average_precision, mrr, ndcg_at_k, recall_at_k

RELS = {"a": 2, "b": 1}


def test_perfect_ndcg():
    assert math.isclose(ndcg_at_k(["a", "b", "c"], RELS, 10), 1.0)


def test_ndcg_zero_when_miss():
    assert ndcg_at_k(["x", "y"], RELS, 10) == 0.0


def test_recall_and_mrr():
    assert recall_at_k(["x", "a"], RELS, 2) == 0.5
    assert mrr(["x", "a"], RELS) == 0.5


def test_average_precision():
    assert math.isclose(average_precision(["a", "x", "b"], RELS), (1 + 2 / 3) / 2)
