"""Tests for src.ir.section_lookup."""
from __future__ import annotations

import pytest

from src.common.schemas import Chunk
from src.ir.section_lookup import SectionLookup, parse_citations


def _chunk(cid: str, section: str, module: str = "device") -> Chunk:
    return Chunk(chunk_id=cid, source="FDA", text=f"text of {cid}", section=section, module=module)


CHUNKS = [
    _chunk("fda_21cfr801_s801.109_c2", "801.109"),
    _chunk("fda_21cfr801_s801.109_c1", "801.109"),
    _chunk("fda_21cfr801_s801.15", "801.15"),
    _chunk("fda_21cfr830_s830.60", "830.60"),
]
MED = [_chunk("fda_21cfr201_s201.5", "201.5", "medicine")]


@pytest.mark.parametrize("query,section,para,cued", [
    ("801.109", "801.109", "", False),
    ("what does 801.109 require", "801.109", "", False),
    ("21 CFR 801.109", "801.109", "", True),
    ("21 C.F.R. 801.109", "801.109", "", True),
    ("21 CFR § 801.109(b)(2)", "801.109", "(b)(2)", True),
    ("§801.109", "801.109", "", True),
    ("see section 801.109 for details", "801.109", "", True),
    ("Sec. 830.60 relabeling", "830.60", "", True),
    ("21 CFR part 801.15", "801.15", "", True),
])
def test_citation_patterns_are_found(query, section, para, cued):
    got = parse_citations(query)
    assert [(c.section, c.paragraph, c.cued) for c in got] == [(section, para, cued)]


@pytest.mark.parametrize("query", [
    "510(k) clearance for a device", "ISO 13485 labeling", "dose of 201.5 mg", "version 3.1.2",
    "page 12.4 of the manual", "section 999.1 does not exist as a part", "Rx only legend wording",
    "price 801.10.5 total",
])
def test_non_citations_are_ignored(query):
    assert parse_citations(query) == []


def test_unit_guard_does_not_apply_when_a_cue_is_present():
    assert [c.section for c in parse_citations("21 CFR 201.5 mg")] == ["201.5"]


def test_lookup_returns_chunks_of_cited_sections_in_order():
    lk = SectionLookup(CHUNKS)
    hits = lk.search("compare 830.60 and 21 CFR 801.109(a)")
    assert [h.doc_id for h in hits] == ["fda_21cfr830_s830.60", "fda_21cfr801_s801.109_c1",
                                        "fda_21cfr801_s801.109_c2"]
    assert [h.rank for h in hits] == [1, 2, 3] and all(h.score == 1.0 for h in hits)
    assert lk.search("801.109", k=1)[0].doc_id == "fda_21cfr801_s801.109_c1"


def test_unknown_sections_and_plain_queries_give_nothing():
    lk = SectionLookup(CHUNKS)
    assert lk.search("801.999") == [] and lk.search("device labeling rules") == []
    assert lk.citations("801.15 and 801.15 again")[0].section == "801.15"
    assert len(lk.citations("801.15 and 801.15 again")) == 1


def test_modules_stay_separate():
    device, medicine = SectionLookup(CHUNKS), SectionLookup(MED)
    assert medicine.search("21 CFR 201.5")[0].doc_id == "fda_21cfr201_s201.5"
    assert device.search("21 CFR 201.5") == []  # a device lookup never returns medicine chunks
    assert "201.5" not in device.sections()
