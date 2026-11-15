"""Inspection, re-check, jobs and search for the API (Step 21c).

`inspectLabel` and `recheckArtwork` run the checker (src/checker) on the extraction of one label version.
The extraction comes from the `extractions` table; when there is none yet, a job runs the CV extractor on the
version's image first and stores the result. Everything is append-only: a check is a new CheckResult row, a
job state change is a new Job row.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.extractor import ExtractorUnavailable
from src.api.models import CheckResult, Extraction, Job, LabelVersion, ProductVersion
from src.api.store import add_check_result, new_id
from src.checker.models import CheckerResult, Finding
from src.checker.runner import run_checks
from src.checker.settings import CheckerSettings, RetrievalSettings
from src.common.schemas import LabelExtraction, ProductRecord

DISCLAIMER = "Draft generated for review. Not a compliance determination."
RASTER_SUFFIXES = (".png", ".jpg", ".jpeg")
JOB_KINDS = {"inspection": "inspect", "self_check": "recheck"}
REAL_JOB_ID = re.compile(r"^job_[0-9a-f]{8}$")  # new_id("job"); the mock jobs use other ids such as job_inspect_0001


def files_dir() -> Path:
    """Folder that relative artwork paths are resolved against (LABELLENS_FILES_DIR, default data/api)."""
    return Path(os.environ.get("LABELLENS_FILES_DIR", "data/api"))


# ---------------------------------------------------------------- jobs


def latest_job(session: Session, job_id: str) -> Job | None:
    """The newest row (current state) of one job."""
    return session.scalars(select(Job).where(Job.job_id == job_id).order_by(Job.seq.desc())).first()


def new_job(session: Session, kind: str, version_id: str, user_id: str) -> Job:
    """Append the first row of a job (state queued)."""
    row = Job(
        job_id=new_id("job"), kind=kind, state="queued", progress=0.0, version_id=version_id,
        created_by=user_id, created_at=utcnow(),
    )
    session.add(row)
    session.commit()
    return row


def advance_job(
    session: Session, job_id: str, state: str, progress: float, message: str = "",
    result_url: str | None = None, error: dict[str, Any] | None = None,
) -> Job:
    """Append a state change for an existing job."""
    previous = latest_job(session, job_id)
    assert previous is not None
    row = Job(
        job_id=job_id, kind=previous.kind, state=state, progress=progress, message=message, result_url=result_url,
        error=error, version_id=previous.version_id, created_by=previous.created_by, created_at=utcnow(),
    )
    session.add(row)
    session.commit()
    return row


def job_json(row: Job) -> dict[str, Any]:
    """Serialize the current state of a job (contract `Job`)."""
    out: dict[str, Any] = {"job_id": row.job_id, "kind": row.kind, "state": row.state, "progress": row.progress}
    if row.message:
        out["message"] = row.message
    if row.result_url:
        out["result_url"] = row.result_url
    if row.error:
        out["error"] = row.error
    return out


# ---------------------------------------------------------------- extraction and product record


def latest_extraction(session: Session, version_id: str) -> Extraction | None:
    """The newest stored extraction of one label version, or None."""
    stmt = select(Extraction).where(Extraction.version_id == version_id).order_by(Extraction.seq.desc())
    return session.scalars(stmt).first()


def image_path(version: LabelVersion) -> Path:
    """The raster image to read for a version. An SVG artwork is read through its rendered PNG next to it."""
    path = Path(version.artwork_file)
    if not path.is_absolute():
        path = files_dir() / path
    if path.suffix.lower() in RASTER_SUFFIXES:
        candidates = [path]
    else:  # the renderer package holds label.svg, label.png, label.pdf and manifest.json side by side
        candidates = [path.with_suffix(".png"), path.parent / "label.png"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ApiError(404, "artwork_not_found", f"No image for {version.artwork_file!r} was found on the server.")


def store_extraction(session: Session, version: LabelVersion, extraction: LabelExtraction, mode: str) -> Extraction:
    """Append an extraction row, labelled with the version's label family and artwork version."""
    fixed = extraction.model_copy(update={"label_id": version.label_id, "version": version.artwork_version})
    row = Extraction(
        extraction_id=new_id("ext"), version_id=version.version_id, label_id=version.label_id, mode=mode,
        payload=fixed.model_dump(mode="json"), created_at=utcnow(),
    )
    session.add(row)
    session.commit()
    return row


def product_record(session: Session, version: LabelVersion) -> ProductRecord:
    """The product record the label was made against (its pinned product_version)."""
    row = session.scalars(
        select(ProductVersion).where(
            ProductVersion.product_id == version.product_id, ProductVersion.version == version.product_version
        )
    ).first()
    if row is None:
        raise ApiError(404, "not_found", f"No product version {version.product_version} of {version.product_id!r}.")
    return ProductRecord(
        product_id=row.product_id, version=row.version, name=row.name, model=row.model,
        manufacturer=row.manufacturer, manufacturer_address=row.manufacturer_address, udi_di=row.udi_di,
        sterilization=row.sterilization, storage=row.storage, extra=dict(row.extra or {}),
    )


# ---------------------------------------------------------------- the check itself


def finding_json(finding: Finding) -> dict[str, Any]:
    """A checker Finding as a contract Finding: no empty optional strings, citations without the internal rank."""
    out = finding.model_dump(mode="json", exclude={"citations"})
    for key in ("field", "rule_id"):
        if not out.get(key):
            out.pop(key, None)
    out["citations"] = [c.model_dump(mode="json", exclude={"rank"}) for c in finding.citations]
    return out


