"""Parse a generated answer and verify it. Any failed check means the extractive fallback."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.common.schemas import Chunk
from src.ir.tokenizer import tokenize

MARKER = re.compile(r"\[(\d+)\]")
BANNED = re.compile(r"\b(complies|compliant|compliance with|approved by|safe to use|you should take)\b", re.I)
NO_ANSWER = "NO_ANSWER"


@dataclass
class Sentence:
    """One answer sentence: display text without markers and the passage numbers it cites."""

    text: str
    markers: list[int]


@dataclass
class Verification:
    """Result of verify(): ok, the first failed check and its detail, and counts for the report."""

    ok: bool
    failed: str = ""
    detail: str = ""
    sentences: list[Sentence] = field(default_factory=list)
    n_sentences: int = 0
    n_valid_sentences: int = 0  # sentences with a marker whose markers are all in 1..k


def parse_sentences(text: str) -> list[Sentence]:
    """Split on sentence ends; a piece with no words (only markers) joins the previous sentence."""
    pieces = [p.strip() for p in re.split(r"(?<=[.!?\]])\s+(?=[A-Z0-9\[])", text.strip()) if p.strip()]
    out: list[Sentence] = []
    for piece in pieces:
        markers = [int(m) for m in MARKER.findall(piece)]
        clean = re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", MARKER.sub("", piece))).strip()
        if not re.search(r"[A-Za-z]", clean) and out:
            out[-1].markers.extend(markers)
            continue
        out.append(Sentence(clean, markers))
    return out


def verify(text: str, chunks: list[Chunk], *, max_sentences: int, min_overlap: float) -> Verification:
    """Run the checks of docs/RAG_SPEC.md section 4 in order. NO_ANSWER is handled by the caller."""
    sentences = parse_sentences(text)
    k = len(chunks)
    result = Verification(ok=False, sentences=sentences, n_sentences=len(sentences))
    result.n_valid_sentences = sum(bool(s.markers) and all(1 <= m <= k for m in s.markers) for s in sentences)
    if not sentences:
        result.failed, result.detail = "empty", "no sentences"
        return result
    if len(sentences) > max_sentences:
        result.failed, result.detail = "too_long", f"{len(sentences)} sentences"
        return result
    for s in sentences:
        if not s.markers:
            result.failed, result.detail = "marker_missing", s.text[:60]
            return result
    for s in sentences:
        bad = [m for m in s.markers if not 1 <= m <= k]
        if bad:
            result.failed, result.detail = "id_invalid", f"marker {bad[0]} of {k}"
            return result
    banned = BANNED.search(text)
    if banned:
        result.failed, result.detail = "banned_claim", banned.group(0)
        return result
    for s in sentences:
        words = set(tokenize(s.text))
        cited: set[str] = set()
        for m in s.markers:
            cited |= set(tokenize(chunks[m - 1].text))
        if words and len(words & cited) / len(words) < min_overlap:
            result.failed, result.detail = "low_overlap", s.text[:60]
            return result
    result.ok = True
    return result
