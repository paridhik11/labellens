"""The real endpoints (Step 20b). Every other operation in openapi.yaml is served from mock JSON (mock_server.py).

Roles (X-User-Id header stub): editor or admin register products, templates and changes; reviewer or admin
review. Reads need a known user.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import changes, checks, views
from src.api.errors import ApiError
from src.api.models import (
    ChangeRequest,
    CheckResult,
    LabelTemplate,
    LabelVersion,
    Product,
    ProductVersion,
    Review,
    User,
)
from src.api.requests import (
    ChangeConfirmCreate,
    ChangeCreate,
    InspectCreate,
    ProductCreate,
    ProfessionalQuestion,
    PublicQuestion,
    ReviewCreate,
    SearchCreate,
    TemplateCreate,
)
from src.api.reviews import record_review
from src.api.store import (
    create_product,
    get_user,
    register_template,
)

# operationIds implemented for real. getHealth lives in main.py. Everything else in the spec is a mock.
REAL_OPERATIONS = frozenset(
    {
        "getCurrentUser",
        "listProducts",
        "registerProduct",
        "getProduct",
        "listProductVersions",
        "registerTemplate",
        "getTemplate",
        "getProductHistory",
        "listLabelVersions",
        "getLabelVersion",
        "assessChange",
        "confirmChange",
        "listAffectedLabels",
        "getChange",
        "listReviews",
        "reviewArtwork",
        "inspectLabel",
        "recheckArtwork",
        "getJob",
        "getCheckResult",
        "searchEvidence",
        "askPublic",
        "askProfessional",
    }
)
router = APIRouter()


def get_session(request: Request) -> Iterator[Session]:
    """One database session per request."""
    with request.app.state.session_factory() as session:
        yield session


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """The user named by the X-User-Id header (a stub, not security). 401 unknown_user otherwise."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        raise ApiError(401, "unknown_user", "The X-User-Id header is required.")
    return get_user(session, user_id)


def writer(user: User = Depends(current_user)) -> User:
    """An editor or admin. A reviewer gets 403 role_forbidden."""
    if user.role not in ("editor", "admin"):
        raise ApiError(403, "role_forbidden", "Only an editor or admin can do this.")
    return user


@router.get("/me", operation_id="getCurrentUser", tags=["common"])
def get_me(user: User = Depends(current_user)) -> dict[str, Any]:
    """The calling user."""
    return views.user_json(user)


@router.get("/products", operation_id="listProducts", tags=["device"])
def list_products(session: Session = Depends(get_session), _: User = Depends(current_user)) -> dict[str, Any]:
    """All products, oldest first."""
    products = session.scalars(select(Product).order_by(Product.created_at, Product.product_id)).all()
    return {"items": [views.product_summary(session, p) for p in products]}


@router.post("/products", operation_id="registerProduct", status_code=201, tags=["device"])
def register_product(
    body: ProductCreate, session: Session = Depends(get_session), user: User = Depends(writer)
) -> dict[str, Any]:
    """Register a product (creates version 1)."""
    data = body.model_dump()
    market = data.pop("intended_market")
    product, _ = create_product(session, user.user_id, data, market)
    return views.product_detail(session, product)


@router.get("/products/{product_id}", operation_id="getProduct", tags=["device"])
def get_product(product_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)) -> dict:
    """Product with its current record, latest templates and latest label versions."""
    return views.product_detail(session, views.require_product(session, product_id))


