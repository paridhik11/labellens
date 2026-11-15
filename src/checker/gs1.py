"""Small GS1 parser for the four AIs used on test labels (01, 17, 10, 21).

Kept separate from ``src.cv.barcode`` because that module imports cv2 and zxingcpp,
which the CI image does not install. ``tests/test_checker_gs1.py`` compares the two
when the CV libraries are present.
"""
from __future__ import annotations

import string
from datetime import date

GROUP_SEPARATOR = "\x1d"
VARIABLE_CHARACTERS = frozenset(string.ascii_letters + string.digits + "!\"%&'()*+,-./:;<=>?_")


def check_digit_ok(gtin14: str) -> bool:
    """True when a 14-digit GTIN passes the GS1 mod 10 check (weights 3,1,3,1 from the right, check digit last)."""
    if len(gtin14) != 14 or not gtin14.isascii() or not gtin14.isdigit():
        return False
    weighted = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(reversed(gtin14)))
    return weighted % 10 == 0


def _validate(ai: str, value: str) -> None:
    if ai in {"01", "17"}:
        length = 14 if ai == "01" else 6
        if len(value) != length or not value.isascii() or not value.isdigit():
            raise ValueError(f"AI {ai} requires exactly {length} ASCII digits")
        if ai == "01":
            if not check_digit_ok(value):
                raise ValueError("AI 01 has an invalid check digit")
        else:
            try:
                date(2000 + int(value[:2]), int(value[2:4]), int(value[4:]))
            except ValueError as error:
                raise ValueError("AI 17 requires a real YYMMDD date with a specific day") from error
    elif not 1 <= len(value) <= 20 or any(c not in VARIABLE_CHARACTERS for c in value):
        raise ValueError(f"AI {ai} requires 1 to 20 GS1 character-set-82 characters")


def parse_gs1(payload: str) -> dict[str, str]:
    """Parse raw GS1 element data for AIs 01, 17, 10 and 21, or raise ValueError (never guesses)."""
    if not isinstance(payload, str) or not payload:
        raise ValueError("GS1 payload must be a nonempty string")
    fields: dict[str, str] = {}
    offset = 0
    while offset < len(payload):
        ai = payload[offset:offset + 2]
        if ai not in {"01", "17", "10", "21"}:
            raise ValueError(f"Unsupported AI or misplaced separator at offset {offset}")
        if ai in fields:
            raise ValueError(f"Duplicate AI {ai}")
        offset += 2
        if ai in {"01", "17"}:
            end = offset + (14 if ai == "01" else 6)
        else:
            separator = payload.find(GROUP_SEPARATOR, offset)
            end = len(payload) if separator == -1 else separator
        value = payload[offset:end]
        _validate(ai, value)
        fields[ai] = value
        offset = end
        if offset < len(payload) and payload[offset] == GROUP_SEPARATOR:
            offset += 1
    return fields
