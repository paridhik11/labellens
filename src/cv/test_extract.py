"""Checks for template field mapping and integrated original-image extraction."""

import json
import shutil
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
from PIL import Image

from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock
from src.cv import extract
from src.gen.generate_dataset import generate_dataset


@pytest.fixture
def blocks() -> list[OcrBlock]:
    """Provide known corrected-space observations, including header and barcode noise."""
    return [
        OcrBlock(text="TEST DATA | DRAFT", bbox=(50, 30, 400, 40), conf=0.99),
        OcrBlock(text=" OCR PRODUCT ", bbox=(50, 120, 550, 50), conf=0.9),
        OcrBlock(text="OCR Manufacturer", bbox=(50, 200, 550, 40), conf=0.95),
        OcrBlock(text="OCR Address", bbox=(50, 260, 550, 40), conf=0.95),
        OcrBlock(text="REF: OCR-MODEL", bbox=(50, 330, 550, 40), conf=0.95),
        OcrBlock(text="LOT: OCR-ERROR", bbox=(50, 400, 550, 40), conf=0.6),
        OcrBlock(text="EXP: OCR-ERROR", bbox=(50, 470, 550, 40), conf=0.95),
        OcrBlock(text="barcode noise", bbox=(750, 220, 200, 20), conf=0.1),
    ]


@pytest.fixture
def template() -> dict[str, Any]:
    """Read only the fixed layout used by the single-family extraction baseline."""
    return json.loads(extract.TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def pipeline_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, blocks: list[OcrBlock]) -> Path:
    """Isolate pipeline decisions with a known crop and mocked engine observations."""
    path = tmp_path / "test_pipeline.png"
    Image.new("RGB", (1400, 800), "white").save(path)
    corners = np.array([[50, 70], [1050, 70], [1050, 670], [50, 670]], dtype=np.float32)
    monkeypatch.setattr(extract, "find_label_corners", lambda image: corners)
    monkeypatch.setattr(extract, "read_text", lambda image: blocks)
    original_barcode = BarcodeResult(
        type="Data Matrix", raw="original raw data", bbox=(900, 300, 200, 30),
        parsed={"10": "BARCODELOT", "17": "271231"},
    )
    monkeypatch.setattr(extract, "decode_barcodes", lambda image: ([original_barcode], []))
    return path


def test_map_fields_preserves_observations(blocks: list[OcrBlock], template: dict[str, Any]) -> None:
    """Assign text by position, retaining whitespace and excluding unrelated regions."""
    fields, warnings = extract.map_fields(blocks, (1001, 601), template)
    assert warnings == []
    assert fields == {
        "product_name": " OCR PRODUCT ", "manufacturer": "OCR Manufacturer",
        "manufacturer_address": "OCR Address", "model": "REF: OCR-MODEL",
        "lot": "LOT: OCR-ERROR", "expiry": "EXP: OCR-ERROR",
    }
    assert "TEST DATA | DRAFT" not in fields.values()
    assert "barcode noise" not in fields.values()


def test_missing_and_ambiguous_fields(blocks: list[OcrBlock], template: dict[str, Any]) -> None:
    """Leave absent and ambiguous fields unset instead of selecting a candidate."""
    candidates = [block for block in blocks if block.text != "OCR Manufacturer"]
    candidates.append(OcrBlock(text="SECOND PRODUCT", bbox=(60, 125, 400, 30), conf=0.99))
    fields, warnings = extract.map_fields(candidates, (1001, 601), template)
    assert "manufacturer" not in fields and "product_name" not in fields
    assert "FIELD_MISSING: manufacturer" in warnings
    assert "FIELD_AMBIGUOUS: product_name has 2 candidate blocks" in warnings


def test_overlapping_slots_are_ambiguous() -> None:
    """A block matching two slots must not populate either one."""
    template = {
        "size_mm": {"w": 100, "h": 60},
        "slots": [
            {"type": "text", "field": field, "bbox_mm": [5, 12, 60, 6]}
            for field in ("first", "second")
        ],
    }
    blocks = [OcrBlock(text="AMBIGUOUS", bbox=(50, 120, 550, 50))]
    fields, warnings = extract.map_fields(blocks, (1001, 601), template)
    assert fields == {}
    assert any("matches multiple slots" in warning for warning in warnings)


