"""CV3 provenance, frozen scoring, crop coordinates and unchanged mismatch checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.cv_experiments import cv3_eval as bench
from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock
from src.cv.cv3 import anchored_crops, available_ocr_models, barcode_prefill, read_anchors
from src.gen.cv3_acquire import acquire, fetch_frozen


def test_reference_split_and_strict_scoring() -> None:
    """No family crosses splits; unscored unreadable values do not inflate denominators."""
    records = json.loads(Path('src/gen/cv3_dataset.json').read_text())['records']
    assert len(records) == 30
    assert sum(r['split'] == 'test' for r in records) == 10
    assert not ({r['family'] for r in records if r['split'] == 'test'} &
                {r['family'] for r in records if r['split'] == 'dev'})
    assert len({r['sha256'] for r in records}) == 30
    assert bench.canonical('product_name', ' Name™ ') == 'name™'
    assert bench.canonical('product_name', 'Name') != 'name™'
    assert bench.canonical('lot', 'LOT: AO1') != bench.canonical('lot', 'A01')
    assert bench.canonical('expiry', '2028/2/29') == '2028-02-29'
    assert bench.canonical('expiry', '02/03/2028') == '02/03/2028'
    assert bench.canonical('expiry', '2027-02-29') == '2027-02-29'
    refs = [{'fields': {'lot': 'ABC'}}]
    before = bench.summarize(refs, [{'fields': {}}])
    after = bench.summarize(refs, [{'fields': {'prefill_lot': 'ABC'}}])
    assert bench.improves(before, after) and not bench.improves(after, before)
    assert not bench.improves(after, after)
    assert after['photo']['effective']['lot']['n'] == 1
    assert after['photo']['printed']['lot']['k'] == 0
    with pytest.raises(ValueError, match='populations'):
        bench.improves(before, bench.summarize(refs*2, [{'fields': {}}]*2))


def test_prefill_validation_and_provenance() -> None:
    """Suggestions require one parsed GS1 barcode and retain raw payload/coordinate evidence."""
    pytest.importorskip('cv2')
    pytest.importorskip('zxingcpp')
    from src.cv.barcode import parse_gs1

    raw = '01000000000000001728022910ALOT7'
    barcode = BarcodeResult(type='DataMatrix', raw=raw, parsed=parse_gs1(raw), bbox=(10, 20, 50, 50))
    prefill = barcode_prefill([barcode])
    assert prefill['expiry']['value'] == '2028-02-29'
    assert prefill['lot']['value'] == 'ALOT7' and prefill['lot']['ai'] == '10'
    assert prefill['lot']['bbox_input_px'] == barcode.bbox
    assert prefill['lot']['source'] == 'decoded_gs1' and prefill['lot']['raw'] == raw
    assert barcode_prefill([]) == barcode_prefill([barcode, barcode]) == {}
    assert barcode_prefill([barcode.model_copy(update={'parsed': {}})]) == {}
    assert barcode_prefill([barcode.model_copy(update={'raw': raw.replace('280229', '270229')})]) == {}


def test_prefill_cannot_hide_printed_mismatch() -> None:
    """Existing checker sees the same printed values even with contradictory prefill fields."""
    pytest.importorskip('cv2')
    pytest.importorskip('zxingcpp')
    from src.cv.barcode import parse_gs1
    from src.cv.consistency import check_extraction

    raw = '01000000000000001731123110OTHERLOT'
    barcode = BarcodeResult(type='DataMatrix', raw=raw, parsed=parse_gs1(raw))
    fields = {'lot': 'LOT: PRINT7', 'expiry': 'EXP: 2028-02-29'}
    extraction = LabelExtraction(label_id='test_conflict', fields=dict(fields), barcodes=[barcode],
                                 ocr_blocks=[OcrBlock(text=v, bbox=(0, i*30, 200, 20), conf=0.99)
                                             for i, v in enumerate(fields.values())])
    before = check_extraction(extraction)
    for field, evidence in barcode_prefill([barcode]).items():
        extraction.fields[f'printed_{field}'] = fields[field]
        extraction.fields[f'prefill_{field}'] = evidence['value']
    assert check_extraction(extraction) == before
    assert sum(f.kind == 'barcode_mismatch' for f in before) == 2


def test_anchor_crop_pixels_and_projection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Crops contain actual keyed pixels and recognized boxes map back to original coordinates."""
    np = pytest.importorskip('numpy')
    pytest.importorskip('cv2')
    from src.cv import ocr

    image = np.full((100, 240, 3), 127, dtype=np.uint8)
    key = OcrBlock(text='LOT', bbox=(20, 30, 30, 10), conf=0.99)
    crops = anchored_crops(image, [key, key, key.model_copy(update={'text': 'LOTION'})])
    assert len(crops) == 1
    field, box, pixels = crops[0]
    assert field == 'lot' and box == (10, 25, 210, 55)
    assert pixels.shape == (90, 600, 3) and (pixels == 127).all()

    def recognize(crop: Any, **kwargs: Any) -> list[OcrBlock]:
        """Return a known observed crop row without accessing any reference value."""
        return [OcrBlock(text='LOT: ABC123', bbox=(30, 15, 120, 30), conf=0.99)]

    monkeypatch.setattr(ocr, 'read_text_robust', recognize)
    fields, evidence = read_anchors(image, [key])
    assert fields['lot'] == 'LOT: ABC123' and evidence[0].bbox == (20, 30, 40, 10)


