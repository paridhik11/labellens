"""Execute the exact public handoff example so signatures and payloads stay usable."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

for _name in ('cv2', 'PIL', 'zxingcpp', 'reportlab', 'pypdf'):
    pytest.importorskip(_name)


def test_handoff_example(tmp_path: Path) -> None:
    """A documented confirmed REGENERATE reaches physical PDF/SVG/QR with draft markings."""
    from pypdf import PdfReader

    document = Path('docs/GEN_HANDOFF.md').read_text()
    code = next(block for block in re.findall(r'```python\n(.*?)```', document, re.S) if 'def example(' in block)
    namespace = {}
    exec(compile(code, 'docs/GEN_HANDOFF.md', 'exec'), namespace)
    result = namespace['example'](tmp_path/'draft')
    assert result['barcode_decision'] == 'REGENERATE' and result['status'] == 'DRAFT'
    assert 'DRAFT, not for production' in PdfReader(result['files']['pdf']).pages[0].extract_text()
    assert 'DRAFT, not for production' in Path(result['files']['svg']).read_text()
    assert Path(result['files']['qr']).is_file()
