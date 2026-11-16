"""Checks for the symbol style library and the styled label generator."""

import pytest

for _module in ("cv2", "PIL", "zxingcpp", "reportlab", "pypdf"):
    pytest.importorskip(_module)

import numpy as np
from PIL import Image

from src.gen.generate_styled import place_boxes
from src.gen.symbol_styles import (
    HELDOUT_DISTRACTORS,
    STYLES,
    SYMBOLS,
    TRAIN_DISTRACTORS,
    paste_symbol,
    render_mask,
    styles_in,
)


def test_splits_are_disjoint_and_complete() -> None:
    """Every style belongs to exactly one split, and held-out geometry is not used by any train style."""
    assert {style.split for style in STYLES} == {"train", "dev", "heldout"}
    assert len({style.id for style in STYLES}) == len(STYLES)
    seen = styles_in("train") + styles_in("dev")
    assert {s.factory for s in styles_in("heldout")} - {s.factory for s in seen}
    assert {s.glass for s in styles_in("heldout")} - {s.glass for s in seen}
    assert "badge" not in {s.mode for s in seen}
    assert not set(TRAIN_DISTRACTORS) & set(HELDOUT_DISTRACTORS)


@pytest.mark.parametrize("style", STYLES, ids=lambda style: style.id)
@pytest.mark.parametrize("name", [*SYMBOLS, *TRAIN_DISTRACTORS, *HELDOUT_DISTRACTORS])
def test_every_style_renders_visible_ink(style, name) -> None:
    """Each symbol in each style has ink, but is not a solid block."""
    mask = np.asarray(render_mask(name, style, 64, 64))
    ink = (mask < 128).mean()
    assert 0.05 < ink < 0.95


def test_paste_only_darkens_and_stays_in_box() -> None:
    """Printing a symbol never lightens pixels and leaves everything outside the box untouched."""
    image = Image.new("RGB", (200, 200), (200, 200, 200))
    before = np.asarray(image).copy()
    paste_symbol(image, "expiry", STYLES[0], (50, 50, 80, 80))
    after = np.asarray(image)
    assert (after <= before).all()
    outside = np.ones(before.shape[:2], bool)
    outside[50:130, 50:130] = False
    assert (after[outside] == before[outside]).all()
    assert (after[50:130, 50:130] < before[50:130, 50:130]).any()


def test_place_boxes_do_not_overlap_and_are_reproducible() -> None:
    """Two boxes are separated by a gap and the same seed gives the same boxes."""
    first = place_boxes(np.random.default_rng(3))
    again = place_boxes(np.random.default_rng(3))
    assert first == again
    a, b = first
    assert max(a[0] - (b[0] + b[2]), b[0] - (a[0] + a[2]), a[1] - (b[1] + b[3]), b[1] - (a[1] + a[3])) >= 12


def test_dev_geometry_is_novel_to_train_and_heldout() -> None:
    """Dev tuning styles include families (F5, H5) that no train or held-out style uses."""
    dev = {s.factory for s in styles_in("dev")} | {s.glass for s in styles_in("dev")}
    others = {s.factory for s in styles_in("train") + styles_in("heldout")}
    others |= {s.glass for s in styles_in("train") + styles_in("heldout")}
    assert {"F5", "H5"} <= dev
    assert not {"F5", "H5"} & others


def test_anchored_boxes_sit_right_of_their_text() -> None:
    """Anchored symbols are placed after the last printed character of their own line."""
    from src.gen.generate_styled import anchored_boxes

    printed = {"manufacturer": "Example Labs 001", "expiry": "EXP: 2027-05-16"}
    manufacturer, expiry = anchored_boxes(np.random.default_rng(1), printed, ["manufacturer", "expiry"])
    assert 200 < manufacturer[0] < 700 and 200 < expiry[0] < 700
    assert manufacturer[1] < expiry[1]  # manufacturer line is above the expiry line


def test_real_artwork_is_cropped_and_printed_inside_its_slot(tmp_path) -> None:
    """The artwork loader crops to visible ink and pasting keeps everything inside the slot."""
    from src.gen.generate_real_artwork import load_artwork, paste_artwork

    picture = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    picture.paste((0, 0, 0, 255), (20, 30, 60, 90))
    path = tmp_path / "art.png"
    picture.save(path)
    art, box = load_artwork(path)
    assert box == (20, 30, 60, 90) and art.shape == (60, 40)
    label = Image.new("RGB", (300, 300), "white")
    left, top, width, height = paste_artwork(label, art, (100, 100, 80, 80))
    assert 100 <= left and left + width <= 180 and 100 <= top and top + height <= 180
    assert np.asarray(label)[100:180, 100:180].min() < 50
    assert np.asarray(label)[:100].min() == 255
