"""Light query rewriting for questions about one selected medicine.

Two rules, both plain string work (no model):
1. "it", "its" and "this" refer to the selected medicine, so they are replaced by its name before retrieval.
2. A storage-type question ("store", "storage", "keep") gets the wording labels use for that section appended.

The rewritten text is only used for retrieval. The question shown to the person is never changed.
"""
from __future__ import annotations

import re

STORAGE_WORDS = re.compile(r"\b(stor(e|es|ed|ing|age)|keep|kept|refrigerat\w*|fridge)\b", re.IGNORECASE)
STORAGE_EXPANSION = "storage and handling, how supplied, store at"
_PRONOUN = re.compile(r"\b(its|it|this)\b", re.IGNORECASE)


def short_name(full_name: str) -> str:
    """First product name of a label title such as "Metoprolol Tartrate / Lopressor" (empty when none)."""
    return full_name.split(" / ")[0].strip()


def resolve_pronouns(question: str, name: str) -> str:
    """Replace it/its/this by the medicine name ("how to store it" -> "how to store metoprolol")."""
    name = short_name(name)
    if not name:
        return question

    def swap(match: re.Match[str]) -> str:
        return f"{name}'s" if match.group(1).lower() == "its" else name

    return _PRONOUN.sub(swap, question)


def expand_storage(question: str) -> str:
    """Append the storage section wording to a storage-type question, leave any other question unchanged."""
    if STORAGE_WORDS.search(question) and STORAGE_EXPANSION not in question:
        return f"{question.rstrip()} {STORAGE_EXPANSION}"
    return question


def rewrite_for_retrieval(question: str, medicine_name: str) -> str:
    """Pronouns first, then storage expansion."""
    return expand_storage(resolve_pronouns(question, medicine_name))
