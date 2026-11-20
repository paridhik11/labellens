"""Print verification (Step 25b, CR-26): photograph a printed label and compare it with its approved version.

The API owns the approval gate. `src.cv.verify_print` has its own gate too, but that gate binds an approval to the
sha256 of a legacy manifest file, while this API binds approval to the sha256 of the PDF (CR-22), so the two hashes can
never agree and nothing here fakes a record to satisfy it. The job instead runs the same three steps `verify_print`
runs after its gate (blind extraction with post-correction, `compare_fields`, `compare_extraction`) on the photo.

Expected content comes from the approved version only: the product record pinned to it and the barcode payload the
renderer encoded (stored with the generated artwork). Symbols are not compared: the detector is not trusted
(`CheckerSettings.symbol_detector_trusted`), so a symbol outcome could only be needs_human. The outcome mapping is
`MATCH` to match, `MISMATCH` to mismatch, `NEEDS_HUMAN_REVIEW` (or a photo that fails the quality gate) to
rescan_needed with a reason. Every result is an append-only row; a failing job ends in state `failed`.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import checks, scans, uploads
from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.extractor import ExtractorUnavailable
from src.api.models import GeneratedArtwork, LabelTemplate, LabelVersion, PrintVerification, ProductVersion, Review
from src.api.status import is_closed, label_version_status, latest_review, latest_version_of_change
from src.api.store import new_id, record_audit

REAL_VERIFICATION_ID = re.compile(r"^pv_[0-9a-f]{8}$")  # new_id("pv"); the mocks use other ids
CONDITIONS = ("clean_print_scan", "phone_photo", "blur", "glare")
AI = re.compile(r"\((\d{2})\)([^(]*)")


class PrintEngine(Protocol):
    """What the job needs from the CV side: compare one photo with the expected content."""

    def verify(self, photo: Path, expected: dict[str, Any]) -> dict[str, Any]:
        """Return {status, fields, issues, warnings, barcode}. Raises ExtractorUnavailable without the CV libraries."""
        ...


class RealPrintEngine:
    """Slot verification bound to the API-approved artwork's pinned template."""

    def verify(self, photo: Path, expected: dict[str, Any]) -> dict[str, Any]:
        """Verify pixels by template slots; missing binding must request a rescan."""
        if expected.get('template'):
            try:
                from src.cv.template_print import verify_template

                return verify_template(photo, expected)
            except ImportError as error:
                raise ExtractorUnavailable(f"CV libraries are not installed: {error}") from error
        return {'status': 'NEEDS_HUMAN_REVIEW', 'fields': [], 'issues': [], 'barcode': None,
                'warnings': ['TEMPLATE_BINDING_MISSING']}


# ---------------------------------------------------------------- the gate and the expected content


def gate(session: Session, version: LabelVersion) -> GeneratedArtwork:
    """Refuse unless the version is approved, current and generated. Returns its GeneratedArtwork.

    Codes (409): `change_closed`/`rejected` (a reject is terminal), `version_superseded`, `not_approved`
    (draft, checked, returned, or never reviewed), `no_reference` (approved but no generated artwork to compare with).
    """
    if version.change_id is not None:
        if is_closed(session, version.change_id):
            raise ApiError(409, "rejected", "This version's change was rejected, so no approved label exists.")
        latest = latest_version_of_change(session, version.change_id)
        if latest is not None and latest.version_id != version.version_id:
            raise ApiError(409, "version_superseded", "A newer version exists, so this approval no longer counts.",
                           {"latest_version_id": latest.version_id})
    review: Review | None = latest_review(session, version.version_id)
    if review is not None and review.decision == "reject":
        raise ApiError(409, "rejected", "This version was rejected, so there is no approved label to verify.")
    status = label_version_status(session, version.version_id)
    if status not in ("reviewed", "published"):
        raise ApiError(409, "not_approved", f"Only an approved version can be verified; this one is {status}.",
                       {"status": status})
    art = session.scalars(select(GeneratedArtwork).where(GeneratedArtwork.version_id == version.version_id)).first()
    if art is None or not (art.barcode_decision or {}).get("new_payload"):
        raise ApiError(409, "no_reference", "This version has no generated artwork to compare the print with.")
    return art


