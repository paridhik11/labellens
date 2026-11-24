"""Abstain display for live labels: gate message, folded passages, storage sections, query rewriting."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from src.api.live_dailymed import LABEL_GATE, LiveService, parse_label
from src.common.schemas import Hit
from src.rag.provider import NullProvider
from src.rag.query_rewrite import expand_storage, resolve_pronouns, rewrite_for_retrieval
from src.rag.settings import RagSettings
from tests.live_helpers import LABEL, XML, FakeHttp, WordRetriever, live_service

STORAGE_TEXT = "Store at 20 to 25 C (68 to 77 F). Keep the bottle tightly closed and out of reach of children."
HOW_SUPPLIED = (b'<component><section><code code="34069-5" codeSystem="2.16.840.1.113883.6.1"/>'
                b"<title>16 HOW SUPPLIED</title><text>" + STORAGE_TEXT.encode() + b"</text></section></component>")
NO_MATCH = "This label doesn't seem to answer that."
PLAIN = RagSettings(rerank_display=False)


class FixedScore:
    """Retriever that scores its first chunks like a question with no shared wording (1/61, one rank-1 vote)."""

    def __init__(self, chunks, score: float = 1 / 61) -> None:
        self.chunks, self.score = chunks, score

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=c.chunk_id, score=self.score, rank=i, text=c.text) for i, c in enumerate(self.chunks[:k], 1)]


def _with_storage(xml: bytes) -> bytes:
    return xml.replace(b"</structuredBody>", HOW_SUPPLIED + b"</structuredBody>", 1)


def _service(tmp_path, xml: bytes, factory) -> tuple[LiveService, str]:
    service = live_service(tmp_path, FakeHttp(xml=xml))
    service._factory = factory
    return service, service.fetch(LABEL["setid"], LABEL["version"]).product_id


def test_repro_gate_miss_says_the_label_does_not_answer(tmp_path) -> None:
    service, pid = _service(tmp_path, XML, FixedScore)  # the fixture label has no storage section
    result, label = service.ask("how to store it", pid, NullProvider(), PLAIN)
    body = service.wire(result, label)
    assert body["abstained"] is True and body["reason"] == "needs_human_check"
    assert body["message"] == NO_MATCH and "language model" not in body["message"].lower()
    assert body["score"] < body["threshold"] == LABEL_GATE
    assert body["sources"]  # kept for the folded "Show closest passages (low confidence)" view
    assert result.question == "how to store it"


def test_storage_section_is_fetched_and_answers_a_storage_question(tmp_path) -> None:
    service, pid = _service(tmp_path, _with_storage(XML), WordRetriever)
    label = service.load(pid)
    assert any(c.section.startswith("storage/34069-5/") for c in label.chunks)
    result, label = service.ask("storage temperature", pid, NullProvider(), PLAIN)
    body = service.wire(result, label)
    assert result.score >= LABEL_GATE
    assert body["message"] != NO_MATCH  # the no language model text, a different reason
    top = body["sources"][0]
    assert "34069-5" in top["section"] and top["quote"] in STORAGE_TEXT
    assert top["source_type"] == "label_section"


def test_ai_mode_is_not_gated(tmp_path) -> None:
    service, pid = _service(tmp_path, XML, FixedScore)
    result, _ = service.ask("how to store it", pid, NullProvider(), PLAIN, gated=False)
    assert result.cause != "score_gate"


def test_curated_sections_do_not_change() -> None:
    from scripts.real.build_medicine_corpus import CATEGORIES as CURATED
    from src.api.live_dailymed import CATEGORIES, LIVE_CATEGORIES

    assert CATEGORIES == CURATED and set(LIVE_CATEGORIES) - set(CURATED) == {"34069-5", "44425-7", "34084-4"}
    plain = parse_label(XML, LABEL["setid"], LABEL["version"], "2026-01-02")
    with_storage = parse_label(_with_storage(XML), LABEL["setid"], LABEL["version"], "2026-01-02")
    assert len(with_storage.chunks) == len(plain.chunks) + 1


def test_stale_cache_is_fetched_again(tmp_path) -> None:
    http = FakeHttp(xml=_with_storage(XML))
    service = live_service(tmp_path, http)
    pid = service.fetch(LABEL["setid"], LABEL["version"]).product_id
    path = service._path(pid)
    old = json.loads(path.read_text(encoding="utf-8"))
    old.pop("parser_version")
    path.write_text(json.dumps(old), encoding="utf-8")
    service.fetch(LABEL["setid"], LABEL["version"])
    assert len([u for u in http.calls if "getFile" in u]) == 2


def test_rewrite_rules() -> None:
    assert resolve_pronouns("how to store it", "Metoprolol Tartrate / Lopressor") == "how to store Metoprolol Tartrate"
    assert resolve_pronouns("what is its dose", "Aspirin") == "what is Aspirin's dose"
    assert resolve_pronouns("is this safe", "") == "is this safe"
    assert resolve_pronouns("Italy city with items", "Aspirin") == "Italy city with items"
    assert expand_storage("how to store it").endswith("storage and handling, how supplied, store at")
    assert expand_storage("what is the dose") == "what is the dose"
    assert expand_storage(expand_storage("keep it cold")).count("how supplied") == 1
    assert rewrite_for_retrieval("how to store it", "Aspirin").startswith("how to store Aspirin storage and handling")


def test_gate_message_is_medicine_only() -> None:
    from src.rag.pipeline import MESSAGES, RagResult

    med = RagResult(outcome="needs_human_check", cause="score_gate", question="q", module="medicine")
    dev = RagResult(outcome="needs_human_check", cause="score_gate", question="q", module="device")
    off = RagResult(outcome="needs_human_check", cause="provider_off", question="q", module="medicine")
    assert med.message() == NO_MATCH and dev.message() == MESSAGES["score_gate"]
    assert "language model" in off.message().lower()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_ui_folds_low_confidence_passages_and_titles_label_sections() -> None:
    script = Path(__file__).parents[1] / "ui" / "tools" / "check_ask_panel.cjs"
    done = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr
