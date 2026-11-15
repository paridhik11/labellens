"""Write operations that append rows. Nothing here updates or deletes anything.

Each function validates its inputs, inserts new rows, writes an AuditEvent and commits.
Role checks (who may call what) belong to the endpoint layer (Step 20b), except the review
rules, which live in src/api/reviews.py.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.models import (
    AuditEvent,
    ChangeRequest,
    CheckResult,
    LabelTemplate,
    LabelVersion,
    Product,
    ProductVersion,
    User,
)

PRODUCT_RECORD_FIELDS = (
    "name",
    "model",
    "manufacturer",
    "manufacturer_address",
    "udi_di",
    "sterilization",
    "storage",
    "extra",
)


def new_id(prefix: str) -> str:
    """Return an opaque id with a readable prefix, for example `prd_3f9a1c2e`."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def get_user(session: Session, user_id: str) -> User:
    """Return the user or raise 401 unknown_user."""
    user = session.get(User, user_id)
    if user is None:
        raise ApiError(401, "unknown_user", f"No user with id {user_id!r}.")
    return user


def record_audit(
    session: Session,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    version_before: int | None = None,
    version_after: int | None = None,
    details: dict[str, Any] | None = None,
    at: str | None = None,
) -> AuditEvent:
    """Append one AuditEvent (not committed here, the caller commits with the change it describes)."""
    event = AuditEvent(
        event_id=new_id("evt"),
        at=at or utcnow(),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        version_before=version_before,
        version_after=version_after,
        details=details,
    )
    session.add(event)
    return event


def current_product_version(session: Session, product_id: str) -> ProductVersion:
    """Return the newest ProductVersion of a product, or raise 404."""
    stmt = select(ProductVersion).where(ProductVersion.product_id == product_id).order_by(ProductVersion.version.desc())
    row = session.scalars(stmt).first()
    if row is None:
        raise ApiError(404, "not_found", f"No product {product_id!r}.")
    return row


def create_product(
    session: Session,
    user_id: str,
    record: dict[str, Any],
    intended_market: list[str] | None = None,
    product_id: str | None = None,
    at: str | None = None,
) -> tuple[Product, ProductVersion]:
    """Register a product: one Product row and its version 1."""
    get_user(session, user_id)
    if not record.get("name"):
        raise ApiError(422, "validation_error", "A product needs a name.")
    unknown = set(record) - set(PRODUCT_RECORD_FIELDS)
    if unknown:
        raise ApiError(422, "validation_error", f"Unknown product fields: {sorted(unknown)}.")
    when = at or utcnow()
    product = Product(
        product_id=product_id or new_id("prd"), module="device", created_at=when, intended_market=intended_market or []
    )
    session.add(product)
    session.flush()
    version = ProductVersion(product_id=product.product_id, version=1, created_at=when, created_by=user_id, **record)
    session.add(version)
    record_audit(session, user_id, "product.version_created", "product", product.product_id, None, 1, at=when)
    session.commit()
    return product, version


def add_product_version(
    session: Session,
    user_id: str,
    product_id: str,
    changes: dict[str, Any],
    source_change_id: str | None = None,
    at: str | None = None,
) -> ProductVersion:
    """Append the next ProductVersion: the current record with `changes` applied. Old versions stay as they are."""
    get_user(session, user_id)
    unknown = set(changes) - set(PRODUCT_RECORD_FIELDS)
    if unknown:
        raise ApiError(422, "validation_error", f"Unknown product fields: {sorted(unknown)}.")
    current = current_product_version(session, product_id)
    values = {f: getattr(current, f) for f in PRODUCT_RECORD_FIELDS}
    values.update(changes)
    when = at or utcnow()
    version = ProductVersion(
        product_id=product_id,
        version=current.version + 1,
        created_at=when,
        created_by=user_id,
        source_change_id=source_change_id,
        supersedes_version=current.version,
        **values,
    )
    session.add(version)
    record_audit(
        session,
        user_id,
        "product.version_created",
        "product",
        product_id,
        current.version,
        version.version,
        {"changed_fields": sorted(changes)},
        at=when,
    )
    session.commit()
    return version


