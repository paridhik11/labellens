"""List the OCR confidence behind every print/barcode disagreement on the very hard dev labels.

Dev seeds only. Run from the repo root with PYTHONPATH=. :

    python scripts/cv_experiments/false_alarm_confidence.py data/synthetic/dev42 data/synthetic/dev43
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def work(path: str) -> list[tuple]:
    from src.cv.consistency import field_confidence
    from src.cv.extract import extract_label_modes
    from src.cv.fields import _canonical, split_key_value

    p = Path(path)
    truth = json.loads(p.with_suffix(".json").read_text(encoding="utf-8"))
    rows = []
    for mode, (extraction, _) in extract_label_modes(p, modes=("template", "blind"), postcorrect=True).items():
        if len(extraction.barcodes) != 1 or not extraction.barcodes[0].parsed:
            continue
        parsed = extraction.barcodes[0].parsed
        targets = {"lot": parsed.get("10", "")}
        code = parsed.get("17", "")
        if len(code) == 6:
            targets["expiry"] = f"20{code[:2]}-{code[2:4]}-{code[4:]}"
        for field, expected in targets.items():
            if field not in extraction.fields:
                continue
            value = split_key_value(extraction.fields[field])[2]
            if _canonical(value) != _canonical(expected):
                rows.append((p.parts[-3], p.stem[11:14], mode, field, field_confidence(extraction, field),
                             value, truth["fields"][field]))
    return rows


if __name__ == "__main__":
    jobs = [str(p) for d in sys.argv[1:] for p in sorted((Path(d) / "very_hard").glob("*.png"))]
    with ProcessPoolExecutor(4) as pool:
        for rows in pool.map(work, jobs):
            for row in rows:
                seed, label, mode, field, conf, read, printed = row
                shown = "none" if conf is None else f"{conf:.3f}"
                print(f"{seed} {label} {mode:8s} {field:6s} conf={shown} read={read!r} printed={printed!r}")
