"""CV4b: fetch candidate photos CV4 never downloaded, from the same publisher feed in the same order.

CV4 downloaded the first 90 accepted images in feed order, and the 90th is ``new_90`` (a CV4 dataset record). The
feed pages are cached by ``curl`` in ``data/cv4b_photos/feed/`` (Python's urllib is answered with HTTP 429 by the
feed host from this machine; the images themselves download normally). Candidates here are the title-matching
products *after* new_90's product, first image only, minus any byte-identical image already in a frozen manifest.
No reference name is inferred from a catalog title or barcode.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

FEED = Path('data/cv4b_photos/feed')
OUTPUT = Path('data/cv4b_photos/candidates')
TITLE = re.compile(r'suture|catheter|introducer|dressing|syringe|cannula|stapler|guidewire', re.I)


def ordered_products() -> list[dict[str, Any]]:
    """Title-matching products with at least one image, in the feed order CV4 used."""
    products: list[dict[str, Any]] = []
    for page in sorted(FEED.glob('page_*.json'), key=lambda p: int(p.stem.split('_')[1])):
        for product in json.loads(page.read_text(encoding='utf-8'))['products']:
            if TITLE.search(product['title']) and product.get('images'):
                products.append(product)
    return products


def after_cv4(products: list[dict[str, Any]], dataset: Path = Path('src/gen/cv4_dataset.json')) -> list[dict[str, Any]]:
    """Products strictly after the one CV4 stopped at (new_90), so none was ever downloaded before."""
    records = json.loads(dataset.read_text(encoding='utf-8'))['records']
    last = next(r for r in records if r['filename'] == 'new_90.jpg')['family_hint_not_reference']
    handles = [p['handle'] for p in products]
    return products[handles.index(last)+1:]


def acquire(limit: int = 140) -> list[dict[str, Any]]:
    """Download up to ``limit`` unseen first images; every file is hashed and its source recorded."""
    from scripts.symbols.fetch_real_labels import get

    OUTPUT.mkdir(parents=True, exist_ok=True)
    known = {r['sha256'] for r in json.loads(Path('src/gen/cv4_dataset.json').read_text(encoding='utf-8'))['records']}
    rows: list[dict[str, Any]] = []
    for product in after_cv4(ordered_products()):
        media = product['images'][0]
        try:
            content = get(media['src'])
        except Exception as error:
            print('IMAGE_FAILED', product['handle'], str(error), flush=True)
            continue
        sha = hashlib.sha256(content).hexdigest()
        if sha in known or len(content) > 15_000_000:
            continue
        known.add(sha)
        name = f'fresh_{len(rows)+1:03d}.jpg'
        (OUTPUT/name).write_bytes(content)
        rows.append({'filename': name, 'sha256': sha, 'url': media['src'],
                     'source_page': 'https://primismedical.com/products/'+product['handle'],
                     'family_hint_not_reference': product['handle'],
                     'catalog_title_not_reference': product['title'],
                     'rights': 'Publisher rights retained; local research only; no image redistribution'})
        (OUTPUT/'acquisition.json').write_text(json.dumps(rows, indent=1)+'\n', encoding='utf-8')
        print(name, product['handle'], flush=True)
        if len(rows) >= limit:
            break
    return rows


if __name__ == '__main__':
    acquire()
