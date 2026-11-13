"""Positive, negative and scale checks for synthetic pictogram matching."""

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

from src.cv.symbols import build_templates, detect_symbols
from src.gen.smoke_label import build_label


def test_references_and_matching(tmp_path: Path) -> None:
    """Rebuild identical references and find both symbols on actual generated artwork."""
    refs = tmp_path / "refs"
    paths = build_templates(refs)
    first = {name: path.read_bytes() for name, path in paths.items()}
    assert {name: path.read_bytes() for name, path in build_templates(refs).items()} == first
    label = build_label(tmp_path / "label")
    truth = json.loads(Path(label["ground_truth"]).read_text())
    with Image.open(label["image"]) as photo:
        image = np.asarray(photo.convert("RGB"))
    for scale in (0.75, 1.0, 1.25):
        resized = cv2.resize(image, None, fx=scale, fy=scale)
        results = detect_symbols(resized, reference_dir=refs)
        found = {result.name: result for result in results}
        assert set(found) == {"manufacturer", "expiry"}
        assert all(0.75 <= result.conf <= 1 and result.iso_ref == "" for result in results)
        fx, fy = resized.shape[1] / image.shape[1], resized.shape[0] / image.shape[0]
        for expected in truth["symbols"]:
            actual = found[expected["name"]].bbox
            x, y, width, height = expected["bbox_px_xywh"]
            assert np.allclose(actual, (x * fx, y * fy, width * fx, height * fy), atol=3)


def test_absent_symbols(tmp_path: Path) -> None:
    """Blank slots and a wrong symbol in another slot must not imply presence."""
    refs = tmp_path / "refs"
    build_templates(refs)
    label = build_label(tmp_path / "label")
    truth = json.loads(Path(label["ground_truth"]).read_text())
    with Image.open(label["image"]) as photo:
        image = np.array(photo.convert("RGB"))
    for symbol in truth["symbols"]:
        x, y, w, h = symbol["bbox_px_xywh"]
        image[y : y + h, x : x + w] = 255
    assert detect_symbols(image, reference_dir=refs) == []
    assert detect_symbols(np.full_like(image, 255), reference_dir=refs) == []

    with Image.open(label["image"]) as photo:
        swapped = np.array(photo.convert("RGB"))
    first, second = truth["symbols"]
    ax, ay, aw, ah = first["bbox_px_xywh"]
    bx, by, bw, bh = second["bbox_px_xywh"]
    first_pixels = swapped[ay : ay + ah, ax : ax + aw].copy()
    second_pixels = swapped[by : by + bh, bx : bx + bw].copy()
    swapped[ay : ay + ah, ax : ax + aw] = second_pixels
    swapped[by : by + bh, bx : bx + bw] = first_pixels
    assert detect_symbols(swapped, reference_dir=refs) == []


def test_invalid_configuration(tmp_path: Path) -> None:
    """Reject bad thresholds, scales and constant reference artwork explicitly."""
    refs = tmp_path / "refs"
    build_templates(refs)
    image = np.full((709, 1181, 3), 255, dtype=np.uint8)
    for threshold in (-1, 1.1, np.nan):
        with pytest.raises(ValueError):
            detect_symbols(image, threshold=threshold)
    with pytest.raises(ValueError):
        detect_symbols(image, scales=())
    Image.new("L", (94, 94), 255).save(refs / "test_manufacturer.png")
    with pytest.raises(ValueError, match="nonconstant"):
        detect_symbols(image, reference_dir=refs)
