"""Checks for the v2 symbol detector, its candidate finder, the evaluation harness and the held-out guard."""

import pytest

for _module in ("cv2", "PIL", "zxingcpp", "reportlab", "pypdf"):
    pytest.importorskip(_module)

import numpy as np
from PIL import Image

from src.common.schemas import SymbolDetection
from src.cv.symbol_eval import Item, box_iou, quad_box, rate, score_detections, tally
from src.cv.symbols_v2 import detect_symbols_v2
from src.cv.symbols_v2.candidates import prepare, propose
from src.cv.symbols_v2.detector import Config, Scored, decide, drop_overlaps, make_rule
from src.cv.symbols_v2.experiment import guard_heldout
from src.cv.symbols_v2.refs import build_bank, fill_holes, silhouette
from src.gen.symbol_styles import paste_symbol, styles_in

STYLE = styles_in("train")[0]


def _label_with(name: str, box: tuple[int, int, int, int] = (400, 300, 90, 90)) -> np.ndarray:
    """A plain white label with one printed pictogram."""
    image = Image.new("RGB", (800, 600), "white")
    paste_symbol(image, name, STYLE, box)
    return np.asarray(image)


def test_fill_holes_makes_outline_and_solid_equal() -> None:
    """A ring and a disc share a silhouette."""
    yy, xx = np.mgrid[:40, :40]
    disc = ((yy - 20) ** 2 + (xx - 20) ** 2 < 15**2).astype(np.uint8)
    ring = disc - ((yy - 20) ** 2 + (xx - 20) ** 2 < 11**2).astype(np.uint8)
    assert (fill_holes(ring) == disc).all()


def test_proposals_find_the_symbol_and_ignore_blank_paper() -> None:
    """One box overlaps the printed symbol; a blank label gives no candidate."""
    gray, factor = prepare(_label_with("manufacturer"))
    boxes = [candidate.box for candidate in propose(gray)]
    truth = (400 * factor, 300 * factor, 90 * factor, 90 * factor)
    assert any(box_iou(tuple(map(float, box)), truth) > 0.5 for box in boxes)
    blank, _ = prepare(np.full((600, 800, 3), 255, np.uint8))
    assert propose(blank) == []


@pytest.mark.parametrize("name", ["manufacturer", "expiry"])
def test_v2_detects_a_train_style_symbol_anywhere(name: str) -> None:
    """The detector finds a printed symbol with no template position and reports the right name and place."""
    found = detect_symbols_v2(_label_with(name))
    assert [item.name for item in found] == [name]
    assert box_iou(found[0].bbox, (400, 300, 90, 90)) > 0.5


def test_v2_reports_nothing_on_a_distractor_and_on_blank_paper() -> None:
    """A wrong pictogram and an empty label give no detection."""
    assert detect_symbols_v2(_label_with("caution")) == []
    assert detect_symbols_v2(np.full((600, 800, 3), 255, np.uint8)) == []


def test_bank_uses_only_train_and_dev_styles() -> None:
    """Held-out styles never appear in the reference bank, even when asked for by id."""
    bank = build_bank(("t1", "h1"))
    assert set(bank.style_ids) == {"t1"}


def test_silhouette_has_fixed_shape() -> None:
    """Any ink crop becomes a 64 by 64 binary silhouette."""
    sil = silhouette(np.ones((17, 29), np.uint8))
    assert sil.shape == (64, 64) and set(np.unique(sil)) <= {0, 1}


def test_rule_requires_margin_over_rival_class() -> None:
    """A close second class blocks a detection, a clear lead allows it."""
    rule = make_rule(Config(method="sil", sil_threshold=0.7, sil_margin=0.1))
    close = Scored((0, 0, 10, 10), {"sil": {"manufacturer": 0.8, "expiry": 0.3, "caution": 0.75}})
    clear = Scored((0, 0, 10, 10), {"sil": {"manufacturer": 0.8, "expiry": 0.3, "caution": 0.5}})
    assert decide([close], rule) == []
    assert [d.name for d in decide([clear], rule)] == ["manufacturer"]


def test_overlapping_names_keep_the_better_one() -> None:
    """Two names on the same box leave only the higher confidence."""
    boxes = [SymbolDetection(name="manufacturer", iso_ref="", conf=0.9, bbox=(0, 0, 50, 50)),
             SymbolDetection(name="expiry", iso_ref="", conf=0.8, bbox=(2, 2, 50, 50))]
    assert [d.name for d in drop_overlaps(boxes)] == ["manufacturer"]


def test_scoring_counts_matches_false_positives_and_mislocation() -> None:
    """Recall, false positives on absent symbols and wrong-place detections are counted separately."""
    item = Item("x", np.zeros((10, 10, 3), np.uint8), None, (100, 100),
                {"manufacturer": (10.0, 10.0, 40.0, 40.0)}, ["expiry"], {"case": "t", "condition": "clean",
                                                                         "style": "s", "split": ""})
    detections = [[SymbolDetection(name="manufacturer", iso_ref="", conf=1, bbox=(10, 10, 40, 40)),
                   SymbolDetection(name="expiry", iso_ref="", conf=1, bbox=(60, 60, 30, 30))]]
    record = score_detections([item], detections)[0]
    assert (record["matched"], record["false_positive"], record["mislocated"]) == (1, 1, 0)
    wrong_place = score_detections([item], [[SymbolDetection(name="manufacturer", iso_ref="", conf=1,
                                                             bbox=(60, 60, 30, 30))]])[0]
    assert (wrong_place["matched"], wrong_place["mislocated"]) == (0, 1)
    assert tally([record], ("case",))[("t",)]["expected"] == 1
    assert rate(0, 0) == "-" and rate(0, 10).startswith("0/10 (0.0%")


def test_quad_box_encloses_the_corners() -> None:
    """The axis-aligned box of a rotated quad covers all four corners."""
    assert quad_box([[1, 5], [4, 1], [7, 5], [4, 9]]) == (1.0, 1.0, 6.0, 8.0)


def test_heldout_guard_refuses_and_logs(tmp_path, monkeypatch) -> None:
    """Held-out data need an explicit flag, and every allowed use is written to the log."""
    from src.cv.symbols_v2 import experiment

    monkeypatch.setattr(experiment, "HELDOUT_LOG", tmp_path / "log.jsonl")
    with pytest.raises(SystemExit):
        guard_heldout(tmp_path / "styled_heldout", False, "x")
    guard_heldout(tmp_path / "styled_dev", False, "x")
    guard_heldout(tmp_path / "styled_heldout", True, "final run")
    assert "final run" in (tmp_path / "log.jsonl").read_text(encoding="utf-8")
