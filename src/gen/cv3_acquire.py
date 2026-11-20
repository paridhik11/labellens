"""Acquire new online device-package candidates with source hashes; never infer reference text."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def acquire(output: Path, limit: int = 45) -> list[dict[str, Any]]:
    """Use the existing online source and polite fetcher, rejecting exact old-image duplicates."""
    from scripts.symbols.fetch_real_labels import get

    output.mkdir(parents=True, exist_ok=True)
    seen = set()
    for folder in ['data/real_photos', 'data/real', 'data/real_labels']:
        for path in Path(folder).rglob('*'):
            if path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
                seen.add(hashlib.sha256(path.read_bytes()).hexdigest())
    rows = []
    for page in range(1, 7):
        url = f'https://primismedical.com/products.json?limit=250&page={page}'
        try:
            products = json.loads(get(url)).get('products', [])
        except Exception as exc:
            print('SOURCE_FAILED', url, type(exc).__name__, str(exc), flush=True)
            continue
        for product in products:
            if not re.search(r'suture|catheter|introducer|dressing|syringe|cannula|stapler|guidewire',
                             product['title'], re.I):
                continue
            # One view per product at acquisition; visually audit label readability before inclusion.
            for media in product.get('images', [])[:1]:
                try:
                    with urlopen(Request(media['src'], headers={'User-Agent': 'LabelLens-research'}),
                                 timeout=30) as response:
                        image = response.read(15_000_001)
                    if len(image) > 15_000_000:
                        continue
                    sha = hashlib.sha256(image).hexdigest()
                    if sha in seen:
                        continue
                    seen.add(sha)
                    name = f'candidate_{len(rows)+1:02d}.jpg'
                    (output/name).write_bytes(image)
                    rows.append({'filename': name, 'sha256': sha, 'url': media['src'],
                                 'source_page': 'https://primismedical.com/products/'+product['handle'],
                                 'catalog_title_not_reference': product['title'], 'family': product['handle'],
                                 'rights': 'Publisher rights retained; local research only; no redistribution',
                                 'review': 'NOT_RUN; candidate not yet admitted as photo/reference'})
                    (output/'acquisition.json').write_text(json.dumps(rows, indent=2)+'\n')
                    print(name, product['title'], flush=True)
                except Exception as exc:
                    print('IMAGE_FAILED', type(exc).__name__, str(exc), flush=True)
                if len(rows) >= limit:
                    return rows
    return rows


def fetch_frozen(manifest: Path, output: Path) -> int:
    """Re-fetch immutable selected source bytes, rejecting a changed publisher image."""
    from scripts.symbols.fetch_real_labels import get

    output.mkdir(parents=True, exist_ok=True)
    records = json.loads(manifest.read_text())['records']
    for row in records:
        target = output / row['filename']
        content = target.read_bytes() if target.exists() else get(row['url'])
        if hashlib.sha256(content).hexdigest() != row['sha256']:
            raise ValueError(f"Frozen source changed: {row['filename']}")
        if not target.exists():
            target.write_bytes(content)
    return len(records)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    if args.frozen:
        print('Verified sources:', fetch_frozen(Path('src/gen/cv3_dataset.json'),
                                                Path('data/cv3_photos/candidates')))
    else:
        acquire(Path('data/cv3_photos/candidates'))
