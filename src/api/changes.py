"""Change assessment for the API (Step 22c): create, store, confirm.

`src/change` decides (pure code, no database). This module reads the product and its labels, runs the assessment
twice (as proposed, and as if confirmed), stores one append-only `change_assessments` row, and on confirmation
appends a `change_confirmations` row plus the confirmed assessment. Nothing is updated in place.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.models import (
    ChangeAssessment,
    ChangeConfirmation,
    ChangeRequest,
    Extraction,
    LabelTemplate,
    LabelVersion,
    ProductVersion,
)
from src.api.requests import ChangeConfirmCreate, ChangeCreate
from src.api.status import is_closed
from src.api.store import create_change, current_product_version, new_id, record_audit
from src.change.assess import assess, item_json
from src.change.fields import record_values
from src.change.models import Assessment, ChangeError, Edit, EditProvider, LabelContext, Unassessed
from src.change.parser import parse_request, validate_edits
from src.checker.settings import CheckerSettings
from src.common.schemas import ProductRecord

NOT_CHECKED = (
    "NEEDS_HUMAN_REVIEW: nothing could be assessed, so the affected list is empty because nothing was checked, "
    "not because nothing is affected."
)
AIS = ("01", "17", "10", "21")


def impact_id(change_id: str, key: str) -> str:
    """Stable id of an item: the same change, label, slot and field always give the same id."""
    return "imp_" + hashlib.sha1(f"{change_id}|{key}".encode()).hexdigest()[:8]


def _record(row: ProductVersion) -> ProductRecord:
    return ProductRecord(
        product_id=row.product_id, version=row.version, name=row.name, model=row.model,
        manufacturer=row.manufacturer, manufacturer_address=row.manufacturer_address, udi_di=row.udi_di,
        sterilization=row.sterilization, storage=row.storage, extra=dict(row.extra or {}),
    )


def build_contexts(session: Session, product_id: str) -> list[LabelContext]:
    """One context per label family of the product: its latest version, template and (if any) decoded barcode."""
    versions = session.scalars(
        select(LabelVersion).where(LabelVersion.product_id == product_id).order_by(LabelVersion.seq)
    ).all()
    latest: dict[str, LabelVersion] = {}
    for version in versions:  # later rows overwrite earlier ones, so the highest artwork_version wins
        latest[version.label_id] = version
    contexts = []
    for version in latest.values():
        pinned = session.scalars(select(ProductVersion).where(
            ProductVersion.product_id == product_id, ProductVersion.version == version.product_version)).first()
        template = None
        if version.template_id:
            row = session.scalars(select(LabelTemplate).where(
                LabelTemplate.template_id == version.template_id, LabelTemplate.product_id == product_id,
                LabelTemplate.version == version.template_version)).first()
            if row is not None:
                template = {"template_id": row.template_id, "version": row.version, "slots": row.slots}
        printed = None
        extraction = session.scalars(
            select(Extraction).where(Extraction.version_id == version.version_id).order_by(Extraction.seq.desc())
        ).first()
        barcodes = (extraction.payload.get("barcodes") or []) if extraction else []
        if len(barcodes) == 1 and barcodes[0].get("parsed"):
            printed = {k: v for k, v in barcodes[0]["parsed"].items() if k in AIS}
        contexts.append(LabelContext(
            label_id=version.label_id, version_id=version.version_id,
            old_values=record_values(_record(pinned)) if pinned else {}, template=template, printed_barcode=printed,
        ))
    return contexts


def _retrieval(settings: CheckerSettings) -> tuple[Any, dict[str, Any]]:
    """The checker's retriever and device chunks, or (None, {}) when retrieval cannot be built (no citations then)."""
    try:
        from src.checker.retrieval import default_retriever, module_chunks

        return default_retriever(settings.retrieval), module_chunks("device")
    except Exception:  # items then say that no passage was retrieved and need a person
        return None, {}


def latest_assessment(session: Session, change_id: str) -> ChangeAssessment | None:
    """The newest stored assessment of a change."""
    stmt = select(ChangeAssessment).where(ChangeAssessment.change_id == change_id).order_by(ChangeAssessment.seq.desc())
    return session.scalars(stmt).first()


