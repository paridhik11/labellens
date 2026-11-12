"""Checks for synthetic pictograms and their ground truth."""

import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.gen.smoke_label import build_label
from src.gen.symbols import draw_symbol


@pytest.mark.parametrize("name", ["manufacturer", "expiry"])
def test_symbol_stays_inside_box(name: str) -> None:
    """Check that a pictogram is visible and stays inside its slot."""
    image = Image.new("RGB", (120, 120), "white")
    draw_symbol(ImageDraw.Draw(image), name, (20, 20, 80, 80))
    ink = image.convert("L").point(lambda value: 255 - value).getbbox()
    assert ink is not None
    assert 20 <= ink[0] < ink[2] <= 100
    assert 20 <= ink[1] < ink[3] <= 100


def test_unknown_symbol() -> None:
    """Reject unsupported names instead of silently drawing nothing."""
    image = Image.new("RGB", (100, 100), "white")
    with pytest.raises(ValueError, match="Unknown symbol"):
        draw_symbol(ImageDraw.Draw(image), "unknown", (0, 0, 80, 80))


def test_symbol_ground_truth(tmp_path: Path) -> None:
    """Check that generated metadata records both symbol positions."""
    paths = build_label(tmp_path)
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    assert {symbol["name"] for symbol in truth["symbols"]} == {
        "manufacturer", "expiry"
    }
    for symbol in truth["symbols"]:
        field = f"{symbol['name']}_symbol"
        assert symbol["bbox_px_xywh"] == truth["slot_boxes_px_xywh"][field]
        assert symbol["synthetic_pictogram"] is True
