"""Reproducible photo effects and coordinate transforms for test labels."""

from typing import Literal

import cv2
import numpy as np
from PIL import Image

Condition = Literal["clean", "moderate", "hard"]


def augment_label(
    image: Image.Image,
    condition: Condition,
    seed: int,
) -> tuple[Image.Image, np.ndarray, list[list[float]]]:
    """Return an augmented image, source-to-photo matrix, and label corners."""
    if condition not in {"clean", "moderate", "hard"}:
        raise ValueError(f"Unknown condition: {condition}")

    source_image = np.asarray(image.convert("RGB"))
    height, width = source_image.shape[:2]
    corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    if condition == "clean":
        return image.convert("RGB"), np.eye(3), corners.astype(float).tolist()

    rng = np.random.default_rng(seed)
    hard = condition == "hard"
    margin = round(max(width, height) * 0.35)
    canvas_width = width + 2 * margin
    canvas_height = height + 2 * margin

    # Rotate the label, then move its corners independently for perspective.
    angle = np.deg2rad(rng.uniform(-18, 18) if hard else rng.uniform(-7, 7))
    rotation = np.array(
        [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    )
    centre = np.array([(width - 1) / 2, (height - 1) / 2])
    destination = (corners - centre) @ rotation.T + centre + margin
    jitter = min(width, height) * (0.07 if hard else 0.025)
    destination += rng.uniform(-jitter, jitter, size=(4, 2))
    destination = destination.astype(np.float32)

    matrix = cv2.getPerspectiveTransform(corners, destination)
    warped = cv2.warpPerspective(
        source_image, matrix, (canvas_width, canvas_height),
        flags=cv2.INTER_LINEAR,
    )
    mask = cv2.warpPerspective(
        np.full((height, width), 255, dtype=np.uint8),
        matrix, (canvas_width, canvas_height),
        flags=cv2.INTER_LINEAR,
    ).astype(np.float32) / 255

    background_colour = rng.integers(60, 190, size=3).astype(np.float32)
    background = np.empty((canvas_height, canvas_width, 3), dtype=np.float32)
    background[:] = background_colour
    photo = warped.astype(np.float32) + background * (1 - mask[..., None])

    # A gradual brightness change simulates uneven illumination.
    horizontal = np.linspace(-1, 1, canvas_width, dtype=np.float32)[None, :]
    vertical = np.linspace(-1, 1, canvas_height, dtype=np.float32)[:, None]
    strength = 0.30 if hard else 0.12
    lighting = (
        rng.uniform(0.80, 1.0)
        + rng.uniform(-strength, strength) * horizontal
        + rng.uniform(-strength, strength) * vertical
    )
    photo *= lighting[..., None]
    sigma = rng.uniform(1.0, 1.8) if hard else rng.uniform(0.3, 0.7)
    photo = cv2.GaussianBlur(photo, (0, 0), sigmaX=sigma)
    photo += rng.normal(0, 8 if hard else 2, size=photo.shape)
    result = Image.fromarray(np.clip(photo, 0, 255).astype(np.uint8))
    return result, matrix, destination.astype(float).tolist()


def transform_box(
    bbox: list[float],
    matrix: np.ndarray,
) -> list[list[float]]:
    """Transform an x, y, width, height box into four photo-space corners."""
    x, y, width, height = bbox
    points = np.array(
        [[[x, y], [x + width, y], [x + width, y + height], [x, y + height]]],
        dtype=np.float32,
    )
    transformed = cv2.perspectiveTransform(points, matrix.astype(np.float64))
    return transformed[0].astype(float).tolist()
