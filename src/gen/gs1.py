"""Validate, serialize and render the GS1 fields used by device labels."""

from __future__ import annotations

import calendar
import re
import string
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Mapping

import numpy as np
import zxingcpp

from src.common.schemas import IdentifierRequired

# GS1 General Specifications 26.0: sections 3.2, 7.8 (separators),
# 7.9 (check digits), 7.11 (character set 82), and 7.12 (date century).
# https://ref.gs1.org/standards/genspecs/26.0.0/
GROUP_SEPARATOR = "\x1d"
VARIABLE_CHARACTERS = frozenset(
    string.ascii_letters + string.digits + "!\"%&'()*+,-./:;<=>?_"
)
AI_ORDER = ("01", "17", "10", "21")
FIXED_LENGTHS = {"01": 14, "17": 6}
REQUIRED_AIS = ("01", "17", "10")
_HRI_PATTERN = re.compile(r"(?<!\\)\(([0-9]{2,4})\)")


class GS1Symbology(StrEnum):
    """Barcode format names supported by the template contract."""

    DATA_MATRIX = "GS1_DataMatrix"
    CODE_128 = "GS1-128"


class BarcodeAction(StrEnum):
    """Safe action choices for a changed label barcode."""

    KEEP = "KEEP"
    REGENERATE = "REGENERATE"
    NEEDS_INPUT = "NEEDS_INPUT"


@dataclass(frozen=True)
class BarcodeDecisionResult:
    """Decision and human-readable reason returned by the barcode policy."""

    action: BarcodeAction
    reason: str


@dataclass(frozen=True)
class EncodedBarcode:
    """GS1 barcode artwork together with its validated payload."""

    symbology: GS1Symbology
    elements: dict[str, str]
    hri: str
    image: np.ndarray
    svg: str


def validate_gtin(value: str) -> None:
    """Require a 14-digit GTIN with a valid GS1 Mod-10 check digit.

    This validates syntax only. It does not allocate or prove ownership of an
    identifier; the all-zero placeholder is valid only for explicit test data.
    """
    if not isinstance(value, str) or len(value) != 14 or not value.isascii() or not value.isdigit():
        raise ValueError("AI 01 requires exactly 14 ASCII digits")
    weighted_sum = sum(
        int(digit) * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(value[0:13]))
    )
    expected = (-weighted_sum) % 10
    if int(value[-1]) != expected:
        raise ValueError("AI 01 has an invalid check digit")


def validate_expiry(
    value: str, *, healthcare: bool = True, reference_date: date | None = None
) -> date:
    """Validate AI 17 YYMMDD, returning the interpreted calendar date.

    Healthcare expiry dates must use a real day, per GS1 General
    Specifications 26.0 section 3.4.7. Outside healthcare, day 00 denotes
    the final day of that month.
    """
    if not isinstance(value, str) or len(value) != 6 or not value.isascii() or not value.isdigit():
        raise ValueError("AI 17 requires exactly six ASCII digits in YYMMDD form")
    # GS1 section 7.12: 49 years in the past through 50 in the future.
    reference_year = (reference_date or date.today()).year
    first_year = reference_year - 49
    year = first_year + (int(value[:2]) - first_year) % 100
    month, day = int(value[2:4]), int(value[4:])
    if day == 0 and healthcare:
        raise ValueError("AI 17 day 00 is not permitted for regulated healthcare products")
    if day == 0:
        if not 1 <= month <= 12:
            raise ValueError("AI 17 must contain a valid month")
        return date(year, month, calendar.monthrange(year, month)[1])
    try:
        return date(year, month, day)
    except ValueError as error:
        raise ValueError("AI 17 must be a valid calendar date") from error


def validate_elements(
    elements: Mapping[str, str], *, healthcare: bool = True
) -> dict[str, str]:
    """Validate supported GS1 fields and return them in canonical AI order."""
    if not isinstance(elements, Mapping):
        raise ValueError("GS1 elements must be a mapping of AI strings to values")
    unsupported = set(elements) - set(AI_ORDER)
    if unsupported:
        raise ValueError(f"Unsupported GS1 AIs: {', '.join(sorted(map(str, unsupported)))}")
    normalized: dict[str, str] = {}
    for ai in AI_ORDER:
        if ai not in elements:
            continue
        value = elements[ai]
        if not isinstance(value, str):
            raise ValueError(f"AI {ai} value must be a string")
        if ai == "01":
            validate_gtin(value)
        elif ai == "17":
            validate_expiry(value, healthcare=healthcare)
        elif not 1 <= len(value) <= 20 or any(char not in VARIABLE_CHARACTERS for char in value):
            raise ValueError(f"AI {ai} requires 1 to 20 GS1 character-set-82 characters")
        normalized[ai] = value
    return normalized


