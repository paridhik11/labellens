"""Checks for GS1 element parsing, real decoding and measured failure handling."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import zxingcpp
from PIL import Image

from src.common.schemas import BarcodeResult
from src.cv import barcode
from src.gen.generate_dataset import generate_dataset
from src.gen.smoke_label import build_label

GS = "\x1d"
GTIN = "00000000000000"  # Existing test placeholder, not an allocated identifier.


def _barcode_image(payload: str, gs1: bool = True) -> np.ndarray:
    """Render a deterministic barcode for decoder integration checks."""
    symbol = zxingcpp.create_barcode(payload, zxingcpp.BarcodeFormat.DataMatrix, gs1=gs1)
    pixels = zxingcpp.write_barcode_to_image(symbol, scale=4, add_quiet_zones=True)
    return np.asarray(Image.fromarray(np.asarray(pixels)).convert("RGB"))


@pytest.fixture(scope="module")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate one label per condition for measured decoder checks."""
    output = tmp_path_factory.mktemp("barcodes")
    generate_dataset(output, seed=42, labels_per_condition=1)
    return output


@pytest.fixture(scope="module")
def recovery_dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate the fixed 17-per-condition set used to guard the hard-barcode target."""
    output = tmp_path_factory.mktemp("barcode_recovery")
    generate_dataset(output, seed=42, labels_per_condition=17)
    return output


@pytest.mark.parametrize(
    "payload, expected",
    [
        (f"01{GTIN}1727123110TESTLOT{GS}21TESTSER", {"01": GTIN, "17": "271231", "10": "TESTLOT", "21": "TESTSER"}),
        (f"21TESTSER{GS}10TESTLOT{GS}1728022901{GTIN}", {"21": "TESTSER", "10": "TESTLOT", "17": "280229", "01": GTIN}),
        ("10LOT21SER17ABC", {"10": "LOT21SER17ABC"}),
        (f"10LOT(21)X{GS}21TESTSER", {"10": "LOT(21)X", "21": "TESTSER"}),
        (f"10{'A' * 20}{GS}21{'B' * 20}", {"10": "A" * 20, "21": "B" * 20}),
        (f"01{GTIN}{GS}17271231{GS}", {"01": GTIN, "17": "271231"}),
        ("10TEST-Lot_01/2", {"10": "TEST-Lot_01/2"}),
    ],
)
def test_parse_gs1(payload: str, expected: dict[str, str]) -> None:
    """Respect lengths and separators without guessing structure inside a value."""
    assert barcode.parse_gs1(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        "", "01", "01" + "0" * 13, "01" + "0" * 13 + "1", "01" + "０" * 14,
        "17271301", "17271200", "17270229", "1727123", "17ABCDEF",
        "10", "21" + "A" * 21, "10HAS SPACE", "10UNICODEé", "10BAD#CHAR", "21BAD\nVALUE",
        f"01{GTIN}01{GTIN}", f"10LOT{GS}10OTHER", f"10LOT{GS}{GS}21SER",
        "11270101", f"(01){GTIN}", f"]d801{GTIN}", GS + f"01{GTIN}",
    ],
)
def test_invalid_gs1(payload: str) -> None:
    """Reject unsupported, duplicate, truncated and malformed field data."""
    with pytest.raises(ValueError):
        barcode.parse_gs1(payload)


def test_decode_generated_label(tmp_path: Path) -> None:
    """Decode the real smoke label into the shared schema with a contained box."""
    paths = build_label(tmp_path)
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    with Image.open(paths["image"]) as photo:
        image = np.asarray(photo.convert("RGB"))
    before = image.copy()
    results, warnings = barcode.decode_barcodes(image)
    assert warnings == []
    assert len(results) == 1 and isinstance(results[0], BarcodeResult)
    assert results[0].type == "Data Matrix"
    assert results[0].parsed == truth["barcode_ais"]
    assert results[0].raw == f"01{GTIN}1727123110TESTLOT001{GS}21TESTSER001"
    x, y, width, height = results[0].bbox
    sx, sy, sw, sh = truth["slot_boxes_px_xywh"]["udi"]
    assert sx <= x < x + width <= sx + sw
    assert sy <= y < y + height <= sy + sh
    assert np.array_equal(image, before)
    assert barcode.decode_barcodes(image) == (results, warnings)


def test_thresholded_template_slot_recovers_barcode(tmp_path: Path) -> None:
    """Decode the fixed slot after local thresholding while preserving full-image coordinates."""
    paths = build_label(tmp_path)
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    with Image.open(paths["image"]) as photo:
        image = np.asarray(photo.convert("RGB"))
    results, warnings = barcode.decode_barcode_slot(image)
    assert len(results) == 1 and results[0].parsed == truth["barcode_ais"]
    assert warnings == []
    x, y, width, height = results[0].bbox
    sx, sy, sw, sh = truth["slot_boxes_px_xywh"]["udi"]
    assert sx <= x < x + width <= sx + sw
    assert sy <= y < y + height <= sy + sh


def test_real_variable_value_parentheses() -> None:
    """Decode literal parentheses inside lot data without treating them as AIs."""
    image = _barcode_image(f"[01]{GTIN}[10]LOT(21)X")
    results, warnings = barcode.decode_barcodes(image)
    assert warnings == []
    assert results[0].parsed == {"01": GTIN, "10": "LOT(21)X"}


def test_real_unsupported_ai() -> None:
    """A valid GS1 symbol with an unsupported AI keeps raw data and a warning."""
    image = _barcode_image(f"(01){GTIN}(11)271101")
    results, warnings = barcode.decode_barcodes(image)
    assert len(results) == 1
    assert results[0].raw == f"01{GTIN}11271101"
    assert results[0].parsed == {}
    assert any(warning.startswith("GS1_PARSE_FAILED:") for warning in warnings)


def test_non_gs1_barcode() -> None:
    """Plain barcode content must not be mistaken for GS1 element data."""
    image = _barcode_image("TEST-NON-GS1", gs1=False)
    results, warnings = barcode.decode_barcodes(image)
    assert len(results) == 1
    assert results[0].raw == "TEST-NON-GS1"
    assert results[0].parsed == {}
    assert any(warning.startswith("NON_GS1_BARCODE:") for warning in warnings)


def test_multiple_barcodes() -> None:
    """Preserve multiple decoded symbols rather than selecting one silently."""
    first = _barcode_image(f"(01){GTIN}(10)TESTA")
    second = _barcode_image(f"(01){GTIN}(10)TESTB")
    shape = (max(first.shape[0], second.shape[0]) + 20, first.shape[1] + second.shape[1] + 40, 3)
    image = np.full(shape, 255, np.uint8)
    image[10:10 + first.shape[0], 10:10 + first.shape[1]] = first
    offset = first.shape[1] + 30
    image[10:10 + second.shape[0], offset:offset + second.shape[1]] = second
    results, warnings = barcode.decode_barcodes(image)
    assert warnings == []
    assert len(results) == 2
    assert {result.parsed["10"] for result in results} == {"TESTA", "TESTB"}


def test_invalid_position_preserves_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bad position does not discard raw bytes or invent a rectangle."""
    point = SimpleNamespace(x=1, y=1)
    result = SimpleNamespace(
        bytes=b"\xffTEST", content_type=zxingcpp.ContentType.Text, format=zxingcpp.BarcodeFormat.DataMatrix,
        position=SimpleNamespace(top_left=point, top_right=point, bottom_right=point, bottom_left=point),
    )
    monkeypatch.setattr(zxingcpp, "read_barcodes", lambda image: [result])
    results, warnings = barcode.decode_barcodes(np.zeros((20, 30, 3), dtype=np.uint8))
    assert results[0].raw.encode("latin-1") == b"\xffTEST"
    assert results[0].bbox is None
    assert any(warning.startswith("BARCODE_POSITION_INVALID:") for warning in warnings)