def test_invalid_mapping_dimensions(template: dict[str, Any]) -> None:
    """Reject dimensions that cannot support normalized pixel coordinates."""
    with pytest.raises(ValueError, match="two pixels"):
        extract.map_fields([], (1, 100), template)


@pytest.mark.parametrize(
    "box, matrix, expected",
    [
        ((10, 20, 30, 40), [[1, 0, 5], [0, 1, 7], [0, 0, 1]], (15, 27, 30, 40)),
        ((0, 0, 2, 2), [[2, 0, 2], [0, 3, 6], [0.5, 0, 1]], (2, 3, 1, 9)),
        ((10, 20, 30, 40), [[0, -1, 50], [1, 0, 10], [0, 0, 1]], (0, 20, 30, 30)),
    ],
)
def test_project_box(
    box: tuple[float, float, float, float], matrix: list[list[float]], expected: tuple[float, ...]
) -> None:
    """Check translation, all-corner perspective enclosure, rotation and clipping."""
    assert np.allclose(extract.project_box(box, np.asarray(matrix), (100, 100)), expected)


@pytest.mark.parametrize(
    "box, matrix, image_size",
    [
        ((0, 0, 0, 10), np.eye(3), (100, 100)),
        ((0, 0, -1, 10), np.eye(3), (100, 100)),
        ((np.nan, 0, 10, 10), np.eye(3), (100, 100)),
        ((200, 200, 10, 10), np.eye(3), (100, 100)),
        ((0, 0, 10, 10), np.zeros((3, 3)), (100, 100)),
        ((0, 0, 10, 10), np.array([[1, 0, 0], [1, 0, 0], [0, 0, 1]]), (100, 100)),
        ((0, 0, 20, 10), np.array([[1, 0, 0], [0, 1, 0], [1, 0, -10]]), (100, 100)),
        ((0, 0, 10, 10), np.eye(2), (100, 100)),
        ((0, 0, 10, 10), np.eye(3), (0, 100)),
    ],
)
def test_invalid_box_projection(
    box: tuple[float, float, float, float], matrix: np.ndarray, image_size: tuple[int, int]
) -> None:
    """Reject invalid or unprojectable geometry instead of creating a false box."""
    with pytest.raises(ValueError):
        extract.project_box(box, matrix, image_size)


def test_blur_score() -> None:
    """A smoothed checkerboard has lower edge variance than the sharp source."""
    pattern = (np.indices((100, 100)).sum(axis=0) % 2 * 255).astype(np.uint8)
    sharp = np.repeat(pattern[..., None], 3, axis=2)
    blurred = cv2.GaussianBlur(sharp, (9, 9), 3)
    assert extract.blur_score(sharp) > extract.blur_score(blurred)
    assert extract.blur_score(np.full((100, 100, 3), 255, np.uint8)) == 0
    with pytest.raises(ValueError, match="uint8 RGB"):
        extract.blur_score(pattern)


def test_pipeline_coordinates_and_fields(pipeline_image: Path, blocks: list[OcrBlock]) -> None:
    """Keep original barcode positions and project corrected OCR boxes back once."""
    result = extract.extract_label(pipeline_image, blur_threshold=0)
    assert isinstance(result, LabelExtraction)
    assert result.label_id == "test_pipeline"
    assert result.barcodes[0].bbox == (900, 300, 200, 30)
    assert result.fields["lot"] == "LOT: OCR-ERROR"
    assert result.fields["expiry"] == "EXP: OCR-ERROR"
    assert result.barcodes[0].parsed["10"] == "BARCODELOT"
    assert len(result.ocr_blocks) == len(blocks)
    for original, projected in zip(blocks, result.ocr_blocks, strict=True):
        x, y, width, height = original.bbox
        assert np.allclose(projected.bbox, (x + 50, y + 70, width, height))
        assert projected.text == original.text and projected.conf == original.conf
    assert sum(warning.startswith("LOW_OCR_CONFIDENCE:") for warning in result.warnings) == 2
    assert any(warning.startswith("SYMBOL_NOT_DETECTED:") for warning in result.warnings)
    assert not any(warning.startswith("BLUR_SUSPECTED:") for warning in result.warnings)
    assert LabelExtraction.model_validate_json(result.model_dump_json()) == result


