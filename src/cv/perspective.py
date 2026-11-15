"""Standalone label flattening at a supplied template aspect ratio.

This module does not alter or call the existing extractor. Boundary detection
uses pixels only. It cannot establish text orientation or recover hidden text.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from src.cv.preprocess import _validate_image, find_label_corners, find_label_corners_fallback


@dataclass(frozen=True)
class PerspectiveResult:
    """Detected source corners, image-to-flat matrix and corrected RGB pixels."""

    image: np.ndarray
    corners: np.ndarray
    homography: np.ndarray
    detector: str


def correct_perspective(
    image: np.ndarray, aspect_ratio: float, *, output_width: int = 1000,
) -> PerspectiveResult | None:
    """Find a dominant interior label and warp it to width/height template ratio.

    Returns None when no boundary is supported. Labels must be roughly upright
    (under 45 degrees rotation); no OCR-based orientation is inferred. Raster
    height is rounded to the nearest pixel. Input pixels are never changed.
    """
    _validate_image(image)
    if isinstance(aspect_ratio, bool) or not math.isfinite(aspect_ratio) or aspect_ratio <= 0:
        raise ValueError("Template aspect ratio must be finite and positive")
    if type(output_width) is not int or not 2 <= output_width <= 10000:
        raise ValueError("Output width must be an integer from 2 to 10000")
    output_height = round(output_width / aspect_ratio)
    if not 2 <= output_height <= 10000 or output_width * output_height > 30_000_000:
        raise ValueError("Output dimensions exceed raster limits")
    corners = find_label_corners(image)
    detector = "quadrilateral"
    if corners is None:
        corners = find_label_corners_fallback(image)
        detector = "boundary_fallback"
    if corners is None:
        return None
    destination = np.array([[0, 0], [output_width - 1, 0],
                            [output_width - 1, output_height - 1], [0, output_height - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), destination)
    corrected = cv2.warpPerspective(image, matrix, (output_width, output_height), flags=cv2.INTER_LINEAR)
    return PerspectiveResult(corrected, corners.copy(), matrix, detector)


def evaluate_dataset(dataset: Path, aspect_ratio: float) -> dict[str, dict[str, int | float | None]]:
    """Score every corner within 10 source pixels, per condition, after detection.

    Ground truth is only accessed to score the result. A returned quadrilateral
    is not by itself counted as success. Missing detections count as failures.
    """
    manifest = json.loads((dataset / "manifest.json").read_text())
    results = {}
    for condition in ("clean", "moderate", "hard"):
        errors, detected, successes, count = [], 0, 0, 0
        for entry in manifest["files"]:
            truth = json.loads((dataset / entry["ground_truth"]).read_text())
            if truth["condition"] != condition:
                continue
            count += 1
            with Image.open(dataset / entry["image"]) as photo:
                result = correct_perspective(np.asarray(photo.convert("RGB")), aspect_ratio)
            if result is None:
                continue
            detected += 1
            distances = np.linalg.norm(result.corners - np.asarray(truth["label_quad_px"]), axis=1)
            errors.extend(distances.tolist())
            successes += int(float(distances.max()) <= 10)
        results[condition] = {"images": count, "detected": detected, "within_10px": successes,
                              "success_rate": successes / count if count else None,
                              "mean_corner_error_px": float(np.mean(errors)) if errors else None}
    return results


def main(argv: list[str] | None = None) -> int:
    """Evaluate standalone perspective detection on an existing synthetic dataset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--aspect-ratio", type=float, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(evaluate_dataset(args.dataset, args.aspect_ratio), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
