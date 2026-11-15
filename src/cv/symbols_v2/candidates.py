"""Find candidate pictogram boxes anywhere on an upright label, using no template positions and no learning.

Steps: flatten uneven light by dividing by a local paper-level estimate, threshold to an ink map, close small
gaps, and keep connected blobs whose size, shape and ink share are plausible for a pictogram. Blobs are
proposed at two closing strengths so a pictogram whose parts do not touch is still found.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Candidate:
    """One proposed box on the working-size image, with its ink pixels."""

    box: tuple[int, int, int, int]  # x, y, w, h on the working image
    ink: np.ndarray  # uint8 0/1 crop of the ink map inside the box


def prepare(image: np.ndarray, work_short_side: int = 600) -> tuple[np.ndarray, float]:
    """Return the grey working image (short side ``work_short_side``) and the scale factor from the original."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if image.ndim == 3 else image
    factor = work_short_side / min(gray.shape[:2])
    interpolation = cv2.INTER_AREA if factor < 1 else cv2.INTER_CUBIC
    return cv2.resize(gray, None, fx=factor, fy=factor, interpolation=interpolation), factor


def ink_map(gray: np.ndarray, *, ratio: float = 0.62) -> np.ndarray:
    """Binary ink map (1 = ink): pixels clearly darker than the local paper level."""
    side = max(31, int(min(gray.shape) * 0.30) // 2 * 2 + 1)
    paper = cv2.blur(cv2.dilate(gray, np.ones((side, side), np.uint8)), (side // 3 | 1, side // 3 | 1))
    paper = np.maximum(paper.astype(np.float32), 40.0)
    return (gray.astype(np.float32) / paper < ratio).astype(np.uint8)


def propose(
    gray: np.ndarray,
    *,
    min_side: float = 0.045,
    max_side: float = 0.30,
    aspect: tuple[float, float] = (0.5, 2.0),
    fill: tuple[float, float] = (0.10, 0.97),
    closings: tuple[int, ...] = (3, 9),
) -> list[Candidate]:
    """Return candidate boxes for pictogram-sized blobs, de-duplicated."""
    short = min(gray.shape)
    ink = ink_map(gray)
    found: list[Candidate] = []
    for size in closings:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
        closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, kernel)
        count, _, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
        for index in range(1, count):
            x, y, w, h, _ = (int(v) for v in stats[index])
            if not (min_side * short <= h <= max_side * short and min_side * short <= w <= max_side * short):
                continue
            if not aspect[0] <= w / h <= aspect[1]:
                continue
            crop = ink[y:y + h, x:x + w]
            share = float(crop.mean())
            if not fill[0] <= share <= fill[1]:
                continue
            box = (x, y, w, h)
            if any(_iou(box, other.box) > 0.7 for other in found):
                continue
            found.append(Candidate(box, crop.copy()))
    return found


def _iou(first: tuple[int, ...], second: tuple[int, ...]) -> float:
    """Intersection over union of two x, y, w, h boxes."""
    x1, y1, w1, h1 = first
    x2, y2, w2, h2 = second
    inter = max(0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
    return inter / (w1 * h1 + w2 * h2 - inter)
