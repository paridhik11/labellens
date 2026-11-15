# Symbol detector v2 (branch `cv-symbols`)

Goal: find the manufacturer and use-by (hourglass) pictograms on a label without knowing the artwork or the
position, so the detector is not tied to our own synthetic drawings. Numbers live in
`results/symbols_experiments.md` and `reports/symbols_*.md`; this page explains the pieces.

## Pieces

| Piece | File | What it does |
| --- | --- | --- |
| Style library | `src/gen/symbol_styles.py` | Both pictograms (and 6 wrong-symbol distractors) in many styles: render mode (outline, filled, duo, badge), stroke weight, rounding, and five factory and five hourglass geometry families. Styles are split `train`, `dev` and `heldout`. |
| Styled labels | `src/gen/generate_styled.py` | Whole-label photos (clean, moderate, hard, very hard) with styled symbols at random places (`random`) or beside their text (`anchored`), plus `empty` and `distractor` negatives. |
| Procedural symbols | `src/gen/symbol_procedural.py` | Random jittered variants of the *seen* geometry families, for the CNN. |
| Harness | `src/cv/symbol_eval.py` | Straightens each photo like `extract_label` does, runs any detector on the whole label, projects boxes back and scores IoU >= 0.5. |
| Candidates | `src/cv/symbols_v2/candidates.py` | Ink map relative to local paper level, connected blobs of pictogram size. No template positions. |
| Scorers | `refs.py`, `matchers.py`, `cnn.py` | Hole-filled silhouette overlap with a reference bank, SIFT or ORB keypoints with RANSAC, a small CNN. |
| Anchors | `anchors.py` | OCR lines that anchor each pictogram (the EXP line, the line above the address) and a proximity test. |
| Detector | `detector.py`, `__init__.py` | `featurize` (slow, cacheable) then `decide` (rule), same call shape as `detect_symbols_blind`. |
| Experiments | `experiment.py`, `scripts/symbols/` | Feature caching, rule sweeps, the held-out guard. |

## Honest limits

* Every style, train, dev and held-out, was drawn by one author. A held-out style is unseen by the detector, not
  independent of that author's idea of a pictogram. The real-artwork checks (`scripts/symbols/real_symbol_sources.json`)
  are the independent evidence.
* Truth boxes of styled symbols are the glyph's tight ink box, not the square slot (the slot overstates narrow glyphs).
* The held-out styles were scored once per frozen variant. Every use is in `results/heldout_log.jsonl`.
* Confidence values are scores, not calibrated probabilities.

## Using it

```python
from src.cv.symbols_v2 import detect_symbols_v2
detections = detect_symbols_v2(upright_rgb_label)           # same shape as detect_symbols_blind

from src.cv.extract import extract_label
extract_label("photo.png", mode="blind", symbol_detector="v2")   # default "v1" is unchanged
```
