"""Random pictograms for training a classifier: jittered variants of the *seen* geometry families only.

Positives (``manufacturer``, ``expiry``) are random saw-tooth and flat-block factories and straight and curved
hourglasses, with random vertex jitter, aspect, render mode (outline, filled, duo), stroke weight and rounding.
The families used by the dev and held-out splits (gable roof, three-tooth tower, tank with stacks, triangles,
framed glass, round bulbs) and the ``badge`` render mode are deliberately absent, so a held-out style is
still unseen. Negatives (``other``) are jittered train distractors, random shapes and large letters or digits.
All of it is synthetic and drawn by one author.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.gen.symbol_styles import (
    SUPERSAMPLE,
    TRAIN_DISTRACTORS,
    Primitive,
    Style,
    primitives,
    render_primitives,
    styles_in,
)

POSITIVE_MODES = ("outline", "filled", "duo")


def _rect(x0: float, y0: float, x1: float, y1: float) -> tuple[tuple[float, float], ...]:
    """Corner points of a rectangle."""
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def _sawtooth(rng: np.random.Generator) -> list[Primitive]:
    """Saw-tooth roofs (one or two teeth) with a chimney at one end and some windows."""
    teeth = int(rng.integers(1, 3))
    chimney = rng.uniform(0.13, 0.20)
    top = rng.uniform(0.10, 0.28)
    valley = rng.uniform(0.50, 0.60)
    peak = rng.uniform(0.28, 0.40)
    start, end = 0.06, 0.94
    pts = [(start, 0.92), (start, top), (start + chimney, top), (start + chimney, valley)]
    cursor = start + chimney
    width = (end - cursor) / teeth
    for _ in range(teeth):
        pts += [(cursor, peak), (cursor + width, valley)]
        cursor += width
    pts += [(end, valley), (end, 0.92)]
    prims: list[Primitive] = [("poly", tuple(pts), "body")]
    windows = int(rng.integers(0, 4))
    for index in range(windows):
        x = 0.16 + index * 0.24
        prims.append(("poly", _rect(x, 0.68, x + 0.12, 0.80), "detail"))
    if rng.random() < 0.5:
        prims = [(kind, tuple((1 - p[0], p[1]) for p in data), role) if kind == "poly" else (kind, data, role)
                 for kind, data, role in prims]
    return prims


def _block(rng: np.random.Generator) -> list[Primitive]:
    """A flat block with one or two chimneys, an optional door and an optional smoke puff."""
    top = rng.uniform(0.34, 0.46)
    prims: list[Primitive] = [("poly", _rect(0.08, top, 0.92, 0.92), "body")]
    chimneys = int(rng.integers(1, 3))
    for index in range(chimneys):
        left = 0.20 + index * 0.44 + rng.uniform(-0.04, 0.04)
        width = rng.uniform(0.13, 0.18)
        prims.append(("poly", _rect(left, rng.uniform(0.10, 0.26), left + width, top), "body"))
    if rng.random() < 0.7:
        prims.append(("poly", _rect(0.42, 0.62, 0.58, 0.92), "detail"))
    if rng.random() < 0.4:
        prims.append(("circle", (0.70, 0.06, 0.05), "accent"))
    return prims


def _straight_glass(rng: np.random.Generator) -> list[Primitive]:
    """An hourglass with straight sides and a pinched neck."""
    half = rng.uniform(0.26, 0.34)
    neck = rng.uniform(0.02, 0.10)
    straight = rng.uniform(0.10, 0.25) * 0.78
    glass = ((0.5 - half, 0.11), (0.5 + half, 0.11), (0.5 + half, 0.11 + straight), (0.5 + neck, 0.5),
             (0.5 + half, 0.89 - straight), (0.5 + half, 0.89), (0.5 - half, 0.89), (0.5 - half, 0.89 - straight),
             (0.5 - neck, 0.5), (0.5 - half, 0.11 + straight))
    cap = rng.uniform(0.34, 0.40)
    prims: list[Primitive] = [("poly", _rect(0.5 - cap, 0.03, 0.5 + cap, 0.11), "cap"),
                              ("poly", _rect(0.5 - cap, 0.89, 0.5 + cap, 0.97), "cap"), ("poly", glass, "body")]
    if rng.random() < 0.7:
        prims.append(("poly", ((0.5 - half + 0.08, 0.89), (0.5 + half - 0.08, 0.89), (0.5, 0.64)), "accent"))
    return prims


def _curved_glass(rng: np.random.Generator) -> list[Primitive]:
    """An hourglass with curved, funnel-like bulbs."""
    maximum = rng.uniform(0.24, 0.33)
    minimum = rng.uniform(0.03, 0.08)
    power = rng.uniform(0.6, 1.5)
    left, right = [], []
    for step in range(25):
        y = 0.11 + 0.78 * step / 24
        t = abs((y - 0.5) / 0.39)
        half = minimum + (maximum - minimum) * math.sin(t * math.pi / 2) ** power
        left.append((0.5 - half, y))
        right.append((0.5 + half, y))
    cap = rng.uniform(0.34, 0.40)
    prims: list[Primitive] = [("poly", _rect(0.5 - cap, 0.03, 0.5 + cap, 0.11), "cap"),
                              ("poly", _rect(0.5 - cap, 0.89, 0.5 + cap, 0.97), "cap"),
                              ("poly", tuple(left + right[::-1]), "body")]
    if rng.random() < 0.7:
        prims.append(("poly", ((0.36, 0.89), (0.64, 0.89), (0.60, 0.78), (0.50, 0.70), (0.40, 0.78)), "accent"))
    return prims


def _jitter(prims: list[Primitive], rng: np.random.Generator, amount: float = 0.02) -> list[Primitive]:
    """Add vertex noise and a mild aspect change and shear to a whole pictogram (kept inside the unit square)."""
    sx, sy = rng.uniform(0.85, 1.15), rng.uniform(0.85, 1.15)
    shear = rng.uniform(-0.08, 0.08)

    def move(p: tuple[float, float]) -> tuple[float, float]:
        x, y = (p[0] - 0.5) * sx, (p[1] - 0.5) * sy
        x += shear * y
        return (float(np.clip(0.5 + x + rng.normal(0, amount), 0.0, 1.0)),
                float(np.clip(0.5 + y + rng.normal(0, amount), 0.0, 1.0)))

    out: list[Primitive] = []
    for kind, data, role in prims:
        if kind == "circle":
            cx, cy, radius = data
            nx, ny = move((cx, cy))
            out.append((kind, (nx, ny, radius * float(rng.uniform(0.85, 1.15))), role))
        else:
            out.append((kind, tuple(move(p) for p in data), role))
    return out


def random_style(rng: np.random.Generator, modes: tuple[str, ...] = POSITIVE_MODES) -> Style:
    """A random train-compatible render style (geometry is chosen separately)."""
    return Style("proc", "train", str(rng.choice(modes)), float(rng.uniform(0.03, 0.11)), bool(rng.random() < 0.5),
                 "F1", "H1")


def random_positive(name: str, rng: np.random.Generator, size: int = 96) -> Image.Image:
    """Render a random manufacturer or expiry pictogram as an 'L' image (0 is ink)."""
    if name == "manufacturer":
        prims = _sawtooth(rng) if rng.random() < 0.5 else _block(rng)
    else:
        prims = _straight_glass(rng) if rng.random() < 0.5 else _curved_glass(rng)
    return render_primitives(_jitter(prims, rng), name, random_style(rng), size, size)


def _random_shape(rng: np.random.Generator) -> list[Primitive]:
    """A random simple shape that is not a pictogram: polygon, ring, plus sign or zigzag."""
    kind = int(rng.integers(0, 4))
    if kind == 0:
        count = int(rng.integers(3, 9))
        angles = np.sort(rng.uniform(0, 2 * math.pi, count))
        radii = rng.uniform(0.25, 0.46, count)
        points = tuple((0.5 + r * math.cos(a), 0.5 + r * math.sin(a)) for a, r in zip(angles, radii, strict=True))
        return [("poly", points, "body")]
    if kind == 1:
        outer, inner = rng.uniform(0.25, 0.44), rng.uniform(0.05, 0.2)
        return [("circle", (0.5, 0.5, outer), "body"), ("circle", (0.5, 0.5, inner), "detail")]
    if kind == 2:
        arm = rng.uniform(0.08, 0.16)
        return [("poly", _rect(0.5 - arm, 0.08, 0.5 + arm, 0.92), "body"),
                ("poly", _rect(0.08, 0.5 - arm, 0.92, 0.5 + arm), "body")]
    steps = int(rng.integers(3, 7))
    return [("line", tuple((0.08 + 0.84 * i / steps, 0.25 + 0.5 * (i % 2)) for i in range(steps + 1)), "body")]


def _letters(rng: np.random.Generator, size: int) -> Image.Image:
    """Render one to three large letters or digits as an 'L' image (0 is ink)."""
    text = "".join(rng.choice(list("ABCDEFGHKLMNPRSTUWXYZ0123456789"), int(rng.integers(1, 4))))
    font = ImageFont.load_default(size=int(size * rng.uniform(0.5, 0.9)))
    big = Image.new("L", (size * SUPERSAMPLE // 2, size * SUPERSAMPLE // 2), 255)
    ImageDraw.Draw(big).text((big.width // 2, big.height // 2), text, font=font.font_variant(size=int(size * 1.4)),
                             fill=0, anchor="mm")
    return big.resize((size, size), Image.Resampling.LANCZOS)


def random_other(rng: np.random.Generator, size: int = 96) -> Image.Image:
    """Render a random non-pictogram: a jittered train distractor, a random shape, or letters."""
    pick = rng.random()
    if pick < 0.40:
        name = str(rng.choice(TRAIN_DISTRACTORS))
        style = random_style(rng, modes=("outline", "filled", "duo"))
        return render_primitives(_jitter(primitives(name, styles_in("train")[0]), rng), name, style, size, size)
    if pick < 0.75:
        return render_primitives(_random_shape(rng), "shape", random_style(rng), size, size)
    return _letters(rng, size)


def random_sample(label: str, rng: np.random.Generator, size: int = 96) -> Image.Image:
    """Render a random sample of ``manufacturer``, ``expiry`` or ``other``."""
    return random_other(rng, size) if label == "other" else random_positive(label, rng, size)
