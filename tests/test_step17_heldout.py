"""Tests for the pure parts of src.ir.step17_heldout."""
from __future__ import annotations

from src.ir.step17_heldout import compare, primary_table
from src.ir.step17_report import Run, Spec


def _run(spec: Spec, vals: list[float]) -> Run:
    qids = [f"q{i}" for i in range(len(vals))]
    return Run(spec, qids, {"ndcg": vals, "cond": vals, "unj": [0.0] * len(vals)}, {q: [] for q in qids})


def test_compare_counts_wins_losses_ties():
    base = _run(Spec("bm25"), [0.5, 0.5, 0.5, 0.5])
    var = _run(Spec("bm25", stem=True), [0.7, 0.5, 0.3, 0.9])
    c = compare(var, base, base.qids)
    assert (c["wins"], c["losses"], c["ties"]) == (2, 1, 1)
    assert abs(c["diff"] - 0.1) < 1e-12 and abs(c["mean"] - 0.6) < 1e-12


def test_primary_table_holm_is_at_least_raw_p():
    base = _run(Spec("bm25"), [0.4] * 10)
    better = _run(Spec("bm25", stem=True), [0.5] * 10)
    same = _run(Spec("hybrid"), [0.4] * 10)
    cfg = {"variants": [
        {"id": "P1", "role": "primary", "name": better.spec.name, "vs": "bm25"},
        {"id": "P2", "role": "primary", "name": "hybrid", "vs": "bm25"},
        {"id": "P3", "role": "primary", "name": "bm25+stem", "vs": "bm25"},
    ]}
    runs = {"bm25": base, "bm25+stem": better, "hybrid": same}
    lines, res = primary_table(cfg, runs, base.qids)
    assert len(lines) == 2 + 3
    assert all(r["holm"] >= r["p"] - 1e-12 for r in res)
    assert res[1]["diff"] == 0.0 and res[1]["ties"] == 10
