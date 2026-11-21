"""CV4 image-only OCR journals; registered-name checks run separately after OCR."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from scripts.cv_experiments.bounded import run_bounded
from scripts.cv_experiments.cv2_benchmark import wilson

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT/'src/gen/cv4_dataset.json'


def predict(task: tuple[str, str, str]) -> dict[str, Any]:
    """Receive image/root/profile only, never product names or reference annotations."""
    image, root, profile = task
    sys.path.insert(0, root)
    if profile == 'cv2':
        from src.cv.extract import extract_label

        extraction = extract_label(image, mode='blind', postcorrect=True)
        return extraction.model_dump(mode='json')
    if profile != 'ppocrv6':
        raise ValueError('Unknown OCR profile')
    from src.cv.ocr_modern import modern_lines

    blocks, source = modern_lines(Path(image), [])
    return {'ocr_blocks': [b.model_dump(mode='json') for b in blocks], 'engine': source,
            'fallback_required': source != 'ppocrv6_small', 'fields': {}}


def evaluate(split: str, profile: str, root: Path, output: Path) -> list[dict[str, Any]]:
    """Collect one immutable prediction per photo, with symmetric process deadlines."""
    dataset = json.loads(DATASET.read_text())
    records = [r for r in dataset['records'] if r['split'] == split]
    images = [ROOT/dataset['images_local']/r['filename'] for r in records]
    for image, row in zip(images, records, strict=True):
        if hashlib.sha256(image.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Frozen source image changed')
    tasks = [(str(image.resolve()), str(root.resolve()), profile) for image in images]
    fingerprint = hashlib.sha256(json.dumps({'dataset': dataset, 'tasks': tasks}, sort_keys=True).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    return run_bounded(tasks, workers=2, timeout=300, journal=output/f'{split}_{profile}.jsonl',
                       fingerprint=fingerprint, predict=predict)


def observations(path: Path, count: int) -> list[dict[str, Any]]:
    """Read complete existing predictions without rerunning OCR or losing timeout observations."""
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    indexed = {r['index']: r['result'] for r in rows[1:]}
    if len(indexed) != count or len(rows) != count+1:
        raise ValueError('Journal incomplete or duplicate indices')
    return [indexed[i] for i in range(count)]


def score(
    records: list[dict[str, Any]], baseline: list[dict[str, Any]], modern: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score names using references only after extraction; failed negatives cannot pass a gate."""
    from src.common.schemas import OcrBlock
    from src.cv.known_product import check_name, tokens

    rows = []
    for i, (record, old) in enumerate(zip(records, baseline, strict=True)):
        new = modern[i] if modern is not None else old
        fallback = modern is not None and bool(new.get('fallback_required') or new.get('error'))
        prediction = old if fallback else new
        blocks = [OcrBlock.model_validate(b) for b in prediction.get('ocr_blocks', [])]
        expected = record.get('query_name', record['name'])
        name_check = check_name(expected, blocks)
        wrong_check = check_name(record['dev_wrong_name'], blocks) if 'dev_wrong_name' in record else None
        rows.append({'filename': record['filename'], 'split': record['split'],
                     'known': name_check, 'dev_wrong': wrong_check,
                     'blind_exact': tokens(old.get('fields', {}).get('product_name', '')) == tokens(record['name']),
                     'fallback': fallback, 'error': prediction.get('error')})
    k = sum(r['known']['status'] == 'found' for r in rows)
    blind = sum(r['blind_exact'] for r in rows)
    wrong = [r['dev_wrong'] for r in rows if r['dev_wrong'] is not None]
    return {'n': len(rows), 'found': k, 'found_ci95': wilson(k, len(rows)),
            'blind_exact': blind, 'blind_ci95': wilson(blind, len(rows)),
            'dev_false_found': sum(r['status'] == 'found' for r in wrong),
            'errors': sum(bool(r['error']) for r in rows), 'fallbacks': sum(r['fallback'] for r in rows),
            'rows': rows}


def release_gate(positive: dict[str, Any], negative: dict[str, Any]) -> tuple[bool, list[str]]:
    """Apply the frozen count-based gate; failures never masquerade as successful negative checks."""
    reasons = []
    if positive['n'] != 10 or negative['n'] != 15:
        reasons.append('Incomplete held-out population')
    if positive['found'] <= positive['blind_exact']:
        reasons.append('Right-product found rate does not beat CV2 blind names')
    if negative['found'] != 0:
        reasons.append('Wrong-product false found is not zero')
    if positive['errors'] or negative['errors']:
        reasons.append('Held-out OCR failure leaves incomplete evidence')
    return not reasons, reasons


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=['dev', 'test', 'negative'], required=True)
    parser.add_argument('--profile', choices=['cv2', 'ppocrv6'], required=True)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, default=Path('results/cv4'))
    args = parser.parse_args()
    evaluate(args.split, args.profile, args.root, args.output)
