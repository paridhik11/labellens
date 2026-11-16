"""Database tables (see docs/contracts/DATA_MODEL.md).

Design rules, in plain words:
- Every table except `users` is append-only. SQLite triggers (src/api/db.py) reject UPDATE and DELETE,
  so an edit is always a new row with the next version number.
- No table has a `status` column. Status is computed from the Review and CheckResult rows
  (src/api/status.py). `closed` on a change and `resulting_status` on a review are also computed.
- `seq` columns are autoincrement counters that break ties between rows with the same timestamp.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, CheckConstraint, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.api.db import Base


class User(Base):
    """A person who can call the API (editor, reviewer or admin). Identified by the X-User-Id header."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('editor','reviewer','admin')", name="ck_user_role"),)

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)


class Product(Base):
    """Stable identity of a device. Its changing content lives in ProductVersion."""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String, primary_key=True)
    module: Mapped[str] = mapped_column(String, default="device")
    created_at: Mapped[str] = mapped_column(String)
    intended_market: Mapped[list[str]] = mapped_column(JSON, default=list)


class ProductVersion(Base):
    """One immutable version of a product record (the fields of ProductRecord plus metadata)."""

    __tablename__ = "product_versions"
    __table_args__ = (UniqueConstraint("product_id", "version"),)

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String, default="")
    manufacturer: Mapped[str] = mapped_column(String, default="")
    manufacturer_address: Mapped[str] = mapped_column(String, default="")
    udi_di: Mapped[str] = mapped_column(String, default="")
    sterilization: Mapped[str] = mapped_column(String, default="")
    storage: Mapped[str] = mapped_column(String, default="")
    extra: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    source_change_id: Mapped[str | None] = mapped_column(String, nullable=True)
    supersedes_version: Mapped[int | None] = mapped_column(Integer, nullable=True)


class LabelTemplate(Base):
    """One immutable version of a label template. Versions count per template_id inside one product."""

    __tablename__ = "label_templates"
    __table_args__ = (UniqueConstraint("template_id", "version"),)

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[str] = mapped_column(String, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    size_w: Mapped[float] = mapped_column(Float)
    size_h: Mapped[float] = mapped_column(Float)
    background: Mapped[str | None] = mapped_column(String, nullable=True)
    min_font_pt: Mapped[float | None] = mapped_column(Float, nullable=True)
    slots: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"))


class ChangeRequest(Base):
    """A requested change to a product field. Status and `closed` are derived, never stored."""

    __tablename__ = "change_requests"

    change_id: Mapped[str] = mapped_column(String, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), index=True)
    field: Mapped[str] = mapped_column(String)
    old_value: Mapped[str] = mapped_column(String, default="")
    new_value: Mapped[str] = mapped_column(String)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parse_state: Mapped[str] = mapped_column(String, default="proposed")
    edits: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"))


class LabelVersion(Base):
    """One immutable artwork version (L1, L2, ...) of a label family.

    `artifact_sha256` (sha256 of the draft manifest, set for generated artwork) and `change_id`
    (the change that produced the version) are stored here instead of in a separate
    GeneratedArtwork table for now.
    """

    __tablename__ = "label_versions"
    __table_args__ = (
        UniqueConstraint("label_id", "artwork_version"),
        CheckConstraint("kind IN ('uploaded','generated')", name="ck_label_kind"),
    )

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_id: Mapped[str] = mapped_column(String, unique=True)
    label_id: Mapped[str] = mapped_column(String, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), index=True)
    artwork_version: Mapped[int] = mapped_column(Integer)
    product_version: Mapped[int] = mapped_column(Integer)
    template_id: Mapped[str | None] = mapped_column(String, nullable=True)
    template_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kind: Mapped[str] = mapped_column(String)
    artwork_file: Mapped[str] = mapped_column(String)
    pdf_file: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    change_id: Mapped[str | None] = mapped_column(ForeignKey("change_requests.change_id"), nullable=True, index=True)
    artifact_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"))


