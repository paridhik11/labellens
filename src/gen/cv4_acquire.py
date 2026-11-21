"""Acquire unseen package candidates using the existing public-photo fetch pipeline."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def acquire(output: Path, limit: int = 90) -> list[dict[str, Any]]:
    """Reject all prior real-photo bytes and freeze candidate URLs without inferred references."""
    from scripts.symbols.fetch_real_labels import get

    output.mkdir(parents=True, exist_ok=True)
    seen = set()
    for folder in ('data/real', 'data/real_photos', 'data/real_labels', 'data/cv3_photos'):
        for path in Path(folder).rglob('*'):
            if path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                seen.add(hashlib.sha256(path.read_bytes()).hexdigest())
    rows: list[dict[str, Any]] = []
    for page in range(1, 9):
        try:
            products = json.loads(get(f'https://primismedical.com/products.json?limit=250&page={page}'))['products']
        except Exception as error:
            print('FEED_FAILED', page, str(error), flush=True)
            continue
        for product in products:
            if not re.search(r'suture|catheter|introducer|dressing|syringe|cannula|stapler|guidewire',
                             product['title'], re.I):
                continue
            for media in product.get('images', [])[:1]:
                try:
                    content = get(media['src'])
                    sha = hashlib.sha256(content).hexdigest()
                    if sha in seen or len(content) > 15_000_000:
                        continue
                    seen.add(sha)
                    name = f'new_{len(rows)+1:02d}.jpg'
                    (output/name).write_bytes(content)
                    rows.append({'filename': name, 'sha256': sha, 'url': media['src'],
                                 'source_page': 'https://primismedical.com/products/'+product['handle'],
                                 'family_hint_not_reference': product['handle'],
                                 'catalog_title_not_reference': product['title'],
                                 'rights': 'Publisher rights retained; local research only; no image redistribution'})
                    (output/'acquisition.json').write_text(json.dumps(rows, indent=2)+'\n')
                    print(name, product['title'], flush=True)
                except Exception as error:
                    print('IMAGE_FAILED', str(error), flush=True)
                if len(rows) >= limit:
                    return rows
    return rows


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    if args.frozen:
        from src.gen.cv3_acquire import fetch_frozen

        print('Verified:', fetch_frozen(Path('src/gen/cv4_dataset.json'), Path('data/cv4_photos/candidates')))
    else:
        acquire(Path('data/cv4_photos/candidates'))
