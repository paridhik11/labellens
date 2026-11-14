"""Tests for src.ir.llm_grade_tool (batching, recording, qrels, human sample)."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

from src.ir import llm_grade_tool as tool
from src.ir.eval import QueryRow
from src.ir.llm_grade_tool import (
    PoolRow,
    allocate,
    append_llm_rows,
    build_next_batch,
    check_batch_grades,
    llm_csv_to_qrels,
    load_llm_rows,
    load_pool_rows,
    next_batch_number,
    parse_grades,
    query_order,
    select_sample,
    split_between_annotators,
    write_sample,
)

POOL_FIELDS = ["qid", "query", "chunk_id", "section", "text", "grade"]


def _pool(sizes: dict[str, int]) -> list[PoolRow]:
    return [
        PoolRow(qid, f"query {qid}", f"c{i}", f"text {qid} {i}")
        for qid, n in sizes.items()
        for i in range(n)
    ]


def _write_pool_csv(path: Path, rows: list[PoolRow], grade: str = "") -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=POOL_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({"qid": r.qid, "query": r.query, "chunk_id": r.chunk_id,
                        "section": "801.1", "text": r.text, "grade": grade})


def test_load_pool_rows_ignores_grade_and_section(tmp_path: Path) -> None:
    p = tmp_path / "pool.csv"
    _write_pool_csv(p, _pool({"q1": 2}), grade="2")
    rows = load_pool_rows(p)
    assert rows[0] == PoolRow("q1", "query q1", "c0", "text q1 0")
    assert not hasattr(rows[0], "grade") and not hasattr(rows[0], "section")
    assert rows[0].row_id == "q1:c0"


def test_query_order_puts_sample_first() -> None:
    pool = _pool({"q1": 1, "q2": 1, "q3": 1})
    assert query_order(pool, ["q3"]) == ["q3", "q1", "q2"]


def test_build_next_batch_keeps_queries_whole_and_respects_max_rows() -> None:
    pool = _pool({"q1": 20, "q2": 15, "q3": 18})
    batch = build_next_batch(pool, set(), [], batch_no=1, max_rows=40)
    assert {r.qid for r in batch} == {"q1", "q2"}  # adding q3 would pass 40
    assert len(batch) == 35

    graded = {r.row_id for r in batch}
    batch2 = build_next_batch(pool, graded, [], batch_no=2, max_rows=40)
    assert {r.qid for r in batch2} == {"q3"}
    graded |= {r.row_id for r in batch2}
    assert build_next_batch(pool, graded, [], batch_no=3) == []


def test_build_next_batch_takes_one_oversized_query() -> None:
    pool = _pool({"q1": 50})
    assert len(build_next_batch(pool, set(), [], batch_no=1, max_rows=40)) == 50


def test_build_next_batch_shuffle_is_seeded() -> None:
    pool = _pool({"q1": 30})
    a = build_next_batch(pool, set(), [], batch_no=1)
    b = build_next_batch(pool, set(), [], batch_no=1)
    assert a == b
    assert [r.chunk_id for r in a] != [r.chunk_id for r in pool]  # order is shuffled


def test_parse_grades_validates_lines() -> None:
    assert parse_grades("q1:c0\t2\n\nq1:c1\t0\n") == {"q1:c0": 2, "q1:c1": 0}
    with pytest.raises(ValueError, match="0, 1 or 2"):
        parse_grades("q1:c0\t3\n")
    with pytest.raises(ValueError, match="twice"):
        parse_grades("q1:c0\t1\nq1:c0\t2\n")
    with pytest.raises(ValueError, match="expected"):
        parse_grades("q1:c0 2\n")


def test_check_batch_grades_requires_exact_rows() -> None:
    batch = _pool({"q1": 2})
    check_batch_grades(batch, {"q1:c0": 1, "q1:c1": 0})
    with pytest.raises(ValueError, match="missing"):
        check_batch_grades(batch, {"q1:c0": 1})
    with pytest.raises(ValueError, match="not in batch"):
        check_batch_grades(batch, {"q1:c0": 1, "q1:c1": 0, "q9:c0": 2})


def test_append_and_to_qrels_round_trip(tmp_path: Path) -> None:
    llm = tmp_path / "pool_t1_llm.csv"
    batch = _pool({"q1": 2})
    with pytest.raises(ValueError, match="model id"):
        append_llm_rows(llm, batch, {"q1:c0": 2, "q1:c1": 0}, 1, " ", "2026-11-12")
    append_llm_rows(llm, batch, {"q1:c0": 2, "q1:c1": 0}, 1, "test-model", "2026-11-12")
    rows = load_llm_rows(llm)
    assert rows[0] == {"qid": "q1", "chunk_id": "c0", "llm_grade": "2", "batch": "1",
                       "model": "test-model", "date": "2026-11-12"}
    assert next_batch_number(rows) == 2
    out = tmp_path / "qrels.tsv"
    assert llm_csv_to_qrels(llm, out) == 2
    assert out.read_text(encoding="utf-8") == "q1 0 c0 2\nq1 0 c1 0\n"


def test_allocate_largest_remainder_with_minimum() -> None:
    counts = {"direct": 17, "field_req": 16, "vocab_mismatch": 13,
              "change_impact": 6, "symbol": 5, "no_answer": 5}
    alloc = allocate(counts, 15, min_each=1)
    assert sum(alloc.values()) == 15
    assert all(v >= 1 for v in alloc.values())
    # Quotas 4.11, 3.87, 3.15, 1.45, 1.21, 1.21 -> whole parts sum to 13;
    # the 2 extra slots go to field_req (.87) and change_impact (.45).
    assert alloc == {"direct": 4, "field_req": 4, "vocab_mismatch": 3,
                     "change_impact": 2, "symbol": 1, "no_answer": 1}
    # The minimum lifts a tiny group above its quota of 0.
    assert allocate({"big": 20, "tiny": 1}, 3, min_each=1) == {"big": 2, "tiny": 1}


def test_select_sample_is_stratified_and_deterministic() -> None:
    rows = [QueryRow(f"q{i:02d}", "x", "device" if i % 3 else "medicine", t)
            for i, t in enumerate(["direct"] * 9 + ["no_answer"] * 3 + ["symbol"] * 3)]
    a = select_sample(rows, n=6, seed=42)
    assert a == select_sample(rows, n=6, seed=42)
    assert len(a) == 6 and len(set(a)) == 6
    types = {r.qid: r.qtype for r in rows}
    assert {types[q] for q in a} == {"direct", "no_answer", "symbol"}


def test_write_sample_blanks_grades_and_refuses_overwrite(tmp_path: Path) -> None:
    pool = tmp_path / "pool.csv"
    _write_pool_csv(pool, _pool({"q1": 2, "q2": 3}), grade="2")
    out = tmp_path / "sample.csv"
    assert write_sample(pool, ["q2"], out) == 3
    with out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert {r["qid"] for r in rows} == {"q2"}
    assert all(r["grade"] == "" for r in rows)
    assert list(rows[0].keys()) == POOL_FIELDS
    with pytest.raises(FileExistsError):
        write_sample(pool, ["q2"], out)


def test_split_between_annotators_overlap_and_balance() -> None:
    rows = [
        QueryRow("q01", "x", "device", "direct"),
        QueryRow("q02", "x", "device", "direct"),
        QueryRow("q03", "x", "device", "direct"),
        QueryRow("q04", "x", "device", "field_req"),
        QueryRow("q05", "x", "device", "field_req"),
        QueryRow("q06", "x", "device", "no_answer"),
        QueryRow("q07", "x", "medicine", "direct"),
        QueryRow("q08", "x", "medicine", "field_req"),
    ]
    counts = {r.qid: 10 for r in rows}
    overlap, assigned = split_between_annotators(rows, counts, ("a", "b"), seed=42)
    mods = {r.qid: r.module for r in rows}
    assert "q06" in overlap and len(overlap) == 3
    assert sorted(mods[q] for q in overlap if q != "q06") == ["device", "medicine"]
    # Every query is graded by someone; only the overlap is graded by both.
    assert set(assigned["a"]) | set(assigned["b"]) == {r.qid for r in rows}
    assert set(assigned["a"]) & set(assigned["b"]) == set(overlap)
    assert abs(len(assigned["a"]) - len(assigned["b"])) <= 1
    assert (overlap, assigned) == split_between_annotators(rows, counts, ("a", "b"), seed=42)


def test_cli_split_refuses_to_overwrite(tmp_path: Path, monkeypatch) -> None:
    pool = tmp_path / "pool.csv"
    _write_pool_csv(pool, _pool({"q1": 2, "q2": 2, "q3": 2}))
    sample = tmp_path / "sample.csv"
    write_sample(pool, ["q1", "q2", "q3"], sample)
    queries = tmp_path / "q.tsv"
    queries.write_text("q1\tx\tdevice\tdirect\nq2\tx\tmedicine\tdirect\nq3\tx\tdevice\tno_answer\n",
                       encoding="utf-8")
    args = ["t", "split", "--queries", str(queries), "--sample", str(sample),
            "--out-dir", str(tmp_path)]
    monkeypatch.setattr(sys, "argv", args)
    tool.main()
    assert (tmp_path / "sample_pari.csv").exists() and (tmp_path / "sample_parth.csv").exists()
    (tmp_path / "sample_pari.csv").write_text("graded by hand", encoding="utf-8")
    with pytest.raises(SystemExit, match="Refusing to overwrite"):
        tool.main()
    assert (tmp_path / "sample_pari.csv").read_text(encoding="utf-8") == "graded by hand"


def test_cli_next_batch_and_record(tmp_path: Path, monkeypatch, capsys) -> None:
    pool = tmp_path / "pool.csv"
    _write_pool_csv(pool, _pool({"q1": 3, "q2": 2}))
    sample = tmp_path / "sample.csv"
    write_sample(pool, ["q2"], sample)
    llm = tmp_path / "llm.csv"
    batch_txt = tmp_path / "batch.md"
    common = ["--pool", str(pool), "--llm", str(llm), "--sample", str(sample), "--max-rows", "2"]

    monkeypatch.setattr(sys, "argv", ["t", "next-batch", *common, "--out", str(batch_txt)])
    tool.main()
    text = batch_txt.read_text(encoding="utf-8")
    assert "row_id: q2:c0" in text and "q1:" not in text  # sample query q2 comes first
    assert "801.1" not in text  # section is never shown

    grades = tmp_path / "grades.tsv"
    grades.write_text("q2:c0\t1\nq2:c1\t0\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["t", "record", *common, "--grades", str(grades),
                                      "--model", "test-model"])
    tool.main()
    out = capsys.readouterr().out
    assert "Recorded batch 1: 2 rows" in out
    assert "human-sample queries fully LLM-graded: 1/1" in out
    assert [r["batch"] for r in load_llm_rows(llm)] == ["1", "1"]
    # The human sample file was not touched.
    with sample.open(encoding="utf-8", newline="") as f:
        assert all(r["grade"] == "" for r in csv.DictReader(f))


# ---------- extra pool (Step 15) ----------

def _extra_inputs(tmp_path: Path) -> dict[str, Path]:
    """Tiny unjudged listing, queries, corpus and qrels for build_extra_pool."""
    unj = tmp_path / "unjudged.csv"
    unj.write_text(
        "qid,chunk_id,variant\n"
        "q10,c_b,rrf_k30\nq2,c_a,rrf_k30\nq2,c_a,bm25_stem\nq2,c_b,bm25_stem\n",
        encoding="utf-8",
    )
    qs = tmp_path / "queries.tsv"
    qs.write_text("q2\tquery two\tdevice\tdirect\nq10\tquery ten\tdevice\tdirect\n", encoding="utf-8")
    corpus = tmp_path / "regs.jsonl"
    corpus.write_text(
        '{"chunk_id": "c_a", "text": "text a"}\n{"chunk_id": "c_b", "text": "text b"}\n',
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text("q2 0 c_z 1\n", encoding="utf-8")
    return {"unj": unj, "qs": qs, "corpus": corpus, "qrels": qrels}


def test_build_extra_pool_dedupes_sorts_and_keeps_four_columns(tmp_path: Path) -> None:
    f = _extra_inputs(tmp_path)
    out = tmp_path / "extra.csv"
    n = tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], out)
    assert n == 3  # (q2,c_a) appears under two variants but is one pair
    with out.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0]) == ["qid", "query", "chunk_id", "text"]  # no variant column
    assert [(r["qid"], r["chunk_id"]) for r in rows] == [("q2", "c_a"), ("q2", "c_b"), ("q10", "c_b")]
    assert rows[0]["query"] == "query two" and rows[0]["text"] == "text a"
    # the existing loader can read it (it ignores any extra columns anyway)
    assert load_pool_rows(out)[0] == PoolRow("q2", "query two", "c_a", "text a")
    with pytest.raises(FileExistsError):
        tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], out)
    assert tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], out, force=True) == 3


def test_build_extra_pool_refuses_protected_paths_and_bad_inputs(tmp_path: Path) -> None:
    f = _extra_inputs(tmp_path)
    for protected in (tool.POOL_PATH, tool.LLM_PATH, tool.SAMPLE_PATH, tool.QRELS_LLM_PATH):
        with pytest.raises(ValueError, match="protected"):
            tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], protected, force=True)
    # a pair that already has an LLM grade must not be graded again
    f["qrels"].write_text("q2 0 c_a 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="already graded"):
        tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], tmp_path / "e.csv")
    f["qrels"].write_text("", encoding="utf-8")
    f["corpus"].write_text('{"chunk_id": "c_a", "text": "text a"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="unknown chunks"):
        tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], tmp_path / "e.csv")
    assert not (tmp_path / "e.csv").exists()


def test_build_extra_pool_skip_graded_leaves_out_graded_pairs(tmp_path: Path) -> None:
    f = _extra_inputs(tmp_path)
    f["qrels"].write_text("q2 0 c_a 1\n", encoding="utf-8")  # (q2, c_a) already graded
    out = tmp_path / "extra2.csv"
    n = tool.build_extra_pool(f["unj"], f["qs"], f["corpus"], f["qrels"], out, skip_graded=True)
    assert n == 2
    with out.open(encoding="utf-8", newline="") as fh:
        got = [(r["qid"], r["chunk_id"]) for r in csv.DictReader(fh)]
    assert got == [("q2", "c_b"), ("q10", "c_b")]


def test_extra_flow_continues_batch_numbers_and_never_touches_main_pool(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    main_pool = tmp_path / "pool_t1.csv"
    _write_pool_csv(main_pool, _pool({"q1": 2}), grade="2")
    before = main_pool.read_bytes()
    extra = tmp_path / "pool_t1_extra.csv"
    extra.write_text(
        "qid,query,chunk_id,text\nq2,query two,c_a,text a\nq2,query two,c_b,text b\n"
        "q10,query ten,c_b,text b\n",
        encoding="utf-8",
    )
    llm = tmp_path / "pool_t1_llm.csv"
    llm.write_text(
        "qid,chunk_id,llm_grade,batch,model,date\nq1,c0,0,43,claude-sonnet-5-5,2026-11-12\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(tool, "POOL_PATH", main_pool)
    monkeypatch.setattr(tool, "EXTRA_PATH", extra)

    def run(*argv: str) -> None:
        monkeypatch.setattr(sys, "argv", ["llm_grade_tool", *argv])
        tool.main()

    batch_file = tmp_path / "batch.txt"
    run("next-batch", "--extra", "--max-rows", "2", "--llm", str(llm), "--out", str(batch_file))
    text = batch_file.read_text(encoding="utf-8")
    assert "# Batch 44 (2 rows)" in text  # continues after batch 43, whole query q2 first
    assert "q2:c_a" in text and "q10:c_b" not in text
    assert "extra pool: graded 0/3 rows" in capsys.readouterr().out

    grades = tmp_path / "grades.tsv"
    grades.write_text("q2:c_a\t1\nq2:c_b\t0\n", encoding="utf-8")
    run("record", "--extra", "--max-rows", "2", "--llm", str(llm), "--grades", str(grades),
        "--model", "claude-sonnet-5-5", "--date", "2026-11-13")
    rows = load_llm_rows(llm)
    assert [(r["qid"], r["chunk_id"], r["batch"], r["model"]) for r in rows[1:]] == [
        ("q2", "c_a", "44", "claude-sonnet-5-5"),
        ("q2", "c_b", "44", "claude-sonnet-5-5"),
    ]
    assert main_pool.read_bytes() == before  # the main pool is never written
    assert "extra pool: graded 2/3 rows; queries still open: 1" in capsys.readouterr().out
    run("next-batch", "--extra", "--max-rows", "2", "--llm", str(llm), "--out", str(batch_file))
    assert "# Batch 45 (1 rows)" in batch_file.read_text(encoding="utf-8")
