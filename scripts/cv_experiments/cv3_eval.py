"""Frozen CV3 image-only predictions, dev selection and one held-out evaluation."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from scripts.cv_experiments.bounded import run_bounded
from scripts.cv_experiments.cv2_benchmark import wilson

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / 'src/gen/cv3_dataset.json'


def canonical(field: str, value: str) -> str:
    """Apply frozen normalization without correcting identifiers or fuzzy title matching."""
    value = re.sub(r'^\s*(?:LOT|BATCH|EXP|EXPIRY|USE BY)\s*:\s*', '', value, flags=re.I).strip()
    if field == 'product_name':
        return re.sub(r'\s+', '', value.casefold())
    if field == 'expiry':
        match = re.fullmatch(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', value)
        if match:
            try:
                return date(*map(int, match.groups())).isoformat()
            except ValueError:
                pass
    return value


def summarize(records: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Count every readable reference, including errors, and report printed OCR separately."""
    totals: dict[str, Any] = {}
    for row, prediction in zip(records, predictions, strict=True):
        fields = prediction.get('fields', {})
        condition = totals.setdefault(row.get('condition', 'photo'), {})
        for kind in ('effective', 'printed'):
            cells = condition.setdefault(kind, {})
            for field, expected in row['fields'].items():
                if field not in ('product_name', 'lot', 'expiry'):
                    continue
                key = f'prefill_{field}' if kind == 'effective' else f'printed_{field}'
                fallback = (prediction.get('details', {}).get('raw_fields', fields)
                            if kind == 'printed' else fields)
                observed = fields.get(key, fallback.get(field, ''))
                cell = cells.setdefault(field, {'k': 0, 'n': 0})
                cell['n'] += 1
                cell['k'] += int(canonical(field, observed) == canonical(field, expected))
    for condition in totals.values():
        for cells in condition.values():
            for cell in cells.values():
                cell['ci95'] = wilson(cell['k'], cell['n'])
    return totals


