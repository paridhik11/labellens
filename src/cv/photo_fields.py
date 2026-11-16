"""Generic field rules for package photos, developed without scoring-set readings."""
from __future__ import annotations

import re
from datetime import date

from src.common.schemas import OcrBlock
from src.cv.fields import KEYS, map_fields_by_layout, split_key_value

_KEY = re.compile(r"^[\[({| ]*(LOT|BATCH|EXPIRY|EXP|USE BY|REF|MODEL|CAT|SN|SERIAL)[\])}| :;.,-]*(.*)$", re.I)
_DATE = re.compile(
    r"(?<!\d)(?:20\d{2}[-/.]\d{1,2}(?:[-/.]\d{1,2})?|"
    r"\d{1,2}[-/.](?:\d{1,2}[-/.])?(?:19|20|21)\d{2}|"
    r"(?:JAN|FEB|MAR|APR|ABR|MAY|MAI|JUN|JUL|AUG|AGO|AGOS|SEP|SEPT|OCT|NOV|DEC|DIC)[ -]+20\d{2})(?!\d)", re.I)
_NOISE = re.compile(
    r"\b(?:STERILE|STERILIZED|LATEX|CAUTION|WARNING|SINGLE USE|DO NOT|USE BY|"
    r"MADE IN|MANUFACTURED|DISTRIBUTED|COPYRIGHT|CE|UDI|GTIN|CONTENTS|QTY|QUANTITY|"
    r"NON ABSORBABLE|ABSORBABLE|POLYPROPYLENE|POLYESTER|RX ONLY)\b", re.I)
_UNITS = re.compile(r"^\s*[\d., /xX-]+\s*(?:mm|cm|ml|mg|g|fr|ga|gauge|inch|in|%)\b", re.I)


def visible_date(text: str) -> str | None:
    """Return a single valid printed date substring without reformatting its characters."""
    if re.search(r"\b(?:MFG|MFD|DOM|MANUFACTURED|COPYRIGHT)\b", text, re.I):
        return None
    matches = list(_DATE.finditer(text))
    if len(matches) != 1:
        return None
    value = matches[0].group()
    numbers = re.findall(r"\d+", value)
    try:
        if re.match(r"^[A-Za-z]", value):
            year, month, day = int(numbers[0]), 1, 1
        elif len(numbers[0]) == 4:
            year, month = int(numbers[0]), int(numbers[1])
            day = int(numbers[2]) if len(numbers) > 2 else 1
        else:
            year = int(numbers[-1])
            if len(numbers) == 2:
                month, day = int(numbers[0]), 1
            elif int(numbers[1]) > 12 >= int(numbers[0]):
                month, day = int(numbers[0]), int(numbers[1])
            else:
                day, month = int(numbers[0]), int(numbers[1])
        date(year, month, day)
    except (ValueError, IndexError):
        return None
    return value


def field_key(text: str) -> tuple[str | None, str]:
    """Recognize boxed or attached keys; attached values must contain a digit."""
    standard, _, value = split_key_value(text)
    if standard:
        return standard, value
    match = _KEY.match(text.strip())
    if match is None:
        return None, text
    key, value = match[1].upper(), match[2].strip()
    key_end = text.upper().find(key) + len(key)
    if value and key_end < len(text) and text[key_end].isalpha() and not any(c.isdigit() for c in value):
        return None, text
    field = next((name for name, keys in KEYS.items() if key in keys), None)
    return field, value


def map_photo_fields(blocks: list[OcrBlock], *, min_confidence: float = 0.5) -> tuple[dict[str, str], list[str]]:
    """Use explicit/split keys, unambiguous dates and typography without fixed slots.

    Conflicting visible values stay absent with a warning. Bare dates are only
    used when exactly one date is visible. Product names are observed text, not
    inferred from a product catalog. Original spelling is retained.
    """
    usable = [b for b in blocks if b.conf >= min_confidence and b.text.strip()]
    fields, warnings = map_fields_by_layout(usable, min_confidence=min_confidence)
    candidates: dict[str, list[tuple[str, int]]] = {field: [] for field in KEYS}
    used = set()
    for index, block in enumerate(usable):
        field, value = field_key(block.text)
        if field is None:
            continue
        used.add(index)
        if value:
            candidates[field].append((value, index))
            continue
        x, y, w, h = block.bbox
        nearby = []
        for other_index, other in enumerate(usable):
            if other_index == index or field_key(other.text)[0] is not None:
                continue
            if not any(c.isdigit() for c in other.text) or _NOISE.search(other.text):
                continue
            if field != "expiry" and visible_date(other.text):
                continue
            ox, oy, ow, oh = other.bbox
            dy = abs(oy + oh / 2 - y - h / 2)
            right = ox >= x + w - 0.25 * h and dy <= 0.75 * max(h, oh) and ox - x - w <= 6 * h
            below = 0 <= oy - y - h <= 1.5 * h and min(x + w, ox + ow) > max(x, ox)
            if right or below:
                distance = max(0, ox - x - w) / max(1, h) + dy / max(1, h)
                nearby.append((distance, other_index))
        if nearby:
            nearby.sort()
            if len(nearby) == 1 or nearby[1][0] - nearby[0][0] > 0.5:
                other_index = nearby[0][1]
                candidates[field].append((usable[other_index].text.strip(), other_index))
    for field, values in candidates.items():
        if values:
            distinct = {value for value, _ in values}
            if len(distinct) == 1:
                fields[field] = f"{KEYS[field][0]}: {next(iter(distinct))}"
                used.update(index for _, index in values)
            else:
                fields.pop(field, None)
                warnings.append(f"FIELD_AMBIGUOUS: {field} has conflicting photo readings")
    if not candidates["expiry"]:
        dates = [(visible_date(b.text), index) for index, b in enumerate(usable)]
        dates = [(value, index) for value, index in dates if value]
        if len({value for value, _ in dates}) == 1:
            fields["expiry"] = f"EXP: {dates[0][0]}"
            used.update(index for _, index in dates)
        elif dates:
            fields.pop("expiry", None)
            warnings.append("FIELD_AMBIGUOUS: multiple unkeyed dates; expiry not selected")
    remaining = []
    for index, block in enumerate(usable):
        text = block.text.strip()
        if (index in used or _NOISE.search(text) or _UNITS.search(text) or visible_date(text)
                or field_key(text)[0] is not None or text == fields.get("manufacturer_address")
                or text == fields.get("manufacturer") or re.search(r"\b(?:DRAFT|TEST DATA)\b", text, re.I)):
            continue
        letters = sum(c.isalpha() for c in text)
        if letters < 4 or letters / max(1, len(text)) < 0.4:
            continue
        _, y, width, height = block.bbox
        size = (width / max(1, len(text)) * height) ** 0.5
        remaining.append((size, -y, text))
    if remaining:
        remaining.sort(reverse=True)
        if len(remaining) == 1 or remaining[0][0] >= 1.15 * remaining[1][0]:
            fields["product_name"] = remaining[0][2]
        elif "product_name" in fields and _NOISE.search(fields["product_name"]):
            fields.pop("product_name")
            warnings.append("FIELD_AMBIGUOUS: product-name typography is not distinctive")
    else:
        fields.pop("product_name", None)
    warnings = [w for w in warnings if not (w.startswith("FIELD_MISSING: ") and w.split(": ", 1)[1] in fields)]
    for field in ("product_name", "lot", "expiry"):
        if field not in fields:
            warnings.append(f"FIELD_MISSING: {field}")
    return fields, list(dict.fromkeys(warnings))
