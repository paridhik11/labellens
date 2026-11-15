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


def padded_crops(image: np.ndarray, boxes: list[np.ndarray], pad_ratio: float) -> list[np.ndarray]:
    """Cut each text quadrilateral out of the image with extra margin on every side.

    The margin is ``pad_ratio`` times the box height. Pixels outside the image
    repeat the nearest edge pixel. Corners are top left, top right, bottom
    right, bottom left, as the detector returns them.
    """
    crops = []
    for box in boxes:
        quad = np.asarray(box, dtype=np.float32)
        width = max(np.linalg.norm(quad[1] - quad[0]), np.linalg.norm(quad[2] - quad[3]))
        height = max(np.linalg.norm(quad[3] - quad[0]), np.linalg.norm(quad[2] - quad[1]))
        pad = pad_ratio * height
        out_w, out_h = max(2, int(round(width + 2 * pad))), max(2, int(round(height + 2 * pad)))
        target = np.array(
            [[pad, pad], [pad + width, pad], [pad + width, pad + height], [pad, pad + height]], dtype=np.float32
        )
        matrix = cv2.getPerspectiveTransform(quad, target)
        crops.append(cv2.warpPerspective(image, matrix, (out_w, out_h), borderMode=cv2.BORDER_REPLICATE))
    return crops


def vote_text(hypotheses: list[tuple[str, float]]) -> tuple[str, float]:
    """Pick one reading from several recognition passes of the same text line.

    Each hypothesis is (text, confidence). The most frequent text wins and ties
    go to the higher mean confidence. The returned confidence is the mean
    confidence of the passes that agree with the winner, multiplied by the
    share of passes that agree, so disagreement lowers it.
    """
    if not hypotheses:
        raise ValueError("At least one hypothesis is required")
    groups: dict[str, list[float]] = {}
    for text, confidence in hypotheses:
        groups.setdefault(text, []).append(float(confidence))
    text, scores = max(groups.items(), key=lambda item: (len(item[1]), float(np.mean(item[1]))))
    return text, float(np.mean(scores)) * len(scores) / len(hypotheses)


def read_text_robust(
    image: np.ndarray,
    *,
    pad_ratios: tuple[float, ...] = (0.5,),
    dither_pad_ratios: tuple[float, ...] = (),
    dither_sigma: float = 4.0,
    target_width: int | None = None,
) -> list[OcrBlock]:
    """Read text with padded line crops and optional extra passes that vote.

    The detector runs once. Every detected line is then recognised once per
    entry of ``pad_ratios`` (crop margin as a share of the line height) and
    once per entry of ``dither_pad_ratios`` on a copy of the image with weak
    fixed-seed Gaussian noise added. Tight crops of very clean text make the
    recogniser drop spaces and confuse 0 with O; margin and weak noise both
    move it away from that tipping point. Recognised text is stripped of
    leading and trailing whitespace and the passes vote with ``vote_text``.
    ``target_width`` resizes the image to that width first; boxes are returned
    in the coordinates of the image that was passed in. The same steps run for
    every image, whatever its condition. Low-confidence lines are kept; the
    caller decides what to filter.
    """
    _validate_image(image)
    if not pad_ratios and not dither_pad_ratios:
        raise ValueError("At least one recognition pass is required")
    scale = 1.0
    working = image
    if target_width is not None and target_width != image.shape[1]:
        scale = target_width / image.shape[1]
        interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
        working = cv2.resize(image, None, fx=scale, fy=scale, interpolation=interpolation)
    bgr = cv2.cvtColor(working, cv2.COLOR_RGB2BGR)
    engine = _get_engine()
    boxes, _ = engine.text_det(bgr)
    if boxes is None or len(boxes) == 0:
        return []
    boxes = [np.asarray(box, dtype=np.float32) for box in engine.sorted_boxes(np.asarray(boxes))]
    passes = [(bgr, ratio) for ratio in pad_ratios]
    if dither_pad_ratios:
        noise = np.random.default_rng(0).normal(0, dither_sigma, bgr.shape)
        dithered = np.clip(bgr.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        passes += [(dithered, ratio) for ratio in dither_pad_ratios]
    readings: list[list[tuple[str, float]]] = [[] for _ in boxes]
    for pixels, ratio in passes:
        recognised, _ = engine.text_rec(padded_crops(pixels, boxes, ratio))
        for index, (text, confidence) in enumerate(recognised):
            readings[index].append((text.strip(), float(np.clip(confidence, 0.0, 1.0))))
    height, width = image.shape[:2]
    blocks = []
    for box, hypotheses in zip(boxes, readings, strict=True):
        text, confidence = vote_text(hypotheses)
        if not text:
            continue
        points = box / scale
        left, top = np.clip(points.min(axis=0), 0, [width, height])
        right, bottom = np.clip(points.max(axis=0), 0, [width, height])
        if right <= left or bottom <= top:
            continue
        blocks.append(OcrBlock(
            text=text,
            bbox=(float(left), float(top), float(right - left), float(bottom - top)),
            conf=confidence,
        ))
    return blocks


# Recognition passes used by the extractor for every image, whatever its condition.
# Chosen on dev seeds 42 and 43, see results/cv_experiments.md.
# One pass on weakly dithered pixels with a 30 percent margin. Voting over three passes and
# upscaling to a fixed width gave no further gain on either dev seed, so they are not used.
DEFAULT_PAD_RATIOS: tuple[float, ...] = ()
DEFAULT_DITHER_PAD_RATIOS: tuple[float, ...] = (0.3,)


def equalise_contrast(image: np.ndarray) -> np.ndarray:
    """Raise local contrast with CLAHE on the lightness channel of an RGB image.

    CLAHE (contrast limited adaptive histogram equalisation) stretches the
    brightness range separately in each of 8 by 8 tiles, with a limit on how
    much any tile may be amplified. Text that glare has washed out to light
    grey on white becomes dark on white again; clean text is left almost
    unchanged.
    """
    _validate_image(image)
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lab[..., 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def read_text_default(image: np.ndarray) -> list[OcrBlock]:
    """Read text the way the extractor does: contrast equalisation, then the padded reader.

    The same two steps run for every image, whatever its condition.
    """
    return read_text_robust(
        equalise_contrast(image), pad_ratios=DEFAULT_PAD_RATIOS, dither_pad_ratios=DEFAULT_DITHER_PAD_RATIOS
    )


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
