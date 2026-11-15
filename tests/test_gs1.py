"""Tests for GS1 validation, barcode decisions and encoded symbol checks."""

from __future__ import annotations

import random
from datetime import date
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest

np = pytest.importorskip("numpy")
zxingcpp = pytest.importorskip("zxingcpp")

from src.common.schemas import IdentifierRequired  # noqa: E402
from src.gen.gs1 import (  # noqa: E402
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
    result = encode_gs1(EXAMPLE, symbology, test_data=True)
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
        for symbology in GS1Symbology:
            result = encode_gs1(elements, symbology, scale=3)
            decoded = zxingcpp.read_barcodes(result.image)
            assert len(decoded) == 1
            assert decoded[0].bytes == build_element_string(elements).encode("ascii")
            assert parse_gs1(decoded[0].bytes.decode("latin-1")) == elements
            assert ET.fromstring(result.svg).tag == "{http://www.w3.org/2000/svg}svg"


def test_literal_parentheses_inside_variable_data_round_trip() -> None:
    """Parentheses in lot data are escaped for the writer, not treated as AIs."""
    elements = {**EXAMPLE, "10": "LOT(21)A"}
    result = encode_gs1(elements, test_data=True)
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


@pytest.mark.parametrize("payload", [
    "(01)00000000000000(10)LOT(99)UNKNOWN",
    "010000000000000010LOT\x1d",
    "01000000000000001728123110LOT\x1d\x1d21SERIAL",
    "(10)LOT(10)DUPLICATE",
    "(01)123",
])
def test_malformed_payloads_do_not_partially_parse(payload: str) -> None:
    """Unsupported AIs and misplaced separators cannot be silently accepted."""
    with pytest.raises(ValueError):
        parse_gs1(payload)


def test_expiry_century_window_and_real_calendar() -> None:
    """Century boundaries follow GS1's reference-year window without guessing 20xx."""
    reference = date(2026, 11, 15)
    assert validate_expiry("770101", reference_date=reference) == date(1977, 1, 1)
    assert validate_expiry("760101", reference_date=reference) == date(2076, 1, 1)
    with pytest.raises(ValueError):
        validate_expiry("230229", reference_date=reference)
    assert validate_expiry("240229", reference_date=reference) == date(2024, 2, 29)


@pytest.mark.parametrize("symbology", list(GS1Symbology))
def test_all_allowed_variable_characters_encode(symbology: GS1Symbology) -> None:
    """Every character in GS1 set 82 survives encoding, including AI-like parentheses."""
    from src.gen.gs1 import VARIABLE_CHARACTERS

    chars = "".join(sorted(VARIABLE_CHARACTERS))
    assert len(chars) == 82
    for start in range(0, len(chars), 20):
        elements = {**EXAMPLE, "10": chars[start:start + 20], "21": "SN(10)"}
        result = encode_gs1(elements, symbology, test_data=True)
        assert zxingcpp.read_barcodes(result.image)[0].bytes == build_element_string(elements).encode("ascii")
    assert parse_gs1(r"(01)00000000000000(10)LOT\(21\)A") == {
        "01": EXAMPLE["01"], "10": "LOT(21)A",
    }


def test_missing_or_placeholder_gtin_requires_explicit_input() -> None:
    """Production encoding never invents or silently permits the test identifier."""
    with pytest.raises(IdentifierRequired):
        encode_gs1({"17": "281231", "10": "LOT"})
    with pytest.raises(IdentifierRequired):
        encode_gs1(EXAMPLE)


@pytest.mark.parametrize("scale", [0, -1, 1.5, True])
def test_invalid_scale_rejected(scale: int) -> None:
    """Rendering requires a positive integer pixel scale."""
    with pytest.raises(ValueError):
        encode_gs1(EXAMPLE, scale=scale, test_data=True)


@pytest.mark.parametrize("failure", ["none", "mismatch", "wrong_format", "not_gs1"])
def test_decode_self_check_refuses_bad_output(monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    """A failed or mismatched decode cannot be returned as a successful barcode."""
    decoded = SimpleNamespace(
        bytes=build_element_string({**EXAMPLE, "10": "WRONG"} if failure == "mismatch" else EXAMPLE).encode(),
        content_type=zxingcpp.ContentType.Text if failure == "not_gs1" else zxingcpp.ContentType.GS1,
        format=zxingcpp.BarcodeFormat.Code128 if failure == "wrong_format" else zxingcpp.BarcodeFormat.DataMatrix,
    )
    monkeypatch.setattr(zxingcpp, "read_barcodes", lambda _: [] if failure == "none" else [decoded])
    with pytest.raises(RuntimeError):
        encode_gs1(EXAMPLE, test_data=True)


@pytest.mark.parametrize("ai", ["01", "17", "10", "21"])
def test_each_missing_required_value_blocks_regeneration(ai: str) -> None:
    """Every required value, including an existing serial, must remain explicit."""
    new = {**EXAMPLE, ai: None}
    assert decide_barcode(EXAMPLE, new).action == BarcodeAction.NEEDS_INPUT


@pytest.mark.parametrize(("ai", "value", "flag"), [
    ("17", "290101", "confirmed_expiry_change"),
    ("21", "NEW-SERIAL", "confirmed_serial_change"),
])
def test_confirmed_changes_regenerate(ai: str, value: str, flag: str) -> None:
    """Expiry and serial changes require confirmation under the current contract."""
    assert decide_barcode(EXAMPLE, {**EXAMPLE, ai: value}, {flag: True}).action == BarcodeAction.REGENERATE


def test_decisions_validate_old_payload_and_symbology() -> None:
    """Broken existing data or unknown formats cannot lead to KEEP."""
    assert decide_barcode("broken", EXAMPLE).action == BarcodeAction.NEEDS_INPUT
    assert decide_barcode(EXAMPLE, EXAMPLE, new_symbology="unknown").action == BarcodeAction.NEEDS_INPUT
    assert decide_barcode(None, EXAMPLE).action == BarcodeAction.REGENERATE
    assert decide_barcode(build_element_string(EXAMPLE), EXAMPLE).action == BarcodeAction.KEEP


@pytest.mark.parametrize("symbology", list(GS1Symbology))
def test_maximum_length_lot_and_serial(symbology: GS1Symbology) -> None:
    """Both formats preserve the full permitted 20-character fields."""
    values = {**EXAMPLE, "10": "L" * 20, "21": "S" * 20}
    result = encode_gs1(values, symbology, test_data=True)
    assert zxingcpp.read_barcodes(result.image)[0].bytes == build_element_string(values).encode()


def test_noncanonical_ai_order_and_optional_serial() -> None:
    """Raw variable fields stop at GS regardless of the following AI's order."""
    payload = "21SN001\x1d10LOT001\x1d172812310100000000000000"
    assert parse_gs1(payload) == EXAMPLE
    no_serial = {key: value for key, value in EXAMPLE.items() if key != "21"}
    assert parse_gs1(build_element_string(no_serial)) == no_serial
    assert not build_element_string(no_serial).endswith("\x1d")


def test_known_external_gtin_check_digit_fixture() -> None:
    """An independent fixed example prevents a shared fixture-calculation error."""
    validate_gtin("09506000134352")
    with pytest.raises(ValueError):
        validate_gtin("09506000134353")
