"""Tests for src.ir.expand."""
from __future__ import annotations

import json
from pathlib import Path

from src.common.schemas import Hit
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.expand import (
    AppendExpansionRetriever,
    ExpandedBM25Retriever,
    SynonymExpander,
    check_lexicon,
    contains_phrase,
    words,
)

GROUPS = [
    {"id": "otc", "source": "failure_derived", "terms": ["over the counter", "over-the-counter", "otc"]},
    {"id": "maker", "source": "failure_derived", "terms": ["manufacturer", "maker"]},
    {"id": "udi", "source": "cfr_definition", "evidence": ["830.3"],
     "terms": ["unique device identifier", "udi"]},
]


def test_words_splits_hyphens_and_contains_phrase():
    assert words("Over-the-Counter") == ["over", "the", "counter"]
    assert contains_phrase(["a", "over", "the", "counter"], ["over", "the", "counter"])
    assert not contains_phrase(["over", "counter"], ["over", "the", "counter"])


def test_group_fires_on_any_term_and_adds_the_others():
    e = SynonymExpander(GROUPS).expand("labeling for over the counter devices")
    assert e.groups == ("otc",)
    assert "otc" in e.added and "over-the-counter" in e.added
    assert "over the counter" not in e.added


def test_hyphen_query_matches_and_no_expansion_without_a_match():
    assert SynonymExpander(GROUPS).expand("over-the-counter wording").groups == ("otc",)
    assert SynonymExpander(GROUPS).expand("size of the font").added == ()


def test_sources_filter_drops_failure_derived_groups():
    e = SynonymExpander(GROUPS, frozenset({"cfr_definition"}))
    assert e.expand("the maker address").added == ()
    assert e.expand("udi rules").added == ("unique device identifier",)


def test_expansion_weights_in_bm25():
    docs = [("d1", "the manufacturer shall print the name"), ("d2", "the printer is large")]
    ix = InvertedIndex().build(docs)
    base = BM25Retriever(ix).search("maker name", k=2)
    exp = ExpandedBM25Retriever(ix, SynonymExpander(GROUPS), weight=0.5)
    assert exp.term_weights("maker name") == {"maker": 1.0, "name": 1.0, "manufacturer": 0.5}
    hits = exp.search("maker name", k=2)
    assert hits[0].doc_id == "d1" and hits[0].score > base[0].score


def test_zero_weight_equals_plain_bm25():
    docs = [("d1", "the manufacturer shall print the name"), ("d2", "the maker name")]
    ix = InvertedIndex().build(docs)
    plain = BM25Retriever(ix).search("maker name", k=2)
    exp = ExpandedBM25Retriever(ix, SynonymExpander(GROUPS), weight=0.0).search("maker name", k=2)
    assert [(h.doc_id, round(h.score, 9)) for h in plain] == [(h.doc_id, round(h.score, 9)) for h in exp]


def test_append_wrapper_extends_the_query_text():
    seen: list[str] = []

    class Spy:
        name = "spy"

        def search(self, query: str, k: int = 10) -> list[Hit]:
            seen.append(query)
            return []

    AppendExpansionRetriever(Spy(), SynonymExpander(GROUPS), "x").search("udi rules")
    assert seen == ["udi rules unique device identifier"]


def test_check_lexicon_flags_missing_evidence():
    chunks = [{"section": "830.3", "text": "Unique device identifier (UDI) means ..."}]
    lines, ok = check_lexicon([GROUPS[2]], chunks)
    assert ok and "ok" in lines[0]
    _, ok2 = check_lexicon([GROUPS[2]], [{"section": "830.3", "text": "nothing here"}])
    assert not ok2


def test_shipped_lexicon_is_well_formed():
    data = json.loads(Path("data/eval/synonyms.json").read_text(encoding="utf-8"))
    ids = [g["id"] for g in data["groups"]]
    assert len(ids) == len(set(ids))
    for g in data["groups"]:
        assert g["source"] in {"cfr_definition", "failure_derived"}
        assert len(g["terms"]) >= 2
        assert ("motivated_by" in g) == (g["source"] == "failure_derived")
