"""Extract sourced aliases and SPL labeler from pinned, fingerprint-verified XML."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

NS = {'s': 'urn:hl7-org:v3'}


def metadata(xml: bytes, row: dict[str, Any]) -> dict[str, Any]:
    """Return exact source strings and provenance; labeler is not necessarily the physical manufacturer."""
    if hashlib.sha256(xml).hexdigest() != row['xml_sha256']:
        raise ValueError('SPL fingerprint mismatch')
    root = ET.fromstring(xml)
    if root.find('s:setId', NS).get('root') != row['setid']:
        raise ValueError('SPL identity mismatch')
    if root.find('s:versionNumber', NS).get('value') != str(row['version']):
        raise ValueError('SPL version mismatch')
    url = row['url']
    values: dict[str, list[dict[str, str]]] = {'aliases': [], 'labelers': [], 'titles': []}
    paths = [('aliases', './/s:manufacturedProduct/s:manufacturedProduct/s:name'),
             ('aliases', './/s:genericMedicine/s:name'), ('titles', 's:title'),
             ('labelers', 's:author/s:assignedEntity/s:representedOrganization/s:name')]
    for key, xpath in paths:
        for node in root.findall(xpath, NS):
            value = ' '.join(' '.join(node.itertext()).split())
            if not value:
                continue
            values[key].append({'value': value, 'url': url, 'xpath': xpath,
                                'xml_sha256': row['xml_sha256'], 'effective_date': row['effective_date']})
    # Short display titles can be aliases; prescribing-information paragraphs cannot.
    values['aliases'] += [dict(v) for v in values['titles'] if len(v['value']) <= 120
                         and not re.fullmatch(r'[\d\W]+', v['value'])]
    return {'setid': row['setid'], 'version': row['version'], **values}


def enrich(directory: Path) -> dict[str, int]:
    """Generate metadata from every pinned product, failing rather than inventing missing sources."""
    rows = json.loads((directory/'products.json').read_text())
    output = [metadata((directory/'source'/f"{r['setid']}_v{r['version']}.xml").read_bytes(), r) for r in rows]
    (directory/'metadata.json').write_text(json.dumps(output, indent=2)+'\n')
    return {'products': len(output), 'aliases': sum(len(r['aliases']) for r in output)}


def expand(directory: Path, target: int = 30) -> dict[str, Any]:
    """Discover additional human-medicine SPLs, pin their bytes, and rebuild with the existing parser."""
    from scripts.real.build_medicine_corpus import build_corpus, fetch_xml, parse_product

    entries = json.loads((directory/'products.json').read_text())
    (directory/'source').mkdir(exist_ok=True)
    for entry in entries:
        path = directory/'source'/f"{entry['setid']}_v{entry['version']}.xml"
        if not path.exists():
            xml = fetch_xml(entry)
            parse_product(xml, entry)
            path.write_bytes(xml)
    # Discovery is fixed by requested ingredient, not query scores or model outcomes.
    ingredients = ['aspirin', 'cetirizine', 'losartan', 'lisinopril', 'sertraline', 'prednisone',
                   'gabapentin', 'escitalopram', 'amlodipine', 'doxycycline', 'furosemide',
                   'naproxen', 'fluoxetine', 'cephalexin', 'clopidogrel', 'pantoprazole',
                   'hydrochlorothiazide', 'allopurinol', 'montelukast', 'rosuvastatin']
    failures = []
    seen = {r['setid'] for r in entries}
    for ingredient in ingredients:
        if len(entries) >= target:
            break
        try:
            url = 'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?'+urlencode(
                {'drug_name': ingredient, 'pagesize': 1})
            with urlopen(Request(url, headers={'User-Agent': 'LabelLens-research'}), timeout=30) as response:
                item = json.load(response)['data'][0]
            if item['setid'] in seen:
                continue
            entry = {'setid': item['setid'], 'version': int(item['spl_version'])}
            xml = fetch_xml(entry)
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
            (directory/'source'/f"{entry['setid']}_v{entry['version']}.xml").write_bytes(xml)
            entries.append(entry)
            seen.add(entry['setid'])
        except Exception as exc:
            failures.append({'ingredient': ingredient, 'error': f'{type(exc).__name__}: {exc}'})
    summary = build_corpus(entries, directory, offline=True)
    (directory/'expansion.json').write_text(json.dumps({'summary': summary, 'failures': failures}, indent=2)+'\n')
    return summary


def main() -> None:
    """One command expands the local corpus if requested, then extracts pinned metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('data/medicine'))
    parser.add_argument('--expand', action='store_true')
    args = parser.parse_args()
    if args.expand:
        print(json.dumps(expand(args.directory)))
    print(json.dumps(enrich(args.directory)))


if __name__ == '__main__':
    main()
