# CV2 candidate frozen before final scores

Choose profile cv2 at CV commit 806c9d0: intact enlarged RapidOCR plus Tesseract
5.5.4 with conservative line voting and generic field association. The shared
parser rejects date-shaped lots and false EXP prefixes, tolerates split keys,
and chooses an observed date when printed GS1 text agrees. Generic category
headings can outrank manufacturer logos; no product catalog or invented glyphs.

Development only: baseline complete clean/moderate/hard = 0/8,0/8,0/8;
upscale = 2/8,4/8,0/8; voting = 4/8,6/8,0/8. Voting wins the predeclared selection:
10/24 complete versus 6/24, with 26 versus 22 correct field observations.
Hard remains poor. The independent engine therefore justifies its optional
system dependency. Without its executable, the explicit cv2 profile falls back
to upscaled RapidOCR; that fallback is not the measured two-engine candidate.

Baseline final processing was queued earlier, but neither its predictions nor
scores have been opened. The selected CV bytes are now frozen; score this one
candidate once. Do not make field-rule edits after viewing final results.
The release gate remains no condition regression and at least one improvement
in complete-image normalized correctness. If it fails, baseline stays default.
Main's application integration was merged without changing these CV bytes.

Deployment safeguard, recorded before final scores were opened: resolve cv2 to
baseline when the Tesseract executable is absent. This supersedes the unscored
upscale fallback above. The archived scoring candidate runs with Tesseract
installed, so its recognition/field inference is unchanged. No final evidence
motivated this availability-only change. Tests cover both dependency states.
