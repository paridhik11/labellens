"""Field mapping without slot positions, and post-correction by format.

``map_fields_by_layout`` names text lines from what they say and how they are
arranged (a printed key such as REF, LOT or EXP, an address pattern, the
largest line), not from where a template says a field should be. The rules
were written for device labels in general but were only ever tested on the
synthetic test-device family, so treat them as a first version.

Post-correction only applies rules that follow from a format: a known key is
followed by a colon and one space, and an ISO date contains digits. It never
copies a value from the barcode unless the printed and encoded values differ
only by characters OCR commonly confuses.
"""

from __future__ import annotations

import re

from src.common.schemas import OcrBlock

# Printed keys that introduce a value, per field. Longer keys are tried first.
KEYS: dict[str, tuple[str, ...]] = {
    "model": ("REF", "MODEL", "CAT"),
    "lot": ("LOT", "BATCH"),
    "expiry": ("EXP", "EXPIRY", "USE BY"),
    "serial": ("SN", "SERIAL"),
}
_KEY_TO_FIELD = {key: field for field, keys in KEYS.items() for key in keys}
_KEY_PATTERN = re.compile(r"^\s*([A-Za-z][A-Za-z ]{1,7}?)\s*[:;.,]\s*(\S.*)$")
_KEY_NO_SEPARATOR = re.compile(r"^\s*([A-Za-z]{2,6})\s+(\S.*)$")
_STREET_WORDS = r"(road|rd|street|st|avenue|ave|lane|ln|drive|dr|boulevard|blvd|way|park|plaza|square)"
_ADDRESS = re.compile(rf"^\d{{1,5}}\s*\S.*\b{_STREET_WORDS}\b", re.IGNORECASE)
_WATERMARK = re.compile(r"\b(draft|specimen|test data|sample|void)\b", re.IGNORECASE)
# Characters OCR confuses with digits. Used only where a digit is required.
CONFUSABLE_TO_DIGIT = str.maketrans(
    {"O": "0", "o": "0", "D": "0", "I": "1", "l": "1", "|": "1", "S": "5", "B": "8", "Z": "2"}
)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _edit_distance(first: str, second: str) -> int:
    """Count the minimum number of single-character edits between two strings."""
    previous = list(range(len(second) + 1))
    for row, expected in enumerate(first, start=1):
        current = [row]
        for column, actual in enumerate(second, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (expected != actual)))
        previous = current
    return previous[-1]


def split_key_value(text: str) -> tuple[str | None, str, str]:
    """Split "REF: X" into (field name, printed key, value).

    The key may be followed by a colon, semicolon, full stop or comma, with or
    without spaces. A key that is one edit away from a known key of at least
    three letters is accepted (for example REE for REF). Without a separator a
    key is only accepted when it matches a known key exactly. Returns
    (None, "", text) when no known key starts the line.
    """
    for pattern, exact_only in ((_KEY_PATTERN, False), (_KEY_NO_SEPARATOR, True)):
        match = pattern.match(text)
        if match is None:
            continue
        printed, value = match.group(1).strip(), match.group(2).strip()
        upper = printed.upper()
        if upper in _KEY_TO_FIELD:
            return _KEY_TO_FIELD[upper], upper, value
        if not exact_only:
            near = [key for key in _KEY_TO_FIELD if len(key) >= 3 and _edit_distance(upper, key) == 1]
            if len(near) == 1:
                return _KEY_TO_FIELD[near[0]], near[0], value
    return None, "", text


