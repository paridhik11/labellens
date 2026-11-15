"""Tests for GS1 validation, barcode decisions and encoded symbol checks."""

from __future__ import annotations

import random

import pytest
import zxingcpp

from src.gen.gs1 import (
    BarcodeAction,
    GS1Symbology,
    build_element_string,
    build_hri,
    decide_barcode,
    encode_gs1,
    parse_gs1,
    validate_elements,
    validate_expiry,
    validate_gtin,
)

EXAMPLE = {"01": "00000000000000", "17": "281231", "10": "LOT001", "21": "SN001"}


def make_gtin(prefix: str) -> str:
    """Build a check-digit-valid GTIN for test fixtures only."""
    data = prefix.zfill(13)
    weighted = sum(int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(reversed(data)))
    return data + str((-weighted) % 10)


def test_hri_raw_string_and_group_separator_round_trip() -> None:
    """Both HRI and raw encoding preserve variable field boundaries."""
    hri = "(01)00000000000000(17)281231(10)LOT001(21)SN001"
    raw = "01000000000000001728123110LOT001\x1d21SN001"
    assert parse_gs1(hri) == EXAMPLE
    assert parse_gs1(raw) == EXAMPLE
    assert build_hri(EXAMPLE) == hri
    assert build_element_string(EXAMPLE) == raw


@pytest.mark.parametrize("symbology", list(GS1Symbology))
def test_encoded_barcodes_decode_to_exact_values(symbology: GS1Symbology) -> None:
    """Both contract barcode formats are decoded and compared after rendering."""
    result = encode_gs1(EXAMPLE, symbology)
    decoded = zxingcpp.read_barcodes(result.image)
    assert result.elements == EXAMPLE
    assert result.hri == build_hri(EXAMPLE)
    assert "<svg" in result.svg
    assert len(decoded) == 1
    assert decoded[0].content_type == zxingcpp.ContentType.GS1
    assert parse_gs1(decoded[0].bytes.decode("latin-1")) == EXAMPLE


def test_generated_symbols_round_trip_for_200_seeded_payloads() -> None:
    """A deterministic varied sample round-trips across both symbologies."""
    rng = random.Random(1701)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-./"
    for index in range(200):
        elements = {
            "01": make_gtin(str(rng.randrange(10**13))),
            "17": f"{28 + index % 10:02d}{rng.randrange(1, 13):02d}{rng.randrange(1, 28):02d}",
            "10": "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 16))),
        }
        if index % 2:
            elements["21"] = "".join(rng.choice(alphabet) for _ in range(rng.randrange(1, 16)))
        result = encode_gs1(elements, list(GS1Symbology)[index % 2], scale=3)
        decoded = zxingcpp.read_barcodes(result.image)
        assert len(decoded) == 1
        assert parse_gs1(decoded[0].bytes.decode("latin-1")) == elements


def test_literal_parentheses_inside_variable_data_round_trip() -> None:
    """Parentheses in lot data are escaped for the writer, not treated as AIs."""
    elements = {**EXAMPLE, "10": "LOT(21)A"}
    result = encode_gs1(elements)
    decoded = zxingcpp.read_barcodes(result.image)
    assert len(decoded) == 1
    assert parse_gs1(decoded[0].bytes.decode("latin-1")) == elements


@pytest.mark.parametrize("value", ["123", "00000000000001", "１２３４５６７８９０１２３４"])
def test_invalid_gtin_is_rejected(value: str) -> None:
    """Incorrect length, check digit and non-ASCII digits do not validate."""
    with pytest.raises(ValueError):
        validate_gtin(value)


@pytest.mark.parametrize("value", ["280200", "281332", "281200", "28A231"])
def test_invalid_or_unspecific_healthcare_expiry_is_rejected(value: str) -> None:
    """Healthcare expiry dates require an actual valid calendar day."""
    with pytest.raises(ValueError):
        validate_expiry(value)


def test_non_healthcare_day_zero_means_month_end() -> None:
    """The general GS1 day-zero meaning uses the correct leap-year month end."""
    assert validate_expiry("240200", healthcare=False).isoformat() == "2024-02-29"


@pytest.mark.parametrize("values", [
    {**EXAMPLE, "10": ""},
    {**EXAMPLE, "10": "X" * 21},
    {**EXAMPLE, "21": "bad space"},
    {**EXAMPLE, "99": "unsupported"},
])
def test_invalid_variable_fields_and_unsupported_ai_are_rejected(values: dict[str, str]) -> None:
    """Unsupported AI, empty, long and disallowed data are rejected."""
    with pytest.raises(ValueError):
        validate_elements(values)


@pytest.mark.parametrize(
    ("old", "new", "confirmed", "action"),
    [
        (EXAMPLE, EXAMPLE, None, BarcodeAction.KEEP),
        (EXAMPLE, {**EXAMPLE, "10": "LOT002"}, None, BarcodeAction.NEEDS_INPUT),
        (EXAMPLE, {**EXAMPLE, "17": "290101"}, None, BarcodeAction.NEEDS_INPUT),
        (EXAMPLE, {**EXAMPLE, "01": make_gtin("1234567890123")}, None, BarcodeAction.NEEDS_INPUT),
        (
            EXAMPLE,
            {**EXAMPLE, "01": make_gtin("1234567890123")},
            {"confirmed_gtin_change": True},
            BarcodeAction.REGENERATE,
        ),
        (
            EXAMPLE,
            {**EXAMPLE, "10": "LOT002"},
            {"confirmed_lot_change": True},
            BarcodeAction.REGENERATE,
        ),
        (EXAMPLE, {key: val for key, val in EXAMPLE.items() if key != "21"}, None, BarcodeAction.NEEDS_INPUT),
        (EXAMPLE, {**EXAMPLE, "10": None}, None, BarcodeAction.NEEDS_INPUT),
    ],
)
def test_barcode_decision_policy(
    old: dict[str, str], new: dict[str, str | None], confirmed: dict[str, bool] | None, action: BarcodeAction
) -> None:
    """A decision never regenerates with missing or unconfirmed identifiers."""
    result = decide_barcode(old, new, confirmed=confirmed)
    assert result.action == action
    assert result.reason


def test_missing_values_on_new_barcode_require_input() -> None:
    """An initial barcode is generated only after every required value exists."""
    result = decide_barcode(None, {"01": "00000000000000", "17": "281231", "10": None})
    assert result.action == BarcodeAction.NEEDS_INPUT


def test_symbology_change_regenerates_even_when_payload_is_unchanged() -> None:
    """The contract requires matching symbology as well as matching data to keep."""
    result = decide_barcode(
        EXAMPLE,
        EXAMPLE,
        old_symbology=GS1Symbology.DATA_MATRIX,
        new_symbology=GS1Symbology.CODE_128,
    )
    assert result.action == BarcodeAction.REGENERATE


def test_parse_rejects_duplicates_and_truncation() -> None:
    """Raw fields cannot be duplicated or end before their fixed length."""
    with pytest.raises(ValueError):
        parse_gs1("01000000000000000100000000000000")
    with pytest.raises(ValueError):
        parse_gs1("010000")
