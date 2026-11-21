"""Frozen known-product matching, literal evidence, optional-model fallback and professional isolation."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.api.known_name import check_registered_name
from src.api.main import create_app
from src.common.schemas import LabelExtraction, OcrBlock
from src.cv.known_product import check_name, coverage, line_groups, tokens
from src.cv.ocr_modern import modern_engine, modern_lines, modern_rows
from tests.checker_api_helpers import h, install
from tests.upload_helpers import passing_gate, png_bytes, upload


def block(text: str, x: float = 10, y: float = 10, conf: float = .99) -> OcrBlock:
    """Create independent observed text, with realistic line dimensions."""
    return OcrBlock(text=text, bbox=(x, y, 240, 20), conf=conf)


def test_normalization_and_one_to_one_tokens() -> None:
    """Trademarks/case normalize; model digits and repeated tokens cannot be guessed."""
    assert tokens('TRÉMO® XT-17™') == ['trémo', 'xt', '17']
    assert coverage(['brand', 'brand'], ['brand'])[0] == .5
    assert not coverage(['17'], ['18'])[1]
    assert coverage(['brand'], ['bramd'])[0] == .8
    assert not coverage(['catheter'], ['catheter'])[1]
    assert coverage([], [])[0] == 0


def test_literal_evidence_thresholds_and_wrong_product() -> None:
    """A close observed name can match, while generic, weak and different names abstain."""
    observed = block('ACME Flowmex™ 17')
    found = check_name('Acme Flowmax 17', [observed])
    assert found['status'] == 'found' and found['matched_line'] == observed.text
    assert found['confidence'] == .99 and found['evidence'][0]['text'] == observed.text
    assert found['similarity'] == pytest.approx(12/13)
    for name, lines in [('Acme Flowmax 18', [observed]), ('Other Flowmax 17', [observed]),
                        ('Catheter kit', [block('CATHETER KIT')]), ('Acme Flow 17', []),
                        ('Acme Flow 17', [block('Acme Flow 17', conf=.799)])]:
        result = check_name(name, lines)
        assert result['status'] == 'not_found' and result['matched_line'] is None


def test_adjacent_lines_not_distant_or_disjoint_columns() -> None:
    """Multi-line evidence is local and exact; distant unrelated words cannot satisfy a name."""
    lines = [block('ACME'), block('Flow Catheter', y=35)]
    assert max(map(len, line_groups(lines))) == 2
    found = check_name('ACME Flow Catheter', lines)
    assert found['status'] == 'found' and found['matched_line'] == 'ACME\nFlow Catheter'
    assert check_name('ACME Flow Catheter', [lines[0], block('Flow Catheter', y=200)])['status'] == 'not_found'
    assert check_name('ACME Flow Catheter', [lines[0], block('Flow Catheter', x=500, y=35)])['status'] == 'not_found'


def test_registered_context_never_invents_or_mutates_blind() -> None:
    """Registered names are comparison inputs, never replacements for missing OCR."""
    blind = LabelExtraction(label_id='photo', fields={'product_name': 'invented blind candidate', 'lot': 'LOT: A7'},
                            ocr_blocks=[block('Other Product')])
    checked, result = check_registered_name(blind, 'ACME Flow')
    assert result['status'] == 'not_found' and 'product_name' not in checked.fields
    assert blind.fields['product_name'] == 'invented blind candidate'
    assert checked.fields['lot'] == blind.fields['lot'] and checked.ocr_blocks == blind.ocr_blocks


def test_modern_output_and_missing_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Modern rows preserve text/geometry; all optional-library/model failures retain old evidence."""
    result = SimpleNamespace(boxes=[[[1, 2], [11, 2], [11, 12], [1, 12]]],
                             txts=['Actual OCR'], scores=[.95])
    assert modern_rows(result, 20, 20)[0].bbox == (1, 2, 10, 10)
    assert modern_rows(SimpleNamespace(boxes=None, txts=None), 20, 20) == []
    monkeypatch.delenv('LABELLENS_CV4_MODELS', raising=False)
    old = [block('Old evidence')]
    assert modern_lines(tmp_path/'absent.jpg', old)[0] is old
    rows, reason = modern_lines(tmp_path/'absent.jpg', old, model_dir=str(tmp_path))
    assert rows is old and reason.startswith('cv2_fallback:')
    with pytest.raises((ImportError, FileNotFoundError)):
        modern_engine(str(tmp_path))


