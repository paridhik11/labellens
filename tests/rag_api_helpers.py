"""Shared setup for the ask API tests: real corpus chunks, a stub retriever and a fake provider (no model)."""
from __future__ import annotations

from typing import Any

from src.common.schemas import Hit
from src.rag.provider import FakeProvider
from src.rag.service import RagService
from src.rag.verify import parse_sentences


class FixedRetriever:
    """Returns the first n chunks of a module in corpus order with falling scores."""

    name = "fixed"

    def __init__(self, chunk_ids: list[str], top: float = 0.04) -> None:
        self.ids, self.top = chunk_ids, top

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """The fixed ids, best first."""
        return [Hit(doc_id=c, score=self.top / (i + 1), rank=i + 1) for i, c in enumerate(self.ids[:k])]


def stub_service(reply: str | Exception | None = None, threshold: float | None = None) -> RagService:
    """A RagService over real device and medicine chunks. The default reply cites the first chunk correctly."""
    probe = RagService(provider=FakeProvider("x"))
    retrievers: dict[str, Any] = {}
    sentence = ""
    for module in ("device", "medicine"):
        chunks = probe.chunks(module)
        ids = list(chunks)[:5]
        retrievers[module] = FixedRetriever(ids)
        if module == "medicine":
            sentence = parse_sentences(chunks[ids[0]].text)[0].text
    if reply is None:
        reply = f"{sentence} [1]"
    return RagService(provider=FakeProvider(reply), threshold=threshold, retrievers=retrievers, chunks=probe._chunks)