def build_hri(elements: Mapping[str, str]) -> str:
    """Build parenthesized human-readable interpretation in canonical order."""
    normalized = validate_elements(elements)
    return "".join(f"({ai}){normalized[ai]}" for ai in AI_ORDER if ai in normalized)


def build_element_string(elements: Mapping[str, str]) -> str:
    """Build raw GS1 data, adding GS after non-final variable-length fields."""
    normalized = validate_elements(elements)
    present = [ai for ai in AI_ORDER if ai in normalized]
    return "".join(
        ai + normalized[ai] + (GROUP_SEPARATOR if ai in {"10", "21"} and ai != present[-1] else "")
        for ai in present
    )


def parse_gs1(payload: str, *, healthcare: bool = True) -> dict[str, str]:
    """Parse raw element data or parenthesized HRI for AIs 01, 17, 10 and 21.

    Raw variable fields are terminated only by a GS character or end of input.
    HRI data uses application identifiers in parentheses and supports literal
    parentheses escaped with a backslash inside variable values.
    """
    if not isinstance(payload, str) or not payload:
        raise ValueError("GS1 payload must be a nonempty string")
    if payload.startswith("("):
        matches = list(_HRI_PATTERN.finditer(payload))
        if not matches or matches[0].start() != 0:
            raise ValueError("Malformed parenthesized GS1 HRI")
        values: dict[str, str] = {}
        for index, match in enumerate(matches):
            ai = match.group(1)
            if ai not in AI_ORDER:
                raise ValueError(f"Unsupported AI {ai}")
            if ai in values:
                raise ValueError(f"Duplicate AI {ai}")
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(payload)
            value = payload[start:end]
            if ai in {"10", "21"}:
                value = re.sub(r"\\([()\\])", r"\1", value)
            elif index + 1 < len(matches) and end - start != FIXED_LENGTHS[ai]:
                raise ValueError(f"AI {ai} must contain exactly {FIXED_LENGTHS[ai]} characters")
            values[ai] = value
        return validate_elements(values, healthcare=healthcare)

    values = {}
    offset = 0
    while offset < len(payload):
        ai = payload[offset:offset + 2]
        if ai not in AI_ORDER or ai in values:
            raise ValueError(f"Unsupported, duplicate or misplaced AI at offset {offset}")
        offset += 2
        if ai in FIXED_LENGTHS:
            end = offset + FIXED_LENGTHS[ai]
            value = payload[offset:end]
            if len(value) != FIXED_LENGTHS[ai]:
                raise ValueError(f"AI {ai} is truncated")
            offset = end
        else:
            end = payload.find(GROUP_SEPARATOR, offset)
            if end < 0:
                end = len(payload)
            value = payload[offset:end]
            offset = end
            if offset < len(payload):
                offset += 1
                if offset == len(payload):
                    raise ValueError("Trailing GS separator has no following AI")
        values[ai] = value
    return validate_elements(values, healthcare=healthcare)


def _writer_hri(elements: Mapping[str, str]) -> str:
    """Escape data parentheses so zxing-cpp does not mistake them for AIs."""
    chunks = []
    for ai in AI_ORDER:
        if ai not in elements:
            continue
        value = elements[ai]
        if ai in {"10", "21"}:
            value = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        chunks.append(f"({ai}){value}")
    return "".join(chunks)


