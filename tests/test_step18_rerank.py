"""Tests for the pure helpers of src.ir.step18_rerank."""
from __future__ import annotations

from src.ir.step18_rerank import load_score_cache, save_score_cache, variant_name


def test_score_cache_round_trip_and_missing_file(tmp_path):
    path = tmp_path / "c.json"
    assert load_score_cache(path) == {}
    cache = {("what is a label?", "fda_21cfr801_s801.1_c1"): 0.25, ("q two", "c2"): -3.5}
    save_score_cache(path, "model-x", cache)
    assert load_score_cache(path) == cache
    save_score_cache(path, "model-x", {**cache, ("q three", "c3"): 1.0})  # overwrite is atomic and complete
    assert len(load_score_cache(path)) == 3


def test_variant_name():
    assert variant_name("hybrid", 30, "replace") == "hybrid+bge-reranker-base(top30,replace)"
    assert variant_name("hybrid+stem+prefix", 50, "blend", "x") == "hybrid+stem+prefix+x(top50,blend)"
