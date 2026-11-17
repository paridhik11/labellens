"""Pinned DailyMed augmentation benchmark; predictions receive images only, never references."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT/'scripts/cv_experiments/config/cv2.json'


def canonical(field: str, value: str) -> str:
    """Normalize declared formats equally for both systems, without fuzzy reference matching."""
    value = re.sub(r'^\s*(?:LOT|BATCH|EXP|EXPIRY|USE BY)\s*:\s*', '', value, flags=re.I).strip()
    if field == 'product_name':
        return re.sub(r'\s+', '', value.casefold().replace('®', '').replace('™', ''))
    if field == 'expiry':
        match = re.fullmatch(r'(\d{4})[-/.](\d{1,2})(?:[-/.](\d{1,2}))?', value)
        if match:
            year, month = int(match[1]), int(match[2])
            day = int(match[3]) if match[3] else 1
            try:
                date(year, month, day)
                return f'{year:04d}-{month:02d}' + (f'-{day:02d}' if match[3] else '')
            except ValueError:
                pass
    return re.sub(r'\s+', '', value)


def wilson(k: int, n: int) -> list[float] | None:
    """Return descriptive Wilson 95% frame-conditional bounds, not product-generalization bounds."""
    if n == 0:
        return None
    z = 1.959963984540054
    p = k/n
    centre = (p+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [max(0.0, centre-half), min(1.0, centre+half)]


def build_dataset(config: dict[str, Any], split: str, output: Path) -> dict[str, Any]:
    """Render fixed crops with fixed seeds and retained source provenance; never inject content."""
    import numpy as np
    from PIL import Image

    from src.gen.augment import augment_label_detailed

    families: dict[str, set[str]] = {}
    for item in config['items']:
        families.setdefault(item['family'], set()).add(item['split'])
    if any(len(parts) > 1 for parts in families.values()):
        raise ValueError('Artwork family crosses development/final split')
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    path = output/'manifest.json'
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest['config_sha256'] != fingerprint or manifest['split'] != split:
            raise ValueError('Refusing to mix benchmark configurations')
        return manifest
    if output.exists() and any(output.iterdir()):
        raise ValueError('Nonempty dataset without a manifest')
    output.mkdir(parents=True, exist_ok=True)
    records = []
    repeats = config['final_repetitions'] if split == 'final' else config['dev_repetitions']
    for index, item in enumerate(config['items']):
        if item['split'] != split:
            continue
        source = ROOT/item['file']
        if hashlib.sha256(source.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Source artwork fingerprint changed')
        with Image.open(source) as original:
            crop = original.convert('RGB').crop(item['crop'])
        scale = config['max_source_side']/max(crop.size)
        crop = crop.resize((max(2, round(crop.width*scale)), max(2, round(crop.height*scale))))
        for repetition in range(repeats):
            for condition, effect in config['conditions'].items():
                seed = int(np.random.SeedSequence([config['seed'], index, repetition]).generate_state(1)[0])
                image, matrix, corners, effects = augment_label_detailed(crop, effect, seed)
                name = f"{item['id']}_{repetition:02d}_{condition}.png"
                image.save(output/name)
                records.append({'image': name, 'condition': condition, 'source': item['id'],
                                'family': item['family'], 'fields': item['fields'], 'seed': seed,
                                'image_sha256': hashlib.sha256((output/name).read_bytes()).hexdigest(),
                                'homography': matrix.tolist(), 'corners': corners, 'effects': effects})
    manifest = {'config_sha256': fingerprint, 'split': split, 'reference_source': 'LLM-generated',
                'condition_scope': 'photo-like transformed device artwork; not real phone captures', 'records': records}
    path.write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def predict(task: tuple[str, str, str]) -> dict[str, Any]:
    """Run one archived extractor in a spawned worker; the task contains no ground truth."""
    image, root, profile = task
    sys.path.insert(0, root)
    from src.cv.extract import extract_label

    try:
        kwargs = {'photo_profile': profile} if 'photo_profile' in inspect.signature(extract_label).parameters else {}
        if not kwargs and profile != 'baseline':
            raise ValueError('Archived extractor does not support the requested candidate')
        extraction = extract_label(image, mode='blind', postcorrect=True, **kwargs)
        return {'fields': extraction.fields, 'warnings': extraction.warnings}
    except Exception as error:
        return {'fields': {}, 'error': f'{type(error).__name__}: {error}'}


def summarize(records: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Score all references after extraction, per condition/field, including every failure."""
    totals: dict[str, Any] = {}
    for record, prediction in zip(records, predictions, strict=True):
        condition = totals.setdefault(record['condition'], {'complete': {'k': 0, 'n': 0}, 'fields': {}})
        complete = True
        for field, expected in record['fields'].items():
            observed = prediction.get('fields', {}).get(field, '')
            normalized = canonical(field, observed) == canonical(field, expected)
            raw = re.sub(r'^(?:LOT|EXP):\s*', '', observed) == expected
            cell = condition['fields'].setdefault(field, {'k': 0, 'n': 0, 'strict_k': 0})
            cell['n'] += 1
            cell['k'] += int(normalized)
            cell['strict_k'] += int(raw)
            complete = complete and normalized
        condition['complete']['n'] += 1
        condition['complete']['k'] += int(complete)
    for condition in totals.values():
        for cell in [condition['complete'], *condition['fields'].values()]:
            cell['ci95'] = wilson(cell['k'], cell['n'])
    return totals