def encode_gs1(
    elements: Mapping[str, str],
    symbology: GS1Symbology = GS1Symbology.DATA_MATRIX,
    *,
    scale: int = 5,
    test_data: bool = False,
) -> EncodedBarcode:
    """Encode and decode-check a GS1 DataMatrix or GS1-128 barcode."""
    if not elements.get("01"):
        raise IdentifierRequired("Enter the allocated GTIN for AI 01")
    normalized = validate_elements(elements)
    if normalized["01"] == "00000000000000" and not test_data:
        raise IdentifierRequired("All-zero GTIN is permitted only with test_data=True")
    missing = set(REQUIRED_AIS) - set(normalized)
    if missing:
        raise ValueError(f"Missing required GS1 AIs: {', '.join(sorted(missing))}")
    if isinstance(scale, bool) or not isinstance(scale, int) or scale < 1:
        raise ValueError("Barcode scale must be at least 1")
    if not isinstance(symbology, GS1Symbology):
        symbology = GS1Symbology(symbology)
    barcode_format = {
        GS1Symbology.DATA_MATRIX: zxingcpp.BarcodeFormat.DataMatrix,
        GS1Symbology.CODE_128: zxingcpp.BarcodeFormat.Code128,
    }[symbology]
    barcode = zxingcpp.create_barcode(_writer_hri(normalized), barcode_format, gs1=True)
    image = np.asarray(barcode.to_image(scale=scale, add_hrt=True, add_quiet_zones=True))
    decoded = zxingcpp.read_barcodes(image)
    if (
        len(decoded) != 1
        or decoded[0].content_type != zxingcpp.ContentType.GS1
        or decoded[0].format != barcode_format
    ):
        raise RuntimeError("Generated barcode failed the GS1 decode self-check")
    decoded_values = parse_gs1(decoded[0].bytes.decode("latin-1"))
    if decoded_values != normalized or decoded[0].bytes != build_element_string(normalized).encode("ascii"):
        raise RuntimeError("Generated barcode decoded to values different from the input")
    svg = barcode.to_svg(scale=scale, add_hrt=True, add_quiet_zones=True)
    return EncodedBarcode(symbology, normalized, build_hri(normalized), image, svg)


def decide_barcode(
    old_elements: Mapping[str, str] | str | None,
    new_values: Mapping[str, str | None],
    confirmed: Mapping[str, bool] | None = None,
    *,
    old_symbology: GS1Symbology = GS1Symbology.DATA_MATRIX,
    new_symbology: GS1Symbology = GS1Symbology.DATA_MATRIX,
) -> BarcodeDecisionResult:
    """Return KEEP, REGENERATE or NEEDS_INPUT without inventing identifiers."""
    confirmed = confirmed or {}
    try:
        old_symbology = GS1Symbology(old_symbology)
        new_symbology = GS1Symbology(new_symbology)
    except ValueError:
        return BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, "Unsupported barcode symbology")
    if old_elements is None:
        old: dict[str, str] | None = None
    else:
        try:
            old = parse_gs1(old_elements) if isinstance(old_elements, str) else validate_elements(old_elements)
        except ValueError as error:
            return BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, f"Existing barcode is invalid: {error}")
    missing = [ai for ai in REQUIRED_AIS if not new_values.get(ai)]
    if missing:
        message = f"Missing required identifiers or values: {', '.join(missing)}"
        return BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, message)
    if old is not None and "21" in old and not new_values.get("21"):
        return BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, "Existing serial AI 21 cannot be silently removed")
    try:
        new = validate_elements({ai: value for ai, value in new_values.items() if value is not None})
    except ValueError as error:
        return BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, f"New barcode values are invalid: {error}")
    if old == new and old_symbology == new_symbology:
        return BarcodeDecisionResult(BarcodeAction.KEEP, "Encoded values and symbology are unchanged")
    if old == new:
        return BarcodeDecisionResult(
            BarcodeAction.REGENERATE,
            "Barcode symbology changed while the encoded values stayed the same",
        )
    if old is not None:
        confirmation_keys = {
            "01": "confirmed_gtin_change",
            "17": "confirmed_expiry_change",
            "10": "confirmed_lot_change",
            "21": "confirmed_serial_change",
        }
        changed = [ai for ai in AI_ORDER if old.get(ai) != new.get(ai)]
        unconfirmed = [ai for ai in changed if confirmed.get(confirmation_keys[ai]) is not True]
        if unconfirmed:
            return BarcodeDecisionResult(
                BarcodeAction.NEEDS_INPUT,
                f"Changed AI values require confirmation: {', '.join(unconfirmed)}",
            )
    message = "All required barcode values are present and encoded changes are confirmed"
    return BarcodeDecisionResult(BarcodeAction.REGENERATE, message)
