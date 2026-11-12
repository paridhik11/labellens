"""Read image text with the pinned RapidOCR ONNX Runtime fallback."""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np
from PIL import Image

from src.common.schemas import OcrBlock
from src.cv.preprocess import _validate_image, find_label_corners, rectify_label

if TYPE_CHECKING:
    from rapidocr_onnxruntime import RapidOCR


@lru_cache(maxsize=1)
def _get_engine() -> RapidOCR:
    """Load bundled models once, using CPU and one inference thread per operator."""
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR(
        text_score=0.0,
        use_det=True,
        use_cls=False,
        use_rec=True,
        det_use_cuda=False,
        cls_use_cuda=False,
        rec_use_cuda=False,
        intra_op_num_threads=1,
        inter_op_num_threads=1,
    )


def ocr_blocks_from_results(
    results: list[list[Any]] | None,
    image_size: tuple[int, int],
) -> list[OcrBlock]:
    """Convert RapidOCR rows to x, y, width, height boxes in input-image pixels.

    Keep recognized text and confidence unchanged, including low confidence.
    Return an empty list for no text and reject malformed engine output.
    Image size is width, height; box boundaries may equal those dimensions.
    """
    width, height = image_size
    if width <= 0 or height <= 0:
        raise ValueError("Image dimensions must be positive")
    blocks = []
    for row in results or []:
        if len(row) != 3:
            raise ValueError("Expected OCR rows containing corners, text and confidence")
        corners, text, confidence = row
        points = np.asarray(corners, dtype=np.float64)
        if points.shape != (4, 2) or not np.isfinite(points).all():
            raise ValueError("OCR corners must contain four finite x, y points")
        try:
            score = float(confidence)
        except (TypeError, ValueError) as error:
            raise ValueError("OCR confidence must be numeric") from error
        if not isinstance(text, str) or not np.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("OCR text must be a string and confidence must be between zero and one")
        left, top = points.min(axis=0)
        right, bottom = points.max(axis=0)
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("OCR box must have positive size and lie inside the image")
        if not text.strip():
            continue
        blocks.append(OcrBlock(
            text=text,
            bbox=(float(left), float(top), float(right - left), float(bottom - top)),
            conf=score,
        ))
    return blocks


def read_text(image: np.ndarray) -> list[OcrBlock]:
    """Read a uint8 RGB image and return text boxes in that same coordinate space.

    The engine expects BGR NumPy input. No ground truth, field substitution or
    confidence filtering is applied by this wrapper. Engine failures propagate.
    """
    _validate_image(image)
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    results, _ = _get_engine()(bgr)
    return ocr_blocks_from_results(results, (image.shape[1], image.shape[0]))


def main(argv: list[str] | None = None) -> int:
    """Print actual OCR blocks for an image, optionally correcting perspective."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--rectify", action="store_true", help="Detect and straighten the label before OCR")
    args = parser.parse_args(argv)
    try:
        with Image.open(args.image) as photo:
            image = np.asarray(photo.convert("RGB"))
        if args.rectify:
            corners = find_label_corners(image)
            if corners is None:
                parser.error("NEEDS_HUMAN_REVIEW: no suitable label boundary")
            image, _ = rectify_label(image, corners)
        blocks = read_text(image)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print("Engine: rapidocr-onnxruntime (CPU, bundled PP-OCRv4 detection/recognition models)")
    coordinate_space = "corrected_image" if args.rectify else "input_image"
    print(f"Coordinates: {coordinate_space}; size={image.shape[1]}x{image.shape[0]}")
    print(f"OCR blocks: {len(blocks)}")
    for block in blocks:
        print(json.dumps(block.model_dump()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
