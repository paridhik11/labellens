"""Expand the pinned medicine corpus from a committed candidate list (med100), with the existing parser.

Discovery is fixed by `data/medicine/med100_candidates.tsv` (order and rule are committed before any fetch).
For each ingredient: DailyMed `drug_name` search, the first three results, the first one that passes
`parse_product` and the single-product checks below is pinned. Failures are recorded, never retried.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from scripts.real.build_medicine_corpus import build_corpus, fetch_xml, parse_product
from src.gen.medicine_metadata import NS, enrich

SEARCH = 'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?'
RESULTS_PER_INGREDIENT = 3


def read_candidates(path: Path) -> list[str]:
    """Ingredient names in committed order (comment lines start with #)."""
    lines = [ln for ln in path.read_text(encoding='utf-8').splitlines() if ln and not ln.startswith('#')]
    return [row['ingredient'] for row in csv.DictReader(lines, delimiter='\t')]


def check_ingredient(xml: bytes, ingredient: str) -> None:
    """Raise unless the label has one product name and one generic name, and names the requested ingredient."""
    root = ET.fromstring(xml)
    generics = {' '.join(' '.join(n.itertext()).split()).lower()
                for n in root.findall('.//s:genericMedicine/s:name', NS)}
    names = {' '.join(' '.join(n.itertext()).split()).lower()
             for n in root.findall('.//s:manufacturedProduct/s:manufacturedProduct/s:name', NS)}
    if len(generics) != 1:
        raise ValueError(f'expected one generic name, found {len(generics)}')
    if not any(re.search(rf'\b{re.escape(ingredient)}', text) for text in generics | names):
        raise ValueError('requested ingredient not in product or generic name')


def search_results(ingredient: str) -> list[dict[str, Any]]:
    """The first DailyMed search results for a drug name."""
    url = SEARCH + urlencode({'drug_name': ingredient, 'pagesize': RESULTS_PER_INGREDIENT})
    with urlopen(Request(url, headers={'User-Agent': 'LabelLens-research'}), timeout=30) as response:
        return json.load(response)['data']


def pin_entry(item: dict[str, Any], ingredient: str) -> tuple[dict[str, Any], bytes]:
    """Fetch one SPL, run every check and return the catalog entry plus the XML bytes."""
    entry: dict[str, Any] = {'setid': item['setid'], 'version': int(item['spl_version'])}
    xml = fetch_xml(entry)
    check_ingredient(xml, ingredient)
    root = ET.fromstring(xml)
    names = {' '.join(' '.join(n.itertext()).split()) for n in root.findall(
        './/s:manufacturedProduct/s:manufacturedProduct/s:name', NS)}
    if len(names) != 1:
        raise ValueError('Multiple product names')
    effective = root.find('s:effectiveTime', NS).get('value')[:8]
    entry.update(product_name=next(iter(names)), xml_sha256=hashlib.sha256(xml).hexdigest(),
                 effective_date=f'{effective[:4]}-{effective[4:6]}-{effective[6:]}',
                 fetched=date.today().isoformat())
    parse_product(xml, entry)
    return entry, xml


def expand100(directory: Path, candidates: Path, total: int = 100) -> dict[str, Any]:
    """Pin new products until `total` is reached, record failures and rebuild corpus and metadata."""
    entries = json.loads((directory / 'products.json').read_text())
    source = directory / 'source'
    source.mkdir(exist_ok=True)
    for entry in entries:  # pinned originals are re-fetched when absent, fingerprint checked by parse_product
        path = source / f"{entry['setid']}_v{entry['version']}.xml"
        if not path.exists():
            xml = fetch_xml(entry)
            parse_product(xml, entry)
            path.write_bytes(xml)
    seen = {r['setid'] for r in entries}
    start = len(entries)
    added, failures = [], []
    for ingredient in read_candidates(candidates):
        if len(entries) >= total:
            break
        try:
            results = search_results(ingredient)
        except Exception as exc:
            failures.append({'ingredient': ingredient, 'setid': '', 'error': f'search {type(exc).__name__}: {exc}'})
            continue
        if not results:
            failures.append({'ingredient': ingredient, 'setid': '', 'error': 'no search results'})
        for item in results:
            if item['setid'] in seen:
                failures.append({'ingredient': ingredient, 'setid': item['setid'], 'error': 'already pinned'})
                continue
            try:
                entry, xml = pin_entry(item, ingredient)
            except Exception as exc:
                failures.append({'ingredient': ingredient, 'setid': item['setid'],
                                 'error': f'{type(exc).__name__}: {exc}'})
                continue
            (source / f"{entry['setid']}_v{entry['version']}.xml").write_bytes(xml)
            entries.append(entry)
            seen.add(entry['setid'])
            added.append({'ingredient': ingredient, 'product_name': entry['product_name'], 'setid': entry['setid']})
            print(len(entries), ingredient, entry['product_name'], flush=True)
            break
        else:
            failures.append({'ingredient': ingredient, 'setid': '', 'error': 'no result passed the checks'})
    summary = build_corpus(entries, directory, offline=True)
    (directory / 'expansion100.json').write_text(json.dumps(
        {'start': start, 'summary': summary, 'added': added, 'failures': failures}, indent=2) + '\n')
    summary['metadata'] = enrich(directory)
    summary['failures'] = len(failures)
    return summary


def main() -> None:
    """Command line entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('data/medicine'))
    parser.add_argument('--candidates', type=Path, default=Path('data/medicine/med100_candidates.tsv'))
    parser.add_argument('--total', type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(expand100(args.directory, args.candidates, args.total)))


if __name__ == '__main__':
    main()
