"""Checks for raw OCR conversion, RGB handling and bundled model inference."""

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageDraw

from src.common.schemas import OcrBlock
from src.cv import ocr
from src.gen.smoke_label import build_label


def test_result_conversion() -> None:
    """Convert a tilted text region without changing text or low confidence."""
    corners = [[10, 20], [50, 10], [60, 40], [20, 50]]
    results = [[corners, " LOT: TEST001 ", 0.123], [corners, "   ", 0.9]]
    before = copy.deepcopy(results)
    blocks = ocr.ocr_blocks_from_results(results, (100, 80))
    assert blocks == [OcrBlock(text=" LOT: TEST001 ", bbox=(10, 10, 50, 40), conf=0.123)]
    assert results == before


@pytest.mark.parametrize("results", [None, []])
def test_empty_results(results: list[list[Any]] | None) -> None:
    """No recognized text becomes an empty list of schema objects."""
    assert ocr.ocr_blocks_from_results(results, (100, 80)) == []


@pytest.mark.parametrize(
    "row",
    [
        ["missing confidence", "text"],
        [[[0, 0], [10, 0], [10, 10]], "text", 0.9],
        [[[0, 0], [10, 0], [10, 10], [0, np.nan]], "text", 0.9],
        [[[0, 0], [10, 0], [10, 10], [0, 10]], "text", np.inf],
        [[[0, 0], [10, 0], [10, 10], [0, 10]], "text", -0.1],
        [[[0, 0], [10, 0], [10, 10], [0, 10]], "text", 1.1],
        [[[0, 0], [10, 0], [10, 10], [0, 10]], "text", None],
        [[[0, 0], [10, 0], [10, 10], [0, 10]], 123, 0.9],
        [[[-1, 0], [10, 0], [10, 10], [-1, 10]], "text", 0.9],
        [[[0, 0], [101, 0], [101, 10], [0, 10]], "text", 0.9],
        [[[10, 0], [10, 0], [10, 10], [10, 10]], "text", 0.9],
    ],
)
def test_invalid_results(row: list[Any]) -> None:
    """Reject malformed geometry, confidence and text instead of inventing values."""
    with pytest.raises(ValueError):
        ocr.ocr_blocks_from_results([row], (100, 80))


def test_invalid_result_image_size() -> None:
    """An invalid image extent is rejected even when no text is found."""
    with pytest.raises(ValueError, match="positive"):
        ocr.ocr_blocks_from_results(None, (0, 80))


def test_engine_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use one cached CPU engine and retain low-confidence recognition results."""
    import rapidocr_onnxruntime

    observed: list[dict[str, Any]] = []
    sentinel = object()

    def factory(**kwargs: Any) -> object:
        """Record engine configuration without loading models in this unit check."""
        observed.append(kwargs)
        return sentinel

    ocr._get_engine.cache_clear()
    monkeypatch.setattr(rapidocr_onnxruntime, "RapidOCR", factory)
    try:
        assert ocr._get_engine() is sentinel
        assert ocr._get_engine() is sentinel
        assert len(observed) == 1
        assert observed[0]["text_score"] == 0.0
        assert observed[0]["use_det"] is observed[0]["use_rec"] is True
        assert observed[0]["use_cls"] is False
        assert all(observed[0][f"{stage}_use_cuda"] is False for stage in ("det", "cls", "rec"))
        assert observed[0]["intra_op_num_threads"] == observed[0]["inter_op_num_threads"] == 1
    finally:
        ocr._get_engine.cache_clear()


def test_rgb_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """Send BGR pixels to RapidOCR while preserving the original RGB array."""
    image = np.full((30, 60, 3), (10, 20, 30), dtype=np.uint8)
    before = image.copy()

    def engine(bgr: np.ndarray) -> tuple[list[list[Any]], list[float]]:
        """Check the actual pixels passed to the engine and provide a known row."""
        assert np.array_equal(bgr[0, 0], (30, 20, 10))
        return [[[[1, 2], [21, 2], [21, 12], [1, 12]], "TEST", 0.4]], [0.0]

    monkeypatch.setattr(ocr, "_get_engine", lambda: engine)
    assert ocr.read_text(image) == [OcrBlock(text="TEST", bbox=(1, 2, 20, 10), conf=0.4)]
    assert np.array_equal(image, before)


def test_read_text_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """A real engine's no-text response is handled without a fabricated block."""
    monkeypatch.setattr(ocr, "_get_engine", lambda: lambda image: (None, None))
    assert ocr.read_text(np.zeros((30, 60, 3), dtype=np.uint8)) == []


def test_read_text_engine_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expose inference failures so the later extraction pipeline can warn."""
    def engine(image: np.ndarray) -> None:
        """Simulate a failed inference call."""
        raise RuntimeError("test inference failed")

    monkeypatch.setattr(ocr, "_get_engine", lambda: engine)
    with pytest.raises(RuntimeError, match="test inference failed"):
        ocr.read_text(np.zeros((30, 60, 3), dtype=np.uint8))


def test_read_text_invalid_image(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate RGB input before loading an engine or trying inference."""
    monkeypatch.setattr(ocr, "_get_engine", lambda: pytest.fail("Engine should not be loaded"))
    with pytest.raises(ValueError, match="uint8 RGB"):
        ocr.read_text(np.zeros((30, 60), dtype=np.uint8))


def test_bundled_models_read_label(tmp_path: Path) -> None:
    """Run actual bundled models and reproduce their text, scores and positions."""
    paths = build_label(tmp_path)
    with Image.open(paths["image"]) as photo:
        image = np.asarray(photo.convert("RGB"))
    first = ocr.read_text(image)
    second = ocr.read_text(image)
    assert first == second
    assert all(isinstance(block, OcrBlock) for block in first)
    assert any("Example" in block.text for block in first)
    assert any("EXP" in block.text for block in first)


@pytest.mark.parametrize("rectify", [False, True])
def test_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], rectify: bool
) -> None:
    """The CLI declares the coordinate space and prints the actual schema data."""
    path = tmp_path / "test_label.png"
    image = Image.new("RGB", (300, 200), "gray")
    ImageDraw.Draw(image).rectangle((40, 30, 250, 170), fill="white")
    image.save(path)
    monkeypatch.setattr(ocr, "read_text", lambda image: [OcrBlock(text="TEST", bbox=(1, 2, 20, 10), conf=0.4)])
    arguments = ["--image", str(path)] + (["--rectify"] if rectify else [])
    assert ocr.main(arguments) == 0
    output = capsys.readouterr().out
    assert f"Coordinates: {'corrected_image' if rectify else 'input_image'}" in output
    assert '"text": "TEST"' in output
    assert '"conf": 0.4' in output
    assert "OCR blocks: 1" in output


def test_cli_no_boundary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing label boundary is an explicit CLI failure when rectifying."""
    path = tmp_path / "blank.png"
    Image.new("RGB", (300, 200), "white").save(path)
    with pytest.raises(SystemExit) as error:
        ocr.main(["--image", str(path), "--rectify"])
    assert error.value.code == 2
    assert "NEEDS_HUMAN_REVIEW: no suitable label boundary" in capsys.readouterr().err


def test_cli_missing_image(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing input image is reported as a command-line error."""
    with pytest.raises(SystemExit) as error:
        ocr.main(["--image", str(tmp_path / "missing.png")])
    assert error.value.code == 2
    assert "No such file" in capsys.readouterr().err
