"""Tests for src.ir.step15_ablation (variants, unjudged listing, summary)."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

from src.common.schemas import Chunk, Hit
from src.ir.step15_ablation import (
    CSV_HEADER,
    DEFAULTS,
    build_variants,
    collect_unjudged,
    summary_markdown,
    unjudged_chunks,
    unjudged_sections,
    variant_names,
    write_csv,
)


class _Fake:
    """Deterministic fake encoder that records what it was asked to encode."""

    def __init__(self) -> None:
        self.seen: list[str] = []

    def encode(self, texts, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.seen.extend(texts)
        rng = np.random.default_rng(sum(ord(c) for t in texts for c in t) % (2**31))
        v = rng.random((len(texts), 16)).astype(np.float32)
        return v / np.linalg.norm(v, axis=1, keepdims=True)


def _chunks() -> list[Chunk]:
    words = ["label", "device", "barcode", "sterile", "warning", "storage"]
    return [
        Chunk(
            chunk_id=f"fda_21cfr801_s801.{i}",
            source="FDA",
            section=f"801.{i}",
            text=f"The {w} statement must appear on the {w}ed label number {i}.",
            hash=hashlib.sha256(w.encode()).hexdigest()[:12],
        )
        for i, w in enumerate(words)
    ]


class _Stub:
    """Retriever that returns a fixed ranking whatever the query."""

    def __init__(self, ids: list[str]) -> None:
        self.ids = ids
        self.name = "stub"

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=d, score=1.0 / (i + 1), rank=i + 1) for i, d in enumerate(self.ids[:k])]


def test_variant_names_are_fixed_and_defaults_first() -> None:
    names = variant_names()
    assert names[:3] == list(DEFAULTS)
    assert names[3:6] == ["rrf_k10", "rrf_k30", "rrf_k100"]
    assert "w_bm25_2_dense_1" in names and "w_bm25_1_dense_3" in names
    assert names[-4:] == ["bm25_stem", "hybrid_stem", "dense_prefix", "hybrid_prefix"]
    assert len(names) == len(set(names)) == 14


def test_build_variants_builds_all_and_prefix_only_changes_queries(tmp_path: Path) -> None:
    model = _Fake()
    variants = build_variants(_chunks(), model=model, cache_dir=tmp_path)
    assert list(variants) == variant_names()
    model.seen.clear()
    variants["default_dense"].search("net weight", k=3)
    variants["dense_prefix"].search("net weight", k=3)
    assert model.seen[0] == "net weight"
    assert model.seen[1].endswith("net weight") and model.seen[1] != "net weight"
    # stemming merges 'labeled' and 'label' in the index, the default does not
    stem_hits = variants["bm25_stem"].search("labeled", k=3)
    plain_hits = variants["default_bm25"].search("labeled", k=3)
    assert len(stem_hits) >= len(plain_hits)


def test_unjudged_chunks_filters_judged_and_dedupes() -> None:
    assert unjudged_chunks(["a", "b", "a", "c"], {"b": 0}) == ["a", "c"]
    assert unjudged_chunks([], {"b": 1}) == []
    assert unjudged_sections(["s1", "s2"], {"s1"}) == ["s2"]


def test_collect_unjudged_rows_and_stats_and_csv(tmp_path: Path) -> None:
    chunks = _chunks()
    ids = [c.chunk_id for c in chunks]
    qrels = {"q1": {ids[0]: 2, ids[1]: 0}}
    variants = {"device": {"default_bm25": _Stub(ids[:3]), "bm25_stem": _Stub(ids[1:4])}}
    rows, stats = collect_unjudged(
        variants, {"device": chunks}, {"device": {"q1": "label"}}, qrels, k=3
    )
    assert rows == [
        ("q1", ids[2], "default_bm25"),
        ("q1", ids[2], "bm25_stem"),
        ("q1", ids[3], "bm25_stem"),
    ]
    assert stats["default_bm25"] == {"chunk_rows": 1, "slots": 3, "section_rows": 1}
    assert stats["bm25_stem"]["chunk_rows"] == 2
    path = tmp_path / "u.csv"
    write_csv(rows, path)
    with path.open(encoding="utf-8", newline="") as f:
        read = list(csv.reader(f))
    assert tuple(read[0]) == CSV_HEADER and len(read) == 4
    text = summary_markdown(rows, stats)
    assert "Unique (qid, chunk) pairs over all variants: 2" in text
    assert "| bm25_stem | 2 |" in text
