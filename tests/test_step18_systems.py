"""Tests for src.ir.step18_systems (BM25-only systems, so no model is loaded)."""
from __future__ import annotations

from src.common.schemas import Chunk
from src.ir.step18_systems import PLAIN_HYBRID, STEM_PREFIX_HYBRID, Context18, Sys18, enrich_chunk, experiments

CHUNKS = [
    Chunk(chunk_id="fda_21cfr801_s801.15_c1", source="F", section="801.15",
          title="Prominence of required label statements",
          text="the word shall appear on the label", hash="h1", module="device"),
    Chunk(chunk_id="fda_21cfr830_s830.60_c1", source="F", section="830.60", title="Relabeling and repackaging",
          text="you must assign a new identifier", hash="h2", module="device"),
    Chunk(chunk_id="fda_21cfr807_s807.25_c1", source="F", section="807.25", title="Listing information",
          text="the owner submits the form", hash="h3", module="device"),
]


def test_enrich_prepends_part_section_and_heading_with_a_new_hash_and_same_id():
    e = enrich_chunk(CHUNKS[0])
    assert e.text.startswith("21 CFR Part 801, section 801.15: Prominence of required label statements. ")
    assert e.text.endswith("the word shall appear on the label")
    assert e.chunk_id == CHUNKS[0].chunk_id and e.hash != CHUNKS[0].hash
    assert CHUNKS[0].text == "the word shall appear on the label"  # the original chunk is untouched


def test_heading_words_become_searchable_only_when_enriched():
    ctx = Context18(CHUNKS)
    plain = ctx.build(Sys18(bm25=(False, False), dense=()))
    head = ctx.build(Sys18(bm25=(False, True), dense=()))
    assert plain.search("repackaging", k=3) == []  # the word is only in the heading
    assert [h.doc_id for h in head.search("repackaging", k=3)] == ["fda_21cfr830_s830.60_c1"]
    assert [h.doc_id for h in head.search("part 807", k=3)][0] == "fda_21cfr807_s807.25_c1"
    assert ctx.build(Sys18(bm25=(False, True), dense=())) is head  # built once


def test_system_names_and_the_experiment_list():
    assert PLAIN_HYBRID.name == "rrf[bm25, small]"
    assert STEM_PREFIX_HYBRID.name == "rrf[bm25+stem, small+prefix]"
    assert Sys18(bm25=(True, True), dense=(("large", True, True),), medcpt=True).name == (
        "rrf[bm25+stem+head, large+prefix+head, medcpt]")
    exps = experiments()
    ids = [e[0] for e in exps]
    assert len(ids) == len(set(ids)) == 15
    assert len({e[3] for e in exps}) == 15  # no two experiments build the same system
    assert PLAIN_HYBRID not in {e[3] for e in exps} and STEM_PREFIX_HYBRID not in {e[3] for e in exps}
