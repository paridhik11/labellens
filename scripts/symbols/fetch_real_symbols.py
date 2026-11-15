"""Fetch real manufacturer and use-by pictogram artwork from Wikimedia Commons.

Writes ``scripts/symbols/real_symbol_sources.json`` (title, page URL, file URL, author, license; this file
is committed) and PNG renderings under ``data/real_symbols/`` (gitignored, not committed).
Run from the repo root:  python scripts/symbols/fetch_real_symbols.py
Only the license text reported by the Commons API is recorded; check it before any redistribution.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "real_symbols"
SOURCES = Path(__file__).with_name("real_symbol_sources.json")
AGENT = "labellens-course-project/0.1 (student research; contact via repository)"
# kind: "iso" is the standardised pictogram; "generic" is a free icon of the same concept (not ISO artwork).
FILES = {
    "manufacturer": {
        "iso": ["ISO 7000 - Ref-No 3082.svg", "Manufacturer.svg"],
        "generic": ["Factory icon.svg", "Factory icon blue.svg", "Factory-fontawesomish.svg",
                    "Simpleicons Places factory-building-1.svg", "Factory clip art.svg"],
    },
    "expiry": {
        "iso": ["ISO 7000 - Ref-No 2607.svg", "Use-by-date.svg"],
        "generic": ["Hourglass icon.svg", "Hourglass 2.svg", "Hourglass modern 2.svg", "Black Hourglass icon.svg",
                    "VK icons hourglass outline 56.svg"],
    },
}


def call(url: str) -> bytes:
    """GET with a polite delay and retry on HTTP 429."""
    for attempt in range(6):
        time.sleep(2.0)
        request = urllib.request.Request(url, headers={"User-Agent": AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code != 429:
                raise
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"gave up: {url}")


def clean(meta: dict, key: str) -> str:
    """Return a Commons metadata value without HTML tags."""
    return html.unescape(re.sub(r"<[^>]+>", "", meta.get(key, {}).get("value", ""))).strip()


def main() -> int:
    """Download every listed file and write the sources list."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for name, groups in FILES.items():
        for kind, titles in groups.items():
            for title in titles:
                query = urllib.parse.urlencode({
                    "action": "query", "titles": f"File:{title}", "prop": "imageinfo", "format": "json",
                    "iiprop": "url|extmetadata", "iiurlwidth": 512,
                })
                data = json.loads(call(f"https://commons.wikimedia.org/w/api.php?{query}"))
                page = next(iter(data["query"]["pages"].values()))
                if "imageinfo" not in page:
                    print("missing", title, file=sys.stderr)
                    continue
                info = page["imageinfo"][0]
                meta = info.get("extmetadata", {})
                stem = re.sub(r"[^A-Za-z0-9]+", "_", title.rsplit(".", 1)[0]).strip("_")
                target = OUT_DIR / f"{name}__{kind}__{stem}.png"
                if not target.exists():
                    target.write_bytes(call(info["thumburl"]))
                records.append({
                    "symbol": name, "kind": kind, "title": title, "page_url": info["descriptionurl"],
                    "file_url": info["url"], "rendered_png_url": info["thumburl"], "local_png": target.name,
                    "author": clean(meta, "Artist"), "license": clean(meta, "LicenseShortName"),
                    "license_url": clean(meta, "LicenseUrl"),
                })
                print("ok", title, records[-1]["license"])
    SOURCES.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
