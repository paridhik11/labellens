"""Scans, extraction and extraction confirmation (Step 24a).

Flow: `uploadScan` validates and stores the file and answers 202 with a Job. The job (a) renders page 1 of a PDF,
(b) runs the photo-quality gate on photos, (c) runs the extractor, and (d) only then creates the label version
(kind uploaded, family L1) and stores the extraction. A photo the gate rejects creates no label version, only a
scan row in state `failed` with the error `retake_photo`. Everything is append-only: scan state changes, jobs,
extractions and confirmations are new rows.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import checks, uploads
from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.extractor import ExtractorUnavailable
from src.api.models import Extraction, ExtractionConfirmation, LabelVersion, Scan
from src.api.store import add_label_version, current_product_version, new_id, record_audit
from src.checker.settings import CheckerSettings
from src.common.schemas import LabelExtraction

REAL_SCAN_ID = re.compile(r"^scn_[0-9a-f]{8}$")  # the form new_id("scn") issues; mock ids look like scn_0001
REAL_VERSION_ID = re.compile(r"^lbv_[0-9a-f]{8}$")
MAX_FIELD_CHARS = 500
PDF_RASTER_SUFFIX = ".page1.png"


# ---------------------------------------------------------------- scan rows


def latest_scan(session: Session, scan_id: str) -> Scan | None:
    """The newest row (current state) of one scan."""
    return session.scalars(select(Scan).where(Scan.scan_id == scan_id).order_by(Scan.seq.desc())).first()


def add_scan(
    session: Session, user_id: str, upload: uploads.CheckedUpload, stored_path: str, source: str, product_id: str
) -> Scan:
    """Append the first row of a scan (state queued). The job id is attached by the caller on the next row."""
    now = utcnow()
    row = Scan(
        scan_id=new_id("scn"), module="device", source=source, file_id=f"fil_{upload.sha256[:12]}", mime=upload.mime,
        sha256=upload.sha256, pages=upload.pages, stored_path=stored_path, product_id=product_id, state="queued",
        created_by=user_id, created_at=now, updated_at=now,
    )
    session.add(row)
    session.commit()
    return row


def advance_scan(
    session: Session, scan_id: str, state: str, *, job_id: str | None = None, label_id: str | None = None,
    version_id: str | None = None, error: dict[str, Any] | None = None,
) -> Scan:
    """Append a state change for an existing scan (every unset field is carried over)."""
    previous = latest_scan(session, scan_id)
    assert previous is not None
    row = Scan(
        scan_id=scan_id, job_id=job_id or previous.job_id, module=previous.module, source=previous.source,
        file_id=previous.file_id, mime=previous.mime, sha256=previous.sha256, pages=previous.pages,
        stored_path=previous.stored_path, product_id=previous.product_id, state=state,
        label_id=label_id or previous.label_id, version_id=version_id or previous.version_id, error=error,
        created_by=previous.created_by, created_at=previous.created_at, updated_at=utcnow(),
    )
    session.add(row)
    session.commit()
    return row


def scan_json(row: Scan) -> dict[str, Any]:
    """Serialize the current state of a scan (contract `Scan`)."""
    file_ref: dict[str, Any] = {"file_id": row.file_id, "mime": row.mime, "sha256": row.sha256}
    if row.pages:
        file_ref["pages"] = row.pages
    out: dict[str, Any] = {
        "scan_id": row.scan_id, "module": row.module, "source": row.source, "file": file_ref,
        "product_id": row.product_id, "state": row.state, "created_at": row.created_at,
    }
    for key in ("job_id", "label_id", "version_id", "error"):
        if getattr(row, key):
            out[key] = getattr(row, key)
    return out


# ---------------------------------------------------------------- the background job


def _fail(session: Session, job_id: str, scan_id: str, error: dict[str, Any]) -> None:
    """End job and scan in `failed` with the same contract Error."""
    advance_scan(session, scan_id, "failed", error=error)
    checks.advance_job(session, job_id, "failed", 1.0, error=error)


def run_scan_job(app: Any, job_id: str, scan_id: str, user_id: str) -> None:
    """Background body of a 202 upload: (render PDF), quality gate, extract, create the version, store the result.

    Any failure ends the job and the scan in state `failed` with the contract Error shape, never an unhandled
    exception. A photo rejected by the gate gets `retake_photo` and no label version.
    """
    with app.state.session_factory() as session:
        try:
            scan = latest_scan(session, scan_id)
            assert scan is not None
            files = checks.files_dir()
            checks.advance_job(session, job_id, "processing", 0.1, "checking the file")
            advance_scan(session, scan_id, "processing")
            stored = uploads.resolve_stored(files, scan.stored_path)
            raster = stored
            if scan.mime == "application/pdf":
                raster = stored.with_name(stored.stem + PDF_RASTER_SUFFIX)
                if not raster.exists():
                    uploads.render_pdf_page(stored, raster)
            else:  # the quality gate is for photographs; a rendered PDF page has no camera defects
                report = app.state.quality_gate(raster)
                if not report.ok:
                    _fail(session, job_id, scan_id, report.error_body(app.state.quality_thresholds))
                    return
            checks.advance_job(session, job_id, "processing", 0.4, "reading the label")
            extraction, mode = app.state.extractor(raster)
            version = add_label_version(
                session, user_id, scan.product_id, scan.stored_path, kind="uploaded",
                product_version=current_product_version(session, scan.product_id).version,
            )
            checks.store_extraction(session, version, extraction, mode, scan_id=scan_id)
            advance_scan(session, scan_id, "done", label_id=version.label_id, version_id=version.version_id)
            checks.advance_job(session, job_id, "done", 1.0, result_url=f"/scans/{scan_id}")
        except ApiError as error:
            _fail(session, job_id, scan_id, error.body())
        except ExtractorUnavailable as error:
            _fail(session, job_id, scan_id, {"error": "extractor_unavailable", "message": str(error)})
        except Exception as error:  # a job must end in a state a client can read
            _fail(session, job_id, scan_id, {"error": "scan_failed", "message": f"{type(error).__name__}: {error}"})


# ---------------------------------------------------------------- extraction view and confirmation


def unclear_fields(extraction: LabelExtraction, settings: CheckerSettings) -> list[str]:
    """Fields to confirm: no OCR line matches the field text, or the best match is below the confidence gate."""
    from src.cv.consistency import field_confidence

    out = []
    for name in extraction.fields:
        conf = field_confidence(extraction, name)
        if conf is None or conf < settings.min_ocr_confidence:
            out.append(name)
    return out


def latest_confirmation(session: Session, extraction_id: str) -> ExtractionConfirmation | None:
    """The confirmation that produced this extraction row, or None when the row is an original extraction."""
    stmt = select(ExtractionConfirmation).where(ExtractionConfirmation.extraction_id == extraction_id)
    return session.scalars(stmt).first()


def extraction_json(session: Session, row: Extraction, settings: CheckerSettings) -> dict[str, Any]:
    """Serialize an extraction row (contract `Extraction`): the LabelExtraction plus ids and confirmation state."""
    payload = LabelExtraction.model_validate(row.payload)
    out: dict[str, Any] = payload.model_dump(mode="json")
    out.update(extraction_id=row.extraction_id, scan_id=row.scan_id, version_id=row.version_id)
    confirmation = latest_confirmation(session, row.extraction_id)
    if confirmation is None:
        out["unclear_fields"] = unclear_fields(payload, settings)
        out["confirmed"] = False
    else:  # the confirmed values are the evidence now, so nothing is left unclear
        out["unclear_fields"] = []
        out.update(confirmed=True, confirmed_by=confirmation.confirmed_by, confirmed_at=confirmation.confirmed_at)
    return out


def scan_extraction(session: Session, version_id: str) -> Extraction | None:
    """The newest extraction of a version if it came from a scan (extractions made by an inspect job have no scan)."""
    row = checks.latest_extraction(session, version_id)
    return row if row is not None and row.scan_id else None


def confirm_extraction(
    session: Session, user_id: str, row: Extraction, fields: dict[str, str], settings: CheckerSettings
) -> dict[str, Any]:
    """Append the user's confirmed or corrected fields as a new extraction row plus a confirmation row.

    Only fields the extraction already has, or the six label fields, may be given (so a typo cannot add a new
    field), each at most 500 characters. Fields not submitted keep their extracted value. The original row stays.
    """
    from src.checker.synthetic import FIELD_ORDER

    payload = LabelExtraction.model_validate(row.payload)
    allowed = set(payload.fields) | set(FIELD_ORDER)
    unknown = sorted(set(fields) - allowed)
    if unknown:
        raise ApiError(422, "validation_error", f"Unknown field names: {', '.join(unknown)}.")
    too_long = sorted(k for k, v in fields.items() if len(v) > MAX_FIELD_CHARS)
    if too_long:
        raise ApiError(422, "validation_error", f"Values over {MAX_FIELD_CHARS} characters: {', '.join(too_long)}.")
    corrected = payload.model_copy(update={"fields": {**payload.fields, **{k: v.strip() for k, v in fields.items()}}})
    now = utcnow()
    new_row = Extraction(
        extraction_id=new_id("ext"), version_id=row.version_id, label_id=row.label_id, mode=row.mode,
        payload=corrected.model_dump(mode="json"), created_at=now, scan_id=row.scan_id,
    )
    session.add(new_row)
    session.add(ExtractionConfirmation(
        confirmation_id=new_id("cnf"), extraction_id=new_row.extraction_id, previous_extraction_id=row.extraction_id,
        version_id=row.version_id, fields=dict(fields), confirmed_by=user_id, confirmed_at=now,
    ))
    record_audit(session, user_id, "extraction.confirmed", "label_version", row.version_id,
                 details={"extraction_id": new_row.extraction_id, "fields": sorted(fields)}, at=now)
    session.commit()
    return extraction_json(session, new_row, settings)


def version_exists(session: Session, version_id: str) -> bool:
    """True when a label version with this id is stored."""
    return session.scalars(select(LabelVersion.seq).where(LabelVersion.version_id == version_id)).first() is not None
