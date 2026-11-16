"""Scope rule: personal medical advice and out-of-module questions are not answered.

Written from the contract's definition of out_of_scope before any evaluation query was scored. It does not
list other jurisdictions or topics, because that would fit the no_answer queries; those must be caught by
the score gate or they count as failures.
"""
from __future__ import annotations

import re

ADVICE_PATTERNS = tuple(re.compile(p, re.I) for p in (
    r"\b(should|can|could|may|must|do) (i|we|my \w+|he|she|they)\b[^?.]*\b(take|give|use|stop|skip|double|mix|drink|combine|crush|split)\b",  # noqa: E501
    r"\bhow (much|many)\b[^?.]*\b(should i|can i|do i|should (he|she|they)|to take|to give)\b",
    r"\b(dose|dosage|dosing)\b[^?.]*\b(for (me|my|a child|my child|an adult|a baby|a toddler)|should i)\b",
    r"\b(is it|are they|is this) safe (for me|to take|while|during|if i|for my|for a)\b",
    r"\bdiagnos(e|is|ing)\b",
    r"\b(do i have|what is wrong with me|what's wrong with me|my symptoms?|treat my)\b",
    r"\b(interact|interacts|interaction|mix|mixing)\b[^?.]*\b(with (alcohol|my|other medic|food|grapefruit))\b",
    r"\b(i am|i'm|i was|my (child|baby|mother|father|wife|husband|son|daughter)( is| was)?) (pregnant|taking|on|allergic|diabetic|breastfeeding|nursing)\b",  # noqa: E501
    r"\b(missed a dose|overdose|overdosed)\b",
))
DEVICE_PATTERNS = tuple(re.compile(p, re.I) for p in (
    r"\bmedical devices?\b", r"\bunique device identifier\b", r"\bUDI\b", r"\bGUDID\b", r"\b510\(k\)", r"\bPMA\b",
))


def out_of_scope(question: str, module: str) -> str | None:
    """A short reason when the question is out of scope, else None. Public (medicine) also rejects device questions."""
    for pattern in ADVICE_PATTERNS:
        if pattern.search(question):
            return "personal medical advice"
    if module == "medicine":
        for pattern in DEVICE_PATTERNS:
            if pattern.search(question):
                return "device regulation, outside 21 CFR 201, 208 and 211"
    return None
