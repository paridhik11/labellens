"""Score one frozen candidate against the pinned baseline without changing references."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]


def validate_inputs(folder: Path, protocol: dict[str, Any]) -> None:
    """Reject changed photos/references or a different scoring cohort."""
    names = {entry['filename'] for entry in protocol['cohort']}
    actual = {path.name for path in folder.glob('*.jpg')} | {'transcriptions.csv'}
    if names != actual:
        raise ValueError('Scoring cohort changed')
    for entry in protocol['cohort']:
        path = (folder / entry['filename']).resolve()
        if not path.is_relative_to(folder.resolve()):
            raise ValueError('Scoring input escapes its folder')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Scoring input fingerprint changed')


def run_evaluation(
    folder: Path, protocol: dict[str, Any], extractor: Callable[..., Any],
) -> dict[str, Any]:
    """Extract all images first, then score exact values and character errors."""
    from src.cv.eval_real import score

    validate_inputs(folder, protocol)
    observations = []
    for entry in protocol['cohort']:
        if entry['filename'] == 'transcriptions.csv':
            continue
        try:
            extracted = extractor(folder / entry['filename'], mode='blind', postcorrect=True)
            observations.append({'photo': entry['filename'], 'extraction': extracted.model_dump(), 'error': None})
        except Exception as error:
            observations.append({'photo': entry['filename'], 'extraction': {'fields': {}},
                                 'error': f'{type(error).__name__}: {error}'})
    with (folder / 'transcriptions.csv').open(newline='', encoding='utf-8-sig') as handle:
        references = {row['filename']: row for row in csv.DictReader(handle)}
    totals: dict[str, dict[str, int]] = {}
    for row in observations:
        reference = {field: references[row['photo']][field].strip()
                     for field in ('product_name', 'lot', 'expiry') if references[row['photo']][field].strip()}
        scores = score(reference, row['extraction']['fields'])
        row.update(reference=reference, scores=scores)
        for field, counts in scores.items():
            total = totals.setdefault(field, {'photos': 0, 'exact': 0, 'edits': 0, 'characters': 0, 'present': 0})
            total['photos'] += 1
            for key, value in counts.items():
                total[key] += value
    return {'protocol': protocol, 'condition': 'photo', 'reference_source': 'LLM-generated transcriptions',
            'human_spotcheck': 'DEFERRED', 'real_photo_symbol_accuracy': 'UNMEASURED',
            'totals': totals, 'rows': observations}


def render_comparison(before: dict[str, Any], after: dict[str, Any]) -> str:
    """Generate before/after numbers with unchanged inputs and explicit exposure limits."""
    if before['protocol'] != after['protocol']:
        raise ValueError('Cannot compare different protocols')
    lines = ['# Frozen-protocol real-photo comparison', '',
             'Condition: photo. Ten fixed device photographs. References: LLM-generated transcriptions.',
             'Human spot-check and symbol-crop human review deferred. Real-photo symbol accuracy unmeasured.',
             'Previously exposed convenience cohort, not an unseen holdout. No tuning on this scoring run.', '',
             f"Baseline: {before.get('code_commit', 'test')}. Candidate: {after.get('code_commit', 'test')}.", '',
             '| Field | Before exact | After exact | Before character edits | After character edits |',
             '|---|---|---|---|---|']
    for field in ('product_name', 'lot', 'expiry'):
        b, a = before['totals'][field], after['totals'][field]
        lines.append(f"| {field} | {b['exact']}/{b['photos']} | {a['exact']}/{a['photos']} | "
                     f"{b['edits']}/{b['characters']} | {a['edits']}/{a['characters']} |")
    lines += ['', 'An extraction exception remains a miss. Empty references are unscored.',
              'Exact matching preserves case, punctuation and printed date format; '
              'only printed field keys are removed.',
              'Improvement does not establish 80% real-world accuracy, human validation or approved-print accuracy.',
              'Choice: installed RapidOCR CPU, original and rectified views, quarter-turn search, overlapping crops,',
              'generic spatial keys and dates. No scoring-specific names or identifiers. Pari owns app integration.']
    return '\n'.join(lines) + '\n'


def main(argv: list[str] | None = None) -> int:
    """Run baseline/candidate extraction or generate the paired comparison report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=ROOT / 'data/real_photos/clear_online')
    parser.add_argument('--protocol', type=Path, default=ROOT / 'scripts/cv_experiments/photo_protocol_v1.json')
    parser.add_argument('--baseline-root', '--code-root', dest='baseline_root', type=Path)
    parser.add_argument('--revision', help='Exact revision of an archived code root')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--after', type=Path)
    args = parser.parse_args(argv)
    if args.before and args.after:
        text = render_comparison(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
        args.output.write_text(text)
        print(text)
        return 0
    protocol = json.loads(args.protocol.read_text())
    root = args.baseline_root or ROOT
    sys.path.insert(0, str(root))
    from src.cv.extract import extract_label

    result = run_evaluation(args.folder, protocol, extract_label)
    result['code_commit'] = args.revision or (
        protocol['baseline_commit'] if args.baseline_root else
        subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    )
    result['extractor_sha256'] = hashlib.sha256((root / 'src/cv/extract.py').read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['totals'], indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
