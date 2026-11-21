"""Professional registered-name evidence; public extraction never calls this helper."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.common.schemas import LabelExtraction
from src.cv.known_product import check_name

RELEASE_PATH = Path(__file__).resolve().parents[1]/'cv/cv4_release.json'


def check_registered_name(
    extraction: LabelExtraction, name: str, *, image: Path | None = None,
) -> tuple[LabelExtraction, dict[str, Any]]:
    """Use observed name text only and keep all other extraction fields/observations intact."""
    blocks, engine = extraction.ocr_blocks, 'cv2'
    selected = json.loads(RELEASE_PATH.read_text()).get('engine', 'cv2') if RELEASE_PATH.exists() else 'cv2'
    if image is not None and selected == 'ppocrv6':
        from src.cv.ocr_modern import modern_lines

        blocks, engine = modern_lines(image, blocks)
    result = {**check_name(name, blocks), 'engine': engine}
    fields = {key: value for key, value in extraction.fields.items() if key != 'product_name'}
    if result['status'] == 'found':
        fields['product_name'] = result['matched_line']
    return extraction.model_copy(update={'fields': fields}), result
