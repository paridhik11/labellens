"""Golden demo determinism, documented renderer paths and persistent prototype warnings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

for _module in ('cv2', 'PIL', 'zxingcpp', 'reportlab', 'pypdf'):
    pytest.importorskip(_module)

from PIL import Image  # noqa: E402

from src.gen.golden import build_golden, main, verify_golden  # noqa: E402


def test_three_golden_packages(tmp_path: Path) -> None:
    """Actual PDF/SVG/QR exports are deterministic, immutable, visibly warned and decode-checked."""
    source = tmp_path/'toy.png'
    Image.new('RGB', (100, 70), 'white').save(source)
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()
    kwargs = {'source_image': source, 'source_sha256': fingerprint, 'source_fields': {'product_name': 'TOY'}}
    manifest = build_golden(tmp_path/'first', **kwargs)
    assert len(manifest['packages']) == 3
    assert build_golden(tmp_path/'first', **kwargs) == manifest
    second = build_golden(tmp_path/'second', **kwargs)
    assert second['files'] == manifest['files']
    changed = json.loads((tmp_path/'first/barcode_change/expected.json').read_text())
    assert changed['barcode_action'] == 'REGENERATE' and changed['record']['extra']['lot'] == 'TESTLOT2'
    assert changed['approval'] == 'NOT_ISSUED'
    assert verify_golden(tmp_path/'first') == manifest
    (tmp_path/'first/synthetic/label.svg').write_text('tampered')
    with pytest.raises(ValueError, match='changed'):
        verify_golden(tmp_path/'first')
    with pytest.raises(ValueError, match='source'):
        build_golden(tmp_path/'bad', **{**kwargs, 'source_sha256': 'wrong'})
    with pytest.raises(SystemExit):
        main(['--help'])
