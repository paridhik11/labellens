"""Step 23c: askPublic and askProfessional are real. Fake provider and fixed retrieval, so no model is needed."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.rag.provider import NullProvider, ProviderError
from src.rag.service import RagService
from tests.rag_api_helpers import stub_service

PUBLIC = {"question": "where does the expiration date go", "product_id": "prd_demo"}
PRO = {"question": "date format on a device label"}


@pytest.fixture()
def client():
    with TestClient(create_app("sqlite://", seed=False)) as c:
        c.app.state.rag = stub_service()
        yield c


def corpus_ids(client, module):
    return set(client.app.state.rag.chunks(module))


def test_public_answer_has_citations_from_the_medicine_module(client) -> None:
    body = client.post("/public/ask", json=PUBLIC).json()
    assert body["abstained"] is False and body["sources"] and body["banner"].startswith("Authenticity not verified")
    assert {s["chunk_id"] for s in body["sources"]} <= corpus_ids(client, "medicine")
    assert "X-Mock" not in client.post("/public/ask", json=PUBLIC).headers


def test_professional_answer_uses_device_chunks_and_has_no_banner(client) -> None:
    body = client.post("/ask", json=PRO).json()
    assert body["abstained"] is False and "banner" not in body
    assert {s["chunk_id"] for s in body["sources"]} <= corpus_ids(client, "device")
    assert not {s["chunk_id"] for s in body["sources"]} & corpus_ids(client, "medicine")


def test_every_answered_source_has_a_verbatim_quote(client) -> None:
    for path, payload, module in (("/public/ask", PUBLIC, "medicine"), ("/ask", PRO, "device")):
        chunks = client.app.state.rag.chunks(module)
        for s in client.post(path, json=payload).json()["sources"]:
            assert s["quote"] in chunks[s["chunk_id"]].text


def test_advice_question_is_out_of_scope_with_null_score(client) -> None:
    body = client.post("/public/ask", json={**PUBLIC, "question": "how much ibuprofen should I take for a headache"}).json()  # noqa: E501
    assert body["abstained"] is True and body["reason"] == "out_of_scope"
    assert body["score"] is None and body["threshold"] is None and body["score_name"] == "scope_rule"


def test_provider_off_gives_extractive_quotes_marked_needs_human_check(client) -> None:
    client.app.state.rag = RagService(provider=NullProvider(), retrievers=client.app.state.rag._retrievers,
                                      chunks=client.app.state.rag._chunks)
    body = client.post("/ask", json=PRO).json()
    assert body["abstained"] is True and body["reason"] == "needs_human_check" and "answer" not in body
    assert len(body["sources"]) == 3
    chunks = client.app.state.rag.chunks("device")
    assert all(s["quote"] in chunks[s["chunk_id"]].text for s in body["sources"])


def test_failed_verification_and_provider_error_fall_back(client) -> None:
    for reply in ("An invented claim with a bad marker [9].", ProviderError("boom")):
        client.app.state.rag = stub_service(reply)
        body = client.post("/public/ask", json=PUBLIC).json()
        assert body["abstained"] and body["reason"] == "needs_human_check" and body["sources"]


def test_score_gate_reports_score_and_threshold_without_quotes(client) -> None:
    client.app.state.rag = stub_service(threshold=0.5)
    body = client.post("/ask", json=PRO).json()
    assert body["reason"] == "needs_human_check" and body["score"] == 0.04 and body["threshold"] == 0.5
    assert "sources" not in body


def test_invalid_requests_are_422(client) -> None:
    assert client.post("/ask", json={"question": "   "}).status_code == 422
    assert client.post("/public/ask", json={"question": "x"}).status_code == 422
    assert client.post("/ask", json={"question": "x", "extra": 1}).status_code == 422


def test_unavailable_retrieval_is_503(client, monkeypatch) -> None:
    def boom(*a, **k):
        raise RuntimeError("cache missing")

    monkeypatch.setattr("src.ir.step18_config.load_system", boom)
    client.app.state.rag = RagService(provider=NullProvider())
    response = client.post("/ask", json=PRO)
    assert response.status_code == 503 and response.json()["error"] == "retrieval_unavailable"
