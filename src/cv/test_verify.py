"""Exact comparison, uncertain evidence and approval-bound reference integrity."""

import hashlib
import json
from pathlib import Path

import pytest

from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock, SymbolDetection
from src.cv import verify


def test_comparison_states() -> None:
    """Separate confirmed observations, OCR differences and weak evidence."""
    reference = {"fields": {"manufacturer": "EXAMPLE"}, "barcode_ais": {"10": "TESTLOT"}, "symbols": ["expiry"]}
    perfect = LabelExtraction(
        label_id="test",
        fields={"manufacturer": "EXAMPLE"},
        ocr_blocks=[OcrBlock(text="EXAMPLE", bbox=(10, 20, 30, 40), conf=0.99)],
        barcodes=[BarcodeResult(type="Data Matrix", raw="test", parsed={"10": "TESTLOT"})],
        symbols=[SymbolDetection(name="expiry", bbox=(50, 50, 10, 10), conf=0.99)],
    )
    assert verify.compare_extraction(perfect, reference).status == "MATCH"
    unsupported = perfect.model_copy(deep=True)
    unsupported.ocr_blocks = []
    assert verify.compare_extraction(unsupported, reference).status == "NEEDS_HUMAN_REVIEW"
    unsupported = perfect.model_copy(deep=True)
    unsupported.ocr_blocks[0].conf = 0.2
    assert verify.compare_extraction(unsupported, reference).status == "NEEDS_HUMAN_REVIEW"
    wrong = perfect.model_copy(deep=True)
    wrong.fields["manufacturer"] = "CHANGED"
    wrong.ocr_blocks[0].text = "CHANGED"
    result = verify.compare_extraction(wrong, reference)
    assert result.status == "MISMATCH" and result.issues[0]["bbox"] == (10, 20, 30, 40)
    wrong.ocr_blocks[0].conf = 0.2
    assert verify.compare_extraction(wrong, reference).status == "NEEDS_HUMAN_REVIEW"
    wrong = perfect.model_copy(deep=True)
    wrong.barcodes[0].parsed["10"] = "DIFFERENT"
    assert verify.compare_extraction(wrong, reference).status == "MISMATCH"
    missing = perfect.model_copy(update={"barcodes": [], "symbols": []})
    assert verify.compare_extraction(missing, reference).status == "NEEDS_HUMAN_REVIEW"
    extra = perfect.model_copy(deep=True)
    extra.symbols.append(SymbolDetection(name="unexpected", bbox=(1, 2, 3, 4), conf=0.99))
    assert verify.compare_extraction(extra, reference).status == "MISMATCH"


def test_approval_binding_and_integrity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use explicitly synthetic review fixtures; never mint a real approval."""
    artifact = tmp_path / "test_reference.txt"
    artifact.write_text("test reference")
    reference = {
        "fields": {},
        "barcode_ais": {"10": "TESTLOT"},
        "symbols": [],
        "artifacts": {"test": artifact.name},
        "artifact_sha256": {"test": hashlib.sha256(artifact.read_bytes()).hexdigest()},
    }
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(reference))
    monkeypatch.setattr(
        verify,
        "extract_label",
        lambda path: LabelExtraction(
            label_id="test", barcodes=[BarcodeResult(type="Data Matrix", raw="test", parsed={"10": "TESTLOT"})]
        ),
    )
    with pytest.raises(PermissionError):
        verify.verify_print(tmp_path / "test_photo.png", manifest)
    approval = {
        "decision": "approve",
        "reviewer": "test_reviewer",
        "reference_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }
    with pytest.raises(PermissionError):
        verify.verify_print(tmp_path / "test_photo.png", manifest, approval_record=approval)
    assert (
        verify.verify_print(
            tmp_path / "test_photo.png",
            manifest,
            approval_record=approval,
            authorized_reviewers=frozenset({"test_reviewer"}),
        ).status
        == "MATCH"
    )
    artifact.write_text("tampered")
    with pytest.raises(ValueError, match="changed"):
        verify.verify_print(
            tmp_path / "test_photo.png",
            manifest,
            approval_record=approval,
            authorized_reviewers=frozenset({"test_reviewer"}),
        )
