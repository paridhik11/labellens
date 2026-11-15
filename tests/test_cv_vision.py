"""Tests for the CV fixes that need OpenCV, Pillow and zxing-cpp.

The whole file is skipped when those libraries are not installed, so the
repo's main CI command (``pytest -q -m "not slow"``) passes without the CV
dependencies. Tests that load the OCR models are also marked slow.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
pytest.importorskip("PIL")
pytest.importorskip("zxingcpp")

from PIL import Image  # noqa: E402

from src.cv.barcode_blind import (  # noqa: E402
    decode_barcode_slot_enhanced,
    decode_barcodes_blind,
    locate_barcode_candidates,
    wiener_deblur,
)
from src.cv.ocr import equalise_contrast, padded_crops, vote_text  # noqa: E402
from src.cv.preprocess import find_label_corners, find_label_corners_fallback, rectify_label  # noqa: E402
from src.cv.symbols import detect_symbols_blind  # noqa: E402
from src.gen.augment import augment_label, augment_label_detailed  # noqa: E402
from src.gen.generate_dataset import generate_dataset  # noqa: E402
from src.gen.generate_negatives import CASES, generate_negatives  # noqa: E402
from src.gen.smoke_label import build_label  # noqa: E402


@pytest.fixture(scope="module")
def label(tmp_path_factory: pytest.TempPathFactory) -> tuple[Image.Image, dict]:
    """Render one clean test label and return it with its ground truth."""
    folder = tmp_path_factory.mktemp("label")
    paths = build_label(folder, label_id="test_label_901")
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    with Image.open(paths["image"]) as image:
        return image.convert("RGB"), truth


def test_default_conditions_unchanged_by_new_ones(label: tuple[Image.Image, dict]) -> None:
    """hard_original and very_hard share the hard geometry and leave hard itself untouched."""
    image, _ = label
    hard, matrix, corners = augment_label(image, "hard", 7)
    original, matrix_original, corners_original, details = augment_label_detailed(image, "hard_original", 7)
    very, matrix_very, _, very_details = augment_label_detailed(image, "very_hard", 7)
    assert np.allclose(matrix, matrix_original) and np.allclose(matrix, matrix_very)
    assert corners == corners_original
    assert details["noise_sigma"] == 8.0 and 1.0 <= details["blur_sigma"] <= 1.8
    assert very_details["noise_sigma"] == 6.0
    assert 1 <= len(very_details["occluders"]) <= 2 and 1 <= len(very_details["glare"]) <= 2
    assert np.asarray(original).shape == np.asarray(hard).shape
    assert not np.array_equal(np.asarray(very), np.asarray(hard))
    # Same seed, same output.
    again, _, _ = augment_label(image, "hard", 7)
    assert np.array_equal(np.asarray(again), np.asarray(hard))
    with pytest.raises(ValueError):
        augment_label(image, "impossible", 7)  # type: ignore[arg-type]


def test_generate_dataset_extra_conditions(tmp_path: Path) -> None:
    default = generate_dataset(tmp_path / "default", seed=5, labels_per_condition=1)
    assert "condition_names" not in default and default["total_images"] == 3
    extra = generate_dataset(
        tmp_path / "extra", seed=5, labels_per_condition=1, conditions=("hard", "hard_original", "very_hard")
    )
    assert extra["condition_names"] == ["hard", "hard_original", "very_hard"]
    name = "test_label_001_hard"
    assert (tmp_path / "default/hard" / f"{name}.png").read_bytes() == (
        tmp_path / "extra/hard" / f"{name}.png"
    ).read_bytes()
    truth = json.loads((tmp_path / "extra/very_hard/test_label_001_very_hard.json").read_text(encoding="utf-8"))
    hard_truth = json.loads((tmp_path / "extra/hard" / f"{name}.json").read_text(encoding="utf-8"))
    assert truth["augmentation_seed"] == hard_truth["augmentation_seed"]
    assert "occluders" in truth["augmentation_details"] and "augmentation_details" not in hard_truth
    with pytest.raises(ValueError):
        generate_dataset(tmp_path / "bad", conditions=("clean", "clean"))


def test_wiener_deblur_sharpens_edges() -> None:
    stripes = np.tile(np.repeat(np.array([0, 255], dtype=np.uint8), 4), 12)
    pattern = np.pad(np.tile(stripes, (40, 1)), 16, constant_values=255)
    blurred = cv2.GaussianBlur(pattern, (0, 0), 1.2)
    restored = wiener_deblur(blurred, 1.2)
    error_before = np.abs(blurred.astype(float) - pattern).mean()
    error_after = np.abs(restored.astype(float) - pattern).mean()
    assert error_after < 0.7 * error_before
    with pytest.raises(ValueError):
        wiener_deblur(blurred, 0)
    with pytest.raises(ValueError):
        wiener_deblur(blurred.astype(np.float32), 1.0)


def test_blind_decode_recovers_blurred_barcode(tmp_path: Path) -> None:
    """A photo that plain decoding cannot read is decoded without the slot position.

    The longer lot and serial values of the generated datasets make zxing-cpp
    choose the 8 by 96 module strip symbol with 3 pixel modules, the case that
    blur breaks.
    """
    import zxingcpp

    paths = build_label(
        tmp_path, label_id="test_label_902", barcode_ais={"10": "TESTLOT0016232", "21": "TESTSER0011234"}
    )
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    with Image.open(paths["image"]) as opened:
        image = opened.convert("RGB")
    pixels = None
    for seed in range(1, 30):
        photo, _, _ = augment_label(image, "hard_original", seed)
        candidate = np.asarray(photo)
        if not zxingcpp.read_barcodes(cv2.cvtColor(candidate, cv2.COLOR_RGB2GRAY)):
            pixels = candidate
            break
    assert pixels is not None, "expected at least one seed that plain decoding cannot read"
    results, warnings, attempt = decode_barcodes_blind(pixels)
    assert len(results) == 1 and results[0].parsed == truth["barcode_ais"]
    assert attempt is not None and attempt != "plain" and warnings == []
    x, y, w, h = results[0].bbox
    assert 0 <= x < x + w <= pixels.shape[1] and 0 <= y < y + h <= pixels.shape[0]


def test_blind_decode_never_invents_a_barcode() -> None:
    rng = np.random.default_rng(0)
    noise = rng.integers(0, 255, size=(240, 320, 3), dtype=np.uint8)
    results, warnings, attempt = decode_barcodes_blind(noise, whole_image_fallback=False)
    assert results == [] and attempt is None and warnings[0].startswith("BARCODE_NOT_DECODED")
    blank = np.full((240, 320, 3), 255, dtype=np.uint8)
    assert decode_barcodes_blind(blank)[0] == []


def test_candidates_include_the_barcode(label: tuple[Image.Image, dict]) -> None:
    image, truth = label
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    x, y, w, h = truth["slot_boxes_px_xywh"]["udi"]
    centre = (float(x + w / 2), float(y + h / 2))
    candidates = locate_barcode_candidates(gray)
    assert any(cv2.pointPolygonTest(box, centre, False) >= 0 for box in candidates)
    with pytest.raises(ValueError):
        locate_barcode_candidates(np.asarray(image))


def test_enhanced_slot_decode_uses_template_slot(label: tuple[Image.Image, dict]) -> None:
    image, truth = label
    blurred = cv2.GaussianBlur(np.asarray(image), (0, 0), 1.5)
    results, _, attempt = decode_barcode_slot_enhanced(blurred)
    assert len(results) == 1 and results[0].parsed == truth["barcode_ais"] and attempt is not None


def test_fallback_corners_survive_occlusion() -> None:
    """A dark bar across one edge defeats the strict detector but not the fallback."""
    truth = np.array([[200, 150], [900, 190], [860, 620], [170, 560]], dtype=np.float32)
    image = np.full((800, 1100, 3), 90, dtype=np.uint8)
    cv2.fillConvexPoly(image, truth.astype(np.int32), (250, 250, 250), lineType=cv2.LINE_AA)
    cv2.rectangle(image, (500, 120), (580, 300), (40, 40, 40), -1)
    assert find_label_corners(image) is None
    corners = find_label_corners_fallback(image)
    assert corners is not None
    assert np.linalg.norm(corners - truth, axis=1).max() <= 6
    rectified, _ = rectify_label(image, corners)
    assert rectified.shape[0] > 350 and rectified.shape[1] > 600
    assert find_label_corners_fallback(np.full((200, 300, 3), 255, dtype=np.uint8)) is None


def test_padded_crops_and_vote() -> None:
    image = np.full((100, 300, 3), 255, dtype=np.uint8)
    box = np.array([[50, 40], [250, 40], [250, 60], [50, 60]], dtype=np.float32)
    assert padded_crops(image, [box], 0.0)[0].shape[:2] == (20, 200)
    assert padded_crops(image, [box], 0.5)[0].shape[:2] == (40, 220)
    assert vote_text([("A B", 0.9), ("AB", 0.99), ("A B", 0.7)]) == ("A B", pytest.approx(0.8 * 2 / 3))
    assert vote_text([("AB", 0.6), ("A B", 0.9)])[0] == "A B"
    with pytest.raises(ValueError):
        vote_text([])
    equalised = equalise_contrast(image)
    assert equalised.shape == image.shape and equalised.dtype == np.uint8


def test_blind_symbols_found_without_slots(label: tuple[Image.Image, dict]) -> None:
    """Both pictograms are found on the whole label, and not on a label without them."""
    image, truth = label
    pixels = np.asarray(image)
    detections = {item.name: item for item in detect_symbols_blind(pixels)}
    assert set(detections) == {"manufacturer", "expiry"}
    for symbol in truth["symbols"]:
        x, y, w, h = symbol["bbox_px_xywh"]
        dx, dy, dw, dh = detections[symbol["name"]].bbox
        assert abs(dx - x) <= 0.25 * w and abs(dy - y) <= 0.25 * h and 0.7 * w <= dw <= 1.3 * w
    erased = pixels.copy()
    for symbol in truth["symbols"]:
        x, y, w, h = symbol["bbox_px_xywh"]
        erased[y - 4:y + h + 4, x - 4:x + w + 4] = 255
    assert detect_symbols_blind(erased) == []


def test_generate_negatives_structure(tmp_path: Path) -> None:
    manifest = generate_negatives(tmp_path / "neg", seed=9, labels_per_case=1, conditions=("moderate",))
    assert manifest["total_images"] == len(CASES)
    by_case = {}
    for entry in manifest["files"]:
        truth = json.loads((tmp_path / "neg" / entry["ground_truth"]).read_text(encoding="utf-8"))
        assert truth["test_data"] is True and (tmp_path / "neg" / entry["image"]).is_file()
        by_case[truth["case"]] = truth
    assert [s["name"] for s in by_case["missing_expiry"]["present_symbols"]] == ["manufacturer"]
    assert [s["name"] for s in by_case["wrong_symbol"]["distractor_symbols"]] == ["caution"]
    assert by_case["wrong_barcode"]["print_matches_barcode"] is False
    printed_lot = by_case["wrong_barcode"]["fields"]["lot"].removeprefix("LOT: ")
    assert printed_lot != by_case["wrong_barcode"]["barcode_ais"]["10"]
    assert by_case["wrong_barcode"]["barcode_ais"]["01"] == "00000000000000"
    assert {s["style"] for s in by_case["alt_style"]["present_symbols"]} == {"alt"}
    assert by_case["small_symbols"]["present_symbols"][0]["scale"] == 0.6
    with pytest.raises(ValueError):
        generate_negatives(tmp_path / "neg", seed=9, labels_per_case=1)


@pytest.mark.slow
def test_padded_ocr_reads_clean_label_exactly(label: tuple[Image.Image, dict]) -> None:
    """The clean label, which the old reader got wrong, is read without a single edit."""
    pytest.importorskip("rapidocr_onnxruntime")
    from src.cv.ocr import read_text_default

    image, truth = label
    texts = {block.text for block in read_text_default(np.asarray(image))}
    for field in ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry"):
        assert truth["fields"][field] in texts


@pytest.mark.slow
def test_blind_extraction_matches_template_extraction(label: tuple[Image.Image, dict], tmp_path: Path) -> None:
    """Blind mode names all six fields and decodes the barcode without the template."""
    pytest.importorskip("rapidocr_onnxruntime")
    from src.common.schemas import LabelExtraction
    from src.cv.extract import extract_label, extract_label_modes

    image, truth = label
    photo, _, _ = augment_label(image, "moderate", 11)
    path = tmp_path / "test_photo.png"
    photo.save(path)
    outputs = extract_label_modes(path, modes=("template", "blind"), postcorrect=True)
    for mode in ("template", "blind"):
        extraction, details = outputs[mode]
        assert isinstance(extraction, LabelExtraction)
        assert extraction.fields == truth["fields"]
        assert [item.parsed for item in extraction.barcodes] == [truth["barcode_ais"]]
        assert {symbol.name for symbol in extraction.symbols} == {"manufacturer", "expiry"}
        assert details["corners"] is not None
    assert "BLIND_MODE" in outputs["blind"][0].warnings[0]
    assert extract_label(path, mode="blind", postcorrect=True) == outputs["blind"][0]
