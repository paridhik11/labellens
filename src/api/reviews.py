"""The review rules: approve, return or reject one exact label version.

Checks run in this order, and the first failure wins (nothing is written on failure):
1. user must exist (401) and be a reviewer or admin (403 role_forbidden)
2. the version must exist (404)
3. decision must be valid (422), return and reject need a comment (422 comment_required)
4. the change must be open (409 change_closed) and this must be its latest version (409 version_superseded)
5. approve only: submitter cannot approve (403 self_approval_forbidden), check_id required (422),
   artifact hash must match (409 hash_mismatch), the check must be a passed check of the same
   version and hash (409 check_not_passed)
Then the Review row and an AuditEvent are appended.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.db import utcnow
from src.api.errors import ApiError
from src.api.models import ChangeRequest, CheckResult, LabelVersion, Review
from src.api.status import is_closed, latest_version_of_change
from src.api.store import get_user, new_id, record_audit

DECISIONS = ("approve", "return", "reject")
RESULTING_STATUS = {"approve": "reviewed", "return": "draft", "reject": "draft"}
AUDIT_ACTION = {"approve": "review.approved", "return": "review.returned", "reject": "review.rejected"}


def record_review(
    session: Session,
    user_id: str,
    version_id: str,
    decision: str,
    artifact_sha256: str,
    comment: str = "",
    check_id: str | None = None,
    review_id: str | None = None,
    at: str | None = None,
) -> Review:
    """Validate the review rules and append a Review. Raises ApiError with the contract's error code."""
    user = get_user(session, user_id)
    if user.role not in ("reviewer", "admin"):
        raise ApiError(403, "role_forbidden", "Only a reviewer or admin can record a review.")

    version = session.scalars(select(LabelVersion).where(LabelVersion.version_id == version_id)).first()
    if version is None:
        raise ApiError(404, "not_found", f"No label version {version_id!r}.")

    if decision not in DECISIONS:
        raise ApiError(422, "validation_error", f"decision must be one of {list(DECISIONS)}.")
    if decision in ("return", "reject") and not comment.strip():
        raise ApiError(422, "comment_required", f"A {decision} needs a comment.")

    change: ChangeRequest | None = None
    if version.change_id is not None:
        change = session.get(ChangeRequest, version.change_id)
        if is_closed(session, version.change_id):
            raise ApiError(409, "change_closed", "This change was rejected. Create a new change request.")
        latest = latest_version_of_change(session, version.change_id)
        if latest is not None and latest.version_id != version.version_id:
            raise ApiError(
                409,
                "version_superseded",
                "A newer artwork version exists for this change, so this version cannot be reviewed.",
                {"latest_version_id": latest.version_id},
            )

    if decision == "approve":
        if change is not None and change.created_by == user.user_id:
            raise ApiError(403, "self_approval_forbidden", "The submitter of a change cannot approve it.")
        if not check_id:
            raise ApiError(422, "check_required", "An approval needs the check_id of a passed check.")
        if not version.artifact_sha256 or artifact_sha256 != version.artifact_sha256:
            raise ApiError(409, "hash_mismatch", "artifact_sha256 does not match this version's artwork.")
        check = session.scalars(select(CheckResult).where(CheckResult.check_id == check_id)).first()
        if (
            check is None
            or not check.passed
            or check.version_id != version.version_id
            or check.artifact_sha256 != version.artifact_sha256
        ):
            raise ApiError(
                409,
                "check_not_passed",
                "check_id must name a passed check of this exact version and artifact hash.",
            )

    review = Review(
        review_id=review_id or new_id("rev"),
        label_id=version.label_id,
        version_id=version.version_id,
        change_id=version.change_id,
        decision=decision,
        user_id=user.user_id,
        reviewer_role=user.role,
        comment=comment,
        artifact_sha256=artifact_sha256,
        check_id=check_id if decision == "approve" else None,
        decided_at=at or utcnow(),
    )
    session.add(review)
    record_audit(
        session,
        user.user_id,
        AUDIT_ACTION[decision],
        "label_version",
        version.version_id,
        details={"review_id": review.review_id, "change_id": version.change_id, "decision": decision},
        at=review.decided_at,
    )
    session.commit()
    return review
