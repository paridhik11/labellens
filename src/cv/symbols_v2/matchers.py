"""Scorers for one candidate crop: hole-filled silhouette overlap, and SIFT or ORB keypoint matching."""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np

from src.cv.symbols_v2.refs import Bank, ink_to_grey, iou_to_bank

SYMBOL_NAMES = ("manufacturer", "expiry")
_FEATURE_CACHE: dict[tuple[int, str], tuple] = {}


def class_scores(sil: np.ndarray, bank: Bank) -> dict[str, float]:
    """Best silhouette IoU per class (the two pictograms and the train distractors)."""
    ious = iou_to_bank(sil, bank)
    out: dict[str, float] = {}
    for name, value in zip(bank.classes, ious, strict=True):
        out[name] = max(out.get(name, 0.0), float(value))
    return out


@lru_cache(maxsize=4)
def _extractor(kind: str):
    """Create a feature extractor ('sift' or 'orb')."""
    if kind == "sift":
        return cv2.SIFT_create(nfeatures=150, contrastThreshold=0.01)
    return cv2.ORB_create(nfeatures=150, fastThreshold=5, edgeThreshold=8, patchSize=15)


def _describe(grey: np.ndarray, kind: str):
    """Keypoints and descriptors of a picture."""
    return _extractor(kind).detectAndCompute(grey, None)


def _reference_features(grey: np.ndarray, kind: str):
    """Cache the keypoints of a reference picture (keyed by array identity, stable while the bank lives)."""
    key = (id(grey), kind)
    if key not in _FEATURE_CACHE:
        _FEATURE_CACHE[key] = _describe(grey, kind)
    return _FEATURE_CACHE[key]


def keypoint_scores(ink: np.ndarray, bank: Bank, kind: str = "sift", ratio: float = 0.8) -> dict[str, float]:
    """RANSAC-verified keypoint matches against every reference, as the best inlier count per class.

    A similarity transform (rotation, scale, shift) is fitted to the ratio-test matches; its inliers are counted.
    """
    kps, desc = _describe(ink_to_grey(ink), kind)
    out = {name: 0.0 for name in set(bank.classes)}
    if desc is None or len(kps) < 4:
        return out
    matcher = cv2.BFMatcher(cv2.NORM_L2 if kind == "sift" else cv2.NORM_HAMMING)
    for name, grey in zip(bank.classes, bank.grey, strict=True):
        rk, rd = _reference_features(grey, kind)
        if rd is None or len(rk) < 4:
            continue
        pairs = matcher.knnMatch(desc, rd, k=2)
        good = [pair[0] for pair in pairs if len(pair) == 2 and pair[0].distance < ratio * pair[1].distance]
        if len(good) < 4:
            continue
        src = np.float32([kps[m.queryIdx].pt for m in good])
        dst = np.float32([rk[m.trainIdx].pt for m in good])
        matrix, inliers = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6.0)
        if matrix is not None:
            out[name] = max(out[name], float(inliers.sum()))
    return out
