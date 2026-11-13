"""Assemble extraction for the single synthetic test-device template family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock
from src.cv.barcode import decode_barcodes
from src.cv.ocr import read_text
from src.cv.preprocess import _validate_image, find_label_corners, rectify_label
from src.cv.symbols import NAMES, detect_symbols

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "gen" / "templates" / "test_device.json"


def map_fields(
    blocks: list[OcrBlock], image_size: tuple[int, int], template: dict[str, Any]
) -> tuple[dict[str, str], list[str]]:
    """Assign one OCR block per text slot using normalized corrected-image centres.

    Preserve text verbatim. Missing or multiple candidate blocks leave a field
    absent with a warning. Text outside the template's text slots is retained
    by the caller as an OCR observation, without becoming a product field.
    """
    width, height = image_size
    if width < 2 or height < 2:
        raise ValueError("Corrected image must have at least two pixels per side")
    slots = [slot for slot in template["slots"] if slot["type"] == "text"]
    candidates: dict[str, list[OcrBlock]] = {slot["field"]: [] for slot in slots}
    warnings = []
    for index, block in enumerate(blocks):
        if not block.text.strip():
            continue
        x, y, box_width, box_height = block.bbox
        centre_x = (x + box_width / 2) / (width - 1) * template["size_mm"]["w"]
        centre_y = (y + box_height / 2) / (height - 1) * template["size_mm"]["h"]
        matches = []
        for slot in slots:
            sx, sy, sw, sh = slot["bbox_mm"]
            if sx <= centre_x <= sx + sw and sy <= centre_y <= sy + sh:
                matches.append(slot["field"])
        if len(matches) > 1:
            warnings.append(f"FIELD_AMBIGUOUS: OCR block {index} matches multiple slots")
        elif matches:
            candidates[matches[0]].append(block)
    fields = {}
    for field, matching in candidates.items():
        if len(matching) == 1:
            fields[field] = matching[0].text
        elif not matching:
            warnings.append(f"FIELD_MISSING: {field}")
        else:
            warnings.append(f"FIELD_AMBIGUOUS: {field} has {len(matching)} candidate blocks")
    return fields, warnings


def project_box(
    box: tuple[float, float, float, float], matrix: np.ndarray, image_size: tuple[int, int]
) -> tuple[float, float, float, float]:
    """Project all four box corners and enclose them in the target image.

    The matrix maps the box's current coordinates to target-image coordinates.
    Return x, y, width, height clipped to the target canvas. Reject degenerate,
    nonfinite or infinity-crossing transformations instead of fabricating a box.
    """
    values = np.asarray(box, dtype=float)
    transform = np.asarray(matrix, dtype=float)
    width, height = image_size
    if values.shape != (4,) or not np.isfinite(values).all() or (values[2:] <= 0).any():
        raise ValueError("Box must have finite coordinates and positive width and height")
    if transform.shape != (3, 3) or not np.isfinite(transform).all() or width <= 0 or height <= 0:
        raise ValueError("Expected a finite 3 by 3 matrix and positive target dimensions")
    if np.linalg.matrix_rank(transform) < 3:
        raise ValueError("Projection matrix must be invertible")
    x, y, w, h = values
    corners = np.array([[x, y, 1], [x + w, y, 1], [x + w, y + h, 1], [x, y + h, 1]])
    homogeneous = corners @ transform.T
    denominator = homogeneous[:, 2]
    if not ((denominator > 1e-10).all() or (denominator < -1e-10).all()):
        raise ValueError("Box projection crosses infinity")
    points = homogeneous[:, :2] / denominator[:, None]
    if not np.isfinite(points).all():
        raise ValueError("Box projection is nonfinite")
    points[:, 0] = np.clip(points[:, 0], 0, width)
    points[:, 1] = np.clip(points[:, 1], 0, height)
    left, top = points.min(axis=0)
    right, bottom = points.max(axis=0)
    if left >= right or top >= bottom:
        raise ValueError("Projected box does not overlap the target image")
    return float(left), float(top), float(right - left), float(bottom - top)


def blur_score(image: np.ndarray) -> float:
    """Return grayscale Laplacian variance as a provisional sharpness indicator.

    Larger values generally indicate more edges. Noise also raises this score,
    so it does not establish whether text is readable or guarantee lack of blur.
    """
    _validate_image(image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _decode_safely(image: np.ndarray) -> tuple[list[BarcodeResult], list[str]]:
    """Keep a decoder failure explicit while allowing the remaining extraction."""
    try:
        return decode_barcodes(image)
    except Exception as error:
        return [], [f"BARCODE_ENGINE_FAILED: {type(error).__name__}: {error}"]


def extract_label(
    image_path: str | Path, *, min_confidence: float = 0.8, blur_threshold: float = 100.0
) -> LabelExtraction:
    """Extract the test-device family into the unchanged shared schema.

    All returned boxes use original-image x, y, width, height coordinates.
    Read only the image and fixed template layout, never a ground-truth sidecar.
    Warning thresholds are provisional settings, not calibrated accuracy claims.
    Unreadable files and unrecoverable geometry errors raise; OCR and barcode
    engine failures become warnings with the original error type and message.
    """
    if not np.isfinite(min_confidence) or not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be finite and between zero and one")
    if not np.isfinite(blur_threshold) or blur_threshold < 0:
        raise ValueError("blur_threshold must be finite and nonnegative")
    path = Path(image_path)
    with Image.open(path) as photo:
        image = np.asarray(photo.convert("RGB"))
    _validate_image(image)
    output = LabelExtraction(label_id=path.stem)
    output.warnings.append("TEMPLATE_ASSUMED: test_device_v1; template identity has not been verified")
    barcodes, barcode_warnings = _decode_safely(image)
    corners = find_label_corners(image)
    if corners is None:
        output.barcodes = barcodes
        output.warnings.extend(barcode_warnings)
        output.warnings.extend([
            "SYMBOL_DETECTION_NOT_RUN",
            "LABEL_NOT_FOUND: no suitable boundary; needs human review",
            "OCR_NOT_RUN: no corrected label geometry",
            "FIELD_MAPPING_SKIPPED: no corrected label geometry",
        ])
        return output
    corrected, forward = rectify_label(image, corners)
    inverse = np.linalg.inv(forward)
    image_size = (image.shape[1], image.shape[0])
    try:
        detected_symbols = detect_symbols(corrected)
        output.symbols = [
            symbol.model_copy(update={"bbox": project_box(symbol.bbox, inverse, image_size)})
            for symbol in detected_symbols
        ]
        for name in NAMES:
            if not any(symbol.name == name for symbol in detected_symbols):
                output.warnings.append(f"SYMBOL_NOT_DETECTED: {name}")
    except Exception as error:
        output.warnings.append(f"SYMBOL_DETECTION_FAILED: {type(error).__name__}: {error}")
    if not barcodes:
        retried, retry_warnings = _decode_safely(corrected)
        if retried:
            barcodes = [
                result.model_copy(update={
                    "bbox": project_box(result.bbox, inverse, image_size) if result.bbox is not None else None,
                })
                for result in retried
            ]
            barcode_warnings = [
                warning for warning in barcode_warnings if not warning.startswith("BARCODE_NOT_DECODED:")
            ]
            barcode_warnings.extend(retry_warnings)
            barcode_warnings.append("BARCODE_DECODED_AFTER_RECTIFICATION")
        else:
            barcode_warnings.extend(retry_warnings)
    output.barcodes = barcodes
    output.warnings.extend(barcode_warnings)
    if len(barcodes) > 1:
        output.warnings.append(f"MULTIPLE_BARCODES: {len(barcodes)} symbols decoded; none selected automatically")
    score = blur_score(corrected)
    if score < blur_threshold:
        output.warnings.append(f"BLUR_SUSPECTED: Laplacian variance={score:.3f} below threshold={blur_threshold:.3f}")
    try:
        corrected_blocks = read_text(corrected)
    except Exception as error:
        corrected_blocks = []
        output.warnings.append(f"OCR_FAILED: {type(error).__name__}: {error}")
    if not corrected_blocks:
        output.warnings.append("OCR_NO_TEXT: no text observations available")
    for index, block in enumerate(corrected_blocks):
        if block.conf < min_confidence:
            output.warnings.append(
                f"LOW_OCR_CONFIDENCE: block {index} score={block.conf:.3f} below {min_confidence:.3f}"
            )
        output.ocr_blocks.append(block.model_copy(update={"bbox": project_box(block.bbox, inverse, image_size)}))
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    output.fields, field_warnings = map_fields(
        corrected_blocks, (corrected.shape[1], corrected.shape[0]), template
    )
    output.warnings.extend(field_warnings)
    output.warnings = list(dict.fromkeys(output.warnings))
    return output


def main(argv: list[str] | None = None) -> int:
    """Print one extraction as JSON, declaring original-image box coordinates."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--blur-threshold", type=float, default=100.0)
    args = parser.parse_args(argv)
    try:
        result = extract_label(args.image, min_confidence=args.min_confidence, blur_threshold=args.blur_threshold)
    except (OSError, ValueError, np.linalg.LinAlgError) as error:
        parser.error(str(error))
    print("Coordinates: input_image; boxes=x,y,width,height")
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
