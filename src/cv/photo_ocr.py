"""Fixed, reference-free photo OCR with orientation search and overlapping crops."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from src.common.schemas import OcrBlock
from src.cv.budget import Deadline, expired
from src.cv.ocr import read_text
from src.cv.preprocess import _validate_image


@dataclass(frozen=True)
class PhotoReading:
    """Upright observations and their mapping back to original-photo coordinates."""

    blocks: list[OcrBlock]
    to_original: np.ndarray
    score: float
    quarter_turns: int
    view: str
    complete: bool = True  # False when a time budget cut the orientation search or the crop passes short


def project_blocks(blocks: list[OcrBlock], matrix: np.ndarray, size: tuple[int, int]) -> list[OcrBlock]:
    """Enclose transformed OCR boxes in the destination image, preserving text/confidence."""
    result = []
    for block in blocks:
        x, y, w, h = block.bbox
        quad = np.array([[[x, y], [x + w, y], [x + w, y + h], [x, y + h]]], dtype=np.float32)
        points = cv2.perspectiveTransform(quad, matrix.astype(float))[0]
        left, top = np.clip(points.min(axis=0), 0, size)
        right, bottom = np.clip(points.max(axis=0), 0, size)
        if right > left and bottom > top:
            result.append(block.model_copy(update={"bbox": (float(left), float(top),
                                                           float(right - left), float(bottom - top))}))
    return result


def merge_blocks(blocks: list[OcrBlock]) -> list[OcrBlock]:
    """Suppress overlapping duplicate line observations without concatenating guessed words."""
    kept = []
    for block in sorted(blocks, key=lambda b: (-b.conf, -len(b.text), b.bbox[1], b.bbox[0])):
        x, y, w, h = block.bbox
        duplicate = False
        for old in kept:
            ox, oy, ow, oh = old.bbox
            intersection = max(0, min(x + w, ox + ow) - max(x, ox)) * max(0, min(y + h, oy + oh) - max(y, oy))
            if intersection / max(1, min(w * h, ow * oh)) >= 0.65:
                duplicate = True
                break
        if not duplicate:
            kept.append(block)
    return sorted(kept, key=lambda b: (b.bbox[1], b.bbox[0]))


def read_photo(
    image: np.ndarray, *, reader: Callable[[np.ndarray], list[OcrBlock]] = read_text,
    view: str = "original", to_original: np.ndarray | None = None, deadline: Deadline | None = None,
    crops: bool = True,
) -> PhotoReading:
    """Choose orientation by confident text coverage, then read four overlapping crops.

    The same four quarter-turns and four 60%-sized crops run for every photo.
    Scores use recognized pixels/text only, never product names or reference
    values. Crops are enlarged when small, bounded to a 1600-pixel long side.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    rotations = [np.eye(3), np.array([[0, 1, 0], [-1, 0, width - 1], [0, 0, 1]]),
                 np.array([[-1, 0, width - 1], [0, -1, height - 1], [0, 0, 1]]),
                 np.array([[0, -1, height - 1], [1, 0, 0], [0, 0, 1]])]
    candidates = []
    complete = True
    for turn in range(4):
        if turn and expired(deadline):  # the upright turn is always read; later turns are optional
            complete = False
            break
        rotated = np.ascontiguousarray(np.rot90(image, turn))
        blocks = reader(rotated)
        score = sum(b.conf ** 2 * sum(c.isalnum() for c in b.text) for b in blocks if b.conf >= 0.6)
        candidates.append((score, -turn, blocks))
    best = max(candidates, key=lambda item: item[:2])
    # Avoid rotating an already readable view for a negligible confidence change.
    score, negative_turn, blocks = candidates[0] if candidates[0][0] >= 0.9 * best[0] else best
    turn = -negative_turn
    upright = np.ascontiguousarray(np.rot90(image, turn))
    uh, uw = upright.shape[:2]
    all_blocks = list(blocks)
    ch, cw = max(2, round(uh * 0.6)), max(2, round(uw * 0.6))
    for top, left in (((0, 0), (0, uw - cw), (uh - ch, 0), (uh - ch, uw - cw)) if crops else ()):
        if expired(deadline):
            complete = False
            break
        crop = upright[top:top + ch, left:left + cw]
        scale = min(2.0, 1600 / max(crop.shape[:2]))
        scaled = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        transform = np.array([[1 / scale, 0, left], [0, 1 / scale, top], [0, 0, 1]])
        all_blocks.extend(project_blocks(reader(scaled), transform, (uw, uh)))
    merged = merge_blocks(all_blocks)
    transform = np.linalg.inv(rotations[turn])
    if to_original is not None:
        transform = to_original @ transform
    return PhotoReading(merged, transform, float(score), turn, view, complete)


def choose_turn(
    image: np.ndarray, *, to_original: np.ndarray | None = None, deadline: Deadline | None = None,
    search_side: int | None = None, reader: Callable[[np.ndarray], list[OcrBlock]] = read_text,
) -> tuple[int, np.ndarray, bool]:
    """Pick the upright quarter turn exactly as ``read_photo`` does, optionally on a smaller copy.

    Each of the four turns is read and scored by confident text coverage, and the upright turn is kept unless
    another turn is more than 10 percent better. With ``search_side`` the scoring copy is shrunk to that long
    side, which makes the four reads much cheaper; the chosen turn is then applied to the full-size image by the
    caller. Returns the turn, the matrix from the upright image back to the original photo, and False when a
    deadline cut the search short.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    rotations = [np.eye(3), np.array([[0, 1, 0], [-1, 0, width - 1], [0, 0, 1]]),
                 np.array([[-1, 0, width - 1], [0, -1, height - 1], [0, 0, 1]]),
                 np.array([[0, -1, height - 1], [1, 0, 0], [0, 0, 1]])]
    small = image
    if search_side and max(height, width) > search_side:
        factor = search_side / max(height, width)
        small = cv2.resize(image, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA)
    complete, candidates = True, []
    for turn in range(4):
        if turn and expired(deadline):
            complete = False
            break
        blocks = reader(np.ascontiguousarray(np.rot90(small, turn)))
        score = sum(b.conf ** 2 * sum(c.isalnum() for c in b.text) for b in blocks if b.conf >= 0.6)
        candidates.append((score, -turn))
    best = max(candidates)
    chosen = -(candidates[0] if candidates[0][0] >= 0.9 * best[0] else best)[1]
    transform = np.linalg.inv(rotations[chosen])
    return chosen, (transform if to_original is None else to_original @ transform), complete
