"""Verify photo-level scoring and the fixed human-confirmed annotation scope."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.cv_experiments import eval_confirmed_symbols as module


def test_presence_counts() -> None:
    """Duplicate detection boxes do not inflate photo-level correctness."""
    metrics = module.score_presence([['expiry'], ['manufacturer'], []],
                                    [{'expiry'}, set(), {'expiry'}], ['expiry', 'manufacturer', 'sterile_r'])
    assert metrics['expiry'] == {'tp': 1, 'fp': 1, 'fn': 0, 'tn': 1, 'precision': 0.5, 'recall': 1}
    assert metrics['manufacturer']['fn'] == 1
    assert metrics['sterile_r']['precision'] is None and metrics['sterile_r']['recall'] is None
    with pytest.raises(ValueError):
        module.score_presence([[]], [], ['expiry'])


def test_confirmed_config() -> None:
    """The six-class photo annotations retain their user-reported assisted provenance."""
    config = json.loads(module.CONFIG.read_text())
    assert config['provenance']['method'] == 'AI-assisted, human-confirmed'
    assert len(config['photos']) == len({p['filename'] for p in config['photos']}) == 10
    totals = {n: sum(n in p['present'] for p in config['photos']) for n in config['categories']}
    assert list(totals.values()) == [4, 9, 8, 1, 9, 5]


def test_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI retains protocol/code hashes and rejects accidental result overwrite."""
    monkeypatch.setattr(module, 'evaluate', lambda *args: {'metrics': {}, 'unsupported': [], 'rows': []})
    output = tmp_path/'observations.json'
    assert module.main(['--output', str(output)]) == 0
    assert len(json.loads(output.read_text())['config_sha256']) == 64
    with pytest.raises(FileExistsError):
        module.main(['--output', str(output)])
