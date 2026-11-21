# Public scan protocol v3 (written before D is scored on anything)

Reason: on the dev sets configs A, B and C gave identical results (`results/public_scan/dev_configs.json`): positives 42 correct,
9 wrong, 1 review, 10 timeout, 1 not identified; decoys 20 wrong of 45; device packs 1 wrong of 20. All three fail the
"zero wrong identifications" rule. The cause is the method: many strings are tried per photo and the best score over dozens
of strings can pass 0.65 by chance, helped by generic words ("tablets", "hydrochloride").

Unchanged: the matcher and its 0.65 threshold, configs A, B and C, the selection rule, the data and the split.

## D (the only addition)
D is the same pipeline plus a name-evidence check after the matcher.

1. Distinctive words, derived from the 30 reference products (no hand-written list). Source words: letters-only words of
   4 or more letters from the product name, its sourced aliases and the active substance field. A word is generic when
   any of these holds: it occurs in the names, aliases or active substance of 2 or more products; it occurs in a
   dosage form value of any product; it occurs in 10% or more of the 618 corpus chunks; it occurs in section headings of
   3 or more products. The derived generic list is printed by `python -m src.api.public_scan --words` and stored in
   `results/public_scan/derived_words.json`. Every product keeps at least one distinctive word (checked by a test).
2. A distinctive word counts as visible when an OCR word has normalized edit similarity (difflib ratio) of at least 0.85
   with it. The OCR text as a whole is searched.
3. Candidate strings: only strings of 1 to 5 words that contain a visible distinctive word (any product's). Fewer strings
   reach the matcher, which also cuts latency.
4. After the matcher: keep only the matcher's candidate products with at least one visible distinctive word. If none is
   left the result is not_identified (never a product). If the matcher said matched, the answer stays matched only when the
   top product has all its distinctive words visible and no other candidate has; otherwise it becomes needs_review with the
   remaining candidates, all-visible first. A matcher needs_review stays needs_review with the remaining candidates.
   A partly visible name (for example "valsartan" alone for "valsartan and hydrochlorothiazide") is never a confident match:
   that last rule (partial means review) is a design choice made here, before any scoring of D.
5. Tuned on dev only (dev_real and dev_device cached OCR). One config frozen in its own commit. Then fresh_real and the
   50 device photos run once each. A, B, C, D are reported side by side on dev, and the gate result whatever it is.
