"""Which retrieved regulation passages apply to one product (display and AI context only, never scoring).

Some 21 CFR sections only govern a narrow product type, for example 801.435 (latex condoms). Retrieval may
rank them high for a general question such as "what must a label show for the expiration date?". For a
product whose record never mentions that type, the passage is dropped. Each section is also shown once,
because several chunks of one section otherwise look like separate sources.

The same table is used in the browser (ui/pro/pro.js PRODUCT_SPECIFIC) for per-field evidence.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any

from src.common.schemas import Chunk

# section -> pattern the product record must match for the section to apply
PRODUCT_SPECIFIC: dict[str, re.Pattern[str]] = {
    "801.435": re.compile(r"latex|condom", re.IGNORECASE),
}


def record_text(record: dict[str, Any] | None) -> str:
    """All string values of a product record (and its extra fields) joined into one text."""
    if not record:
        return ""
    parts: list[str] = []
    for value in record.values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            parts.extend(v for v in value.values() if isinstance(v, str))
    return " ".join(parts)


def applies(section: str, product_text: str) -> bool:
    """False when the section is product-specific and the product text does not match it."""
    pattern = PRODUCT_SPECIFIC.get(str(section))
    return pattern is None or bool(pattern.search(product_text))


def filter_chunks(chunks: Iterable[Chunk], product_text: str) -> list[Chunk]:
    """Drop sections that do not apply to the product and keep the first chunk of each section, in order."""
    seen: set[str] = set()
    out: list[Chunk] = []
    for chunk in chunks:
        section = str(chunk.section)
        if not applies(section, product_text) or section in seen:
            continue
        seen.add(section)
        out.append(chunk)
    return out


def chunk_filter(product_text: str) -> Callable[[list[Chunk]], list[Chunk]]:
    """A context filter for answer_question bound to one product's text."""
    return lambda chunks: filter_chunks(chunks, product_text)
