import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

CONDS = sys.argv[2].split(",")
VARIANTS = ("base", "clahe", "vote_base_clahe", "flatten", "vote_base_flatten")


def clahe_rgb(image):
    import cv2

    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    lab[..., 0] = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(lab[..., 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def flatten(image):
    """Local contrast stretch: paper to white, local dark level to black, bounded gain."""
    import cv2
    import numpy as np

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    k = 2 * (max(15, round(0.085 * min(gray.shape))) // 2) + 1
    kernel = np.ones((k, k), np.uint8)
    smooth = cv2.GaussianBlur(gray, (0, 0), 1.0)
    paper = cv2.GaussianBlur(cv2.morphologyEx(smooth, cv2.MORPH_CLOSE, kernel), (0, 0), k / 4).astype(np.float32)
    dark = cv2.GaussianBlur(cv2.erode(smooth, kernel), (0, 0), k / 4).astype(np.float32)
    span = np.maximum(paper - dark, 1.0)
    gain = np.clip(255.0 / span, 1.0, 5.0)
    gain = np.where(span < 45, 1.0, gain)
    out = 255.0 - np.clip((paper - gray.astype(np.float32)) * gain, 0, 255)
    out = out.astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2RGB)


def work(job):
    import numpy as np
    from PIL import Image

    from src.cv.eval_v2 import FIELDS, edit_distance
    from src.cv.extract import TEMPLATE_PATH, map_fields
    from src.cv.ocr import read_text_default, vote_text
    from src.cv.preprocess import find_label_corners, find_label_corners_fallback, rectify_label

    p = Path(job)
    truth = json.loads(p.with_suffix(".json").read_text())
    tpl = json.loads(TEMPLATE_PATH.read_text())
    img = np.asarray(Image.open(p).convert("RGB"))
    c = find_label_corners(img)
    if c is None:
        c = find_label_corners_fallback(img)
    out = {"cond": truth["condition"], "seed": p.parts[-3]}
    if c is None:
        return out
    rect, _ = rectify_label(img, c)
    size = (rect.shape[1], rect.shape[0])
    readings = {"base": read_text_default(rect), "clahe": read_text_default(clahe_rgb(rect)),
                "flatten": read_text_default(flatten(rect))}

    def fields_of(blocks):
        f, _ = map_fields([b for b in blocks if b.conf >= 0.5], size, tpl)
        return f

    per = {k: fields_of(v) for k, v in readings.items()}
    # field-level vote by confidence between passes
    conf = {k: {b.text: b.conf for b in v} for k, v in readings.items()}
    for name, others in (("vote_base_clahe", ("base", "clahe")), ("vote_base_flatten", ("base", "flatten"))):
        merged = {}
        for f in FIELDS:
            cands = [(conf[o].get(per[o][f], 0), per[o][f]) for o in others if f in per[o]]
            if cands:
                merged[f] = max(cands)[1]
        per[name] = merged
    for name in VARIANTS:
        out[name] = sum(edit_distance(truth["fields"][f], per[name].get(f, "")) for f in FIELDS)
    return out


if __name__ == "__main__":
    jobs = [str(p) for ds in ("dev42", "dev43") for c in CONDS for p in sorted((Path("data/synthetic") / ds / c).glob("*.png"))]
    with ProcessPoolExecutor(int(sys.argv[1])) as ex:
        res = list(ex.map(work, jobs))
    for seed in ("dev42", "dev43"):
        for c in CONDS:
            rs = [r for r in res if r["cond"] == c and r["seed"] == seed and "base" in r]
            print(seed, c, f"n={len(rs)}", {v: sum(r[v] for r in rs) for v in VARIANTS})
