"""CV4b: registered-name photo check with a hard per-photo deadline, dev diagnosis and fresh scoring.

OCR runs in a process-isolated worker (``run_bounded``), the name check runs afterwards in the parent, and a photo
the deadline cut short counts as ``timeout`` (never as a rejection that succeeded).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from scripts.cv_experiments.bounded import run_bounded
from scripts.cv_experiments.cv2_benchmark import wilson

ROOT = Path(__file__).resolve().parents[2]
CV4_DATASET = ROOT/'src/gen/cv4_dataset.json'
FRESH_DATASET = ROOT/'src/gen/cv4b_fresh.json'

# Candidate configurations. Only the keys listed here exist; a frozen one is copied to src/cv/cv4_release.json.
CONFIGS: dict[str, dict[str, Any]] = {
    'full': {'max_side': None, 'budget_s': None},                 # the CV4 pipeline unchanged (no deadline)
    'b1600': {'max_side': 1600, 'budget_s': 55.0},
    'c2': {'max_side': 1600, 'budget_s': 55.0, 'search_side': 800},   # cheap orientation search
    'b1200': {'max_side': 1200, 'budget_s': 55.0},
}


def predict(task: tuple[str, str, str]) -> dict[str, Any]:
    """Read one photo in blind mode with the named configuration; never sees names or references."""
    image, root, config_json = task
    sys.path.insert(0, root)
    config = json.loads(config_json)
    from src.cv.extract import extract_label

    start = time.monotonic()
    extra = {k: config[k] for k in ('max_side', 'budget_s', 'search_side') if config.get(k) is not None}
    extraction = extract_label(image, mode='blind', postcorrect=True, **extra)
    payload = {'ocr_blocks': [b.model_dump(mode='json') for b in extraction.ocr_blocks],
               'warnings': [w for w in extraction.warnings if 'TIME_BUDGET' in w or 'OCR' in w or 'DOWNSCALED' in w
                            or 'PROFILE' in w]}
    payload['elapsed_s'] = round(time.monotonic()-start, 2)
    return payload


def load_records(dataset: Path, split: str) -> list[dict[str, Any]]:
    """Records of one split, with source bytes checked against the frozen hash."""
    data = json.loads(dataset.read_text(encoding='utf-8'))
    rows = [r for r in data['records'] if r['split'] == split]
    for row in rows:
        path = ROOT/data['images_local']/row['filename']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f"Frozen source image changed: {row['filename']}")
    return rows


def collect(dataset: Path, split: str, config: str, workers: int, timeout: float, output: Path) -> list[dict[str, Any]]:
    """Run (or resume) one immutable prediction per photo and journal it."""
    data = json.loads(dataset.read_text(encoding='utf-8'))
    records = load_records(dataset, split)
    tasks = [(str((ROOT/data['images_local']/r['filename']).resolve()), str(ROOT),
              json.dumps(CONFIGS[config], sort_keys=True)) for r in records]
    fingerprint = hashlib.sha256(json.dumps({'records': records, 'tasks': tasks, 'config': config},
                                            sort_keys=True).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    return run_bounded(tasks, workers=workers, timeout=timeout, journal=output/f'{split}_{config}.jsonl',
                       fingerprint=fingerprint, predict=predict)


def outcome(prediction: dict[str, Any], expected: str) -> dict[str, Any]:
    """Name check for one photo: found, not_found or timeout (deadline or worker failure)."""
    from src.common.schemas import OcrBlock
    from src.cv.known_product import check_name

    error = prediction.get('error')
    if error and 'Timeout' not in error:  # a crash is a failure of the harness, never a timeout or a rejection
        raise RuntimeError(f'Prediction failed: {error}')
    if error or any(w.startswith('OCR_TIME_BUDGET') for w in prediction.get('warnings', [])):
        return {'status': 'timeout', 'reason': error or 'OCR_TIME_BUDGET', 'elapsed_s': prediction.get('elapsed_s')}
    blocks = [OcrBlock.model_validate(b) for b in prediction['ocr_blocks']]
    result = check_name(expected, blocks)
    return {'status': result['status'], 'matched_line': result['matched_line'], 'similarity': result['similarity'],
            'elapsed_s': prediction.get('elapsed_s')}


def summarize(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Counts, Wilson intervals and latency for one outcome column."""
    n = len(rows)
    count = {s: sum(r[key]['status'] == s for r in rows) for s in ('found', 'not_found', 'timeout')}
    times = sorted(r[key]['elapsed_s'] for r in rows if r[key].get('elapsed_s') is not None)
    return {'n': n, **count, 'found_ci95': wilson(count['found'], n),
            'median_s': statistics.median(times) if times else None,
            'p90_s': times[min(len(times)-1, int(0.9*len(times)))] if times else None,
            'max_s': times[-1] if times else None}


def score_dev(config: str, workers: int, timeout: float, output: Path) -> dict[str, Any]:
    """Dev split: registered name vs the same photo (found rate) and vs another dev product (false found)."""
    records = load_records(CV4_DATASET, 'dev')
    predictions = collect(CV4_DATASET, 'dev', config, workers, timeout, output)
    rows = []
    for record, prediction in zip(records, predictions, strict=True):
        rows.append({'filename': record['filename'], 'name': record['name'],
                     'known': outcome(prediction, record['name']),
                     'wrong': outcome(prediction, record['dev_wrong_name']),
                     'elapsed_s': prediction.get('elapsed_s')})
    return {'config': config, 'known': summarize(rows, 'known'), 'wrong': summarize(rows, 'wrong'), 'rows': rows}


def score_fresh(config: str, workers: int, timeout: float, output: Path) -> dict[str, Any]:
    """Fresh set: positives are checked against their own name, negatives against their frozen paired name."""
    out: dict[str, Any] = {'config': config}
    for split, key in (('positive', 'known'), ('negative', 'wrong')):
        records = load_records(FRESH_DATASET, split)
        predictions = collect(FRESH_DATASET, split, config, workers, timeout, output)
        rows = [{'filename': r['filename'], key: outcome(p, r['name'] if split == 'positive' else r['query_name']),
                 'elapsed_s': p.get('elapsed_s')} for r, p in zip(records, predictions, strict=True)]
        out[split] = {'summary': summarize(rows, key), 'rows': rows}
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--set', choices=['dev', 'fresh'], required=True)
    parser.add_argument('--config', choices=sorted(CONFIGS), required=True)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--timeout', type=float, default=60.0)
    parser.add_argument('--output', type=Path, default=Path('results/cv4b'))
    args = parser.parse_args()
    result = (score_dev if args.set == 'dev' else score_fresh)(args.config, args.workers, args.timeout, args.output)
    path = args.output/f'{args.set}_{args.config}_scored.json'
    path.write_text(json.dumps(result, indent=1)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=1)[:3000])
