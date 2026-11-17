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
system dependency. Without its executable, the cv2 profile resolves to the established baseline.
The two-engine candidate is measured only with Tesseract installed.

The frozen final gate passed: complete-image normalized correctness improved
from baseline 0/96 in each condition to 32/96 clean, 27/96 moderate and 17/96
hard. CV2 is the default profile. The explicit baseline is still callable, and
an unavailable Tesseract executable resolves CV2 to baseline. The final result
did not trigger field-rule changes.

Deployment safeguard, recorded before final scores were opened: resolve cv2 to
baseline when the Tesseract executable is absent. The archived scoring candidate runs with Tesseract
installed, so its recognition/field inference is unchanged. No final evidence
motivated this availability-only change. Tests cover both dependency states.
