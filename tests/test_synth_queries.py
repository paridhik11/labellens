"""Tests for src.ir.synth_queries (sampling away from the exclusion list, validation)."""
from __future__ import annotations

from collections import Counter

from src.common.schemas import Chunk
from src.ir.synth_queries import eligible_pool, make_worksheet, validate

FILLER = " ".join(f"word{i}" for i in range(45))


def _chunks() -> list[Chunk]:
    out = []
    plan = {"device": {"21cfr801": 20, "21cfr830": 12}, "medicine": {"21cfr201": 18, "21cfr211": 8}}
    n = 0
    for module, parts in plan.items():
        for part, count in parts.items():
            for i in range(count):
                n += 1
                extra = ""
                if i % 3 == 0:
                    extra += " the symbol shall appear"
                if i % 4 == 0:
                    extra += " any change or amendment requires an update"
                sec = f"{part[-3:]}.{i // 2 + 1}"
                out.append(Chunk(chunk_id=f"fda_{part}_s{sec}_c{i % 2 + 1}", source="F", module=module,
                                 section=sec, text=f"{FILLER} alpha{n} beta{n} gamma{n}{extra}", hash=f"h{n}"))
    return out


QUOTA = {"direct": 6, "field_req": 5, "vocab_mismatch": 4, "change_impact": 3, "symbol": 2}


def test_sample_never_uses_excluded_chunks_and_follows_the_strata():
    chunks = _chunks()
    excluded = {c.chunk_id for c in chunks if c.section in {"801.1", "201.1"}}
    ws = make_worksheet(chunks, excluded, n_module={"device": 12, "medicine": 8}, quota=QUOTA)
    assert len(ws) == 20 and not {r["source_chunk"] for r in ws} & excluded
    assert Counter(r["module"] for r in ws) == {"device": 12, "medicine": 8}
    assert Counter(r["type"] for r in ws) == QUOTA
    assert [r["qid"] for r in ws][:2] == ["sq001", "sq002"]
    assert len(eligible_pool(chunks, excluded)) == len(chunks) - len(excluded)


def test_validate_flags_excluded_sources_duplicates_forbidden_text_and_copying():
    chunks = _chunks()
    ws = make_worksheet(chunks, set(), n_module={"device": 12, "medicine": 8}, quota=QUOTA)
    queries = {w["qid"]: f"unrelated phrase number {i}" for i, w in enumerate(ws)}
    rows, problems = validate(ws, queries, chunks, set(), set())
    assert problems == [] and len(rows) == 20 and rows[0]["source_chunk"] == ws[0]["source_chunk"]
    # an excluded source chunk, a forbidden text, a duplicate and heavy copying are all reported
    queries[ws[0]["qid"]] = "unrelated phrase number 1"  # duplicates sq002
    queries[ws[2]["qid"]] = "A Forbidden Query"
    src = next(c for c in chunks if c.chunk_id == ws[3]["source_chunk"])
    queries[ws[3]["qid"]] = " ".join(w for w in src.text.split() if w.startswith(("alpha", "beta", "gamma")))
    _, problems = validate(ws, queries, chunks, {ws[4]["source_chunk"]}, {"a forbidden query"})
    text = "\n".join(problems)
    assert "duplicates" in text and "evaluation or fresh query" in text and "copies rare" in text
    assert "exclusion list" in text
