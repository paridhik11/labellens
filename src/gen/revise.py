"""Prepare a new template/record version and a checked draft export snapshot.

Changes are structured ChangeRequests, not free-text interpretation. No files,
approvals, identifiers or publication records are created by this module.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Mapping

from src.common.schemas import ChangeRequest, IdentifierRequired, ProductRecord
from src.export.label_model import Label
from src.export.template import from_template
from src.gen.gs1 import BarcodeAction, BarcodeDecisionResult, GS1Symbology, decide_barcode, validate_expiry

CORE_FIELDS = frozenset({"name", "model", "manufacturer", "manufacturer_address", "udi_di", "sterilization", "storage"})
STERILE_SYMBOLS = {"EO": "sterile_eo", "R": "sterile_r", "sterile_eo": "sterile_eo", "sterile_r": "sterile_r",
                  "sterile": "sterile", "gamma": "sterile_r"}


@dataclass(frozen=True)
class RevisionResult:
    """Unpublished proposal; a blocked decision never contains drawable artwork."""

    template: dict[str, Any]
    record: ProductRecord
    fields: dict[str, str]
    barcode_decision: BarcodeDecisionResult
    label: Label | None
    change_log: tuple[dict[str, Any], ...]
    required_identifier: str | None = None
    self_check: dict[str, str] = field(default_factory=lambda: {
        "status": "NEEDS_HUMAN_REVIEW",
        "scope": "Template layout and barcode decode only; OCR and symbol detection NOT_RUN",
    })

    @property
    def status(self) -> str:
        """Distinguish a renderable draft from a proposal that still needs input."""
        return "NEEDS_INPUT" if self.label is None else "DRAFT"


    def require_label(self) -> Label:
        """Return renderable artwork or raise the contract's missing-identifier error."""
        if self.required_identifier:
            raise IdentifierRequired(f"Enter an allocated {self.required_identifier} before rendering")
        if self.label is None:
            raise ValueError(self.barcode_decision.reason)
        return self.label


def record_fields(record: ProductRecord) -> dict[str, str]:
    """Bind core fields and extra values without allowing extra to override identity."""
    values = {**record.extra, **{key: getattr(record, key) for key in CORE_FIELDS}}
    return {**values, "product_name": record.name}


def barcode_values(record: ProductRecord) -> dict[str, str]:
    """Translate supplied record values to GS1 AIs without inventing missing data."""
    expiry_text = record.extra.get("expiry", "")
    expiry = date.fromisoformat(expiry_text)
    if expiry.isoformat() != expiry_text or validate_expiry(expiry.strftime("%y%m%d")) != expiry:
        raise ValueError("Expiry must be an ISO date within the supported GS1 century window")
    values = {"01": record.udi_di, "17": expiry.strftime("%y%m%d"), "10": record.extra.get("lot", "")}
    if record.extra.get("serial"):
        values["21"] = record.extra["serial"]
    return values


