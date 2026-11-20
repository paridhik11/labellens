# Parth Task 7a: independent perspective correction

## 1. What I did
Added standalone label flattening at the supplied template aspect ratio. Reused existing pixel-based boundary detectors without changing them or the extractor. Tested rotation and perspective, invalid dimensions, absent boundaries, coordinate mapping and deterministic output.

## 2. Files created or changed
- `src/cv/perspective.py`: correction result, template-ratio warp and per-condition scorer.
- `scripts/cv_experiments/eval_perspective.py`: reproducible three-seed benchmark and local JSON evidence.
- `tests/test_perspective.py`: 13 tests, including aggregation and CLI behavior.
- CV README and learning log: usage, verification and limits.

## 3. How it works
Four detected corners are mapped into a rectangle. For a 100 x 60 mm template, a 1000-pixel width produces a 600-pixel height. No ground-truth corners enter detection. Success requires every corner within 10 source-image pixels of generated truth; missing detections remain in the denominator.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m scripts.cv_experiments.eval_perspective
clean: detected=30/30, within_10px=30/30
moderate: detected=30/30, within_10px=30/30
hard: detected=30/30, within_10px=30/30
```
Seeds 7001, 7002, 7003; ten base labels per seed, each in three conditions. Success rate: 100% separately in each condition. Raw per-seed results: local data/synthetic/perspective_task7a/evaluation.json. This measures geometry, not OCR improvement.
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
436 passed, 3 deselected in 158.85s (0:02:38)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real scripts/cv_experiments/eval_perspective.py
All checks passed!
```

## 5. What you should check yourself
Review the homography corner assertions, fixed aspect ratio and no-boundary result. Confirm extractor and preprocessing files are unchanged.

## 6. What I am unsure about or assumed
One synthetic template family with roughly upright labels and visible dominant boundaries. No orientation recognition, arbitrary 90/180-degree correction or real-photo success claim. A missing boundary returns None. Supplied aspect ratio must be trusted. The existing extractor has not been connected to this module. Photo extraction remains deferred: name 1/10, lot 0/10, expiry 0/10; human spot-check deferred, NOT_RUN.
