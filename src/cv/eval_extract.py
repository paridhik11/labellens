"""Measure the unchanged extractor on a synthetic set, separately by condition."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import platform
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.common.schemas import LabelExtraction
from src.cv.extract import TEMPLATE_PATH, extract_label
from src.cv.preprocess import find_label_corners, rectify_label
from src.cv.symbols import NAMES

CONDITIONS = ("clean", "moderate", "hard")
FIELDS = ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry")
AIS = ("01", "17", "10", "21")
SETTINGS = {
    name: inspect.signature(extract_label).parameters[name].default for name in ("min_confidence", "blur_threshold")
}


def edit_distance(reference: str, observed: str) -> int:
    """Count minimum character insertions, deletions and substitutions without normalization."""
    if len(reference) < len(observed):
        reference, observed = observed, reference
    previous = list(range(len(observed) + 1))
    for row, expected in enumerate(reference, start=1):
        current = [row]
        for column, actual in enumerate(observed, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (expected != actual)))
        previous = current
    return previous[-1]


def _load_dataset(dataset_dir: Path) -> tuple[dict[str, Any], list[tuple[Path, dict[str, Any]]]]:
    """Validate synthetic truth and manifest counts before scoring any images.

    Missing images are allowed here so extraction failures remain measurable.
    Missing or malformed truth aborts evaluation because it cannot be scored.
    """
    root = dataset_dir.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("generator") != "src.gen.generate_dataset" or manifest.get("format_version") != 1:
        raise ValueError("Expected a supported synthetic-generator manifest")
    entries = manifest.get("files", [])
    if not entries or len(entries) != manifest.get("total_images"):
        raise ValueError("Manifest must contain a nonempty, complete image list")
    samples = []
    seen: set[Path] = set()
    truth_seen: set[Path] = set()
    counts: Counter[str] = Counter()
    for entry in entries:
        image_path = (root / entry["image"]).resolve()
        truth_path = (root / entry["ground_truth"]).resolve()
        if not image_path.is_relative_to(root) or not truth_path.is_relative_to(root):
            raise ValueError("Dataset paths must remain inside the dataset directory")
        if image_path in seen or truth_path in truth_seen:
            raise ValueError("Manifest contains duplicate image or ground-truth paths")
        seen.add(image_path)
        truth_seen.add(truth_path)
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        condition = truth.get("condition")
        if condition not in CONDITIONS or truth.get("test_data") is not True:
            raise ValueError("Each truth must identify synthetic test data and a supported condition")
        if any(
            not isinstance(truth.get("fields", {}).get(field), str) or not truth["fields"][field] for field in FIELDS
        ):
            raise ValueError("Ground truth must contain nonempty references for all six text fields")
        if set(truth.get("barcode_ais", {})) != set(AIS):
            raise ValueError("Ground truth must contain exactly the four supported barcode AIs")
        if any(not isinstance(value, str) or not value for value in truth["barcode_ais"].values()):
            raise ValueError("Barcode references must be nonempty strings")
        corners = np.asarray(truth.get("label_quad_px"), dtype=float)
        if corners.shape != (4, 2) or not np.isfinite(corners).all():
            raise ValueError("Ground truth must contain four finite label corners")
        symbols = truth.get("symbols")
        if (
            not isinstance(symbols, list)
            or len(symbols) != len(NAMES)
            or any(not isinstance(symbol, dict) for symbol in symbols)
            or {symbol.get("name") for symbol in symbols} != set(NAMES)
        ):
            raise ValueError("Ground truth must contain exactly the supported symbol names")
        for symbol in symbols:
            quad = np.asarray(symbol.get("quad_px"), dtype=float)
            if quad.shape != (4, 2) or not np.isfinite(quad).all():
                raise ValueError("Each symbol must contain four finite ground-truth corners")
        counts[condition] += 1
        samples.append((image_path, truth))
    for condition in CONDITIONS:
        expected_count = manifest.get("conditions", {}).get(condition, {}).get("images")
        if (
            counts[condition] == 0
            or counts[condition] != expected_count
            or counts[condition] != manifest.get("labels_per_condition")
        ):
            raise ValueError("Manifest condition counts must match all ground-truth samples")
    return manifest, samples


def _box_iou(
    first: tuple[float, float, float, float], second: tuple[float, float, float, float]
) -> float:
    """Return intersection over union for two positive x, y, width, height boxes."""
    boxes = np.asarray([first, second], dtype=float)
    if not np.isfinite(boxes).all() or (boxes[:, 2:] <= 0).any():
        raise ValueError("Boxes must be finite with positive width and height")
    (x1, y1, w1, h1), (x2, y2, w2, h2) = boxes
    intersection = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(
        0.0, min(y1 + h1, y2 + h2) - max(y1, y2)
    )
    return float(intersection / (w1 * h1 + w2 * h2 - intersection))


def _probe_geometry(image_path: Path, expected: list[list[float]]) -> tuple[bool, bool, str | None]:
    """Repeat the deterministic image-only detector to measure known-corner accuracy.

    Detection geometry is not exposed by the locked extraction schema. This
    independent probe uses the same unchanged detector and rectifier, not OCR
    success as a substitute for detection. The tolerance is fixed at 10 pixels.
    """
    try:
        with Image.open(image_path) as photo:
            image = np.asarray(photo.convert("RGB"))
        corners = find_label_corners(image)
        if corners is None:
            return False, False, None
        rectify_label(image, corners)
        distances = np.linalg.norm(corners - np.asarray(expected), axis=1)
        return True, bool(distances.max() <= 10), None
    except Exception as error:
        return False, False, f"{type(error).__name__}: {error}"


def _provenance(dataset_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Record measured input, source and bundled-model fingerprints without timestamps."""
    import rapidocr_onnxruntime

    digest = hashlib.sha256()
    root = dataset_dir.resolve()
    names = ["manifest.json"] + [entry[key] for entry in manifest["files"] for key in ("image", "ground_truth")]
    for name in sorted(names):
        digest.update(name.encode("utf-8") + b"\0")
        try:
            content = (root / name).read_bytes()
        except OSError:
            content = b"UNREADABLE_INPUT"
        digest.update(hashlib.sha256(content).digest())
    source_root = Path(__file__).resolve().parents[1]
    source_names = [
        "cv/eval_extract.py",
        "cv/extract.py",
        "cv/preprocess.py",
        "cv/symbols.py",
        "cv/verify.py",
        "cv/ocr.py",
        "cv/barcode.py",
        "gen/generate_dataset.py",
        "gen/smoke_label.py",
        "gen/augment.py",
        "gen/symbols.py",
        "gen/render.py",
    ]
    model_root = Path(rapidocr_onnxruntime.__file__).parent / "models"
    return {
        "seed": manifest["seed"],
        "total_images": manifest["total_images"],
        "dataset_sha256": digest.hexdigest(),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "settings": SETTINGS,
        "packages": {
            name: version(name)
            for name in (
                "Pillow",
                "numpy",
                "opencv-python",
                "zxing-cpp",
                "rapidocr-onnxruntime",
                "onnxruntime",
                "pydantic",
            )
        },
        "source_sha256": {
            f"src/{name}": hashlib.sha256((source_root / name).read_bytes()).hexdigest() for name in source_names
        },
        "template_sha256": hashlib.sha256(TEMPLATE_PATH.read_bytes()).hexdigest(),
        "model_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(model_root.glob("*.onnx"))
        },
    }


