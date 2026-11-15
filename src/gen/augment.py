"""Reproducible photo effects and coordinate transforms for test labels."""

from typing import Any, Literal

import cv2
import numpy as np
from PIL import Image

Condition = Literal["clean", "moderate", "hard", "hard_original", "very_hard"]

# "hard" is the reduced setting introduced in commit 3c98598 (blur up to 1.6, noise 6).
# "hard_original" restores the setting used before that commit (blur up to 1.8, noise 8)
# so both can be reported side by side. "very_hard" is "hard" plus glare and occlusion.
ALL_CONDITIONS: tuple[str, ...] = ("clean", "moderate", "hard", "hard_original", "very_hard")
_HARD_FAMILY = {"hard", "hard_original", "very_hard"}


def _glare_and_occlusion(
    photo: np.ndarray, matrix: np.ndarray, size: tuple[int, int], seed: int
) -> dict[str, Any]:
    """Draw occluders and glare on a float photo in place and describe them.

    Occluders are opaque bars that enter from a label edge, like a fingertip
    or a strip of tape. Glare is a bright additive blob that saturates the
    pixels under it. Positions are drawn in label coordinates and mapped
    through the label-to-photo matrix. A separate random generator keeps the
    base photo identical to the "hard" photo that uses the same seed.
    """
    width, height = size
    rng = np.random.default_rng([seed, 1])
    transform = matrix.astype(np.float64)
    occluders = []
    for _ in range(int(rng.integers(1, 3))):
        edge = int(rng.integers(0, 4))
        reach = rng.uniform(0.10, 0.25)
        thickness = rng.uniform(0.06, 0.11) * width
        along = rng.uniform(0.05, 0.95)
        if edge == 0:
            box = [along * width - thickness / 2, -5.0, thickness, reach * height + 5.0]
        elif edge == 1:
            box = [width * (1 - reach), along * height - thickness / 2, reach * width + 5.0, thickness]
        elif edge == 2:
            box = [along * width - thickness / 2, height * (1 - reach), thickness, reach * height + 5.0]
        else:
            box = [-5.0, along * height - thickness / 2, reach * width + 5.0, thickness]
        colour = [float(value) for value in rng.integers(40, 200, size=3)]
        quad = cv2.perspectiveTransform(
            np.array(
                [[
                    [box[0], box[1]], [box[0] + box[2], box[1]],
                    [box[0] + box[2], box[1] + box[3]], [box[0], box[1] + box[3]],
                ]],
                dtype=np.float32,
            ),
            transform,
        )[0]
        cv2.fillConvexPoly(photo, np.round(quad).astype(np.int32), colour, lineType=cv2.LINE_AA)
        occluders.append({
            "source_bbox_px_xywh": [float(value) for value in box],
            "quad_px": quad.astype(float).tolist(),
        })
    glare = []
    yy, xx = np.mgrid[0:photo.shape[0], 0:photo.shape[1]].astype(np.float32)
    for _ in range(int(rng.integers(1, 3))):
        centre_source = np.array(
            [[[rng.uniform(0.1, 0.9) * width, rng.uniform(0.1, 0.9) * height]]], dtype=np.float32
        )
        centre = cv2.perspectiveTransform(centre_source, transform)[0, 0]
        sigma = float(rng.uniform(0.05, 0.10) * width)
        peak = float(rng.uniform(150, 230))
        blob = peak * np.exp(-((xx - centre[0]) ** 2 + (yy - centre[1]) ** 2) / (2 * sigma**2))
        photo += blob[..., None]
        glare.append({
            "source_centre_px": [float(value) for value in centre_source[0, 0]],
            "centre_px": [float(value) for value in centre],
            "sigma_px": sigma,
            "peak": peak,
        })
    return {"occluders": occluders, "glare": glare}


def augment_label_detailed(
    image: Image.Image,
    condition: Condition,
    seed: int,
) -> tuple[Image.Image, np.ndarray, list[list[float]], dict[str, Any]]:
    """Return an augmented image, source-to-photo matrix, label corners and effect details."""
    if condition not in ALL_CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")

    source_image = np.asarray(image.convert("RGB"))
    height, width = source_image.shape[:2]
    corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    if condition == "clean":
        return image.convert("RGB"), np.eye(3), corners.astype(float).tolist(), {}

    rng = np.random.default_rng(seed)
    hard = condition in _HARD_FAMILY
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
    details: dict[str, Any] = {}
    if condition == "very_hard":
        details = _glare_and_occlusion(photo, matrix, (width, height), seed)
    blur_top, hard_noise = (1.8, 8) if condition == "hard_original" else (1.6, 6)
    sigma = rng.uniform(1.0, blur_top) if hard else rng.uniform(0.3, 0.7)
    photo = cv2.GaussianBlur(photo, (0, 0), sigmaX=sigma)
    noise = hard_noise if hard else 2
    photo += rng.normal(0, noise, size=photo.shape)
    result = Image.fromarray(np.clip(photo, 0, 255).astype(np.uint8))
    details.update(blur_sigma=float(sigma), noise_sigma=float(noise))
    return result, matrix, destination.astype(float).tolist(), details


def augment_label(
    image: Image.Image,
    condition: Condition,
    seed: int,
) -> tuple[Image.Image, np.ndarray, list[list[float]]]:
    """Return an augmented image, source-to-photo matrix, and label corners."""
    result, matrix, corners, _ = augment_label_detailed(image, condition, seed)
    return result, matrix, corners


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
