"""Turn database rows into the JSON shapes of docs/contracts/openapi.yaml, and the read queries behind them.

Status, `closed`, `draft_watermark` and `resulting_status` are computed here from the record trail.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.changes import is_confirmed
from src.api.errors import ApiError
from src.api.models import (
    AuditEvent,
    ChangeRequest,
    CheckResult,
    LabelTemplate,
    LabelVersion,
    Product,
    ProductVersion,
    Review,
    User,
)
from src.api.reviews import RESULTING_STATUS
from src.api.status import (
    change_latest_review_id,
    change_status,
    draft_watermark,
    is_closed,
    label_version_status,
    latest_check,
    latest_review,
)
from src.api.store import PRODUCT_RECORD_FIELDS, current_product_version


def drop_none(data: dict[str, Any]) -> dict[str, Any]:
    """Remove keys whose value is None (optional fields are absent in the contract, not null)."""
    return {k: v for k, v in data.items() if v is not None}


def user_json(user: User) -> dict[str, Any]:
    """Serialize a User."""
    return {"user_id": user.user_id, "name": user.name, "role": user.role}


def product_json(session: Session, product: Product) -> dict[str, Any]:
    """Serialize a Product with its current version number."""
    current = current_product_version(session, product.product_id)
    return {
        "product_id": product.product_id,
        "module": product.module,
        "current_version": current.version,
        "created_at": product.created_at,
        "intended_market": product.intended_market,
    }


def product_version_json(row: ProductVersion) -> dict[str, Any]:
    """Serialize a ProductVersion (the ProductRecord fields plus metadata)."""
    out = {"product_id": row.product_id, "version": row.version}
    out.update({f: getattr(row, f) for f in PRODUCT_RECORD_FIELDS})
    out.update(
        drop_none(
            {
                "created_at": row.created_at,
                "created_by": row.created_by,
                "source_change_id": row.source_change_id,
                "supersedes_version": row.supersedes_version,
            }
        )
    )
    return out


def template_json(row: LabelTemplate) -> dict[str, Any]:
    """Serialize a LabelTemplate version."""
    return drop_none(
        {
            "template_id": row.template_id,
            "version": row.version,
            "product_id": row.product_id,
            "size_mm": {"w": row.size_w, "h": row.size_h},
            "background": row.background,
            "min_font_pt": row.min_font_pt,
            "slots": row.slots,
            "created_at": row.created_at,
            "created_by": row.created_by,
        }
    ) | {"background": row.background}  # background is required and may be null


def label_version_json(session: Session, row: LabelVersion) -> dict[str, Any]:
    """Serialize a LabelVersion with its derived status and watermark flag."""
    review = latest_review(session, row.version_id)
    return drop_none(
        {
            "version_id": row.version_id,
            "label_id": row.label_id,
            "product_id": row.product_id,
            "artwork_version": row.artwork_version,
            "product_version": row.product_version,
            "template_id": row.template_id,
            "template_version": row.template_version,
            "kind": row.kind,
            "status": label_version_status(session, row.version_id),
            "latest_review_id": review.review_id if review else None,
            "artwork_file": row.artwork_file,
            "pdf_file": row.pdf_file,
            "draft_watermark": draft_watermark(session, row.version_id),
            "parent_version_id": row.parent_version_id,
            "created_at": row.created_at,
            "created_by": row.created_by,
        }
    )


def change_json(session: Session, row: ChangeRequest) -> dict[str, Any]:
    """Serialize a ChangeRequest. Status, closed and latest_review_id are derived, never stored."""
    return drop_none(
        {
            "change_id": row.change_id,
            "product_id": row.product_id,
            "field": row.field,
            "old_value": row.old_value,
            "new_value": row.new_value,
            "status": change_status(session, row.change_id),
            "latest_review_id": change_latest_review_id(session, row.change_id),
            "closed": is_closed(session, row.change_id),
            "raw_text": row.raw_text,
            "parse_state": "confirmed" if is_confirmed(session, row.change_id) else row.parse_state,
            "edits": row.edits,
            "created_at": row.created_at,
            "created_by": row.created_by,
        }
    )


def review_json(row: Review) -> dict[str, Any]:
    """Serialize a Review. resulting_status follows from the decision."""
    return drop_none(
        {
            "review_id": row.review_id,
            "label_id": row.label_id,
            "version_id": row.version_id,
            "change_id": row.change_id,
            "decision": row.decision,
            "user_id": row.user_id,
            "reviewer_role": row.reviewer_role,
            "comment": row.comment,
            "artifact_sha256": row.artifact_sha256,
            "check_id": row.check_id,
            "assessment_id": row.assessment_id,
            "resulting_status": RESULTING_STATUS[row.decision],
            "decided_at": row.decided_at,
        }
    )


def audit_json(row: AuditEvent) -> dict[str, Any]:
    """Serialize an AuditEvent."""
    return drop_none(
        {
            "event_id": row.event_id,
            "at": row.at,
            "user_id": row.user_id,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "version_before": row.version_before,
            "version_after": row.version_after,
            "details": row.details,
        }
    )


# ---------------------------------------------------------------- read queries


def require_product(session: Session, product_id: str) -> Product:
    """Return the product or raise 404."""
    product = session.get(Product, product_id)
    if product is None:
        raise ApiError(404, "not_found", f"No product {product_id!r}.")
    return product


def latest_labels(session: Session, product_id: str) -> list[LabelVersion]:
    """Latest artwork version of each label family of a product, in order of first appearance."""
    rows = session.scalars(select(LabelVersion).where(LabelVersion.product_id == product_id).order_by(LabelVersion.seq))
    latest: dict[str, LabelVersion] = {}
    for row in rows:
        latest[row.label_id] = row  # later rows have higher artwork_version
    return list(latest.values())


def latest_templates(session: Session, product_id: str) -> list[LabelTemplate]:
    """Latest version of each template of a product."""
    rows = session.scalars(
        select(LabelTemplate).where(LabelTemplate.product_id == product_id).order_by(LabelTemplate.seq)
    )
    latest: dict[str, LabelTemplate] = {}
    for row in rows:
        latest[row.template_id] = row
    return list(latest.values())


def open_findings(session: Session, labels: list[LabelVersion]) -> int:
    """Critical plus review findings in the latest check of each family's latest version."""
    total = 0
    for label in labels:
        check: CheckResult | None = latest_check(session, label.version_id)
        if check is not None:
            total += check.critical_count + check.review_count
    return total


