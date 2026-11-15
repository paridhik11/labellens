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


def _line_intersection(
    first: tuple[np.ndarray, np.ndarray], second: tuple[np.ndarray, np.ndarray]
) -> np.ndarray | None:
    """Intersect two infinite lines, each given by two points; None when parallel."""
    (p1, p2), (p3, p4) = first, second
    d1, d2 = p2 - p1, p4 - p3
    denominator = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(denominator) < 1e-9:
        return None
    t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / denominator
    return p1 + t * d1


def _refit_side(
    start: np.ndarray, end: np.ndarray, centre: np.ndarray, outline: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray]:
    """Refit one label side so that a small bump from an occluder does not tilt it.

    The side is cut into 48 pieces along its length. In each piece the
    outermost edge pixel within 10 pixels of the side is kept, and a line is
    fitted to those pixels with a Huber loss, which gives little weight to the
    few pieces where an occluder sticks out past the label. Returns two points
    on the fitted line, or the original end points when there is too little
    evidence.
    """
    if outline is None:
        return start, end
    length = float(np.linalg.norm(end - start))
    direction = (end - start) / length
    normal = np.array([-direction[1], direction[0]])
    if float(normal @ ((start + end) / 2 - centre)) < 0:
        normal = -normal
    relative = outline - start
    along = relative @ direction
    across = relative @ normal
    keep = (along > 0.03 * length) & (along < 0.97 * length) & (np.abs(across) <= 10)
    if keep.sum() < 20:
        return start, end
    bins = np.minimum((along[keep] / length * 48).astype(int), 47)
    points = outline[keep]
    distances = across[keep]
    chosen = []
    for index in range(48):
        members = np.flatnonzero(bins == index)
        if len(members):
            chosen.append(points[members[np.argmax(distances[members])]])
    if len(chosen) < 12:
        return start, end
    vx, vy, x0, y0 = cv2.fitLine(np.asarray(chosen, dtype=np.float32), cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    origin = np.array([x0, y0], dtype=np.float64)
    return origin, origin + np.array([vx, vy], dtype=np.float64)


def find_label_corners_fallback(image: np.ndarray) -> np.ndarray | None:
    """Rebuild label corners when something hides part of the outline.

    ``find_label_corners`` needs a clean four-sided contour, so a fingertip
    or tape crossing the edge makes it return None. This fallback takes the
    largest bright region and wraps it in its convex hull, which bridges
    notches cut by dark occluders. The longest hull edge is taken as one side
    of the label. The opposite side is the longest edge that is roughly
    parallel to it and far away; the other two sides are the two longest
    edges that are roughly perpendicular and far from each other. Neighbouring
    sides are intersected, so a corner that is itself covered is recovered as
    the crossing point of the two visible sides. Returns None unless the
    result is a convex quadrilateral inside the image that agrees with the
    hull area. Like the strict detector it uses only pixels.
    """
    _validate_image(image)
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, bright = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [contour for contour in contours if cv2.contourArea(contour) >= width * height * 0.15]
    if not contours:
        return None
    hull = cv2.convexHull(max(contours, key=cv2.contourArea))
    # The bright region stops at the inside of a printed border, a few pixels short of the
    # real label edge. Edge pixels just around that region include the outer outline, so the
    # hull of those edge pixels is the label outline itself.
    near = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(near, hull, 255)
    near = cv2.dilate(near, np.ones((25, 25), dtype=np.uint8))
    edge_points = cv2.findNonZero(cv2.bitwise_and(cv2.Canny(blurred, 40, 120), near))
    outline = None
    if edge_points is not None and len(edge_points) >= 4:
        hull = cv2.convexHull(edge_points)
        outline = edge_points.reshape(-1, 2).astype(np.float64)
    hull_area = cv2.contourArea(hull)
    polygon = cv2.approxPolyDP(hull, 2.0, True).reshape(-1, 2).astype(np.float64)
    if len(polygon) < 4 or hull_area <= 0:
        return None
    size = float(np.sqrt(hull_area))
    edges = []
    for index in range(len(polygon)):
        start, end = polygon[index], polygon[(index + 1) % len(polygon)]
        length = float(np.linalg.norm(end - start))
        if length >= 0.08 * size:
            edges.append((length, start, end))
    if len(edges) < 4:
        return None
    edges.sort(key=lambda edge: -edge[0])

    def angle_between(first: tuple, second: tuple) -> float:
        """Return the unsigned angle in degrees between two edges, from 0 to 90."""
        a, b = first[2] - first[1], second[2] - second[1]
        cosine = abs(float(a @ b)) / (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.degrees(np.arccos(np.clip(cosine, 0.0, 1.0))))

    def separation(first: tuple, second: tuple) -> float:
        """Return the distance from the midpoint of one edge to the line through the other."""
        middle = (second[1] + second[2]) / 2
        direction = (first[2] - first[1]) / np.linalg.norm(first[2] - first[1])
        offset = middle - first[1]
        return float(abs(direction[0] * offset[1] - direction[1] * offset[0]))

    base = edges[0]
    opposite = next(
        (edge for edge in edges[1:] if angle_between(base, edge) < 25 and separation(base, edge) > 0.3 * size), None
    )
    across = [edge for edge in edges[1:] if angle_between(base, edge) > 55]
    pair = next(
        (
            (first, second)
            for position, first in enumerate(across)
            for second in across[position + 1:]
            if separation(first, second) > 0.3 * size
        ),
        None,
    )
    if opposite is None or pair is None:
        return None
    centre = polygon.mean(axis=0)
    sides = sorted(
        [base, opposite, *pair],
        key=lambda edge: np.arctan2(*(((edge[1] + edge[2]) / 2 - centre)[::-1])),
    )
    lines = [_refit_side(edge[1], edge[2], centre, outline) for edge in sides]
    corners = []
    for index in range(4):
        point = _line_intersection(lines[index], lines[(index + 1) % 4])
        if point is None:
            return None
        corners.append(point)
    points = np.asarray(corners, dtype=np.float32)
    if (
        not np.isfinite(points).all()
        or (points[:, 0] <= 0).any() or (points[:, 0] >= width - 1).any()
        or (points[:, 1] <= 0).any() or (points[:, 1] >= height - 1).any()
    ):
        return None
    try:
        ordered = order_corners(points)
    except ValueError:
        return None
    area = cv2.contourArea(ordered)
    if not 0.95 <= area / hull_area <= 1.25:
        return None
    return ordered


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
