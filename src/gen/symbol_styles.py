"""A parametric library of manufacturer and hourglass pictogram styles, for detector tests.

Written from scratch for the symbol-generalisation experiments: it does not
import or copy the geometry of ``src.gen.symbols`` (the artwork the original
detector was built on) or of ``src.gen.alt_symbols``. Each *style* combines

* a render mode (``outline``, ``filled``, ``duo`` = outlined body with a filled accent, ``badge`` = white
  glyph on a black rounded square),
* a stroke weight (share of the box side) and rounded or sharp corners,
* a geometry family for the factory (``F1`` to ``F4``) and for the hourglass (``H1`` to ``H4``).

Styles are split into ``train`` (used to build references and train classifiers), ``dev`` (used to tune
thresholds) and ``heldout`` (never used to build or tune anything; scored once on a frozen detector).
The held-out split uses geometry families and a render mode that no train style uses. All styles are
still simplified drawings by one author, not certified ISO artwork.

Distractor pictograms (``caution``, ``thermometer``, ``umbrella`` for training; ``circle_slash``, ``sun``,
``wineglass`` held out) are drawn in the same styles and serve as wrong-symbol negatives.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

SUPERSAMPLE = 4
SYMBOLS = ("manufacturer", "expiry")
TRAIN_DISTRACTORS = ("caution", "thermometer", "umbrella")
HELDOUT_DISTRACTORS = ("circle_slash", "sun", "wineglass")

Point = tuple[float, float]
# A primitive is (kind, data, role). kind: "poly" (closed), "line" (open), "circle" (centre, radius).
# role: "body" (main outline), "detail" (inner feature), "accent" (sand, smoke), "cap" (always solid).
Primitive = tuple[str, tuple, str]


@dataclass(frozen=True)
class Style:
    """One rendering style shared by both pictograms of a label."""

    id: str
    split: str
    mode: str
    stroke: float
    rounded: bool
    factory: str
    glass: str


STYLES: tuple[Style, ...] = (
    Style("t1", "train", "outline", 0.050, False, "F1", "H1"),
    Style("t2", "train", "outline", 0.090, True, "F2", "H2"),
    Style("t3", "train", "filled", 0.060, False, "F1", "H2"),
    Style("t4", "train", "filled", 0.080, True, "F2", "H1"),
    Style("t5", "train", "duo", 0.060, False, "F1", "H1"),
    Style("t6", "train", "duo", 0.080, True, "F2", "H2"),
    Style("t7", "train", "outline", 0.035, False, "F1", "H2"),
    Style("t8", "train", "filled", 0.050, False, "F2", "H1"),
    Style("d1", "dev", "outline", 0.060, True, "F1", "H2"),
    Style("d2", "dev", "filled", 0.070, False, "F2", "H2"),
    Style("d3", "dev", "outline", 0.060, False, "F5", "H5"),
    Style("d4", "dev", "filled", 0.060, True, "F5", "H5"),
    Style("h1", "heldout", "filled", 0.060, False, "F3", "H3"),
    Style("h2", "heldout", "outline", 0.040, False, "F3", "H3"),
    Style("h3", "heldout", "outline", 0.070, True, "F4", "H4"),
    Style("h4", "heldout", "filled", 0.050, False, "F4", "H4"),
    Style("h5", "heldout", "badge", 0.060, True, "F2", "H1"),
    Style("h6", "heldout", "outline", 0.120, True, "F3", "H1"),
)


def styles_in(split: str) -> tuple[Style, ...]:
    """Return the styles of one split (``train``, ``dev`` or ``heldout``)."""
    return tuple(style for style in STYLES if style.split == split)


def _rect(x0: float, y0: float, x1: float, y1: float) -> tuple[Point, ...]:
    """Corner points of a rectangle."""
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def _factory(family: str) -> list[Primitive]:
    """Primitives of a factory building in the unit square."""
    if family == "F1":  # chimney left, two saw-tooth roofs, three windows
        body = ((0.06, 0.92), (0.06, 0.14), (0.24, 0.14), (0.24, 0.52), (0.52, 0.32), (0.52, 0.52),
                (0.80, 0.32), (0.80, 0.52), (0.94, 0.44), (0.94, 0.92))
        windows = [("poly", _rect(x, 0.68, x + 0.12, 0.80), "detail") for x in (0.20, 0.44, 0.68)]
        return [("poly", body, "body"), *windows]
    if family == "F2":  # flat block, two chimneys, door, smoke puff
        return [
            ("poly", _rect(0.08, 0.38, 0.92, 0.92), "body"),
            ("poly", _rect(0.64, 0.14, 0.80, 0.38), "body"),
            ("poly", _rect(0.20, 0.22, 0.34, 0.38), "body"),
            ("poly", _rect(0.42, 0.62, 0.58, 0.92), "detail"),
            ("circle", (0.72, 0.07, 0.05), "accent"),
        ]
    if family == "F3":  # gable roof house-factory with stack and round window
        body = ((0.08, 0.92), (0.08, 0.48), (0.50, 0.16), (0.92, 0.48), (0.92, 0.92))
        return [
            ("poly", body, "body"),
            ("poly", _rect(0.66, 0.08, 0.80, 0.34), "body"),
            ("circle", (0.50, 0.50, 0.09), "detail"),
            ("poly", _rect(0.42, 0.70, 0.58, 0.92), "detail"),
        ]
    if family == "F5":  # tank and stacks: dome tank on the left, block with two stacks on the right
        dome = [(0.17 + 0.15 * math.cos(math.pi * (1 - i / 12)), 0.62 - 0.22 * math.sin(math.pi * (1 - i / 12)))
                for i in range(13)]
        return [
            ("poly", _rect(0.04, 0.62, 0.30, 0.92), "body"), ("poly", tuple(dome), "body"),
            ("poly", _rect(0.30, 0.42, 0.96, 0.92), "body"),
            ("poly", _rect(0.58, 0.10, 0.68, 0.42), "body"), ("poly", _rect(0.80, 0.18, 0.90, 0.42), "body"),
            ("poly", _rect(0.42, 0.56, 0.52, 0.68), "detail"), ("poly", _rect(0.72, 0.56, 0.82, 0.68), "detail"),
        ]
    # F4: three saw-teeth, a tall tower on the right with two smoke puffs
    body = ((0.04, 0.92), (0.04, 0.42), (0.24, 0.58), (0.24, 0.42), (0.44, 0.58), (0.44, 0.42), (0.64, 0.58),
            (0.64, 0.12), (0.84, 0.12), (0.84, 0.92))
    return [
        ("poly", body, "body"),
        ("circle", (0.74, 0.05, 0.04), "accent"),
        ("poly", _rect(0.14, 0.72, 0.24, 0.84), "detail"),
        ("poly", _rect(0.34, 0.72, 0.44, 0.84), "detail"),
    ]


def _glass(family: str) -> list[Primitive]:
    """Primitives of an hourglass in the unit square."""
    top, bottom = _rect(0.14, 0.03, 0.86, 0.11), _rect(0.14, 0.89, 0.86, 0.97)
    if family == "H1":  # straight-sided glass, sand in the lower half
        glass = ((0.22, 0.11), (0.78, 0.11), (0.78, 0.28), (0.54, 0.50), (0.78, 0.72), (0.78, 0.89), (0.22, 0.89),
                 (0.22, 0.72), (0.46, 0.50), (0.22, 0.28))
        sand = ((0.30, 0.89), (0.70, 0.89), (0.70, 0.78), (0.50, 0.62), (0.30, 0.78))
        return [("poly", top, "cap"), ("poly", bottom, "cap"), ("poly", glass, "body"), ("poly", sand, "accent")]
    if family == "H2":  # curved bulbs
        left, right = [], []
        for step in range(25):
            y = 0.11 + 0.78 * step / 24
            t = abs((y - 0.5) / 0.39)
            half = 0.05 + 0.26 * math.sin(t * math.pi / 2) ** 0.8
            left.append((0.5 - half, y))
            right.append((0.5 + half, y))
        glass = tuple(left + right[::-1])
        sand = ((0.36, 0.89), (0.64, 0.89), (0.60, 0.78), (0.50, 0.70), (0.40, 0.78))
        return [("poly", top, "cap"), ("poly", bottom, "cap"), ("poly", glass, "body"), ("poly", sand, "accent")]
    if family == "H3":  # two triangles tip to tip
        upper = ((0.16, 0.08), (0.84, 0.08), (0.50, 0.48))
        lower = ((0.50, 0.52), (0.84, 0.92), (0.16, 0.92))
        sand = ((0.34, 0.92), (0.66, 0.92), (0.50, 0.70))
        return [("poly", upper, "body"), ("poly", lower, "body"), ("poly", sand, "accent")]
    if family == "H5":  # two round bulbs joined by a neck
        return [
            ("poly", _rect(0.20, 0.03, 0.80, 0.10), "cap"), ("poly", _rect(0.20, 0.90, 0.80, 0.97), "cap"),
            ("circle", (0.50, 0.30, 0.20), "body"), ("circle", (0.50, 0.70, 0.20), "body"),
            ("poly", _rect(0.46, 0.46, 0.54, 0.54), "body"), ("circle", (0.50, 0.74, 0.09), "accent"),
        ]
    # H4: framed glass with two posts
    glass = ((0.28, 0.11), (0.72, 0.11), (0.72, 0.30), (0.54, 0.50), (0.72, 0.70), (0.72, 0.89), (0.28, 0.89),
             (0.28, 0.70), (0.46, 0.50), (0.28, 0.30))
    return [
        ("poly", _rect(0.08, 0.03, 0.92, 0.12), "cap"), ("poly", _rect(0.08, 0.88, 0.92, 0.97), "cap"),
        ("poly", _rect(0.10, 0.12, 0.17, 0.88), "cap"), ("poly", _rect(0.83, 0.12, 0.90, 0.88), "cap"),
        ("poly", glass, "body"), ("poly", ((0.40, 0.89), (0.60, 0.89), (0.50, 0.74)), "accent"),
    ]


def _distractor(name: str) -> list[Primitive]:
    """Primitives of a pictogram that is neither manufacturer nor expiry."""
    if name == "caution":
        return [("poly", ((0.50, 0.08), (0.94, 0.90), (0.06, 0.90)), "body"),
                ("poly", _rect(0.46, 0.36, 0.54, 0.64), "accent"), ("circle", (0.50, 0.75, 0.045), "accent")]
    if name == "thermometer":
        return [("poly", _rect(0.42, 0.06, 0.58, 0.66), "body"), ("circle", (0.50, 0.76, 0.20), "body"),
                ("poly", _rect(0.47, 0.30, 0.53, 0.70), "accent"), ("circle", (0.50, 0.76, 0.10), "accent")]
    if name == "umbrella":
        arc = [(0.5 + 0.44 * math.cos(math.pi * (1 - i / 16)), 0.52 - 0.40 * math.sin(math.pi * (1 - i / 16)))
               for i in range(17)]
        return [("poly", tuple(arc), "body"), ("line", ((0.50, 0.52), (0.50, 0.88), (0.42, 0.94)), "detail")]
    if name == "circle_slash":
        return [("circle", (0.50, 0.50, 0.42), "body"), ("line", ((0.20, 0.80), (0.80, 0.20)), "detail")]
    if name == "sun":
        rays = [("line", ((0.5 + 0.30 * math.cos(a), 0.5 + 0.30 * math.sin(a)),
                          (0.5 + 0.46 * math.cos(a), 0.5 + 0.46 * math.sin(a))), "detail")
                for a in (k * math.pi / 4 for k in range(8))]
        return [("circle", (0.50, 0.50, 0.20), "body"), *rays]
    if name == "wineglass":
        bowl = ((0.26, 0.06), (0.74, 0.06), (0.70, 0.40), (0.50, 0.56), (0.30, 0.40))
        return [("poly", bowl, "body"), ("line", ((0.50, 0.56), (0.50, 0.88)), "detail"),
                ("poly", _rect(0.30, 0.88, 0.70, 0.95), "cap")]
    raise ValueError(f"Unknown distractor: {name}")


def primitives(name: str, style: Style) -> list[Primitive]:
    """Return the geometry of a symbol or distractor under a style."""
    if name == "manufacturer":
        return _factory(style.factory)
    if name == "expiry":
        return _glass(style.glass)
    return _distractor(name)


def _scaled(points, size: tuple[int, int]) -> list[Point]:
    """Map unit coordinates to supersampled pixels, with a small safe margin."""
    width, height = size
    return [(0.04 * width + p[0] * 0.92 * width, 0.04 * height + p[1] * 0.92 * height) for p in points]


def _stroke_path(draw: ImageDraw.ImageDraw, points: list[Point], width: int, fill: int, rounded: bool, closed: bool):
    """Draw a polyline with optional round joins and ends."""
    path = points + ([points[0]] if closed else [])
    draw.line(path, fill=fill, width=width, joint="curve" if rounded else None)
    if rounded:
        radius = width / 2
        for x, y in points:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def render_mask(name: str, style: Style, width: int, height: int) -> Image.Image:
    """Render a symbol as an 'L' image: 0 is ink (black) and 255 is paper, antialiased by supersampling."""
    return render_primitives(primitives(name, style), name, style, width, height)


def render_primitives(
    prims: list[Primitive], name: str, style: Style, width: int, height: int
) -> Image.Image:
    """Render given primitives under a style (``name`` only selects a few special cases)."""
    big = (width * SUPERSAMPLE, height * SUPERSAMPLE)
    canvas = Image.new("L", big, 255)
    draw = ImageDraw.Draw(canvas)
    badge = style.mode == "badge"
    ink, paper = (255, 0) if badge else (0, 255)
    if badge:
        draw.rounded_rectangle((0, 0, big[0] - 1, big[1] - 1), radius=int(0.18 * min(big)), fill=0)
    mode = "filled" if badge else style.mode
    scale = 0.74 if badge else 1.0
    offset = (1 - scale) / 2

    def shrink(point: Point) -> Point:
        return (offset + point[0] * scale, offset + point[1] * scale)

    weight = max(2, round(style.stroke * min(big)))
    for kind, data, role in prims:
        if kind == "poly":
            pts = _scaled([shrink(p) for p in data], big)
            if role == "cap":
                draw.polygon(pts, fill=ink)
                if style.rounded:
                    _stroke_path(draw, pts, weight, ink, True, True)
            elif mode == "filled":
                if role == "body":
                    draw.polygon(pts, fill=ink)
                    if style.rounded:
                        _stroke_path(draw, pts, weight, ink, True, True)
                elif role == "detail":
                    draw.polygon(pts, fill=paper)
                else:
                    draw.polygon(pts, fill=paper)
            elif mode == "duo" and role == "accent":
                draw.polygon(pts, fill=ink)
            else:
                _stroke_path(draw, pts, weight, ink, style.rounded, True)
        elif kind == "circle":
            cx, cy, radius = data
            (x, y), = _scaled([shrink((cx, cy))], big)
            r = radius * 0.92 * scale * min(big)
            box = (x - r, y - r, x + r, y + r)
            if mode == "filled" and role == "detail":
                draw.ellipse(box, fill=paper)
            elif mode == "filled" or (mode == "duo" and role == "accent"):
                draw.ellipse(box, fill=ink if role != "accent" or not badge else ink)
            else:
                draw.ellipse(box, outline=ink, width=weight)
        else:  # open line
            pts = _scaled([shrink(p) for p in data], big)
            if mode == "filled" and role == "detail" and name in ("manufacturer", "expiry"):
                continue
            # A slash across a filled disc has to be cut out of it, not drawn in the disc's own ink.
            cut = mode == "filled" and name == "circle_slash"
            _stroke_path(draw, pts, weight, paper if cut else ink, style.rounded, False)
    return canvas.resize((width, height), Image.Resampling.LANCZOS)


def paste_symbol(
    image: Image.Image, name: str, style: Style, bbox: tuple[int, int, int, int], *, ink_level: int = 0
) -> None:
    """Darken the pixels of an RGB image with a rendered symbol (the symbol is printed, not pasted over white)."""
    x, y, width, height = bbox
    mask = np.asarray(render_mask(name, style, width, height), dtype=np.float32) / 255.0
    region = np.asarray(image.crop((x, y, x + width, y + height)), dtype=np.float32)
    ink = ink_level + (255 - ink_level) * mask
    out = region * (ink / 255.0)[..., None]
    image.paste(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), (x, y))


def style_sheet(styles: tuple[Style, ...], names: tuple[str, ...] = SYMBOLS, size: int = 96) -> Image.Image:
    """Return a contact sheet (rows = styles, columns = symbols) for looking at the library by eye."""
    sheet = Image.new("L", (size * len(names) + 40, size * len(styles)), 255)
    for row, style in enumerate(styles):
        for col, name in enumerate(names):
            sheet.paste(render_mask(name, style, size, size), (40 + col * size, row * size))
        ImageDraw.Draw(sheet).text((2, row * size + size // 2), style.id, fill=0)
    return sheet