def test_blank_image() -> None:
    """No decode is represented explicitly, without a fabricated barcode."""
    results, warnings = barcode.decode_barcodes(np.full((200, 300, 3), 255, dtype=np.uint8))
    assert results == []
    assert warnings == ["BARCODE_NOT_DECODED: no barcode could be decoded"]


def test_invalid_image() -> None:
    """Reject grayscale input under the documented RGB interface."""
    with pytest.raises(ValueError, match="uint8 RGB"):
        barcode.decode_barcodes(np.zeros((20, 30), dtype=np.uint8))


def test_engine_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A decoder exception must not be misreported as successful empty output."""
    def fail(image: np.ndarray) -> None:
        """Simulate an inference-engine failure."""
        raise RuntimeError("test decoder failure")

    monkeypatch.setattr(zxingcpp, "read_barcodes", fail)
    with pytest.raises(RuntimeError, match="test decoder failure"):
        barcode.decode_barcodes(np.zeros((20, 30, 3), dtype=np.uint8))


@pytest.mark.parametrize("rectify", [False, True])
def test_dataset_evaluation(dataset: Path, rectify: bool, capsys: pytest.CaptureFixture[str]) -> None:
    """Count every condition separately and keep failed images in denominators."""
    results = barcode.evaluate_dataset(dataset, rectify=rectify)
    for condition, counts in results.items():
        assert counts["images"] == 1
        assert counts["correction_failures"] == counts["parse_warning_images"] == 0
        assert 0 <= counts["matching_ai_images"] <= counts["decoded_images"] <= 1
        if condition == "clean":
            assert counts["matching_ai_images"] == 1
    arguments = ["--dataset", str(dataset)] + (["--rectify"] if rectify else [])
    assert barcode.main(arguments) == 0
    output = capsys.readouterr().out
    mode = "corrected-image-first" if rectify else "original-image-first with correction fallback"
    assert f"Barcode evaluation: {mode}, including template-slot recovery" in output
    assert "clean: decoded=1/1, all_ais_match=1/1" in output


def test_hard_barcode_recovery_stays_at_least_80_percent(recovery_dataset: Path) -> None:
    """Keep the complete seed-42 hard-condition exact GS1 match rate above 80%."""
    results = barcode.evaluate_dataset(recovery_dataset)
    assert results["clean"]["matching_ai_images"] == 17
    assert results["moderate"]["matching_ai_images"] == 17
    assert results["hard"]["images"] == 17
    assert results["hard"]["matching_ai_images"] >= 14


def test_evaluation_correction_failure(dataset: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing boundary remains an explicit failed image during evaluation."""
    monkeypatch.setattr(barcode, "find_label_corners", lambda image: None)
    monkeypatch.setattr(barcode, "decode_barcodes", lambda image: pytest.fail("No corrected image is available"))
    results = barcode.evaluate_dataset(dataset, rectify=True)
    for counts in results.values():
        assert counts["images"] == counts["correction_failures"] == 1
        assert counts["decoded_images"] == counts["matching_ai_images"] == 0


