import json
from pathlib import Path

import numpy as np
from PIL import Image

from src.cv.preprocess import find_label_corners, find_label_corners_fallback

for ds in ("dev42", "dev43"):
    for cond in ("moderate", "hard", "very_hard"):
        errs_strict, errs_fb, none = [], [], 0
        for p in sorted((Path("data/synthetic") / ds / cond).glob("*.png")):
            t = json.loads(p.with_suffix(".json").read_text())
            img = np.asarray(Image.open(p).convert("RGB"))
            truth = np.asarray(t["label_quad_px"])
            c = find_label_corners(img)
            f = find_label_corners_fallback(img)
            if c is not None:
                errs_strict.append(np.linalg.norm(c - truth, axis=1).max())
            if f is None:
                none += 1
            else:
                errs_fb.append(np.linalg.norm(f - truth, axis=1).max())
        fb = np.asarray(errs_fb)
        print(ds, cond, "strict found", len(errs_strict), "max", round(max(errs_strict), 1) if errs_strict else None,
              "| fallback found", len(fb), "none", none, "<=10px", int((fb <= 10).sum()),
              "median", round(float(np.median(fb)), 1) if len(fb) else None, "worst", np.round(np.sort(fb)[-4:], 1))
