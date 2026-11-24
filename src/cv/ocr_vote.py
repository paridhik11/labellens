"""Optional, CPU-only Tesseract evidence and conservative two-engine line voting."""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from src.common.schemas import OcrBlock


def tesseract_lines(
    image: Any, *, executable: str | None = None, timeout: float | None = None,
) -> list[OcrBlock]:
    """Read sparse upright text as TSV lines; do not infer fields or fabricate characters."""
    from PIL import Image

    program = executable or shutil.which('tesseract')
    if not program:
        raise RuntimeError('Tesseract is unavailable; install the optional system engine')
    with TemporaryDirectory(prefix='labellens_ocr_') as folder:
        path = Path(folder)/'input.png'
        Image.fromarray(image).save(path)
        result = subprocess.run([program, str(path), 'stdout', '-l', 'eng', '--psm', '11', 'tsv'],
                                # Tesseract writes UTF-8; the Windows default code page turned "®" into "Â®"
                                capture_output=True, text=True, encoding='utf-8', errors='replace', check=True,
                                timeout=60 if timeout is None else min(60.0, timeout),
                                env={**os.environ, 'OMP_THREAD_LIMIT': '1'})
    groups: dict[tuple[str, ...], list[dict[str, str]]] = {}
    for row in csv.DictReader(StringIO(result.stdout), delimiter='\t'):
        if row['level'] == '5' and row['text'].strip() and float(row['conf']) >= 0:
            key = tuple(row[name] for name in ('page_num', 'block_num', 'par_num', 'line_num'))
            groups.setdefault(key, []).append(row)
    blocks = []
    for words in groups.values():
        left = min(int(w['left']) for w in words)
        top = min(int(w['top']) for w in words)
        right = max(int(w['left'])+int(w['width']) for w in words)
        bottom = max(int(w['top'])+int(w['height']) for w in words)
        confidence = sum(float(w['conf'])*len(w['text']) for w in words)/sum(len(w['text']) for w in words)/100
        blocks.append(OcrBlock(text=' '.join(w['text'] for w in words), bbox=(left, top, right-left, bottom-top),
                               conf=max(0.0, min(1.0, confidence))))
    return blocks


def vote_lines(rapid: list[OcrBlock], secondary: list[OcrBlock]) -> list[OcrBlock]:
    """Prefer agreeing complete observations; preserve unmatched lines, reduce disputed confidence.

    Engine confidence values are not calibrated probabilities. Text is always
    copied from an actual engine observation. No dictionary or reference is used.
    """
    result = list(rapid)
    for other in secondary:
        x, y, w, h = other.bbox
        overlaps = []
        for index, old in enumerate(result):
            ox, oy, ow, oh = old.bbox
            area = max(0, min(x+w, ox+ow)-max(x, ox))*max(0, min(y+h, oy+oh)-max(y, oy))
            if area/max(1, min(w*h, ow*oh)) >= 0.5:
                overlaps.append(index)
        if not overlaps:
            result.append(other)
            continue
        index = max(overlaps, key=lambda i: result[i].conf)
        old = result[index]
        a = ''.join(c.casefold() for c in old.text if c.isalnum())
        b = ''.join(c.casefold() for c in other.text if c.isalnum())
        if a == b:
            chosen = other if other.text.count(' ') >= old.text.count(' ') else old
            result[index] = chosen.model_copy(update={'conf': min(old.conf, other.conf)})
        elif a and a in b and other.conf >= 0.7:
            result[index] = other
        elif other.conf > old.conf + 0.15:
            result[index] = other.model_copy(update={'conf': min(0.79, other.conf)})
    return sorted(result, key=lambda b: (b.bbox[1], b.bbox[0]))
