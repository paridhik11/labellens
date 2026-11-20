"""Verify bound template slots using pixel evidence, never expected-value OCR hints."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any


def normalized(value: str) -> str:
    """Normalize Unicode and whitespace only; preserve identifier characters and case."""
    return ' '.join(unicodedata.normalize('NFKC', value).split())


def decide(fields: list[dict[str, Any]], decoded: list[dict[str, Any]], ais: dict[str, str]) -> str:
    """A confident difference wins; match requires every field and one exact GS1 decode."""
    if any(f['status'] == 'MISMATCH' for f in fields):
        return 'MISMATCH'
    if any(b.get('parsed') and b['parsed'] != ais for b in decoded):
        return 'MISMATCH'
    if (not fields or any(f['status'] != 'MATCH' for f in fields)
            or len(decoded) != 1 or decoded[0].get('parsed') != ais):
        return 'NEEDS_HUMAN_REVIEW'
    return 'MATCH'


def verify_template(photo: Path, expected: dict[str, Any]) -> dict[str, Any]:
    """Rectify a label, mask the draft band, then read independently bound field crops."""
    import cv2
    import numpy as np
    import zxingcpp
    from PIL import Image

    from src.cv.barcode import _format_results
    from src.cv.extract import project_box
    from src.cv.ocr import _get_engine
    from src.cv.perspective import correct_perspective, warp_label

    empty = {'status': 'NEEDS_HUMAN_REVIEW', 'fields': [], 'issues': [], 'barcode': None}
    template = expected.get('template')
    if not template:
        return {**empty, 'warnings': ['TEMPLATE_BINDING_MISSING']}
    width, height = template['size_mm']['w'], template['size_mm']['h']
    with Image.open(photo) as source:
        pixels = np.asarray(source.convert('RGB'))
    correction = correct_perspective(pixels, width/height, output_width=1600)
    # Flat rendered/scanned pages have no outer contour against a white background.
    # Only accept the full frame when its aspect and white perimeter agree.
    ph, pw = pixels.shape[:2]
    perimeter = np.concatenate((pixels[0], pixels[-1], pixels[:, 0], pixels[:, -1]))
    if (correction is None and abs(pw/ph-width/height) < 0.01
            and float(np.mean(np.all(perimeter > 245, axis=1))) > 0.98):
        corners = np.array([[0, 0], [pw-1, 0], [pw-1, ph-1], [0, ph-1]], dtype=np.float32)
        correction = warp_label(pixels, corners, width/height, output_width=1600)
    if correction is None:
        return {**empty, 'warnings': ['LABEL_BOUNDARY_MISSING']}
    image = correction.image.copy()
    ih, iw = image.shape[:2]
    image[:int(np.ceil(9*ih/height))] = 255
    inverse = np.linalg.inv(correction.homography)
    fields, warnings, decoded = [], [], []
    for field, value in expected['fields'].items():
        slots = [s for s in template['slots'] if s['type'] == 'text' and s.get('field') == field]
        evidence = {'field': field, 'expected': value, 'observed': None, 'confidence': None,
                    'status': 'NEEDS_HUMAN_REVIEW', 'bbox': None}
        if len(slots) != 1 or slots[0].get('max_lines', 1) != 1:
            fields.append(evidence)
            continue
        x, y, w, h = slots[0]['bbox_mm']
        if y < 9 or min(w, h) <= 0 or x < 0 or x+w > width or y+h > height:
            fields.append(evidence)
            continue
        left, top = int(x*iw/width), int(y*ih/height)
        right, bottom = int(np.ceil((x+w)*iw/width)), int(np.ceil((y+h)*ih/height))
        region = image[top:bottom, left:right]
        ink = np.any(region < 180, axis=2)
        ys, xs = np.where(ink)
        if len(xs) == 0:
            fields.append(evidence)
            continue
        region = region[max(0, ys.min()-4):min(len(region), ys.max()+5),
                        max(0, xs.min()-4):min(region.shape[1], xs.max()+5)]
        crop = cv2.copyMakeBorder(region, 5, 5, 5, 5,
                                  cv2.BORDER_CONSTANT, value=(255, 255, 255))
        readings, _ = _get_engine()(cv2.cvtColor(crop, cv2.COLOR_RGB2BGR),
                                   use_det=False, use_cls=False, use_rec=True)
        if readings and len(readings) == 1:
            observed, confidence = readings[0]
            prefix = slots[0].get('prefix', '')
            if prefix and observed.startswith(prefix):
                observed = observed[len(prefix):]
            evidence.update(observed=observed, confidence=float(confidence),
                            bbox=project_box((left, top, right-left, bottom-top), inverse,
                                             (pixels.shape[1], pixels.shape[0])))
            if confidence >= 0.8 and normalized(observed):
                evidence['status'] = 'MATCH' if normalized(observed) == normalized(value) else 'MISMATCH'
        fields.append(evidence)
    # DataMatrix-only bounded-area search avoids whole-photo QR false finder stalls.
    for slot in template['slots']:
        if slot['type'] != 'barcode':
            continue
        x, y, w, h = slot['bbox_mm']
        left, top = max(0, int(x*iw/width)-20), max(0, int(y*ih/height)-20)
        right, bottom = min(iw, int((x+w)*iw/width)+20), min(ih, int((y+h)*ih/height)+20)
        found = zxingcpp.read_barcodes(cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_RGB2GRAY),
                                       formats=zxingcpp.BarcodeFormat.DataMatrix)
        results, notes = _format_results(found, (iw, ih), (left, top))
        decoded.extend(b.model_dump() for b in results)
        warnings.extend(notes)
    status = decide(fields, decoded, expected['barcode_ais'])
    issues = [{'kind': 'BARCODE_DIFFERENCE', 'expected': expected['barcode_ais'], 'observed': b['parsed']}
              for b in decoded if b.get('parsed') and b['parsed'] != expected['barcode_ais']]
    if not decoded:
        warnings.append('BARCODE_NOT_DECODED')
    if re.search(r'DRAFT|TEST DATA', ' '.join(f['observed'] or '' for f in fields)):
        return {**empty, 'fields': fields, 'warnings': ['DRAFT_CONTAMINATION']}
    return {'status': status, 'fields': fields, 'issues': issues, 'warnings': warnings,
            'barcode': decoded[0] if len(decoded) == 1 else None}