def register_template(
    session: Session,
    user_id: str,
    product_id: str,
    size_mm: dict[str, float],
    slots: list[dict[str, Any]],
    background: str | None = None,
    min_font_pt: float | None = None,
    template_id: str | None = None,
    at: str | None = None,
) -> LabelTemplate:
    """Register a template version.

    New `template_id` (or None) gives version 1. An existing `template_id` of the same product gives the
    next version. A template_id that belongs to another product is refused (409).
    """
    get_user(session, user_id)
    current_product_version(session, product_id)  # 404 if the product does not exist
    version = 1
    if template_id is not None:
        stmt = (
            select(LabelTemplate).where(LabelTemplate.template_id == template_id).order_by(LabelTemplate.version.desc())
        )
        latest = session.scalars(stmt).first()
        if latest is not None:
            if latest.product_id != product_id:
                raise ApiError(
                    409, "template_product_mismatch", f"Template {template_id!r} belongs to another product."
                )
            version = latest.version + 1
    else:
        template_id = new_id("tpl")
    row = LabelTemplate(
        template_id=template_id,
        product_id=product_id,
        version=version,
        size_w=size_mm["w"],
        size_h=size_mm["h"],
        background=background,
        min_font_pt=min_font_pt,
        slots=slots,
        created_at=at or utcnow(),
        created_by=user_id,
    )
    session.add(row)
    record_audit(
        session,
        user_id,
        "template.version_created",
        "template",
        template_id,
        version - 1 or None,
        version,
        at=row.created_at,
    )
    session.commit()
    return row


def create_change(
    session: Session,
    user_id: str,
    product_id: str,
    field: str,
    new_value: str,
    old_value: str = "",
    raw_text: str | None = None,
    parse_state: str = "proposed",
    change_id: str | None = None,
    edits: list[dict[str, str]] | None = None,
    at: str | None = None,
) -> ChangeRequest:
    """Record a change request. Status and `closed` are derived later from reviews, never set here."""
    get_user(session, user_id)
    current_product_version(session, product_id)
    when = at or utcnow()
    change = ChangeRequest(
        change_id=change_id or new_id("chg"),
        product_id=product_id,
        field=field,
        old_value=old_value,
        new_value=new_value,
        raw_text=raw_text,
        parse_state=parse_state,
        edits=edits or [],
        created_at=when,
        created_by=user_id,
    )
    session.add(change)
    record_audit(session, user_id, "change.created", "change", change.change_id, at=when)
    session.commit()
    return change


