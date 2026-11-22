"""The new unused set for the NDC scan: products no earlier run touched, pinned with hashes before scoring.

Rule (fixed before looking at any result): walk NAMES in order; for each name take the first DailyMed SPL (API order,
human Rx or OTC label) whose title contains the name and that has an image in its principal display panel section
(LOINC 51945-4); download that SPL XML and its FIRST such image; stop at TARGET products. None is among the 30
reference products or the 70 decoys of the earlier sets (checked by set id and by name). Each image is rendered as
artwork, moderate and hard with the same simulator and seed rule as the public scan photos.

    python -m scripts.ndc_scan.make_new_set acquire   # network: XML + image, writes results/ndc_scan/new_set.json
    python -m scripts.ndc_scan.make_new_set render    # photos + sha256 under data/ndc_scan/photos
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from src.gen import public_scan_acquire as acq

NAMES = ["lorazepam", "alprazolam", "clonazepam", "cetirizine", "prednisolone", "methylprednisolone", "tamoxifen",
         "anastrozole", "letrozole", "lithium", "risperidone", "haloperidol", "digoxin", "labetalol", "bisoprolol",
         "ramipril", "irbesartan", "pantoprazole", "lansoprazole", "ropinirole", "pramipexole", "memantine",
         "oxybutynin", "folic acid", "ketorolac", "oxycodone", "methotrexate", "carbamazepine"]
TARGET = 18
OUT_DIR = Path("data/ndc_scan")
MANIFEST = Path("results/ndc_scan/new_set.json")
CONDITIONS = ("artwork", "moderate", "hard")


def acquire() -> None:
    """Walk NAMES, pin XML and first PDP image of the first usable SPL of each (network)."""
    known = {r["setid"] for r in json.loads(Path("src/gen/public_scan_images.json").read_text("utf-8"))}
    (OUT_DIR / "images").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "xml").mkdir(parents=True, exist_ok=True)
    products: list[dict] = []
    for name in NAMES:
        if len(products) >= TARGET:
            break
        found = json.loads(acq.get(f"{acq.API}spls.json?drug_name={name.replace(' ', '%20')}&pagesize=10"))["data"]
        for hit in found:
            if hit["setid"] in known or name.upper() not in hit["title"].upper():
                continue
            xml = acq.get(f"{acq.API}spls/{hit['setid']}.xml")
            xml_path = OUT_DIR / "xml" / f"{hit['setid']}_v{hit['spl_version']}.xml"
            xml_path.write_bytes(xml)
            names = [n for n in acq.pdp_image_names(xml_path) if n.lower().endswith(acq.USABLE)]
            if not names:
                continue
            media = json.loads(acq.get(f"{acq.API}spls/{hit['setid']}/media.json"))["data"]["media"]
            by_name = {m["name"].lower(): m for m in media if m.get("mime_type", "").startswith("image/")}
            usable = next((by_name[n.lower()] for n in names if n.lower() in by_name), None)
            if usable is None:
                continue
            content = acq.get(usable["url"])
            local = f"{hit['setid'][:8]}__{acq.safe(usable['name'])}"
            (OUT_DIR / "images" / local).write_bytes(content)
            products.append({"ingredient_query": name, "product_name": hit["title"], "setid": hit["setid"],
                             "spl_version": hit["spl_version"], "xml_sha256": hashlib.sha256(xml).hexdigest(),
                             "image_url": usable["url"], "local_file": local,
                             "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
            print("ok", name, hit["setid"], len(content), flush=True)
            break
        else:
            print("none", name, flush=True)
    photos = []
    for p in products:
        for cond in CONDITIONS:
            seed = int(hashlib.sha256(f"{p['sha256']}{cond}".encode()).hexdigest()[:8], 16)
            photos.append({"id": f"{p['local_file'].rsplit('.', 1)[0]}__{cond}", "set": "new_set", "role": "decoy",
                           "condition": cond, "seed": seed, "setid": p["setid"], "product_name": p["product_name"],
                           "expected": None, "source_file": p["local_file"], "source_sha256": p["sha256"]})
    MANIFEST.write_text(json.dumps({"names_tried": NAMES, "products": products, "photos": photos}, indent=1) + "\n",
                        encoding="utf-8")
    print(len(products), "products", len(photos), "photos")


def render() -> None:
    """Render the manifest photos (artwork unchanged, moderate and hard with src.gen.augment) and add sha256."""
    from scripts.public_scan import make_real_photos as mrp

    mrp.SRC, mrp.OUT = OUT_DIR / "images", OUT_DIR / "photos"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mrp.render(manifest, MANIFEST)
    print("rendered", len(manifest["photos"]))


if __name__ == "__main__":
    {"acquire": acquire, "render": render}[sys.argv[1]]()