def expected_content(session: Session, version: LabelVersion, art: GeneratedArtwork) -> dict[str, Any]:
    """What the printed label must show: label text fields and the GS1 values of the encoded payload."""
    pv = session.scalars(select(ProductVersion).where(
        ProductVersion.product_id == version.product_id, ProductVersion.version == version.product_version)).first()
    extra = pv.extra or {}
    fields = {"product_name": pv.name, "manufacturer": pv.manufacturer, "manufacturer_address": pv.manufacturer_address,
              "model": pv.model, "lot": extra.get("lot", ""), "expiry": extra.get("expiry", "")}
    payload = art.barcode_decision["new_payload"]
    template = session.scalars(select(LabelTemplate).where(
        LabelTemplate.template_id == version.template_id,
        LabelTemplate.version == version.template_version)).first()
    return {"fields": {k: v for k, v in fields.items() if v}, "payload": payload,
            "barcode_ais": {ai: value for ai, value in AI.findall(payload)},
            "template": {"size_mm": {"w": template.size_w, "h": template.size_h},
                         "slots": template.slots} if template else None}


# ---------------------------------------------------------------- mapping an engine result to the contract


def _quality(report: Any | None, result: dict[str, Any] | None, thresholds: Any) -> dict[str, float]:
    """Display numbers 0 to 1. blur: 0 sharp, 1 flat (scaled against twice the gate's cut-off); glare: size of a soft
    saturated blob (0 when none); confidence: the weakest OCR evidence among the compared fields (0 when a field
    has none)."""
    metrics = report.metrics if report is not None else {}
    blur = 0.0 if not metrics else max(0.0, min(1.0, 1 - metrics["sharpness"] / (2 * thresholds.min_sharpness)))
    soft = bool(metrics) and metrics["glare_edge"] < thresholds.glare_max_edge
    glare = min(1.0, metrics["glare_blob"] * 10) if soft else 0.0
    confs = [f["confidence"] or 0.0 for f in (result or {}).get("fields", [])]
    return {"blur": round(blur, 3), "glare": round(glare, 3), "confidence": round(min(confs), 3) if confs else 0.0}


def outcome_of(result: dict[str, Any]) -> tuple[str, list[dict[str, Any]], str | None]:
    """(outcome, mismatches, rescan_reason) for an engine result."""
    mismatches = [{"field": f["field"], "expected": f["expected"], "observed": f["observed"] or "",
                   **({"bbox": list(f["bbox"])} if f.get("bbox") else {})}
                  for f in result["fields"] if f["status"] == "MISMATCH"]
    for issue in result["issues"]:
        if issue["kind"] == "BARCODE_DIFFERENCE":
            mismatches.append(
                {"field": "barcode", "expected": str(issue["expected"]), "observed": str(issue["observed"])})
    if result["status"] == "MISMATCH":
        return "mismatch", mismatches, None
    if result["status"] == "NEEDS_HUMAN_REVIEW":
        unsure = [f["field"] for f in result["fields"] if f["status"] == "NEEDS_HUMAN_REVIEW"]
        kinds = sorted({i["kind"] for i in result["issues"]})
        what = ", ".join(unsure + kinds) or "see warnings"
        reason = f"Weak or missing evidence: {what}. Rescan or check by eye."
        return "rescan_needed", mismatches, reason
    return "match", mismatches, None


def verification_json(row: PrintVerification) -> dict[str, Any]:
    """Serialize a row (contract `PrintVerification`, plus the optional `fields` and `notes` of CR-26)."""
    out: dict[str, Any] = {
        "verification_id": row.verification_id, "label_id": row.label_id, "version_id": row.version_id,
        "photo_file": {"file_id": f"pf_{row.photo_sha256[:8]}", "mime": row.photo_mime, "sha256": row.photo_sha256},
        "condition": row.condition, "outcome": row.outcome, "mismatches": row.mismatches, "quality": row.quality,
        "fields": row.fields, "notes": row.notes, "created_at": row.created_at,
    }
    if row.barcode:
        out["barcode"] = row.barcode
    if row.rescan_reason:
        out["rescan_reason"] = row.rescan_reason
    return out


def list_for(session: Session, version_id: str) -> list[PrintVerification]:
    """Verifications of one version, oldest first."""
    return list(session.scalars(select(PrintVerification).where(
        PrintVerification.version_id == version_id).order_by(PrintVerification.seq)))


