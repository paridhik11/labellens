"""Build three deterministic review-only demo packages, never approval or production artwork."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MARK = 'DRAFT, not for production'


def verify_golden(output: Path) -> dict[str, Any]:
    """Verify fingerprints and the visible warning on every package PDF and SVG."""
    from xml.etree import ElementTree as ET

    from pypdf import PdfReader

    manifest = json.loads((output/'manifest.json').read_text())
    for relative, expected in manifest['files'].items():
        path = (output/relative).resolve()
        if not path.is_relative_to(output.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Golden artifact changed: {relative}')
    for name in manifest['packages']:
        if MARK not in PdfReader(output/name/'label.pdf').pages[0].extract_text():
            raise ValueError(f'PDF draft warning missing: {name}')
        if MARK not in ''.join(ET.parse(output/name/'label.svg').getroot().itertext()):
            raise ValueError(f'SVG draft warning missing: {name}')
    return manifest


def _export(label: Any, folder: Path, metadata: dict[str, Any]) -> None:
    """Export an immutable snapshot using the documented PDF/SVG/QR entry points."""
    from src.export.pdf import render_pdf
    from src.export.qr import make_qr
    from src.export.svg import render_svg

    render_pdf(label, folder/'label.pdf')
    render_svg(label, folder/'label.svg')
    qr = make_qr(f'https://example.org/published/{label.version_id}')
    (folder/'qr.png').write_bytes(qr.png)
    (folder/'qr.svg').write_text(qr.svg)
    (folder/'expected.json').write_text(json.dumps(metadata, indent=2, sort_keys=True)+'\n')


def build_golden(
    output: Path, *, source_image: Path, source_sha256: str, source_fields: dict[str, str],
) -> dict[str, Any]:
    """Atomically build or verify clean DailyMed, synthetic and confirmed barcode-change demos.

    DailyMed is an embedded source-artwork review sheet, not an asserted original
    physical-size label. Its identifier/artwork is not invented or certified.
    The other packages explicitly use the already-established test placeholder.
    """
    from io import BytesIO

    from PIL import Image

    from src.common.schemas import ChangeRequest, ProductRecord
    from src.export.label_model import Element, Label
    from src.export.template import from_product
    from src.gen.revise import revise_template

    if hashlib.sha256(source_image.read_bytes()).hexdigest() != source_sha256:
        raise ValueError('Golden source fingerprint changed')
    if output.exists():
        manifest = verify_golden(output)
        if manifest['source_sha256'] != source_sha256:
            raise ValueError('Existing demo uses a different source')
        return manifest
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='golden_', dir=output.parent) as temporary:
        work = Path(temporary)/'package'
        work.mkdir()
        with Image.open(source_image) as original:
            buffer = BytesIO()
            original.convert('RGB').save(buffer, format='PNG')
            ratio = original.height/original.width
        source_label = Label(100, max(90, 16+96*ratio),
                             (Element('source_artwork', 'image', (2, 12, 96, 96*ratio), png=buffer.getvalue()),),
                             'golden-dailymed-v1', 'demo-editor', 'Public artwork review sheet', test_data=True)
        _export(source_label, work/'clean_dailymed', {'fields': source_fields, 'source_sha256': source_sha256,
                'reference_source': 'LLM-generated', 'condition': 'clean artwork',
                'physical_size_scope': '100mm review sheet, not original manufacturer dimensions',
                'approval': 'NOT_ISSUED', 'real_symbol_accuracy': 'UNMEASURED'})
        template = json.loads((ROOT/'src/gen/templates/test_device.json').read_text())
        record = ProductRecord(product_id='golden-test', name='TEST DEVICE', model='TEST-M001',
                               manufacturer='DEMO LABS', manufacturer_address='12 Demo Road',
                               udi_di='00000000000000',
                               extra={'lot': 'TESTLOT1', 'expiry': '2033-06-15', 'serial': 'TESTSER1'})
        baseline = from_product(template, record, version_id='golden-synthetic-v1', actor='demo-editor',
                                reason='Deterministic test-only demo', test_data=True)
        _export(baseline, work/'synthetic', {'record': record.model_dump(), 'status': 'DRAFT',
                                            'approval': 'NOT_ISSUED', 'barcode_action': 'GENERATED'})
        change = ChangeRequest(change_id='golden-lot-change', product_id=record.product_id,
                               field='lot', old_value='TESTLOT1', new_value='TESTLOT2')
        revision = revise_template(template, record, change, previous_label=baseline,
                                   version_id='golden-barcode-v2', actor='demo-editor',
                                   reason='Confirmed test lot change',
                                   confirmed={'confirmed_lot_change': True})
        _export(revision.require_label(), work/'barcode_change', {'record': revision.record.model_dump(),
                'status': revision.status, 'barcode_action': revision.barcode_decision.action.value,
                'change_log': list(revision.change_log), 'self_check': revision.self_check, 'approval': 'NOT_ISSUED'})
        packages = ['clean_dailymed', 'synthetic', 'barcode_change']
        files = {p.relative_to(work).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(work.rglob('*')) if p.is_file()}
        manifest = {'version': 1, 'packages': packages, 'source_sha256': source_sha256, 'files': files,
                    'warning': MARK, 'publication': 'NOT_ISSUED'}
        (work/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
        verify_golden(work)
        os.rename(work, output)
    return verify_golden(output)


def main(argv: list[str] | None = None) -> int:
    """Run one repeatable demo command, fetching pinned originals only if absent."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'data/golden_demo')
    args = parser.parse_args(argv)
    config = json.loads((ROOT/'scripts/cv_experiments/config/cv2.json').read_text())
    source = next(item for item in config['items'] if item['id'] == 'device_05')
    path = ROOT/source['file']
    if not path.exists():
        from scripts.real.fetch_dailymed import load_catalog, materialize

        materialize(load_catalog(ROOT/'data/real/SOURCES.md'), ROOT/'data/real/devices')
    result = build_golden(args.output, source_image=path, source_sha256=source['sha256'],
                          source_fields=source['fields'])
    print(json.dumps({'packages': result['packages'], 'verified_pdf_svg_warnings': 6, 'publication': 'NOT_ISSUED'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
