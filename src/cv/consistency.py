"""Checks on one extraction that need no product database, returned as shared ``Flag`` objects.

Three things are checked: an expected pictogram is missing, the barcode could
not be read, and the printed lot or expiry disagrees with the barcode.
Characters that OCR commonly confuses (0 and O, 1 and I, 5 and S, 8 and B) are
treated as equal, so a real misprint of exactly that kind cannot be noticed.
Every flag asks for human review; nothing here decides compliance.
"""

from __future__ import annotations

from src.common.schemas import Flag, LabelExtraction
from src.cv.fields import _canonical, split_key_value

EXPECTED_SYMBOLS = ("manufacturer", "expiry")


def check_extraction(
    extraction: LabelExtraction, expected_symbols: tuple[str, ...] = EXPECTED_SYMBOLS
) -> list[Flag]:
    """Return review flags for missing symbols, an unreadable barcode and print/barcode mismatches."""
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
        if _canonical(value) != _canonical(expected):
            flags.append(Flag(
                flag_id=f"{extraction.label_id}:barcode_mismatch:{field}",
                kind="barcode_mismatch",
                severity="critical",
                message=f"Printed {field} differs from the barcode",
                observed=value,
                expected=expected,
            ))
    return flags