# ---------------------------------------------------------------- the request and the job


def accept(session: Session, user_id: str, version: LabelVersion, condition: str, data: bytes) -> tuple[Any, str, str]:
    """Validate everything refusable before a job exists. Returns (checked upload, stored path, verification_id)."""
    if condition not in CONDITIONS:
        raise ApiError(422, "validation_error", f"condition must be one of {list(CONDITIONS)}.")
    gate(session, version)
    upload = uploads.validate_upload(data)
    if upload.mime == "application/pdf":
        raise ApiError(422, "unsupported_media_type", "Send a photo (PNG or JPEG) of the printed label, not a PDF.")
    stored = uploads.store_bytes(checks.files_dir(), upload, data)
    return upload, stored, new_id("pv")


def run_verify_job(app: Any, job_id: str, verification_id: str, version_id: str, user_id: str, stored: str,
                   mime: str, sha256: str, condition: str) -> None:
    """Background body of a 202 verifyPrint: quality gate, compare, append the result row, finish the job."""
    with app.state.session_factory() as session:
        try:
            checks.advance_job(session, job_id, "processing", 0.1, "checking the photo")
            version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).one()
            art = gate(session, version)  # approval can change between the request and the job
            expected = expected_content(session, version, art)
            photo = uploads.resolve_stored(checks.files_dir(), stored)
            # The gate is for camera photos (as in the upload job, which skips it for a rendered PDF page). A flat
            # clean_print_scan is mostly white paper, which the gate reads as low contrast, so it is not applied there.
            report = app.state.quality_gate(photo) if condition != "clean_print_scan" else None
            result: dict[str, Any] | None = None
            if report is not None and not report.ok:
                outcome, mismatches = "rescan_needed", []
                reason = "Photo quality: " + ", ".join(report.reasons) + ". Retake it."
            else:
                checks.advance_job(session, job_id, "processing", 0.4, "reading the printed label")
                result = app.state.print_engine.verify(photo, expected)
                outcome, mismatches, reason = outcome_of(result)
            expected_payload = expected["payload"]
            decoded = (result or {}).get("barcode")
            row = PrintVerification(
                verification_id=verification_id, job_id=job_id, label_id=version.label_id, version_id=version_id,
                photo_path=stored, photo_mime=mime, photo_sha256=sha256, condition=condition, outcome=outcome,
                mismatches=mismatches, fields=(result or {}).get("fields", []),
                barcode={"expected_payload": expected_payload, "decoded": decoded,
                         "match": bool(decoded and decoded.get("parsed") == expected["barcode_ais"])
                         } if result else None,
                quality=_quality(report, result, app.state.quality_thresholds), rescan_reason=reason,
                notes={"symbols": "not compared: the symbol detector is not trusted",
                       "engine_status": (result or {}).get("status", "NOT_RUN"),
                       "warnings": (result or {}).get("warnings", []),
                       "quality_metrics": report.metrics if report else "gate not applied (clean_print_scan)",
                       "reference_sha256": version.artifact_sha256},
                created_by=user_id, created_at=utcnow())
            session.add(row)
            record_audit(session, user_id, "print.verified", "label_version", version_id,
                         details={"verification_id": verification_id, "outcome": outcome, "condition": condition})
            session.commit()
            checks.advance_job(session, job_id, "done", 1.0, result_url=f"/print-verifications/{verification_id}")
        except ApiError as error:
            checks.advance_job(session, job_id, "failed", 1.0, error=error.body())
        except ExtractorUnavailable as error:
            checks.advance_job(session, job_id, "failed", 1.0,
                               error={"error": "extractor_unavailable", "message": str(error)})
        except Exception as error:  # a job must end in a state a client can read
            checks.advance_job(session, job_id, "failed", 1.0, error={
                "error": "print_verify_failed", "message": f"{type(error).__name__}: {error}"})


def require_real_version(session: Session, version_id: str) -> LabelVersion | None:
    """The version, or None for ids this server never issued (those keep the mock). 404 for an unknown real-form id."""
    row = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
    if row is None and scans.REAL_VERSION_ID.match(version_id):
        raise ApiError(404, "not_found", f"No label version {version_id!r}.")
    return row