class CheckResult(Base):
    """One run of a checker against a label version (or a template). `passed` means zero critical findings."""

    __tablename__ = "check_results"
    __table_args__ = (CheckConstraint("kind IN ('inspection','layout','self_check','template')", name="ck_check_kind"),)

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    check_id: Mapped[str] = mapped_column(String, unique=True)
    kind: Mapped[str] = mapped_column(String)
    label_id: Mapped[str | None] = mapped_column(String, nullable=True)
    version_id: Mapped[str | None] = mapped_column(ForeignKey("label_versions.version_id"), nullable=True, index=True)
    template_id: Mapped[str | None] = mapped_column(String, nullable=True)
    artifact_sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    run_at: Mapped[str] = mapped_column(String)
    passed: Mapped[bool] = mapped_column(Boolean)
    critical_count: Mapped[int] = mapped_column(Integer)
    review_count: Mapped[int] = mapped_column(Integer)
    info_count: Mapped[int] = mapped_column(Integer)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    # Step 21 (CR-17). Null on rows written before the checker existed or by tests that give no coverage.
    needs_human_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    retrieval_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class Extraction(Base):
    """A LabelExtraction produced for one label version (Step 21). Append-only: a re-extraction is a new row."""

    __tablename__ = "extractions"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    extraction_id: Mapped[str] = mapped_column(String, unique=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("label_versions.version_id"), index=True)
    label_id: Mapped[str] = mapped_column(String)
    mode: Mapped[str] = mapped_column(String)  # blind | template | stub
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)  # LabelExtraction.model_dump(mode="json")
    created_at: Mapped[str] = mapped_column(String)
    scan_id: Mapped[str | None] = mapped_column(String, nullable=True)  # set when it came from a scan (Step 24)


class Scan(Base):
    """One state of an upload (Step 24). Append-only like `jobs`: a state change is a new row, the newest is current.

    `created_at` is when the upload arrived (copied to every row), `updated_at` is when this row was written.
    The stored file is `stored_path` under the files folder, named by its sha256, never by the client filename.
    """

    __tablename__ = "scans"
    __table_args__ = (CheckConstraint("state IN ('queued','processing','done','failed')", name="ck_scan_state"),)

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[str] = mapped_column(String, index=True)
    job_id: Mapped[str | None] = mapped_column(String, nullable=True)
    module: Mapped[str] = mapped_column(String, default="device")
    source: Mapped[str] = mapped_column(String)  # upload | camera
    file_id: Mapped[str] = mapped_column(String)
    mime: Mapped[str] = mapped_column(String)
    sha256: Mapped[str] = mapped_column(String)
    pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stored_path: Mapped[str] = mapped_column(String)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id"), index=True)
    state: Mapped[str] = mapped_column(String)
    label_id: Mapped[str | None] = mapped_column(String, nullable=True)
    version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)


class ExtractionConfirmation(Base):
    """A user's confirmation or correction of an extraction (Step 24). Append-only.

    The corrected values are stored here (`fields`) and also as a new `extractions` row (`extraction_id`), so the
    checker, which reads the newest extraction, sees them. The corrected row stays untouched (`previous_extraction_id`).
    """

    __tablename__ = "extraction_confirmations"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    confirmation_id: Mapped[str] = mapped_column(String, unique=True)
    extraction_id: Mapped[str] = mapped_column(String, index=True)  # the new row that holds the confirmed values
    previous_extraction_id: Mapped[str] = mapped_column(String)
    version_id: Mapped[str] = mapped_column(String, index=True)
    fields: Mapped[dict[str, str]] = mapped_column(JSON)  # exactly what the user submitted
    confirmed_by: Mapped[str] = mapped_column(String)
    confirmed_at: Mapped[str] = mapped_column(String)


class Job(Base):
    """One state change of a background job (Step 21). The job's current state is its newest row."""

    __tablename__ = "jobs"
    __table_args__ = (CheckConstraint("state IN ('queued','processing','done','failed')", name="ck_job_state"),)

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str] = mapped_column(String, default="")
    result_url: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    version_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


class ChangeAssessment(Base):
    """One stored assessment of a change (Step 22). Append-only: confirming appends the confirmed assessment."""

    __tablename__ = "change_assessments"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[str] = mapped_column(String, unique=True)
    change_id: Mapped[str] = mapped_column(ForeignKey("change_requests.change_id"), index=True)
    parent_assessment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)  # parser, items, confirmed_items, citations, warnings, ...
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


class ChangeConfirmation(Base):
    """A person confirmed the parsed change and some checklist decisions (Step 22). Append-only."""

    __tablename__ = "change_confirmations"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    confirmation_id: Mapped[str] = mapped_column(String, unique=True)
    change_id: Mapped[str] = mapped_column(ForeignKey("change_requests.change_id"), index=True)
    assessment_id: Mapped[str] = mapped_column(String)  # the assessment the person was shown
    decisions: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


