"""Photo-level symbol presence evaluation using user-confirmed annotations."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CONFIG = Path('scripts/cv_experiments/config/confirmed_photo_symbols.json')


def score_presence(expected: list[list[str]], predicted: list[set[str]], names: list[str]) -> dict[str, Any]:
    """Count each photo/class once; absent predictions remain misses, without localization claims."""
    result = {}
    for name in names:
        tp = fp = fn = tn = 0
        for reference, observed in zip(expected, predicted, strict=True):
            present, detected = name in reference, name in observed
            tp += int(present and detected)
            fp += int(not present and detected)
            fn += int(present and not detected)
            tn += int(not present and not detected)
        result[name] = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
                        'precision': tp/(tp+fp) if tp+fp else None,
                        'recall': tp/(tp+fn) if tp+fn else None}
    return result


def evaluate(config: dict[str, Any], folder: Path) -> dict[str, Any]:
    """Run the deployed v1 blind detector on original RGB photos with unchanged defaults."""
    import numpy as np
    from PIL import Image

    from src.cv.symbols import NAMES, detect_symbols_blind

    rows = []
    for item in config['photos']:
        path = folder/item['filename']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Photo fingerprint changed: '+item['filename'])
        with Image.open(path) as image:
            pixels = np.asarray(image.convert('RGB'))
        try:
            found = [d.model_dump() for d in detect_symbols_blind(pixels)]
            error = None
        except Exception as exc:
            found, error = [], f'{type(exc).__name__}: {exc}'
        rows.append({**item, 'detections': found, 'error': error})
    metrics = score_presence([r['present'] for r in rows],
                             [{d['name'] for d in r['detections']} for r in rows], config['categories'])
    return {'condition': 'photo', 'scope': 'whole-original-image presence; not extractor or bounding-box accuracy',
            'provenance': config['provenance'], 'supported': list(NAMES),
            'unsupported': [n for n in config['categories'] if n not in NAMES],
            'metrics': metrics, 'rows': rows}


def main(argv: list[str] | None = None) -> int:
    """Evaluate once and retain observations, configuration and code fingerprints for audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--folder', type=Path, default=Path('data/real_photos/clear_online'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('Use a new output; do not overwrite frozen observations')
    result = evaluate(json.loads(args.config.read_text()), args.folder)
    result['config_sha256'] = hashlib.sha256(args.config.read_bytes()).hexdigest()
    result['detector_sha256'] = hashlib.sha256(Path('src/cv/symbols.py').read_bytes()).hexdigest()
    result['reference_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(Path('data/symbols/device').glob('test_*.png'))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'metrics': result['metrics'], 'unsupported': result['unsupported'],
                      'errors': sum(r['error'] is not None for r in result['rows'])}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
