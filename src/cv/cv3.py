"""Opt-in CV3 experiments; barcode prefill never replaces observed printed fields."""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from src.common.schemas import BarcodeResult, OcrBlock


def barcode_prefill(barcodes: list[BarcodeResult]) -> dict[str, dict[str, Any]]:
    """Return validated AI 10/17 suggestions from one unambiguous decoded GS1 symbol.

    Reparse the decoded raw payload instead of trusting arbitrary parsed metadata.
    Multiple symbols, unsupported payloads and invalid dates yield no suggestions.
    The result is a record-entry suggestion, never a claim about visible print.
    """
    from src.cv.barcode import parse_gs1

    if len(barcodes) != 1:
        return {}
    barcode = barcodes[0]
    try:
        parsed = parse_gs1(barcode.raw)
    except ValueError:
        return {}
    if parsed != barcode.parsed:
        return {}
    result = {}
    for field, ai in [('lot', '10'), ('expiry', '17')]:
        value = parsed.get(ai)
        if not value:
            continue
        if ai == '17':
            try:
                value = date(2000+int(value[:2]), int(value[2:4]), int(value[4:])).isoformat()
            except ValueError:
                continue
        result[field] = {'value': value, 'ai': ai, 'source': 'decoded_gs1',
                         'raw': barcode.raw, 'bbox_input_px': barcode.bbox}
    return result


def anchored_crops(image: Any, blocks: list[OcrBlock]) -> list[tuple[str, tuple[int, int, int, int], Any]]:
    """Crop keyed rows from original pixels, with fixed margins and 3x upscaling.

    Exact observed LOT/BATCH/EXP keys anchor a short row to their right, including
    one line below. No template, reference value or barcode text positions enter.
    Returned boxes are left, top, right, bottom in the original input image.
    """
    import cv2

    height, width = image.shape[:2]
    crops = []
    seen = set()
    for block in blocks:
        match = re.match(r'^\s*[\[({]?(LOT|BATCH|EXP|EXPIRY)\b', block.text, re.I)
        if not match or block.conf < 0.5:
            continue
        field = 'lot' if match[1].upper() in ('LOT', 'BATCH') else 'expiry'
        x, y, w, h = block.bbox
        box = (max(0, int(x-h)), max(0, int(y-.5*h)),
               min(width, int(x+max(w, 18*h)+h)), min(height, int(y+2.5*h)))
        if box in seen or box[2] <= box[0] or box[3] <= box[1]:
            continue
        seen.add(box)
        crop = image[box[1]:box[3], box[0]:box[2]]
        crops.append((field, box, cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)))
    return crops


def read_anchors(image: Any, blocks: list[OcrBlock]) -> tuple[dict[str, str], list[OcrBlock]]:
    """Read anchored crop pixels and accept a field only when crop readings agree."""
    from src.cv.ocr import read_text_robust
    from src.cv.photo_cv2 import map_cv2_fields

    observed: list[OcrBlock] = []
    values: dict[str, set[str]] = {}
    for field, box, crop in anchored_crops(image, blocks):
        readings = read_text_robust(crop, pad_ratios=(0.3,), dither_pad_ratios=())
        fields, _ = map_cv2_fields(readings, min_confidence=0.5)
        if field in fields:
            values.setdefault(field, set()).add(fields[field])
        observed.extend(b.model_copy(update={'bbox': (
            box[0]+b.bbox[0]/3, box[1]+b.bbox[1]/3, b.bbox[2]/3, b.bbox[3]/3,
        )}) for b in readings)
    return {field: next(iter(v)) for field, v in values.items() if len(v) == 1}, observed


def available_ocr_models() -> dict[str, Any]:
    """Inspect installed bundled models without importing CV runtimes or downloading."""
    import importlib.util
    from importlib.metadata import PackageNotFoundError, distribution

    try:
        installed = distribution('rapidocr-onnxruntime')
    except PackageNotFoundError:
        return {'available': False, 'reason': 'rapidocr-onnxruntime absent', 'fallback': 'existing OCR'}
    models = [str(p) for p in installed.files or [] if str(p).endswith('.onnx')]
    newer = [p for p in models if re.search(r'pp.?ocr.?v[56]', p, re.I)]
    return {'version': installed.version, 'models': models, 'newer_models': newer,
            'modern_api_available': importlib.util.find_spec('rapidocr') is not None,
            'available': bool(newer), 'fallback': 'existing OCR' if not newer else None}
