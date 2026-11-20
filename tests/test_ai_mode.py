"""Step 24c: the optional AI answer (mode=ai). A fake provider only, so CI never needs Ollama or a model."""
from __future__ import annotations

import dataclasses
import json

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.rag.provider import FakeProvider, ProviderError, ProviderTimeout
from src.rag.settings import AI_MODEL, AI_SETTINGS
from src.rag.verify import parse_sentences
from tests.rag_api_helpers import stub_service

PUBLIC = {"question": "where does the expiration date go", "product_id": "prd_demo"}
PRO = {"question": "date format on a device label"}


@pytest.fixture()
def client():
    with TestClient(create_app("sqlite://", seed=False)) as c:
        c.app.state.rag = stub_service()
        yield c


def good_reply(client, module: str = "medicine") -> str:
    """A JSON answer that quotes the first stub passage and cites it."""
    chunks = client.app.state.rag.chunks(module)
    first = list(chunks)[0]
    sentence = parse_sentences(chunks[first].text)[0].text
    return json.dumps({"no_answer": False, "sentences": [{"text": sentence, "sources": [1]}]})


def ask_ai(client, provider, path: str = "/public/ask", body: dict | None = None) -> dict:
    """Start an AI ask with a fake provider and return the finished job (the test client runs the background task)."""
    client.app.state.ai_provider = provider
    started = client.post(f"{path}?mode=ai", json=body or PUBLIC)
    assert started.status_code == 202
    assert started.json()["kind"] == "ask" and started.json()["state"] == "queued"
    job = client.get(f"/jobs/{started.json()['job_id']}")
    assert job.status_code == 200
    return job.json()


def test_default_is_still_the_instant_extractive_answer(client) -> None:
    for url in ("/public/ask", "/public/ask?mode=extractive"):
        response = client.post(url, json=PUBLIC)
        assert response.status_code == 200 and "job_id" not in response.json()


def test_bad_mode_is_422(client) -> None:
    assert client.post("/public/ask?mode=magic", json=PUBLIC).status_code == 422
    assert client.post("/ask?mode=magic", json=PRO).status_code == 422


def test_ai_answer_public_and_professional(client) -> None:
    job = ask_ai(client, FakeProvider(good_reply(client)))
    assert job["state"] == "done" and job["progress"] == 1.0
    result = job["result"]
    assert result["model_used"] is True and "fallback_reason" not in result and result["model"] == AI_MODEL
    assert result["answer"]["abstained"] is False and result["answer"]["sources"] and "banner" in result["answer"]
    chunks = client.app.state.rag.chunks("medicine")
    assert all(s["quote"] in chunks[s["chunk_id"]].text for s in result["answer"]["sources"])
    pro = ask_ai(client, FakeProvider(good_reply(client, "device")), "/ask", PRO)["result"]
    assert pro["answer"]["abstained"] is False and "banner" not in pro["answer"]


@pytest.mark.parametrize("reply,reason", [
    (ProviderTimeout("slow"), "timeout"),
    (ProviderError("connection refused"), "model_unavailable"),
    ("not json at all", "verification_failed"),
    ('{"no_answer": false, "sentences": [{"text": "An invented claim.", "sources": [9]}]}', "verification_failed"),
])
def test_fallbacks_never_fail_the_job(client, reply, reason) -> None:
    job = ask_ai(client, FakeProvider(reply))
    assert job["state"] == "done"
    result = job["result"]
    assert result["fallback_reason"] == reason and result["model_used"] is False
    answer = result["answer"]
    assert answer["abstained"] is True and answer["reason"] == "needs_human_check" and len(answer["sources"]) == 3


def test_ollama_missing_falls_back_to_model_unavailable(client, monkeypatch) -> None:
    """No provider override, so the real OllamaProvider runs against a closed port."""
    monkeypatch.setattr("src.api.ask_jobs.AI_SETTINGS", dataclasses.replace(AI_SETTINGS, ollama_url="http://127.0.0.1:9"))
    job = ask_ai(client, None)
    assert job["state"] == "done" and job["result"]["fallback_reason"] == "model_unavailable"
    assert job["result"]["answer"]["sources"]


def test_model_saying_no_answer_is_not_a_fallback(client) -> None:
    job = ask_ai(client, FakeProvider('{"no_answer": true, "sentences": []}'))
    result = job["result"]
    assert result["model_used"] is True and "fallback_reason" not in result
    assert result["answer"]["abstained"] is True and "sources" not in result["answer"]


def test_unexpected_provider_error_still_shows_passages(client) -> None:
    job = ask_ai(client, FakeProvider(RuntimeError("bug")))
    assert job["state"] == "done" and job["result"]["fallback_reason"] == "model_unavailable"
    assert job["result"]["answer"]["sources"]


def test_unavailable_retrieval_ends_the_job_failed_with_the_error(client, monkeypatch) -> None:
    from src.rag.service import RagService

    monkeypatch.setattr("src.ir.step18_config.load_system", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    client.app.state.rag = RagService(provider=FakeProvider("x"))
    job = ask_ai(client, FakeProvider("x"))
    assert job["state"] == "failed" and job["error"]["error"] == "retrieval_unavailable"


def test_ai_settings_equal_the_frozen_step23e_run() -> None:
    from src.rag import step23e

    cfg = json.loads(step23e.CONFIG.read_text(encoding="utf-8"))
    assert AI_MODEL in cfg["models"]
    assert dataclasses.replace(AI_SETTINGS, timeout_s=step23e.SETTINGS.timeout_s) == step23e.SETTINGS
    assert AI_SETTINGS.timeout_s == 90.0


def test_ai_results_are_append_only(client) -> None:
    from sqlalchemy import text

    ask_ai(client, FakeProvider("not json"))
    with client.app.state.session_factory() as session:
        with pytest.raises(Exception, match="append-only"):
            session.execute(text("DELETE FROM ask_results"))
