"""Check a registered name against observed OCR without inventing product text."""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from src.common.schemas import OcrBlock

THRESHOLD = 0.90
MIN_OCR_CONFIDENCE = 0.80
TOKEN_THRESHOLD = 0.80
GENERIC = frozenset(('medical device catheter introducer set kit suture sterile disposable system guidewire '
                     'needle surgical balloon delivery single use and the for of').split())


def tokens(text: str) -> list[str]:
    """Normalize Unicode/case/trademarks and return letter/number tokens in order."""
    text = unicodedata.normalize('NFKC', text.replace('™', '').replace('®', '')).casefold()
    return re.findall(r'\d+|[^\W\d_]+', text, flags=re.UNICODE)


def coverage(expected: list[str], observed: list[str]) -> tuple[float, bool]:
    """Greedily assign token pairs once; numeric tokens require exact equality."""
    if not expected:
        return 0.0, False
    edges = []
    for i, a in enumerate(expected):
        for j, b in enumerate(observed):
            similarity = (float(a == b) if a.isdecimal() or b.isdecimal()
                          else SequenceMatcher(None, a, b, autojunk=False).ratio())
            if similarity >= TOKEN_THRESHOLD:
                edges.append((-similarity, i, j))
    matched: dict[int, float] = {}
    used = set()
    for negative, i, j in sorted(edges):
        if i not in matched and j not in used:
            matched[i] = -negative
            used.add(j)
    distinctive = [i for i, word in enumerate(expected) if word not in GENERIC]
    score = sum(len(word)*matched.get(i, 0.0) for i, word in enumerate(expected))/sum(map(len, expected))
    return score, bool(distinctive) and all(i in matched for i in distinctive)


def line_groups(blocks: list[OcrBlock]) -> list[list[OcrBlock]]:
    """Form at most three neighboring aligned lines, never concatenate distant evidence."""
    usable = sorted((b for b in blocks if b.conf >= MIN_OCR_CONFIDENCE and tokens(b.text)),
                    key=lambda b: (b.bbox[1], b.bbox[0], b.text))
    groups = []
    for first in usable:
        group = [first]
        groups.append(list(group))
        for _ in range(2):
            x, y, w, h = group[-1].bbox
            candidates = []
            for other in usable:
                if any(other is b for b in group):
                    continue
                ox, oy, ow, oh = other.bbox
                gap = oy-y-h
                aligned = min(x+w, ox+ow)-max(x, ox) >= 0.5*min(w, ow)
                if aligned and -0.2*min(h, oh) <= gap <= 1.5*max(h, oh) and oy > y:
                    candidates.append((max(0, gap), ox, other.text, other))
            if not candidates:
                break
            group.append(min(candidates, key=lambda item: item[:3])[3])
            groups.append(list(group))
    return groups


def check_name(registered_name: str, blocks: list[OcrBlock]) -> dict[str, Any]:
    """Return found/not_found with literal observed evidence and uncalibrated scores."""
    expected = tokens(registered_name)
    best: dict[str, Any] = {'status': 'not_found', 'matched_line': None, 'confidence': 0.0,
                            'similarity': 0.0, 'threshold': THRESHOLD, 'evidence': []}
    for group in line_groups(blocks):
        text = '\n'.join(b.text for b in group)
        score, distinctive = coverage(expected, tokens(text))
        confidence = min(b.conf for b in group)
        if distinctive and score >= THRESHOLD:
            rank = (score, confidence, -len(group))
            current = (best['similarity'], best['confidence'], -len(best['evidence']))
            if best['status'] == 'not_found' or rank > current:
                best = {'status': 'found', 'matched_line': text, 'confidence': confidence,
                        'similarity': score, 'threshold': THRESHOLD,
                        'evidence': [b.model_dump(mode='json') for b in group]}
    return best