def improves(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Require an effective-field gain without losing printed or effective counts."""
    changes = []
    for condition, groups in before.items():
        for kind, cells in groups.items():
            for field, cell in cells.items():
                other = after[condition][kind][field]
                if cell['n'] != other['n']:
                    raise ValueError('Scoring populations differ')
                if other['k'] < cell['k']:
                    return False
        for field, cell in groups['effective'].items():
            other = after[condition]['effective'][field]
            changes.append(other['k']-cell['k'])
    return bool(changes) and min(changes) >= 0 and max(changes) > 0


def release_gate(before: dict[str, Any], after: dict[str, Any]) -> tuple[bool, list[str]]:
    """Reject any real/synthetic field loss or suppressed safety flag; require a gain.

    Both printed-only and effective counts are protected. Wilson intervals are
    descriptive; this gate compares exact counts, not significance claims.
    """
    from src.common.schemas import LabelExtraction
    from src.cv.consistency import check_extraction

    reasons = []
    gain = False
    for split in ('test', 'synthetic'):
        for condition, groups in before[split]['totals'].items():
            for kind, cells in groups.items():
                for field, cell in cells.items():
                    other = after[split]['totals'][condition][kind][field]
                    if cell['n'] != other['n'] or other['k'] < cell['k']:
                        reasons.append(f'{split}/{condition}/{kind}/{field} regressed or population differs')
                    gain |= kind == 'effective' and other['k'] > cell['k']
    if not gain:
        reasons.append('No effective held-out or synthetic field gain')
    a, b = before['synthetic']['safety'], after['synthetic']['safety']
    if len(a) != 6 or [r['filename'] for r in a] != [r['filename'] for r in b]:
        reasons.append('Incomplete or different safety cases')
    else:
        for old, new in zip(a, b, strict=True):
            if old['prediction'].get('error') or new['prediction'].get('error'):
                reasons.append('Safety extraction failed')
                continue
            old_flags = check_extraction(LabelExtraction.model_validate(old['prediction']))
            new_flags = check_extraction(LabelExtraction.model_validate(new['prediction']))
            required = {f.flag_id for f in old_flags if f.kind == 'barcode_mismatch'}
            found = {f.flag_id for f in new_flags if f.kind == 'barcode_mismatch'}
            if not required <= found:
                reasons.append(f"Safety mismatch suppressed: {old['filename']}")
    return not reasons, reasons


def predict(task: tuple[str, str, str]) -> dict[str, Any]:
    """Extract one photo without any reference values; preserve complete observed evidence."""
    image, root, stage_string = task
    sys.path.insert(0, root)
    from src.cv.extract import extract_label_modes

    options = json.loads(stage_string)
    stage = options['stage'] if isinstance(options, dict) else int(options)
    kwargs = {'cv3_stage': stage} if 'cv3_stage' in inspect.signature(extract_label_modes).parameters else {}
    if isinstance(options, dict):
        kwargs['cv3_prefill'] = options['prefill']
    if stage and not kwargs:
        raise ValueError('Requested stage absent from archived extractor')
    extraction, details = extract_label_modes(image, modes=('blind',), postcorrect=True, **kwargs)['blind']
    return {**extraction.model_dump(), 'details': details}


def build_synthetic(output: Path) -> list[dict[str, Any]]:
    """Render fixed fresh seeds plus separate deliberate print/barcode conflict safety cases."""
    from PIL import Image

    from src.gen.augment import augment_label
    from src.gen.smoke_label import build_label

    manifest = output / 'manifest.json'
    if manifest.exists():
        return json.loads(manifest.read_text())
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for condition in ('clean', 'moderate', 'hard'):
        for seed in range(12000, 12016):
            day = seed % 28 + 1
            month = seed % 12 + 1
            expiry = f'2028-{month:02d}-{day:02d}'
            lot = f'R{seed}X{seed % 97:02d}'
            fields = {'product_name': f'TEST SENSOR {seed}', 'lot': f'LOT: {lot}', 'expiry': f'EXP: {expiry}'}
            for safety in (False, True) if seed < 12002 else (False,):
                name = f'test_cv3_{condition}_{seed}' + ('_conflict' if safety else '')
                ais = {'10': 'OTHERLOT' if safety else lot,
                       '17': '311231' if safety else f'28{month:02d}{day:02d}'}
                generated = build_label(output/'source', label_id=name, field_values=fields,
                                        barcode_ais=ais, allow_print_barcode_mismatch=safety)
                with Image.open(generated['image']) as original:
                    photo, _, _ = augment_label(original.convert('RGB'), condition, seed)
                path = output / f'{name}.png'
                photo.save(path)
                records.append({'filename': str(path.resolve()), 'condition': condition,
                                'fields': fields, 'seed': seed, 'safety': safety,
                                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest.write_text(json.dumps(records, indent=2)+'\n')
    return records


def evaluate(split: str, stage: int, root: Path, output: Path, *, prefill: bool = True) -> dict[str, Any]:
    """Run one immutable journal with equal per-photo deadlines and descriptive intervals."""
    output.mkdir(parents=True, exist_ok=True)
    if split == 'synthetic':
        records = build_synthetic(ROOT / 'data/cv3_synthetic')
    else:
        dataset = json.loads(DATASET.read_text())
        records = [r for r in dataset['records'] if r['split'] == split]
        records = [{**r, 'filename': str((ROOT / dataset['images_local'] / r['filename']).resolve())} for r in records]
    for row in records:
        if hashlib.sha256(Path(row['filename']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Frozen image changed')
    options = str(stage) if prefill else json.dumps({'stage': stage, 'prefill': False})
    tasks = [(r['filename'], str(root.resolve()), options) for r in records]
    fingerprint = hashlib.sha256(json.dumps({'records': records, 'stage': stage, 'root': str(root),
                                            **({'prefill': False} if not prefill else {})},
                                           sort_keys=True).encode()).hexdigest()
    suffix = f'stage{stage}' + ('_noprefill' if not prefill else '')
    journal = output / f'{split}_{suffix}.jsonl'
    predictions = run_bounded(tasks, workers=2, timeout=300, journal=journal,
                              fingerprint=fingerprint, predict=predict)
    normal = [(r, p) for r, p in zip(records, predictions, strict=True) if not r.get('safety')]
    summary = {'split': split, 'stage': stage, 'fingerprint': fingerprint,
               'totals': summarize([r for r, _ in normal], [p for _, p in normal]),
               'errors': sum(bool(p.get('error')) for p in predictions),
               'prefilled_photos': sum(any(k.startswith('prefill_') for k in p.get('fields', {})) for p in predictions)}
    summary['safety'] = [{'filename': r['filename'], 'prediction': p}
                         for r, p in zip(records, predictions, strict=True) if r.get('safety')]
    (output / f'{split}_{suffix}_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'safety'}, indent=2), flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['dev', 'test', 'synthetic'], required=True)
    parser.add_argument('--stage', type=int, choices=range(5), required=True)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, default=Path('results/cv3'))
    parser.add_argument('--without-prefill', action='store_true')
    args = parser.parse_args()
    evaluate(args.split, args.stage, args.root, args.output, prefill=not args.without_prefill)
