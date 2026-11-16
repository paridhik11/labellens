"""Prompt text and numbered context. The model sees passage numbers, never chunk ids."""
from __future__ import annotations

import hashlib

from src.common.schemas import Chunk

SYSTEM = (
    "You answer questions about US drug and medical device labeling regulations (21 CFR) using ONLY the "
    "numbered passages you are given.\n"
    "Rules:\n"
    "1. Write at most 4 short sentences.\n"
    "2. Every sentence must end with the number of the passage that supports it, like [2]. "
    "Use several like [1][3] if needed.\n"
    "3. Use only facts stated in the passages. Add no outside knowledge.\n"
    "4. Never say a label or product complies, is compliant or approved. Never give medical advice.\n"
    "5. If the passages do not answer the question, reply with exactly: NO_ANSWER"
)
USER_TEMPLATE = "Passages:\n{context}\n\nQuestion: {question}\n\nAnswer:"
PROMPT_VERSION = hashlib.sha256((SYSTEM + USER_TEMPLATE).encode()).hexdigest()[:12]


def build_context(chunks: list[Chunk]) -> str:
    """One line per passage: [n] 21 CFR <section> <title>: <text>."""
    return "\n".join(f"[{n}] 21 CFR {c.section} {c.title}: {c.text}" for n, c in enumerate(chunks, start=1))


def build_user(question: str, chunks: list[Chunk]) -> str:
    """The user message for one question and its retrieved chunks."""
    return USER_TEMPLATE.format(context=build_context(chunks), question=question)