def comparison(before: dict[str, Any], after: dict[str, Any]) -> tuple[str, bool]:
    """Apply the predeclared gate without selecting or tuning a second candidate."""
    if before['manifest_sha256'] != after['manifest_sha256']:
        raise ValueError('Different final frames')
    conditions = before['totals']
    wins = [after['totals'][c]['complete']['k']-before['totals'][c]['complete']['k'] for c in conditions]
    promote = all(delta >= 0 for delta in wins) and any(delta > 0 for delta in wins)
    lines = ['# CV2 fresh transformed-artwork result', '',
             'LLM-generated references. Human review deferred. Real symbols unmeasured.',
             'Framewise conditional Wilson intervals; repeated artwork is not independent product validation.', '',
             '| Condition | Complete before (95% CI) | Complete after (95% CI) |', '|---|---|---|']
    for c in conditions:
        cells = []
        for result in (before, after):
            cell = result['totals'][c]['complete']
            lo, hi = cell['ci95']
            cells.append(f"{cell['k']}/{cell['n']} ({lo:.3f} to {hi:.3f})")
        lines.append(f'| {c} | {cells[0]} | {cells[1]} |')
    lines += ['', f'Predeclared release gate: {"PASS" if promote else "FAIL; retain baseline"}.', '',
              '| Condition | Field | Before | After | Strict before/after |', '|---|---|---|---|---|']
    for c in conditions:
        for field, b in before['totals'][c]['fields'].items():
            a = after['totals'][c]['fields'][field]
            lines.append(f"| {c} | {field} | {b['k']}/{b['n']} ({b['ci95'][0]:.3f} to {b['ci95'][1]:.3f}) "
                         f"| {a['k']}/{a['n']} ({a['ci95'][0]:.3f} to {a['ci95'][1]:.3f}) "
                         f"| {b['strict_k']}/{a['strict_k']} |")
    return '\n'.join(lines)+'\n', promote


def main(argv: list[str] | None = None) -> int:
    """Build or score immutable frames, or compare the two single scoring outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--dataset', type=Path)
    parser.add_argument('--split', choices=['dev', 'final'], default='dev')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--code-root', type=Path, default=ROOT)
    parser.add_argument('--profile', choices=['baseline', 'upscale', 'cv2'], default='baseline')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--resume', action='store_true', help='Resume the identical durable prediction journal')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--after', type=Path)
    args = parser.parse_args(argv)
    if args.before and args.after:
        text, promote = comparison(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
        args.output.write_text(text)
        print(text)
        return int(not promote)
    config = json.loads(args.config.read_text())
    if args.build:
        manifest = build_dataset(config, args.split, args.output)
        print(json.dumps({'images': len(manifest['records']), 'split': args.split}))
        return 0
    manifest_path = args.dataset/'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    if args.output.exists():
        raise FileExistsError('Scoring output is immutable; do not rescore final data')
    lock = args.output.with_suffix('.lock')
    if not args.resume:
        with lock.open('x') as handle:
            handle.write(args.profile+'\n')
    elif not lock.exists():
        raise ValueError('No scoring lock to resume')
    tasks = {}
    for record in manifest['records']:
        path = args.dataset/record['image']
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['image_sha256']:
            raise ValueError('Frame fingerprint changed')
        tasks.setdefault(record['image_sha256'], (str(path.resolve()), str(args.code_root.resolve()), args.profile))
    code_hash = hashlib.sha256()
    for source in sorted((args.code_root/'src/cv').glob('*.py')):
        code_hash.update(source.name.encode()+source.read_bytes())
    fingerprint = hashlib.sha256((hashlib.sha256(manifest_path.read_bytes()).hexdigest()+
                                  code_hash.hexdigest()+args.profile+str(args.timeout)).encode()).hexdigest()
    from scripts.cv_experiments.bounded import run_bounded

    observations = run_bounded(list(tasks.values()), workers=args.workers, timeout=args.timeout,
                               journal=args.output.with_suffix('.predictions.jsonl'),
                               fingerprint=fingerprint, predict=predict)
    unique = dict(zip(tasks, observations, strict=True))
    predictions = [unique[record['image_sha256']] for record in manifest['records']]
    result = {'timeout_seconds': args.timeout, 'unique_images': len(tasks),
              'cv_source_sha256': code_hash.hexdigest(), 'python': sys.version,
              'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(), 'profile': args.profile,
              'totals': summarize(manifest['records'], predictions), 'predictions': predictions,
              'failures': sum('error' in p for p in predictions)}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'totals': result['totals'], 'failures': result['failures']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
