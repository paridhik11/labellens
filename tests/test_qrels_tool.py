"""Tests for src.ir.qrels_tool (pooling, TREC qrels export, Cohen's kappa)."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np
import pytest

from src.common.schemas import Chunk
from src.ir.eval import QueryRow
from src.ir.qrels_tool import (
    POOL_COLUMNS,
    build_pool_rows,
    compute_cohens_kappa,
    csv_to_qrels,
    write_pool_csv,
)


class FakeTransformer:
    """Deterministic fake encoder so pooling runs fast without model loads."""

    DIM = 16

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = False,
    ) -> np.ndarray:
        rng = np.random.default_rng(seed=sum(ord(c) for t in texts for c in t) % (2**31))
        vecs = rng.random((len(texts), self.DIM)).astype(np.float32)
        if normalize_embeddings:
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            vecs = vecs / np.where(norms == 0, 1.0, norms)
        return vecs


def _sample_corpus() -> list[Chunk]:
    items = [
        ("dev_1", "801.40", "device", "Unique device identifier format and label rules."),
        ("dev_2", "801.15", "device", "Sterile symbol and prominence requirements."),
        ("dev_3", "801.18", "device", "Expiration date YYYY-MM-DD formatting."),
        ("dev_4", "801.109", "device", "Prescription device caution statement."),
        ("med_1", "201.17", "medicine", "Drug product expiration date location."),
        ("med_2", "201.50", "medicine", "Prescription drug statement of identity."),
        ("med_3", "211.137", "medicine", "Drug stability and expiration dating."),
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


def test_pool_deduplicates_respects_module_and_leaves_grade_empty(
    tmp_path: Path,
) -> None:
    chunks = _sample_corpus()
    queries = [
        QueryRow(qid="q01", query="expiration date label", module="device", qtype="keyword"),
        QueryRow(qid="q02", query="expiration date drug", module="medicine", qtype="keyword"),
    ]
    rows, counts = build_pool_rows(
        chunks,
        queries,
        top_k=3,
        seed=42,
        with_dense=True,
        cache_dir=tmp_path,
        model=FakeTransformer(),
    )
    csv_path = write_pool_csv(rows, tmp_path / "pool.csv")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == POOL_COLUMNS
        loaded = list(reader)

    assert len(loaded) == counts["q01"] + counts["q02"]
    q01_ids = [r["chunk_id"] for r in loaded if r["qid"] == "q01"]
    q02_ids = [r["chunk_id"] for r in loaded if r["qid"] == "q02"]

    # Module isolation: no medicine chunks for q01, no device chunks for q02.
    assert all(cid.startswith("dev_") for cid in q01_ids)
    assert all(cid.startswith("med_") for cid in q02_ids)
    # Deduplicated: unique chunk IDs per query.
    assert len(q01_ids) == len(set(q01_ids))
    assert len(q02_ids) == len(set(q02_ids))
    # Blank grade column ready for manual annotation.
    assert all(r["grade"] == "" for r in loaded)


def test_csv_to_qrels_conversion_and_validation(tmp_path: Path) -> None:
    pool_csv = tmp_path / "annotated.csv"
    with pool_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=POOL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {"qid": "q01", "query": "udi", "chunk_id": "dev_1", "section": "801.40", "text": "t", "grade": "2"}
        )
        writer.writerow(
            {"qid": "q01", "query": "udi", "chunk_id": "dev_2", "section": "801.15", "text": "t", "grade": "0"}
        )
        writer.writerow(
            {"qid": "q01", "query": "udi", "chunk_id": "dev_3", "section": "801.18", "text": "t", "grade": ""}
        )

    qrels_out = tmp_path / "qrels.tsv"
    written, skipped = csv_to_qrels(pool_csv, qrels_out)
    assert written == 2
    assert skipped == 1
    assert qrels_out.read_text(encoding="utf-8") == "q01 0 dev_1 2\nq01 0 dev_2 0\n"

    with pytest.raises(ValueError, match="Missing grade"):
        csv_to_qrels(pool_csv, qrels_out, strict=True)

    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "qid,query,chunk_id,section,text,grade\nq01,udi,dev_1,801.40,t,5\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="out of valid range"):
        csv_to_qrels(bad_csv, qrels_out)


def test_cohens_kappa_perfect_and_partial_agreement(tmp_path: Path) -> None:
    def _write_csv(name: str, rows: list[tuple[str, str, str]]) -> Path:
        p = tmp_path / name
        with p.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=POOL_COLUMNS)
            writer.writeheader()
            for qid, cid, grade in rows:
                writer.writerow(
                    {"qid": qid, "query": "q", "chunk_id": cid, "section": "801.1", "text": "t", "grade": grade}
                )
        return p

    a = _write_csv("a.csv", [("q1", "c1", "2"), ("q1", "c2", "1"), ("q1", "c3", "0"), ("q1", "c4", "0")])
    b_same = _write_csv("b_same.csv", [("q1", "c1", "2"), ("q1", "c2", "1"), ("q1", "c3", "0"), ("q1", "c4", "0")])
    assert compute_cohens_kappa(a, b_same).kappa == pytest.approx(1.0)

    # 4 overlapping rows: A=[2,1,0,0], B=[2,0,0,0] -> non-overlapping c5 ignored, blank c6 ignored.
    # po = 3/4 = 0.75. P_A={0:0.5, 1:0.25, 2:0.25}, P_B={0:0.75, 1:0.0, 2:0.25}
    # pe = 0.5*0.75 + 0.25*0.0 + 0.25*0.25 = 0.375 + 0.0625 = 0.4375
    # kappa = (0.75 - 0.4375) / (1 - 0.4375) = 0.3125 / 0.5625 = 5/9
    b_part = _write_csv(
        "b_part.csv",
        [
            ("q1", "c1", "2"),
            ("q1", "c2", "0"),
            ("q1", "c3", "0"),
            ("q1", "c4", "0"),
            ("q1", "c5", "2"),
            ("q1", "c6", ""),
        ],
    )
    res = compute_cohens_kappa(a, b_part)
    assert res.n_overlap == 4
    assert res.n_agree == 3
    assert res.po == pytest.approx(0.75)
    assert res.pe == pytest.approx(0.4375)
    assert res.kappa == pytest.approx(5 / 9)

    c_disjoint = _write_csv("disjoint.csv", [("q9", "cx", "1")])
    with pytest.raises(ValueError, match="No overlapping graded"):
        compute_cohens_kappa(a, c_disjoint)
