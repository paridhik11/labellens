# Symbols, phase 3: learned classifier

**What I did.** A small CNN (three conv blocks, about 60 thousand weights, CPU only, 4 torch threads or fewer) classifies each
candidate crop as manufacturer, expiry or other. Input is two 48 by 48 channels from the crop's ink map (ink and
hole-filled silhouette), so lighting and polarity do not matter. Training crops: 4,000 per class of random
pictograms (jittered saw-tooth and flat-block factories, straight and curved hourglasses, outline or filled or duo,
stroke 3 to 11%) printed on noisy canvases and pushed through the *same* candidate finder, with distractors, random shapes
and letters as "other", plus crops mined from train-split labels. Dev, held-out and badge styles are never used in training.

**Dev result** (256 symbols, 480 absent symbols): 241/256 (94.1%; 90.6 to 96.4), very hard 51/64 (79.7%),
false positives 0/480 (0.0%; 0.0 to 0.8). Identical recall to silhouette overlap (94.1%), one fewer false positive.
A procedural-only model scored the same, so the mined crops did not matter on dev.

**What it means.** Both detectors are limited by the candidate finder and by glare and occlusion, not by classification.
Whether the CNN generalises better than the silhouette bank is a held-out question, answered once at the end.

**Files.** `src/cv/symbols_v2/cnn.py`, `train_data.py`, `src/gen/symbol_procedural.py`, `src/cv/test_symbols_cnn.py` (3 tests),
`requirements-cv.txt` (`torch==2.15.0`, CPU, only for this classifier). Weights are in ignored `data/models/` and rebuilt with
`python -m src.cv.symbols_v2.cnn train --mined data/synthetic/styled_train`.

**Unsure.** The seen families (saw-tooth, block, straight and curved glass) are my choice, so "unseen" is relative to them.
