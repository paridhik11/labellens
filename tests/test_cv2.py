"""CV2 diagnosis-driven OCR, parsing and benchmark tests; no final-set scoring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.cv_experiments import cv2_benchmark as bench
from src.common.schemas import OcrBlock
from src.cv.ocr_vote import tesseract_lines, vote_lines
from src.cv.photo_cv2 import map_cv2_fields


def test_consensus_and_formats() -> None:
    """Only observed strings are selected, with conservative evidence confidence."""
    a = OcrBlock(text='TESTDEVICE', bbox=(0, 0, 100, 20), conf=0.98)
    b = a.model_copy(update={'text': 'TEST DEVICE', 'conf': 0.85})
    result = vote_lines([a], [b])
    assert result[0].text == 'TEST DEVICE' and result[0].conf == 0.85
    full = b.model_copy(update={'text': 'TEST DEVICE SYSTEM', 'bbox': (0, 0, 160, 20)})
    assert vote_lines([a], [full])[0].text == full.text
    inputs = [OcrBlock(text=text, bbox=(x, y, w, 20), conf=0.99) for text, x, y, w in [
        ('L0T', 0, 50, 30), ('ABCDE', 40, 50, 80), ('2033-06-15', 0, 100, 120),
        ('2030-06-15', 0, 140, 120), ('(17)330615', 0, 180, 120)]]
    fields, warnings = map_cv2_fields(inputs)
    assert fields['lot'] == 'LOT: ABCDE' and fields['expiry'] == 'EXP: 2033-06-15'
    assert any('HRI' in w for w in warnings)
    # Never fill an unobserved expiry merely from an encoded-looking token.
    fields, _ = map_cv2_fields(inputs[-1:])
    assert 'expiry' not in fields


def test_tesseract_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse an independent engine's TSV without requiring its binary in CI."""
    np = pytest.importorskip('numpy')
    pytest.importorskip('PIL')
    import src.cv.ocr_vote as vote

    text = 'level\tpage_num\tblock_num\tpar_num\tline_num\tleft\ttop\twidth\theight\tconf\ttext\n'
    text += '5\t1\t1\t1\t1\t2\t3\t30\t10\t90\tLOT\n'
    text += '5\t1\t1\t1\t1\t40\t3\t40\t10\t80\tABC123\n'
    monkeypatch.setattr(vote.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout=text))
    blocks = tesseract_lines(np.zeros((30, 100, 3), dtype=np.uint8), executable='fake-tesseract')
    assert blocks[0].text == 'LOT ABC123' and blocks[0].bbox == (2, 3, 78, 10)
    monkeypatch.setattr(vote.shutil, 'which', lambda _: None)
    with pytest.raises(RuntimeError, match='unavailable'):
        tesseract_lines(np.zeros((30, 100, 3), dtype=np.uint8))