class Review(Base):
    """An approval record: approve, return or reject one exact label version."""

    __tablename__ = "reviews"
    __table_args__ = (CheckConstraint("decision IN ('approve','return','reject')", name="ck_review_decision"),)

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(String, unique=True)
    label_id: Mapped[str] = mapped_column(String)
    version_id: Mapped[str] = mapped_column(ForeignKey("label_versions.version_id"), index=True)
    change_id: Mapped[str | None] = mapped_column(ForeignKey("change_requests.change_id"), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"))
    reviewer_role: Mapped[str] = mapped_column(String)
    comment: Mapped[str] = mapped_column(Text, default="")
    artifact_sha256: Mapped[str] = mapped_column(String)
    check_id: Mapped[str | None] = mapped_column(ForeignKey("check_results.check_id"), nullable=True)
    decided_at: Mapped[str] = mapped_column(String)
    # Step 22 (CR-18): the change's latest assessment when the review was recorded. Null for changes without one.
    assessment_id: Mapped[str | None] = mapped_column(String, nullable=True)


class GeneratedArtwork(Base):
    """One generation run (Step 24b): the draft label version it created and what it was built from. Append-only.

    A regeneration is a new row and a new label version. `artifact_sha256` is the sha256 of the PDF bytes, the
    same value stored on the label version, and approval binds to it.
    """

    __tablename__ = "generated_artworks"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artwork_id: Mapped[str] = mapped_column(String, unique=True)
    change_id: Mapped[str] = mapped_column(ForeignKey("change_requests.change_id"), index=True)
    label_id: Mapped[str] = mapped_column(String, index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("label_versions.version_id"), unique=True)
    assessment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    self_check_id: Mapped[str] = mapped_column(String)  # the layout check written with the draft
    artifact_sha256: Mapped[str] = mapped_column(String)
    reference_sha256: Mapped[str] = mapped_column(String)  # the renderer's snapshot hash (not the file hash)
    test_data: Mapped[bool] = mapped_column(Boolean, default=False)
    size_w: Mapped[float] = mapped_column(Float)
    size_h: Mapped[float] = mapped_column(Float)
    barcode_decision: Mapped[dict[str, Any]] = mapped_column(JSON)
    change_log: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    visible_markings: Mapped[list[str]] = mapped_column(JSON)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


class Artifact(Base):
    """One stored file of a generated version (Step 24b), kept as `artifacts/<sha256>.<ext>`. Append-only."""

    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("version_id", "role"),
        CheckConstraint("role IN ('pdf','svg','report','qr_png','qr_svg')", name="ck_artifact_role"),
    )

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha256: Mapped[str] = mapped_column(String, index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("label_versions.version_id"), index=True)
    role: Mapped[str] = mapped_column(String)
    mime: Mapped[str] = mapped_column(String)
    ext: Mapped[str] = mapped_column(String)
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String)


class PublishedPage(Base):
    """The page a supplementary QR opens. Pinned to one version_id forever."""

    __tablename__ = "published_pages"

    page_id: Mapped[str] = mapped_column(String, primary_key=True)
    label_id: Mapped[str] = mapped_column(String)
    version_id: Mapped[str] = mapped_column(ForeignKey("label_versions.version_id"), index=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.review_id"))
    url: Mapped[str] = mapped_column(String)
    qr_payload: Mapped[str] = mapped_column(String)
    published_at: Mapped[str] = mapped_column(String)


class AuditEvent(Base):
    """Who did what, when. Append only."""

    __tablename__ = "audit_events"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String, unique=True)
    at: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(String)  # a user id, or "system"
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String, index=True)
    version_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# Tables where UPDATE and DELETE are rejected by triggers. Only `users` is left out.
IMMUTABLE_TABLES: tuple[str, ...] = (
    "products",
    "product_versions",
    "label_templates",
    "change_requests",
    "label_versions",
    "check_results",
    "extractions",
    "scans",
    "extraction_confirmations",
    "jobs",
    "change_assessments",
    "change_confirmations",
    "generated_artworks",
    "artifacts",
    "reviews",
    "published_pages",
    "audit_events",
)
