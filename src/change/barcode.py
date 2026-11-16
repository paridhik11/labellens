"""GS1 payload builder and the KEEP, REGENERATE, NEEDS_INPUT decision (docs/CHANGE_SPEC.md section 5).

Never fills a missing identifier, never pads, never accepts the test placeholder as a new value.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from src.change.fields import ENCODED_FIELDS, PLACEHOLDER_UDI
from src.change.models import BarcodeOutcome
from src.checker import gs1

AI_OF = {"udi_di": "01", "expiry": "17", "lot": "10", "serial": "21"}


class PayloadUnbuildable(ValueError):
    """The GS1 payload cannot be built. `field` is the first missing or invalid one (udi_di, expiry, lot, serial)."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"{field}: {reason}")
        self.field = field
        self.reason = reason


def build_ais(values: Mapping[str, str]) -> dict[str, str]:
    """AI values (01, 17, 10, 21) from canonical record values. All four are required, as the renderer requires."""
    udi = values.get("udi_di", "")
    if not udi:
        raise PayloadUnbuildable("udi_di", "no UDI-DI has been entered")
    if not (len(udi) == 14 and udi.isascii() and udi.isdigit() and gs1.check_digit_ok(udi)):
        raise PayloadUnbuildable("udi_di", "not 14 digits with a valid check digit")
    expiry = values.get("expiry", "")
    if not expiry:
        raise PayloadUnbuildable("expiry", "no expiry date has been entered")
    try:
        day = date.fromisoformat(expiry)
    except ValueError as error:
        raise PayloadUnbuildable("expiry", "not an ISO date") from error
    if not 2000 <= day.year <= 2099:
        raise PayloadUnbuildable("expiry", "year outside 2000 to 2099")
    ais = {"01": udi, "17": day.strftime("%y%m%d")}
    for name in ("lot", "serial"):
        value = values.get(name, "")
        if not value:
            raise PayloadUnbuildable(name, f"no {name} has been entered")
        if len(value) > 20 or any(c not in gs1.VARIABLE_CHARACTERS for c in value):
            raise PayloadUnbuildable(name, "not 1 to 20 characters from the GS1 character set")
        ais[AI_OF[name]] = value
    # the shared parser has the last word (lengths, check digit, real date)
    gs1.parse_gs1(f"01{ais['01']}17{ais['17']}10{ais['10']}{gs1.GROUP_SEPARATOR}21{ais['21']}")
    return ais


def readable(ais: Mapping[str, str]) -> str:
    """Human-readable element string, for example (01)...(17)...(10)...(21)..."""
    return "".join(f"({ai}){ais[ai]}" for ai in ("01", "17", "10", "21"))


def build_payload(values: Mapping[str, str]) -> str:
    """Human-readable GS1 payload for a record, or raise PayloadUnbuildable."""
    return readable(build_ais(values))


def _try(values: Mapping[str, str]) -> str:
    """Payload or empty text when it cannot be built."""
    try:
        return build_payload(values)
    except PayloadUnbuildable:
        return ""


def decide_barcode(
    old_values: Mapping[str, str], new_values: Mapping[str, str], edited: Sequence[str], *, symbology: str,
    confirmed: bool, invalid_encoded: Sequence[str] = (),
) -> BarcodeOutcome:
    """The barcode decision for one label. `edited` lists the canonical fields with a valid edit.

    First match wins (see the spec table). `invalid_encoded` names encoded fields whose edit was refused as
    invalid: the barcode cannot be assessed until a valid value is given.
    """
    old_payload = _try(old_values)
    touched = [f for f in ENCODED_FIELDS if f in edited]

    def need(field: str, reason: str, *rules: str, new: str = "") -> BarcodeOutcome:
        return BarcodeOutcome("NEEDS_INPUT", old_payload, new, symbology, reason, field, rules)

    if invalid_encoded:
        field = next(f for f in ENCODED_FIELDS if f in invalid_encoded)
        return need(field, f"The new {field} was refused as invalid, so the barcode cannot be assessed.", "BC-INVALID")
    if "model" in edited and "udi_di" not in edited:
        return need(
            "udi_di",
            "The model changed. A new model normally needs a new UDI-DI (21 CFR 830.50(a)). "
            "Send the allocated identifier as a udi_di edit.",
            "BC-830-50",
        )
    if not touched:
        placeholder = old_values.get("udi_di") == PLACEHOLDER_UDI
        note = " The label carries the test placeholder identifier." if placeholder else ""
        return BarcodeOutcome(
            "KEEP", old_payload, old_payload, symbology,
            "No encoded value (UDI-DI, expiry, lot, serial) changes, so the barcode is reused as it is." + note,
            None, ("BC-KEEP",),
        )
    if "udi_di" in edited and new_values.get("udi_di") == PLACEHOLDER_UDI:
        return need("udi_di", "The test placeholder identifier is not accepted as a new value.", "BC-PLACEHOLDER")
    try:
        new_payload = build_payload(new_values)
    except PayloadUnbuildable as error:
        reason = f"The new payload cannot be built: {error.reason}. Nothing is filled in."
        return need(error.field, reason, "BC-UNBUILDABLE")
    if new_payload == old_payload:
        return BarcodeOutcome("KEEP", old_payload, new_payload, symbology,
                              "The payload is unchanged, so the barcode is reused.", None, ("BC-KEEP",))
    changed = [f for f in touched if old_values.get(f, "") != new_values.get(f, "")]
    if confirmed:
        return BarcodeOutcome(
            "REGENERATE", old_payload, new_payload, symbology,
            f"Confirmed change to {', '.join(changed)}: a new barcode is drawn and checked by decoding it.",
            None, ("BC-REGENERATE",),
        )
    return need(
        f"confirm_{changed[0]}",
        f"The payload changes ({', '.join(changed)}). Confirm the change before a new barcode is drawn.",
        "BC-CONFIRM", new=new_payload,
    )
