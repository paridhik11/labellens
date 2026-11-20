"""Plain data classes for change assessment (docs/CHANGE_SPEC.md). Not part of src/common/schemas.py."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class ChangeError(Exception):
    """A request the rules refuse outright. `code` is an API error code, `message` is plain language."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Edit:
    """One validated edit: canonical field name, the record's current value, and the normalised new value."""

    field: str
    old_value: str
    new_value: str


@dataclass(frozen=True)
class Unassessed:
    """An edit that was not assessed, with a machine reason (`unknown_field`, `invalid_value`, ...) and words."""

    field: str
    reason: str
    message: str


@dataclass
class EditResult:
    """Result of validating structured edits against the current record."""

    edits: list[Edit] = field(default_factory=list)
    unassessed: list[Unassessed] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Result of parsing plain text. status: parsed, ambiguous, unknown or empty. source: rules or llm."""

    status: str
    edits: list[dict[str, str]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    source: str = "rules"


class EditProvider(Protocol):
    """Optional LLM path. Returns raw proposals (dicts with field, new_value, optional old_value) only.

    The parser validates every proposal itself. No provider is shipped in Step 22.
    """

    def propose_edits(self, raw_text: str, fields: tuple[str, ...]) -> list[dict[str, str]]:
        """Propose edits for a text the rules could not parse."""
        ...


@dataclass(frozen=True)
class BarcodeOutcome:
    """The barcode decision for one label (contract BarcodeDecision plus the rule ids that fired)."""

    decision: str  # KEEP, REGENERATE or NEEDS_INPUT
    old_payload: str
    new_payload: str
    symbology: str
    reason: str
    required_identifier: str | None = None
    rule_ids: tuple[str, ...] = ()

    def to_json(self) -> dict[str, str]:
        """Contract BarcodeDecision (no null optional keys)."""
        out = {
            "decision": self.decision, "old_payload": self.old_payload, "new_payload": self.new_payload,
            "symbology": self.symbology, "reason": self.reason,
        }
        if self.required_identifier:
            out["required_identifier"] = self.required_identifier
        return out


@dataclass
class LabelContext:
    """What impact analysis needs to know about one label family (its latest version)."""

    label_id: str
    version_id: str
    old_values: dict[str, str]  # canonical field -> value of the pinned product record
    template: dict[str, Any] | None = None  # {"template_id", "version", "slots": [...]} or None
    printed_barcode: dict[str, str] | None = None  # AIs of a stored extraction's decoded barcode, if any


@dataclass
class Item:
    """One affected item before citations. `key` is stable, so ids survive a re-assessment."""

    key: str
    label_id: str
    version_id: str
    item_kind: str  # text, symbol, barcode, linked_label
    title: str
    description: str
    suggestion: str  # edit_required, review_suggested, no_change
    rule_ids: list[str]
    fields: list[str]
    slot_id: str | None = None
    needs_human: bool = True
    barcode: BarcodeOutcome | None = None
    evidence_chunk_ids: list[str] = field(default_factory=list)


@dataclass
class Assessment:
    """The full result: items, de-duplicated citations, warnings and unassessed edits."""

    items: list[Item]
    citations: list[dict[str, Any]]
    warnings: list[str]
    unassessed: list[Unassessed]
    needs_human_review: str | None