def evaluate_dataset(dataset_dir: Path) -> dict[str, Any]:
    """Score all images with fixed extraction defaults and explicit failure denominators."""
    manifest, samples = _load_dataset(dataset_dir)
    conditions = {
        condition: {
            "images": 0,
            "decoded": 0,
            "gs1_exact": 0,
            "expected_symbols": 0,
            "matched_symbols": 0,
            "exact_symbol_sets": 0,
            "symbol_iou_sum": 0.0,
            "symbol_iou_pairs": 0,
            "symbol_false_positives": 0,
            "detected": 0,
            "corrected_within_10px": 0,
            "extraction_failures": 0,
            "geometry_failures": 0,
            "gs1_per_ai": {ai: 0 for ai in AIS},
            "ocr": {field: {"edits": 0, "reference_characters": 0, "observed": 0} for field in FIELDS},
            "warning_images": {},
        }
        for condition in CONDITIONS
    }
    records = []
    for image_path, truth in samples:
        counts = conditions[truth["condition"]]
        counts["images"] += 1
        failure = None
        fields = {}
        barcodes = []
        symbols = []
        try:
            extraction = LabelExtraction.model_validate(extract_label(image_path))
            fields, barcodes, symbols, warnings = (
                extraction.fields, extraction.barcodes, extraction.symbols, extraction.warnings
            )
        except Exception as error:
            failure = f"{type(error).__name__}: {error}"
            counts["extraction_failures"] += 1
            warnings = [f"EXTRACTION_FAILED: {failure}"]
        detected, accurate, geometry_failure = _probe_geometry(image_path, truth["label_quad_px"])
        counts["detected"] += int(detected)
        counts["corrected_within_10px"] += int(accurate)
        counts["geometry_failures"] += int(geometry_failure is not None)
        counts["decoded"] += int(bool(barcodes))
        expected_symbols = {}
        for item in truth["symbols"]:
            quad = np.asarray(item["quad_px"], dtype=float)
            left, top = quad.min(axis=0)
            right, bottom = quad.max(axis=0)
            expected_symbols[item["name"]] = (float(left), float(top), float(right - left), float(bottom - top))
        observed_names = [symbol.name for symbol in symbols]
        counts["expected_symbols"] += len(expected_symbols)
        counts["exact_symbol_sets"] += int(
            len(observed_names) == len(expected_symbols) and set(observed_names) == set(expected_symbols)
        )
        for symbol in symbols:
            if symbol.name not in expected_symbols:
                counts["symbol_false_positives"] += 1
                continue
            iou = _box_iou(symbol.bbox, expected_symbols[symbol.name])
            counts["symbol_iou_sum"] += iou
            counts["symbol_iou_pairs"] += 1
            counts["matched_symbols"] += int(iou >= 0.5)
        parsed = barcodes[0].parsed if len(barcodes) == 1 else {}
        for ai in AIS:
            counts["gs1_per_ai"][ai] += int(parsed.get(ai) == truth["barcode_ais"][ai])
        counts["gs1_exact"] += int(parsed == truth["barcode_ais"])
        field_errors = []
        for field in FIELDS:
            reference = truth["fields"][field]
            observed = fields.get(field, "")
            edits = edit_distance(reference, observed)
            counts["ocr"][field]["edits"] += edits
            counts["ocr"][field]["reference_characters"] += len(reference)
            counts["ocr"][field]["observed"] += int(field in fields)
            if edits:
                field_errors.append({"field": field, "reference": reference, "observed": observed, "edits": edits})
        for code in sorted({warning.split(":", 1)[0] for warning in warnings}):
            counts["warning_images"][code] = counts["warning_images"].get(code, 0) + 1
        records.append(
            {
                "image": image_path.relative_to(dataset_dir.resolve()).as_posix(),
                "condition": truth["condition"],
                "extraction_error": failure,
                "geometry_error": geometry_failure,
                "field_errors": field_errors,
            }
        )
    return {"conditions": conditions, "records": records, "provenance": _provenance(dataset_dir, manifest)}


