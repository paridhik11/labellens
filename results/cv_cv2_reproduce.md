# CV2 reproducibility and interpretation

Use the labellens-cv Conda environment, Python 3.12. The optional independent
engine was Tesseract 5.5.4 with eng trained data. Exact RapidOCR model fingerprints
and the selected CV source hash are in scripts/cv_experiments/config/cv2_candidate.json.
No new Python OCR package is required. The system binary is optional; minimal CI
imports extraction without CV packages. Missing Tesseract resolves a cv2 call to the established baseline,
not to unscored upscaling. This availability-only safeguard was added before
final scores were opened; it does not change inference with Tesseract installed.
The baseline remains explicitly available via photo_profile="baseline".

## Fixed source material

Fetch pinned artwork using `python scripts/real/fetch_dailymed.py`.
The committed cv2.json predates all final scoring. It pins source SHA-256 values,
crop coordinates, LLM transcriptions, family separation, seeds and conditions.
Four dev sources from three families yield 24 frames; six final sources from
four different families yield 288 frames. Clean is an identity transform:
96 clean frames are six unique images repeated 16 times. Moderate and hard each
have 96 unique frames. Total unique final images: 198. Hard maps to very_hard
augmentation, including perspective, blur, noise, uneven lighting and glare.
No annotations or product dictionary are passed into extraction.

Only nonempty, actually visible reference fields are scored. Final product names
have n=96 per condition; lot and expiry each have n=48, from the three PROPEL
artworks, which share a printed example lot. This is not broad batch-code coverage.
Strict exact and predeclared case/spacing/trademark-normalized counts are both
reported. No O/0 equivalence is applied to scored identifiers. Wilson 95% intervals
are descriptive, conditional frame intervals. Correlated frames, repeated source
artwork and LLM reference uncertainty invalidate population-level interpretation.
Clean additionally has only six unique images; its frame interval is especially
optimistic. No unseen real phone-photo accuracy or symbol accuracy is established.

## Commands

Run from the repository root. These commands create immutable outputs; do not
reuse the final set to tune, delete score locks or retry a candidate after seeing
its score. Existing identical clean pixels reuse one prediction in the candidate
runner without changing the declared frame denominators. The baseline's earlier
queued runner evaluated repeated clean frames separately; its results stayed
sealed until the candidate was selected.

```sh
python -m scripts.cv_experiments.cv2_benchmark --build --split dev --output data/synthetic/cv2_dev
python -m scripts.cv_experiments.cv2_benchmark --build --split final --output data/synthetic/cv2_final
mkdir -p /tmp/ll_cv2_baseline /tmp/ll_cv2_candidate
git archive d39b0fb | tar -x -C /tmp/ll_cv2_baseline
git archive 806c9d0 | tar -x -C /tmp/ll_cv2_candidate
python -m scripts.cv_experiments.cv2_benchmark --dataset data/synthetic/cv2_final --code-root /tmp/ll_cv2_baseline --profile baseline --workers 3 --output data/synthetic/cv2_final_baseline.json
python -m scripts.cv_experiments.cv2_benchmark --dataset data/synthetic/cv2_final --code-root /tmp/ll_cv2_candidate --profile cv2 --workers 5 --output data/synthetic/cv2_final_vote.json
python -m scripts.cv_experiments.cv2_benchmark --before data/synthetic/cv2_final_baseline.json --after data/synthetic/cv2_final_vote.json --output results/cv_cv2_final_eval.md
python -m src.gen.golden
```

Baseline was queued asynchronously before candidate selection but its scores
were not inspected. Candidate 806c9d0 was selected solely from dev results and
frozen in e1f30ca before the candidate's single final run. CV code did not change
when newer main application integration was merged. The release decision changes
only the default profile if the frozen complete-image gate passes; no field rule
is tuned from final results. The explicit baseline remains callable.

## Previously exposed online photos

The original ten online package images are a convenience check, not newly taken
phone captures or an unseen holdout. Six were used for the initial error analysis;
all ten had been exposed in earlier work. Original references and source files
remain unchanged. Strict counts use the same reference text and printed-key
removal as the earlier real-photo protocol. Source acquisition metadata stays in
data/real/SOURCES.md. Human spot-check of 01,04,08 and human
symbol-crop review remain deferred. LLM-generated labels are not human truth;
real-photo symbol accuracy is unmeasured. Synthetic or artwork success must not
be reported as real-photo accuracy.
