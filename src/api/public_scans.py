"""Public photo scans (CR-27): rows, the 202 job and the result view. Open to anyone, no user, no product.

Flow: `publicScan` validates and stores the photo and answers 202 with a Job of kind `public_scan`. The job
(a) renders page 1 of a PDF, (b) runs the photo-quality gate on photos (a rejected photo ends in `retake_photo`),
(c) reads every text line in a child process under the CV4b time budget, (d) matches candidate strings with the
medicine matcher and stores the PublicMatchResult. Rows are append-only like `scans` and `jobs`.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import checks, public_scan, uploads
from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.extractor import ExtractorUnavailable
from src.api.models import PublicScan
from src.api.store import new_id

MAX_RUNNING = 2  # a public scan uses a CPU for up to a minute; more than this at once is answered with 429
SLOTS = threading.BoundedSemaphore(MAX_RUNNING)
PUBLIC_USER = "public"  # Job.created_by for an anonymous request
REAL_PUBLIC_SCAN_ID = r"^pscn_[0-9a-f]{8}$"


def latest(session: Session, scan_id: str) -> PublicScan | None:
    """The newest row (current state) of one public scan."""
    stmt = select(PublicScan).where(PublicScan.scan_id == scan_id).order_by(PublicScan.seq.desc())
    return session.scalars(stmt).first()


def add_row(session: Session, upload: uploads.CheckedUpload | None, stored_path: str, *, scan_id: str | None = None,
            state: str = "queued", job_id: str | None = None, result: dict[str, Any] | None = None,
            error: dict[str, Any] | None = None, seconds: float | None = None) -> PublicScan:
    """Append a row. The first row (no `scan_id`) comes from the upload, later rows carry the first row over."""
    now = utcnow()
    if scan_id is None:
        assert upload is not None
        row = PublicScan(scan_id=new_id("pscn"), mime=upload.mime, sha256=upload.sha256, stored_path=stored_path,
                         state=state, job_id=job_id, created_at=now, updated_at=now)
    else:
        first = latest(session, scan_id)
        assert first is not None
        row = PublicScan(scan_id=scan_id, job_id=job_id or first.job_id, mime=first.mime, sha256=first.sha256,
                         stored_path=first.stored_path, state=state, result=result, error=error, seconds=seconds,
                         created_at=first.created_at, updated_at=now)
    session.add(row)
    session.commit()
    return row


def result_json(row: PublicScan) -> dict[str, Any]:
    """The body of getPublicScan for a done scan."""
    assert row.result is not None
    return row.result


def try_acquire() -> None:
    """Take a running slot or answer 429 busy (the slot is given back when the job ends)."""
    if not SLOTS.acquire(blocking=False):
        raise ApiError(429, "busy", f"{MAX_RUNNING} photos are being read already. Try again in a minute.")


def release() -> None:
    """Give a running slot back (safe to call once per successful `try_acquire`)."""
    SLOTS.release()


def run_job(app: Any, job_id: str, scan_id: str) -> None:
    """Background body of a 202 public scan; always ends the job and the scan in `done` or `failed`."""
    started = time.monotonic()
    try:
        with app.state.session_factory() as session:
            try:
                row = latest(session, scan_id)
                assert row is not None
                checks.advance_job(session, job_id, "processing", 0.1, "checking the photo")
                add_row(session, None, "", scan_id=scan_id, state="processing")
                stored = uploads.resolve_stored(checks.files_dir(), row.stored_path)
                raster = stored
                if row.mime == "application/pdf":
                    raster = stored.with_name(stored.stem + ".page1.png")
                    if not raster.exists():
                        uploads.render_pdf_page(stored, raster)
                else:
                    report = app.state.quality_gate(raster)
                    if not report.ok:
                        _fail(session, job_id, scan_id, report.error_body(app.state.quality_thresholds), started)
                        return
                checks.advance_job(session, job_id, "processing", 0.3, "reading the text on the pack")
                try:
                    outcome = public_scan.scan_photo(raster, app.state.medicine, public_scan.load_config(),
                                                     read=getattr(app.state, "public_reader", None))
                except ApiError:
                    raise
                except (ImportError, OSError, ExtractorUnavailable) as error:
                    _fail(session, job_id, scan_id,
                          {"error": "retrieval_unavailable", "message": f"public scan is not available: {error}"},
                          started)
                    return
                add_row(session, None, "", scan_id=scan_id, state="done", result=outcome.body,
                        seconds=round(time.monotonic() - started, 2))
                checks.advance_job(session, job_id, "done", 1.0, result_url=f"/public/scans/{scan_id}")
            except ApiError as error:
                _fail(session, job_id, scan_id, error.body(), started)
            except Exception as error:  # a job must end in a state a client can read
                _fail(session, job_id, scan_id,
                      {"error": "scan_failed", "message": f"{type(error).__name__}: {error}"}, started)
    finally:
        release()


def _fail(session: Session, job_id: str, scan_id: str, error: dict[str, Any], started: float) -> None:
    """End job and scan in `failed` with the same contract Error."""
    add_row(session, None, "", scan_id=scan_id, state="failed", error=error,
            seconds=round(time.monotonic() - started, 2))
    checks.advance_job(session, job_id, "failed", 1.0, error=error)
