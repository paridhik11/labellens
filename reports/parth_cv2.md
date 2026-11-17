# CV2 report

Dev misses: OCR 7, parser 4, label-not-found 0, perspective 0. Perspective was
already connected. I upscaled intact crops, then compared independent Tesseract
voting and tolerant key/date rules. Dev complete frames: baseline 0/24, upscale
6/24, voting 10/24. Voting was frozen before final scoring.

| Condition | Baseline complete, 95% Wilson | CV2 complete, 95% Wilson |
|---|---|---|
| Clean | 0/96, 0-4% | 32/96, 25-43% |
| Moderate | 0/96, 0-4% | 27/96, 20-38% |
| Hard | 0/96, 0-4% | 17/96, 11-27% |

The frozen gate passes, so CV2 is the default. Each system had the same
300-second deadline; timeouts counted as misses. The 288 frames contain 198
unique images and four source families, so intervals do not generalize to
products or phone photos.

Previously exposed photos, n=10: name 1 to 1, lot 7 to 4, expiry 3 to 5; all
three remained 0 to 0. Lot regressed. References are LLM-generated, human review
is deferred, and real-symbol accuracy is unmeasured. No 80% real-photo claim is
justified. Details: results/cv_cv2_final_eval.md.
