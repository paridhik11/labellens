"""Prompt text and numbered context. The model sees passage numbers, never chunk ids."""
from __future__ import annotations

import hashlib

from src.common.schemas import Chunk

SYSTEM_V1 = (
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
USER_TEMPLATE_V1 = "Passages:\n{context}\n\nQuestion: {question}\n\nAnswer:"
# v2 (post hoc, after the frozen v1 run returned only bare markers such as "[1][3]"): a worked format example
# and a reminder at the end of the user message.
SYSTEM_V2 = (
    "You answer questions about US drug and medical device labeling regulations (21 CFR) using ONLY the "
    "numbered passages you are given.\n"
    "The passages are called Passage 1, Passage 2 and so on. Write 1 to 3 plain English sentences in your own "
    "words. At the END of each sentence put the number of the supporting passage in square brackets.\n"
    "Format only, not content: First sentence of the answer [1]. Second sentence of the answer [2][3].\n"
    "Every sentence needs its own number. Keep the answer under 60 words.\n"
    "Rules: use only facts stated in the passages. Never reply with only numbers. Never say a label or product "
    "complies, is compliant or approved. Never give medical advice. If the passages do not answer the "
    "question, reply with exactly: NO_ANSWER"
)
USER_TEMPLATE_V2 = (
    "Passages:\n{context}\n\nQuestion: {question}\n\n"
    "Write 1 to 3 sentences, each ending with a passage number like [1]. If the passages do not answer, write "
    "NO_ANSWER.\n\nAnswer:"
)
# v3 (Step 23e): the answer is a JSON object enforced by the server (Ollama structured outputs), so there is
# no marker format to get wrong. The numbers in "sources" are passage numbers.
SYSTEM_V3 = (
    "You answer questions about US drug and medical device labeling regulations (21 CFR) using ONLY the "
    "numbered passages you are given. Reply with a JSON object.\n"
    "Set no_answer to true and sentences to an empty list if the passages do not answer the question.\n"
    "Otherwise set no_answer to false and write 1 to 3 plain English sentences in sentences. Each item has "
    "text (one sentence, no passage numbers inside it) and sources (the numbers of the passages that support "
    "that sentence, at least one).\n"
    "Rules: use only facts stated in the passages. Never say a label or product complies, is compliant or "
    "approved. Never give medical advice."
)
USER_TEMPLATE_V3 = "Passages:\n{context}\n\nQuestion: {question}"
PROMPTS = {"v1": (SYSTEM_V1, USER_TEMPLATE_V1), "v2": (SYSTEM_V2, USER_TEMPLATE_V2),
           "v3": (SYSTEM_V3, USER_TEMPLATE_V3)}
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "no_answer": {"type": "boolean"},
        "sentences": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "sources": {"type": "array", "items": {"type": "integer"}}},
            "required": ["text", "sources"]}},
    },
    "required": ["no_answer", "sentences"],
}
SYSTEM, USER_TEMPLATE = PROMPTS["v1"]  # the frozen Step 23 run used v1


def prompt_version(name: str) -> str:
    """Short hash of a prompt version, recorded in reports."""
    return hashlib.sha256("".join(PROMPTS[name]).encode()).hexdigest()[:12]


PROMPT_VERSION = prompt_version("v1")  # same value as before (hash of system + user template)


def build_context(chunks: list[Chunk], version: str = "v1") -> str:
    """One line per passage. v1: [n] 21 CFR ...; v2: Passage n: 21 CFR ... (the model must not copy a leading [n])."""
    label = "Passage {n}:" if version in ("v2", "v3") else "[{n}]"
    lines = (f"{label.format(n=n)} 21 CFR {c.section} {c.title}: {c.text}" for n, c in enumerate(chunks, start=1))
    return "\n".join(lines)


def build_user(question: str, chunks: list[Chunk], version: str = "v1") -> str:
    """The user message for one question and its retrieved chunks."""
    return PROMPTS[version][1].format(context=build_context(chunks, version), question=question)
