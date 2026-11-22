"""Recorded DailyMed fixtures and a stub retriever for the live lookup tests. No network, no models."""
from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from src.api.live_dailymed import BASE, HUMAN_DOCTYPES, LiveService, LiveUnavailable
from src.common.schemas import Chunk, Hit

FIX = Path(__file__).parent / "fixtures" / "dailymed"
LABEL = json.loads((FIX / "label_cetirizine.json").read_text())  # {"setid", "version"} of the recorded label
XML = (FIX / "label_cetirizine.xml").read_bytes()


def zip_of(xml: bytes) -> bytes:
    """A DailyMed style archive holding one SPL XML."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("label.xml", xml)
    return buffer.getvalue()


class FakeHttp:
    """Answers search URLs with the recorded JSON and the label URL with the recorded label. Counts calls."""

    def __init__(self, error: LiveUnavailable | None = None, xml: bytes = XML, empty: bool = False) -> None:
        self.error, self.xml, self.empty = error, xml, empty
        self.calls: list[str] = []

    def __call__(self, url: str, timeout: float, max_bytes: int) -> bytes:
        assert timeout > 0 and url.startswith(BASE)
        self.calls.append(url)
        if self.error:
            raise self.error
        if "spls.json" in url:
            if self.empty:
                return json.dumps({"data": [], "metadata": {"total_elements": 0}}).encode()
            for doctype in HUMAN_DOCTYPES:
                if f"doctype={doctype}" in url:
                    return (FIX / f"search_cetirizine_{doctype}.json").read_bytes()
        if "getFile.cfm" in url:
            return zip_of(self.xml)
        raise AssertionError(url)


class WordRetriever:
    """Ranks chunks by shared words with the query (stands in for E5b)."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Best chunks first."""
        words = set(query.lower().split())
        scored = sorted(((len(words & set(c.text.lower().split())), c) for c in self.chunks), key=lambda t: -t[0])
        return [Hit(doc_id=c.chunk_id, score=float(s) + 0.01, rank=i, text=c.text) for i, (s, c) in enumerate(scored[:k], 1)]


def live_service(tmp_path: Path, http: FakeHttp | None = None) -> LiveService:
    """A LiveService over fixtures, a temp cache and the word retriever."""
    return LiveService(http=http or FakeHttp(), cache_dir=tmp_path / "live", retriever_factory=WordRetriever,
                       today=lambda: date(2026, 1, 2))
