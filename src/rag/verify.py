"""Parse a generated answer and verify it. Any failed check means the extractive fallback."""
from __future__ import annotations

import json
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
    return _check(parse_sentences(text), text, chunks, max_sentences=max_sentences, min_overlap=min_overlap)


def _check(
    sentences: list[Sentence], text: str, chunks: list[Chunk], *, max_sentences: int, min_overlap: float,
) -> Verification:
    """The shared checks, applied to sentences however they were obtained (prose markers or parsed JSON)."""
    k = len(chunks)
    texts = [s for s in sentences if re.search(r"[A-Za-z]", s.text)]  # marker-only pieces are not sentences
    result = Verification(ok=False, sentences=sentences, n_sentences=len(texts))
    result.n_valid_sentences = sum(bool(s.markers) and all(1 <= m <= k for m in s.markers) for s in texts)
    if not sentences:
        result.failed, result.detail = "empty", "no sentences"
        return result
    if len(sentences) > max_sentences:
        result.failed, result.detail = "too_long", f"{len(sentences)} sentences"
        return result
    for s in sentences:
        if not re.search(r"[A-Za-z]", s.text):
            result.failed, result.detail = "empty_sentence", "only markers"
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
        if not words or len(words & cited) / len(words) < min_overlap:
            result.failed, result.detail = "low_overlap", s.text[:60]
            return result
    result.ok = True
    return result


@dataclass
class Parsed:
    """A structured reply after parsing: no_answer flag and sentences, or a failure name and detail."""

    no_answer: bool = False
    sentences: list[Sentence] = field(default_factory=list)
    failed: str = ""
    detail: str = ""


def parse_structured(raw: str) -> Parsed:
    """Parse {"no_answer": bool, "sentences": [{"text": str, "sources": [int]}]}. Bad shape gives failed=bad_json."""
    try:
        data = json.loads(raw)
    except ValueError as error:
        return Parsed(failed="bad_json", detail=str(error)[:60])
    if not (isinstance(data, dict) and isinstance(data.get("no_answer"), bool)
            and isinstance(data.get("sentences"), list)):
        return Parsed(failed="bad_json", detail="wrong top-level shape")
    out: list[Sentence] = []
    for item in data["sentences"]:
        text, sources = (item.get("text"), item.get("sources")) if isinstance(item, dict) else (None, None)
        if not (isinstance(text, str) and isinstance(sources, list)
                and all(isinstance(m, int) and not isinstance(m, bool) for m in sources)):
            return Parsed(failed="bad_json", detail="sentence item has wrong shape")
        clean = re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", MARKER.sub("", text))).strip()
        out.append(Sentence(clean, list(sources)))
    return Parsed(no_answer=data["no_answer"], sentences=out)


def verify_structured(
    parsed: Parsed, chunks: list[Chunk], *, max_sentences: int, min_overlap: float,
) -> Verification:
    """Same rules as verify() on parsed JSON: valid source ids, no empty sources, banned words, overlap guard."""
    if parsed.failed:
        return Verification(ok=False, failed=parsed.failed, detail=parsed.detail)
    return _check(parsed.sentences, " ".join(s.text for s in parsed.sentences), chunks,
                  max_sentences=max_sentences, min_overlap=min_overlap)
