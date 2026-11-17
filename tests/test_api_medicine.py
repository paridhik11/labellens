"""Step 25a: public medicine mode. Name matching, reference fields with evidence, section chunks, product-scoped ask.

The E5b models are replaced by stubs (no model download), but the catalog is the real data/medicine corpus.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.api.medicine import MedicineCatalog
from src.common.schemas import Hit
from src.rag.provider import NullProvider
from src.rag.service import RagService
from tests.medicine_helpers import stub_medicine
from tests.rag_api_helpers import stub_service

CATALOG = MedicineCatalog()
BY_NAME = {p.name: p for p in CATALOG.products.values()}


@pytest.fixture()
def client():
    with TestClient(create_app("sqlite://", seed=False)) as c:
        c.app.state.medicine = stub_medicine()
        c.app.state.rag = stub_service()
        yield c


def test_derived_fields_have_verbatim_evidence_and_no_invented_manufacturer() -> None:
    for product in CATALOG.products.values():
        assert product.fields["manufacturer"] is None and "manufacturer" in product.not_in_corpus
        for name, proof in product.evidence.items():
            chunk = CATALOG.chunks[proof["chunk_id"]]
            assert proof["quote"].lower() in f"{chunk.title} {chunk.text}".lower(), (product.name, name)
        assert product.fields["dosage_form"] and product.fields["active_substance"]
    assert BY_NAME["Omeprazole"].fields["pack_size"] == "42 tablets"  # not "20 tablet" from the 20 mg strength
    assert BY_NAME["ALBUTEROL SULFATE"].fields["pack_size"] is None  # five carton sizes, so no single value


def test_exact_name_matches_with_reference_fields_and_sections(client) -> None:
    body = client.post("/public/match", json={"product_name": "Childrens Ibuprofen"}).json()
    assert body["outcome"] == "matched" and body["banner"].startswith("Authenticity not verified")
    best = body["candidates"][0]
    assert best["product_name"] == "Childrens Ibuprofen" and best["dosage_form"] == "oral suspension"
    assert best["active_substance"] == "ibuprofen" and "manufacturer" in best["not_in_corpus"]
    assert "manufacturer" not in best
    sections = body["sections"]
    assert sections["summary"] and sections["warnings"] and sections["ingredients"] and sections["sources"]
    chunks = CATALOG.chunks
    for citation in sections["summary"] + sections["ingredients"] + sections["warnings"]:
        assert citation["source_type"] == "label_section" and citation["quote"] in chunks[citation["chunk_id"]].text
        assert citation["chunk_id"] in CATALOG.products[best["product_id"]].chunk_ids  # nothing from another product
    assert sections["sources"][0]["url"].startswith("https://dailymed.nlm.nih.gov/")


def test_unknown_product_is_no_reference_match_without_a_summary(client) -> None:
    body = client.post("/public/match", json={"product_name": "Zzyzx Gummies"}).json()
    assert body["outcome"] == "no_reference_match" and body["candidates"] == []
    assert "sections" not in body and "summary" not in body and body["message"]
    assert body["score"] < body["threshold"]


def test_blank_name_is_a_validation_error(client) -> None:
    assert client.post("/public/match", json={"product_name": "   "}).status_code == 422


def test_ask_public_with_a_reference_product_answers_from_its_chunks(client) -> None:
    product = BY_NAME["Omeprazole"]
    client.app.state.medicine._scoped = ScopedStub(product)
    client.app.state.rag = RagService(provider=NullProvider(), retrievers={}, chunks={})  # CFR path must stay unused
    ask = {"question": "what are the warnings", "product_id": product.product_id}
    body = client.post("/public/ask", json=ask).json()
    assert body["abstained"] is True and body["reason"] == "needs_human_check"  # provider off: passages, no answer
    assert body["sources"] and {s["chunk_id"] for s in body["sources"]} <= set(product.chunk_ids)
    assert all(s["source_type"] == "label_section" for s in body["sources"])
    assert body["banner"].startswith("Authenticity not verified")


def test_ask_public_with_an_unknown_product_id_keeps_the_cfr_path(client) -> None:
    ask = {"question": "where does the expiration date go", "product_id": "prd_demo"}
    body = client.post("/public/ask", json=ask).json()
    assert body["abstained"] is False and "product prd_demo" in body["based_on"]


class ScopedStub:
    """Returns the chunks of one product in order, ignoring the query (the real retriever is E5b)."""

    def __init__(self, product) -> None:
        self.ids = list(product.chunk_ids)

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=c, score=1.0 / (i + 1), rank=i + 1) for i, c in enumerate(self.ids)]


def test_the_medicine_page_is_served(client) -> None:
    page = client.get("/public/medicine")
    assert page.status_code == 200 and "Authenticity not verified" in page.text
