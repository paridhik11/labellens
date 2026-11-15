import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

CONFIGS = {
    "pad50": dict(pad_ratios=(0.5,)),
    "pad30": dict(pad_ratios=(0.3,)),
    "dither15": dict(pad_ratios=(), dither_pad_ratios=(0.15,)),
    "dither30": dict(pad_ratios=(), dither_pad_ratios=(0.3,)),
    "vote_p50_p30_d15": dict(pad_ratios=(0.5, 0.3), dither_pad_ratios=(0.15,)),
    "vote_p50_d15_d30": dict(pad_ratios=(0.5,), dither_pad_ratios=(0.15, 0.3)),
    "pad50_w1800": dict(pad_ratios=(0.5,), target_width=1800),
    "vote_p50_d15_d30_w1800": dict(pad_ratios=(0.5,), dither_pad_ratios=(0.15, 0.3), target_width=1800),
}
CONDS = ("clean", "moderate", "hard", "hard_original", "very_hard")


def work(job):
    import numpy as np
    from PIL import Image

    from src.cv.diagnose import FIELDS, edit_distance
    from src.cv.extract import TEMPLATE_PATH, map_fields
    from src.cv.ocr import read_text_robust
    from src.cv.preprocess import find_label_corners, rectify_label

    p = Path(job)
    truth = json.loads(p.with_suffix(".json").read_text())
    tpl = json.loads(TEMPLATE_PATH.read_text())
    img = np.asarray(Image.open(p).convert("RGB"))
    c = find_label_corners(img)
    out = {"cond": truth["condition"], "seed": p.parts[-3]}
    if c is None:
        return out
    rect, _ = rectify_label(img, c)
    for name, kw in CONFIGS.items():
        blocks = read_text_robust(rect, **kw)
        fields, _ = map_fields(blocks, (rect.shape[1], rect.shape[0]), tpl)
        out[name] = {
            f: [edit_distance(truth["fields"][f], fields.get(f, "")), fields.get(f, ""), truth["fields"][f]]
            for f in FIELDS
        }
    return out


if __name__ == "__main__":
    jobs = [
        str(p) for ds in ("dev42", "dev43") for c in CONDS
        for p in sorted((Path("data/synthetic") / ds / c).glob("*.png"))
    ]
    with ProcessPoolExecutor(7) as ex:
        res = list(ex.map(work, jobs))
    json.dump(res, open(sys.argv[1], "w"))
    for name in CONFIGS:
        for seed in ("dev42", "dev43"):
            row = []
            for c in CONDS:
                rs = [r for r in res if r["cond"] == c and r["seed"] == seed and name in r]
                row.append(f"{c}:{sum(v[0] for r in rs for v in r[name].values())}(n={len(rs)})")
            print(name, seed, " ".join(row))