def add_label_version(
    session: Session,
    user_id: str,
    product_id: str,
    artwork_file: str,
    kind: str = "uploaded",
    label_id: str | None = None,
    product_version: int | None = None,
    template_id: str | None = None,
    template_version: int | None = None,
    pdf_file: str | None = None,
    change_id: str | None = None,
    artifact_sha256: str | None = None,
    version_id: str | None = None,
    at: str | None = None,
) -> LabelVersion:
    """Append the next artwork version of a label family (a new family when `label_id` is None)."""
    get_user(session, user_id)
    current = current_product_version(session, product_id)
    if kind == "generated" and not artifact_sha256:
        raise ApiError(422, "artifact_hash_required", "Generated artwork needs the sha256 of its draft manifest.")
    if product_version is None:
        product_version = current.version
    elif product_version < 1 or product_version > current.version:
        raise ApiError(422, "validation_error", f"Product {product_id!r} has no version {product_version}.")
    if change_id is not None:
        change = session.get(ChangeRequest, change_id)
        if change is None or change.product_id != product_id:
            raise ApiError(404, "not_found", f"No change {change_id!r} for product {product_id!r}.")
    if template_id is not None:
        stmt = select(LabelTemplate).where(
            LabelTemplate.template_id == template_id, LabelTemplate.product_id == product_id
        )
        if template_version is not None:
            stmt = stmt.where(LabelTemplate.version == template_version)
        found = session.scalars(stmt.order_by(LabelTemplate.version.desc())).first()
        if found is None:
            raise ApiError(
                404, "not_found", f"No template {template_id!r} (version {template_version}) for this product."
            )
        template_version = found.version
    parent: LabelVersion | None = None
    artwork_version = 1
    if label_id is None:
        label_id = new_id("lbl")
    else:
        stmt = (
            select(LabelVersion).where(LabelVersion.label_id == label_id).order_by(LabelVersion.artwork_version.desc())
        )
        parent = session.scalars(stmt).first()
        if parent is not None:
            if parent.product_id != product_id:
                raise ApiError(409, "label_product_mismatch", f"Label {label_id!r} belongs to another product.")
            artwork_version = parent.artwork_version + 1
    when = at or utcnow()
    row = LabelVersion(
        version_id=version_id or new_id("lbv"),
        label_id=label_id,
        product_id=product_id,
        artwork_version=artwork_version,
        product_version=product_version,
        template_id=template_id,
        template_version=template_version,
        kind=kind,
        artwork_file=artwork_file,
        pdf_file=pdf_file,
        parent_version_id=parent.version_id if parent else None,
        change_id=change_id,
        artifact_sha256=artifact_sha256,
        created_at=when,
        created_by=user_id,
    )
    session.add(row)
    record_audit(
        session,
        user_id,
        "label.version_created",
        "label_version",
        row.version_id,
        parent.artwork_version if parent else None,
        artwork_version,
        {"label_id": label_id, "change_id": change_id},
        at=when,
    )
    session.commit()
    return row


def add_check_result(
    session: Session,
    kind: str,
    findings: list[dict[str, Any]],
    version_id: str | None = None,
    template_id: str | None = None,
    artifact_sha256: str | None = None,
    check_id: str | None = None,
    user_id: str = "system",
    at: str | None = None,
    coverage: list[dict[str, Any]] | None = None,
    retrieval_config: dict[str, Any] | None = None,
) -> CheckResult:
    """Record one checker run. Counts and `passed` (zero critical findings) are computed from `findings`.

    `coverage` (one entry per checker rule) is stored as given and `needs_human_count` is computed from it.
    """
    label_id = None
    if kind in ("inspection", "self_check"):
        if version_id is None:
            raise ApiError(422, "validation_error", f"A {kind} check needs a version_id.")
    elif template_id is None:
        raise ApiError(422, "validation_error", f"A {kind} check needs a template_id.")
    if version_id is not None:
        version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
        if version is None:
            raise ApiError(404, "not_found", f"No label version {version_id!r}.")
        label_id = version.label_id
    counts = {s: sum(1 for f in findings if f.get("severity") == s) for s in ("critical", "review", "info")}
    when = at or utcnow()
    row = CheckResult(
        check_id=check_id or new_id("chk"),
        kind=kind,
        label_id=label_id,
        version_id=version_id,
        template_id=template_id,
        artifact_sha256=artifact_sha256,
        run_at=when,
        passed=counts["critical"] == 0,
        critical_count=counts["critical"],
        review_count=counts["review"],
        info_count=counts["info"],
        findings=findings,
        coverage=coverage,
        needs_human_count=None if coverage is None else sum(1 for c in coverage if c.get("outcome") == "needs_human"),
        retrieval_config=retrieval_config,
    )
    session.add(row)
    record_audit(
        session, user_id, "check.recorded", "check", row.check_id, details={"kind": kind, "passed": row.passed}, at=when
    )
    session.commit()
    return row


def count_rows(session: Session, model: type) -> int:
    """Return how many rows a table holds (used by tests and the seed)."""
    return session.scalar(select(func.count()).select_from(model)) or 0
