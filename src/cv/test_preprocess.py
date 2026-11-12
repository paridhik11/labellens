"""Checks for image-only label detection and perspective correction."""

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from src.cv.preprocess import evaluate_dataset, find_label_corners, main, order_corners, rectify_label
from src.gen.generate_dataset import generate_dataset


@pytest.fixture(scope="module")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build one known label in each photo condition for integration checks."""
    folder = tmp_path_factory.mktemp("preprocess")
    generate_dataset(folder, seed=42, labels_per_condition=1)
    return folder


@pytest.mark.parametrize("condition", ["clean", "moderate", "hard"])
def test_generated_label_corners(dataset: Path, condition: str) -> None:
    """Detect known corners from pixels without changing the input image."""
    stem = dataset / condition / f"test_label_001_{condition}"
    truth = json.loads(stem.with_suffix(".json").read_text(encoding="utf-8"))
    with Image.open(stem.with_suffix(".png")) as photo:
        image = np.asarray(photo.convert("RGB"))
    before = image.copy()
    corners = find_label_corners(image)
    assert corners is not None
    assert corners.shape == (4, 2)
    assert np.linalg.norm(corners - np.asarray(truth["label_quad_px"]), axis=1).max() <= 10
    assert np.array_equal(corners, find_label_corners(image))
    assert np.array_equal(image, before)
    corrected, matrix = rectify_label(image, corners)
    assert corrected.dtype == np.uint8
    assert corrected.ndim == 3
    assert corrected.shape[0] > 100 and corrected.shape[1] > 100
    projected = np.column_stack([corners, np.ones(4)]) @ matrix.T
    projected = projected[:, :2] / projected[:, 2:]
    height, width = corrected.shape[:2]
    assert np.allclose(projected, [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])


def test_order_corners() -> None:
    """An unordered tilted rectangle has a stable clockwise corner order."""
    expected = np.array([[20, 10], [120, 30], [100, 90], [10, 70]], dtype=np.float32)
    actual = order_corners(expected[[2, 0, 3, 1]])
    assert np.array_equal(actual, expected)


def test_rectify_known_rectangle() -> None:
    """Recover an exact RGB crop, including orientation and channel order."""
    image = np.zeros((100, 150, 3), dtype=np.uint8)
    image[20:50, 20:70] = (255, 0, 0)
    image[20:50, 70:120] = (0, 255, 0)
    image[50:80, 70:120] = (0, 0, 255)
    image[50:80, 20:70] = (255, 255, 0)
    corners = np.array([[119, 79], [20, 20], [20, 79], [119, 20]])
    corrected, matrix = rectify_label(image, corners)
    assert np.array_equal(corrected, image[20:80, 20:120])
    assert np.allclose(matrix, [[1, 0, -20], [0, 1, -20], [0, 0, 1]])


def test_rectify_perspective() -> None:
    """Correct a known perspective warp while preserving coloured quadrants."""
    source = np.zeros((60, 100, 3), dtype=np.uint8)
    source[:30, :50] = (255, 0, 0)
    source[:30, 50:] = (0, 255, 0)
    source[30:, 50:] = (0, 0, 255)
    source[30:, :50] = (255, 255, 0)
    original = np.array([[0, 0], [99, 0], [99, 59], [0, 59]], dtype=np.float32)
    corners = np.array([[30, 20], [140, 35], [125, 100], [15, 90]], dtype=np.float32)
    forward = cv2.getPerspectiveTransform(original, corners)
    photo = cv2.warpPerspective(source, forward, (160, 120))
    corrected, backward = rectify_label(photo, corners)
    height, width = corrected.shape[:2]
    assert np.array_equal(corrected[height // 4, width // 4], (255, 0, 0))
    assert np.array_equal(corrected[height // 4, 3 * width // 4], (0, 255, 0))
    assert np.array_equal(corrected[3 * height // 4, 3 * width // 4], (0, 0, 255))
    assert np.array_equal(corrected[3 * height // 4, width // 4], (255, 255, 0))
    projected = np.column_stack([corners, np.ones(4)]) @ backward.T
    expected = [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]
    assert np.allclose(projected[:, :2] / projected[:, 2:], expected)


def test_largest_label_boundary() -> None:
    """Select the dominant bright rectangle instead of a small distractor."""
    image = np.full((300, 500, 3), 60, dtype=np.uint8)
    cv2.rectangle(image, (80, 50), (420, 250), (255, 255, 255), thickness=-1)
    cv2.rectangle(image, (10, 10), (35, 35), (255, 255, 255), thickness=-1)
    corners = find_label_corners(image)
    assert corners is not None
    assert np.allclose(corners, [[80, 50], [420, 50], [420, 250], [80, 250]], atol=3)


@pytest.mark.parametrize("value", [0, 127, 255])
def test_blank_image(value: int) -> None:
    """A blank image has no label boundary and must not become a full-frame guess."""
    assert find_label_corners(np.full((200, 300, 3), value, dtype=np.uint8)) is None


def test_text_without_label() -> None:
    """Text on a borderless white image does not establish a label outline."""
    image = np.full((200, 300, 3), 255, dtype=np.uint8)
    cv2.putText(image, "NO BORDER", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0))
    assert find_label_corners(image) is None


@pytest.mark.parametrize(
    "image",
    [
        np.zeros((0, 20, 3), dtype=np.uint8),
        np.zeros((1, 20, 3), dtype=np.uint8),
        np.zeros((20, 20), dtype=np.uint8),
        np.zeros((20, 20, 4), dtype=np.uint8),
        np.zeros((20, 20, 3), dtype=np.float32),
    ],
)
def test_invalid_images(image: np.ndarray) -> None:
    """Both public image functions reject unsupported shapes and dtypes."""
    with pytest.raises(ValueError, match="uint8 RGB"):
        find_label_corners(image)
    with pytest.raises(ValueError, match="uint8 RGB"):
        rectify_label(image, np.array([[0, 0], [10, 0], [10, 10], [0, 10]]))


@pytest.mark.parametrize(
    "corners",
    [
        [[0, 0], [10, 0], [10, 10]],
        [[0, 0], [10, 0], [10, 10], [0, np.nan]],
        [[0, 0], [10, 0], [10, 10], [0, np.inf]],
        [[0, 0], [10, 0], [10, 10], [0, 0]],
        [[0, 0], [1, 1], [2, 2], [3, 3]],
        [[0, 0], [10, 0], [0, 10], [2, 2]],
    ],
)
def test_invalid_corners(corners: list[list[float]]) -> None:
    """Reject missing, nonfinite, repeated, collinear and concave corners."""
    with pytest.raises(ValueError):
        order_corners(np.asarray(corners))
    with pytest.raises(ValueError):
        rectify_label(np.zeros((20, 20, 3), dtype=np.uint8), np.asarray(corners))


def test_corners_outside_image() -> None:
    """Reject a quadrilateral that extends beyond the input image."""
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="inside the image"):
        rectify_label(image, np.array([[-1, 0], [10, 0], [10, 10], [-1, 10]]))


def test_evaluation_and_cli(dataset: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Report separate measured counts with explicit denominators and errors."""
    results = evaluate_dataset(dataset)
    for condition in ("clean", "moderate", "hard"):
        assert results[condition]["images"] == 1
        assert results[condition]["detected"] == 1
        assert results[condition]["within_10px"] == 1
        assert 0 <= results[condition]["mean_corner_error_px"] <= 10
        assert results[condition]["mean_corner_error_px"] <= results[condition]["max_corner_error_px"] <= 10
    assert main(["--dataset", str(dataset)]) == 0
    output = capsys.readouterr().out
    assert "no OCR run" in output
    for condition in ("clean", "moderate", "hard"):
        assert f"{condition}: detected=1/1, within_10px=1/1" in output


def test_missing_detection_is_counted(
    dataset: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Failed detections stay in denominators and have no invented corner error."""
    monkeypatch.setattr("src.cv.preprocess.find_label_corners", lambda image: None)
    results = evaluate_dataset(dataset)
    for result in results.values():
        assert result == {
            "images": 1, "detected": 0, "within_10px": 0,
            "mean_corner_error_px": None, "max_corner_error_px": None,
        }
    assert main(["--dataset", str(dataset)]) == 0
    assert "detected=0/1, within_10px=0/1, mean_corner_error_px=N/A" in capsys.readouterr().out
