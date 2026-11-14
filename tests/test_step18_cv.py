"""Tests for src.ir.step18_cv (folds, keep rule, log, unjudged CSV)."""
from __future__ import annotations

import csv

from src.ir.eval import QueryRow
from src.ir.step18_cv import (
    decide,
    evaluate_experiment,
    experiment_markdown,
    make_folds,
    update_unjudged_csv,
    upsert_section,
)

JUDGED = [f"d{i}" for i in range(12)]


def _rows(n_device: int = 30, n_med: int = 15) -> list[QueryRow]:
    rows = []
    types = ["direct", "field_req", "vocab_mismatch"]
    for i in range(n_device):
        rows.append(QueryRow(f"q{i:02d}", "t", "device", types[i % 3]))
    for i in range(n_med):
        rows.append(QueryRow(f"m{i:02d}", "t", "medicine", types[i % 3]))
    rows.append(QueryRow("q99", "t", "device", "no_answer"))
    return rows


def test_folds_partition_balanced_deterministic_and_stratified():
    rows = _rows()
    a, b = make_folds(rows), make_folds(rows)
    assert a == b and a["k"] == 5
    flat = [q for f in a["folds"] for q in f]
    assert len(flat) == len(set(flat)) == 45 and "q99" not in flat and a["no_answer"] == ["q99"]
    sizes = [len(f) for f in a["folds"]]
    assert max(sizes) - min(sizes) <= 1
    info = {r.qid: r for r in rows}
    for f in a["folds"]:  # every fold sees both modules
        assert {info[q].module for q in f} == {"device", "medicine"}


def _folds(qids: list[str]) -> dict:
    return {"k": 5, "folds": [qids[i::5] for i in range(5)], "seed": 42, "no_answer": []}


def _setup(gains: dict[str, int | None], n: int = 25):
    """Each query: relevant doc 'a'. Base puts it at rank 4; variant at rank 1 when gains[q] is set."""
    qids = [f"q{i:02d}" for i in range(n)]
    qrels = {q: {**{d: 0 for d in JUDGED}, "a": 2} for q in qids}
    base = {q: ["d1", "d2", "d3", "a", "d4", "d5"] for q in qids}
    var = {q: (["a", "d1", "d2", "d3", "d4", "d5"] if gains.get(q, 0) else list(base[q])) for q in qids}
    return qids, qrels, base, var


def test_kept_when_gain_is_broad():
    qids, qrels, base, var = _setup({q: 1 for q in [f"q{i:02d}" for i in range(25)]})
    res = evaluate_experiment("T1", "broad", base, var, qrels, _folds(qids))
    decision, _ = decide(res)
    assert decision == "KEPT" and res.folds_won() == 5 and res.unjudged10() == 0.0


def test_dropped_when_driven_by_two_queries():
    qids, qrels, base, var = _setup({"q00": 1, "q01": 1})
    # make the two gains huge by pushing their base rank of 'a' off the top 10
    for q in ("q00", "q01"):
        base[q] = [f"d{i}" for i in range(10)] + ["a"]
        var[q] = ["a"] + [f"d{i}" for i in range(9)]
    res = evaluate_experiment("T2", "two queries", base, var, qrels, _folds(qids))
    decision, reason = decide(res)
    assert decision == "DROPPED" and ("1 to 2 queries" in reason or "folds" in reason or "not above" in reason)
    assert res.without_top2("ndcg") <= 0.01


def test_dropped_when_too_few_folds_won_and_when_gain_small():
    qids, qrels, base, var = _setup({"q00": 1, "q05": 1, "q10": 1, "q15": 1, "q20": 1})  # all in fold 1
    res = evaluate_experiment("T3", "one fold", base, var, qrels, _folds(qids))
    assert res.folds_won() == 1
    assert decide(res)[0] == "DROPPED"


def test_pending_when_variant_surfaces_unjudged_chunks():
    qids, qrels, base, var = _setup({q: 1 for q in [f"q{i:02d}" for i in range(25)]})
    for q in qids:  # variant top 10 contains two chunks nobody graded
        var[q] = ["a", "new1", "new2"] + var[q][1:]
    res = evaluate_experiment("T4", "unjudged", base, var, qrels, _folds(qids))
    assert res.unjudged10() > 0.05 and decide(res)[0] == "PENDING_GRADING"


def test_markdown_section_is_replaced_not_duplicated(tmp_path):
    qids, qrels, base, var = _setup({q: 1 for q in [f"q{i:02d}" for i in range(25)]})
    res = evaluate_experiment("E7", "demo", base, var, qrels, _folds(qids))
    md = experiment_markdown(res, "demo change", {"w": 1})
    assert "Decision: KEPT" in md and md.count("| 1 |") >= 1
    path = tmp_path / "log.md"
    upsert_section(path, "E7", md)
    upsert_section(path, "E7", md.replace("demo change", "second run"))
    upsert_section(path, "E3", md.replace("E7", "E3").replace("demo change", "other idea"))
    text = path.read_text(encoding="utf-8")
    assert text.count("## E7:") == 1 and "second run" in text and "demo change" not in text
    assert text.index("## E3:") < text.index("## E7:")


def test_unjudged_csv_accumulates_merges_variants_and_drops_graded(tmp_path):
    path = tmp_path / "u.csv"
    rows = [QueryRow("q01", "the query", "device", "direct")]
    qrels = {"q01": {"a": 1}}
    texts = {"x": "text  x", "y": "text y", "a": "text a"}
    n1 = update_unjudged_csv(path, "v1", "E1", rows, {"q01": ["a", "x", "y"]}, qrels, texts)
    n2 = update_unjudged_csv(path, "v2", "E2", rows, {"q01": ["x"]}, qrels, texts)
    assert (n1, n2) == (2, 2)
    got = {r["chunk_id"]: r for r in csv.DictReader(path.open(encoding="utf-8"))}
    assert got["x"]["variants"] == "v1 | v2" and got["x"]["first_seen_in"] == "E1"
    assert got["x"]["text"] == "text x" and "a" not in got
    n3 = update_unjudged_csv(path, "v3", "E3", rows, {"q01": []}, {"q01": {"a": 1, "x": 0}}, texts)
    assert n3 == 1  # x has been graded in the meantime
