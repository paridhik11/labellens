"""Opt-in CV3 experiments; barcode prefill never replaces observed printed fields."""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from src.common.schemas import BarcodeResult


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
