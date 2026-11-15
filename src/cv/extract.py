"""Assemble extraction for the single synthetic test-device template family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import cv2
import numpy as np
from PIL import Image

from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock
from src.cv.barcode import decode_barcode_slot, decode_barcodes
from src.cv.barcode_blind import decode_barcode_slot_enhanced, decode_barcodes_blind
from src.cv.fields import map_fields_by_layout, normalise_field, reconcile_with_barcode
from src.cv.ocr import read_text_default as read_text
from src.cv.preprocess import _validate_image, find_label_corners, find_label_corners_fallback, rectify_label
from src.cv.symbols import NAMES, detect_symbols, detect_symbols_blind

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "gen" / "templates" / "test_device.json"
Mode = Literal["template", "blind"]


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


def _project_barcodes(
    results: list[BarcodeResult], inverse: np.ndarray, image_size: tuple[int, int]
) -> list[BarcodeResult]:
    """Map barcode boxes from the corrected label back to original-photo pixels."""
    return [
        result.model_copy(update={
            "bbox": project_box(result.bbox, inverse, image_size) if result.bbox is not None else None,
        })
        for result in results
    ]


def _without_not_decoded(warnings: list[str]) -> list[str]:
    """Drop earlier "not decoded" notes once a later attempt has succeeded."""
    return [warning for warning in warnings if not warning.startswith("BARCODE_NOT_DECODED:")]


def _template_barcodes(
    barcodes: list[BarcodeResult], warnings: list[str], corrected: np.ndarray, inverse: np.ndarray,
    image_size: tuple[int, int],
) -> tuple[list[BarcodeResult], list[str], str | None]:
    """Template-assisted barcode chain: rectified label, then the known slot, then the deblurred slot."""
    if barcodes:
        return barcodes, warnings, "original_image"
    retried, retry_warnings = _decode_safely(corrected)
    if retried:
        return (
            _project_barcodes(retried, inverse, image_size),
            [*_without_not_decoded(warnings), *retry_warnings, "BARCODE_DECODED_AFTER_RECTIFICATION"],
            "rectified_image",
        )
    try:
        slot_results, slot_warnings = decode_barcode_slot(corrected)
        method = "template_slot"
        if not slot_results:
            enhanced, enhanced_warnings, attempt = decode_barcode_slot_enhanced(corrected)
            if enhanced:
                slot_results, slot_warnings, method = enhanced, enhanced_warnings, f"template_slot_{attempt}"
    except Exception as error:
        slot_results = []
        slot_warnings = [f"BARCODE_SLOT_ENGINE_FAILED: {type(error).__name__}: {error}"]
    if slot_results:
        return (
            _project_barcodes(slot_results, inverse, image_size),
            [
                *_without_not_decoded([*warnings, *retry_warnings, *slot_warnings]),
                "BARCODE_DECODED_FROM_TEMPLATE_SLOT",
            ],
            method,
        )
    return [], [*warnings, *retry_warnings, *slot_warnings], None


def _blind_barcodes(
    barcodes: list[BarcodeResult], warnings: list[str], image: np.ndarray, corrected: np.ndarray | None,
    inverse: np.ndarray | None, image_size: tuple[int, int],
) -> tuple[list[BarcodeResult], list[str], str | None]:
    """Blind barcode chain: no slot position. Located regions on the label, then on the photo."""
    if barcodes:
        return barcodes, warnings, "original_image"
    try:
        if corrected is not None and inverse is not None:
            results, blind_warnings, attempt = decode_barcodes_blind(corrected)
            if results:
                return (
                    _project_barcodes(results, inverse, image_size),
                    [*_without_not_decoded(warnings), *blind_warnings, "BARCODE_DECODED_BLIND"],
                    f"rectified_{attempt}",
                )
        results, blind_warnings, attempt = decode_barcodes_blind(image)
        if results:
            return (
                results, [*_without_not_decoded(warnings), *blind_warnings, "BARCODE_DECODED_BLIND"],
                f"photo_{attempt}",
            )
    except Exception as error:
        return [], [*warnings, f"BARCODE_ENGINE_FAILED: {type(error).__name__}: {error}"], None
    return [], warnings, None


def _postcorrect(fields: dict[str, str], barcodes: list[BarcodeResult]) -> tuple[dict[str, str], list[str]]:
    """Apply format rules, then let a single decoded barcode settle 0/O style doubts."""
    corrected = {field: normalise_field(field, text) for field, text in fields.items()}
    notes: list[str] = []
    if len(barcodes) == 1 and barcodes[0].parsed:
        corrected, notes = reconcile_with_barcode(corrected, barcodes[0].parsed)
    return corrected, notes


def extract_label_modes(
    image_path: str | Path,
    *,
    modes: tuple[Mode, ...] = ("template",),
    min_confidence: float = 0.8,
    blur_threshold: float = 100.0,
    postcorrect: bool = False,
    field_confidence: float = 0.5,
) -> dict[str, tuple[LabelExtraction, dict[str, Any]]]:
    """Run the extraction once and return one result per requested mode.

    Label detection, rectification, the plain barcode attempt and OCR are
    shared, so asking for both modes costs little more than one. Each value is
    the ``LabelExtraction`` and a details dictionary with the detected label
    corners, the corner method, the name of the barcode attempt that worked and
    the fields before post-correction (for evaluation only).

    Mode "template" uses the known test-device layout for the barcode slot,
    the field slots and the symbol windows. Mode "blind" uses none of it:
    barcodes are located in the pixels, fields are named from their text and
    arrangement, symbols are searched over the whole label, and when no label
    boundary is found the whole photo is read instead.
    """
    if not np.isfinite(min_confidence) or not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be finite and between zero and one")
    if not np.isfinite(blur_threshold) or blur_threshold < 0:
        raise ValueError("blur_threshold must be finite and nonnegative")
    if not modes or set(modes) - {"template", "blind"}:
        raise ValueError("modes must be chosen from template and blind")
    path = Path(image_path)
    with Image.open(path) as photo:
        image = np.asarray(photo.convert("RGB"))
    _validate_image(image)
    image_size = (image.shape[1], image.shape[0])
    plain_barcodes, plain_warnings = _decode_safely(image)
    shared_warnings: list[str] = []
    corners = find_label_corners(image)
    corner_method = "contour" if corners is not None else None
    if corners is None:
        corners = find_label_corners_fallback(image)
        if corners is not None:
            corner_method = "hull_fallback"
            shared_warnings.append("LABEL_FOUND_BY_FALLBACK: boundary rebuilt from a partly hidden outline")
    corrected = inverse = None
    if corners is not None:
        corrected, forward = rectify_label(image, corners)
        inverse = np.linalg.inv(forward)
    need_photo_ocr = corrected is None and "blind" in modes
    ocr_image = corrected if corrected is not None else (image if need_photo_ocr else None)
    blocks: list[OcrBlock] = []
    ocr_warnings: list[str] = []
    if ocr_image is not None:
        score = blur_score(ocr_image)
        if score < blur_threshold:
            ocr_warnings.append(
                f"BLUR_SUSPECTED: Laplacian variance={score:.3f} below threshold={blur_threshold:.3f}"
            )
        try:
            blocks = read_text(ocr_image)
        except Exception as error:
            ocr_warnings.append(f"OCR_FAILED: {type(error).__name__}: {error}")
        if not blocks:
            ocr_warnings.append("OCR_NO_TEXT: no text observations available")
        for index, block in enumerate(blocks):
            if block.conf < min_confidence:
                ocr_warnings.append(
                    f"LOW_OCR_CONFIDENCE: block {index} score={block.conf:.3f} below {min_confidence:.3f}"
                )
    projected_blocks = [
        block if inverse is None else block.model_copy(update={"bbox": project_box(block.bbox, inverse, image_size)})
        for block in blocks
    ]
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    outputs: dict[str, tuple[LabelExtraction, dict[str, Any]]] = {}
    for mode in modes:
        output = LabelExtraction(label_id=path.stem)
        details: dict[str, Any] = {
            "corners": None if corners is None else np.asarray(corners).tolist(),
            "corner_method": corner_method,
            "barcode_method": None,
            "raw_fields": {},
        }
        if mode == "template":
            output.warnings.append("TEMPLATE_ASSUMED: test_device_v1; template identity has not been verified")
        else:
            output.warnings.append("BLIND_MODE: no template layout used; field names come from text rules")
        if corrected is None and mode == "template":
            output.barcodes = plain_barcodes
            details["barcode_method"] = "original_image" if plain_barcodes else None
            output.warnings.extend(plain_warnings)
            output.warnings.extend([
                "SYMBOL_DETECTION_NOT_RUN",
                "LABEL_NOT_FOUND: no suitable boundary; needs human review",
                "OCR_NOT_RUN: no corrected label geometry",
                "FIELD_MAPPING_SKIPPED: no corrected label geometry",
            ])
            output.warnings = list(dict.fromkeys(output.warnings))
            outputs[mode] = (output, details)
            continue
        output.warnings.extend(shared_warnings)
        if corrected is None:
            output.warnings.append("LABEL_NOT_FOUND: no suitable boundary; the whole photo was read instead")
        try:
            if mode == "template":
                detected = detect_symbols(corrected)
            else:
                detected = detect_symbols_blind(corrected if corrected is not None else image)
            output.symbols = [
                symbol if inverse is None
                else symbol.model_copy(update={"bbox": project_box(symbol.bbox, inverse, image_size)})
                for symbol in detected
            ]
            for name in NAMES:
                if not any(symbol.name == name for symbol in detected):
                    output.warnings.append(f"SYMBOL_NOT_DETECTED: {name}")
        except Exception as error:
            output.warnings.append(f"SYMBOL_DETECTION_FAILED: {type(error).__name__}: {error}")
        if mode == "template":
            barcodes, barcode_warnings, method = _template_barcodes(
                plain_barcodes, list(plain_warnings), corrected, inverse, image_size
            )
        else:
            barcodes, barcode_warnings, method = _blind_barcodes(
                plain_barcodes, list(plain_warnings), image, corrected, inverse, image_size
            )
        output.barcodes = barcodes
        details["barcode_method"] = method
        output.warnings.extend(barcode_warnings)
        if len(barcodes) > 1:
            output.warnings.append(
                f"MULTIPLE_BARCODES: {len(barcodes)} symbols decoded; none selected automatically"
            )
        output.warnings.extend(ocr_warnings)
        output.ocr_blocks = list(projected_blocks)
        usable = [block for block in blocks if block.conf >= field_confidence]
        if mode == "template":
            fields, field_warnings = map_fields(usable, (corrected.shape[1], corrected.shape[0]), template)
        else:
            fields, field_warnings = map_fields_by_layout(blocks, min_confidence=field_confidence)
        details["raw_fields"] = dict(fields)
        if postcorrect:
            fields, notes = _postcorrect(fields, barcodes)
            field_warnings = [*field_warnings, *notes]
        output.fields = fields
        output.warnings.extend(field_warnings)
        output.warnings = list(dict.fromkeys(output.warnings))
        outputs[mode] = (output, details)
    return outputs


def extract_label(
    image_path: str | Path,
    *,
    min_confidence: float = 0.8,
    blur_threshold: float = 100.0,
    mode: Mode = "template",
    postcorrect: bool = False,
) -> LabelExtraction:
    """Extract one label photo into the unchanged shared schema.

    All returned boxes use original-image x, y, width, height coordinates.
    Read only the image (and, in "template" mode, the fixed template layout),
    never a ground-truth sidecar. Warning thresholds are provisional settings,
    not calibrated accuracy claims. Unreadable files and unrecoverable
    geometry errors raise; OCR and barcode engine failures become warnings.

    ``mode`` is "template" (uses the known test-device layout) or "blind"
    (uses no layout knowledge, see ``extract_label_modes``). With
    ``postcorrect`` the field texts are normalised by format rules and
    0/O style doubts in lot and expiry are settled by the barcode; without it
    the fields are exactly what OCR read.
    """
    return extract_label_modes(
        image_path, modes=(mode,), min_confidence=min_confidence, blur_threshold=blur_threshold,
        postcorrect=postcorrect,
    )[mode][0]


def main(argv: list[str] | None = None) -> int:
    """Print one extraction as JSON, declaring original-image box coordinates."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--blur-threshold", type=float, default=100.0)
    parser.add_argument("--mode", choices=["template", "blind"], default="template")
    parser.add_argument("--postcorrect", action="store_true", help="Apply format rules to the field texts")
    args = parser.parse_args(argv)
    try:
        result = extract_label(
            args.image, min_confidence=args.min_confidence, blur_threshold=args.blur_threshold,
            mode=args.mode, postcorrect=args.postcorrect,
        )
    except (OSError, ValueError, np.linalg.LinAlgError) as error:
        parser.error(str(error))
    print("Coordinates: input_image; boxes=x,y,width,height")
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
