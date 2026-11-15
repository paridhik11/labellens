"""Citations: a real chunk id, its section and a verbatim quote, never invented.

Each rule has a fixed query and a set of accepted sections (frozen before the final
evaluation, see docs/CHECKER_SPEC.md section 5). The first retrieved hit from an accepted
section is cited. If none of the top k is accepted there is no citation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.tokenizer import tokenize


@dataclass(frozen=True)
class CitationSpec:
    """How one rule finds its citation. strength is direct, indirect or none (no regulation applies)."""

    query: str
    sections: frozenset[str]
    strength: str


class Citation(BaseModel):
    """Contract Citation (DATA_MODEL.md), read from the Chunk, plus the retrieval rank for evaluation."""

    source_type: str = "cfr"
    chunk_id: str
    source: str
    section: str
    title: str
    url: str
    quote: str
    rank: int = 0


_Q_MFR = "name and place of business of the manufacturer, packer or distributor on the label"
_Q_UDI = "label of every medical device shall bear a unique device identifier"
_Q_AIDC = "UDI automatic identification and data capture AIDC technology plain-text"
_Q_ISO = "UDI must conform to ISO/IEC 15459 issuing agency standards"
_Q_PI = "UDI production identifier segment lot or batch number expiration date"
_Q_DATE = "format of dates on a medical device label year month day hyphens expiration date"
_Q_RX = "prescription device label bears Rx only statement caution federal law restricts"
_Q_SYM = "symbols in labeling used without adjacent explanatory text, symbols glossary"


def _spec(query: str, section: str, strength: str) -> CitationSpec:
    return CitationSpec(query, frozenset({section}), strength)


CITATION_SPECS: dict[str, CitationSpec] = {
    "P-MFR": _spec(_Q_MFR, "801.1", "direct"),
    "P-ADDR": _spec(_Q_MFR, "801.1", "direct"),
    "R-NAMEPLACE": _spec(_Q_MFR, "801.1", "direct"),
    "P-UDI": _spec(_Q_UDI, "801.20", "indirect"),
    "R-UDI": _spec(_Q_UDI, "801.20", "direct"),
    "B-READ": _spec(_Q_AIDC, "801.40", "indirect"),
    "B-GS1": _spec(_Q_ISO, "830.20", "indirect"),
    "B-LOT": _spec(_Q_PI, "801.40", "direct"),
    "B-EXP": _spec(_Q_PI, "801.40", "direct"),
    "D-FMT": _spec(_Q_DATE, "801.18", "direct"),
    "R-RX": _spec(_Q_RX, "801.109", "direct"),
    "S-MFR": _spec(_Q_SYM, "801.15", "indirect"),
    "S-EXP": _spec(_Q_SYM, "801.15", "indirect"),
}
NO_CITATION_RULES = ("P-NAME", "P-REF", "X-HEALTH")  # internal consistency rules, strength none
MAX_QUOTE_CHARS = 300


def best_quote(text: str, query: str) -> str:
    """The text segment (up to about 300 characters) with the most query terms, copied verbatim.

    Segments end at paragraph breaks, full stops, semicolons and colons followed by a space.
    A short best segment is extended with the segments after it.
    """
    spans = [m.span() for m in re.finditer(r"[^\n]+?(?:[.;:](?=\s)|(?=\n)|$)", text) if m.group().strip()]
    if not spans:
        raise ValueError("chunk has no text")
    wanted = set(tokenize(query))
    scores = [len(wanted & set(tokenize(text[a:b]))) for a, b in spans]
    best = max(range(len(spans)), key=lambda i: (scores[i], -i))
    start, end = spans[best]
    j = best
    while end - start < 80 and j + 1 < len(spans) and spans[j + 1][1] - start <= MAX_QUOTE_CHARS:
        j += 1
        end = spans[j][1]
    quote = text[start:end].strip()
    if len(quote) > MAX_QUOTE_CHARS:
        cut = quote[:MAX_QUOTE_CHARS]
        quote = cut[: cut.rfind(" ")] if " " in cut else cut
    if quote not in text:
        raise AssertionError("quote is not a verbatim substring of the chunk")
    return quote


def find_citation(spec: CitationSpec, retriever: Retriever, chunks: dict[str, Chunk], k: int) -> Citation | None:
    """Cite the highest ranked hit from an accepted section, or return None when the top k has none."""
    for rank, hit in enumerate(retriever.search(spec.query, k=k), start=1):
        chunk = chunks.get(hit.doc_id)
        if chunk is not None and chunk.section in spec.sections:
            return Citation(
                chunk_id=chunk.chunk_id, source=chunk.source, section=chunk.section, title=chunk.title,
                url=chunk.url, quote=best_quote(chunk.text, spec.query), rank=rank,
            )
    return None
