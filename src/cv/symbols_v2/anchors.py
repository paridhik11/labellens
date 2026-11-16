"""Text-anchor rule: a pictogram is expected next to the printed text it belongs to.

On labels that follow ISO 15223-1 practice the manufacturer pictogram sits beside the manufacturer name and
address and the use-by pictogram beside the expiry date. OCR text is a second, independent signal for the
pictogram: a candidate that scores a little below the normal threshold is accepted when it lies close to its
anchor line, and (in the strict variant) a candidate far from every anchor line is refused.

Anchor lines are found from OCR text only:

* expiry: a line whose printed key is EXP (``split_key_value``),
* manufacturer: the line directly above a street-address line (the same rule the blind field mapper uses), or a
  line that starts with the word "manufacturer" or "mfg".

Nothing here reads ground truth. If the anchor lines are not found (OCR failure, unusual layout) the rule does
nothing, so the detector falls back to its normal behaviour.
"""

from __future__ import annotations

import re

from src.common.schemas import OcrBlock
from src.cv.fields import _ADDRESS, split_key_value

_MANUFACTURER_WORD = re.compile(r"^\s*(manufacturer|manufactured by|mfg)\b", re.IGNORECASE)


def anchor_lines(blocks: list[OcrBlock]) -> dict[str, list[tuple[float, float, float, float]]]:
    """Boxes (x, y, w, h) of the OCR lines that anchor each pictogram."""
    anchors: dict[str, list[tuple[float, float, float, float]]] = {"manufacturer": [], "expiry": []}
    ordered = sorted(blocks, key=lambda block: block.bbox[1])
    for index, block in enumerate(ordered):
        field, _, _ = split_key_value(block.text)
        if field == "expiry":
            anchors["expiry"].append(block.bbox)
        if _MANUFACTURER_WORD.match(block.text):
            anchors["manufacturer"].append(block.bbox)
        if _ADDRESS.match(block.text.strip()) and index > 0:
            anchors["manufacturer"].append(ordered[index - 1].bbox)
    return anchors


def distance_in_lines(box: tuple[float, float, float, float], line: tuple[float, float, float, float]) -> float:
    """Gap between two boxes divided by the anchor line's height (0 when they touch or overlap)."""
    bx, by, bw, bh = box
    lx, ly, lw, lh = line
    dx = max(0.0, max(bx - (lx + lw), lx - (bx + bw)))
    dy = max(0.0, max(by - (ly + lh), ly - (by + bh)))
    return float((dx**2 + dy**2) ** 0.5 / max(lh, 1.0))


def near_anchor(
    name: str, box: tuple[float, float, float, float], anchors: dict[str, list[tuple[float, float, float, float]]],
    reach: float = 3.0,
) -> bool:
    """True when ``box`` lies within ``reach`` line heights of an anchor line for ``name``."""
    return any(distance_in_lines(box, line) <= reach for line in anchors.get(name, []))
