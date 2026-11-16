"""Real artwork remains local, reproducible and separate from photo evaluation."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest


def test_no_tracked_real_label_images() -> None:
    """Only synthetic reference PNGs, never downloaded DailyMed/real-label media, are versioned."""
    paths = subprocess.check_output(['git', 'ls-files', 'data'], text=True).splitlines()
    media = [p for p in paths if Path(p).suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip'}]
    assert set(media) <= {'data/symbols/device/test_manufacturer.png', 'data/symbols/device/test_expiry.png'}


def test_supplement_rebuild(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline archive validation and deterministic documented cropping use no network."""
    pytest.importorskip('PIL')
    from PIL import Image

    from scripts.real import fetch_extra_artwork as extra

    data = b'explicit synthetic PDF test fixture'
    monkeypatch.setattr(extra, 'SHA256', hashlib.sha256(data).hexdigest())
    (tmp_path/'curisoft_notice.pdf').write_bytes(data)

    def render(command: list[str], **kwargs: object) -> None:
        """Create a synthetic rendered page instead of invoking a PDF process."""
        Image.new('RGB', (1273, 1800), 'white').save(Path(command[-1]).with_suffix('.png'))

    monkeypatch.setattr(extra.subprocess, 'run', render)
    result = extra.fetch_artwork(tmp_path, offline=True)
    assert result['images'] == 2 and result['condition'] == 'artwork'
    assert {entry['split'] for entry in result['entries']} == {'dev'}
    assert extra.main(['--output', str(tmp_path), '--offline']) == 0
    (tmp_path/'curisoft_notice.pdf').write_bytes(b'changed')
    with pytest.raises(ValueError, match='fingerprint'):
        extra.fetch_artwork(tmp_path, offline=True)
    with pytest.raises(FileNotFoundError):
        extra.fetch_artwork(tmp_path/'absent', offline=True)