def normalise_field(field: str, text: str) -> str:
    """Apply format rules to one field reading and return the corrected text.

    All fields: surrounding whitespace removed and runs of spaces collapsed.
    Keyed fields (model, lot, expiry, serial): the key is written as
    "KEY: value" with exactly one space. Expiry: if replacing commonly confused
    letters by digits turns the value into an ISO date, that date is used.
    Nothing else is changed, so a wrong character in a name stays wrong.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    if field not in KEYS:
        return cleaned
    found, key, value = split_key_value(cleaned)
    if found != field:
        return cleaned
    if field == "expiry":
        digits = value.replace(" ", "").translate(CONFUSABLE_TO_DIGIT)
        if _ISO_DATE.match(digits):
            value = digits
    return f"{key}: {value}"


def strip_key(text: str) -> str:
    """Return the value of a keyed reading without its printed key ("REF: X" gives "X")."""
    _, _, value = split_key_value(text)
    return value.strip()


def map_fields_by_layout(
    blocks: list[OcrBlock], *, min_confidence: float = 0.5
) -> tuple[dict[str, str], list[str]]:
    """Name text lines from their content and arrangement, without slot positions.

    Lines below ``min_confidence`` or with fewer than two letters or digits are
    ignored (confidence filtering; this removes junk read from barcodes and
    pictograms). Rules, in order: a line that starts with a known key becomes
    that field; a line that starts with a number and contains a street word is
    the address; the nearest line directly above the address is the
    manufacturer; the remaining line with the widest characters is the product
    name, provided it is not a watermark such as DRAFT and is clearly larger
    than the other lines. Text is returned as read, keys included.
    """
    warnings = []
    usable = [
        block for block in blocks
        if block.conf >= min_confidence and sum(character.isalnum() for character in block.text) >= 2
    ]
    ignored = len(blocks) - len(usable)
    if ignored:
        warnings.append(f"OCR_BLOCKS_IGNORED: {ignored} low-confidence or empty text lines not used for fields")
    fields: dict[str, str] = {}
    used: set[int] = set()
    for field in KEYS:
        matches = [
            (block.conf, index) for index, block in enumerate(usable) if split_key_value(block.text)[0] == field
        ]
        if matches:
            _, index = max(matches)
            fields[field] = usable[index].text
            used.add(index)
            if len(matches) > 1:
                warnings.append(f"FIELD_AMBIGUOUS: {field} has {len(matches)} candidate lines; kept the most confident")
    addresses = [
        (block.conf, index) for index, block in enumerate(usable)
        if index not in used and _ADDRESS.match(block.text.strip())
    ]
    if addresses:
        _, address_index = max(addresses)
        address = usable[address_index]
        fields["manufacturer_address"] = address.text
        used.add(address_index)
        left, top, width, _ = address.bbox
        above = []
        for index, block in enumerate(usable):
            if index in used or _WATERMARK.search(block.text):
                continue
            x, y, w, h = block.bbox
            gap = top - (y + h)
            overlaps = min(x + w, left + width) - max(x, left) > 0
            if overlaps and -0.3 * h <= gap <= 2.5 * h:
                above.append((gap, index))
        if above:
            _, index = min(above)
            fields["manufacturer"] = usable[index].text
            used.add(index)
    # Width per character is a steadier font-size measure than box height, because box
    # height also depends on whether the line has descenders or lower-case letters.
    def glyph_width(block: OcrBlock) -> float:
        return block.bbox[2] / max(1, len(block.text))

    remaining = [
        (glyph_width(block), -block.bbox[1], index) for index, block in enumerate(usable)
        if index not in used and not _WATERMARK.search(block.text)
        and sum(character.isalnum() for character in block.text) >= 3
    ]
    if remaining:
        largest, _, index = max(remaining)
        # A product name is printed larger than body text. Without this check an ordinary
        # line is promoted to product name whenever the real one is unreadable.
        others = sorted(glyph_width(block) for position, block in enumerate(usable) if position != index)
        if not others or largest >= 1.15 * others[len(others) // 2]:
            fields["product_name"] = usable[index].text
    for field in ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry"):
        if field not in fields:
            warnings.append(f"FIELD_MISSING: {field}")
    return fields, warnings


def _canonical(value: str) -> str:
    """Reduce a value to a form in which commonly confused characters are equal."""
    return value.replace(" ", "").upper().translate(CONFUSABLE_TO_DIGIT)


def reconcile_with_barcode(fields: dict[str, str], parsed: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """Use the barcode to settle 0/O style doubts in the printed lot and expiry.

    If the printed value and the barcode value (AI 10 for lot, AI 17 for
    expiry) are equal once commonly confused characters and spaces are
    ignored, the printed reading is replaced by the barcode's spelling. If
    they differ in any other way nothing is changed, so a real mismatch
    between print and barcode stays visible for the checker.
    """
    result = dict(fields)
    notes = []
    targets = {}
    if "10" in parsed:
        targets["lot"] = parsed["10"]
    if "17" in parsed and len(parsed["17"]) == 6 and parsed["17"].isdigit():
        code = parsed["17"]
        targets["expiry"] = f"20{code[:2]}-{code[2:4]}-{code[4:]}"
    for field, expected in targets.items():
        if field not in result:
            continue
        found, key, value = split_key_value(result[field])
        if found != field or value == expected:
            continue
        if _canonical(value) == _canonical(expected):
            result[field] = f"{key}: {expected}"
            notes.append(f"FIELD_SNAPPED_TO_BARCODE: {field} differed only by commonly confused characters")
    return result, notes


def snap_to_vocabulary(text: str, vocabulary: list[str], max_relative_distance: float = 0.2) -> str:
    """Return the closest vocabulary entry if it is close enough, else the text unchanged.

    Distance is edit distance after removing spaces and upper-casing, divided
    by the length of the vocabulary entry. A snap needs a unique closest entry
    within ``max_relative_distance``. Use this only with a real list of
    allowed values, such as product names from the product database.
    """
    key = text.replace(" ", "").upper()
    scored = sorted(
        (_edit_distance(key, entry.replace(" ", "").upper()) / max(1, len(entry.replace(" ", ""))), entry)
        for entry in vocabulary
    )
    if not scored or scored[0][0] > max_relative_distance:
        return text
    if len(scored) > 1 and scored[1][0] == scored[0][0] and scored[1][1] != scored[0][1]:
        return text
    return scored[0][1]