def revise_template(
    template: Mapping[str, Any],
    record: ProductRecord,
    change: ChangeRequest,
    *,
    previous_label: Label,
    version_id: str,
    actor: str,
    reason: str,
    confirmed: Mapping[str, bool] | None = None,
    requires_new_identifier: bool = False,
    allocated_identifier: str | None = None,
) -> RevisionResult:
    """Copy a template and record into a new draft using the existing GS1 policy.

    Caller supplies the current export snapshot, a fresh version ID and any
    trusted per-AI confirmations. Whether a model change needs a new identifier
    is an explicit caller decision, never guessed from the model's wording.
    Only field edits are supported: layout migration and free-text changes are
    outside this API. Inputs are never modified, including on failed proposals.
    """
    if not all(isinstance(value, str) and value.strip() for value in (version_id, actor, reason)):
        raise ValueError("A new version ID, actor and reason are required")
    if version_id == previous_label.version_id:
        raise ValueError("A revision needs a new version ID")
    if type(requires_new_identifier) is not bool:
        raise ValueError("requires_new_identifier must be boolean")
    if not change.change_id.strip():
        raise ValueError("A change ID is required for the audit log")
    if change.product_id != record.product_id or template.get("product_id") not in {None, record.product_id}:
        raise ValueError("Template, change and record must belong to the same product")
    if type(template.get("version")) is not int or template["version"] < 1 or record.version < 1:
        raise ValueError("Template and record versions must be positive integers")
    slots = [slot for slot in template["slots"] if slot["type"] == "barcode"]
    barcodes = [element for element in previous_label.elements if element.kind == "barcode"]
    if len(slots) != 1 or len(barcodes) != 1:
        raise ValueError("Exactly one existing GS1 barcode slot is supported")
    symbology = GS1Symbology(slots[0]["symbology"])
    old_fields = record_fields(record)
    old_values = barcode_values(record)
    # Decode and compare the supplied source snapshot without drawing another barcode.
    bound = from_template(
        template, old_fields, old_values, version_id=previous_label.version_id,
        actor=previous_label.created_by, reason=previous_label.reason, test_data=previous_label.test_data,
        reuse_barcode=barcodes[0],
    )
    if (
        bound.template_id != previous_label.template_id or bound.template_version != previous_label.template_version
        or bound.width_mm != previous_label.width_mm or bound.height_mm != previous_label.height_mm
        or bound.elements != previous_label.elements
    ):
        raise ValueError("Source snapshot does not match the supplied template and current record")
    field_name = "name" if change.field == "product_name" else change.field.removeprefix("extra.")
    if field_name in {"product_id", "version", "extra"}:
        raise ValueError("Product identity and version metadata cannot be edited as label fields")
    if change.field.startswith("extra.") and field_name in CORE_FIELDS | {"product_name", "version", "product_id"}:
        raise ValueError("Extra fields cannot shadow core product fields")
    represented = {slot["field"] for slot in template["slots"] if slot["type"] == "text"}
    for slot in template["slots"]:
        if slot["type"] == "symbol" and slot["field"] == "sterilization":
            if STERILE_SYMBOLS.get(record.sterilization) != slot["symbol_name"]:
                raise ValueError("Source sterilization method and symbol disagree")
            represented.add("sterilization")
    if "product_name" in represented:
        represented.add("name")
    if field_name not in CORE_FIELDS | set(record.extra) | represented | {"lot", "expiry", "serial"}:
        raise ValueError("Unknown product field")
    if field_name not in represented | {"udi_di", "lot", "expiry", "serial"}:
        raise ValueError("No template slot represents the requested field")
    before = old_fields.get(field_name, "")
    if change.old_value != before:
        raise ValueError("Stale change: old_value does not match the current record")
    if change.new_value == before:
        raise ValueError("Change does not alter a value")
    if allocated_identifier is not None and not requires_new_identifier:
        raise ValueError("An allocated replacement identifier needs requires_new_identifier=True")
    new_template = deepcopy(dict(template))
    new_template["version"] += 1
    data = record.model_dump()
    data["version"] += 1
    if field_name in CORE_FIELDS:
        data[field_name] = change.new_value
    else:
        data["extra"][field_name] = change.new_value
    if requires_new_identifier:
        if field_name == "udi_di":
            if allocated_identifier is not None and allocated_identifier != change.new_value:
                raise ValueError("Conflicting replacement identifiers")
        else:
            data["udi_di"] = allocated_identifier or ""
    new_record = ProductRecord.model_validate(data)
    for slot in new_template["slots"]:
        if slot["type"] == "symbol" and slot["field"] == "sterilization" and field_name == "sterilization":
            if change.new_value not in STERILE_SYMBOLS:
                raise ValueError("Enter a supported sterilization symbol name or method: EO, R or gamma")
            slot["symbol_name"] = STERILE_SYMBOLS[change.new_value]
    required_identifier = "udi_di" if not new_record.udi_di else None
    if requires_new_identifier and new_record.udi_di == record.udi_di:
        required_identifier = "udi_di"
    if new_record.udi_di == "00000000000000" and not previous_label.test_data:
        required_identifier = "udi_di"
    try:
        new_values = barcode_values(new_record)
    except ValueError as error:
        decision = BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, str(error))
    else:
        decision = decide_barcode(old_values, new_values, confirmed,
                                  old_symbology=symbology, new_symbology=symbology)
    if required_identifier:
        decision = BarcodeDecisionResult(BarcodeAction.NEEDS_INPUT, "Enter an allocated udi_di before rendering")
    new_fields = record_fields(new_record)
    label = None
    if decision.action != BarcodeAction.NEEDS_INPUT:
        label = from_template(
            new_template, new_fields, new_values, version_id=version_id, actor=actor, reason=reason,
            test_data=previous_label.test_data,
            reuse_barcode=barcodes[0] if decision.action == BarcodeAction.KEEP else None,
        )
    log: list[dict[str, Any]] = [{
        "change_id": change.change_id, "field": field_name, "before": before, "after": change.new_value,
        "actor": actor, "reason": reason, "source_version_id": previous_label.version_id,
        "version_id": version_id, "template_version": new_template["version"],
        "record_version": new_record.version, "barcode_action": str(decision.action),
    }]
    if field_name != "udi_di" and new_record.udi_di != record.udi_di:
        log.append({"field": "udi_di", "before": record.udi_di, "after": new_record.udi_di,
                    "actor": actor, "reason": reason})
    result = RevisionResult(new_template, new_record, new_fields, decision, label, tuple(log), required_identifier)
    if label is None:
        result.self_check.update(status="NEEDS_INPUT", scope="Blocked proposal; no revised artwork checks run")
    return result