def test_upscale_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enlargement before recognition maps boxes back without changing source coordinates."""
    np = pytest.importorskip('numpy')
    pytest.importorskip('cv2')
    from src.cv import ocr, photo_ocr
    from src.cv.photo_cv2 import read_cv2

    reading = photo_ocr.PhotoReading([], np.eye(3), 0, 0, 'original')
    monkeypatch.setattr(photo_ocr, 'read_photo', lambda *args, **kwargs: reading)
    seen = []

    def recognize(image: object, **kwargs: object) -> list[OcrBlock]:
        """Observe the enlarged shape and provide a known enlarged-coordinate box."""
        seen.append(image.shape)
        return [OcrBlock(text='TEST', bbox=(40, 20, 80, 40), conf=0.9)]

    monkeypatch.setattr(ocr, 'read_text_robust', recognize)
    result = read_cv2(np.zeros((40, 80, 3), dtype=np.uint8), view='original',
                      to_original=np.eye(3), second_engine=False)
    assert seen == [(160, 320, 3)] and result.blocks[0].bbox == (10, 5, 20, 10)


def test_benchmark_scoring_and_gate(tmp_path: Path) -> None:
    """The declared normalization and conditional intervals apply equally to both systems."""
    assert bench.canonical('product_name', ' TEST Device® ') == bench.canonical('product_name', 'testdevice')
    assert bench.canonical('lot', 'LOT: AO1') != bench.canonical('lot', 'LOT: A01')
    assert bench.canonical('expiry', '2033/6/15') == '2033-06-15'
    assert bench.wilson(0, 4)[1] > 0.48
    records = [{'condition': 'hard', 'fields': {'lot': 'A1'}}]
    a = bench.summarize(records, [{'fields': {}}])
    b = bench.summarize(records, [{'fields': {'lot': 'LOT: A1'}}])
    before, after = {'manifest_sha256': 'same', 'totals': a}, {'manifest_sha256': 'same', 'totals': b}
    text, promote = bench.comparison(before, after)
    assert promote and 'PASS' in text
    assert not bench.comparison(after, before)[1]
    with pytest.raises(ValueError):
        bench.comparison(before, {**after, 'manifest_sha256': 'other'})
    p, q = tmp_path/'b.json', tmp_path/'a.json'
    p.write_text(json.dumps(before))
    q.write_text(json.dumps(after))
    assert bench.main(['--before', str(p), '--after', str(q), '--output', str(tmp_path/'report.md')]) == 0


def test_builder_pins_and_reproducibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Build toy artwork only; final source labels and final images are not evaluated in tests."""
    pytest.importorskip('cv2')
    image = pytest.importorskip('PIL.Image')
    monkeypatch.setattr(bench, 'ROOT', tmp_path)
    source = tmp_path/'toy.png'
    image.new('RGB', (80, 50), 'white').save(source)
    config = {'seed': 3, 'max_source_side': 80, 'dev_repetitions': 1, 'conditions': {'clean': 'clean'},
              'items': [{'id': 'toy', 'file': 'toy.png', 'family': 'one', 'split': 'dev',
                         'crop': [0, 0, 80, 50], 'fields': {'lot': 'TEST'},
                         'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]}
    first = bench.build_dataset(config, 'dev', tmp_path/'data')
    assert first == bench.build_dataset(config, 'dev', tmp_path/'data')
    assert first['records'][0]['fields'] == {'lot': 'TEST'}
    with pytest.raises(ValueError):
        bench.build_dataset({**config, 'seed': 4}, 'dev', tmp_path/'data')


def test_title_and_identifier_prefix() -> None:
    """A batch beginning with EXP remains whole and a category title outranks a logo."""
    from src.cv.photo_cv2 import observed_product_name

    blocks = [OcrBlock(text=t, bbox=box, conf=0.99) for t, box in [
        ('LOT', (0, 200, 30, 20)), ('EXP123ABC', (40, 200, 100, 20)),
        ('2033-06-15', (0, 250, 100, 20)), ('EXAMPLE', (300, 0, 200, 60)),
        ('TEST SPINAL', (10, 50, 150, 30)), ('PENCIL POINT', (10, 85, 160, 30))]]
    fields, _ = map_cv2_fields(blocks)
    assert fields['lot'] == 'LOT: EXP123ABC'
    assert fields['expiry'] == 'EXP: 2033-06-15'
    assert fields['product_name'] == 'TEST SPINAL PENCIL POINT'
    assert observed_product_name([]) is None


def test_predict_explicit_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Baseline stays explicitly selectable after a new default is promoted."""
    import sys

    seen = []

    def extractor(image: str, *, mode: str, postcorrect: bool, photo_profile: str = 'cv2') -> object:
        """Observe the profile instead of loading any CV engine."""
        seen.append(photo_profile)
        return SimpleNamespace(fields={'lot': 'LOT: TEST'}, warnings=[])

    monkeypatch.setitem(sys.modules, 'src.cv.extract', SimpleNamespace(extract_label=extractor))
    monkeypatch.setattr(sys, 'path', list(sys.path))
    assert bench.predict(('toy.png', '.', 'baseline'))['fields']['lot'] == 'LOT: TEST'
    assert seen == ['baseline']


def test_score_identical_pixels_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Repeated identical clean frames reuse predictions, keeping the predeclared frame denominator."""
    source = tmp_path/'one.png'
    source.write_bytes(b'toy bytes')
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    record = {'image': 'one.png', 'image_sha256': fingerprint, 'condition': 'clean', 'fields': {'lot': 'A1'}}
    (tmp_path/'manifest.json').write_text(json.dumps({'records': [record, record]}))
    seen = []

    class Pool:
        """Observe worker calls without starting real recognition."""

        def __init__(self, **kwargs: object) -> None:
            """Accept the executor's configuration."""

        def __enter__(self) -> Pool:
            """Enter this in-memory executor."""
            return self

        def __exit__(self, *args: object) -> None:
            """Leave this in-memory executor."""

        def map(self, function: object, tasks: object) -> list[dict[str, object]]:
            """Provide a single known observed value for each unique image."""
            seen.extend(tasks)
            return [{'fields': {'lot': 'LOT: A1'}} for _ in seen]

    monkeypatch.setattr(bench, 'ProcessPoolExecutor', Pool)
    result = tmp_path/'result.json'
    assert bench.main(['--dataset', str(tmp_path), '--output', str(result)]) == 0
    observed = json.loads(result.read_text())
    assert len(seen) == 1 and observed['unique_images'] == 1
    assert observed['totals']['clean']['complete']['k'] == 2
    with pytest.raises(FileExistsError):
        bench.main(['--dataset', str(tmp_path), '--output', str(result)])


def test_optional_engine_keeps_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unavailable second engine cannot promote an unscored fallback."""
    import shutil

    from src.cv.extract import resolve_photo_profile

    monkeypatch.setattr(shutil, 'which', lambda _: None)
    assert resolve_photo_profile('cv2') == 'baseline'
    assert resolve_photo_profile('upscale') == 'upscale'
    assert resolve_photo_profile('baseline') == 'baseline'
    monkeypatch.setattr(shutil, 'which', lambda _: '/optional/tesseract')
    assert resolve_photo_profile('cv2') == 'cv2'
    with pytest.raises(ValueError, match='Unknown'):
        resolve_photo_profile('typo')
