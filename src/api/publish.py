"""publishVersion and the public page a supplementary QR opens (Step 25b, CR-24).

Publishing needs a valid approval of exactly this version: its latest review is an approve whose artifact hash is the
version's own, the change is open and this is still the change's latest version (a newer version voids an approval).
The page is pinned to the version_id, so a newer version gets a new page. The QR files were rendered at generation time
with a payload of `<base>/versions/<version_id>`; the page URL is read back from the stored report so the two
always agree. The page says plainly when the stored files still carry the DRAFT mark (the prototype never renders
an approved variant).
"""
from __future__ import annotations

import hashlib
import html
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api import checks
from src.api.artwork import ARTIFACT_DIR, DISCLAIMER, public_base_url
from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.models import Artifact, GeneratedArtwork, LabelVersion, ProductVersion, PublishedPage, Review
from src.api.status import is_closed, latest_review, latest_version_of_change
from src.api.store import get_user, new_id, record_audit

PAGE_STYLE = (
    "body{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#1b1f23}"
    "h1{font-size:1.4rem}dt{font-weight:600;margin-top:.7rem}dd{margin:0;word-break:break-all}"
    ".note{background:#fff7e0;border:1px solid #e3c766;padding:.6rem .9rem;border-radius:6px}"
    "code{background:#f1f3f5;padding:0 .25rem;border-radius:3px}"
)


def _page_json(page: PublishedPage) -> dict[str, Any]:
    """The contract PublishedPage."""
    return {"page_id": page.page_id, "label_id": page.label_id, "version_id": page.version_id, "url": page.url,
            "qr_payload": page.qr_payload, "published_at": page.published_at, "review_id": page.review_id}


def existing_page(session: Session, version_id: str) -> PublishedPage | None:
    """The page of a version, if it was published."""
    return session.scalars(select(PublishedPage).where(PublishedPage.version_id == version_id)).first()


def stored_qr_payload(session: Session, version_id: str) -> str | None:
    """The QR payload written into the stored report of a generated version (None when there is no report)."""
    row = session.scalars(select(Artifact).where(Artifact.version_id == version_id, Artifact.role == "report")).first()
    if row is None:
        return None
    path = checks.files_dir() / ARTIFACT_DIR / f"{row.sha256}.{row.ext}"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("qr", {}).get("payload")


def publish_version(session: Session, user_id: str, version_id: str) -> tuple[dict[str, Any], bool]:
    """Publish an approved version. Returns (PublishedPage, created); a second call returns the same page.

    Errors: 403 role_forbidden (reviewer or admin only), 404 not_found, 409 change_closed, version_superseded,
    not_approved (no approval, or the latest review is a return or reject) or hash_mismatch.
    """
    user = get_user(session, user_id)
    if user.role not in ("reviewer", "admin"):
        raise ApiError(403, "role_forbidden", "Only a reviewer or admin can publish.")
    version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
    if version is None:
        raise ApiError(404, "not_found", f"No label version {version_id!r}.")
    page = existing_page(session, version_id)
    if page is not None:
        return _page_json(page), False
    if version.change_id is not None:
        if is_closed(session, version.change_id):
            raise ApiError(409, "change_closed", "This change was rejected, so nothing of it can be published.")
        latest = latest_version_of_change(session, version.change_id)
        if latest is not None and latest.version_id != version_id:
            raise ApiError(409, "version_superseded", "A newer version exists, so this approval no longer counts.",
                           {"latest_version_id": latest.version_id})
    review: Review | None = latest_review(session, version_id)
    if review is None or review.decision != "approve":
        raise ApiError(409, "not_approved", "Only a version whose latest review is an approval can be published.")
    if not version.artifact_sha256 or review.artifact_sha256 != version.artifact_sha256:
        raise ApiError(409, "hash_mismatch", "The approval does not name this version's artifact hash.")
    url = stored_qr_payload(session, version_id) or f"{public_base_url()}/versions/{version_id}"
    page = PublishedPage(page_id=new_id("pub"), label_id=version.label_id, version_id=version_id,
                         review_id=review.review_id, url=url, qr_payload=url, published_at=utcnow())
    session.add(page)
    record_audit(session, user.user_id, "version.published", "label_version", version_id,
                 details={"page_id": page.page_id, "review_id": review.review_id, "url": url})
    session.commit()
    return _page_json(page), True


def public_page_html(session: Session, version_id: str) -> str | None:
    """The HTML of a published version's public page, or None when the version is not published."""
    page = existing_page(session, version_id)
    if page is None:
        return None
    version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
    review = session.scalars(select(Review).where(Review.review_id == page.review_id)).first()
    product = session.scalars(select(ProductVersion).where(
        ProductVersion.product_id == version.product_id, ProductVersion.version == version.product_version)).first()
    art = session.scalars(select(GeneratedArtwork).where(GeneratedArtwork.version_id == version_id)).first()
    e = html.escape
    rows = [
        ("Product", product.name if product else version.product_id),
        ("Label", f"{version.label_id}, artwork version {version.artwork_version}"),
        ("Approved", f"{review.decided_at} by a {review.reviewer_role}"),
        ("Published", page.published_at),
        ("Artifact SHA-256", version.artifact_sha256 or ""),
    ]
    items = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in rows)
    marks = list(art.visible_markings) if art else []
    note = ("The stored label files still carry the visible mark: " + e(" | ".join(marks)) + ". This is a prototype, "
            "the identifiers are test placeholders, and the label is not for production use.") if marks else ""
    pdf = f"/versions/{e(version_id)}/label.pdf"
    return (f"<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width'>"
            f"<title>Published label {e(version_id)}</title><style>{PAGE_STYLE}</style><body>"
            f"<h1>Published label version</h1><p>This page is pinned to <code>{e(version_id)}</code>. "
            f"A newer version gets a new page.</p>"
            f"{f'<p class=note>{note}</p>' if note else ''}<dl>{items}</dl>"
            f"<p><a href='{pdf}'>Download the approved PDF</a> (its SHA-256 is shown above)</p>"
            f"<p><a href='/public/medicine'>Medicine information (public mode)</a></p>"
            f"<p><small>{e(DISCLAIMER)} LabelLens does not certify compliance or authenticity.</small></p>"
            f"</body></html>")


def published_pdf(session: Session, version_id: str) -> bytes:
    """The stored PDF of a published version, re-hashed before it is returned. 404 when not published or missing."""
    if existing_page(session, version_id) is None:
        raise ApiError(404, "not_found", f"No published version {version_id!r}.")
    row = session.scalars(select(Artifact).where(Artifact.version_id == version_id, Artifact.role == "pdf")).first()
    if row is None:
        raise ApiError(404, "no_artifacts", "This published version has no stored PDF.")
    path = checks.files_dir() / ARTIFACT_DIR / f"{row.sha256}.{row.ext}"
    if not path.is_file():
        raise ApiError(404, "artifact_missing", "The stored file is missing on the server.")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != row.sha256:
        raise ApiError(500, "artifact_corrupt", "The stored file does not match its hash and was not served.")
    return data