def retrieval_for(base: CheckerSettings, override: dict[str, Any] | None) -> CheckerSettings:
    """Apply a request's RetrievalConfig to the app's checker settings. Unset keys keep the app default."""
    if not override:
        return base
    allowed = {k: override[k] for k in ("method", "stem", "prefix") if k in override}
    return CheckerSettings(
        min_ocr_confidence=base.min_ocr_confidence, symbol_detector_trusted=base.symbol_detector_trusted,
        expected_symbols=base.expected_symbols,
        retrieval=RetrievalSettings(**{**base.retrieval.__dict__, **allowed}),
    )


def perform_check(
    session: Session, kind: str, version: LabelVersion, extraction: LabelExtraction, settings: CheckerSettings,
    user_id: str,
) -> CheckResult:
    """Run the checker on a stored extraction and persist the CheckResult (a self_check copies the artifact hash)."""
    from src.checker.retrieval import default_retriever

    result: CheckerResult = run_checks(
        extraction, product_record(session, version), settings=settings,
        retriever=default_retriever(settings.retrieval),
    )
    return add_check_result(
        session, kind, [finding_json(f) for f in result.findings], version_id=version.version_id,
        artifact_sha256=version.artifact_sha256 if kind == "self_check" else None, user_id=user_id,
        coverage=[o.model_dump(mode="json") for o in result.coverage], retrieval_config=result.retrieval_config,
    )


def check_result_json(row: CheckResult) -> dict[str, Any]:
    """Serialize a CheckResult (contract `CheckResult`)."""
    out: dict[str, Any] = {
        "check_id": row.check_id, "kind": row.kind, "run_at": row.run_at, "findings": row.findings,
        "critical_count": row.critical_count, "review_count": row.review_count, "info_count": row.info_count,
        "passed": row.passed,
    }
    for key in ("label_id", "version_id", "template_id", "artifact_sha256"):
        if getattr(row, key) is not None:
            out[key] = getattr(row, key)
    if row.kind in ("inspection", "self_check"):
        out["coverage"] = row.coverage or []
        out["needs_human_count"] = row.needs_human_count or 0
        out["disclaimer"] = DISCLAIMER
    if row.retrieval_config:
        out["retrieval_config"] = row.retrieval_config
    return out


def search(
    base: CheckerSettings, module: str, query: str, k: int, section_level: bool, override: dict[str, Any] | None
) -> dict[str, Any]:
    """Evidence retrieval for one module (device or medicine, never both) with the default or overridden retriever.

    Hits are chunks (or, with section_level, the best chunk of each section). One citation per hit, with a
    verbatim quote chosen by query-term overlap.
    """
    from src.checker.citations import best_quote
    from src.checker.retrieval import default_retriever, module_chunks

    settings = retrieval_for(base, override).retrieval
    settings = RetrievalSettings(**{**settings.__dict__, "module": module})
    chunks = module_chunks(module)
    hits = default_retriever(settings).search(query, k=k * 4 if section_level else k)
    if section_level:
        seen: set[str] = set()
        kept = []
        for hit in hits:
            section = chunks[hit.doc_id].section
            if section not in seen:
                seen.add(section)
                kept.append(hit)
        hits = kept[:k]
    out_hits, citations = [], []
    for rank, hit in enumerate(hits, start=1):
        chunk = chunks[hit.doc_id]
        out_hits.append({"doc_id": hit.doc_id, "score": hit.score, "rank": rank, "text": chunk.text})
        citations.append({
            "source_type": "cfr", "chunk_id": chunk.chunk_id, "source": chunk.source, "section": chunk.section,
            "title": chunk.title, "url": chunk.url, "quote": best_quote(chunk.text, query),
        })
    config = {k: v for k, v in settings.echo().items() if k in ("method", "stem", "prefix")}
    return {"query": query, "module": module, "retrieval": {**config, "rerank": False, "expansion": False},
            "hits": out_hits, "citations": citations}


def run_check_job(app: Any, job_id: str, kind: str, version_id: str, user_id: str, settings: CheckerSettings) -> None:
    """Background body of a 202 inspect or re-check: extract if needed, check, store, finish the job.

    Any failure ends the job in state `failed` with the contract Error shape, never an unhandled exception.
    """
    with app.state.session_factory() as session:
        try:
            advance_job(session, job_id, "processing", 0.1, "reading the label")
            version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).one()
            stored = latest_extraction(session, version_id)
            if stored is None:
                extraction, mode = app.state.extractor(image_path(version))
                stored = store_extraction(session, version, extraction, mode)
            advance_job(session, job_id, "processing", 0.6, "checking the label")
            check = perform_check(
                session, kind, version, LabelExtraction.model_validate(stored.payload), settings, user_id
            )
            advance_job(session, job_id, "done", 1.0, result_url=f"/check-results/{check.check_id}")
        except ApiError as error:
            advance_job(session, job_id, "failed", 1.0, error=error.body())
        except ExtractorUnavailable as error:
            advance_job(session, job_id, "failed", 1.0, error={"error": "extractor_unavailable", "message": str(error)})
        except Exception as error:  # a job must end in a state a client can read
            advance_job(session, job_id, "failed", 1.0, error={
                "error": "check_failed", "message": f"{type(error).__name__}: {error}"})
