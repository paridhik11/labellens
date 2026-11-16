"""Approval records bound to an exact reference, version and passed check."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ApprovalRecord:
    """Externally issued decision using the agreed reference_sha256 name."""

    reviewer: str
    version_id: str
    reference_sha256: str
    check_id: str
    reviewer_role: str
    decision: str = "approve"


@dataclass(frozen=True)
class PassedCheck:
    """Trusted check result for the same version and exact reference bytes."""

    check_id: str
    version_id: str
    reference_sha256: str
    passed: bool


def require_approved_reference(
    reference_sha256: str,
    version_id: str,
    created_by: str,
    approval: ApprovalRecord,
    check: PassedCheck | None,
    authorized_reviewers: frozenset[str],
) -> None:
    """Refuse missing, stale, failed, self-issued or unauthorized approvals.

    Authorization and check provenance must come from trusted application storage,
    not an uploaded record. This validates supplied records and creates none.
    """
    if (
        not all(
            isinstance(value, str) and value.strip()
            for value in (
                reference_sha256,
                version_id,
                created_by,
                approval.reviewer,
                approval.check_id,
                approval.reviewer_role,
            )
        )
        or approval.decision != "approve"
        or not approval.check_id.strip()
        or approval.reviewer_role not in {"reviewer", "admin"}
        or approval.reviewer not in authorized_reviewers
        or approval.reviewer == created_by
        or approval.version_id != version_id
        or approval.reference_sha256 != reference_sha256
        or check is None
        or check.passed is not True
        or check.check_id != approval.check_id
        or check.version_id != version_id
        or check.reference_sha256 != reference_sha256
    ):
        raise PermissionError("Approval requires an authorized independent reviewer and a matching passed check_id")


def _record_string(record: Mapping[str, Any], name: str, alias: str | None = None) -> str:
    """Read a required record value without accepting conflicting field aliases."""
    value = record.get(name, record.get(alias) if alias else None)
    if alias and name in record and alias in record and record[name] != record[alias]:
        raise PermissionError(f"Conflicting approval/check fields: {name}, {alias}")
    if not isinstance(value, str) or not value.strip():
        raise PermissionError(f"Approval/check requires a nonempty {name}")
    return value


def approval_from_records(
    review: Mapping[str, Any],
    check: Mapping[str, Any] | None,
) -> tuple[ApprovalRecord, PassedCheck]:
    """Map stored API or local record names without changing the reference meaning.

    Local names remain reviewer/reference_sha256. API aliases user_id and
    artifact_sha256 mean reviewer and the manifest hash, not per-file hashes.
    Both spellings may be supplied only when their values agree.
    """
    if not isinstance(review, Mapping) or not isinstance(check, Mapping):
        raise PermissionError("Both an approval and its passed check record are required")
    approval = ApprovalRecord(
        reviewer=_record_string(review, "reviewer", "user_id"),
        version_id=_record_string(review, "version_id"),
        reference_sha256=_record_string(review, "reference_sha256", "artifact_sha256"),
        check_id=_record_string(review, "check_id"),
        reviewer_role=_record_string(review, "reviewer_role"),
        decision=_record_string(review, "decision"),
    )
    if check.get("critical_count", 0) != 0 or any(
        finding.get("severity") == "critical" for finding in check.get("findings", [])
    ):
        raise PermissionError("A check with critical findings cannot clear approval")
    result = PassedCheck(
        check_id=_record_string(check, "check_id"),
        version_id=_record_string(check, "version_id"),
        reference_sha256=_record_string(check, "reference_sha256", "artifact_sha256"),
        passed=check.get("passed"),
    )
    return approval, result
