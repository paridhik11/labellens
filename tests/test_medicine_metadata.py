"""SPL metadata values have source evidence and never come from a handwritten alias map."""
import hashlib
import json
from pathlib import Path

import pytest

from src.gen.eval_medicine_aliases import summarize
from src.gen.medicine import load_medicine_metadata
from src.gen.medicine_metadata import enrich, metadata


def test_sourced_metadata(tmp_path: Path) -> None:
    """Read literal brand/generic/title and labeler values, preserving the labeler's actual role."""
    xml = b'''<document xmlns="urn:hl7-org:v3"><setId root="id"/><versionNumber value="2"/>
    <title>Source Brand</title><author><assignedEntity><representedOrganization><name>Source Labeler</name>
    </representedOrganization></assignedEntity></author><manufacturedProduct><manufacturedProduct>
    <name>Source Brand</name><asEntityWithGeneric><genericMedicine><name>Source Generic</name></genericMedicine>
    </asEntityWithGeneric></manufacturedProduct></manufacturedProduct></document>'''
    row = {'setid': 'id', 'version': 2, 'xml_sha256': hashlib.sha256(xml).hexdigest(),
           'url': 'https://dailymed.nlm.nih.gov/example', 'effective_date': '2026-11-21'}
    result = metadata(xml, row)
    assert {v['value'] for v in result['aliases']} == {'Source Brand', 'Source Generic'}
    assert result['labelers'][0]['value'] == 'Source Labeler'
    assert result['labelers'][0]['url'] == row['url']
    with pytest.raises(ValueError):
        metadata(xml+b' ', row)
    (tmp_path/'products.json').write_text(json.dumps([row]))
    (tmp_path/'source').mkdir()
    (tmp_path/'source/id_v2.xml').write_bytes(xml)
    assert enrich(tmp_path)['products'] == 1
    assert load_medicine_metadata(tmp_path)['id']['version'] == 2
    result['labelers'][0]['url'] = 'wrong'
    (tmp_path/'metadata.json').write_text(json.dumps([result]))
    with pytest.raises(ValueError, match='source mismatch'):
        load_medicine_metadata(tmp_path)


def test_strict_decoy_gate() -> None:
    """Even a needs-review decoy candidate blocks promotion rather than hiding a wrong suggestion."""
    row = {'kind': 'decoy', 'predicted': 'wrong', 'expected': '',
           'result': {'outcome': 'needs_review', 'candidates': [['id', 0.66]]}}
    assert not summarize([row])['gate_passed']
    row['result'] = {'outcome': 'no_reference_match', 'candidates': []}
    assert summarize([row])['gate_passed']


def test_expansion_preserves_pinned_products(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An already-full catalog rebuilds from pinned data without new discovery."""
    from scripts.real import build_medicine_corpus as builder
    from src.gen.medicine_metadata import expand

    (tmp_path/'products.json').write_text(json.dumps([{'setid': 'existing', 'version': 1}]))
    (tmp_path/'source').mkdir()
    (tmp_path/'source/existing_v1.xml').write_bytes(b'pinned')
    monkeypatch.setattr(builder, 'build_corpus', lambda rows, *a, **k: {'products': len(rows)})
    assert expand(tmp_path, target=1) == {'products': 1}
    assert json.loads((tmp_path/'expansion.json').read_text())['failures'] == []
