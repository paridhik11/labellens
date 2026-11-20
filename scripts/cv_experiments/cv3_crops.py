"""Rejected CV3 crop prototype, retained for audit only, outside the extractor."""
from __future__ import annotations

import re
from typing import Any

from src.common.schemas import OcrBlock


def anchored_crops(
    image: Any, blocks: list[OcrBlock], *, min_confidence: float = 0.5,
) -> list[tuple[str, tuple[int, int, int, int], Any]]:
    """Cut observed keyed rows at fixed margins and 3x scale; return input-pixel boxes."""
    import cv2

    height, width = image.shape[:2]
    crops = []
    seen = set()
    for block in blocks:
        match = re.match(r'^\s*[\[({]?(LOT|BATCH|EXP|EXPIRY)\b', block.text, re.I)
        if not match or block.conf < min_confidence:
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


def read_anchors(
    image: Any, blocks: list[OcrBlock], *, min_confidence: float = 0.5,
) -> tuple[dict[str, str], list[OcrBlock]]:
    """OCR crop pixels and abstain when observed crop readings disagree."""
    from src.cv.ocr import read_text_robust
    from src.cv.photo_cv2 import map_cv2_fields

    observed: list[OcrBlock] = []
    values: dict[str, set[str]] = {}
    for field, box, crop in anchored_crops(image, blocks, min_confidence=min_confidence):
        readings = read_text_robust(crop, pad_ratios=(0.3,), dither_pad_ratios=())
        fields, _ = map_cv2_fields(readings, min_confidence=min_confidence)
        if field in fields:
            values.setdefault(field, set()).add(fields[field])
        observed.extend(b.model_copy(update={'bbox': (
            box[0]+b.bbox[0]/3, box[1]+b.bbox[1]/3, b.bbox[2]/3, b.bbox[3]/3,
        )}) for b in readings)
    return {field: next(iter(v)) for field, v in values.items() if len(v) == 1}, observed