@router.get("/products/{product_id}/versions", operation_id="listProductVersions", tags=["device"])
def list_product_versions(
    product_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """Every product version, oldest first."""
    views.require_product(session, product_id)
    rows = session.scalars(
        select(ProductVersion).where(ProductVersion.product_id == product_id).order_by(ProductVersion.version)
    ).all()
    return {"product_id": product_id, "versions": [views.product_version_json(r) for r in rows]}


@router.post("/products/{product_id}/templates", operation_id="registerTemplate", status_code=201, tags=["device"])
def register_template_route(
    product_id: str, body: TemplateCreate, session: Session = Depends(get_session), user: User = Depends(writer)
) -> dict[str, Any]:
    """Register a template, or the next version of an existing one. Shape is validated, layout is not (yet)."""
    row = register_template(
        session,
        user.user_id,
        product_id,
        body.size_mm.model_dump(),
        [s.to_json() for s in body.slots],
        body.background,
        body.min_font_pt,
        body.template_id,
    )
    return views.template_json(row)


@router.get("/templates/{template_id}", operation_id="getTemplate", tags=["device"])
def get_template(
    template_id: str,
    version: int | None = None,
    session: Session = Depends(get_session),
    _: User = Depends(current_user),
) -> dict[str, Any]:
    """One template version, the latest unless `version` is given."""
    stmt = select(LabelTemplate).where(LabelTemplate.template_id == template_id)
    if version is not None:
        stmt = stmt.where(LabelTemplate.version == version)
    row = session.scalars(stmt.order_by(LabelTemplate.version.desc())).first()
    if row is None:
        raise ApiError(404, "not_found", f"No template {template_id!r} (version {version}).")
    return views.template_json(row)


@router.get("/products/{product_id}/history", operation_id="getProductHistory", tags=["device"])
def get_product_history(
    product_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """Audit trail for a product and everything under it, newest first."""
    views.require_product(session, product_id)
    return {
        "product_id": product_id,
        "items": [views.audit_json(e) for e in views.product_history(session, product_id)],
    }


@router.get("/labels/{label_id}/versions", operation_id="listLabelVersions", tags=["device"])
def list_label_versions(
    label_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """All artwork versions of one label family, oldest first."""
    rows = session.scalars(
        select(LabelVersion).where(LabelVersion.label_id == label_id).order_by(LabelVersion.artwork_version)
    ).all()
    if not rows:
        raise ApiError(404, "not_found", f"No label {label_id!r}.")
    return {"label_id": label_id, "versions": [views.label_version_json(session, r) for r in rows]}


def require_version(session: Session, version_id: str) -> LabelVersion:
    """Return the label version or raise 404."""
    row = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
    if row is None:
        raise ApiError(404, "not_found", f"No label version {version_id!r}.")
    return row


@router.get("/label-versions/{version_id}", operation_id="getLabelVersion", tags=["device"])
def get_label_version(
    version_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """One label version with its derived status."""
    return views.label_version_json(session, require_version(session, version_id))


@router.post("/changes", operation_id="assessChange", status_code=201, tags=["device"])
def assess_change(
    body: ChangeCreate, request: Request, session: Session = Depends(get_session), user: User = Depends(writer)
) -> dict[str, Any]:
    """Parse a change (structured `edits`, or `raw_text` through the rules parser), create it and assess its impact.

    The response has `parser: rules` (or `llm`). It keeps `parser: not_implemented` when nothing could be assessed,
    and says so, so an empty affected list is never mistaken for "nothing is affected" (docs/CHANGE_SPEC.md).
    """
    return changes.create_assessed_change(
        session, user.user_id, body, request.app.state.checker_settings, request.app.state.edit_provider
    )


@router.post("/changes/{change_id}/confirm", operation_id="confirmChange", tags=["device"])
def confirm_change(
    change_id: str, body: ChangeConfirmCreate, request: Request, session: Session = Depends(get_session),
    user: User = Depends(writer),
) -> Any:
    """Confirm the parsed change and the checklist decisions (append-only). No stored assessment: the mock."""
    if session.get(ChangeRequest, change_id) is None:
        raise ApiError(404, "not_found", f"No change {change_id!r}.")
    if changes.latest_assessment(session, change_id) is None:
        from src.api.mock_server import mock_response  # imported here: mock_server imports this module

        return mock_response("confirmChange", request)
    return changes.confirm_change(session, user.user_id, change_id, body)


@router.get("/changes/{change_id}/affected", operation_id="listAffectedLabels", tags=["device"])
def list_affected_labels(
    change_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """Items of the latest stored assessment with their current decisions. A change without one keeps the mock."""
    if session.get(ChangeRequest, change_id) is None:
        raise ApiError(404, "not_found", f"No change {change_id!r}.")
    row = changes.latest_assessment(session, change_id)
    if row is None:
        from src.api.mock_server import mock_response

        return mock_response("listAffectedLabels", request)
    return {"change_id": change_id, "items": changes.affected_items(session, row)}


@router.get("/changes/{change_id}", operation_id="getChange", tags=["device"])
def get_change(
    change_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """A change with its derived status, `closed` flag and latest_review_id."""
    row = session.get(ChangeRequest, change_id)
    if row is None:
        raise ApiError(404, "not_found", f"No change {change_id!r}.")
    return views.change_json(session, row)


@router.get("/label-versions/{version_id}/reviews", operation_id="listReviews", tags=["device"])
def list_reviews(
    version_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """Review decisions for one version, oldest first."""
    require_version(session, version_id)
    rows = session.scalars(select(Review).where(Review.version_id == version_id).order_by(Review.seq)).all()
    return {"version_id": version_id, "items": [views.review_json(r) for r in rows]}


@router.post("/label-versions/{version_id}/reviews", operation_id="reviewArtwork", status_code=201, tags=["device"])
def review_artwork(
    version_id: str, body: ReviewCreate, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> dict[str, Any]:
    """Approve, return or reject. The rules (role, self approval, hash, passed check) live in reviews.py."""
    review = record_review(
        session, user.user_id, version_id, body.decision, body.artifact_sha256, body.comment, body.check_id
    )
    return views.review_json(review)


# ---------------------------------------------------------------- checker (Step 21c)


def _start_check(
    kind: str, version_id: str, body: InspectCreate | None, background: BackgroundTasks, request: Request,
    session: Session, user: User,
) -> JSONResponse:
    """Shared body of inspectLabel and recheckArtwork.

    200 with the CheckResult when the version already has a stored extraction (only the rules run, which is
    fast). 202 with a Job when the extraction must be computed first: the job reads the image, stores the
    extraction, runs the checker and ends with a result_url.
    """
    version = require_version(session, version_id)
    if kind == "self_check" and (version.kind != "generated" or not version.artifact_sha256):
        raise ApiError(409, "not_generated", "Only generated artwork with an artifact hash can be re-checked.")
    try:
        override = body.retrieval.overrides() if body and body.retrieval else None
    except ValueError as error:
        raise ApiError(422, "validation_error", str(error)) from error
    settings = checks.retrieval_for(request.app.state.checker_settings, override)
    stored = checks.latest_extraction(session, version_id)
    if stored is not None:
        from src.common.schemas import LabelExtraction

        row = checks.perform_check(
            session, kind, version, LabelExtraction.model_validate(stored.payload), settings, user.user_id
        )
        return JSONResponse(checks.check_result_json(row), status_code=200)
    job = checks.new_job(session, checks.JOB_KINDS[kind], version_id, user.user_id)
    background.add_task(checks.run_check_job, request.app, job.job_id, kind, version_id, user.user_id, settings)
    return JSONResponse(checks.job_json(job), status_code=202)


@router.post("/label-versions/{version_id}/inspect", operation_id="inspectLabel", tags=["device"])
def inspect_label(
    version_id: str, request: Request, background: BackgroundTasks, body: InspectCreate | None = None,
    session: Session = Depends(get_session), user: User = Depends(current_user),
) -> JSONResponse:
    """Compare the extraction with the product record and retrieved requirements (rules decide, retrieval cites)."""
    return _start_check("inspection", version_id, body, background, request, session, user)


@router.post("/label-versions/{version_id}/recheck", operation_id="recheckArtwork", tags=["device"])
def recheck_artwork(
    version_id: str, request: Request, background: BackgroundTasks,
    session: Session = Depends(get_session), user: User = Depends(current_user),
) -> JSONResponse:
    """Closed-loop self-check of generated artwork: read the rendered image back and run the checker on it."""
    return _start_check("self_check", version_id, None, background, request, session, user)


@router.get("/jobs/{job_id}", operation_id="getJob", tags=["common"])
def get_job(job_id: str, request: Request, session: Session = Depends(get_session)) -> Any:
    """Current state of a job. Job ids that were never issued by this server fall back to the mock job (X-Mock)."""
    row = checks.latest_job(session, job_id)
    if row is not None:
        return checks.job_json(row)
    if checks.REAL_JOB_ID.match(job_id):  # the form this server issues, so an unknown one really is unknown
        raise ApiError(404, "not_found", f"No job {job_id!r}.")
    from src.api.mock_server import mock_response  # imported here: mock_server imports this module

    return mock_response("getJob", request)


@router.get("/check-results/{check_id}", operation_id="getCheckResult", tags=["device"])
def get_check_result(
    check_id: str, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> dict[str, Any]:
    """One stored CheckResult (the result_url of a finished inspect or re-check job)."""
    row = session.scalars(select(CheckResult).where(CheckResult.check_id == check_id)).first()
    if row is None:
        raise ApiError(404, "not_found", f"No check result {check_id!r}.")
    return checks.check_result_json(row)


@router.post("/search", operation_id="searchEvidence", tags=["device", "public"])
def search_evidence(body: SearchCreate, request: Request) -> dict[str, Any]:
    """Retrieve requirement passages for one module. No header needed. The response echoes the retrieval config used."""
    try:
        override = body.retrieval.overrides() if body.retrieval else None
    except ValueError as error:
        raise ApiError(422, "validation_error", str(error)) from error
    settings = request.app.state.checker_settings
    return checks.search(settings, body.module, body.query, body.k, body.section_level, override)


PUBLIC_BASED_ON = "21 CFR Parts 201, 208 and 211 (no product label text is used yet)"


def _ask(request: Request, question: str, module: str) -> Any:
    """Run the RAG pipeline for one module. 503 when the frozen retrieval cannot be built."""
    from src.rag.service import RetrievalUnavailable

    try:
        return request.app.state.rag.ask(question, module)
    except RetrievalUnavailable as error:
        raise ApiError(503, "retrieval_unavailable", str(error)) from error


@router.post("/public/ask", operation_id="askPublic", tags=["public"])
def ask_public(body: PublicQuestion, request: Request) -> dict[str, Any]:
    """Cited answer from 21 CFR 201, 208 and 211, or an abstention. Works with the language model off (extractive)."""
    result = _ask(request, body.question, "medicine")
    return result.to_wire(based_on=f"{PUBLIC_BASED_ON}; product {body.product_id}")


@router.post("/ask", operation_id="askProfessional", tags=["device"])
def ask_professional(body: ProfessionalQuestion, request: Request) -> dict[str, Any]:
    """Cited answer from the device regulations (21 CFR 8xx), or an abstention. No header needed."""
    return _ask(request, body.question, "device").to_wire(banner=False)
