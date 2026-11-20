"""Selection mode tests (fake provider only, no model)."""
from __future__ import annotations

import json

from src.common.schemas import Chunk, Hit
from src.rag.pipeline import answer_question
from src.rag.provider import FakeProvider
from src.rag.selection import build_candidates, parse_selection, split_sentences
from src.rag.settings import RagSettings

SEL = RagSettings(output="select", max_tokens=60)
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


def ask(reply: str):
    return answer_question("what goes on the label?", "medicine", Stub(), CHUNKS, FakeProvider(reply), SEL, None)


def test_split_keeps_exact_substrings_and_abbreviations() -> None:
    text = TEXTS[1]
    parts = split_sentences(text)
    assert parts == ["See sec. 201.17 for location.",
                     "The statement of identity shall appear on the principal display panel."]
    assert all(p in text for p in parts)


def test_short_pieces_join_and_long_sentences_split() -> None:
    assert split_sentences("Yes. It is so.") == ["Yes. It is so."]
    long = "word " * 40 + "end; " + "more " * 40 + "done."
    parts = split_sentences(long)
    assert len(parts) == 2 and all(len(p.split()) <= 60 for p in parts)


def test_candidates_are_numbered_across_chunks() -> None:
    cands = build_candidates(list(CHUNKS.values()))
    assert [c.num for c in cands] == list(range(1, len(cands) + 1))
    assert cands[0].chunk_id == "c1" and cands[-1].chunk_id == "c2"


def test_parse_selection_checks() -> None:
    ok = parse_selection('{"no_answer": false, "sentences": [3, 1]}', 4)
    assert ok.numbers == [1, 3] and not ok.failed
    assert parse_selection('{"no_answer": true, "sentences": []}', 4).no_answer
    assert parse_selection("nope", 4).failed == "bad_json"
    assert parse_selection('{"no_answer": false, "sentences": []}', 4).failed == "empty"
    assert parse_selection('{"no_answer": false, "sentences": [1,2,3,4]}', 4).failed == "too_many"
    assert parse_selection('{"no_answer": false, "sentences": [9]}', 4).failed == "id_invalid"
    assert parse_selection('{"no_answer": false, "sentences": [2, 2]}', 4).failed == "id_invalid"
    assert parse_selection('{"no_answer": false, "sentences": ["1"]}', 4).failed == "bad_json"


def test_answer_is_the_exact_sentences_with_citations() -> None:
    cands = build_candidates(list(CHUNKS.values()))
    pick = [c.num for c in cands if c.text.startswith("The statement") or c.text.startswith("The label")]
    r = ask(json.dumps({"no_answer": False, "sentences": pick}))
    assert r.outcome == "answered" and r.mode == "selected"
    assert [s["text"] for s in r.sentences] == [c.text for c in cands if c.num in pick]
    for src in r.sources:
        assert src["quote"] in CHUNKS[src["chunk_id"]].text
    assert r.answer and "[1]" in r.answer and "[2]" in r.answer


def test_failures_fall_back_to_extractive() -> None:
    r = ask('{"no_answer": false, "sentences": [99]}')
    assert r.outcome == "needs_human_check" and r.cause == "verification" and r.sources
    assert ask('{"no_answer": true, "sentences": []}').cause == "no_answer"
    assert ask("garbage").checks["failed"] == "bad_json"
