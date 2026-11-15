"""Checks for the text-anchor rule (the package imports OpenCV, so this skips without it)."""

import pytest

pytest.importorskip("cv2")

from src.common.schemas import OcrBlock
from src.cv.symbols_v2.anchors import anchor_lines, distance_in_lines, near_anchor


def _blocks() -> list[OcrBlock]:
    return [
        OcrBlock(text="Example Labs 001", bbox=(60, 230, 300, 40), conf=0.9),
        OcrBlock(text="101 Example Road", bbox=(60, 300, 270, 40), conf=0.9),
        OcrBlock(text="LOT: TESTLOT001", bbox=(60, 470, 380, 40), conf=0.9),
        OcrBlock(text="EXP: 2027-05-16", bbox=(60, 550, 330, 40), conf=0.9),
    ]


def test_anchor_lines_come_from_text_only() -> None:
    """The EXP line anchors the expiry symbol and the line above the address anchors the manufacturer symbol."""
    anchors = anchor_lines(_blocks())
    assert anchors["expiry"] == [(60, 550, 330, 40)]
    assert anchors["manufacturer"] == [(60, 230, 300, 40)]
    assert anchor_lines([]) == {"manufacturer": [], "expiry": []}


def test_distance_and_nearness() -> None:
    """Distance is the gap in line heights; overlapping boxes are at distance zero."""
    line = (60, 550, 330, 40)
    assert distance_in_lines((100, 560, 20, 20), line) == 0.0
    assert distance_in_lines((430, 550, 50, 40), line) == 1.0
    anchors = anchor_lines(_blocks())
    assert near_anchor("expiry", (420, 540, 60, 60), anchors)
    assert not near_anchor("expiry", (900, 100, 60, 60), anchors)
    assert not near_anchor("manufacturer", (420, 540, 60, 60), anchors)
