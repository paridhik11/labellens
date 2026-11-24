"""Make public/12_synthetic_lopressor.jpg: a synthetic carton face for a drug outside the 30 curated medicines.

    python demo_photos/make_lopressor_image.py

The NDC 12345-678-90 is a placeholder that resolves to nothing, so the photo scan cannot decide by NDC and has to
take the name from the text it reads. The image is drawn with Pillow (plain text on a carton-like panel, slight
blur and noise); it is not a real pack and not real artwork. The ® and the curly quotes test that OCR text is
decoded as UTF-8 (no "Â®" or "â€œ" on screen).
"""
from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent / "public" / "12_synthetic_lopressor.jpg"
FONTS = Path("C:/Windows/Fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """A Windows TrueType font, or Pillow's default when it is missing."""
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        return ImageFont.load_default(size)


def main() -> None:
    """Draw the panel and save it as a JPEG."""
    random.seed(12)
    img = Image.new("RGB", (1400, 900), (205, 205, 200))
    d = ImageDraw.Draw(img)
    d.rectangle((100, 80, 1300, 820), fill=(250, 250, 246), outline=(90, 90, 90), width=3)
    d.rectangle((100, 80, 1300, 200), fill=(30, 70, 140))
    d.text((140, 105), "NDC 12345-678-90", font=font("arialbd.ttf", 54), fill="white")
    d.text((1020, 120), "Rx only", font=font("arialbd.ttf", 46), fill="white")
    d.text((140, 250), "LOPRESSOR\u00ae", font=font("arialbd.ttf", 120), fill=(20, 20, 20))
    d.text((140, 400), "(metoprolol tartrate) Tablets, USP", font=font("arial.ttf", 62), fill=(20, 20, 20))
    d.text((140, 500), "50 mg", font=font("arialbd.ttf", 90), fill=(160, 20, 20))
    d.text((140, 630), "100 Tablets", font=font("arial.ttf", 54), fill=(20, 20, 20))
    d.text((140, 710), "\u201cKeep out of reach of children\u201d", font=font("arial.ttf", 44), fill=(20, 20, 20))
    d.text((820, 780), "Synthetic test image", font=font("arial.ttf", 26), fill=(120, 120, 120))
    img = img.rotate(-2, resample=Image.BICUBIC, expand=False, fillcolor=(205, 205, 200))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    px = img.load()
    for _ in range(40000):
        x, y = random.randrange(img.width), random.randrange(img.height)
        r, g, b = px[x, y]
        n = random.randint(-18, 18)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "JPEG", quality=88)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