def product_detail(session: Session, product: Product) -> dict[str, Any]:
    """The ProductDetail response for a product."""
    return {
        "product": product_json(session, product),
        "record": product_version_json(current_product_version(session, product.product_id)),
        "templates": [template_json(t) for t in latest_templates(session, product.product_id)],
        "labels": [label_version_json(session, v) for v in latest_labels(session, product.product_id)],
    }


def product_summary(session: Session, product: Product) -> dict[str, Any]:
    """One row of the products list."""
    labels = latest_labels(session, product.product_id)
    return {
        "product": product_json(session, product),
        "record": product_version_json(current_product_version(session, product.product_id)),
        "open_findings": open_findings(session, labels),
        "label_count": len(labels),
    }


def product_history(session: Session, product_id: str) -> list[AuditEvent]:
    """Audit events for a product and everything under it, newest first."""
    versions = session.scalars(select(LabelVersion.version_id).where(LabelVersion.product_id == product_id)).all()
    templates = session.scalars(select(LabelTemplate.template_id).where(LabelTemplate.product_id == product_id)).all()
    changes = session.scalars(select(ChangeRequest.change_id).where(ChangeRequest.product_id == product_id)).all()
    checks = session.scalars(
        select(CheckResult.check_id).where(
            CheckResult.version_id.in_(versions) | CheckResult.template_id.in_(set(templates))
        )
    ).all()
    ids = {product_id, *versions, *templates, *changes, *checks}
    stmt = select(AuditEvent).where(AuditEvent.entity_id.in_(ids)).order_by(AuditEvent.at.desc(), AuditEvent.seq.desc())
    return list(session.scalars(stmt))
