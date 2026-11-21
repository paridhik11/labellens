"""Fixed print-template benchmark; final seeds never enter the verifier."""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any


def run(output: Path, *, final: bool = False) -> list[dict[str, Any]]:
    """Render correct and three different-label variants, then score immutable observations."""
    from PIL import Image

    from scripts.step25b_print_eval import RECORD, render_page
    from src.api.printverify import RealPrintEngine, outcome_of
    from src.common.schemas import ProductRecord
    from src.export.pdf import render_pdf
    from src.export.template import from_product
    from src.gen.augment import augment_label_detailed

    if output.exists():
        raise FileExistsError('Refusing to rerun or overwrite frozen scoring output')
    output.mkdir(parents=True)
    template = json.loads(Path('src/gen/templates/test_device.json').read_text())
    data = {**RECORD, 'product_id': 'print-eval'}
    record = ProductRecord.model_validate(data)
    label = from_product(template, record, version_id='print-eval', actor='eval', reason='test', test_data=True)
    fields = {'product_name': record.name, 'model': record.model, 'manufacturer': record.manufacturer,
              'manufacturer_address': record.manufacturer_address, 'lot': record.extra['lot'],
              'expiry': record.extra['expiry']}
    barcode = next(e for e in label.elements if e.kind == 'barcode')
    import re

    ais = dict(re.findall(r'\((\d{2})\)([^(]*)', barcode.payload))
    expected = {'template': template, 'fields': fields, 'barcode_ais': ais, 'payload': barcode.payload}
    labels = {'correct': label}
    # Text-only changes retain the original barcode, so barcode agreement alone cannot pass negatives.
    for field, value in [('lot', 'OTHERLOT'), ('expiry', '2031-07-31'), ('product_name', 'Other Pump')]:
        elements = tuple(replace(e, text=value) if e.field == field else e for e in label.elements)
        labels[field] = replace(label, elements=elements)
        if field in {'lot', 'expiry'}:
            altered = record.model_copy(update={'extra': {**record.extra, field: value}})
            labels[field+'_encoded'] = from_product(template, altered, version_id='wrong-'+field,
                                                     actor='eval', reason='different label', test_data=True)
    pages = {}
    for kind, source in labels.items():
        path = render_pdf(source, output/f'{kind}.pdf')
        pages[kind] = render_page(path.read_bytes())
    rows = []
    count, start = (16, 9000) if final else (2, 7000)
    engine = RealPrintEngine()
    for condition in ['clean', 'moderate', 'hard']:
        for negative in [False, True]:
            for i in range(count):
                kind = ['lot', 'expiry', 'product_name'][i % 3] if negative else 'correct'
                if negative and kind != 'product_name' and (i//3) % 2:
                    kind += '_encoded'
                photo, *_ = augment_label_detailed(pages[kind], condition, start+i)
                path = output/'photo.png'
                photo.save(path)
                try:
                    result = engine.verify(path, expected)
                    outcome = outcome_of(result)[0]
                except Exception as exc:
                    result, outcome = {'error': f'{type(exc).__name__}: {exc}'}, 'rescan_needed'
                row = {'condition': condition, 'seed': start+i, 'kind': kind, 'outcome': outcome, 'result': result}
                rows.append(row)
                with (output/'rows.jsonl').open('a') as handle:
                    handle.write(json.dumps(row)+'\n')
                print(condition, kind, start+i, outcome, flush=True)
    Image.new('RGB', (1, 1)).save(output/'photo.png')
    return rows


def main() -> None:
    """Choose the disjoint debug or single final run explicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    run(args.output, final=args.final)


if __name__ == '__main__':
    main()
