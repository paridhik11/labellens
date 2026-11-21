"""Sentence reranker tests (stub scorer, no model)."""
from __future__ import annotations

import json

from src.common.schemas import Chunk, Hit
from src.rag import rerank
from src.rag.pipeline import answer_question, reranked_display_sources
from src.rag.provider import NullProvider
from src.rag.rerank_eval import pick_threshold
from src.rag.settings import RagSettings

TEXTS = [
    "The label shall bear the expiration date. Use the format month and year; do not use only numbers.",
    "See sec. 201.17 for location. The statement of identity shall appear on the principal display panel.",
]
CHUNKS = {
    f"c{i}": Chunk(chunk_id=f"c{i}", source="eCFR", url="https://x", title=f"T{i}", section=f"201.{i}", text=t,
                   module="medicine")
    for i, t in enumerate(TEXTS, start=1)
}


class Stub:
    """Two chunks, falling scores."""

    name = "stub"

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=f"c{i}", score=0.03 / i, rank=i) for i in (1, 2)][:k]


class WordScorer:
    """Score = number of words of the sentence that are also in the question (10 per shared word, minus 5)."""

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [10.0 * len(set(q.lower().split()) & set(s.lower().split())) - 5 for q, s in pairs]


def ask(output: str = "rerank", threshold: float | None = None, display: bool = True):
    settings = RagSettings(output=output, rerank_threshold=threshold, rerank_display=display)
    return answer_question("what is the expiration date format?", "medicine", Stub(), CHUNKS, NullProvider(),
                           settings, None)


def test_rank_sentences_orders_by_score_and_keeps_exact_text() -> None:
    ranked = rerank.rank_sentences("expiration date format", list(CHUNKS.values()), WordScorer())
    assert [r.score for r in ranked] == sorted((r.score for r in ranked), reverse=True)
    assert all(r.candidate.text in TEXTS[r.candidate.chunk_rank - 1] for r in ranked)


def test_top_sentences_applies_threshold_and_cap() -> None:
    ranked = rerank.rank_sentences("the expiration date format", list(CHUNKS.values()), WordScorer())
    assert len(rerank.top_sentences(ranked, -1e9)) == rerank.TOP
    assert rerank.top_sentences(ranked, 1e9) == []


def test_rerank_mode_answers_with_cited_sentences() -> None:
    rerank.set_scorer(WordScorer())
    result = ask(threshold=0.0)
    assert result.outcome == "answered" and result.mode == "reranked"
    assert result.sentences[0]["text"] in TEXTS[0] + TEXTS[1]
    assert all(s["quote"] in TEXTS[0] + TEXTS[1] for s in result.sources)
    assert result.checks["scored"][0]["score"] >= result.checks["scored"][-1]["score"]


def test_rerank_mode_below_threshold_is_no_answer() -> None:
    rerank.set_scorer(WordScorer())
    result = ask(threshold=1e6)
    assert result.outcome == "needs_human_check" and result.cause == "rerank_gate" and not result.sources


def test_score_gate_still_applies_before_reranking() -> None:
    rerank.set_scorer(WordScorer())
    result = answer_question("what is the expiration date format?", "medicine", Stub(), CHUNKS, NullProvider(),
                             RagSettings(output="rerank"), 0.5)
    assert result.cause == "score_gate" and not result.sources


def test_default_display_uses_reranked_sentences_and_keeps_outcome(monkeypatch) -> None:
    monkeypatch.setattr(rerank, "frozen_threshold", lambda path=None: 5.0)
    rerank.set_scorer(WordScorer())
    result = ask(output="text")
    assert result.outcome == "needs_human_check" and result.cause == "provider_off"
    assert result.sources and all(len(s["quote"].split()) < 25 for s in result.sources)


def test_default_display_falls_back_to_chunk_quotes_without_model(monkeypatch) -> None:
    monkeypatch.setattr(rerank, "frozen_threshold", lambda path=None: 5.0)
    result = ask(output="text")  # conftest scorer raises, like an uncached model
    assert result.cause == "provider_off" and len(result.sources) == 2
    assert reranked_display_sources("x", list(CHUNKS.values())) == []


def test_default_display_falls_back_when_no_sentence_reaches_t(monkeypatch) -> None:
    monkeypatch.setattr(rerank, "frozen_threshold", lambda path=None: 1e6)
    rerank.set_scorer(WordScorer())
    assert len(ask(output="text").sources) == 2


def test_display_off_shows_chunk_quotes(monkeypatch) -> None:
    monkeypatch.setattr(rerank, "frozen_threshold", lambda path=None: 5.0)
    rerank.set_scorer(WordScorer())
    assert len(ask(output="text", display=False).sources) == 2


def test_pick_threshold_prefers_high_t_on_ties_and_respects_wrong_rate() -> None:
    table = [{"T": t, "hit": h, "n_ans": 10, "wrong": w, "n_non": 5}
             for t, h, w in [(0, 9, 2), (1, 8, 1), (2, 8, 0), (3, 5, 0)]]
    assert pick_threshold(table) == 2


def test_frozen_config_exists_and_matches_plan() -> None:
    cfg = json.loads(rerank.CONFIG_PATH.read_text(encoding="utf-8"))
    assert cfg["model"] == rerank.MODEL and cfg["threshold_T"] == 1 and rerank.frozen_threshold() == 1.0
