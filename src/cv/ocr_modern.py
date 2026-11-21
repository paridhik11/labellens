"""Optional local PP-OCRv6 name evidence, with no model downloads during uploads."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.common.schemas import OcrBlock

MODEL_NAMES = {'Det': 'PP-OCRv6_det_small.onnx', 'Rec': 'PP-OCRv6_rec_small.onnx',
               'Cls': 'ch_ppocr_mobile_v2.0_cls_mobile.onnx'}


def modern_rows(result: Any, width: int, height: int) -> list[OcrBlock]:
    """Convert literal modern-engine output to clipped input-pixel boxes, preserving scores."""
    if result.boxes is None or result.txts is None:
        return []
    rows = []
    for quad, text, score in zip(result.boxes, result.txts, result.scores, strict=True):
        x = max(0.0, min(float(p[0]) for p in quad))
        y = max(0.0, min(float(p[1]) for p in quad))
        right = min(float(width), max(float(p[0]) for p in quad))
        bottom = min(float(height), max(float(p[1]) for p in quad))
        if x < right and y < bottom and text.strip():
            rows.append(OcrBlock(text=text, bbox=(x, y, right-x, bottom-y), conf=float(score)))
    return rows


@lru_cache(maxsize=1)
def modern_engine(model_dir: str) -> Any:
    """Load only explicitly installed local models; missing packages/assets raise for fallback."""
    from rapidocr import RapidOCR

    directory = Path(model_dir)
    if not all((directory/name).is_file() for name in MODEL_NAMES.values()):
        raise FileNotFoundError('CV4 model assets absent')
    params: dict[str, Any] = {'EngineConfig.onnxruntime.intra_op_num_threads': 1,
                              'EngineConfig.onnxruntime.inter_op_num_threads': 1}
    params.update({f'{task}.model_path': str(directory/name) for task, name in MODEL_NAMES.items()})
    return RapidOCR(params=params)


def modern_lines(path: Path, fallback: list[OcrBlock], *, model_dir: str | None = None) -> tuple[list[OcrBlock], str]:
    """Read independent name evidence, retaining old OCR when optional models fail or are absent."""
    directory = model_dir or os.environ.get('LABELLENS_CV4_MODELS')
    if not directory:
        return fallback, 'cv2_fallback:models_not_configured'
    try:
        from PIL import Image

        with Image.open(path) as original:
            image = original.convert('RGB')
            result = modern_engine(directory)(image)
            rows = modern_rows(result, image.width, image.height)
        if not rows:
            return fallback, 'cv2_fallback:no_modern_text'
        return rows, 'ppocrv6_small'
    except Exception as error:
        return fallback, f'cv2_fallback:{type(error).__name__}'
