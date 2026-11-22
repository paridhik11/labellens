"""The real endpoints (Step 20b). Every other operation in openapi.yaml is served from mock JSON (mock_server.py).

Roles (X-User-Id header stub): editor or admin register products, templates and changes; reviewer or admin
review. Reads need a known user.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Path, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import (
    artwork,
    ask_jobs,
    changes,
    checks,
    live_jobs,
    medicine,
    pages,
    printverify,
    public_scans,
    publish,
    scans,
    uploads,
    views,
)
from src.api.errors import ApiError
from src.api.models import (
    ChangeRequest,
    CheckResult,
    GeneratedArtwork,
    LabelTemplate,
    LabelVersion,
    PrintVerification,
    Product,
    ProductVersion,
    Review,
    User,
)
from src.api.requests import (
    ChangeConfirmCreate,
    ChangeCreate,
    ExtractionConfirmCreate,
    GenerateCreate,
    InspectCreate,
    LiveFetchCreate,
    LiveSearchCreate,
    MedicineMatchCreate,
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
        "uploadScan",
        "getScan",
        "getExtraction",
        "confirmExtraction",
        "listLabelVersions",
        "getLabelVersion",
        "assessChange",
        "confirmChange",
        "listAffectedLabels",
        "getChange",
        "generateArtwork",
        "getArtwork",
        "getExports",
        "downloadArtifact",
        "listReviews",
        "reviewArtwork",
        "inspectLabel",
        "recheckArtwork",
        "getJob",
        "getCheckResult",
        "searchEvidence",
        "askPublic",
        "askProfessional",
        "publishVersion",
        "verifyPrint",
        "getPrintVerification",
        "listPrintVerifications",
        "matchMedicine",
        "publicScan",
        "getPublicScan",
        "searchLiveMedicine",
        "fetchLiveLabel",
        "getLiveProduct",
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


# ---------------------------------------------------------------- upload, scan, extraction (Step 24a)


@router.post("/scans", operation_id="uploadScan", status_code=202, tags=["device"])
async def upload_scan(
    request: Request, background: BackgroundTasks, file: UploadFile = File(...),  # noqa: B008
    source: str = Form(...),
    product_id: str | None = Form(None), session: Session = Depends(get_session), user: User = Depends(writer),
) -> JSONResponse:
    """Accept a PNG, JPEG or PDF of a device label and answer 202 with a Job; the job runs the extractor.

    The file is checked by its first bytes (never its name or Content-Type), capped at 15 MB and 40 megapixels,
    and stored as uploads/<sha256>.<ext>. `product_id` is required for now: a scan creates a label version,
    and a version belongs to a product (docs/contracts/SCHEMA_CHANGE_REQUESTS.md, CR-20).
    """
    if source not in ("upload", "camera"):
        raise ApiError(422, "validation_error", "source must be 'upload' or 'camera'.")
    if not product_id:
        raise ApiError(422, "validation_error", "product_id is required: a scan creates a version of its label.")
    views.require_product(session, product_id)
    data = await file.read(uploads.MAX_BYTES + 1)  # never read more than the cap plus one byte
    upload = uploads.validate_upload(data)
    stored = uploads.store_bytes(checks.files_dir(), upload, data)
    scan = scans.add_scan(session, user.user_id, upload, stored, source, product_id)
    job = checks.new_job(session, "scan", None, user.user_id, result_url=f"/scans/{scan.scan_id}")
    scans.advance_scan(session, scan.scan_id, "queued", job_id=job.job_id)
    background.add_task(scans.run_scan_job, request.app, job.job_id, scan.scan_id, user.user_id)
    return JSONResponse(checks.job_json(job), status_code=202)


@router.get("/scans/{scan_id}", operation_id="getScan", tags=["device"])
def get_scan(
    scan_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """Scan state. label_id and version_id are set when done. Ids this server never issued fall back to the mock."""
    row = scans.latest_scan(session, scan_id)
    if row is not None:
        return scans.scan_json(row)
    if scans.REAL_SCAN_ID.match(scan_id):
        raise ApiError(404, "not_found", f"No scan {scan_id!r}.")
    from src.api.mock_server import mock_response  # imported here: mock_server imports this module

    return mock_response("getScan", request)


@router.get("/label-versions/{version_id}/extraction", operation_id="getExtraction", tags=["device"])
def get_extraction(
    version_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """The newest extraction of a version that came from a scan, with its unclear fields and confirmation state."""
    row = scans.scan_extraction(session, version_id)
    if row is not None:
        return scans.extraction_json(session, row, request.app.state.checker_settings)
    if scans.REAL_VERSION_ID.match(version_id) and scans.version_exists(session, version_id):
        raise ApiError(404, "not_found", f"Version {version_id!r} has no extraction from a scan.")
    if scans.REAL_VERSION_ID.match(version_id):
        raise ApiError(404, "not_found", f"No label version {version_id!r}.")
    from src.api.mock_server import mock_response

    return mock_response("getExtraction", request)


@router.post("/label-versions/{version_id}/extraction/confirm", operation_id="confirmExtraction", tags=["device"])
def confirm_extraction(
    version_id: str, body: ExtractionConfirmCreate, request: Request, session: Session = Depends(get_session),
    user: User = Depends(writer),
) -> Any:
    """Confirm or correct the extracted fields (append-only: a new extraction row and a confirmation row)."""
    row = scans.scan_extraction(session, version_id)
    if row is not None:
        return scans.confirm_extraction(session, user.user_id, row, body.fields, request.app.state.checker_settings)
    if scans.REAL_VERSION_ID.match(version_id):
        raise ApiError(404, "not_found", f"Version {version_id!r} has no extraction from a scan.")
    from src.api.mock_server import mock_response

    return mock_response("confirmExtraction", request)


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


# ---------------------------------------------------------------- generate, artwork, export (Step 24b)


@router.post("/changes/{change_id}/generate", operation_id="generateArtwork", status_code=202, tags=["device"])
def generate_artwork(
    change_id: str, body: GenerateCreate, request: Request, background: BackgroundTasks,
    session: Session = Depends(get_session), user: User = Depends(writer),
) -> JSONResponse:
    """Fill the label's template with the confirmed values and answer 202 with a Job; the job renders and stores.

    Everything that can be refused is refused here, before a job exists: closed change, unconfirmed assessment,
    NEEDS_INPUT (never invents an identifier), layout failure. A new draft version is appended, never an edit.
    """
    plan = artwork.prepare(session, request.app.state.artwork_engine, user, change_id, body.label_id, body.test_data)
    job = checks.new_job(session, "generate", None, user.user_id, result_url=f"/artworks/{plan.artwork_id}")
    background.add_task(artwork.run_generate_job, request.app, job.job_id, plan)
    return JSONResponse(checks.job_json(job), status_code=202)


@router.get("/artworks/{artwork_id}", operation_id="getArtwork", tags=["device"])
def get_artwork(
    artwork_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """A generated DRAFT artwork. Ids this server never issued fall back to the mock."""
    row = session.scalars(select(GeneratedArtwork).where(GeneratedArtwork.artwork_id == artwork_id)).first()
    if row is not None:
        return artwork.artwork_json(session, row)
    if artwork.REAL_ARTWORK_ID.match(artwork_id):
        raise ApiError(404, "not_found", f"No artwork {artwork_id!r}.")
    from src.api.mock_server import mock_response

    return mock_response("getArtwork", request)


@router.get("/label-versions/{version_id}/exports", operation_id="getExports", tags=["device"])
def get_exports(
    version_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """PDF, SVG and report of a generated version (the stored drafts, DRAFT mark included)."""
    version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
    if version is None:
        if scans.REAL_VERSION_ID.match(version_id):
            raise ApiError(404, "not_found", f"No label version {version_id!r}.")
        from src.api.mock_server import mock_response

        return mock_response("getExports", request)
    return artwork.export_json(session, version)


@router.get("/artifacts/{artifact_sha256}", operation_id="downloadArtifact", tags=["device"])
def download_artifact(
    artifact_sha256: str = Path(pattern=r"^[0-9a-f]{64}$"), session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Response:
    """Download one stored file by its sha256. The file is re-hashed first, so a changed file is never served."""
    return artwork.download(session, user, artifact_sha256)


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


@router.post("/label-versions/{version_id}/publish", operation_id="publishVersion", status_code=201, tags=["device"])
def publish_version_route(
    version_id: str, response: Response, session: Session = Depends(get_session), user: User = Depends(current_user)
) -> dict[str, Any]:
    """Publish an approved version: a PublishedPage pinned to this version_id (201). A repeat call answers 200."""
    page, created = publish.publish_version(session, user.user_id, version_id)
    response.status_code = 201 if created else 200
    return page


@router.get("/versions/{version_id}", include_in_schema=False)
def public_version_page(version_id: str, session: Session = Depends(get_session)) -> HTMLResponse:
    """The public page a published label's QR opens. 404 for a version that was never published."""
    body = publish.public_page_html(session, version_id)
    if body is None:
        return HTMLResponse("<!doctype html><title>Not found</title><p>This label version is not published.</p>", 404)
    return HTMLResponse(body)


