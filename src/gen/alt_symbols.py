"""Second, independent set of test pictograms and some distractors.

These drawings are deliberately NOT produced by ``src.gen.symbols.draw_symbol``,
the function that also creates the reference templates of the detector. They
are filled silhouettes with different proportions, closer in spirit to the
real ISO 7000 "manufacturer" and "use by" pictograms, and are used only to
test how well a detector copes with artwork it has no reference for. They are
still simplified synthetic drawings, not certified ISO artwork.
"""

from PIL import ImageDraw

ALT_NAMES = ("manufacturer", "expiry")
DISTRACTOR_NAMES = ("caution", "temperature")


def _mapper(bbox: tuple[int, int, int, int]):
    """Return a function that maps relative 0 to 1 coordinates into the pixel box."""
    x, y, width, height = bbox

    def point(u: float, v: float) -> tuple[int, int]:
        return round(x + u * width), round(y + v * height)

    return point


def draw_alt_symbol(draw: ImageDraw.ImageDraw, name: str, bbox: tuple[int, int, int, int]) -> None:
    """Draw the filled-silhouette version of a supported pictogram in an x, y, width, height box."""
    if name not in ALT_NAMES:
        raise ValueError(f"Unknown alternative symbol: {name}")
    if bbox[2] < 10 or bbox[3] < 10:
        raise ValueError("Symbol box must be at least 10 pixels per side")
    point = _mapper(bbox)
    stroke = max(1, round(min(bbox[2], bbox[3]) * 0.07))
    if name == "manufacturer":
        # Filled factory: tall chimney on the left, saw-tooth roof with two teeth.
        draw.polygon(
            [
                point(0.05, 0.95), point(0.05, 0.05), point(0.25, 0.05), point(0.25, 0.55),
                point(0.60, 0.35), point(0.60, 0.55), point(0.95, 0.35), point(0.95, 0.95),
            ],
            fill="black",
        )
    else:
        # Hourglass: two bars, a glass outline and a filled lower half.
        draw.rectangle([point(0.12, 0.04), point(0.88, 0.12)], fill="black")
        draw.rectangle([point(0.12, 0.88), point(0.88, 0.96)], fill="black")
        draw.line(
            [point(0.22, 0.12), point(0.22, 0.28), point(0.50, 0.50), point(0.78, 0.28), point(0.78, 0.12)],
            fill="black", width=stroke,
        )
        draw.polygon([point(0.50, 0.50), point(0.80, 0.74), point(0.80, 0.88), point(0.20, 0.88), point(0.20, 0.74)],
                     fill="black")


def draw_distractor(draw: ImageDraw.ImageDraw, name: str, bbox: tuple[int, int, int, int]) -> None:
    """Draw a pictogram that is neither manufacturer nor expiry (a wrong symbol)."""
    if name not in DISTRACTOR_NAMES:
        raise ValueError(f"Unknown distractor symbol: {name}")
    if bbox[2] < 10 or bbox[3] < 10:
        raise ValueError("Symbol box must be at least 10 pixels per side")
    point = _mapper(bbox)
    stroke = max(1, round(min(bbox[2], bbox[3]) * 0.05))
    if name == "caution":
        draw.line([point(0.5, 0.08), point(0.94, 0.9), point(0.06, 0.9), point(0.5, 0.08)], fill="black", width=stroke)
        draw.rectangle([point(0.46, 0.36), point(0.54, 0.66)], fill="black")
        draw.ellipse([point(0.45, 0.72), point(0.55, 0.82)], fill="black")
    else:
        draw.rounded_rectangle([point(0.40, 0.06), point(0.60, 0.70)], radius=stroke * 2, outline="black", width=stroke)
        draw.ellipse([point(0.30, 0.60), point(0.70, 0.96)], fill="black")
        draw.rectangle([point(0.47, 0.30), point(0.53, 0.70)], fill="black")
