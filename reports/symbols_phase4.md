# Symbols, phase 4: zero-shot CLIP (run because the CNN missed 0.90 on held-out)

**What I did.** The CNN reached 63.5% on held-out styles, below 0.90, so, as agreed, I ran a CLIP check
(`openai/clip-vit-base-patch32`, about 600 MB downloaded once with your approval, CPU, 4 threads or fewer). Each candidate crop is drawn
black on white and compared with text prompts for the two pictograms and ten wrong things (warning triangle, thermometer,
umbrella, prohibition sign, sun, glass, letters, barcode, plain shape, noise). A crop is accepted for a name when that
prompt's softmax share is at least a threshold. No training on our drawings. The threshold (0.4) was chosen on dev and
frozen (commit 2e3f3cb) before any held-out look.

**Dev:** 229/256 (89.5%; 85.1 to 92.6), 0/480 false positives.

**Held-out styles (scored once):** 308/384 (80.2%; 75.9 to 83.9), false positives 27/640 (4.2%; 2.9 to 6.1). It is the best
generaliser: the white-on-black badge style that scored 0% with the silhouette and CNN gets 59/64 (92.2%). It also leads on real
artwork (206/336, 61.3%) and on held-out styles beside text (148/192, 77.1%; FP 5.0%). It does not meet the 90% and 2% targets, and
it is weakest on the tower and framed-glass outline style (h3, 53%) and the gable and triangle filled style (h1, 50%).

**Cost.** About 0.1 to 0.5 s per candidate on CPU, 600 MB of weights, and a threshold that trades recall for false positives
steeply (0.3: 92% and 2.3% FP; 0.5: 80% and 0 FP on dev).

**Files.** `src/cv/symbols_v2/clip_zero_shot.py`, `scripts/symbols/clip_eval.py`, `run_final_clip.sh`,
`results/symbols_frozen_clip.json`.

**Unsure.** The prompts are my wording and untuned; a better prompt for the factory (CLIP confuses it with a thermometer on
the simplest style) might help, but would need a new frozen run.
