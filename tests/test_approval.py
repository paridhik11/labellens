"""Approval contracts tested without importing CV or PDF dependencies."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.export.approval import (
    ApprovalRecord,
    PassedCheck,
    approval_from_records,
    require_approved_reference,
)


@pytest.fixture
def records() -> tuple[ApprovalRecord, PassedCheck]:
    """Supply synthetic review/check fixtures, never real issued approvals."""
    return ApprovalRecord("reviewer", "version-1", "a" * 64, "check-1", "reviewer"), PassedCheck(
        "check-1",
        "version-1",
        "a" * 64,
        True,
    )


def test_matching_reference_and_passed_check(records: tuple[ApprovalRecord, PassedCheck]) -> None:
    """Authorization needs the exact version, reference and passed check."""
    approval, check = records
    require_approved_reference("a" * 64, "version-1", "author", approval, check, frozenset({"reviewer"}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("check_id", ""),
        ("check_id", "other"),
        ("reviewer_role", "editor"),
        ("version_id", "old-version"),
        ("reference_sha256", "b" * 64),
        ("reviewer", "author"),
        ("decision", "return"),
    ],
)
def test_invalid_approval_rejected(records: tuple[ApprovalRecord, PassedCheck], field: str, value: str) -> None:
    """A stale or unauthorized approval must fail even when a check exists."""
    approval, check = records
    with pytest.raises(PermissionError):
        require_approved_reference(
            "a" * 64,
            "version-1",
            "author",
            replace(approval, **{field: value}),
            check,
            frozenset({"reviewer", "author"}),
        )


@pytest.mark.parametrize(
    "change",
    [
        {"passed": False},
        {"passed": 1},
        {"version_id": "wrong"},
        {"reference_sha256": "b" * 64},
        {"check_id": "wrong"},
    ],
)
def test_invalid_check_rejected(records: tuple[ApprovalRecord, PassedCheck], change: dict) -> None:
    """A boolean passed result and matching check identity are both required."""
    approval, check = records
    with pytest.raises(PermissionError):
        require_approved_reference(
            "a" * 64, "version-1", "author", approval, replace(check, **change), frozenset({"reviewer"})
        )


def test_missing_check_authorization_or_version_rejected(records: tuple[ApprovalRecord, PassedCheck]) -> None:
    """Knowing a reference hash alone cannot grant approval."""
    approval, check = records
    for result, reviewers, version in (
        (None, frozenset({"reviewer"}), "version-1"),
        (check, frozenset(), "version-1"),
        (check, frozenset({"reviewer"}), ""),
    ):
        with pytest.raises(PermissionError):
            require_approved_reference("a" * 64, version, "author", approval, result, reviewers)


def test_contract_mock_names_map_to_reference_names() -> None:
    """Read existing contract examples without editing their schema or data."""
    base = Path("src/api/mock/professional/review")
    review = json.loads((base / "approved.json").read_text())
    result = json.loads((base / "recheck_success.json").read_text())
    approval, check = approval_from_records(review, result)
    assert approval.reference_sha256 == review["artifact_sha256"]
    assert approval.reviewer == review["user_id"]
    assert approval.check_id == check.check_id
    require_approved_reference(
        review["artifact_sha256"],
        review["version_id"],
        "fixture_author",
        approval,
        check,
        frozenset({review["user_id"]}),
    )
    local = {**review, "reviewer": review["user_id"], "reference_sha256": review["artifact_sha256"]}
    assert approval_from_records(local, result)[0] == approval
    with pytest.raises(PermissionError, match="Conflicting"):
        approval_from_records({**local, "reference_sha256": "wrong"}, result)
    with pytest.raises(PermissionError):
        approval_from_records({**review, "reviewer_role": ""}, result)
    with pytest.raises(PermissionError):
        approval_from_records(review, None)
    with pytest.raises(PermissionError, match="critical"):
        approval_from_records(review, {**result, "critical_count": 1})
