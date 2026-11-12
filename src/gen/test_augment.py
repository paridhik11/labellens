"""Checks for reproducible photo effects and transformed positions."""

import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.gen.augment import augment_label, transform_box


@pytest.mark.parametrize("condition", ["clean", "moderate", "hard"])
def test_reproducible_augmentation(condition: str) -> None:
    """The same seed and condition must produce identical output."""
    image = Image.new("RGB", (300, 180), "white")
    ImageDraw.Draw(image).rectangle((30, 30, 100, 80), fill="black")
    first, first_matrix, first_corners = augment_label(image, condition, seed=42)
    second, second_matrix, second_corners = augment_label(image, condition, seed=42)
    assert np.array_equal(np.asarray(first), np.asarray(second))
    assert np.array_equal(first_matrix, second_matrix)
    assert first_corners == second_corners


@pytest.mark.parametrize("condition", ["clean", "moderate", "hard"])
def test_label_geometry(condition: str) -> None:
    """Returned label corners must agree with the transformation matrix."""
    image = Image.new("RGB", (300, 180), "white")
    photo, matrix, corners = augment_label(image, condition, seed=42)
    transformed = transform_box([0, 0, image.width - 1, image.height - 1], matrix)
    assert np.allclose(transformed, corners, atol=0.001)
    for x, y in transformed:
        assert 0 <= x < photo.width
        assert 0 <= y < photo.height
    if condition == "clean":
        assert np.array_equal(matrix, np.eye(3))
        assert corners == [[0, 0], [299, 0], [299, 179], [0, 179]]
        assert np.array_equal(np.asarray(image), np.asarray(photo))
    else:
        assert photo.width > image.width
        assert photo.height > image.height


def test_box_translation() -> None:
    """Check transformed field corners against a known movement."""
    matrix = np.array([[1, 0, 5], [0, 1, 7], [0, 0, 1]], dtype=float)
    assert np.allclose(
        transform_box([10, 20, 30, 40], matrix),
        [[15, 27], [45, 27], [45, 67], [15, 67]],
    )


def test_box_perspective() -> None:
    """Check corner order and perspective division against known coordinates."""
    matrix = np.array([[2, 0, 2], [0, 3, 6], [0.5, 0, 1]], dtype=float)
    # Map (x, y) to ((2*x + 2)/(0.5*x + 1), (3*y + 6)/(0.5*x + 1)).
    assert np.allclose(
        transform_box([0, 0, 2, 2], matrix),
        [[2, 6], [3, 3], [3, 6], [2, 12]],
    )


def test_unknown_condition() -> None:
    """Reject unsupported difficulty levels."""
    with pytest.raises(ValueError, match="Unknown condition"):
        augment_label(Image.new("RGB", (100, 60)), "unknown", seed=42)
