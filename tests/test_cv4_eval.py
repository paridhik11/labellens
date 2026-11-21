"""CV4 evaluation isolation, fallback and once-only journal checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.cv_experiments import cv4_eval as bench
from src.common.schemas import LabelExtraction, OcrBlock


def test_score_and_gate_with_fallback() -> None:
    """Expected names reach matching only after OCR; missing modern models use real old observations."""
    rows = [{'filename': 'x.jpg', 'split': 'test', 'name': 'ACME Flow', 'dev_wrong_name': 'Other Flow'}]
    old = [{'fields': {'product_name': 'Generic thing'}, 'ocr_blocks': [
        OcrBlock(text='ACME Flow', bbox=(0, 0, 200, 20), conf=.99).model_dump()]}]
    result = bench.score(rows, old, [{'fallback_required': True}])
    assert result['found'] == 1 and result['blind_exact'] == 0 and result['dev_false_found'] == 0
    assert result['fallbacks'] == 1 and not result['errors']
    failed = bench.score(rows, [{'error': 'timeout', 'fields': {}}])
    assert failed['fallbacks'] == 0 and failed['errors'] == 1 and failed['found'] == 0
    good = {'n': 10, 'found': 5, 'blind_exact': 0, 'errors': 0}
    negative = {'n': 15, 'found': 0, 'errors': 0}
    assert bench.release_gate(good, negative)[0]
    assert not bench.release_gate(good, {**negative, 'found': 1})[0]
    assert not bench.release_gate(good, {**negative, 'errors': 1})[0]
    assert not bench.release_gate({**good, 'found': 0}, negative)[0]
    assert not bench.release_gate({**good, 'n': 9}, negative)[0]


def test_complete_observations_only(tmp_path: Path) -> None:
    """A partial or duplicated journal is never silently rescored or accepted."""
    path = tmp_path/'journal.jsonl'
    path.write_text(json.dumps({'fingerprint': 'fake'})+'\n'+json.dumps({'index': 0, 'result': {'fields': {}}})+'\n')
    assert bench.observations(path, 1) == [{'fields': {}}]
    with pytest.raises(ValueError, match='incomplete'):
        bench.observations(path, 2)
    path.write_text(path.read_text()+json.dumps({'index': 0, 'result': {}})+'\n')
    with pytest.raises(ValueError, match='duplicate'):
        bench.observations(path, 1)


def test_worker_and_evaluation_task_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A prediction task contains only pixels, code root and engine choice."""
    from src.cv import extract

    seen = []

    def fake(image: str, **kwargs: Any) -> LabelExtraction:
        """Capture recognizer arguments without loading models or references."""
        seen.append((image, kwargs))
        return LabelExtraction(label_id='fake')

    monkeypatch.setattr(extract, 'extract_label', fake)
    assert bench.predict(('pixels.jpg', str(tmp_path), 'cv2'))['label_id'] == 'fake'
    assert seen[0][1] == {'mode': 'blind', 'postcorrect': True}
    with pytest.raises(ValueError, match='Unknown'):
        bench.predict(('pixels.jpg', str(tmp_path), 'no_such_engine'))
    photo = tmp_path/'pixels.jpg'
    photo.write_bytes(b'pixels')
    dataset = tmp_path/'dataset.json'
    dataset.write_text(json.dumps({'images_local': str(tmp_path), 'records': [
        {'filename': photo.name, 'split': 'dev', 'name': 'SECRET REFERENCE',
         'sha256': hashlib.sha256(b'pixels').hexdigest()}]}))
    monkeypatch.setattr(bench, 'DATASET', dataset)
    tasks_seen = []

    def bounded(tasks: Any, **kwargs: Any) -> list[dict[str, Any]]:
        """Observe task isolation without running native inference."""
        tasks_seen.extend(tasks)
        return [{'fields': {}}]

    monkeypatch.setattr(bench, 'run_bounded', bounded)
    assert bench.evaluate('dev', 'cv2', tmp_path, tmp_path/'results') == [{'fields': {}}]
    assert 'SECRET' not in str(tasks_seen) and len(tasks_seen[0]) == 3


def test_frozen_dataset_and_family_separation() -> None:
    """All 45 admitted photos are distinct and no family crosses protocol splits."""
    dataset = json.loads(Path('src/gen/cv4_dataset.json').read_text())
    records = dataset['records']
    assert {s: sum(r['split'] == s for r in records) for s in ['dev', 'test', 'negative']} == {
        'dev': 20, 'test': 10, 'negative': 15}
    assert len({r['sha256'] for r in records}) == 45
    families = {s: {r['family'] for r in records if r['split'] == s} for s in ['dev', 'test', 'negative']}
    assert not families['dev'] & families['test']
    assert not (families['dev'] | families['test']) & families['negative']
    for record in records:
        if record['split'] == 'negative':
            assert record['query_name'] != record['name']
        assert 'LLM' in record['reference_provenance']
