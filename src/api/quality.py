"""Photo-quality gate that runs before extraction (Step 24a).

A photo that is too blurry, too flat or washed out by glare makes OCR and barcode reading unreliable, and an
unreliable reading becomes a confident false alarm in the checker. The gate turns such a photo into a
`retake_photo` outcome instead of letting it reach extraction. It does not change any checker threshold.

Three measurements, all on a grayscale copy shrunk to 800 px on its long side (so the numbers do not depend on the
phone's resolution):

- sharpness: variance of the Laplacian (an edge detector). Low variance means few sharp edges, so blur.
- contrast: the 95th minus the 5th percentile of the gray levels. Low means a flat or washed out picture.
- glare: a saturated blob (pixels >= 250 after removing thin white lines, at least 2% of the picture) with a
  SOFT edge. A white label surface is also saturated, but it ends at a hard edge; a glare spot fades out, so the
  mean gradient along its border is low. A spot that touches the white label merges with it and is not seen (a
  known limit). A page that is mostly white (a flat digital render) is not glare.

The cut-offs in `Thresholds` were chosen on development seeds 200 and 201 only (see reports/step24_a.md).
OpenCV is imported inside `assess_photo`, never at import time, so CI works without it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.api.extractor import ExtractorUnavailable


@dataclass(frozen=True)
class Thresholds:
    """Cut-offs of the gate. A photo is rejected when any one is crossed."""

    min_sharpness: float = 200.0  # Laplacian variance at 800 px; reject below
    min_contrast: float = 40.0  # p95 - p5 of gray levels (0 to 255); reject below
    glare_min_blob: float = 0.02  # reject only if the soft blob covers at least this share of the picture ...
    glare_max_edge: float = 60.0  # ... and its border gradient is below this (hard paper edges score 95 to 125)
    flat_page: float = 0.6  # more than this share saturated: a flat white page, not glare
    work_size: int = 800


DEFAULT = Thresholds()

MESSAGES = {
    "blur": "The photo is too blurry to read. Hold the camera steady and focus on the label.",
    "low_contrast": "The photo is too flat or too dark to read. Use even light and avoid shadows.",
    "glare": "Glare covers part of the label. Tilt the label or the light to remove the reflection.",
}


@dataclass(frozen=True)
class QualityReport:
    """Outcome of the gate: `ok`, the reasons it failed (codes of MESSAGES) and the measured numbers."""

    ok: bool
    reasons: tuple[str, ...]
    metrics: dict[str, float]

    def error_body(self, thresholds: Thresholds = DEFAULT) -> dict[str, Any]:
        """The contract Error for a rejected photo: code `retake_photo`, reasons and numbers in `details`."""
        return {
            "error": "retake_photo",
            "message": " ".join(MESSAGES[r] for r in self.reasons) or "Retake the photo.",
            "details": {"reasons": list(self.reasons), "metrics": self.metrics, "thresholds": asdict(thresholds)},
        }


def measure(gray: Any, thresholds: Thresholds = DEFAULT) -> dict[str, float]:
    """The four numbers of the gate for one grayscale uint8 image: sharpness, contrast, glare_blob, glare_edge."""
    import cv2
    import numpy as np

    height, width = gray.shape[:2]
    scale = thresholds.work_size / max(height, width)
    if scale < 1:
        size = (max(1, round(width * scale)), max(1, round(height * scale)))
        gray = cv2.resize(gray, size, interpolation=cv2.INTER_AREA)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    low, high = np.percentile(gray, [5, 95])
    saturated = (gray >= 250).astype(np.uint8)
    blob, edge = 0.0, 255.0  # no soft blob found: a large edge value means "not glare"
    if saturated.mean() <= thresholds.flat_page:
        opened = cv2.morphologyEx(saturated, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        count, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
        soft = cv2.GaussianBlur(gray, (5, 5), 0).astype(np.float32)
        gradient = np.hypot(cv2.Sobel(soft, cv2.CV_32F, 1, 0), cv2.Sobel(soft, cv2.CV_32F, 0, 1))
        for index in range(1, count):  # every blob big enough to matter; the softest-edged one decides
            share = stats[index, cv2.CC_STAT_AREA] / gray.size
            if share < thresholds.glare_min_blob:
                continue
            mask = (labels == index).astype(np.uint8)
            ring = cv2.dilate(mask, np.ones((9, 9), np.uint8)) - cv2.erode(mask, np.ones((9, 9), np.uint8))
            border = float(gradient[ring > 0].mean())
            if border < edge:
                blob, edge = float(share), border
    return {"sharpness": round(sharpness, 1), "contrast": round(float(high - low), 1),
            "glare_blob": round(blob, 4), "glare_edge": round(edge, 1)}


def judge(metrics: dict[str, float], thresholds: Thresholds = DEFAULT) -> QualityReport:
    """Apply the cut-offs to measured numbers (pure function, no OpenCV)."""
    reasons: list[str] = []
    if metrics["sharpness"] < thresholds.min_sharpness:
        reasons.append("blur")
    if metrics["contrast"] < thresholds.min_contrast:
        reasons.append("low_contrast")
    if metrics["glare_blob"] >= thresholds.glare_min_blob and metrics["glare_edge"] < thresholds.glare_max_edge:
        reasons.append("glare")
    return QualityReport(ok=not reasons, reasons=tuple(reasons), metrics=metrics)


def assess_photo(path: Path, thresholds: Thresholds = DEFAULT) -> QualityReport:
    """Read an image file and judge it. Raises ExtractorUnavailable when OpenCV is missing, ApiError never."""
    try:
        import cv2
    except ImportError as error:
        raise ExtractorUnavailable(f"CV libraries are not installed: {error}") from error
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError("the image could not be decoded")
    return judge(measure(gray, thresholds), thresholds)
