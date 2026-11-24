"""CR-29: passages of sections that do not apply to a device product are dropped, each section shows once,
in the extractive passages and in what the AI model sees. The score gate still reads the raw top hit."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.seed import PRODUCT_ID
from src.rag.applicability import applies, filter_chunks, record_text
from src.rag.pipeline import answer_question
from src.rag.provider import NullProvider, ProviderUnavailable
from src.rag.service import RagService
from src.rag.settings import AI_SETTINGS
from tests.rag_api_helpers import FixedRetriever

# what retrieval returned for the expiration-date question on Golden Pump: latex condom chunks ranked high
IDS = ["fda_21cfr801_s801.435_c1", "fda_21cfr801_s801.18", "fda_21cfr801_s801.435_c2", "fda_21cfr801_s801.435_c3"]


class CapturingProvider:
    """Records the prompt the model would see, then says it is not running (extractive fallback)."""

    name = "capture"

    def __init__(self) -> None:
        self.users: list[str] = []

    def generate(self, system: str, user: str, *, max_tokens: int) -> str:
        """Record and fail."""
        self.users.append(user)
        raise ProviderUnavailable("off")

    def generate_json(self, system: str, user: str, schema: dict, *, max_tokens: int) -> str:
        """Record and fail."""
        self.users.append(user)
        raise ProviderUnavailable("off")


@pytest.fixture(scope="module")
def device_chunks() -> dict:
    return RagService(provider=NullProvider()).chunks("device")


def test_record_text_and_applies() -> None:
    text = record_text({"name": "Golden Pump", "extra": {"lot": "LOT1"}, "version": 3})
    assert "Golden Pump" in text and "LOT1" in text
    assert not applies("801.435", text) and applies("801.18", text)
    assert applies("801.435", "Natural rubber latex condom")


def test_filter_drops_latex_section_and_dedupes(device_chunks) -> None:
    chunks = [device_chunks[i] for i in IDS]
    kept = filter_chunks(chunks, "Golden Pump infusion pump")
    assert [c.chunk_id for c in kept] == ["fda_21cfr801_s801.18"]
    kept = filter_chunks(chunks, "latex condom")
    assert [c.chunk_id for c in kept] == ["fda_21cfr801_s801.435_c1", "fda_21cfr801_s801.18"]


def test_model_sees_only_filtered_passages_and_gate_reads_raw_top(device_chunks) -> None:
    provider = CapturingProvider()
    retriever = FixedRetriever(IDS)
    result = answer_question("what must a label show for the expiration date?", "device", retriever, device_chunks,
                             provider, AI_SETTINGS, threshold=0.0315,
                             context_filter=lambda cs: filter_chunks(cs, "Golden Pump"))
    assert provider.users and "801.435" not in provider.users[0]
    assert {s["section"] for s in result.sources} == {"801.18"}
    assert result.score == 0.04  # unfiltered top hit (FixedRetriever top score), gate unchanged


def test_without_filter_nothing_changes(device_chunks) -> None:
    result = answer_question("expiration date", "device", FixedRetriever(IDS), device_chunks, NullProvider(),
                             threshold=None)
    assert result.retrieved == IDS


def test_api_ask_with_product_id_filters(device_chunks) -> None:
    with TestClient(create_app("sqlite://", seed=True)) as client:
        client.app.state.rag = RagService(provider=NullProvider(), retrievers={"device": FixedRetriever(IDS)},
                                          chunks={"device": device_chunks})
        q = "what must a label show for the expiration date?"
        raw = client.post("/ask", json={"question": q}).json()
        assert any(s["section"] == "801.435" for s in raw["sources"])
        body = client.post("/ask", json={"question": q, "product_id": PRODUCT_ID}).json()
        sections = [s["section"] for s in body["sources"]]
        assert "801.435" not in sections and len(sections) == len(set(sections))
        assert client.post("/ask", json={"question": q, "product_id": "prd_nope"}).status_code == 404