def decisions_of(session: Session, change_id: str) -> dict[str, str]:
    """impact_id to user_decision, the latest confirmation winning."""
    rows = session.scalars(
        select(ChangeConfirmation).where(ChangeConfirmation.change_id == change_id).order_by(ChangeConfirmation.seq)
    ).all()
    out: dict[str, str] = {}
    for row in rows:
        for decision in row.decisions:
            out[decision["impact_id"]] = decision["user_decision"]
    return out


def is_confirmed(session: Session, change_id: str) -> bool:
    """True once any confirmation exists for the change (parse_state is then `confirmed`)."""
    return session.scalars(
        select(ChangeConfirmation.seq).where(ChangeConfirmation.change_id == change_id)
    ).first() is not None


def affected_items(session: Session, row: ChangeAssessment) -> list[dict[str, Any]]:
    """The assessment's items with the current user_decision filled in."""
    decided = decisions_of(session, row.change_id)
    return [{**item, "user_decision": decided.get(item["impact_id"], "pending")} for item in row.payload["items"]]


def assessment_response(session: Session, change: ChangeRequest, row: ChangeAssessment) -> dict[str, Any]:
    """Contract ChangeAssessment for a stored assessment."""
    from src.api import views

    items = affected_items(session, row)
    payload = row.payload
    out: dict[str, Any] = {
        "change": views.change_json(session, change), "affected": items, "citations": payload["citations"],
        "checklist_complete": bool(items) and all(i["user_decision"] != "pending" for i in items),
        "parser": payload["parser"], "assessment_id": row.assessment_id,
    }
    if payload.get("needs_human_review"):
        out["needs_human_review"] = payload["needs_human_review"]
    if payload.get("unassessed"):
        out["unassessed_edits"] = payload["unassessed"]
    return out


def _merge_citations(*assessments: Assessment) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for a in assessments:
        for citation in a.citations:
            merged.setdefault(citation["chunk_id"], citation)
    return list(merged.values())


def create_assessed_change(
    session: Session, user_id: str, body: ChangeCreate, settings: CheckerSettings, provider: EditProvider | None
) -> dict[str, Any]:
    """POST /changes: parse, create the ChangeRequest, assess it, store the assessment, return the response."""
    record_row = current_product_version(session, body.product_id)
    current = record_values(_record(record_row))
    parser = "rules"
    if body.edits:
        raw_edits: list[dict[str, str | None]] = [e.model_dump() for e in body.edits]
    else:
        parsed = parse_request(body.raw_text or "", provider)
        if parsed.status != "parsed":
            raise ApiError(
                422, "parser_not_implemented",
                "The request could not be turned into edits without guessing. Send structured `edits` instead.",
                {"status": parsed.status, "issues": parsed.issues},
            )
        raw_edits = list(parsed.edits)  # type: ignore[arg-type]
        parser = parsed.source
    try:
        validated = validate_edits(raw_edits, current)
    except ChangeError as error:
        raise ApiError(422, error.code, error.message) from error

    if not validated.edits:  # nothing could be assessed: keep the request, say so
        first = raw_edits[0]
        change = create_change(session, user_id, body.product_id, first["field"] or "", first["new_value"] or "",
                               first.get("old_value") or "", body.raw_text, edits=[])
        unassessed = [{"field": u.field, "reason": u.reason, "message": u.message} for u in validated.unassessed]
        notes = " ".join(f"{u['field'] or '(no field)'}: {u['message']}" for u in unassessed)
        payload = {"parser": "not_implemented", "items": [], "citations": [], "warnings": [], "unassessed": unassessed,
                   "needs_human_review": f"{NOT_CHECKED} {notes}".strip()}
        row = _store(session, change.change_id, None, payload, False, user_id)
        return assessment_response(session, change, row)

    first, rest = validated.edits[0], validated.edits[1:]
    change = create_change(
        session, user_id, body.product_id, first.field, first.new_value, first.old_value, body.raw_text,
        edits=[{"field": e.field, "old_value": e.old_value, "new_value": e.new_value} for e in rest],
    )
    retriever, chunks = _retrieval(settings)
    row = assess_and_store(
        session, change, validated.edits, current, parser, validated.unassessed, validated.warnings, retriever,
        chunks, settings.retrieval.k, user_id,
    )
    return assessment_response(session, change, row)