def test_evaluation_parse_warning(dataset: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse failures count as decoded images without claiming matched fields."""
    monkeypatch.setattr(
        barcode, "decode_barcodes",
        lambda image: ([BarcodeResult(type="Data Matrix", raw="unsupported")], ["GS1_PARSE_FAILED: test"]),
    )
    for counts in barcode.evaluate_dataset(dataset).values():
        assert counts["images"] == counts["decoded_images"] == counts["parse_warning_images"] == 1
        assert counts["matching_ai_images"] == 0


@pytest.mark.parametrize("rectify", [False, True])
def test_image_cli(dataset: Path, rectify: bool, capsys: pytest.CaptureFixture[str]) -> None:
    """Print schema objects with raw separators escaped in JSON."""
    arguments = ["--image", str(dataset / "clean/test_label_001_clean.png")] + (["--rectify"] if rectify else [])
    assert barcode.main(arguments) == 0
    output = capsys.readouterr().out
    assert f"Coordinates: {'corrected_image' if rectify else 'input_image'}" in output
    assert '"01": "00000000000000"' in output
    assert "\\u001d" in output
    assert '"warnings": []' in output


def test_image_cli_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Report missing files and absent boundaries as explicit command errors."""
    with pytest.raises(SystemExit) as missing:
        barcode.main(["--image", str(tmp_path / "missing.png")])
    assert missing.value.code == 2
    assert "No such file" in capsys.readouterr().err
    path = tmp_path / "blank.png"
    Image.new("RGB", (200, 100), "white").save(path)
    with pytest.raises(SystemExit) as blank:
        barcode.main(["--image", str(path), "--rectify"])
    assert blank.value.code == 2
    assert "NEEDS_HUMAN_REVIEW: no suitable label boundary" in capsys.readouterr().err
