"""Grouped photo development and one-use paired test evaluation with Wilson intervals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.cv.intervals import wilson_interval

ROOT = Path(__file__).resolve().parents[2]


def prepare_partition(split: dict[str, Any], source: Path, output: Path, partition: str) -> dict[str, Any]:
    """Materialize one byte-identical partition, retaining whole families and AI provenance."""
    if partition not in {'dev', 'test'}:
        raise ValueError('Partition must be dev or test')
    groups: dict[str, set[str]] = {}
    for entry in split['entries']:
        groups.setdefault(entry['group'], set()).add(entry['split'])
    if any(len(assigned) != 1 for assigned in groups.values()):
        raise ValueError('Product family crosses dev/test')
    selected = [entry for entry in split['entries'] if entry['split'] == partition]
    if not selected:
        raise ValueError('Empty partition')
    expected = split.get('reference_sha256')
    if expected and hashlib.sha256((source/'transcriptions.csv').read_bytes()).hexdigest() != expected:
        raise ValueError('Reference transcriptions changed')
    output.mkdir(parents=True, exist_ok=True)
    with (source / 'transcriptions.csv').open(newline='', encoding='utf-8-sig') as handle:
        references = {row['filename']: row for row in csv.DictReader(handle)}
    cohort = []
    for entry in selected:
        path = (source / entry['filename']).resolve()
        if not path.is_relative_to(source.resolve()):
            raise ValueError('Photo path escapes source')
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != entry['sha256']:
            raise ValueError('Photo fingerprint changed')
        (output / path.name).write_bytes(content)
        cohort.append({'filename': path.name, 'sha256': entry['sha256']})
    csv_path = output / 'transcriptions.csv'
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['filename', 'product_name', 'lot', 'expiry'])
        writer.writeheader()
        writer.writerows(references[e['filename']] for e in selected)
    cohort.append({'filename': csv_path.name, 'sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest()})
    return {'cohort': cohort, 'baseline_commit': split['baseline_commit'], 'partition': partition,
            'reference_source': 'LLM-generated', 'prior_exposure': split['prior_exposure']}


def render_report(before: dict[str, Any], after: dict[str, Any], partition: str) -> str:
    """Render exact k/n with per-field Wilson intervals, without pooling conditions."""
    if before['protocol'] != after['protocol']:
        raise ValueError('Mismatched evaluation inputs')
    lines = [f'# Photo {partition}: frozen paired comparison', '',
             'Condition: photo. References: LLM-generated, human review deferred.',
             'Real-symbol accuracy unmeasured. Original photos were previously exposed, not an unseen holdout.',
             '', f"Before: {before['code_commit']}. After: {after['code_commit']}.", '',
             '| Field | Before exact (95% Wilson CI) | After exact (95% Wilson CI) |', '|---|---|---|']
    for field in ('product_name', 'lot', 'expiry'):
        cells = []
        for result in (before, after):
            total = result['totals'][field]
            k, n = total['exact'], total['photos']
            low, high = wilson_interval(k, n)
            cells.append(f'{k}/{n} ({100*low:.1f}% to {100*high:.1f}%)')
        lines.append(f'| {field} | {cells[0]} | {cells[1]} |')
    lines += ['', 'Intervals are descriptive marginal intervals, not paired-effect significance tests.',
              'Related layouts and the tiny convenience sample limit independence and generalization.',
              'Errors remain in denominators. Printed keys alone are removed; case/trademarks remain exact.',
              ('No checker threshold changed. No tuning followed the single test scoring invocation.'
               if partition == 'test' else 'Development-only selection; the test partition is not used for tuning.')]
    return '\n'.join(lines)+'\n'


def main(argv: list[str] | None = None) -> int:
    """Run dev freely or a single guarded paired test using frozen code directories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partition', choices=['dev', 'test'], required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'data/real_photos/clear_online')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--split', type=Path, default=ROOT/'scripts/cv_experiments/photo_split_v2.json')
    parser.add_argument('--baseline-root', type=Path, required=True)
    parser.add_argument('--candidate-root', type=Path, required=True)
    parser.add_argument('--candidate-revision', required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.partition == 'test':
        with (args.output/'test_scoring.lock').open('x') as lock:
            lock.write(args.candidate_revision+'\n')
    split = json.loads(args.split.read_text())
    folder = args.output/args.partition
    protocol = prepare_partition(split, args.source, folder, args.partition)
    protocol_path = args.output/'protocol.json'
    protocol_path.write_text(json.dumps(protocol, indent=2)+'\n')
    for tag, root, revision in [('before', args.baseline_root, split['baseline_commit']),
                                ('after', args.candidate_root, args.candidate_revision)]:
        command = [sys.executable, str(ROOT/'scripts/cv_experiments/eval_photo_protocol.py'),
                   '--folder', str(folder), '--protocol', str(protocol_path), '--code-root', str(root),
                   '--revision', revision, '--output', str(args.output/f'{tag}.json')]
        subprocess.run(command, check=True, cwd=ROOT)
    report = render_report(json.loads((args.output/'before.json').read_text()),
                           json.loads((args.output/'after.json').read_text()), args.partition)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report)
    print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
