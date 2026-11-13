"""Tests for src.ir.partboost."""
from __future__ import annotations

from src.common.schemas import Hit
from src.ir.partboost import PartBoostRetriever, build_part_index, part_of

DOCS = [
    ("fda_21cfr801_s801.1_c1", "label name place of business manufacturer packer"),
    ("fda_21cfr801_s801.2_c1", "label statement prescription device legend"),
    ("fda_21cfr830_s830.1_c1", "unique device identifier udi barcode gudid database"),
    ("fda_21cfr830_s830.2_c1", "device identifier issuing agency label"),
    ("fda_21cfr803_s803.1_c1", "adverse event report death serious injury"),
]


class FixedBase:
    """Returns the documents in a fixed order, whatever the query."""

    name = "fixed"

    def __init__(self, order: list[str]) -> None:
        self.order = order

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=d, score=1.0 / (i + 1), rank=i + 1, text=d)
                for i, d in enumerate(self.order[:k])]


ORDER = [d for d, _ in DOCS]


def test_part_of():
    assert part_of("fda_21cfr801_s801.1_c1") == "21cfr801"


def test_part_index_has_one_doc_per_part():
    ix = build_part_index(DOCS)
    assert sorted(ix.doc_ids) == ["21cfr801", "21cfr803", "21cfr830"]


def test_topic_part_follows_query_vocabulary():
    r = PartBoostRetriever(FixedBase(ORDER), build_part_index(DOCS), top_parts=1)
    assert r.topic_parts("unique device identifier barcode") == ["21cfr830"]
    assert r.topic_parts("adverse event death") == ["21cfr803"]
    assert r.topic_parts("zzz qqq") == []


def test_beta_zero_keeps_base_order():
    r = PartBoostRetriever(FixedBase(ORDER), build_part_index(DOCS), beta=0.0)
    assert [h.doc_id for h in r.search("unique device identifier", k=5)] == ORDER


def test_boost_lifts_topic_part_chunks_only_as_far_as_beta_allows():
    ix = build_part_index(DOCS)
    # rank 3 (830) vs rank 1 (801): 1/63*(1+b) > 1/61 needs b > 0.0328
    small = PartBoostRetriever(FixedBase(ORDER), ix, beta=0.02)
    big = PartBoostRetriever(FixedBase(ORDER), ix, beta=0.5)
    q = "unique device identifier barcode"
    assert small.search(q, k=5)[0].doc_id == ORDER[0]
    assert big.search(q, k=5)[0].doc_id == "fda_21cfr830_s830.1_c1"


def test_no_matching_part_means_no_change_and_ranks_are_renumbered():
    r = PartBoostRetriever(FixedBase(ORDER), build_part_index(DOCS), beta=1.0)
    hits = r.search("zzz qqq", k=3)
    assert [h.doc_id for h in hits] == ORDER[:3]
    assert [h.rank for h in hits] == [1, 2, 3]
