"""Template decisions never turn weak or missing evidence into matches."""
from pathlib import Path

import pytest

from src.api.printverify import RealPrintEngine
from src.cv.template_print import decide, normalized


def test_template_decisions() -> None:
    """Correct barcode cannot hide a confident text-only change."""
    barcode = [{'parsed': {'10': 'LOT1'}}]
    assert normalized(' A\n B ') == 'A B'
    assert decide([{'status': 'MATCH'}], barcode, {'10': 'LOT1'}) == 'MATCH'
    assert decide([{'status': 'MISMATCH'}], barcode, {'10': 'LOT1'}) == 'MISMATCH'
    assert decide([{'status': 'NEEDS_HUMAN_REVIEW'}], barcode, {'10': 'LOT1'}) == 'NEEDS_HUMAN_REVIEW'
    assert decide([{'status': 'MATCH'}], [], {'10': 'LOT1'}) == 'NEEDS_HUMAN_REVIEW'
    assert decide([{'status': 'MATCH'}], barcode, {'10': 'OTHER'}) == 'MISMATCH'
    assert decide([], barcode, {'10': 'LOT1'}) == 'NEEDS_HUMAN_REVIEW'


def test_missing_binding_abstains() -> None:
    """No template means no blind-match fallback or photo access."""
    assert RealPrintEngine().verify(Path('missing.png'), {})['status'] == 'NEEDS_HUMAN_REVIEW'


def test_slot_ocr_uses_pixels_and_masks_band(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrong expected strings cannot enter recognition; projected evidence stays in input coordinates."""
    np = pytest.importorskip('numpy')
    cv2 = pytest.importorskip('cv2')
    image_module = pytest.importorskip('PIL.Image')
    pytest.importorskip('zxingcpp')
    from types import SimpleNamespace

    from src.cv import ocr, perspective
    from src.cv.template_print import verify_template

    pixels = np.full((600, 1000, 3), 255, dtype=np.uint8)
    cv2.putText(pixels, 'VISIBLE', (55, 155), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    path = tmp_path/'label.png'
    image_module.fromarray(pixels).save(path)
    monkeypatch.setattr(perspective, 'correct_perspective', lambda *a, **k:
                        SimpleNamespace(image=pixels, homography=np.eye(3)))
    seen = []

    def recognize(crop: object, **kwargs: object) -> tuple[list[list[object]], None]:
        """Observe only pixel input and fixed OCR flags."""
        seen.append(kwargs)
        return [['VISIBLE', 0.99]], None

    monkeypatch.setattr(ocr, '_get_engine', lambda: recognize)
    expected = {'fields': {'product_name': 'WRONG'}, 'barcode_ais': {}, 'template': {
        'size_mm': {'w': 100, 'h': 60}, 'slots': [
            {'type': 'text', 'field': 'product_name', 'bbox_mm': [5, 12, 60, 6]}]}}
    result = verify_template(path, expected)
    assert result['status'] == 'MISMATCH' and result['fields'][0]['observed'] == 'VISIBLE'
    assert result['fields'][0]['bbox'] == (50, 120, 600, 60)
    assert seen == [{'use_det': False, 'use_cls': False, 'use_rec': True}]