def test_upload_stores_known_product_check_and_preserves_confirmation(tmp_path: Path,
                                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """A product-bound scan exposes pinned-name evidence without adding a shared schema field."""
    with TestClient(create_app('sqlite://', seed=True)) as client:
        stub = install(client, tmp_path, monkeypatch)
        client.app.state.quality_gate = passing_gate
        response = upload(client, png_bytes(), h())
        assert response.status_code == 202, response.text
        scan = client.get(response.json()['result_url'], headers=h()).json()
        extraction = client.get(f"/label-versions/{scan['version_id']}/extraction", headers=h()).json()
        check = extraction['known_product_name_check']
        assert check['status'] == 'found' and check['product_version'] >= 1
        assert check['matched_line'] == stub.record['name']
        assert json.loads(json.dumps(check))['evidence']
        confirmed = client.post(f"/label-versions/{scan['version_id']}/extraction/confirm",
                                json={'fields': {'product_name': 'HUMAN CONFIRMED NAME'}}, headers=h()).json()
        assert confirmed['fields']['product_name'] == 'HUMAN CONFIRMED NAME'
        assert confirmed['known_product_name_check']['applies_to'] == 'original_ocr'
        assert confirmed['known_product_name_check']['matched_line'] == check['matched_line']


def test_acquisition_excludes_prior_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Known CV3 bytes never enter the new acquisition, and title text is not a reference."""
    from scripts.symbols import fetch_real_labels
    from src.gen.cv4_acquire import acquire

    old = tmp_path/'data/cv3_photos/old.jpg'
    old.parent.mkdir(parents=True)
    old.write_bytes(b'old')
    products = [{'title': 'Catheter', 'handle': 'catheter', 'images': [{'src': url}]} for url in ['old', 'new']]

    def get(url: str) -> bytes:
        """Return deterministic fake publisher responses without networking."""
        return json.dumps({'products': products}).encode() if url.startswith('https') else url.encode()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(fetch_real_labels, 'get', get)
    rows = acquire(tmp_path/'output', limit=1)
    assert len(rows) == 1 and rows[0]['url'] == 'new' and 'fields' not in rows[0]


def test_not_found_upload_requires_name_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unrelated blind guess is removed and the missing registered name remains reviewable."""
    with TestClient(create_app('sqlite://', seed=True)) as client:
        stub = install(client, tmp_path, monkeypatch)
        stub.fields['product_name'] = 'OTHER BRAND DEVICE'
        client.app.state.quality_gate = passing_gate
        response = upload(client, png_bytes(), h())
        scan = client.get(response.json()['result_url'], headers=h()).json()
        extraction = client.get(f"/label-versions/{scan['version_id']}/extraction", headers=h()).json()
        assert extraction['known_product_name_check']['status'] == 'not_found'
        assert 'product_name' not in extraction['fields'] and 'product_name' in extraction['unclear_fields']


def test_selected_modern_engine_is_separate_name_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Only a dev-selected modern reader can supply name evidence; other fields keep their original source."""
    from src.api import known_name
    from src.cv import ocr_modern

    choice = tmp_path/'release.json'
    choice.write_text(json.dumps({'engine': 'ppocrv6'}))
    monkeypatch.setattr(known_name, 'RELEASE_PATH', choice)
    modern = [block('ACME Flow')]
    monkeypatch.setattr(ocr_modern, 'modern_lines', lambda path, fallback: (modern, 'ppocrv6_small'))
    original = LabelExtraction(label_id='x', fields={'lot': 'LOT: ORIGINAL'}, ocr_blocks=[block('old OCR')])
    updated, result = check_registered_name(original, 'ACME Flow', image=tmp_path/'image.png')
    assert result['engine'] == 'ppocrv6_small' and updated.fields['product_name'] == 'ACME Flow'
    assert updated.fields['lot'] == 'LOT: ORIGINAL' and updated.ocr_blocks == original.ocr_blocks
    choice.write_text(json.dumps({'engine': 'cv2'}))
    assert check_registered_name(original, 'ACME Flow', image=tmp_path/'image.png')[1]['status'] == 'not_found'