def assess_and_store(
    session: Session, change: ChangeRequest, edits: list[Edit], current: dict[str, str], parser: str,
    unassessed: list[Unassessed], warnings: list[str], retriever: Any, chunks: dict[str, Any], k: int, user_id: str,
) -> ChangeAssessment:
    """Assess a change against the product's current labels (as proposed and as if confirmed) and store the result.

    Also used by the demo seed, with no retriever (so no citations are looked up).
    """
    new_values = {**current, **{e.field: e.new_value for e in edits}}
    contexts = build_contexts(session, change.product_id)
    common: dict[str, Any] = dict(unassessed=unassessed, warnings=warnings, retriever=retriever, chunks=chunks, k=k)
    shown = assess(edits, new_values, contexts, confirmed=False, **common)
    confirmed = assess(edits, new_values, contexts, confirmed=True, **common)

    def dump(a: Assessment) -> list[dict[str, Any]]:
        return [item_json(i, change.change_id, impact_id(change.change_id, i.key)) for i in a.items]

    payload = {
        "parser": parser, "items": dump(shown), "confirmed_items": dump(confirmed),
        "citations": _merge_citations(shown, confirmed), "warnings": shown.warnings,
        "unassessed": [{"field": u.field, "reason": u.reason, "message": u.message} for u in unassessed],
        "needs_human_review": shown.needs_human_review, "confirmed_needs_human_review": confirmed.needs_human_review,
        "edits": [{"field": e.field, "old_value": e.old_value, "new_value": e.new_value} for e in edits],
    }
    return _store(session, change.change_id, None, payload, False, user_id)


def _store(
    session: Session, change_id: str, parent: str | None, payload: dict[str, Any], confirmed: bool, user_id: str,
) -> ChangeAssessment:
    """Append an assessment row and its audit event."""
    row = ChangeAssessment(
        assessment_id=new_id("asm"), change_id=change_id, parent_assessment_id=parent, confirmed=confirmed,
        payload=payload, created_by=user_id, created_at=utcnow(),
    )
    session.add(row)
    record_audit(session, user_id, "change.assessed" if not confirmed else "change.assessment_confirmed", "change",
                 change_id, details={"assessment_id": row.assessment_id, "parser": payload["parser"],
                                     "items": len(payload["items"]), "confirmed": confirmed})
    session.commit()
    return row


def confirm_change(session: Session, user_id: str, change_id: str, body: ChangeConfirmCreate) -> dict[str, Any]:
    """POST /changes/{id}/confirm for a change that has a stored assessment."""
    change = session.get(ChangeRequest, change_id)
    assert change is not None  # the route checked
    latest = latest_assessment(session, change_id)
    assert latest is not None
    if is_closed(session, change_id):
        raise ApiError(409, "change_closed", "This change was rejected. Create a new change request.")
    if latest.payload["parser"] == "not_implemented" or not latest.payload["items"]:
        raise ApiError(409, "nothing_to_confirm", "Nothing was assessed, so there is nothing to confirm.")
    if not body.parse_confirmed:
        raise ApiError(422, "parse_not_confirmed", "parse_confirmed must be true to confirm a change.")
    if body.edits:
        raise ApiError(
            422, "edits_not_supported",
            "A changed set of edits is a new change (change requests are immutable). Create a new change instead.",
        )
    known = {i["impact_id"] for i in latest.payload["items"]}
    unknown = sorted({d.impact_id for d in body.decisions} - known)
    if unknown:
        message = f"Unknown impact ids for this change: {unknown}."
        raise ApiError(422, "unknown_impact", message, {"impact_ids": unknown})
    session.add(ChangeConfirmation(
        confirmation_id=new_id("cfm"), change_id=change_id, assessment_id=latest.assessment_id,
        decisions=[d.model_dump() for d in body.decisions], created_by=user_id, created_at=utcnow(),
    ))
    record_audit(session, user_id, "change.confirmed", "change", change_id,
                 details={"assessment_id": latest.assessment_id, "decisions": len(body.decisions)})
    session.commit()
    if not latest.confirmed:  # the first confirmation appends the confirmed variant of the assessment
        payload = {**latest.payload, "items": latest.payload["confirmed_items"],
                   "needs_human_review": latest.payload.get("confirmed_needs_human_review")}
        latest = _store(session, change_id, latest.assessment_id, payload, True, user_id)
    return assessment_response(session, change, latest)
