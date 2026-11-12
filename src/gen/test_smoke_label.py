"""Tests for the clean synthetic label generator."""

import json
from pathlib import Path

import numpy as np
import pytest
import zxingcpp
from PIL import Image

from src.gen.smoke_label import build_label, mm_to_px


@pytest.mark.parametrize("millimetres, pixels", [(0, 0), (25.4, 300), (50.8, 600)])
def test_mm_to_px(millimetres: float, pixels: int) -> None:
    """Check conversion from millimetres to pixels."""
    assert mm_to_px(millimetres) == pixels


def test_generated_label(tmp_path: Path) -> None:
    """Check image size, ground truth, and the decoded GS1 payload."""
    paths = build_label(tmp_path)
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))

    with Image.open(paths["image"]) as image:
        assert image.size == (mm_to_px(100), mm_to_px(60))
        assert truth["image_size_px"] == list(image.size)
        decoded = zxingcpp.read_barcodes(np.asarray(image.convert("RGB")))

    assert truth["test_data"] is True
    assert truth["status"] == "DRAFT"
    assert len(decoded) == 1
    assert decoded[0].content_type == zxingcpp.ContentType.GS1
    assert decoded[0].text == truth["barcode_payload"]
    expected = "".join(
        f"({key}){value}" for key, value in truth["barcode_ais"].items()
    )
    assert decoded[0].text == expected
    assert set(truth["fields"]).issubset(truth["slot_boxes_px_xywh"])


def test_reproducible_output(tmp_path: Path) -> None:
    """Check that two runs produce identical image and JSON bytes."""
    first = build_label(tmp_path / "first")
    second = build_label(tmp_path / "second")

    for key in ("image", "ground_truth"):
        assert Path(first[key]).read_bytes() == Path(second[key]).read_bytes()


def test_custom_label_values(tmp_path: Path) -> None:
    """Vary printed fields and GS1 data without overwriting the default label."""
    original = build_label(tmp_path)
    fields = {"product_name": "TEST SENSOR", "model": "REF: TEST-M002"}
    ais = {"10": "TESTLOT002", "17": "280229", "21": "TESTSER002"}
    paths = build_label(
        tmp_path, label_id="test_label_002", field_values=fields, barcode_ais=ais
    )
    repeated = build_label(
        tmp_path / "repeat", label_id="test_label_002", field_values=fields, barcode_ais=ais
    )
    truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    assert truth["label_id"] == "test_label_002"
    assert truth["fields"]["product_name"] == "TEST SENSOR"
    assert truth["fields"]["model"] == "REF: TEST-M002"
    assert truth["fields"]["lot"] == "LOT: TESTLOT002"
    assert truth["fields"]["expiry"] == "EXP: 2028-02-29"
    assert truth["barcode_ais"] == {"01": "00000000000000", **ais}
    assert fields == {"product_name": "TEST SENSOR", "model": "REF: TEST-M002"}
    assert ais == {"10": "TESTLOT002", "17": "280229", "21": "TESTSER002"}
    with Image.open(paths["image"]) as image, Image.open(original["image"]) as baseline:
        decoded = zxingcpp.read_barcodes(np.asarray(image.convert("RGB")))
        assert len(decoded) == 1
        assert decoded[0].content_type == zxingcpp.ContentType.GS1
        assert decoded[0].text == "(01)00000000000000(17)280229(10)TESTLOT002(21)TESTSER002"
        for field in ("product_name", "model", "lot", "expiry"):
            x, y, width, height = truth["slot_boxes_px_xywh"][field]
            region = (x, y, x + width, y + height)
            assert image.crop(region).tobytes() != baseline.crop(region).tobytes()
    assert Path(original["image"]).name == "test_label_001.png"
    assert Path(paths["image"]).name == "test_label_002.png"
    for key in ("image", "ground_truth"):
        assert Path(paths[key]).read_bytes() == Path(repeated[key]).read_bytes()
        assert Path(original[key]).is_file()


@pytest.mark.parametrize("label_id", ["label_002", "test_", "test_../../escape", "/tmp/test_label"])
def test_invalid_label_id(tmp_path: Path, label_id: str) -> None:
    """Reject names that omit the test marker or escape the output folder."""
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="label_id"):
        build_label(output, label_id=label_id)
    assert not output.exists()


@pytest.mark.parametrize(
    "fields, ais, message",
    [
        ({"lot": "LOT: DIFFERENT"}, None, "must match"),
        ({"expiry": "EXP: 2030-01-01"}, None, "must match"),
        ({"unknown": "value"}, None, "Unknown label field"),
        (None, {"99": "value"}, "Unknown barcode AI"),
        (None, {"01": ""}, "test placeholder"),
        (None, {"17": "20271231"}, "YYMMDD"),
        (None, {"17": "270229"}, "day"),
        (None, {"10": ""}, "Test AI 10"),
        (None, {"21": "A" * 21}, "Test AI 21"),
        ({"product_name": "X" * 100}, None, "Text does not fit"),
    ],
)
def test_invalid_label_values(
    tmp_path: Path,
    fields: dict[str, str] | None,
    ais: dict[str, str] | None,
    message: str,
) -> None:
    """Reject inconsistent or unsupported inputs before writing label files."""
    output = tmp_path / "output"
    with pytest.raises(ValueError, match=message):
        build_label(output, field_values=fields, barcode_ais=ais)
    assert not output.exists()
