"""Simplified pictograms for synthetic test labels only."""

from PIL import ImageDraw


def draw_symbol(
    draw: ImageDraw.ImageDraw,
    name: str,
    bbox: tuple[int, int, int, int],
) -> None:
    """Draw a supported pictogram inside an x, y, width, height box."""
    if name not in {"manufacturer", "expiry"}:
        raise ValueError(f"Unknown symbol: {name}")

    x, y, width, height = bbox
    if width < 10 or height < 10:
        raise ValueError("Symbol box must be at least 10 pixels per side")

    def point(u: float, v: float) -> tuple[int, int]:
        """Map relative coordinates to pixels inside the box."""
        return round(x + u * width), round(y + v * height)

    stroke = max(1, round(min(width, height) * 0.05))
    if name == "manufacturer":
        outline = [
            point(0.1, 0.9), point(0.1, 0.45),
            point(0.35, 0.3), point(0.35, 0.45),
            point(0.6, 0.3), point(0.6, 0.55),
            point(0.75, 0.55), point(0.75, 0.1),
            point(0.9, 0.1), point(0.9, 0.9),
            point(0.1, 0.9),
        ]
        draw.line(outline, fill="black", width=stroke)
        for u in (0.25, 0.45, 0.65):
            draw.rectangle(
                [point(u, 0.68), point(u + 0.08, 0.8)], fill="black"
            )
    else:
        draw.line(
            [point(0.15, 0.1), point(0.85, 0.1)],
            fill="black", width=stroke,
        )
        draw.line(
            [point(0.15, 0.9), point(0.85, 0.9)],
            fill="black", width=stroke,
        )
        draw.line(
            [
                point(0.25, 0.1), point(0.25, 0.25),
                point(0.75, 0.75), point(0.75, 0.9),
            ],
            fill="black", width=stroke,
        )
        draw.line(
            [
                point(0.75, 0.1), point(0.75, 0.25),
                point(0.25, 0.75), point(0.25, 0.9),
            ],
            fill="black", width=stroke,
        )
