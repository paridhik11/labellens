"""Confidence, abstention and trusted-reference tests for per-field verification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

for _module in ("cv2", "PIL", "zxingcpp"):
    pytest.importorskip(_module)

from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock  # noqa: E402
from src.cv import print_verify  # noqa: E402


def observed(value: str = "LOT: TEST001", confidence: float = 0.95) -> LabelExtraction:
    """Build explicitly synthetic OCR evidence without loading an OCR model."""
    return LabelExtraction(label_id="test", fields={"lot": value},
                           ocr_blocks=[OcrBlock(text=value, bbox=(1, 2, 30, 10), conf=confidence)],
                           barcodes=[BarcodeResult(type="Data Matrix", raw="test", parsed={"10": "TEST001"})])


def test_field_decisions() -> None:
    """Keep missing/weak/ambiguous observations distinct from confident mismatches."""
    match = print_verify.compare_fields(observed(), {"lot": "TEST001", "expiry": ""})
    assert len(match) == 1 and match[0].status == "MATCH" and match[0].confidence == 0.95
    assert print_verify.compare_fields(observed("LOT: WRONG"), {"lot": "TEST001"})[0].status == "MISMATCH"
    assert print_verify.compare_fields(observed(confidence=0.2), {"lot": "TEST001"})[0].status == "NEEDS_HUMAN_REVIEW"
    missing = print_verify.compare_fields(observed(), {"expiry": "2028-01-01"})[0]
    assert missing.status == "NEEDS_HUMAN_REVIEW" and missing.confidence is None
    extraction = observed()
    extraction.ocr_blocks *= 2
    assert print_verify.compare_fields(extraction, {"lot": "TEST001"})[0].confidence is None
    with pytest.raises(ValueError):
        print_verify.compare_fields(extraction, {}, min_confidence=float('nan'))


def test_approval_and_artifact_guard(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use test review records only and reject absent, stale and tampered approvals."""
    artifact = tmp_path / "test.txt"
    artifact.write_text("synthetic test artifact")
    reference = {"version_id": "test-v1", "created_by": "test_creator", "fields": {"lot": "TEST001"},
                 "barcode_ais": {"10": "TEST001"}, "symbols": [], "artifacts": {"test": "test.txt"},
                 "artifact_sha256": {"test": hashlib.sha256(artifact.read_bytes()).hexdigest()}}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(reference))
    calls = []

    def fake_extract(path: Path, **kwargs: object) -> LabelExtraction:
        """Record extraction mode after the trusted-reference gate passes."""
        calls.append(kwargs)
        return observed()

    monkeypatch.setattr(print_verify, "extract_label", fake_extract)
    with pytest.raises(PermissionError):
        print_verify.verify_print(tmp_path / "photo.png", manifest)
    assert not calls
    approval = {"decision": "approve", "reviewer": "test_reviewer", "reviewer_role": "reviewer",
                "version_id": "test-v1", "check_id": "test-check",
                "reference_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest()}
    check = {"check_id": "test-check", "version_id": "test-v1", "passed": True,
             "reference_sha256": approval["reference_sha256"]}
    kwargs = {"approval_record": approval, "check_record": check,
              "authorized_reviewers": frozenset({"test_reviewer"})}
    result = print_verify.verify_print(tmp_path / "photo.png", manifest, **kwargs)
    assert result["status"] == "MATCH" and result["fields"][0]["confidence"] == 0.95
    assert calls == [{"mode": "blind", "postcorrect": True}]
    artifact.write_text("changed")
    with pytest.raises(ValueError, match="changed"):
        print_verify.verify_print(tmp_path / "photo.png", manifest, **kwargs)


def test_photo_evaluation_keeps_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Score errors as misses and preserve AI provenance and missing human review."""
    (tmp_path / "transcriptions.csv").write_text("filename,lot\nphoto.png,TEST001\n")
    monkeypatch.setattr(print_verify, "extract_label", lambda *args, **kwargs: observed())
    result = print_verify.evaluate_photos(tmp_path)
    assert result["totals"]["lot"]["exact"] == 1
    assert result["human_spotcheck"] == "NOT_RUN"
    assert print_verify.main(["--folder", str(tmp_path)]) == 0
    assert (tmp_path / "print_comparison_llm.json").exists()

    def fail(*args: object, **kwargs: object) -> LabelExtraction:
        """Simulate an OCR failure to verify it remains in the denominator."""
        raise RuntimeError("test failure")

    monkeypatch.setattr(print_verify, "extract_label", fail)
    result = print_verify.evaluate_photos(tmp_path)
    assert result["totals"]["lot"]["scored"] == 1 and result["totals"]["lot"]["exact"] == 0
    assert result["totals"]["lot"]["NEEDS_HUMAN_REVIEW"] == 1
    (tmp_path / "transcriptions.csv").write_text("filename,lot\n../escape.png,TEST001\n")
    with pytest.raises(ValueError, match="escapes"):
        print_verify.evaluate_photos(tmp_path)
