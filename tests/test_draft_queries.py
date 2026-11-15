"""Tests for src.ir.draft_queries (sampling, copy rule, validation, exclusions)."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.draft_queries import (
    TYPE_QUOTA,
    build_candidates,
    copied_words,
    eligible,
    exclusion_lists,
    generic_words,
    sample_worksheet,
)

FILLER = " ".join(f"word{i}" for i in range(45))


def _chunks() -> list[Chunk]:
    out = []
    plan = {"device": {"21cfr801": 14, "21cfr830": 8, "21cfr807": 8, "21cfr803": 6},
            "medicine": {"21cfr201": 14, "21cfr211": 6}}
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
                out.append(Chunk(chunk_id=f"fda_{part}_s{sec}_c{i % 2 + 1}", source="FDA", module=module,
                                 section=sec, text=f"{FILLER} alpha{n} beta{n} gamma{n}{extra}"))
    return out


def test_sample_follows_module_part_and_type_quotas():
    rows = sample_worksheet(_chunks(), n_module={"device": 8, "medicine": 4},
                            quota={"symbol": 2, "change_impact": 2, "vocab_mismatch": 3,
                                   "field_req": 3, "direct": 2})
    assert len(rows) == 12 and len({r["source_chunk"] for r in rows}) == 12
    assert Counter(r["module"] for r in rows) == {"device": 8, "medicine": 4}
    assert Counter(r["type"] for r in rows) == {"symbol": 2, "change_impact": 2, "vocab_mismatch": 3,
                                                "field_req": 3, "direct": 2}
    parts = {r["part"] for r in rows}
    assert {"21cfr801", "21cfr830", "21cfr807", "21cfr803", "21cfr201", "21cfr211"} <= parts
    by_id = {c.chunk_id: c for c in _chunks()}
    for r in rows:  # special types only on chunks that can support them
        assert eligible(by_id[r["source_chunk"]], r["type"])
    assert [r["qid"] for r in rows] == [f"fc{i:02d}" for i in range(1, 13)]


def test_sample_is_deterministic_and_default_quota_adds_up():
    a = sample_worksheet(_chunks(), n_module={"device": 8, "medicine": 4},
                         quota={"symbol": 2, "change_impact": 2, "vocab_mismatch": 3, "field_req": 3, "direct": 2})
    b = sample_worksheet(_chunks(), n_module={"device": 8, "medicine": 4},
                         quota={"symbol": 2, "change_impact": 2, "vocab_mismatch": 3, "field_req": 3, "direct": 2})
    assert a == b and sum(TYPE_QUOTA.values()) == 30


def test_copy_rule_ignores_common_vocabulary_and_counts_rare_words():
    chunks = [Chunk(chunk_id=f"c{i}", source="F", text="label device statement widget") for i in range(20)]
    chunks.append(Chunk(chunk_id="x", source="F", text="label device zirconium sterilant widget"))
    generic = generic_words(chunks)
    assert {"label", "device"} <= generic and "zirconium" not in generic
    assert copied_words("label for zirconium sterilant", "label device zirconium sterilant", generic) == [
        "sterilant", "zirconium"]
    assert copied_words("the device label", "label device zirconium", generic) == []


def test_build_reports_every_problem_and_exports_clean_rows():
    chunks = _chunks()
    ws = sample_worksheet(chunks, n_module={"device": 8, "medicine": 4},
                          quota={"symbol": 2, "change_impact": 2, "vocab_mismatch": 3, "field_req": 3, "direct": 2})
    text_of = {c.chunk_id: c.text for c in chunks}
    web = [{"qid": "fw01", "text": "a web query", "type": "direct", "module": "device",
            "source_url": "https://www.fda.gov/x", "original_question": "Why?", "extraction": "pdftotext_verbatim",
            "target_cfr_part": "801", "target_section": "801.1", "target_evidence": "answer cites 801.1"}]
    queries = {w["qid"]: "plain words only" for w in ws}
    rows, problems = build_candidates(ws, queries, web, chunks, existing={"existing query"})
    assert any("duplicates" in p for p in problems)  # same text used for every chunk query
    queries = {w["qid"]: f"unrelated phrase number {i}" for i, w in enumerate(ws)}
    rare = [w for w in text_of[ws[0]["source_chunk"]].split() if w.startswith(("alpha", "beta", "gamma"))]
    queries[ws[0]["qid"]] = " ".join(rare)  # copies three rare words
    queries[ws[1]["qid"]] = ""
    rows, problems = build_candidates(ws, queries, web, chunks, existing={"existing query"})
    assert any("copies" in p for p in problems) and any("no query written" in p for p in problems)
    queries[ws[0]["qid"]] = "unrelated phrase zero"
    queries[ws[1]["qid"]] = "unrelated phrase one"
    rows, problems = build_candidates(ws, queries, web, chunks, existing={"existing query"})
    assert problems == [] and len(rows) == 13
    assert Counter(r["source_group"] for r in rows) == {"web_faq": 1, "chunk_derived": 12}
    web[0]["source_url"] = ""
    assert any("source URL" in p for p in build_candidates(ws, queries, web, chunks, set())[1])


def test_exclusions_cover_source_chunks_and_whole_sections():
    chunks = _chunks()
    src = [c.chunk_id for c in chunks if c.section == "801.1"][:1]
    ex = exclusion_lists(chunks, src)
    same = {c.chunk_id for c in chunks if c.section == "801.1"}
    assert set(ex["excluded_chunk_ids"]) == same and ex["chunk_derived_source_sections"] == ["801.1"]
    assert "pending" in ex["web_faq_answer_chunks"]


def test_module_does_not_import_any_retrieval_code():
    tree = ast.parse(Path("src/ir/draft_queries.py").read_text(encoding="utf-8"))
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not {m for m in mods if any(k in m for k in ("bm25", "dense", "hybrid", "rerank", "step17", "step18"))}


def test_overlap_stats_counts_common_words_and_jaccard():
    from src.ir.draft_queries import overlap_stats

    ov = overlap_stats("device label name", "the device label shows the name of the firm")
    assert ov["copied_all_words"] == ["device", "label", "name"] and ov["copied_all_count"] == 3
    assert 0 < ov["jaccard"] < 1
    none = overlap_stats("zzz qqq", "device label")
    assert none["copied_all_count"] == 0 and none["jaccard"] == 0.0


def test_build_flags_high_overlap_queries():
    chunks = _chunks()
    ws = sample_worksheet(chunks, n_module={"device": 8, "medicine": 4},
                          quota={"symbol": 2, "change_impact": 2, "vocab_mismatch": 3, "field_req": 3, "direct": 2})
    queries = {w["qid"]: f"unrelated phrase number {i}" for i, w in enumerate(ws)}
    first = next(c for c in chunks if c.chunk_id == ws[0]["source_chunk"])
    queries[ws[0]["qid"]] = " ".join(first.text.split()[:6])  # five filler words plus one more: heavy copying
    _, problems = build_candidates(ws, queries, [], chunks, set())
    assert any("incl. common" in p for p in problems)


def test_target_part_is_checked_against_the_real_corpus_and_moved_when_absent():
    from src.ir.draft_queries import corpus_index, split_no_answer

    chunks = _chunks()
    parts, sections = corpus_index(chunks)
    assert parts == {"801", "830", "807", "803", "201", "211"} and "801.1" in sections
    web = [
        {"qid": "fw01", "text": "in corpus", "type": "direct", "module": "device",
         "source_url": "https://x", "original_question": "?", "extraction": "e",
         "target_cfr_part": "801", "target_section": "801.1", "target_evidence": "e"},
        {"qid": "fw02", "text": "part absent", "type": "direct", "module": "device",
         "source_url": "https://x", "original_question": "?", "extraction": "e",
         "target_cfr_part": "606", "target_section": "606.121", "target_evidence": "e"},
        {"qid": "fw03", "text": "section absent", "type": "direct", "module": "device",
         "source_url": "https://x", "original_question": "?", "extraction": "e",
         "target_cfr_part": "801", "target_section": "801.9999", "target_evidence": "e"},
    ]
    rows, problems = build_candidates([], {}, web, chunks, set())
    assert problems == []
    by = {r["qid"]: r for r in rows}
    assert (by["fw01"]["part_in_corpus"], by["fw01"]["section_in_corpus"]) == ("yes", "yes")
    assert (by["fw02"]["part_in_corpus"], by["fw02"]["section_in_corpus"]) == ("no", "no")
    assert (by["fw03"]["part_in_corpus"], by["fw03"]["section_in_corpus"]) == ("yes", "no")
    keep, moved = split_no_answer(rows)
    assert [r["qid"] for r in moved] == ["fw02"] and [r["qid"] for r in keep] == ["fw01", "fw03"]