@router.get("/versions/{version_id}/label.pdf", include_in_schema=False)
def public_version_pdf(version_id: str, session: Session = Depends(get_session)) -> Response:
    """The approved PDF of a published version (re-hashed before it is sent)."""
    return Response(
        publish.published_pdf(session, version_id), media_type="application/pdf",
        headers={"X-Content-Type-Options": "nosniff", "Content-Disposition": f'inline; filename="{version_id}.pdf"'},
    )


# ---------------------------------------------------------------- print verification (Step 25b)


@router.post("/label-versions/{version_id}/print-verifications", operation_id="verifyPrint", status_code=202,
             tags=["device"])
async def verify_print_route(
    version_id: str, request: Request, background: BackgroundTasks, photo: UploadFile = File(...),  # noqa: B008
    condition: str = Form(...), session: Session = Depends(get_session), user: User = Depends(current_user),
) -> JSONResponse:
    """Accept a photo of a printed label and answer 202 with a Job; the job compares it with the approved version.

    Refused before any job: a version that is not approved (409 not_approved, rejected, version_superseded,
    no_reference), an unknown condition or a file that is not a PNG or JPEG (422).
    """
    version = require_version(session, version_id)
    data = await photo.read(uploads.MAX_BYTES + 1)
    upload, stored, verification_id = printverify.accept(session, user.user_id, version, condition, data)
    job = checks.new_job(session, "print_verify", version_id, user.user_id,
                         result_url=f"/print-verifications/{verification_id}")
    background.add_task(printverify.run_verify_job, request.app, job.job_id, verification_id, version_id, user.user_id,
                        stored, upload.mime, upload.sha256, condition)
    return JSONResponse(checks.job_json(job), status_code=202)


