"""Derived status. Nothing here is stored: every value is read off the Review and CheckResult rows.

Rules come from DATA_MODEL.md, "Status derivation". For a change, only its latest artwork
version counts, so a newer version silently voids an earlier approval.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.models import CheckResult, GeneratedArtwork, LabelVersion, PublishedPage, Review


def latest_review(session: Session, version_id: str) -> Review | None:
    """Return the newest Review of one version (highest decided_at, ties broken by insert order)."""
    stmt = select(Review).where(Review.version_id == version_id).order_by(Review.decided_at.desc(), Review.seq.desc())
    return session.scalars(stmt).first()


def latest_check(session: Session, version_id: str) -> CheckResult | None:
    """Return the newest inspection or self-check of one version.

    The layout check written with a generated draft (Step 24b) is not counted: it proves the template fit and the
    barcode decoded, not that the rendered image reads back correctly, so it never makes a version `checked`.
    """
    stmt = (
        select(CheckResult)
        .where(CheckResult.version_id == version_id, CheckResult.kind.in_(("inspection", "self_check")))
        .order_by(CheckResult.run_at.desc(), CheckResult.seq.desc())
    )
    return session.scalars(stmt).first()


def label_version_status(session: Session, version_id: str) -> str:
    """Return `draft`, `checked`, `reviewed` or `published` for one label version, from its own record trail."""
    if session.scalars(select(PublishedPage).where(PublishedPage.version_id == version_id)).first():
        return "published"
    review = latest_review(session, version_id)
    if review is not None:
        return "reviewed" if review.decision == "approve" else "draft"
    check = latest_check(session, version_id)
    if check is not None and check.passed:
        return "checked"
    return "draft"


def draft_watermark(session: Session, version_id: str) -> bool:
    """True until an approval exists for the version (reviewed or published means approved).

    A generated version stays True after approval: its stored files were rendered as drafts and carry the visible
    `DRAFT, not for production` mark, and this step does not render an approved variant (docs/contracts, CR-22).
    """
    if label_version_status(session, version_id) not in ("reviewed", "published"):
        return True
    art = session.scalars(select(GeneratedArtwork).where(GeneratedArtwork.version_id == version_id)).first()
    return art is not None and bool(art.visible_markings)


def latest_version_of_change(session: Session, change_id: str) -> LabelVersion | None:
    """Return the newest artwork version produced for a change, or None if none exists yet."""
    stmt = select(LabelVersion).where(LabelVersion.change_id == change_id).order_by(LabelVersion.seq.desc())
    return session.scalars(stmt).first()


def is_closed(session: Session, change_id: str) -> bool:
    """A change is closed once any Review of it is a reject (reject is terminal)."""
    stmt = select(Review.seq).where(Review.change_id == change_id, Review.decision == "reject")
    return session.scalars(stmt).first() is not None


def change_status(session: Session, change_id: str) -> str:
    """Status of a change = status of its latest artwork version. No version yet means `draft`."""
    version = latest_version_of_change(session, change_id)
    return label_version_status(session, version.version_id) if version else "draft"


def change_latest_review_id(session: Session, change_id: str) -> str | None:
    """The review the change's status was derived from (latest review of the latest version), if any."""
    version = latest_version_of_change(session, change_id)
    if version is None:
        return None
    review = latest_review(session, version.version_id)
    return review.review_id if review else None
