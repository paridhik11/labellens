"""Grouped split safety, interval arithmetic and one-use test-scoring guard."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.cv_experiments import eval_photo_split as split_eval


def test_partition_and_group_integrity(tmp_path: Path) -> None:
    """Only selected photo bytes and reference rows enter a partition."""
    source = tmp_path/'source'
    source.mkdir()
    (source/'a.jpg').write_bytes(b'development')
    (source/'b.jpg').write_bytes(b'test')
    (source/'transcriptions.csv').write_text('filename,product_name,lot,expiry\na.jpg,DEV,A1,2033-01\nb.jpg,TEST,B2,2034-01\n')
    split = {'baseline_commit': 'before', 'prior_exposure': 'previously exposed',
             'entries': [{'filename': name, 'group': name, 'split': part,
                          'sha256': hashlib.sha256((source/name).read_bytes()).hexdigest()}
                         for name, part in [('a.jpg', 'dev'), ('b.jpg', 'test')]]}
    protocol = split_eval.prepare_partition(split, source, tmp_path/'dev', 'dev')
    assert {p['filename'] for p in protocol['cohort']} == {'a.jpg', 'transcriptions.csv'}
    assert 'TEST' not in (tmp_path/'dev/transcriptions.csv').read_text()
    split['entries'][1]['group'] = 'a.jpg'
    with pytest.raises(ValueError, match='family'):
        split_eval.prepare_partition(split, source, tmp_path/'bad', 'test')
    split['entries'][1]['group'] = 'b.jpg'
    (source/'a.jpg').write_bytes(b'changed')
    with pytest.raises(ValueError, match='fingerprint'):
        split_eval.prepare_partition(split, source, tmp_path/'bad', 'dev')


def test_wilson_report_and_single_test_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One paired invocation is allowed; intervals do not collapse at zero or all correct."""
    result = {'protocol': {'same': True}, 'code_commit': 'frozen', 'totals': {
        name: {'photos': 4, 'exact': 0} for name in ('product_name', 'lot', 'expiry')}}
    after = {**result, 'totals': {name: {'photos': 4, 'exact': 4} for name in result['totals']}}
    report = split_eval.render_report(result, after, 'test')
    assert '0/4 (0.0% to 49.0%)' in report and '4/4 (51.0% to 100.0%)' in report
    with pytest.raises(ValueError):
        split_eval.render_report(result, {**after, 'protocol': {}}, 'test')
    catalog = tmp_path/'split.json'
    catalog.write_text('{}')
    output = tmp_path/'out'
    monkeypatch.setattr(split_eval, 'prepare_partition', lambda *args: {'same': True})

    def simulate(command: list[str], **kwargs: object) -> SimpleNamespace:
        """Write offline fixture outcomes for each archived-code subprocess."""
        target = Path(command[command.index('--output')+1])
        target.write_text(json.dumps(result if target.stem == 'before' else after))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(split_eval.subprocess, 'run', simulate)
    args = ['--partition', 'test', '--output', str(output), '--split', str(catalog),
            '--baseline-root', 'before', '--candidate-root', 'after', '--candidate-revision', 'frozen',
            '--report', str(tmp_path/'report.md')]
    # Main reads the baseline identity from the catalog.
    catalog.write_text(json.dumps({'baseline_commit': 'before'}))
    assert split_eval.main(args) == 0
    with pytest.raises(FileExistsError):
        split_eval.main(args)
