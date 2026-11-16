"""Fetch real label images from DailyMed (US National Library of Medicine) that may carry ISO 15223-1 pictograms.

Writes ``scripts/symbols/real_label_sources.json`` (set id, title, image name and URL; committed) and the images under
``data/real_labels/`` (not committed). DailyMed hosts structured product labels submitted by the labeler; the label art
belongs to the labeler, so the images are used locally for research only and are never redistributed here.
Run from the repo root:  python scripts/symbols/fetch_real_labels.py
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "real_labels"
SOURCES = Path(__file__).with_name("real_label_sources.json")
API = "https://dailymed.nlm.nih.gov/dailymed/services/v2/"
AGENT = "labellens-course-project/0.1 (student research; contact via repository)"
# Set ids found by searching DailyMed titles for device-like products (test strips, pregnancy test, lancet, meters).
SETIDS = {
    "69932e8d-582d-44e7-b148-3554695cca4b": "ATLAS PREGNANCY TEST [ECLIPSE PHARMA LLC]",
    "c7b67525-a5f7-477f-a7bb-e1b51748445a": "50 TD GOLD BLOOD GLUCOSE TEST STRIP [EPS BIO TECHNOLOGY CORP]",
    "6d1aee93-3ea3-4684-acfa-587dc428889d": "TD GOLD BLOOD GLUCOSE TEST STRIP [EPS BIO TECHNOLOGY CORP.]",
    "0e2498a8-b150-49c2-a5bd-2746654069da": "TD GOLD BLOOD GLUCOSE MONITOR SET [EPS BIO TECHNOLOGY CORP.]",
    "82984eb0-4e9e-4cca-b234-50d337cd6cfe": "TD GOLD VOICE BLOOD GLUCOSE MONITOR SET [EPS BIO TECHNOLOGY CORP.]",
    "d491f12b-f766-4c59-a92b-bcb465699ed0": "PRESSURE ACTIVATED SAFETY LANCET [CARE LIVING DIAGNOSTICS INC.]",
}


def get(url: str) -> bytes:
    """GET with a polite delay."""
    time.sleep(1.5)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=90) as response:
        return response.read()


def main() -> int:
    """Download every image of every listed set id and write the sources list."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for setid, title in SETIDS.items():
        for media in json.loads(get(f"{API}spls/{setid}/media.json"))["data"]["media"]:
            if not media["mime_type"].startswith("image/"):
                continue
            local = f"{setid[:8]}__{re.sub(r'[^A-Za-z0-9.]+', '_', media['name'])}"
            target = OUT_DIR / local
            if not target.exists():
                target.write_bytes(get(media["url"]))
            records.append({
                "setid": setid, "title": title, "image_name": media["name"], "image_url": media["url"],
                "dailymed_page": f"https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid={urllib.parse.quote(setid)}",
                "local_file": local, "bytes": target.stat().st_size, "rights": "labeler's; research use only",
            })
            print("ok", local, records[-1]["bytes"])
    SOURCES.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
