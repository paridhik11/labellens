"""Selection mode (docs: reports/rag_select_plan.md): the model only picks sentence numbers.

Retrieved chunks are split into numbered sentences. The model returns the numbers of the sentences that answer
the question. The answer is those exact sentences, so nothing the model writes is ever shown.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

from src.common.schemas import Chunk

MAX_CANDIDATES = 60
MAX_SELECTED = 3
MIN_WORDS = 5
LONG_WORDS = 60
ABBREVIATIONS = {"no", "nos", "u.s", "e.g", "i.e", "inc", "sec", "approx", "vs", "etc", "al", "fig", "ca", "co", "corp"}
_BOUNDARY = re.compile(r"(?<=[.!?;])\s+(?=[A-Z0-9(])")

SYSTEM_V4 = (
    "You answer questions about US drug and medical device labeling regulations (21 CFR). You are given numbered "
    "sentences taken from the regulations. Reply with a JSON object. Set no_answer to true and sentences to an "
    "empty list if none of the sentences answer the question. Otherwise set no_answer to false and list the "
    "numbers of the 1 to 3 sentences that best answer the question, most important first. Use only numbers that "
    "appear in the list. Do not write any other text."
)
USER_V4 = "Sentences:\n{context}\n\nQuestion: {question}"
SELECT_SCHEMA = {
    "type": "object",
    "properties": {"no_answer": {"type": "boolean"}, "sentences": {"type": "array", "items": {"type": "integer"}, "maxItems": 3}},
    "required": ["no_answer", "sentences"],
}


def prompt_hash() -> str:
    """Short hash of the selection prompt, recorded in the frozen config."""
    return hashlib.sha256((SYSTEM_V4 + USER_V4 + json.dumps(SELECT_SCHEMA, sort_keys=True)).encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Candidate:
    """One numbered sentence: its number (1 based), the chunk it came from (1 based rank) and its exact text."""

    num: int
    chunk_rank: int
    chunk_id: str
    section: str
    text: str


def _ends_with_abbreviation(piece: str) -> bool:
    last = piece.rstrip().split()[-1].lower().rstrip(".;!?") if piece.split() else ""
    return last in ABBREVIATIONS or (len(last) == 1 and last.isalpha() and piece.rstrip().endswith("."))


def _split_long(piece: str) -> list[str]:
    """Split a sentence longer than LONG_WORDS words after the ; or : closest to its middle, repeatedly."""
    words = piece.split()
    if len(words) <= LONG_WORDS:
        return [piece]
    marks = [m.end() for m in re.finditer(r"[;:](?=\s)", piece)]
    marks = [m for m in marks if MIN_WORDS <= len(piece[:m].split()) <= len(words) - MIN_WORDS]
    if not marks:
        return [piece]
    mid = len(piece) / 2
    cut = min(marks, key=lambda m: abs(m - mid))
    return _split_long(piece[:cut].strip()) + _split_long(piece[cut:].strip())


def split_sentences(text: str) -> list[str]:
    """Split chunk text into sentences. Every piece is an exact substring of the text (only stripped)."""
    raw = [p.strip() for p in _BOUNDARY.split(text.strip()) if p.strip()]
    merged: list[str] = []
    for piece in raw:
        if merged and (_ends_with_abbreviation(merged[-1]) or len(piece.split()) < MIN_WORDS
                       or len(merged[-1].split()) < MIN_WORDS):
            merged[-1] = f"{merged[-1]} {piece}"
        else:
            merged.append(piece)
    out: list[str] = []
    for piece in merged:
        out.extend(_split_long(piece))
    return out


def build_candidates(chunks: list[Chunk], limit: int = MAX_CANDIDATES) -> list[Candidate]:
    """Numbered sentences of the chunks in retrieval rank order, at most `limit`."""
    out: list[Candidate] = []
    for rank, chunk in enumerate(chunks, start=1):
        for sentence in split_sentences(chunk.text):
            if len(out) >= limit:
                return out
            out.append(Candidate(len(out) + 1, rank, chunk.chunk_id, chunk.section, sentence))
    return out


def build_user(question: str, candidates: list[Candidate]) -> str:
    """The user message: one numbered line per sentence with its section."""
    context = "\n".join(f"{c.num}. (21 CFR {c.section}) {c.text}" for c in candidates)
    return USER_V4.format(context=context, question=question)


@dataclass
class Selection:
    """Parsed and checked reply: chosen numbers in document order, or a failure name and detail."""

    no_answer: bool = False
    numbers: list[int] = field(default_factory=list)
    failed: str = ""
    detail: str = ""


def parse_selection(raw: str, n_candidates: int, max_selected: int = MAX_SELECTED) -> Selection:
    """Parse {"no_answer": bool, "sentences": [int]} and check it. Failures: bad_json, empty, too_many, id_invalid."""
    try:
        data = json.loads(raw)
    except ValueError as error:
        return Selection(failed="bad_json", detail=str(error)[:60])
    if not (isinstance(data, dict) and isinstance(data.get("no_answer"), bool)
            and isinstance(data.get("sentences"), list)
            and all(isinstance(n, int) and not isinstance(n, bool) for n in data["sentences"])):
        return Selection(failed="bad_json", detail="wrong shape")
    nums: list[int] = data["sentences"]
    if data["no_answer"]:
        return Selection(no_answer=True)
    if not nums:
        return Selection(failed="empty", detail="no numbers")
    if len(nums) > max_selected:
        return Selection(failed="too_many", detail=f"{len(nums)} numbers")
    if len(set(nums)) != len(nums):
        return Selection(failed="id_invalid", detail="repeated number")
    bad = [n for n in nums if not 1 <= n <= n_candidates]
    if bad:
        return Selection(failed="id_invalid", detail=f"number {bad[0]} of {n_candidates}")
    return Selection(numbers=sorted(nums))