def test_original_barcode_is_not_retried(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Do not replace a successful original decode with a degraded corrected one."""
    shapes = []

    def decode(image: np.ndarray) -> tuple[list[BarcodeResult], list[str]]:
        """Record decoder inputs and fail if the original is decoded twice."""
        shapes.append(image.shape)
        assert len(shapes) == 1
        return [BarcodeResult(type="Data Matrix", raw="original", bbox=(900, 300, 200, 30))], []

    monkeypatch.setattr(extract, "decode_barcodes", decode)
    assert extract.extract_label(pipeline_image).barcodes[0].raw == "original"
    assert shapes == [(800, 1400, 3)]


def test_corrected_barcode_retry(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Retry only after no original decode and project the recovered barcode box."""
    shapes = []

    def decode(image: np.ndarray) -> tuple[list[BarcodeResult], list[str]]:
        """Simulate one successful barcode recovery after perspective correction."""
        shapes.append(image.shape)
        if len(shapes) == 1:
            return [], ["BARCODE_NOT_DECODED: no barcode could be decoded"]
        return [BarcodeResult(type="Data Matrix", raw="recovered", bbox=(750, 220, 200, 20))], []

    monkeypatch.setattr(extract, "decode_barcodes", decode)
    result = extract.extract_label(pipeline_image)
    assert shapes == [(800, 1400, 3), (601, 1001, 3)]
    assert np.allclose(result.barcodes[0].bbox, (800, 290, 200, 20))
    assert result.barcodes[0].raw == "recovered"
    assert "BARCODE_DECODED_AFTER_RECTIFICATION" in result.warnings
    assert not any(warning.startswith("BARCODE_NOT_DECODED:") for warning in result.warnings)


def test_missing_barcode(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Retain OCR fields when both barcode attempts fail, with one final warning."""
    monkeypatch.setattr(extract, "decode_barcodes", lambda image: ([], ["BARCODE_NOT_DECODED: test"]))
    result = extract.extract_label(pipeline_image)
    assert result.barcodes == []
    assert result.fields["manufacturer"] == "OCR Manufacturer"
    assert result.warnings.count("BARCODE_NOT_DECODED: test") == 1


def test_missing_boundary(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep original barcodes but skip template field guesses when no label is found."""
    monkeypatch.setattr(extract, "find_label_corners", lambda image: None)
    monkeypatch.setattr(extract, "read_text", lambda image: pytest.fail("No corrected label is available"))
    result = extract.extract_label(pipeline_image)
    assert result.fields == {} and result.ocr_blocks == []
    assert result.barcodes[0].bbox == (900, 300, 200, 30)
    assert any(warning.startswith("LABEL_NOT_FOUND:") for warning in result.warnings)
    assert any(warning.startswith("FIELD_MAPPING_SKIPPED:") for warning in result.warnings)


def test_ocr_engine_failure(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Preserve available barcodes and the OCR error reason without fabricated text."""
    def fail(image: np.ndarray) -> None:
        """Simulate an OCR inference failure."""
        raise RuntimeError("test OCR engine failure")

    monkeypatch.setattr(extract, "read_text", fail)
    result = extract.extract_label(pipeline_image)
    assert result.fields == {} and result.ocr_blocks == []
    assert result.barcodes
    assert "OCR_FAILED: RuntimeError: test OCR engine failure" in result.warnings


def test_barcode_engine_failure(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep text extraction available and report the decoder exception explicitly."""
    def fail(image: np.ndarray) -> None:
        """Simulate a barcode inference failure."""
        raise RuntimeError("test barcode engine failure")

    monkeypatch.setattr(extract, "decode_barcodes", fail)
    result = extract.extract_label(pipeline_image)
    assert result.barcodes == [] and result.fields
    assert "BARCODE_ENGINE_FAILED: RuntimeError: test barcode engine failure" in result.warnings


def test_multiple_barcodes(pipeline_image: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep multiple symbols with a warning instead of selecting an identifier."""
    values = [BarcodeResult(type="Data Matrix", raw=value) for value in ("first", "second")]
    monkeypatch.setattr(extract, "decode_barcodes", lambda image: (values, []))
    result = extract.extract_label(pipeline_image)
    assert [item.raw for item in result.barcodes] == ["first", "second"]
    assert any(warning.startswith("MULTIPLE_BARCODES:") for warning in result.warnings)


def test_provisional_warning_settings(pipeline_image: Path) -> None:
    """Expose configurable warning thresholds without presenting them as accuracy."""
    result = extract.extract_label(pipeline_image, min_confidence=0.5, blur_threshold=1)
    assert sum(warning.startswith("LOW_OCR_CONFIDENCE:") for warning in result.warnings) == 1
    assert any(warning.startswith("BLUR_SUSPECTED:") for warning in result.warnings)


@pytest.mark.parametrize("confidence, threshold", [(-1, 100), (1.1, 100), (np.nan, 100), (0.8, -1), (0.8, np.inf)])
def test_invalid_settings(tmp_path: Path, confidence: float, threshold: float) -> None:
    """Reject invalid thresholds before reading an input file."""
    with pytest.raises(ValueError):
        extract.extract_label(tmp_path / "missing.png", min_confidence=confidence, blur_threshold=threshold)


@pytest.fixture(scope="module")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate one actual image per condition for full-pipeline smoke tests."""
    folder = tmp_path_factory.mktemp("extraction")
    generate_dataset(folder, seed=42, labels_per_condition=1)
    return folder


@pytest.mark.parametrize("condition", ["clean", "moderate", "hard"])
def test_real_extraction_without_sidecar(dataset: Path, tmp_path: Path, condition: str) -> None:
    """Run actual engines on an image alone and verify original-space field positions."""
    original = dataset / condition / f"test_label_001_{condition}.png"
    copied = tmp_path / original.name
    shutil.copyfile(original, copied)
    assert not copied.with_suffix(".json").exists()
    result = extract.extract_label(copied)
    assert isinstance(result, LabelExtraction)
    assert LabelExtraction.model_validate_json(result.model_dump_json()) == result
    truth = json.loads(original.with_suffix(".json").read_text(encoding="utf-8"))
    assert set(result.fields) == set(truth["fields"])
    assert result.fields["manufacturer"] == "Example Labs 001"
    assert {symbol.name for symbol in result.symbols} == {"manufacturer", "expiry"}
    width, height = truth["image_size_px"]
    for block in [*result.ocr_blocks, *result.barcodes]:
        if block.bbox is not None:
            x, y, w, h = block.bbox
            assert 0 <= x < x + w <= width
            assert 0 <= y < y + h <= height
    for field, text in result.fields.items():
        matches = [block for block in result.ocr_blocks if block.text == text]
        assert len(matches) == 1
        x, y, w, h = matches[0].bbox
        quad = np.asarray(truth["slot_quads_px"][field], dtype=np.float32)
        assert cv2.pointPolygonTest(quad, (x + w / 2, y + h / 2), measureDist=True) >= -10
    if condition in {"clean", "moderate"}:
        assert len(result.barcodes) == 1
    for item in result.barcodes:
        assert item.parsed == truth["barcode_ais"]


def test_real_blank_image(tmp_path: Path) -> None:
    """An actual blank image returns warnings and no fictional fields or symbols."""
    path = tmp_path / "test_blank.png"
    Image.new("RGB", (300, 200), "white").save(path)
    result = extract.extract_label(path)
    assert result.fields == {} and result.barcodes == [] and result.ocr_blocks == [] and result.symbols == []
    assert any(warning.startswith("LABEL_NOT_FOUND:") for warning in result.warnings)
    assert any(warning.startswith("BARCODE_NOT_DECODED:") for warning in result.warnings)


def test_cli(pipeline_image: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Print a valid schema result with an explicit original-image coordinate header."""
    assert extract.main(["--image", str(pipeline_image), "--blur-threshold", "0"]) == 0
    header, payload = capsys.readouterr().out.split("\n", 1)
    assert header == "Coordinates: input_image; boxes=x,y,width,height"
    assert LabelExtraction.model_validate_json(payload).label_id == "test_pipeline"


def test_cli_bad_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Report unreadable images and invalid warning settings as CLI errors."""
    with pytest.raises(SystemExit) as missing:
        extract.main(["--image", str(tmp_path / "missing.png")])
    assert missing.value.code == 2
    assert "No such file" in capsys.readouterr().err
    with pytest.raises(SystemExit) as settings:
        extract.main(["--image", str(tmp_path / "missing.png"), "--min-confidence", "2"])
    assert settings.value.code == 2
    assert "min_confidence" in capsys.readouterr().err
