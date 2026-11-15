import json, sys
from pathlib import Path
import cv2, numpy as np, zxingcpp
from PIL import Image
from src.cv.barcode import parse_gs1
DM = zxingcpp.BarcodeFormat.DataMatrix
def dec(g, **kw):
    for r in zxingcpp.read_barcodes(g, formats=DM, **kw):
        if r.content_type == zxingcpp.ContentType.GS1:
            try: return parse_gs1(r.bytes.decode("latin-1"))
            except ValueError: pass
    return None
methods = {
 "raw": lambda g: g,
 "g1": lambda g: cv2.GaussianBlur(g,(0,0),1.0),
 "g2": lambda g: cv2.GaussianBlur(g,(0,0),2.0),
 "g3": lambda g: cv2.GaussianBlur(g,(0,0),3.0),
 "half": lambda g: cv2.resize(g,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA),
 "third": lambda g: cv2.resize(g,None,fx=1/3,fy=1/3,interpolation=cv2.INTER_AREA),
 "med5": lambda g: cv2.medianBlur(g,5),
 "g2ad": lambda g: cv2.adaptiveThreshold(cv2.GaussianBlur(g,(0,0),2.0),255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,51,0),
 "g1.5ad": lambda g: cv2.adaptiveThreshold(cv2.GaussianBlur(g,(0,0),1.5),255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,51,0),
 "half_ad": lambda g: cv2.adaptiveThreshold(cv2.resize(g,None,fx=.5,fy=.5,interpolation=cv2.INTER_AREA),255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,0),
}
for ds in ("dev42","dev43"):
  for cond in sys.argv[1:]:
    root = Path("data/synthetic")/ds/cond
    hits = {m: 0 for m in methods}; anyhit = 0; fails = []
    for p in sorted(root.glob("*.png")):
        truth = json.loads(p.with_suffix(".json").read_text())["barcode_ais"]
        g = cv2.cvtColor(np.asarray(Image.open(p).convert("RGB")), cv2.COLOR_RGB2GRAY)
        ok = False
        for m, f in methods.items():
            r = dec(f(g))
            if r == truth: hits[m] += 1; ok = True
            elif r is not None: print("WRONG DECODE", p.name, m)
        anyhit += ok
        if not ok: fails.append(p.stem[11:14])
    print(ds, cond, hits, "any:", anyhit, "fails:", fails)