def test_model_probe_has_clean_absence_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """No optional model installation is required to inspect availability."""
    import importlib.metadata

    def absent(name: str) -> Any:
        """Simulate minimal CI without installed OCR packages."""
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, 'distribution', absent)
    assert available_ocr_models()['fallback'] == 'existing OCR'


def test_acquisition_and_frozen_source_verification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acquisition keeps source bytes separate from references and refuses a changed frozen image."""
    import scripts.symbols.fetch_real_labels as fetch
    import src.gen.cv3_acquire as module

    content = b'uninterpreted-image-bytes'

    class Response:
        """Minimal HTTP response without a network request."""

        def __enter__(self) -> Response:
            """Return this fake response."""
            return self

        def __exit__(self, *args: Any) -> None:
            """Close this fake response."""

        def read(self, count: int) -> bytes:
            """Return bounded image bytes."""
            return content[:count]

    monkeypatch.setattr(module, 'urlopen', lambda *a, **kw: Response())
    monkeypatch.setattr(fetch, 'get', lambda url: json.dumps({'products': [
        {'title': 'A catheter', 'handle': 'family', 'images': [{'src': 'https://example.org/photo.jpg'}]}]}).encode())
    monkeypatch.chdir(tmp_path)
    rows = acquire(tmp_path/'photos', limit=1)
    assert len(rows) == 1 and 'fields' not in rows[0]
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'records': rows}))
    assert fetch_frozen(manifest, tmp_path/'photos') == 1
    assert rows[0]['sha256'] == hashlib.sha256(content).hexdigest()
    (tmp_path/'photos'/rows[0]['filename']).write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        fetch_frozen(manifest, tmp_path/'photos')


def test_extractor_keeps_perspective_and_print_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The connected warp is called; opt-in prefill never replaces checker-facing text."""
    np = pytest.importorskip('numpy')
    pytest.importorskip('cv2')
    pytest.importorskip('zxingcpp')
    from types import SimpleNamespace

    from PIL import Image

    from src.cv import extract
    from src.cv.barcode import parse_gs1
    from src.cv.photo_ocr import PhotoReading

    path = tmp_path/'photo.png'
    Image.new('RGB', (200, 100), 'white').save(path)
    corners = np.array([[0, 0], [199, 0], [199, 99], [0, 99]])
    raw = '01000000000000001731123110OTHERLOT'
    barcode = BarcodeResult(type='DataMatrix', raw=raw, parsed=parse_gs1(raw))
    printed = {'lot': 'LOT: PRINT7', 'expiry': 'EXP: 2028-02-29'}
    blocks = [OcrBlock(text=v, bbox=(10, 10+i*30, 170, 20), conf=0.99) for i, v in enumerate(printed.values())]
    monkeypatch.setattr(extract, 'resolve_photo_profile', lambda p: p)
    monkeypatch.setattr(extract, '_decode_safely', lambda im: ([], []))
    monkeypatch.setattr(extract, 'find_label_corners', lambda im: corners)
    warped = []

    def warp(im: Any, quad: Any, ratio: Any) -> Any:
        """Observe the perspective call without a model or final-image extraction."""
        warped.append(ratio)
        return SimpleNamespace(image=im, homography=np.eye(3))

    monkeypatch.setattr(extract, 'warp_label', warp)
    reading = PhotoReading(blocks, np.eye(3), 1, 0, 'original')
    monkeypatch.setattr(extract, '_read_blind_photo', lambda *a: (reading, []))
    monkeypatch.setattr(extract, 'detect_symbols_blind', lambda im: [])
    monkeypatch.setattr(extract, '_blind_barcodes', lambda *a: ([barcode], [], 'test'))
    monkeypatch.setattr(extract, 'map_cv2_fields', lambda *a, **kw: (dict(printed), []))
    base, _ = extract.extract_label_modes(path, modes=('blind',), postcorrect=True)['blind']
    candidate, details = extract.extract_label_modes(path, modes=('blind',), postcorrect=True, cv3_stage=1)['blind']
    assert warped == [None, None]
    assert candidate.fields['lot'] == base.fields['lot'] == printed['lot']
    assert candidate.fields['expiry'] == base.fields['expiry'] == printed['expiry']
    assert candidate.fields['printed_lot'] == printed['lot']
    assert candidate.fields['prefill_lot'] == details['record_prefill']['lot']['value'] == 'OTHERLOT'
    with pytest.raises(ValueError, match='cv3_stage'):
        extract.extract_label_modes(path, cv3_stage=99)


