"""Public scan evaluation data: package-label images referenced by pinned DailyMed SPLs.

Positives: the 30 reference products (data/medicine/products.json). Decoys: the 70 extra human medicines of the
med100 branch (data/medicine/expansion100.json there), none of which is in the 30. For each product the images
inside the principal display panel section (LOINC 51945-4, "package label") of its PINNED SPL are taken, at most
two, in document order. A product with no usable image is recorded as skipped. Every image is hashed.

    python -m src.gen.public_scan_acquire --xml-dir ../labellens-med100/data/medicine/source \\
        --expansion ../labellens-med100/data/medicine/expansion100.json

Images go to data/public_scan_real/images (git-ignored; labeler artwork, research use only, never redistributed).
The list with hashes is written to src/gen/public_scan_images.json. The SPL XML files are the pinned versions kept
by the med100 branch (their sha256 is checked against data/medicine/products.json for the 30). The image bytes come
from the DailyMed media service of the CURRENT version of the set id, matched by file name; a name missing there
is skipped and recorded. Python urllib is tried first, curl when it is refused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

API = "https://dailymed.nlm.nih.gov/dailymed/services/v2/"
AGENT = "labellens-course-project/0.1 (student research; contact via repository)"
NS = {"v3": "urn:hl7-org:v3"}
PDP_CODE = "51945-4"
OUT_DIR = Path("data/public_scan_real/images")
LIST_PATH = Path("src/gen/public_scan_images.json")
MAX_IMAGES = 2
USABLE = (".jpg", ".jpeg", ".png")


def get(url: str) -> bytes:
    """GET with a polite delay; curl when urllib is refused."""
    time.sleep(1.5)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=90) as response:
            return response.read()
    except Exception:
        done = subprocess.run(["curl", "-sSL", "--fail", "-A", AGENT, url], capture_output=True, timeout=120)
        if done.returncode != 0:
            raise RuntimeError(f"fetch failed: {url}: {done.stderr.decode(errors='replace')[:200]}") from None
        return done.stdout


def pdp_image_names(xml_path: Path) -> list[str]:
    """File names of the images inside the principal display panel sections, in document order, no duplicates."""
    root = ET.parse(xml_path).getroot()
    files = {}
    for media in root.iter("{urn:hl7-org:v3}observationMedia"):
        reference = media.find("v3:value/v3:reference", NS)
        if reference is not None and media.get("ID"):
            files[media.get("ID")] = reference.get("value")
    names: list[str] = []
    for section in root.iter("{urn:hl7-org:v3}section"):
        code = section.find("v3:code", NS)
        if code is None or code.get("code") != PDP_CODE:
            continue
        for item in section.iter("{urn:hl7-org:v3}renderMultiMedia"):
            name = files.get(item.get("referencedObject"))
            if name and name not in names:
                names.append(name)
    return names


def safe(name: str) -> str:
    """A file-system safe version of an image name."""
    return re.sub(r"[^A-Za-z0-9.]+", "_", name)


def acquire_product(setid: str, version: int, xml_dir: Path, role: str, product_name: str) -> list[dict[str, Any]]:
    """Download up to MAX_IMAGES PDP images of one pinned SPL. Returns records (one skip record when none)."""
    xml_path = xml_dir / f"{setid}_v{version}.xml"
    base = {"role": role, "product_name": product_name, "setid": setid, "spl_version": version,
            "xml_sha256": hashlib.sha256(xml_path.read_bytes()).hexdigest()}
    names = [n for n in pdp_image_names(xml_path) if n.lower().endswith(USABLE)]
    if not names:
        return [{**base, "skipped": "no usable image in the principal display panel section"}]
    media = json.loads(get(f"{API}spls/{setid}/media.json"))["data"]["media"]
    by_name = {m["name"].lower(): m for m in media if m.get("mime_type", "").startswith("image/")}
    records: list[dict[str, Any]] = []
    for name in names:
        if len(records) >= MAX_IMAGES:
            break
        found = by_name.get(name.lower())
        if found is None:
            continue
        content = get(found["url"])
        local = f"{setid[:8]}__{safe(name)}"
        (OUT_DIR / local).write_bytes(content)
        records.append({**base, "image_name": name, "image_url": found["url"], "local_file": local,
                        "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content),
                        "rights": "labeler's artwork; research use only; not redistributed"})
        print("ok", role, product_name, local, len(content), flush=True)
    return records or [{**base, "skipped": "image names not found in the DailyMed media list"}]


def main() -> int:
    """Fetch the images of the 30 reference products and the 70 extra products, write the list."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, required=True)
    parser.add_argument("--expansion", type=Path, required=True)
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reference = json.loads(Path("data/medicine/products.json").read_text(encoding="utf-8"))
    extra = json.loads(args.expansion.read_text(encoding="utf-8"))["added"]
    ref_ids = {r["setid"] for r in reference}
    assert len(reference) == 30 and not ref_ids & {e["setid"] for e in extra} and len(extra) == 70
    records: list[dict[str, Any]] = []
    for row in reference:
        records += acquire_product(row["setid"], row["version"], args.xml_dir, "positive", row["product_name"])
    for row in extra:
        found = sorted(args.xml_dir.glob(f"{row['setid']}_v*.xml"))
        if not found:
            records.append({"role": "decoy", "product_name": row["product_name"], "setid": row["setid"],
                            "skipped": "pinned SPL xml not found"})
            continue
        version = int(re.search(r"_v(\d+)\.xml$", found[-1].name).group(1))
        records += acquire_product(row["setid"], version, args.xml_dir, "decoy", row["product_name"])
    LIST_PATH.write_text(json.dumps(records, indent=1) + "\n", encoding="utf-8")
    print("images", sum("sha256" in r for r in records), "skipped products", sum("skipped" in r for r in records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
