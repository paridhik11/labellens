"""CV4b: the cooperative time budget and its OCR cut-off (the name-check test stays on the cv4b branch)."""
from __future__ import annotations

import time

import pytest

from src.common.schemas import OcrBlock
from src.cv.budget import Deadline, expired


def test_deadline_semantics() -> None:
    """No budget never expires; a zero budget expires at once; a stage is a share of the same start."""
    assert not Deadline(None).expired() and not expired(None)
    assert Deadline(0).expired() and expired(Deadline(0))
    parent = Deadline(100.0)
    assert not parent.expired() and parent.stage(0.8).seconds == pytest.approx(80.0)
    assert Deadline(None).stage(0.5).seconds is None
    old = Deadline(1.0, start=time.monotonic()-5)
    assert old.expired() and old.elapsed() >= 5


def test_read_photo_stops_after_the_upright_turn_when_expired() -> None:
    """An expired budget still reads the upright view once, skips other turns and crops, and says incomplete."""
    np = pytest.importorskip('numpy')
    pytest.importorskip('cv2')
    from src.cv.photo_ocr import read_photo

    calls: list[tuple[int, int]] = []

    def reader(image):  # one call per OCR pass
        calls.append(image.shape[:2])
        return [OcrBlock(text='ACME 17', bbox=(1, 1, 40, 10), conf=0.95)]

    image = np.full((200, 300, 3), 255, dtype=np.uint8)
    short = read_photo(image, reader=reader, deadline=Deadline(0))
    assert len(calls) == 1 and short.complete is False and short.blocks[0].text == 'ACME 17'
    calls.clear()
    full = read_photo(image, reader=reader)  # no deadline: 4 turns and 4 crops, as before
    assert len(calls) == 8 and full.complete is True


def test_budget_options_are_off_by_default_everywhere() -> None:
    """max_side, budget_s and search_side default to None on every entry point, and no caller in src passes them."""
    import inspect
    import pathlib

    pytest.importorskip('numpy')
    from src.cv import extract

    for function in (extract.extract_label, extract.extract_label_modes):
        parameters = inspect.signature(function).parameters
        for name in ('max_side', 'budget_s', 'search_side'):
            assert parameters[name].default is None, (function.__name__, name)
    callers = [p for p in pathlib.Path('src').rglob('*.py')
               if p.parts[:2] != ('src', 'cv') and p.name != 'public_scan.py'
               and any(k in p.read_text(encoding='utf-8') for k in ('budget_s=', 'max_side=', 'search_side='))]
    assert callers == []
