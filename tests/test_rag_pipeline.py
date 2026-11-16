"""RAG pipeline tests. Only the fake provider is used, so CI never needs Ollama or a model."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.common.schemas import Chunk, Hit
from src.rag.pipeline import answer_question
from src.rag.provider import FakeProvider, NullProvider, ProviderError, provider_from_env
from src.rag.scope import out_of_scope
from src.rag.settings import RagSettings
from src.rag.verify import parse_sentences, verify

TEXTS = [
    "The expiration date shall appear on the immediate container label of the drug product. "
    "Use the format month and year.",
    "The label shall bear the name and place of business of the manufacturer packer or distributor.",
    "Prescription drug labels shall bear the statement Rx only.",
]
CHUNKS = {
    f"c{i}": Chunk(chunk_id=f"c{i}", source="eCFR", url=f"https://x/{i}", title=f"T{i}", section=f"201.{i}",
                   text=t, module="medicine")
    for i, t in enumerate(TEXTS, start=1)
}


class StubRetriever:
    """Returns the three chunks in order with falling scores, and counts calls."""

    name = "stub"

    def __init__(self, top: float = 0.03) -> None:
        self.top, self.calls = top, 0

    def search(self, query: str, k: int = 10) -> list[Hit]:
        self.calls += 1
        return [Hit(doc_id=f"c{i}", score=self.top / i, rank=i) for i in (1, 2, 3)][:k]


def run(provider, threshold=None, question="where is the expiration date on the drug label"):
    return answer_question(question, "medicine", StubRetriever(), CHUNKS, provider, RagSettings(), threshold)


def test_answered_with_valid_markers_and_verbatim_quotes() -> None:
    r = run(FakeProvider("The expiration date shall appear on the container label [1]. The label names the manufacturer [2]."))  # noqa: E501
    assert r.outcome == "answered" and r.mode == "generated"
    assert [s["chunk_id"] for s in r.sources] == ["c1", "c2"]
    for s in r.sources:
        assert s["quote"] in CHUNKS[s["chunk_id"]].text
    assert r.answer.endswith("[2]") and "[1]" in r.answer
    wire = r.to_wire(based_on="Demo product")
    assert wire["abstained"] is False and wire["sources"] and "banner" in wire


def test_markers_are_renumbered_in_order_of_first_citation() -> None:
    r = run(FakeProvider("The label names the manufacturer packer or distributor [2]. The expiration date shall appear on the label [1]."))  # noqa: E501
    assert r.outcome == "answered"
    assert [s["chunk_id"] for s in r.sources] == ["c2", "c1"]
    assert r.answer == (
        "The label names the manufacturer packer or distributor. [1] The expiration date shall appear on the label. [2]"
    )


def test_invented_marker_falls_back_to_quotes() -> None:
    r = run(FakeProvider("The expiration date shall appear on the label [9]."))
    assert r.outcome == "needs_human_check" and r.cause == "verification"
    assert r.checks["failed"] == "id_invalid" and r.mode == "extractive" and len(r.sources) == 3
    for s in r.sources:
        assert s["quote"] in CHUNKS[s["chunk_id"]].text
    assert r.answer is None and "answer" not in r.to_wire()


def test_sentence_without_marker_fails() -> None:
    r = run(FakeProvider("The expiration date shall appear on the label."))
    assert r.checks["failed"] == "marker_missing" and r.outcome == "needs_human_check"


def test_no_answer_has_no_quotes() -> None:
    r = run(FakeProvider("NO_ANSWER"))
    assert (r.outcome, r.cause, r.sources) == ("needs_human_check", "no_answer", [])


@pytest.mark.parametrize("provider,cause", [(NullProvider(), "provider_off"), (FakeProvider(ProviderError("boom")), "provider_error")])  # noqa: E501
def test_provider_off_or_failing_gives_extractive_quotes(provider, cause) -> None:
    r = run(provider)
    assert r.outcome == "needs_human_check" and r.cause == cause and r.mode == "extractive" and r.sources


def test_banned_claim_fails() -> None:
    r = run(FakeProvider("The label complies with the expiration date rule [1]."))
    assert r.checks["failed"] == "banned_claim"


def test_low_overlap_fails() -> None:
    r = run(FakeProvider("Aspirin lowers fever in children quickly [1]."))
    assert r.checks["failed"] == "low_overlap"


def test_score_gate_blocks_before_the_provider() -> None:
    provider = FakeProvider("The expiration date shall appear on the label [1].")
    r = run(provider, threshold=0.05)
    assert (r.outcome, r.cause, r.sources, r.score, r.threshold) == ("needs_human_check", "score_gate", [], 0.03, 0.05)
    assert provider.calls == []
    wire = r.to_wire()
    assert wire["reason"] == "needs_human_check" and wire["score_name"] == "e5b_top_score" and wire["threshold"] == 0.05


def test_scope_rule_skips_retrieval() -> None:
    retriever = StubRetriever()
    r = answer_question("how much ibuprofen should I take for my headache", "medicine", retriever, CHUNKS, FakeProvider("x"))  # noqa: E501
    assert r.outcome == "out_of_scope" and retriever.calls == 0
    wire = r.to_wire()
    assert wire["reason"] == "out_of_scope" and wire["score"] is None and wire["score_name"] == "scope_rule"


def test_professional_wire_has_no_banner() -> None:
    wire = run(FakeProvider("The expiration date shall appear on the label [1].")).to_wire(banner=False)
    assert "banner" not in wire and "based_on" not in wire and wire["sources"]


def test_verify_counts_and_length() -> None:
    chunks = list(CHUNKS.values())
    v = verify("One thing [1]. Two [2]. Three [3]. Four [1]. Five [2].", chunks, max_sentences=4, min_overlap=0.0)
    assert v.failed == "too_long" and v.n_sentences == 5


def test_parse_sentences_joins_trailing_markers() -> None:
    s = parse_sentences("The date goes on the label. [1] The name goes there too [2][3].")
    assert [x.markers for x in s] == [[1], [2, 3]]
    assert s[0].text == "The date goes on the label."


def test_provider_from_env(monkeypatch) -> None:
    monkeypatch.delenv("LABELLENS_LLM", raising=False)
    assert provider_from_env().name == "off"
    monkeypatch.setenv("LABELLENS_LLM", "ollama:qwen2.5:1.5b-instruct-q4_K_M")
    assert provider_from_env().name == "ollama:qwen2.5:1.5b-instruct-q4_K_M"


def test_scope_rule_has_no_false_trigger_on_existing_queries() -> None:
    """None of the answerable or no_answer evaluation queries is flagged as personal advice."""
    root = Path(__file__).resolve().parents[1] / "data" / "eval"
    queries = []
    for name, module_col in (("queries_t1.tsv", 2), ("queries_t1_abstain.tsv", 2), ("fresh_web_faq.tsv", 3)):
        with open(root / name, encoding="utf8", newline="") as fh:
            rows = [r for r in csv.reader(fh, delimiter="\t") if r and r[0] != "qid"]
        queries += [(r[1], r[module_col]) for r in rows]
    assert len(queries) > 100
    flagged = [q for q, m in queries if out_of_scope(q, m)]
    assert flagged == []
