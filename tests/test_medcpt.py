"""Tests for src.ir.medcpt (fake encoders, no model is loaded)."""
from __future__ import annotations

import numpy as np

from src.common.schemas import Chunk
from src.ir.medcpt import MedCPTDenseRetriever

CHUNKS = [Chunk(chunk_id=f"c{i}", source="F", title=f"title {i}", text=f"text {i}", hash=f"h{i}")
          for i in range(4)]


def _article(items):  # one fixed vector per chunk, recorded so the test can check the (title, text) pairs
    _article.seen = items
    return np.array([[1, 0], [0, 1], [2, 2], [-1, 0]], dtype=np.float32)


def _query(items):
    return np.array([[1.0, 0.5] for _ in items], dtype=np.float32)


def test_search_uses_unnormalised_inner_product_and_title_text_pairs(tmp_path):
    r = MedCPTDenseRetriever.from_chunks(CHUNKS, cache_dir=tmp_path, article_encoder=_article, query_encoder=_query)
    assert _article.seen[0] == ["title 0", "text 0"]
    hits = r.search("anything", k=3)
    assert [h.doc_id for h in hits] == ["c2", "c0", "c1"]  # scores 3.0, 1.0, 0.5
    assert [round(h.score, 6) for h in hits] == [3.0, 1.0, 0.5]
    assert [h.rank for h in hits] == [1, 2, 3] and hits[0].text == "text 2"


def test_embeddings_are_cached_and_reused(tmp_path):
    calls = []

    def counting(items):
        calls.append(len(items))
        return _article(items)

    MedCPTDenseRetriever.from_chunks(CHUNKS, cache_dir=tmp_path, article_encoder=counting, query_encoder=_query)
    again = MedCPTDenseRetriever.from_chunks(CHUNKS, cache_dir=tmp_path, article_encoder=counting,
                                             query_encoder=_query)
    assert calls == [4]  # the second build did not encode again
    assert again.search("q", k=1)[0].doc_id == "c2"
    changed = [CHUNKS[0].model_copy(update={"hash": "new"})] + CHUNKS[1:]
    MedCPTDenseRetriever.from_chunks(changed, cache_dir=tmp_path, article_encoder=counting, query_encoder=_query)
    assert calls == [4, 4]  # a changed content hash invalidates the cache
