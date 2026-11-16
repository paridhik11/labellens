"""Rebuild two supplemental device artworks from a pinned public Swissmedic notice.

These are annotated packaging illustrations, not newly captured photographs.
They are development-only and never enter the photo test denominator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

URL = 'https://fsca.swissmedic.ch/mep/api/publications/Vk_20181002_08/documents/2'
SHA256 = 'e92214df50365aa44c7835b15c0c19e239f31aa8f4ffb960be81a25a1aebed99'
BOXES = {'primary': (480, 442, 1060, 750), 'carton': (509, 958, 866, 1516)}


def fetch_artwork(output: Path, *, offline: bool = False) -> dict[str, object]:
    """Verify original PDF bytes, render page six and crop documented original-pixel boxes."""
    output.mkdir(parents=True, exist_ok=True)
    pdf = output/'curisoft_notice.pdf'
    if not pdf.exists():
        if offline:
            raise FileNotFoundError(pdf)
        request = Request(URL, headers={'User-Agent': 'LabelLens-academic-source-collector/1.0'})
        with urlopen(request, timeout=60) as response:
            content = response.read(10_000_001)
        if len(content) > 10_000_000:
            raise ValueError('Supplement exceeds download limit')
    else:
        content = pdf.read_bytes()
    if hashlib.sha256(content).hexdigest() != SHA256:
        raise ValueError('Source PDF fingerprint changed')
    pdf.write_bytes(content)
    page = output/'curisoft_page'
    subprocess.run(['pdftoppm', '-f', '6', '-singlefile', '-scale-to', '1800', '-png', str(pdf), str(page)], check=True)
    entries = []
    with Image.open(page.with_suffix('.png')) as image:
        for name, box in BOXES.items():
            if box[2] > image.width or box[3] > image.height:
                raise ValueError('Rendered source dimensions changed')
            path = output/f'curisoft_{name}.png'
            image.crop(box).save(path)
            entries.append({'file': path.name, 'bbox_xyxy_px': box, 'module': 'device', 'condition': 'artwork',
                            'split': 'dev', 'source': URL, 'label_source': 'LLM-generated',
                            'fields': {'product_name': 'CuriSoft® Tiemann catheter CH12',
                                       'lot': '8C02317', 'expiry': '2023-02'},
                            'uncertainty': 'Annotated related illustrations; human review deferred'})
    result = {'images': len(entries), 'condition': 'artwork', 'split': 'dev', 'entries': entries,
              'source_sha256': SHA256, 'human_review': 'DEFERRED', 'symbol_accuracy': 'UNMEASURED'}
    (output/'sources.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main(argv: list[str] | None = None) -> int:
    """Re-fetch the supplemental original or rebuild solely from its cached PDF."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/real_photos/extra_dev'))
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args(argv)
    result = fetch_artwork(args.output, offline=args.offline)
    print(json.dumps({key: result[key] for key in ('images', 'condition', 'split', 'human_review', 'symbol_accuracy')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
