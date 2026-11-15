"""Evidence-preserving draft comparison and approval-gated print verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.common.schemas import LabelExtraction
from src.cv.extract import extract_label


@dataclass
class VerificationResult:
    """Observed differences or uncertain evidence, never automatic publication approval."""

    status: str
    issues: list[dict[str, Any]]
    warnings: list[str]


def compare_extraction(extraction: LabelExtraction, reference: dict[str, Any]) -> VerificationResult:
    """Compare observed fields, GS1 values and symbols against explicit expected content.

    Used internally for draft self-checks. It makes no approval claim. Text is
    compared exactly; OCR differences remain proposals requiring human review.
    """
    issues = []
    mismatch = False
    uncertain = False
    for field, expected in reference["fields"].items():
        observed = extraction.fields.get(field)
        candidates = [block for block in extraction.ocr_blocks if block.text == observed]
        bbox = candidates[0].bbox if len(candidates) == 1 else None
        if observed != expected:
            confident = len(candidates) == 1 and candidates[0].conf >= 0.8
            mismatch = mismatch or (observed is not None and confident)
            uncertain = uncertain or observed is None or not confident
            issues.append(
                {
                    "kind": "TEXT_DIFFERENCE" if observed is not None else "TEXT_UNREADABLE",
                    "field": field,
                    "expected": expected,
                    "observed": observed,
                    "bbox": bbox,
                    "reason": "OCR evidence requires reviewer confirmation",
                }
            )
        elif len(candidates) != 1 or candidates[0].conf < 0.8:
            uncertain = True
            issues.append(
                {
                    "kind": "TEXT_UNCONFIRMED",
                    "field": field,
                    "expected": expected,
                    "observed": observed,
                    "bbox": bbox,
                    "reason": "Matching field text lacks one sufficiently confident OCR observation",
                }
            )
    if len(extraction.barcodes) != 1 or not extraction.barcodes[0].parsed:
        uncertain = True
        issues.append(
            {
                "kind": "BARCODE_UNREADABLE_OR_AMBIGUOUS",
                "bbox": None,
                "reason": "Provide a clearer image or resolve multiple/unsupported symbols",
            }
        )
    else:
        barcode = extraction.barcodes[0]
        if barcode.parsed != reference["barcode_ais"]:
            mismatch = True
            issues.append(
                {
                    "kind": "BARCODE_DIFFERENCE",
                    "expected": reference["barcode_ais"],
                    "observed": barcode.parsed,
                    "bbox": barcode.bbox,
                }
            )
    found = {symbol.name for symbol in extraction.symbols}
    for name in reference["symbols"]:
        if name not in found:
            uncertain = True
            issues.append(
                {
                    "kind": "SYMBOL_UNCONFIRMED",
                    "symbol": name,
                    "bbox": None,
                    "reason": "A failed template match cannot establish physical absence",
                }
            )
    for name in sorted(found - set(reference["symbols"])):
        mismatch = True
        issues.append(
            {
                "kind": "UNEXPECTED_SYMBOL",
                "symbol": name,
                "reason": "Observed symbol is not present in the expected symbol list",
            }
        )
    critical_prefixes = (
        "BLUR_SUSPECTED",
        "LOW_OCR_CONFIDENCE",
        "OCR_FAILED",
        "LABEL_NOT_FOUND",
        "SYMBOL_DETECTION_FAILED",
        "FIELD_AMBIGUOUS",
        "SYMBOL_DETECTION_NOT_RUN",
    )
    if any(warning.startswith(critical_prefixes) for warning in extraction.warnings):
        uncertain = True
    status = "MISMATCH" if mismatch else "NEEDS_HUMAN_REVIEW" if uncertain else "MATCH"
    return VerificationResult(status, issues, list(extraction.warnings))


def verify_print(
    photo_path: str | Path,
    approved_label: str | Path,
    *,
    approval_record: dict[str, str] | None = None,
    authorized_reviewers: frozenset[str] = frozenset(),
) -> VerificationResult:
    """Verify a photo only against an intact reference explicitly approved by an authorized reviewer.

    The application must supply the authorized reviewer set from trusted auth,
    not from an upload. Approval references the exact manifest SHA-256. This
    function neither creates approval records nor publishes any artwork.
    """
    path = Path(approved_label)
    fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
    if (
        not approval_record
        or approval_record.get("decision") != "approve"
        or approval_record.get("reviewer") not in authorized_reviewers
        or approval_record.get("reference_sha256") != fingerprint
    ):
        raise PermissionError("An authorized approval record bound to this exact reference is required")
    reference = json.loads(path.read_text(encoding="utf-8"))
    for name, relative in reference["artifacts"].items():
        artifact = (path.parent / relative).resolve()
        if not artifact.is_relative_to(path.parent.resolve()):
            raise ValueError("Reference artifact path escapes its package")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != reference["artifact_sha256"][name]:
            raise ValueError(f"Approved reference artifact changed: {name}")
    return compare_extraction(extract_label(photo_path), reference)