def test_prediction_and_evaluation_have_no_reference_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The worker receives image/options only; exceptions remain counted as field misses."""
    from src.cv import extract

    seen = []

    def fake_extract(image: str, *, cv3_stage: int = 0, **kwargs: Any) -> dict[str, Any]:
        """Stand in for a recognizer and capture image-only inputs."""
        seen.append((image, cv3_stage, kwargs))
        return {'blind': (LabelExtraction(label_id='dummy', fields={'lot': 'LOT: X1'}), {})}

    monkeypatch.setattr(extract, 'extract_label_modes', fake_extract)
    assert bench.predict(('pixels.jpg', str(tmp_path), '1'))['fields']['lot'] == 'LOT: X1'
    assert seen[0][1] == 1 and 'fields' not in seen[0][2]
    photo = tmp_path/'pixels.jpg'
    photo.write_bytes(b'pixels')
    dataset = tmp_path/'dataset.json'
    dataset.write_text(json.dumps({'images_local': str(tmp_path), 'records': [
        {'filename': photo.name, 'sha256': hashlib.sha256(b'pixels').hexdigest(),
         'fields': {'lot': 'X1'}, 'split': 'dev'}]}))
    monkeypatch.setattr(bench, 'DATASET', dataset)
    tasks_seen = []

    def bounded(tasks: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Simulate a recognizer timeout without accessing reference values."""
        tasks_seen.extend(tasks)
        return [{'fields': {}, 'error': 'timeout'}]

    monkeypatch.setattr(bench, 'run_bounded', bounded)
    summary = bench.evaluate('dev', 1, tmp_path, tmp_path/'results')
    assert summary['errors'] == 1 and summary['totals']['photo']['effective']['lot']['k'] == 0
    assert len(tasks_seen[0]) == 3 and 'X1' not in str(tasks_seen)


def test_synthetic_builder_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise generation bookkeeping with stub pixels, never OCR or final-set tuning."""
    pytest.importorskip('cv2')
    pytest.importorskip('zxingcpp')
    from PIL import Image

    from src.gen import augment, smoke_label

    image = tmp_path/'stub.png'
    Image.new('RGB', (20, 10), 'white').save(image)
    calls = []

    def build(output: Path, **kwargs: Any) -> dict[str, str]:
        """Use inert pixels to test generator call contracts only."""
        calls.append(kwargs)
        return {'image': str(image)}

    monkeypatch.setattr(smoke_label, 'build_label', build)
    monkeypatch.setattr(augment, 'augment_label', lambda im, condition, seed: (im, None, None))
    records = bench.build_synthetic(tmp_path/'synthetic')
    assert len(records) == 54 and sum(r['safety'] for r in records) == 6
    assert {r['seed'] for r in records} == set(range(12000, 12016))
    assert sum(c['allow_print_barcode_mismatch'] for c in calls) == 6
    assert bench.build_synthetic(tmp_path/'synthetic') == records
