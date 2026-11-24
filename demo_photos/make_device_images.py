"""Make demo device images from golden/golden_label.pdf (originals untouched): a photo-style clean image and a blurry one."""
import sys
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter

ROOT = Path(r"C:\Users\parid\Downloads\labellens\labellens")
sys.path.insert(0, str(ROOT))
out = ROOT / "demo_photos" / "device"
page = pdfium.PdfDocument(str(ROOT / "golden" / "golden_label.pdf"))[0]
w, h = page.get_size()
label = page.render(scale=min(300 / 72, 3000 / max(w, h))).to_pil().convert("RGB")

# a desk: dark mid-grey with a soft gradient and a little grain, label placed on it with a 2 degree tilt
W, H = int(label.width * 1.5), int(label.height * 1.5)
yy, xx = np.mgrid[0:H, 0:W]
desk = (90 + 12 * (xx / W) + 8 * (yy / H))[..., None].repeat(3, axis=2)
rng = np.random.default_rng(7)
desk = np.clip(desk + rng.normal(0, 0.0, desk.shape), 0, 255).astype("uint8")
canvas = Image.fromarray(desk)
tilted = label.rotate(2, expand=True, resample=Image.BICUBIC, fillcolor=(95, 95, 95))
canvas.paste(tilted, ((W - tilted.width) // 2, (H - tilted.height) // 2))
canvas.convert("RGB").save(out / "02_golden_photo_clean.jpg", quality=92)

blur = canvas.filter(ImageFilter.GaussianBlur(radius=4))
blur.convert("RGB").save(out / "03_golden_blurry.jpg", quality=90)

from src.api.quality import assess_photo  # read only: the same gate the app uses

for name in ("02_golden_photo_clean.jpg", "03_golden_blurry.jpg"):
    rep = assess_photo(out / name)
    print(name, "ok" if rep.ok else "REJECT", rep.reasons, {k: round(v, 1) for k, v in rep.metrics.items()})
