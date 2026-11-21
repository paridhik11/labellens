"""Opt-in CV2 evidence: upscale intact views before recognition and optionally vote."""
from __future__ import annotations

import subprocess
from typing import Any

from src.common.schemas import OcrBlock


def read_cv2(image: Any, *, view: str, to_original: Any, second_engine: bool = True, deadline: Any = None,
             search_side: int | None = None) -> Any:
    """Return upright, enlarged observations with the exact inverse coordinate mapping.

    The photo orientation is chosen by the existing pixel-only reader. A new
    intact full-view recognition pass prevents clipped tiles replacing titles.
    No template ratio or final-set annotations enter this function.
    """
    import cv2
    import numpy as np

    from src.cv.budget import expired, remaining
    from src.cv.ocr import read_text_robust
    from src.cv.ocr_vote import tesseract_lines, vote_lines
    from src.cv.photo_ocr import PhotoReading, choose_turn

    # Only the chosen quarter turn is used from the orientation pass (the final blocks come from the enlarged
    # read below), so the four crop passes of read_photo would be discarded. The turn is chosen with the same
    # rule as read_photo, optionally on a smaller copy of the view (search_side).
    turn, transform, complete = choose_turn(image, to_original=to_original, deadline=deadline,
                                            search_side=search_side)
    if expired(deadline):  # the enlarged second pass and Tesseract are skipped once the budget is gone
        return PhotoReading([], transform, 0.0, turn, view, False)
    upright = np.ascontiguousarray(np.rot90(image, turn))
    scale = min(4.0, max(1.0, 1800/max(upright.shape[:2])))
    enlarged = cv2.resize(upright, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    rapid = read_text_robust(enlarged, pad_ratios=(0.3,), dither_pad_ratios=())
    if second_engine:
        try:
            secondary = tesseract_lines(enlarged, timeout=None if deadline is None else max(1.0, remaining(deadline)))
            observations = vote_lines(rapid, secondary)
        except subprocess.TimeoutExpired:  # Tesseract ran past the budget: the vote is missing, say so
            observations, complete = rapid, False
    else:
        observations = rapid
    blocks = [b.model_copy(update={'bbox': tuple(float(v)/scale for v in b.bbox)}) for b in observations]
    score = sum(b.conf**2*sum(c.isalnum() for c in b.text) for b in blocks if b.conf >= 0.6)
    return PhotoReading(blocks, transform, float(score), turn, view, complete)


def map_cv2_fields(blocks: list[OcrBlock], *, min_confidence: float = 0.5) -> tuple[dict[str, str], list[str]]:
    """Associate tolerant keys and select only visible dates matching a printed GS1 hint."""
    import re

    from src.cv.photo_fields import map_photo_fields, visible_date

    cleaned = []
    hints = []
    for block in blocks:
        text = block.text.strip()
        text = re.sub(r'^\s*[\[(]?L[O0][T7][\])]?(?=\s|:|$)', 'LOT', text, flags=re.I)
        text = re.sub(r'^\s*E\s*X\s*P(?=\s|:|$)', 'EXP', text, flags=re.I)
        text = re.sub(r'^(LOT|EXP|REF)\s+(?:Number|No\.?|Date)\s*:?\s*$', r'\1', text, flags=re.I)
        # Repair numeric date positions only; never replace O/I in arbitrary batch identifiers.
        if re.search(r'[12][0-9OI]{3}[-/.][0-9OI]{1,2}', text):
            text = re.sub(r'[12][0-9OI]{3}[-/.][0-9OI]{1,2}(?:[-/.][0-9OI]{1,2})?',
                          lambda m: m[0].translate(str.maketrans({'O': '0', 'I': '1'})), text)
        cleaned.append(block.model_copy(update={'text': text}))
        hints += re.findall(r'[（(]17[）)]\s*(\d{6})', text)
    fields, warnings = map_photo_fields(cleaned, min_confidence=min_confidence)
    # An identifier beginning with EXP is not automatically a valid date.
    if 'expiry' in fields and visible_date(fields['expiry']) is None:
        fields.pop('expiry')
        dates = {value for b in cleaned if b.conf >= min_confidence
                 if (value := visible_date(b.text)) is not None}
        if len(dates) == 1:
            fields['expiry'] = 'EXP: '+next(iter(dates))
    # A printed HRI is text evidence, not a license to invent a missing printed date.
    if len(set(hints)) == 1:
        target = hints[0]
        matches = []
        for b in cleaned:
            value = visible_date(b.text)
            if value:
                numbers = re.findall(r'\d+', value)
                if len(numbers) >= 2 and len(numbers[0]) == 4:
                    compact = numbers[0][2:]+numbers[1].zfill(2)
                    if len(numbers) == 3:
                        compact += numbers[2].zfill(2)
                    if target.startswith(compact):
                        matches.append(value)
        if len(set(matches)) == 1:
            fields['expiry'] = 'EXP: '+matches[0]
            warnings.append('FIELD_SELECTED_FROM_PRINTED_HRI: matching observed expiry; needs human review')
    # Exact visible keys may sit on a different line, including alphabetic-only lots.
    for field, key in [('lot', 'LOT'), ('expiry', 'EXP')]:
        if field in fields:
            continue
        values = []
        for b in cleaned:
            if b.text.upper().strip('[](): ') != key:
                continue
            x, y, w, h = b.bbox
            for other in cleaned:
                ox, oy, ow, oh = other.bbox
                same_row = abs(oy+oh/2-y-h/2) <= 0.6*max(h, oh) and 0 <= ox-x-w <= 6*h
                below = 0 <= oy-y-h <= 2*h and min(x+w, ox+ow) > max(x, ox)
                valid = (bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9./_-]{1,19}', other.text))
                         and visible_date(other.text) is None
                         if field == 'lot' else visible_date(other.text) is not None)
                if other is not b and other.conf >= min_confidence and (same_row or below) and valid:
                    values.append(other.text)
        if len(set(values)) == 1:
            fields[field] = f'{key}: {values[0]}'
    name = observed_product_name(cleaned, min_confidence=min_confidence)
    if name:
        fields['product_name'] = name
    warnings = [w for w in warnings if not (w.startswith('FIELD_MISSING: ') and w.split(': ', 1)[1] in fields)]
    return fields, warnings


