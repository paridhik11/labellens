"""Reference bank: silhouettes and keypoint images of the pictograms rendered in chosen styles.

Only styles from the ``train`` and ``dev`` splits can be requested; held-out styles are never read here.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import cv2
import numpy as np

from src.gen.symbol_styles import SYMBOLS, TRAIN_DISTRACTORS, Style, render_mask, styles_in

SIL = 64  # side of the normalised silhouette, in pixels
KP = 128  # side of the image used for keypoints


def fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill every enclosed hole of a 0/1 mask, so an outline and a filled drawing share a silhouette."""
    padded = cv2.copyMakeBorder((mask > 0).astype(np.uint8) * 255, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    flooded = padded.copy()
    cv2.floodFill(flooded, None, (0, 0), 255)
    holes = cv2.bitwise_not(flooded)[1:-1, 1:-1]
    return ((mask > 0) | (holes > 0)).astype(np.uint8)


def silhouette(ink: np.ndarray) -> np.ndarray:
    """Normalise a 0/1 ink crop to a SIL by SIL hole-filled silhouette (stretched to a square)."""
    closed = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    resized = cv2.resize(closed.astype(np.float32), (SIL, SIL), interpolation=cv2.INTER_AREA)
    return fill_holes((resized > 0.35).astype(np.uint8))


def tight_ink(mask: np.ndarray) -> np.ndarray:
    """Crop a 0/1 mask to the bounding box of its ink, as the candidate finder does for photos."""
    ys, xs = np.nonzero(mask)
    return (mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1] > 0).astype(np.uint8)


def ink_to_grey(ink: np.ndarray) -> np.ndarray:
    """Turn an ink crop into a black-on-white picture of the keypoint size (polarity and light are normalised)."""
    closed = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    big = cv2.resize((1 - closed).astype(np.float32) * 255, (KP, KP), interpolation=cv2.INTER_CUBIC)
    return np.clip(cv2.GaussianBlur(big, (3, 3), 0), 0, 255).astype(np.uint8)


@dataclass(frozen=True)
class Bank:
    """Silhouettes (R, SIL, SIL) with their class names, and grey keypoint images, per reference."""

    classes: tuple[str, ...]
    sil: np.ndarray
    grey: tuple[np.ndarray, ...]
    style_ids: tuple[str, ...]


@lru_cache(maxsize=8)
def build_bank(style_ids: tuple[str, ...] | None = None) -> Bank:
    """Render every pictogram and train distractor in the chosen styles (default: all train styles)."""
    styles: tuple[Style, ...] = styles_in("train") if style_ids is None else tuple(
        style for style in styles_in("train") + styles_in("dev") if style.id in style_ids
    )
    classes, sils, greys, ids = [], [], [], []
    for style in styles:
        for name in (*SYMBOLS, *TRAIN_DISTRACTORS):
            ink = tight_ink(np.asarray(render_mask(name, style, 192, 192)) < 128)
            classes.append(name)
            sils.append(silhouette(ink))
            greys.append(ink_to_grey(ink))
            ids.append(style.id)
    return Bank(tuple(classes), np.stack(sils), tuple(greys), tuple(ids))


def iou_to_bank(candidate: np.ndarray, bank: Bank) -> np.ndarray:
    """IoU of one silhouette against every reference silhouette."""
    inter = (bank.sil & candidate).sum(axis=(1, 2))
    union = (bank.sil | candidate).sum(axis=(1, 2))
    return inter / np.maximum(union, 1)
