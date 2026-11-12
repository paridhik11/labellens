"""Find and rectify a dominant label with a visible quadrilateral boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def _validate_image(image: np.ndarray) -> None:
    """Require a nonempty uint8 RGB image with at least two pixels per side."""
    if (
        not isinstance(image, np.ndarray)
        or image.dtype != np.uint8
        or image.ndim != 3
        or image.shape[2] != 3
        or min(image.shape[:2]) < 2
    ):
        raise ValueError("Expected a uint8 RGB image with at least two pixels per side")


def order_corners(corners: np.ndarray) -> np.ndarray:
    """Order four convex corners clockwise, starting with minimum x plus y.

    The result represents top left, top right, bottom right, bottom left for
    upright labels. This geometric rule does not infer text orientation.
    """
    points = np.asarray(corners, dtype=np.float32)
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise ValueError("Expected four finite x, y corners")
    hull = cv2.convexHull(points).reshape(-1, 2)
    if len(hull) != 4 or cv2.contourArea(hull) < 1:
        raise ValueError("Corners must form a nondegenerate convex quadrilateral")
    centre = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - centre[1], points[:, 0] - centre[0])
    ordered = points[np.argsort(angles)]
    return np.roll(ordered, -int(np.argmin(ordered.sum(axis=1))), axis=0)


def find_label_corners(image: np.ndarray) -> np.ndarray | None:
    """Find the largest interior convex quadrilateral covering 15% of the image.

    Only pixels are used. Thresholded bright regions and closed edge contours
    supply candidates. Frame-touching candidates are rejected; absent boundary
    evidence returns None rather than assuming that the whole image is a label.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bright = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges = cv2.Canny(blurred, 40, 120)
    kernel = np.ones((3, 3), dtype=np.uint8)
    candidates = []
    for mask in (bright, cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)):
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < width * height * 0.15:
                continue
            polygon = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                continue
            points = polygon.reshape(4, 2)
            if (
                (points[:, 0] <= 0).any() or (points[:, 0] >= width - 1).any()
                or (points[:, 1] <= 0).any() or (points[:, 1] >= height - 1).any()
            ):
                continue
            candidates.append((area, points))
    if not candidates:
        return None
    return order_corners(max(candidates, key=lambda candidate: candidate[0])[1])


def rectify_label(image: np.ndarray, corners: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Warp a supplied label quadrilateral into an RGB rectangle.

    Return the corrected image and image-to-corrected homography. Output width
    and height use the longer of each pair of opposite edges, plus one pixel.
    No template dimensions or ground-truth coordinates are used.
    """
    _validate_image(image)
    ordered = order_corners(corners)
    height, width = image.shape[:2]
    if (
        (ordered[:, 0] < 0).any() or (ordered[:, 0] > width - 1).any()
        or (ordered[:, 1] < 0).any() or (ordered[:, 1] > height - 1).any()
    ):
        raise ValueError("Corners must lie inside the image")
    top_left, top_right, bottom_right, bottom_left = ordered
    output_width = round(max(np.linalg.norm(top_right - top_left), np.linalg.norm(bottom_right - bottom_left))) + 1
    output_height = round(max(np.linalg.norm(bottom_left - top_left), np.linalg.norm(bottom_right - top_right))) + 1
    if output_width < 2 or output_height < 2:
        raise ValueError("Corrected label must have at least two pixels per side")
    destination = np.array(
        [[0, 0], [output_width - 1, 0], [output_width - 1, output_height - 1], [0, output_height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(ordered, destination)
    corrected = cv2.warpPerspective(image, matrix, (output_width, output_height), flags=cv2.INTER_LINEAR)
    return corrected, matrix


def evaluate_dataset(dataset_dir: Path) -> dict[str, dict[str, int | float | None]]:
    """Measure detection and corner errors per condition against generated truth.

    Ground truth is read only for evaluation, after image-only detection.
    A correction counts as accurate when every corner is within 10 source-image
    pixels of its true position. Error averages include detected images only.
    """
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    results: dict[str, dict[str, int | float | None]] = {}
    for condition in ("clean", "moderate", "hard"):
        errors = []
        count = 0
        accurate = 0
        for entry in manifest["files"]:
            truth = json.loads((dataset_dir / entry["ground_truth"]).read_text(encoding="utf-8"))
            if truth["condition"] != condition:
                continue
            count += 1
            with Image.open(dataset_dir / entry["image"]) as photo:
                image = np.asarray(photo.convert("RGB"))
            corners = find_label_corners(image)
            if corners is None:
                continue
            rectify_label(image, corners)
            distances = np.linalg.norm(corners - np.asarray(truth["label_quad_px"]), axis=1)
            errors.append(distances)
            accurate += int(distances.max() <= 10)
        results[condition] = {
            "images": count,
            "detected": len(errors),
            "within_10px": accurate,
            "mean_corner_error_px": float(np.mean(errors)) if errors else None,
            "max_corner_error_px": float(np.max(errors)) if errors else None,
        }
    return results


def main(argv: list[str] | None = None) -> int:
    """Print reproducible per-condition detection measurements for a dataset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    args = parser.parse_args(argv)
    results = evaluate_dataset(args.dataset)
    print("Criterion: every detected corner within 10 pixels of ground truth; no OCR run")
    for condition, result in results.items():
        mean = result["mean_corner_error_px"]
        maximum = result["max_corner_error_px"]
        error_text = "mean_corner_error_px=N/A, max_corner_error_px=N/A"
        if mean is not None and maximum is not None:
            error_text = f"mean_corner_error_px={mean:.3f}, max_corner_error_px={maximum:.3f}"
        print(
            f"{condition}: detected={result['detected']}/{result['images']}, "
            f"within_10px={result['within_10px']}/{result['images']}, {error_text}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
