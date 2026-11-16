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

from src.cv.preprocess import _validate_image, find_label_corners, find_label_corners_fallback, order_corners


@dataclass(frozen=True)
class PerspectiveResult:
    """Detected source corners, image-to-flat matrix and corrected RGB pixels."""

    image: np.ndarray
    corners: np.ndarray
    homography: np.ndarray
    detector: str


def warp_label(
    image: np.ndarray, corners: np.ndarray, aspect_ratio: float | None = None, *,
    output_width: int | None = None, detector: str = "provided_boundary",
) -> PerspectiveResult:
    """Flatten detected corners, using native edge proportions when no template is known.

    Native proportions are an estimate from the photographed edges, not recovered
    physical dimensions. All coordinates map from the original RGB image.
    """
    _validate_image(image)
    ordered = order_corners(corners)
    height, width = image.shape[:2]
    if (ordered < 0).any() or (ordered[:, 0] > width - 1).any() or (ordered[:, 1] > height - 1).any():
        raise ValueError("Corners must lie inside the image")
    native_width = max(np.linalg.norm(ordered[1] - ordered[0]), np.linalg.norm(ordered[2] - ordered[3])) + 1
    native_height = max(np.linalg.norm(ordered[3] - ordered[0]), np.linalg.norm(ordered[2] - ordered[1])) + 1
    if aspect_ratio is not None and (
        isinstance(aspect_ratio, bool) or not math.isfinite(aspect_ratio) or aspect_ratio <= 0
    ):
        raise ValueError("Template aspect ratio must be finite and positive")
    ratio = native_width / native_height if aspect_ratio is None else aspect_ratio
    out_width = round(native_width) if output_width is None else output_width
    if type(out_width) is not int or not 2 <= out_width <= 10000:
        raise ValueError("Output width must be an integer from 2 to 10000")
    proposed_height = out_width / ratio
    if not math.isfinite(proposed_height) or not 2 <= proposed_height <= 10000:
        raise ValueError("Output dimensions exceed raster limits")
    out_height = round(proposed_height)
    if out_width * out_height > 30_000_000:
        raise ValueError("Output dimensions exceed raster limits")
    destination = np.array([[0, 0], [out_width - 1, 0],
                            [out_width - 1, out_height - 1], [0, out_height - 1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(ordered.astype(np.float32), destination)
    corrected = cv2.warpPerspective(image, matrix, (out_width, out_height), flags=cv2.INTER_LINEAR)
    return PerspectiveResult(corrected, ordered.copy(), matrix, detector)


def correct_perspective(
    image: np.ndarray, aspect_ratio: float | None, *, output_width: int = 1000,
) -> PerspectiveResult | None:
    """Detect and flatten a roughly upright label; None when no boundary is supported.

    A supplied template ratio controls dimensions. None explicitly requests the
    observed edge ratio, without assuming the synthetic template for real photos.
    """
    _validate_image(image)
    # Validate dimensions even when boundary detection would fail.
    if aspect_ratio is not None and (
        isinstance(aspect_ratio, bool) or not math.isfinite(aspect_ratio) or aspect_ratio <= 0
    ):
        raise ValueError("Template aspect ratio must be finite and positive")
    if type(output_width) is not int or not 2 <= output_width <= 10000:
        raise ValueError("Output width must be an integer from 2 to 10000")
    if aspect_ratio is not None and not 2 <= output_width / aspect_ratio <= 10000:
        raise ValueError("Output dimensions exceed raster limits")
    corners = find_label_corners(image)
    detector = "quadrilateral"
    if corners is None:
        corners = find_label_corners_fallback(image)
        detector = "boundary_fallback"
    if corners is None:
        return None
    return warp_label(image, corners, aspect_ratio, output_width=output_width, detector=detector)


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
