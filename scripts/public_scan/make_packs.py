"""Synthetic medicine-pack photos for the public scan check (names authored, not read from real photos).

The 50 CV4b fresh photos are device packs, so none of them can be identified as a reference medicine. To measure
the identification rate at all, positives are rendered from the catalog product names (a big brand line plus
ordinary pack text), then degraded like a phone photo (small rotation, blur, noise, brightness). Decoys carry the
name of a medicine that is NOT in the catalog. Everything is seeded and written to data/public_scan_packs/<split>/.
Usage: python -m scripts.public_scan.make_packs dev|heldout
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIRS = (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu"))
FONTS = ("arialbd.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf")
BODY = ("arial.ttf", "calibri.ttf", "DejaVuSans.ttf")
FILLER = ("Tablets USP", "Store at 20 to 25 C (68 to 77 F)", "Keep out of reach of children", "Rx only",
          "Do not use if seal is broken", "100 tablets", "See package insert", "Lot A1B2C3  Exp 12/2028",
          "Each tablet contains 10 mg", "Dispense in a tight container")
DEV_DECOYS = ("Keytruda pembrolizumab infusion", "Humira adalimumab injection", "Dupixent dupilumab pen",
              "Eliquis apixaban tablet", "Xarelto rivaroxaban tablets", "Biktarvy antiviral tablets",
              "Genvoya antiviral tablets", "Entyvio vedolizumab infusion", "Cosentyx secukinumab injection",
              "Skyrizi risankizumab injection")
HELDOUT_DECOYS = ("Ozempic semaglutide pen", "Jardiance empagliflozin tablets", "Farxiga dapagliflozin tablets",
                  "Zepbound tirzepatide injection", "Trulicity dulaglutide pen", "Symbicort budesonide inhaler",
                  "Advair Diskus fluticasone", "Benadryl diphenhydramine allergy", "Sudafed pseudoephedrine",
                  "Mucinex guaifenesin", "Imodium loperamide", "Dulcolax bisacodyl laxative",
                  "Zofran ondansetron tablets", "Tamiflu oseltamivir capsules", "Zithromax azithromycin tablets")


def font(names: tuple[str, ...], size: int) -> ImageFont.FreeTypeFont:
    """The first available TrueType font from the list (Windows or DejaVu)."""
    for folder in FONT_DIRS:
        for name in names:
            if (folder / name).exists():
                return ImageFont.truetype(str(folder / name), size)
    raise RuntimeError("no TrueType font found for the synthetic packs")


def render(title: str, rng: random.Random) -> Image.Image:
    """One pack face: coloured panel, big name (wrapped), a subtitle and filler text, then a phone-photo look."""
    width, height = 1800, 1300
    colour = tuple(rng.randint(150, 245) for _ in range(3))
    image = Image.new("RGB", (width, height), (225, 225, 220))
    draw = ImageDraw.Draw(image)
    draw.rectangle((120, 90, width - 120, height - 90), fill=colour, outline=(40, 40, 40), width=6)
    size, y = rng.randint(120, 170), 190
    words = title.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textlength(test, font=font(FONTS, size)) > width - 400 and current:
            lines.append(current)
            current = word
        else:
            current = test
    lines.append(current)
    for line in lines:
        draw.text((220, y), line, fill=(20, 20, 60), font=font(FONTS, size))
        y += size + 30
    y += 60
    for text in rng.sample(FILLER, 5):
        draw.text((220, y), text, fill=(30, 30, 30), font=font(BODY, rng.randint(46, 60)))
        y += 100
    image = image.rotate(rng.uniform(-6, 6), resample=Image.BICUBIC, expand=False, fillcolor=(210, 210, 205))
    image = image.filter(ImageFilter.GaussianBlur(rng.uniform(0.0, 1.2)))
    pixels = np.asarray(image).astype(np.float32)
    pixels = pixels * rng.uniform(0.85, 1.1) + np.random.default_rng(rng.randint(0, 10**6)).normal(0, 6, pixels.shape)
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8))


def build(split: str, out_root: Path = Path("data/public_scan_packs")) -> list[dict]:
    """Write the split's images and its manifest (filename, expected product name or null, kind, seed)."""
    from src.api.medicine import MedicineCatalog

    names = [p.name for p in MedicineCatalog().products.values()]
    if split == "dev":
        positives, decoys, base = names[:20], DEV_DECOYS, 7000
    elif split == "heldout":
        positives, decoys, base = names, HELDOUT_DECOYS, 7100
    else:
        raise SystemExit("split must be dev or heldout")
    folder = out_root / split
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, (title, kind) in enumerate([(n, "positive") for n in positives] + [(d, "decoy") for d in decoys]):
        seed = base + i
        image = render(title, random.Random(seed))
        name = f"{split}_{i:02d}.jpg"
        image.save(folder / name, quality=88)
        rows.append({"filename": name, "kind": kind, "expected": title if kind == "positive" else None,
                     "title": title, "seed": seed})
    (folder / "manifest.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return rows


if __name__ == "__main__":
    print(len(build(sys.argv[1])), "images")
