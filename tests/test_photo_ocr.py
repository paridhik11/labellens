"""Reference-free orientation, crop coordinates and extractor integration tests."""
from __future__ import annotations

from pathlib import Path

import pytest

cv2 = pytest.importorskip('cv2')
np = pytest.importorskip('numpy')
pytest.importorskip('PIL')
pytest.importorskip('zxingcpp')
from PIL import Image  # noqa: E402

from src.common.schemas import OcrBlock  # noqa: E402
from src.cv import extract, photo_ocr  # noqa: E402
from src.cv.perspective import warp_label  # noqa: E402


def test_native_and_template_geometry() -> None:
    """Known templates control proportions; unknown photos retain observed edge ratio."""
    image = np.zeros((200, 300, 3), dtype=np.uint8)
    corners = np.array([[10, 20], [209, 20], [209, 119], [10, 119]], dtype=np.float32)
    native = warp_label(image, corners)
    assert native.image.shape == (100, 200, 3)
    assert warp_label(image, corners, 1).image.shape == (200, 200, 3)
    with pytest.raises(ValueError):
        warp_label(image, corners + 1000)


def test_rotation_crop_projection_and_deduplication() -> None:
    """Choose an upright marker from pixels only and map boxes back through rotation."""
    image = np.zeros((80, 120, 3), dtype=np.uint8)
    image[0, 0] = [255, 0, 0]

    def reader(pixels: np.ndarray) -> list[OcrBlock]:
        """Recognize the marker only when its pixel is at bottom left."""
        confidence = 0.99 if pixels[-1, 0, 0] == 255 else 0.1
        return [OcrBlock(text='INVENTED', bbox=(5, 6, 20, 10), conf=confidence)]

    result = photo_ocr.read_photo(image, reader=reader)
    assert result.quarter_turns == 1
    projected = photo_ocr.project_blocks(result.blocks, result.to_original, (120, 80))
    assert projected and all(0 <= b.bbox[0] < 120 and 0 <= b.bbox[1] < 80 for b in projected)
    assert photo_ocr.read_photo(image, reader=reader).score == result.score
    b = OcrBlock(text='UNIQUE', bbox=(10, 10, 80, 20), conf=0.9)
    lower = b.model_copy(update={'conf': 0.5})
    assert photo_ocr.merge_blocks([lower, b]) == [b]
    assert photo_ocr.project_blocks([b], np.array([[1, 0, 999], [0, 1, 0], [0, 0, 1]]), (120, 80)) == []


def test_blind_entry_and_original_boxes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the wired perspective module and fixed photo reader, retaining original coordinates."""
    path = tmp_path / 'invented.png'
    Image.new('RGB', (400, 300), 'white').save(path)
    corners = np.array([[50, 50], [349, 50], [349, 249], [50, 249]], dtype=np.float32)
    monkeypatch.setattr(extract, 'find_label_corners', lambda image: corners)
    monkeypatch.setattr(extract, 'detect_symbols_blind', lambda image: [])
    monkeypatch.setattr(extract, '_decode_safely', lambda image: ([], []))
    monkeypatch.setattr(extract, '_blind_barcodes', lambda *args: ([], [], None))
    seen = []

    def reader(image: np.ndarray, **kwargs: object) -> photo_ocr.PhotoReading:
        """Return a synthetic split-key reading and track both OCR views."""
        seen.append(kwargs['view'])
        blocks = [OcrBlock(text='NOVA DEVICE', bbox=(10, 10, 200, 30), conf=0.99),
                  OcrBlock(text='LOT: Z981', bbox=(10, 60, 120, 20), conf=0.99),
                  OcrBlock(text='EXP: 2033-06-15', bbox=(10, 100, 160, 20), conf=0.99)]
        return photo_ocr.PhotoReading(blocks, kwargs['to_original'], 100, 0, kwargs['view'])

    monkeypatch.setattr(extract, 'read_photo', reader)
    result = extract.extract_label(path, mode='blind', postcorrect=True)
    assert seen == ['original', 'rectified']
    assert result.fields['lot'] == 'LOT: Z981' and result.fields['expiry'] == 'EXP: 2033-06-15'
    assert result.ocr_blocks[0].bbox == (10, 10, 200, 30)
    assert any(w.startswith('PHOTO_OCR:') for w in result.warnings)


def test_failed_photo_views(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failed views are explicit failures, never reference-filled successful readings."""
    def fail(*args: object, **kwargs: object) -> photo_ocr.PhotoReading:
        """Simulate a model failure independently of any scoring image."""
        raise RuntimeError('synthetic failure')

    monkeypatch.setattr(extract, 'read_photo', fail)
    reading, warnings = extract._read_blind_photo(np.zeros((10, 10, 3), dtype=np.uint8), None, None)
    assert reading is None and any(w.startswith('OCR_FAILED:') for w in warnings)


def test_full_text_survives_a_confident_clipped_crop() -> None:
    """Overlapping crops must not delete the first words of a correctly read full line."""
    full = OcrBlock(text='NOVA AIRWAY CATHETER', bbox=(0, 0, 300, 30), conf=0.94)
    fragment = OcrBlock(text='CATHETER', bbox=(180, 0, 120, 30), conf=0.99)
    assert photo_ocr.merge_blocks([fragment, full]) == [full]
