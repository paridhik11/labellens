"""NDC parsing: printed NDC strings and barcode payloads to normalised 11-digit codes. Exact lookup only.

An NDC has 10 digits on the pack in one of three hyphen layouts (4-4-2, 5-3-2, 5-4-1) and 11 digits (5-4-2) in
billing systems. To normalise 10 to 11 digits a zero is added to the short segment: 4-4-2 -> 0 + labeler,
5-3-2 -> 0 + product, 5-4-1 -> 0 + package. Without hyphens a 10-digit string is ambiguous, so all three
readings are returned and each is looked up exactly (no fuzzy matching anywhere).
"""

from __future__ import annotations

import re
from typing import Iterable

# One NDC: segments joined by a hyphen-like mark or a space (OCR often turns a hyphen into a dash or a space).
SEP = r"[\-‐-―−\s.]{1,3}"
PRINTED = re.compile(
    rf"(?<!\d)(?:(\d{{4}}){SEP}(\d{{4}}){SEP}(\d{{2}})|(\d{{5}}){SEP}(\d{{3}}){SEP}(\d{{2}})"
    rf"|(\d{{5}}){SEP}(\d{{4}}){SEP}(\d{{1}}))(?!\d)")
ELEVEN = re.compile(r"(?<!\d)(\d{11})(?!\d)")
TEN = re.compile(r"(?<!\d)(\d{10})(?!\d)")


def from_segments(a: str, b: str, c: str) -> str | None:
    """Normalise segments of lengths 4-4-2, 5-3-2, 5-4-1 (or 5-4-2) to 11 digits, else None."""
    shape = (len(a), len(b), len(c))
    if shape == (4, 4, 2):
        return "0" + a + b + c
    if shape == (5, 3, 2):
        return a + "0" + b + c
    if shape == (5, 4, 1):
        return a + b + "0" + c
    if shape == (5, 4, 2):
        return a + b + c
    return None


def ten_digit_readings(digits: str) -> list[str]:
    """The three 11-digit readings of an unhyphenated 10-digit NDC (4-4-2, 5-3-2, 5-4-1)."""
    readings = [from_segments(digits[:4], digits[4:8], digits[8:]),
                from_segments(digits[:5], digits[5:8], digits[8:]),
                from_segments(digits[:5], digits[5:9], digits[9:])]
    return [r for r in readings if r]


def printed_ndcs(text: str) -> list[str]:
    """Every 11-digit NDC reading found in OCR text (hyphenated layouts, bare 11 digits, bare 10 digits)."""
    found: list[str] = []
    for m in PRINTED.finditer(text):
        groups = m.groups()
        for i in range(0, 9, 3):
            if groups[i]:
                code = from_segments(*groups[i:i + 3])
                if code:
                    found.append(code)
    for m in ELEVEN.finditer(text):
        found.append(m.group(1))
    for m in TEN.finditer(text):
        found.extend(ten_digit_readings(m.group(1)))
    return list(dict.fromkeys(found))


def check_digit_ok(digits: str) -> bool:
    """UPC-A / EAN-13 / GTIN-14 check digit (mod 10, weights 3 and 1 from the right)."""
    if not digits.isdigit() or len(digits) < 8:
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def barcode_ndcs(payload: str) -> list[str]:
    """NDC readings inside one decoded barcode: UPC-A "3" + NDC10 + check, EAN-13 "03" + NDC10 + check, GTIN-14
    (GS1 AI 01) with the "03" product prefix. The check digit must be valid, otherwise no reading is returned."""
    text = payload.strip()
    for prefix in ("]d2", "]C1", "]E0", "]d1"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    text = text.replace("(01)", "01", 1) if text.startswith("(01)") else text
    digits = re.sub(r"\D", "", text)
    if not digits:
        return []
    ten = ""
    whole = ""
    if len(digits) == 12 and digits.startswith("3"):
        ten, whole = digits[1:11], digits
    elif len(digits) == 13 and digits.startswith("03"):
        ten, whole = digits[2:12], digits
    elif len(digits) == 14 and digits[1:3] == "03":
        ten, whole = digits[3:13], digits
    elif len(digits) >= 16 and digits.startswith("01") and digits[3:5] == "03":
        gtin = digits[2:16]
        ten, whole = gtin[3:13], gtin
    if not ten or not check_digit_ok(whole):
        return []
    return ten_digit_readings(ten)


def lookup(codes: Iterable[str], table: dict[str, list[str]]) -> dict[str, list[str]]:
    """Exact lookup: ``{ndc11: [product ids]}`` for every code present in the table."""
    return {c: table[c] for c in dict.fromkeys(codes) if c in table}
