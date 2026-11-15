"""Checks on one extraction that need no product database, returned as shared ``Flag`` objects.

Three things are checked: an expected pictogram is missing, the barcode could
not be read, and the printed lot or expiry disagrees with the barcode.
Characters that OCR commonly confuses (0 and O, 1 and I, 5 and S, 8 and B) are
treated as equal, so a real misprint of exactly that kind cannot be noticed.

A disagreement is only called a ``barcode_mismatch`` when the printed reading
is well formed and the OCR reading of that field is confident. A reading that
has lost its printed key (LOT or EXP), a lot with characters a lot cannot
have, or an expiry that is not a valid calendar date is a damaged reading, not
evidence about the print, so it gives ``needs_human_review`` whatever the OCR
confidence. The same flag is used when the reading is uncertain (confidence
below ``min_ocr_confidence``, or no OCR line can be matched to the field): the print may be fine and the OCR wrong,
so a person should compare the label with the barcode. Every flag asks for
human review; nothing here decides compliance.
"""

from __future__ import annotations

import re
from datetime import date

from src.common.schemas import Flag, LabelExtraction
from src.cv.fields import _canonical, normalise_field, split_key_value

EXPECTED_SYMBOLS = ("manufacturer", "expiry")
# Same value as the extractor's LOW_OCR_CONFIDENCE warning threshold (``min_confidence``).
# Chosen before measuring, not tuned on any seed.
DEFAULT_MIN_OCR_CONFIDENCE = 0.8


def field_confidence(extraction: LabelExtraction, field: str) -> float | None:
    """Return the OCR confidence of the line that produced ``extraction.fields[field]``.

    The field text may have been post-corrected (spacing, key format), so a
    line matches when its text equals the field text after collapsing spaces
    or after the same format normalisation. Returns the highest matching
    confidence, or None when the field is absent or no line matches.
    """
    text = extraction.fields.get(field)
    if text is None:
        return None
    target = re.sub(r"\s+", " ", text).strip()
    matches = [
        block.conf for block in extraction.ocr_blocks
        if re.sub(r"\s+", " ", block.text).strip() == target or normalise_field(field, block.text) == target
    ]
    return max(matches) if matches else None


_LOT_VALUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,19}")
_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


def format_problem(field: str, text: str) -> str | None:
    """Describe why a printed lot or expiry reading is malformed, or return None when it is well formed.

    Well formed means: the printed key (LOT or EXP) is present, a lot is 1 to 20 letters, digits or ``._/-``,
    and an expiry is an ISO date (YYYY-MM-DD) that exists in the calendar.
    """
    found, key, value = split_key_value(text)
    wanted = {"lot": "LOT", "expiry": "EXP"}[field]
    if found != field or key != wanted:
        return f"the printed key {wanted} is missing or unreadable"
    value = value.strip()
    if field == "lot":
        return None if _LOT_VALUE.fullmatch(value) else "the lot has characters a lot cannot have"
    match = _ISO_DATE.fullmatch(value)
    if match is None:
        return "the expiry is not written as YYYY-MM-DD"
    try:
        date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return "the expiry is not a valid calendar date"
    return None


def check_extraction(
    extraction: LabelExtraction,
    expected_symbols: tuple[str, ...] = EXPECTED_SYMBOLS,
    min_ocr_confidence: float = DEFAULT_MIN_OCR_CONFIDENCE,
    check_format: bool = True,
) -> list[Flag]:
    """Return review flags for missing symbols, an unreadable barcode and print/barcode disagreements.

    ``check_format=False`` switches off the malformed-reading rule, which reproduces the earlier behaviour
    (only OCR confidence separated a mismatch from a review request); it exists to compare the two on the same OCR.
    """
    flags = []
    found = {symbol.name for symbol in extraction.symbols}
    for name in expected_symbols:
        if name not in found:
            flags.append(Flag(
                flag_id=f"{extraction.label_id}:missing_symbol:{name}",
                kind="missing_symbol",
                severity="review",
                message=f"Expected symbol '{name}' was not detected",
                expected=name,
                confidence=0.0,
            ))
    if len(extraction.barcodes) != 1 or not extraction.barcodes[0].parsed:
        flags.append(Flag(
            flag_id=f"{extraction.label_id}:barcode_unreadable",
            kind="barcode_unreadable",
            severity="review",
            message=f"Expected one GS1 barcode, decoded {len(extraction.barcodes)}",
            observed=str(len(extraction.barcodes)),
            expected="1",
        ))
        return flags
    parsed = extraction.barcodes[0].parsed
    targets = {}
    if "10" in parsed:
        targets["lot"] = parsed["10"]
    if "17" in parsed and len(parsed["17"]) == 6 and parsed["17"].isdigit():
        code = parsed["17"]
        targets["expiry"] = f"20{code[:2]}-{code[2:4]}-{code[4:]}"
    for field, expected in targets.items():
        if field not in extraction.fields:
            continue
        _, _, value = split_key_value(extraction.fields[field])
        if _canonical(value) == _canonical(expected):
            continue
        confidence = field_confidence(extraction, field)
        problem = format_problem(field, extraction.fields[field]) if check_format else None
        if problem is not None or confidence is None or confidence < min_ocr_confidence:
            shown = "unknown" if confidence is None else f"{confidence:.2f}"
            reason = (
                f"the reading is damaged ({problem})" if problem is not None
                else f"the OCR reading is uncertain (confidence {shown})"
            )
            flags.append(Flag(
                flag_id=f"{extraction.label_id}:needs_human_review:{field}",
                kind="needs_human_review",
                severity="review",
                message=(
                    f"Printed {field} differs from the barcode, but {reason}; "
                    "compare the label with the barcode by eye"
                ),
                observed=value,
                expected=expected,
                confidence=0.0 if confidence is None else confidence,
                needs_human=True,
            ))
        else:
            flags.append(Flag(
                flag_id=f"{extraction.label_id}:barcode_mismatch:{field}",
                kind="barcode_mismatch",
                severity="critical",
                message=f"Printed {field} differs from the barcode",
                observed=value,
                expected=expected,
                confidence=confidence,
            ))
    return flags