@router.get("/label-versions/{version_id}/print-verifications", operation_id="listPrintVerifications", tags=["device"])
def list_print_verifications(
    version_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """Print verifications of one version, oldest first. Ids this server never issued keep the mock."""
    if printverify.require_real_version(session, version_id) is None:
        from src.api.mock_server import mock_response

        return mock_response("listPrintVerifications", request)
    return {"version_id": version_id,
            "items": [printverify.verification_json(r) for r in printverify.list_for(session, version_id)]}


@router.get("/print-verifications/{verification_id}", operation_id="getPrintVerification", tags=["device"])
def get_print_verification(
    verification_id: str, request: Request, session: Session = Depends(get_session), _: User = Depends(current_user)
) -> Any:
    """One stored print verification. Ids this server never issued keep the mock."""
    row = session.scalars(select(PrintVerification).where(
        PrintVerification.verification_id == verification_id)).first()
    if row is not None:
        return printverify.verification_json(row)
    if printverify.REAL_VERIFICATION_ID.match(verification_id):
        raise ApiError(404, "not_found", f"No print verification {verification_id!r}.")
    from src.api.mock_server import mock_response

    return mock_response("getPrintVerification", request)


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
        result = ask_jobs.stored_result(session, job_id) if row.kind == "ask" and row.state == "done" else None
        return checks.job_json(row, result)
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


def _ask_job(
    request: Request, background: BackgroundTasks, session: Session, question: str, module: str, product_id: str | None,
) -> JSONResponse:
    """Start the optional AI answer (CR-21) as a 202 job. The job falls back to the extractive passages."""
    job = checks.new_job(session, "ask", None, "anonymous")
    background.add_task(ask_jobs.run_ask_job, request.app, job.job_id, question, module, product_id)
    return JSONResponse(checks.job_json(job), status_code=202)


def _ask_mode(mode: str) -> str:
    """Validate the optional mode query flag (extractive is the default)."""
    if mode not in ("extractive", "ai"):
        raise ApiError(422, "validation_error", "mode must be extractive or ai.")
    return mode


@router.post("/public/ask", operation_id="askPublic", tags=["public"])
def ask_public(
    body: PublicQuestion, request: Request, background: BackgroundTasks, mode: str = "extractive",
    session: Session = Depends(get_session),
) -> Any:
    """Cited answer from 21 CFR 201, 208 and 211, or an abstention. Extractive by default (instant, no model).

    `mode=ai` starts a 202 job that asks the language model and falls back to the extractive passages.
    """
    if _ask_mode(mode) == "ai":
        return _ask_job(request, background, session, body.question, "medicine", body.product_id)
    service = request.app.state.medicine
    if request.app.state.live.knows(body.product_id):  # a label fetched live from DailyMed (CR-28)
        return _ask_live(request, body.question, body.product_id)
    if service.knows(body.product_id):  # a reference product: answer from its own label chunks (CR-23)
        rag = request.app.state.rag
        result = _ask_product(service, body.question, body.product_id, rag.provider, rag.settings)
        return result.to_wire(based_on=medicine.based_on(service.catalog.products[body.product_id]))
    result = _ask(request, body.question, "medicine")
    return result.to_wire(based_on=f"{PUBLIC_BASED_ON}; product {body.product_id}")


def _ask_live(request: Request, question: str, product_id: str) -> Any:
    """Extractive answer from one live label, every citation checked against the label text (CR-28)."""
    live, rag = request.app.state.live, request.app.state.rag
    try:
        result, label = live.ask(question, product_id, rag.provider, rag.settings)
    except Exception as error:  # models missing or the cached label is damaged
        raise ApiError(503, "retrieval_unavailable", f"live label retrieval is not available: {error}") from error
    return live.wire(result, label)


def _ask_product(service: Any, question: str, product_id: str, provider: Any, settings: Any) -> Any:
    """Answer from one reference product's chunks. 503 when the retrieval models cannot be loaded."""
    try:
        return service.ask(question, product_id, provider, settings)
    except Exception as error:  # model files missing, offline cache incomplete
        raise ApiError(503, "retrieval_unavailable", f"medicine retrieval is not available: {error}") from error


@router.post("/public/match", operation_id="matchMedicine", tags=["public"])
def match_medicine(body: MedicineMatchCreate, request: Request) -> Any:
    """Match a product name to the nearest of the ten reference products, or answer `no_reference_match` (CR-23)."""
    service = request.app.state.medicine
    try:
        return medicine.match_result(service.catalog, service.matcher, body.product_name)
    except Exception as error:  # the E5b models could not be loaded (offline cache missing)
        raise ApiError(503, "retrieval_unavailable", f"medicine matching is not available: {error}") from error


@router.post("/public/scans", operation_id="publicScan", status_code=202, tags=["public"])
async def public_scan(
    request: Request, background: BackgroundTasks, file: UploadFile = File(...),  # noqa: B008
) -> JSONResponse:
    """Accept a photo (PNG, JPEG or a PDF page) of a medicine pack and answer 202 with a public_scan Job (CR-27).

    No login. The file is checked by its first bytes, capped at 15 MB and 40 megapixels. At most two photos are
    read at once; another is answered with 429 `busy`. Poll GET /jobs/{job_id}, then GET /public/scans/{scan_id}.
    """
    data = await file.read(uploads.MAX_BYTES + 1)
    upload = uploads.validate_upload(data)
    public_scans.try_acquire()
    try:
        session: Session = request.app.state.session_factory()
        with session:
            stored = uploads.store_bytes(checks.files_dir(), upload, data)
            row = public_scans.add_row(session, upload, stored)
            job = checks.new_job(session, "public_scan", None, public_scans.PUBLIC_USER,
                                 result_url=f"/public/scans/{row.scan_id}")
            public_scans.add_row(session, None, "", scan_id=row.scan_id, job_id=job.job_id)
            body = checks.job_json(job)
    except BaseException:
        public_scans.release()
        raise
    background.add_task(public_scans.run_job, request.app, job.job_id, row.scan_id)
    return JSONResponse(body, status_code=202)


@router.get("/public/scans/{scan_id}", operation_id="getPublicScan", tags=["public"])
def get_public_scan(scan_id: str, request: Request, session: Session = Depends(get_session)) -> Any:
    """The match result of a finished public scan. 409 while it runs or after it failed (the Error says why)."""
    row = public_scans.latest(session, scan_id)
    if row is not None:
        if row.state == "done":
            return public_scans.result_json(row)
        if row.state == "failed" and row.error:
            return JSONResponse(row.error, status_code=409)
        raise ApiError(409, "scan_not_ready", "The photo is still being read. Poll the job first.")
    if re.match(public_scans.REAL_PUBLIC_SCAN_ID, scan_id):
        raise ApiError(404, "not_found", f"No public scan {scan_id!r}.")
    from src.api.mock_server import mock_response  # imported here: mock_server imports this module

    return mock_response("getPublicScan", request)


@router.post("/public/live/search", operation_id="searchLiveMedicine", tags=["public"])
def search_live_medicine(body: LiveSearchCreate, request: Request) -> Any:
    """List DailyMed human drug labels with this name (CR-28). A list to pick from, never a ranking or a match.

    Offline or a DailyMed error is a 200 with outcome `unavailable` and a plain message: the 30 curated medicines
    keep working, nothing is mocked.
    """
    return request.app.state.live.search(body.product_name)


@router.post("/public/live/fetch", operation_id="fetchLiveLabel", status_code=202, tags=["public"])
def fetch_live_label(
    body: LiveFetchCreate, request: Request, background: BackgroundTasks, session: Session = Depends(get_session),
) -> JSONResponse:
    """Fetch the label the person picked, index it and cache it (202 Job of kind live_fetch, CR-28).

    Poll GET /jobs/{job_id}; a done job points at GET /public/live/products/{product_id}.
    """
    if not request.app.state.live.enabled:
        raise ApiError(503, "live_disabled", "Live lookup is switched off on this server.")
    live_jobs.try_acquire()
    try:
        job = checks.new_job(session, "live_fetch", None, public_scans.PUBLIC_USER)
        payload = checks.job_json(job)
    except BaseException:
        live_jobs.release()
        raise
    background.add_task(live_jobs.run_fetch_job, request.app, job.job_id, body.setid, body.version)
    return JSONResponse(payload, status_code=202)


@router.get("/public/live/products/{product_id}", operation_id="getLiveProduct", tags=["public"])
def get_live_product(product_id: str, request: Request) -> Any:
    """The reference page of a fetched live label: fields, sections and the live label info (CR-28)."""
    from src.api.live_dailymed import LiveFetchError, product_body

    try:
        label = request.app.state.live.load(product_id)
    except LiveFetchError as error:
        raise ApiError(404, "not_found", error.message) from error
    return product_body(label)


@router.get("/public/medicine", include_in_schema=False)
def medicine_page() -> HTMLResponse:
    """The small public medicine page (match a name, read the reference label, ask a question)."""
    return HTMLResponse(pages.MEDICINE_PAGE)


@router.post("/ask", operation_id="askProfessional", tags=["device"])
def ask_professional(
    body: ProfessionalQuestion, request: Request, background: BackgroundTasks, mode: str = "extractive",
    session: Session = Depends(get_session),
) -> Any:
    """Cited answer from the device regulations (21 CFR 8xx), or an abstention. No header needed. `mode=ai` as above."""
    if _ask_mode(mode) == "ai":
        return _ask_job(request, background, session, body.question, "device", None)
    return _ask(request, body.question, "device").to_wire(banner=False)
