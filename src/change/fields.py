"""The one table of supported fields, aliases and value rules (docs/CHANGE_SPEC.md section 2)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from src.change.models import ChangeError
from src.checker import gs1
from src.common.schemas import ProductRecord


class InvalidValue(ValueError):
    """A value that fails its field's rule. `code` is `invalid_value` or `ambiguous_date`."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class FieldSpec:
    """A supported field. `ai` is the GS1 application identifier it is encoded in, if any."""

    name: str
    aliases: tuple[str, ...]
    in_extra: bool = False
    ai: str | None = None


FIELDS: dict[str, FieldSpec] = {s.name: s for s in (
    FieldSpec("name", ("product name", "device name")),
    FieldSpec("model", ("model number",)),
    FieldSpec("manufacturer", ("mfr",)),
    FieldSpec("manufacturer_address", ("address", "mfr address", "manufacturer address")),
    FieldSpec("udi_di", ("udi", "gtin", "device identifier"), ai="01"),
    FieldSpec("sterilization", ("sterilisation", "sterilization method")),
    FieldSpec("storage", ("storage conditions",)),
    FieldSpec("lot", ("batch", "lot number"), in_extra=True, ai="10"),
    FieldSpec("expiry", ("expiry date", "expiration date", "exp"), in_extra=True, ai="17"),
    FieldSpec("serial", ("serial number", "sn"), in_extra=True, ai="21"),
    FieldSpec("ref", ("reference", "ref number"), in_extra=True),
    FieldSpec("rx_only", ("prescription only", "rx"), in_extra=True),
)}
ENCODED_FIELDS = ("udi_di", "expiry", "lot", "serial")  # also the order problems are reported in
PLACEHOLDER_UDI = "00000000000000"
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TEXT_DATE_FORMATS = ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y")
NUMERIC_DATE = re.compile(r"^\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}$")


def _key(text: str) -> str:
    """Lower case, underscores and hyphens as spaces, whitespace collapsed (alias matching key)."""
    return re.sub(r"\s+", " ", re.sub(r"[_\-]+", " ", text.lower())).strip()


ALIAS_TO_FIELD: dict[str, str] = {}
for _spec in FIELDS.values():
    for _alias in (_spec.name, *_spec.aliases):
        ALIAS_TO_FIELD[_key(_alias)] = _spec.name


def resolve_field(text: str) -> str | None:
    """Canonical field name for a name or alias, or None when it is not supported."""
    return ALIAS_TO_FIELD.get(_key(text))


def normalise_value(field: str, value: str) -> str:
    """Trim, collapse whitespace and validate. Raises InvalidValue. Never repairs or pads."""
    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        raise InvalidValue("invalid_value", f"The new {field} is empty.")
    if field == "udi_di":
        if not (len(text) == 14 and text.isascii() and text.isdigit() and gs1.check_digit_ok(text)):
            raise InvalidValue("invalid_value", "A UDI-DI must be exactly 14 digits with a valid GS1 check digit.")
    elif field in ("lot", "serial"):
        if not 1 <= len(text) <= 20 or any(c not in gs1.VARIABLE_CHARACTERS for c in text):
            raise InvalidValue("invalid_value", f"A {field} must be 1 to 20 characters from the GS1 character set.")
    elif field == "expiry":
        text = _normalise_date(text)
    elif field == "rx_only":
        lowered = text.lower()
        if lowered in ("true", "yes", "on"):
            return "true"
        if lowered in ("false", "no", "off"):
            return "false"
        raise InvalidValue("invalid_value", "rx_only must be true or false.")
    return text


def _normalise_date(text: str) -> str:
    """ISO date or a written-out date to YYYY-MM-DD. Numeric day/month dates are ambiguous and refused."""
    parsed: date | None = None
    if ISO_DATE.match(text):
        try:
            parsed = date.fromisoformat(text)
        except ValueError as error:
            raise InvalidValue("invalid_value", f"{text!r} is not a real calendar date.") from error
    elif NUMERIC_DATE.match(text):
        raise InvalidValue("ambiguous_date", f"{text!r} could be day first or month first. Write it as YYYY-MM-DD.")
    else:
        for fmt in TEXT_DATE_FORMATS:
            try:
                parsed = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
    if parsed is None:
        raise InvalidValue("invalid_value", f"{text!r} is not a date. Write it as YYYY-MM-DD.")
    if not 2000 <= parsed.year <= 2099:
        raise InvalidValue("invalid_value", "The expiry year must be between 2000 and 2099.")
    return parsed.isoformat()


def record_values(record: ProductRecord) -> dict[str, str]:
    """Flat canonical-field view of a product record (extra keys included, missing ones empty)."""
    out: dict[str, str] = {}
    for spec in FIELDS.values():
        out[spec.name] = (record.extra.get(spec.name, "") if spec.in_extra else getattr(record, spec.name, "")) or ""
    return out


def check_edit_set(fields: list[str]) -> None:
    """Refuse the same canonical field twice."""
    seen: set[str] = set()
    for name in fields:
        if name in seen:
            raise ChangeError("duplicate_field", f"The field {name!r} appears more than once. Send one edit per field.")
        seen.add(name)
