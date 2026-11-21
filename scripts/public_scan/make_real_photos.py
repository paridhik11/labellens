"""Real DailyMed package-label artwork -> simulated phone photos (protocol v2: results/public_scan/protocol_v2.md).

Reads src/gen/public_scan_images.json (images fetched by src/gen/public_scan_acquire.py), splits PRODUCTS (never
images) into dev and fresh with a seeded shuffle, and renders each chosen image under three conditions:

- artwork:  the image unchanged (the project's simulator "clean" condition applies no change at all)
- moderate: src.gen.augment condition "moderate" (small rotation, perspective, blur, noise, lighting)
- hard:     src.gen.augment condition "hard"

Artwork smaller than 1400 px on its long side is enlarged (Lanczos) before moderate and hard so the simulated
label is not tiny. Output: data/public_scan_real/photos/<set>/<id>.jpg (JPEG quality 90, git-ignored) and the
manifest results/public_scan/photos_v2.json with source and rendered sha256 for every photo.

    python -m scripts.public_scan.make_real_photos plan     # write the split and the manifest of what will be rendered
    python -m scripts.public_scan.make_real_photos render   # render every photo of the manifest and record hashes
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

from PIL import Image

IMAGES = Path("src/gen/public_scan_images.json")
SRC = Path("data/public_scan_real/images")
OUT = Path("data/public_scan_real/photos")
MANIFEST = Path("results/public_scan/photos_v2.json")
SEED = 42
CONDITIONS = ("artwork", "moderate", "hard")
DEV_POSITIVES, DEV_DECOYS, FRESH_DECOYS = 15, 15, 40
MIN_LONG_SIDE = 1400


def plan() -> dict:
    """Split products, choose images (positives up to 2 per product, decoys the first image only), list photos."""
    records = json.loads(IMAGES.read_text(encoding="utf-8"))
    usable = {"positive": {}, "decoy": {}}
    skipped = []
    for r in records:
        if "skipped" in r:
            skipped.append({k: r[k] for k in ("role", "product_name", "setid", "skipped")})
        else:
            usable[r["role"]].setdefault(r["setid"], []).append(r)
    rng = random.Random(SEED)
    pos = sorted(usable["positive"])
    dec = sorted(usable["decoy"])
    rng.shuffle(pos)
    rng.shuffle(dec)
    split = {"dev_positive": pos[:DEV_POSITIVES], "fresh_positive": pos[DEV_POSITIVES:],
             "dev_decoy": dec[:DEV_DECOYS], "fresh_decoy": dec[DEV_DECOYS:DEV_DECOYS + FRESH_DECOYS],
             "decoys_unused": dec[DEV_DECOYS + FRESH_DECOYS:]}
    photos = []
    for group, role, set_name in (("dev_positive", "positive", "dev_real"),
                                  ("fresh_positive", "positive", "fresh_real"),
                                  ("dev_decoy", "decoy", "dev_real"), ("fresh_decoy", "decoy", "fresh_real")):
        for setid in split[group]:
            images = usable[role][setid][: 2 if role == "positive" else 1]
            for image in images:
                for condition in CONDITIONS:
                    pid = f"{image['local_file'].rsplit('.', 1)[0]}__{condition}"
                    seed = int(hashlib.sha256(f"{image['sha256']}{condition}".encode()).hexdigest()[:8], 16)
                    photos.append({"id": pid, "set": set_name, "role": role, "condition": condition, "seed": seed,
                                   "setid": setid, "product_name": image["product_name"],
                                   "expected": image["product_name"] if role == "positive" else None,
                                   "source_file": image["local_file"], "source_sha256": image["sha256"]})
    return {"seed": SEED, "split": split, "skipped_products": skipped, "photos": photos}


def render(manifest: dict) -> None:
    """Render every photo (same seed, same bytes) and add the rendered sha256."""
    from src.gen.augment import augment_label

    for photo in manifest["photos"]:
        folder = OUT / photo["set"]
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{photo['id']}.jpg"
        source = Image.open(SRC / photo["source_file"]).convert("RGB")
        if photo["condition"] == "artwork":
            image = source
        else:
            scale = MIN_LONG_SIDE / max(source.size)
            if scale > 1:
                source = source.resize((round(source.width * scale), round(source.height * scale)), Image.LANCZOS)
            image, _, _ = augment_label(source, photo["condition"], photo["seed"])
        image.save(target, quality=90)
        photo["file"] = str(target)
        photo["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        data = plan()
        MANIFEST.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        print({k: len(v) for k, v in data["split"].items()}, len(data["photos"]), "photos,",
              len(data["skipped_products"]), "products skipped")
    elif sys.argv[1] == "render":
        render(json.loads(MANIFEST.read_text(encoding="utf-8")))
        print("rendered")
    else:
        raise SystemExit(__doc__)