def _fraction(numerator: int, denominator: int) -> str:
    """Format a measured count and rate while keeping zero denominators explicit."""
    return (
        f"{numerator}/{denominator} ({100 * numerator / denominator:.2f}%)" if denominator else f"{numerator}/0 (N/A)"
    )


def _cell(text: str) -> str:
    """Escape observed text for a Markdown table without hiding whitespace changes."""
    return json.dumps(text, ensure_ascii=True).replace("|", "\\|").replace("`", "&#96;")


def render_report(evaluation: dict[str, Any]) -> str:
    """Render only computed counts, errors and provenance into a deterministic report."""
    provenance = evaluation["provenance"]
    lines = [
        "# Synthetic device-label extraction baseline",
        "",
        f"Seed: {provenance['seed']}. Images evaluated: {provenance['total_images']}.",
        "",
        "Synthetic device labels from one template family do not validate real-photo performance.",
        "The extractor and its warning thresholds were not tuned during this measurement step.",
        "",
        "## Metric definitions",
        "",
        "- OCR character error rate (CER) is total edit distance divided by total reference characters,",
        "  separately per field and condition. Insertions, deletions and substitutions each cost one.",
        "  Case, spaces and punctuation count; nothing is normalized.",
        "  Missing or ambiguous fields use an empty hypothesis, so all reference characters count as deletions.",
        "  CER can exceed 100% when insertions outnumber reference characters.",
        "  Characters are Python Unicode code points.",
        "- Barcode decode rate counts images with any decoded symbol, including failed GS1 parses.",
        "- Exact GS1 accuracy requires one decoded symbol. Per-AI and all-four matches use all images as denominator.",
        "  Missing decodes and ambiguous multiple symbols count as incorrect.",
        "  Conditional all-four accuracy is also shown, with decoded images as denominator.",
        "- Detection/correction success requires four detected corners, successful rectification, and every corner",
        "  within 10 original-image pixels of known corners. A deterministic geometry probe reruns the unchanged",
        "  detector because the shared schema does not expose internal corners. It is independent of OCR success.",
        "- A symbol match needs the expected synthetic name and axis-aligned box intersection over union (IoU)",
        "  of at least 0.50. Mean same-name IoU is also reported. The two pictograms are not certified ISO artwork.",
        "- Extraction exceptions stay in denominators, with empty text hypotheses and failed barcode results.",
        "  Missing or malformed ground truth aborts evaluation rather than inventing references.",
        "",
        "## Per-condition summary",
        "",
        "| Condition | Images | Barcode decoded | All four AIs exact | All four exact given decode | "
        "Boundary detected | Corrected within 10 px | Symbols IoU >= 0.50 | Exact symbol sets | Mean symbol IoU | "
        "Extraction exceptions |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for condition, counts in evaluation["conditions"].items():
        total = counts["images"]
        decoded, gs1, detected, corrected, failures = (
            counts[key] for key in ("decoded", "gs1_exact", "detected", "corrected_within_10px", "extraction_failures")
        )
        mean_iou = counts["symbol_iou_sum"] / counts["symbol_iou_pairs"] if counts["symbol_iou_pairs"] else 0.0
        lines.append(
            f"| {condition} | {total} | {_fraction(decoded, total)} | {_fraction(gs1, total)} | "
            f"{_fraction(gs1, decoded)} | {_fraction(detected, total)} | "
            f"{_fraction(corrected, total)} | {_fraction(counts['matched_symbols'], counts['expected_symbols'])} | "
            f"{_fraction(counts['exact_symbol_sets'], total)} | {mean_iou:.3f} | {_fraction(failures, total)} |"
        )
    lines += [
        "",
        "## OCR character error by field",
        "",
        "| Condition | Field | CER | Edits / reference characters | Images | Field present |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for condition, counts in evaluation["conditions"].items():
        for field, score in counts["ocr"].items():
            edits, characters = score["edits"], score["reference_characters"]
            lines.append(
                f"| {condition} | {field} | {100 * edits / characters:.2f}% | {edits}/{characters} | "
                f"{counts['images']} | {score['observed']}/{counts['images']} |"
            )
    lines += [
        "",
        "## Exact GS1 matches per AI",
        "",
        "| Condition | AI 01 | AI 17 | AI 10 | AI 21 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for condition, counts in evaluation["conditions"].items():
        lines.append(
            f"| {condition} | " + " | ".join(_fraction(counts["gs1_per_ai"][ai], counts["images"]) for ai in AIS) + " |"
        )
    lines += [
        "",
        "## Warning counts",
        "",
        "Counts are images with each warning code, not individual occurrences. Informational warnings are included.",
        "",
        "| Condition | Warning | Images |",
        "| --- | --- | --- |",
    ]
    for condition, counts in evaluation["conditions"].items():
        for warning, count in sorted(counts["warning_images"].items()):
            lines.append(f"| {condition} | {warning} | {count}/{counts['images']} |")
    lines += [
        "",
        "## Largest text errors",
        "",
        "Up to three field errors per condition, sorted by edit count, filename and field. Quotes expose whitespace.",
        "",
        "| Condition | Image | Field | Reference | Observed | Edits |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for condition in CONDITIONS:
        errors = [
            {**error, "image": record["image"]}
            for record in evaluation["records"]
            if record["condition"] == condition
            for error in record["field_errors"]
        ]
        for error in sorted(errors, key=lambda item: (-item["edits"], item["image"], item["field"]))[:3]:
            lines.append(
                f"| {condition} | {error['image']} | {error['field']} | {_cell(error['reference'])} | "
                f"{_cell(error['observed'])} | {error['edits']} |"
            )
    lines += ["", "## Evaluation failures", ""]
    failures = [record for record in evaluation["records"] if record["extraction_error"] or record["geometry_error"]]
    if not failures:
        lines.append(
            "No extraction or geometry-probe exceptions occurred. Decode and OCR errors are still reflected above."
        )
    for record in failures:
        lines.append(
            f"- {record['image']}: extraction={_cell(record['extraction_error'] or 'none')}; "
            f"geometry={_cell(record['geometry_error'] or 'none')}"
        )
    lines += [
        "",
        "## Reproduce",
        "",
        "Generate inputs once, then run the evaluator with one command:",
        "",
        "```bash",
        f"python -m src.gen.generate_dataset --output-dir data/synthetic/task1 --seed {provenance['seed']} "
        f"--labels-per-condition {evaluation['conditions']['clean']['images']}",
        "python -m src.cv.eval_extract --dataset data/synthetic/task1 --output results/cv_extract.md",
        "```",
        "",
        f"Python: {provenance['python']}. Platform: {provenance['platform']}.",
        f"Extraction defaults: {json.dumps(provenance['settings'], sort_keys=True)}.",
        "Install recorded dependencies from `src/gen/requirements-cv.txt`. Models are bundled with RapidOCR.",
        "",
        "| Package | Version |",
        "| --- | --- |",
    ]
    lines += [f"| {name} | {value} |" for name, value in provenance["packages"].items()]
    lines += [
        "",
        "### SHA-256 fingerprints",
        "",
        f"Dataset contents: `{provenance['dataset_sha256']}`.",
        f"Template: `{provenance['template_sha256']}`.",
        "",
        "| File | SHA-256 |",
        "| --- | --- |",
    ]
    for name, fingerprint in {**provenance["source_sha256"], **provenance["model_sha256"]}.items():
        lines.append(f"| {name} | {fingerprint} |")
    lines += [
        "",
        "## Limits",
        "",
        "- One synthetic template family does not establish performance on real labels or other layouts.",
        "- GS1 values include an all-zero test identifier. Syntax matches do not prove allocation or authenticity.",
        "- Fields preserve printed prefixes and OCR whitespace errors. Barcode values never replace text hypotheses.",
        "- Confidence and blur warnings are provisional. High-confidence errors and noise-masked blur remain possible.",
        "- Symbols are two simplified synthetic pictograms in one template family, not certified ISO artwork.",
        "  The measured set has no symbol-absent examples and cannot measure false-positive behavior broadly.",
        "- All dataset files were read only; this report is generated from the computed results.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Evaluate a complete dataset, write its report and print the computed summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/cv_extract.md"))
    args = parser.parse_args(argv)
    try:
        if args.output.resolve().is_relative_to(args.dataset.resolve()):
            raise ValueError("Report output must be outside the read-only dataset directory")
        evaluation = evaluate_dataset(args.dataset)
        report = render_report(evaluation)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    print(f"Evaluated {evaluation['provenance']['total_images']} images; extraction defaults unchanged")
    for condition, counts in evaluation["conditions"].items():
        total = counts["images"]
        print(
            f"{condition}: decoded={counts['decoded']}/{total}, all_ais_match={counts['gs1_exact']}/{total}, "
            f"corrected_within_10px={counts['corrected_within_10px']}/{total}, "
            f"symbols_iou_050={counts['matched_symbols']}/{counts['expected_symbols']}, "
            f"exact_symbol_sets={counts['exact_symbol_sets']}/{total}, "
            f"extraction_exceptions={counts['extraction_failures']}"
        )
        print(
            "  CER: "
            + ", ".join(
                f"{field}={100 * score['edits'] / score['reference_characters']:.2f}%"
                for field, score in counts["ocr"].items()
            )
        )
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
