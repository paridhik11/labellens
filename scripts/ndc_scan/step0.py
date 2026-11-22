"""Step 0: how often can an NDC be read? (measured on existing images only, before any design choice).

(a) barcode: zxing-cpp on the 145 pinned DailyMed package-label images (condition "artwork") and on the dev
    photos rendered from them (moderate, hard). An NDC barcode is UPC-A starting with 3, EAN-13 starting with 03,
    or GS1 DataMatrix with AI 01 (GTIN-14 with the 03 prefix), valid check digit.
(b) printed NDC: regex on the cached OCR lines of the dev photos (lines_dev_real.jsonl, existing reader, nothing
    re-read), counted when the normalised code is in the corpus table (positives) or is any NDC-shaped string.

    python -m scripts.ndc_scan.step0
"""
from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from src.ndc.barcode import read_payloads
from src.ndc.codes import printed_ndcs
from src.ndc.table import load_table

IMAGES = Path("src/gen/public_scan_images.json")
IMG_DIR = Path("../labellens-publicscan/data/public_scan_real/images")
PHOTO_DIR = Path("../labellens-publicscan/data/public_scan_real/photos/dev_real")
OUT = Path("results/ndc_scan/step0.json")


def main() -> None:
    table = load_table()
    rows: list[dict] = []
    records = json.loads(IMAGES.read_text(encoding="utf-8"))
    for r in records:
        t = time.monotonic()
        hits = read_payloads(IMG_DIR / r["local_file"])
        rows.append({"condition": "artwork", "role": r["role"], "id": r["local_file"], "setid": r["setid"],
                     "payloads": [h["payload"] for h in hits], "any_barcode": bool(hits),
                     "ndc_barcode": any(h["ndcs"] for h in hits),
                     "in_table": [c for h in hits for c in h["ndcs"] if c in table],
                     "seconds": round(time.monotonic() - t, 2)})
    cache = Path("results/public_scan/lines_dev_real.jsonl")
    dev = [json.loads(line) for line in cache.read_text("utf-8").splitlines()]
    ocr = []
    for d in dev:
        path = PHOTO_DIR / Path(d["path"]).name
        hits = read_payloads(path)
        text = " ".join(x["text"] for x in d["lines"])
        codes = printed_ndcs(text)
        ocr.append({"condition": d["condition"], "role": d["kind"], "id": d["id"], "expected": d["expected"],
                    "ocr_ndc_shaped": bool(codes), "ocr_ndc_in_table": [c for c in codes if c in table],
                    "ndc_barcode": any(h["ndcs"] for h in hits), "any_barcode": bool(hits),
                    "barcode_in_table": [c for h in hits for c in h["ndcs"] if c in table],
                    "ocr_complete": d["complete"]})
    agg: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        k = f"artwork-all145/{r['role']}"
        agg[k]["n"] += 1
        agg[k]["any_barcode"] += r["any_barcode"]
        agg[k]["ndc_barcode"] += r["ndc_barcode"]
        agg[k]["ndc_in_table"] += bool(r["in_table"])
    for r in ocr:
        k = f"dev-photos/{r['role']}/{r['condition']}"
        agg[k]["n"] += 1
        agg[k]["any_barcode"] += r["any_barcode"]
        agg[k]["ndc_barcode"] += r["ndc_barcode"]
        agg[k]["barcode_in_table"] += bool(r["barcode_in_table"])
        agg[k]["ocr_ndc_shaped"] += r["ocr_ndc_shaped"]
        agg[k]["ocr_ndc_in_table"] += bool(r["ocr_ndc_in_table"])
        agg[k]["either_in_table"] += bool(r["ocr_ndc_in_table"] or r["barcode_in_table"])
    OUT.write_text(json.dumps({"summary": {k: dict(v) for k, v in sorted(agg.items())}, "images": rows,
                               "dev_photos": ocr}, indent=1), encoding="utf-8")
    for k, v in sorted(agg.items()):
        print(k, dict(v))


if __name__ == "__main__":
    main()
