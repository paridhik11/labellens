"""Per-field print comparison with evidence confidence and approval-gated entry.

Real-photo evaluation against AI transcriptions is separate from verification
against a trusted approved artwork package. No approval is created here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.common.schemas import LabelExtraction
from src.cv.eval_real import load_transcriptions
from src.cv.extract import extract_label
from src.cv.fields import strip_key
from src.cv.verify import compare_extraction
from src.export.approval import approval_from_records, require_approved_reference


@dataclass(frozen=True)
class FieldComparison:
    """One observed field; confidence is OCR evidence strength, not correctness probability."""

    field: str
    expected: str
    observed: str | None
    status: str
    confidence: float | None
    bbox: tuple[float, float, float, float] | None


def compare_fields(
    extraction: LabelExtraction, expected: dict[str, str], *, min_confidence: float = 0.8,
) -> list[FieldComparison]:
    """Compare exact text after key removal, abstaining on missing or weak evidence.

    No fuzzy matching, product vocabulary or reference text is supplied to OCR.
    A unique supporting OCR block is required. Missing or multiple supporting
    observations have no confidence value and require human review.
    """
    if not 0 <= min_confidence <= 1:
        raise ValueError("Confidence threshold must be between zero and one")
    results = []
    for field, value in expected.items():
        if not value:
            continue
        observed = extraction.fields.get(field)
        keyed = field in {"model", "lot", "expiry", "serial"}
        observed = strip_key(observed) if keyed and observed else observed
        candidates = [block for block in extraction.ocr_blocks
                      if (strip_key(block.text) if keyed else block.text) == observed]
        block = candidates[0] if len(candidates) == 1 else None
        confidence = block.conf if block is not None else None
        status = "NEEDS_HUMAN_REVIEW"
        if observed and confidence is not None and confidence >= min_confidence:
            status = "MATCH" if observed == value else "MISMATCH"
        results.append(FieldComparison(field, value, observed, status, confidence, block.bbox if block else None))
    return results


def verify_print(
    photo_path: str | Path, approved_label: str | Path, *,
    approval_record: dict[str, Any] | None = None, check_record: dict[str, Any] | None = None,
    authorized_reviewers: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Verify a photo against an intact approved legacy manifest using blind OCR.

    Caller supplies trusted auth and review records. The reference manifest and
    all artifacts are fingerprint-checked before reading the photo. This entry
    complements the old verifier; neither the extractor nor old API is changed.
    """
    path = Path(approved_label)
    raw = path.read_bytes()
    reference = json.loads(raw)
    approval, check = approval_from_records(approval_record, check_record)
    require_approved_reference(hashlib.sha256(raw).hexdigest(), reference.get("version_id", ""),
                               reference.get("created_by", ""), approval, check, authorized_reviewers)
    for name, relative in reference["artifacts"].items():
        artifact = (path.parent / relative).resolve()
        if not artifact.is_relative_to(path.parent.resolve()):
            raise ValueError("Reference artifact path escapes its package")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != reference["artifact_sha256"][name]:
            raise ValueError(f"Approved reference artifact changed: {name}")
    extraction = extract_label(photo_path, mode="blind", postcorrect=True)
    fields = compare_fields(extraction, reference["fields"])
    other = compare_extraction(extraction, {**reference, "fields": {}})
    states = {field.status for field in fields} | {other.status}
    status = ("MISMATCH" if "MISMATCH" in states else
              "NEEDS_HUMAN_REVIEW" if "NEEDS_HUMAN_REVIEW" in states else "MATCH")
    return {"status": status, "fields": [asdict(field) for field in fields],
            "other_issues": other.issues, "warnings": other.warnings}


def evaluate_photos(folder: Path) -> dict[str, Any]:
    """Evaluate evidence per field against AI references, without inventing approvals."""
    references = load_transcriptions(folder / "transcriptions.csv")
    rows = []
    totals = {field: {"scored": 0, "exact": 0, "MATCH": 0, "MISMATCH": 0, "NEEDS_HUMAN_REVIEW": 0}
              for field in ("product_name", "lot", "expiry")}
    for filename, values in references.items():
        path = (folder / filename).resolve()
        if not path.is_relative_to(folder.resolve()):
            raise ValueError("Photo path escapes the dataset")
        expected = {field: value for field, value in values.items() if field in totals}
        try:
            extraction = extract_label(path, mode="blind", postcorrect=True)
            error = None
        except Exception as exception:
            extraction = LabelExtraction(label_id=path.stem)
            error = f"{type(exception).__name__}: {exception}"
        comparisons = compare_fields(extraction, expected)
        for field in comparisons:
            total = totals[field.field]
            total["scored"] += 1
            total["exact"] += int(field.expected == field.observed)
            total[field.status] += 1
        rows.append({"photo": filename, "error": error, "fields": [asdict(field) for field in comparisons]})
    return {"reference_source": "LLM-labelled", "condition": "photo", "human_spotcheck": "NOT_RUN",
            "approved_print_evaluation": "NOT_RUN: no trusted approved references for these online photos",
            "totals": totals, "rows": rows}


def main(argv: list[str] | None = None) -> int:
    """Write per-photo provisional field comparison evidence, not an approval result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path("data/real_photos/clear_online"))
    args = parser.parse_args(argv)
    result = evaluate_photos(args.folder)
    (args.folder / "print_comparison_llm.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