def observed_product_name(blocks: list[OcrBlock], *, min_confidence: float = 0.5) -> str | None:
    """Prefer a visible device category over a logo, joining adjacent title lines only.

    Category words are generic device descriptions, not a product-name catalog.
    Every returned character comes from an observed OCR block.
    """
    import re

    category = re.compile(r"\b(?:catheter|spinal|epidural|lancets?|dressing|sensor|implant)\b", re.I)
    excluded = re.compile(r"\b(?:sterile|warning|caution|contains|instructions|manufactured|use|only|for)\b", re.I)
    usable = [b for b in blocks if b.conf >= min_confidence and not excluded.search(b.text)]
    titles = [b for b in usable if category.search(b.text) and len(b.text) <= 80]
    if not titles:
        return None
    title = max(titles, key=lambda b: b.bbox[3]*b.bbox[2]/max(1, len(b.text)))
    x, y, w, h = title.bbox
    parts = [title]
    for b in usable:
        if b is title or not re.fullmatch(r"[A-Za-z0-9 ®™'-]{3,45}", b.text):
            continue
        ox, oy, ow, oh = b.bbox
        aligned = min(x+w, ox+ow)-max(x, ox) >= 0.5*min(w, ow)
        near_above = 0 <= y-oy-oh <= 0.75*h
        near_below = 0 <= oy-y-h <= 0.75*h
        if aligned and 0.65*h <= oh <= 1.6*h and (near_above or near_below):
            parts.append(b)
    return ' '.join(b.text for b in sorted(parts, key=lambda b: (b.bbox[1], b.bbox[0])))
