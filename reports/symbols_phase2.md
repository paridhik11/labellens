# Symbols, phase 2: detector v2 without learning

**What I did.** `src/cv/symbols_v2` finds pictogram-sized blobs anywhere on the label (ink relative to local paper level,
connected blobs, no template positions) and compares each blob with a bank of train-style references. Two scorers:
hole-filled silhouette overlap (an outline and a filled drawing share a silhouette) and SIFT or ORB keypoints with RANSAC.
`detect_symbols_v2(image)` has the same call shape as `detect_symbols_blind`; `extract_label(..., symbol_detector="v2")` selects it
(default `"v1"`, behaviour unchanged, tested).

**Dev results** (4 dev styles, 256 symbols, 480 absent symbols; settings chosen on dev):

| Idea | Recall | False positives |
| --- | --- | --- |
| v1 baseline | 4/256 (1.6%) | 0/480 |
| silhouette (train bank) | 241/256 (94.1%; 90.6 to 96.4) | 1/480 (0.2%) |
| SIFT | 35/256 (13.7%) | 9/480 (1.9%) |
| ORB | 39/256 (15.2%) | 137/480 (28.5%) |

Silhouette overlap is the clear winner; keypoints do not work on flat pictograms with few corners (few stable keypoints).
Very hard images (glare, opaque bars) cap recall at 79.7%.

**Files.** `src/cv/symbols_v2/{candidates,refs,matchers,detector,experiment,registry,__init__}.py`, `src/cv/extract.py`
(option), tests (`test_symbols_v2.py`, one added to `test_extract.py`), `scripts/symbols/{sweep,dev_table}.py`.

**Check yourself.** Reference bank only reads train and dev styles (tested); the very-hard misses are really occluded.

**Unsure.** Dev geometry includes two families no train style has, but all drawings are one author's.
