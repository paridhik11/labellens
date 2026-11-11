"""Tests for src.ir.eval (cache reuse, --module, --no-dense, section-level metrics)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

from src.common.schemas import Chunk, Hit
from src.ir import eval as eval_mod
from src.ir.eval import (
    QueryRow,
    aggregate_hits_by_section,
    aggregate_qrels_by_section,
    build_systems,
    evaluate,
    evaluate_no_answer,
    find_corpus_gaps,
    load_query_rows,
    mean_top1_score,
    no_answer_to_markdown,
    split_no_answer,
)


class FixedRetriever:
    """Always returns c1, c2, c3 with fixed scores, whatever the query."""

    name = "fixed"

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [
            Hit(doc_id="c1", score=0.9, rank=1, text="t1"),
            Hit(doc_id="c2", score=0.8, rank=2, text="t2"),
            Hit(doc_id="c3", score=0.5, rank=3, text="t3"),
        ][:k]


class CountingFakeTransformer:
    """Deterministic fake encoder that counts encode() calls to verify cache hits."""

    DIM = 16

    def __init__(self) -> None:
        self.encode_calls = 0

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = False,
    ) -> np.ndarray:
        self.encode_calls += 1
        rng = np.random.default_rng(seed=sum(ord(c) for t in texts for c in t) % (2**31))
        vecs = rng.random((len(texts), self.DIM)).astype(np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs = vecs / np.where(norms == 0, 1.0, norms)
        return vecs


def _make_chunks() -> list[Chunk]:
    items = [
        ("dev_801_c1", "801.40", "device", "General § 801.40 UDI technical form on label."),
        ("dev_801_c2", "801.40", "device", "Unique device identifier barcode presentation."),
        ("dev_830_c1", "830.50", "device", "Changes requiring a new device identifier."),
        ("med_201_c1", "201.17", "medicine", "Drug expiration date on label."),
    ]
    return [
        Chunk(
            chunk_id=cid,
            source="FDA",
            section=sec,
            module=mod,  # type: ignore[arg-type]
            text=txt,
            hash=hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16],
        )
        for cid, sec, mod, txt in items
    ]


def test_build_systems_reuses_cache_via_chunk_hashes(tmp_path: Path) -> None:
    chunks = _make_chunks()
    docs = [(c.chunk_id, c.text) for c in chunks]

    enc1 = CountingFakeTransformer()
    systems1 = build_systems(
        docs, with_dense=True, chunks=chunks, cache_dir=tmp_path, model=enc1
    )
    assert [s.name for s in systems1] == ["tfidf", "bm25", "dense", "hybrid"]
    assert enc1.encode_calls == 1

    # Second call with identical chunks (including hashes) must hit the disk cache.
    enc2 = CountingFakeTransformer()
    build_systems(docs, with_dense=True, chunks=chunks, cache_dir=tmp_path, model=enc2)
    assert enc2.encode_calls == 0


def test_section_level_max_score_aggregation() -> None:
    chunk_to_section = {
        "c_801_1": "801.40",
        "c_801_2": "801.40",
        "c_830_1": "830.50",
    }
    # Section 801.40 has scores 0.2 and 0.9 (mean 0.55 < 0.70, max 0.90 > 0.70).
    # Max aggregation must rank 801.40 above 830.50 (0.70).
    hits = [
        Hit(doc_id="c_801_2", score=0.90, rank=1, text="a"),
        Hit(doc_id="c_830_1", score=0.70, rank=2, text="b"),
        Hit(doc_id="c_801_1", score=0.20, rank=3, text="c"),
    ]
    ranked_sections = aggregate_hits_by_section(hits, chunk_to_section)
    assert ranked_sections == ["801.40", "830.50"]

    qrels = {"q1": {"c_801_1": 1, "c_801_2": 2, "c_830_1": 0}}
    sec_qrels = aggregate_qrels_by_section(qrels, chunk_to_section)
    assert sec_qrels == {"q1": {"801.40": 2, "830.50": 0}}


def test_split_no_answer_keeps_untyped_as_answerable() -> None:
    rows = [
        QueryRow("q1", "a", "device", "direct"),
        QueryRow("q2", "b", "device", "no_answer"),
        QueryRow("q3", "c"),  # 2-column file: no type
    ]
    answerable, no_answer = split_no_answer(rows)
    assert [r.qid for r in answerable] == ["q1", "q3"]
    assert [r.qid for r in no_answer] == ["q2"]


def test_find_corpus_gaps_ignores_ungraded_and_answered() -> None:
    qrels = {"q1": {"c1": 0, "c2": 0}, "q2": {"c1": 1}, "q3": {"c1": 2}}
    # q1 all zeros -> gap; q2 and q3 answered; q4 ungraded -> not a gap.
    assert find_corpus_gaps(["q1", "q2", "q3", "q4"], qrels) == ["q1"]


def test_evaluate_no_answer_separates_grade1_and_grade2() -> None:
    queries = {"n1": "x", "n2": "y", "n3": "z", "n4": "ungraded"}
    qrels = {
        "n1": {"c1": 0, "c2": 0},  # nothing relevant in top k
        "n2": {"c2": 1},  # related context only, not an error
        "n3": {"c3": 2},  # a passage states the rule
    }
    res = evaluate_no_answer([FixedRetriever()], queries, qrels, k=10)["fixed"]
    assert res["n"] == 3.0  # n4 has no grades, so it is skipped
    assert abs(res["any_rel_topk"] - 2 / 3) < 1e-9
    assert abs(res["grade2_topk"] - 1 / 3) < 1e-9
    assert abs(res["top1_score"] - 0.9) < 1e-9

    md = no_answer_to_markdown({"fixed": res}, {"fixed": 0.9})
    assert "| fixed | 0.667 | 0.333 | 0.900 | 0.900 |" in md


def test_mean_top1_score_handles_empty_queries() -> None:
    assert mean_top1_score([FixedRetriever()], {}) == {"fixed": 0.0}


def test_evaluate_with_no_graded_queries_does_not_crash() -> None:
    res, _ = evaluate([FixedRetriever()], {"q1": "x"}, {})
    assert res["fixed"] == {"ndcg": 0.0, "recall": 0.0, "mrr": 0.0, "map": 0.0}


def test_evaluate_returns_both_chunk_and_section_metrics() -> None:
    chunk_to_section = {"c1": "801.40", "c2": "801.40", "c3": "830.50"}
    queries = {"q1": "udi"}
    # Only c2 (rank 2) is judged relevant at chunk level, but c1 & c2 share 801.40.
    qrels = {"q1": {"c2": 2}}

    chunk_res, _ = evaluate([FixedRetriever()], queries, qrels)
    sec_res, _ = evaluate(
        [FixedRetriever()], queries, qrels, chunk_to_section=chunk_to_section
    )
    assert chunk_res["fixed"]["mrr"] == 0.5  # c2 is at chunk rank 2
    assert sec_res["fixed"]["mrr"] == 1.0  # section 801.40 is at section rank 1


def test_eval_cli_module_no_dense_and_section_level(
    tmp_path: Path, monkeypatch
) -> None:
    chunks = _make_chunks()
    corpus_path = tmp_path / "regs.jsonl"
    corpus_path.write_text(
        "\n".join(c.model_dump_json() for c in chunks) + "\n", encoding="utf-8"
    )

    queries_path = tmp_path / "queries_t1.tsv"
    queries_path.write_text(
        "qid\tquery\tmodule\ttype\n"
        "q01\tunique device identifier\tdevice\tkeyword\n"
        "q02\texpiration date\tmedicine\tkeyword\n"
        "q03\tdevice tax refund form\tdevice\tno_answer\n"
        "q04\tidentifier changes\tdevice\tdirect\n",
        encoding="utf-8",
    )
    assert len(load_query_rows(queries_path)) == 4

    qrels_path = tmp_path / "qrels_t1.tsv"
    # q03 (no_answer) and q04 (answerable, all zeros = corpus gap) would both
    # score 0 and drag the bm25 average down if they were not excluded.
    qrels_path.write_text(
        "q01 0 dev_801_c2 2\nq02 0 med_201_c1 2\n"
        "q03 0 dev_801_c1 0\nq04 0 dev_830_c1 0\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "eval.md"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eval.py",
            "--corpus",
            str(corpus_path),
            "--queries",
            str(queries_path),
            "--qrels",
            str(qrels_path),
            "--out",
            str(out_path),
            "--module",
            "device",
            "--no-dense",
            "--section-level",
        ],
    )
    eval_mod.main()

    md = out_path.read_text(encoding="utf-8")
    assert "### Chunk-level" in md
    assert "### Section-level" in md
    assert "| tfidf |" in md
    assert "| bm25 |" in md
    assert "| dense |" not in md
    assert "| hybrid |" not in md
    # Medicine query q02 was filtered out, and q01 matched dev_801_c2.
    assert "| bm25 | 1.000 | 1.000 | 1.000 | 1.000 |" in md
    assert "### Chunk-level (queries evaluated: 1)" in md
    assert "### Section-level (queries evaluated: 1)" in md
    assert "### no_answer queries (queries evaluated: 1," in md
    assert "### Corpus gaps (count: 1," in md
    assert md.rstrip().endswith("q04")

