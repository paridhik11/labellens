"""Training crops for the classifier: procedural pictograms degraded like photos, and crops mined from labels.

A procedural crop is made by printing a random pictogram (or a non-pictogram) on a noisy, unevenly lit 600 px
canvas, rotating and warping it, blurring, adding noise and sometimes glare, then running the *same* candidate
finder as for real labels and keeping the candidate that overlaps the printed box. That way the classifier sees
exactly what the detector will show it.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.cv.symbols_v2.candidates import propose
from src.gen.symbol_procedural import random_sample

CANVAS = 600
LABEL_INDEX = {"manufacturer": 0, "expiry": 1, "other": 2}


def _iou(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    """Intersection over union of two x, y, w, h boxes."""
    x1, y1, w1, h1 = first
    x2, y2, w2, h2 = second
    inter = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
    return inter / (w1 * h1 + w2 * h2 - inter)


def _text_clutter(canvas: np.ndarray, rng: np.random.Generator, avoid: tuple[int, int, int, int]) -> None:
    """Print a few random text lines (default font) away from ``avoid`` so letters appear as candidates."""
    image = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(image)
    for _ in range(int(rng.integers(0, 4))):
        size = int(rng.integers(34, 80))
        text = "".join(rng.choice(list("ABCDEFGHKLMNPRSTUWXYZ0123456789 :-"), int(rng.integers(3, 12))))
        x, y = int(rng.integers(20, 300)), int(rng.integers(20, CANVAS - 100))
        if y + size > avoid[1] - 10 and y < avoid[1] + avoid[3] + 10:
            continue
        draw.text((x, y), text, font=ImageFont.load_default(size=size), fill=int(rng.integers(0, 60)))
    canvas[:] = np.asarray(image, dtype=np.float32)


def make_scene(label: str, rng: np.random.Generator) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Return a degraded grey canvas and the box of the printed object (axis-aligned, after the warp)."""
    size = int(rng.integers(50, 125))
    mask = np.asarray(random_sample(label, rng, size), dtype=np.float32) / 255.0
    base = float(rng.uniform(170, 250))
    yy, xx = np.mgrid[0:CANVAS, 0:CANVAS].astype(np.float32) / CANVAS - 0.5
    slope_x, slope_y = rng.uniform(-0.25, 0.25, 2)
    canvas = base * (1 + slope_x * xx + slope_y * yy)
    x, y = int(rng.integers(80, CANVAS - size - 80)), int(rng.integers(80, CANVAS - size - 80))
    ink = float(rng.uniform(0, 70))
    canvas[y:y + size, x:x + size] *= (ink + (255 - ink) * mask) / 255.0
    _text_clutter(canvas, rng, (x, y, size, size))
    corners = np.array([[0, 0], [CANVAS, 0], [CANVAS, CANVAS], [0, CANVAS]], np.float32)
    angle = np.deg2rad(rng.uniform(-12, 12))
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    moved = (corners - CANVAS / 2) @ rotation.T + CANVAS / 2 + rng.uniform(-18, 18, (4, 2))
    matrix = cv2.getPerspectiveTransform(corners, moved.astype(np.float32))
    canvas = cv2.warpPerspective(canvas, matrix, (CANVAS, CANVAS), borderMode=cv2.BORDER_REPLICATE)
    box = np.array([[[x, y], [x + size, y], [x + size, y + size], [x, y + size]]], np.float32)
    warped = cv2.perspectiveTransform(box, matrix)[0]
    left, top = warped.min(axis=0)
    right, bottom = warped.max(axis=0)
    if rng.random() < 0.25:
        cx, cy = rng.uniform(0.1, 0.9, 2) * CANVAS
        sigma = rng.uniform(0.05, 0.10) * CANVAS
        dist2 = (xx * CANVAS + CANVAS / 2 - cx) ** 2 + (yy * CANVAS + CANVAS / 2 - cy) ** 2
        canvas += rng.uniform(80, 200) * np.exp(-dist2 / (2 * sigma**2))
    canvas = cv2.GaussianBlur(canvas, (0, 0), float(rng.uniform(0.4, 1.8)))
    canvas += rng.normal(0, float(rng.uniform(0, 8)), canvas.shape)
    return np.clip(canvas, 0, 255).astype(np.uint8), (float(left), float(top), float(right - left), float(bottom - top))


def make_samples(seed: int, count: int) -> tuple[np.ndarray, np.ndarray]:
    """``count`` scenes per class; return encoded candidate crops and labels (0, 1, 2)."""
    from src.cv.symbols_v2.cnn import encode

    rng = np.random.default_rng(seed)
    inputs, labels = [], []
    for label, index in LABEL_INDEX.items():
        made = 0
        while made < count:
            gray, truth = make_scene(label, rng)
            candidates = propose(gray)
            if label == "other":
                for candidate in candidates:
                    inputs.append(encode(candidate.ink))
                    labels.append(index)
                    made += 1
                continue
            matches = [(c, _iou(c.box, truth)) for c in candidates]
            matches = [(c, v) for c, v in matches if v >= 0.4]
            if matches:
                best = max(matches, key=lambda pair: pair[1])[0]
                inputs.append(encode(best.ink))
                labels.append(index)
                made += 1
    return np.stack(inputs), np.array(labels, np.int64)


def mine_crops(roots: list[Path]) -> tuple[np.ndarray, np.ndarray]:
    """Candidate crops from train-split label sets: overlap with a present symbol is positive, the rest 'other'."""
    from src.cv.symbol_eval import load_dataset
    from src.cv.symbols_v2.candidates import prepare
    from src.cv.symbols_v2.cnn import encode

    inputs, labels = [], []
    for root in roots:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("split") != "train":
            raise ValueError(f"{root} is not a train-split set")
        for item in load_dataset(root):
            gray, factor = prepare(item.corrected)
            to_label = np.eye(3) if item.inverse is None else np.linalg.inv(item.inverse)
            truths = {}
            for name, (x, y, w, h) in item.present.items():
                corners = np.array([[[x, y], [x + w, y], [x + w, y + h], [x, y + h]]], np.float32)
                mapped = cv2.perspectiveTransform(corners, to_label)[0] * factor
                left, top = mapped.min(axis=0)
                right, bottom = mapped.max(axis=0)
                truths[name] = (float(left), float(top), float(right - left), float(bottom - top))
            for candidate in propose(gray):
                label = "other"
                for name, box in truths.items():
                    if _iou(candidate.box, box) >= 0.4:
                        label = name
                inputs.append(encode(candidate.ink))
                labels.append(LABEL_INDEX[label])
    return np.stack(inputs), np.array(labels, np.int64)
