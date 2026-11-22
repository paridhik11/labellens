# Live DailyMed lookup: evaluation protocol (written before scoring)

Fixed before any eval name was sent to DailyMed or to the system. The set is `data/eval/live_dailymed_set.json`
(30 products, 10 decoys). The names were chosen from my own knowledge of common products. Their active ingredients
are not among the 30 curated products, the 100 med100 candidates (`med100_candidates.tsv` on branch med100) or the
public scan names. Development used other names (cetirizine, Zyrtec, Dexcom as a raw API probe only).

## What is scored
Per query the harness runs the same code as the API, in this order:
1. Local match (`ProductMatcher`, unchanged threshold 0.65). Outcome `matched` for any eval name is a **local false
   accept**: a curated product would be shown as the answer.
2. Live search (`search_labels`, human Rx and OTC labels only). Candidates are listed, never auto-picked.
3. Scripted person: picks the first listed candidate whose title contains the expected ingredient (case-insensitive).
   No match in the list means the product is `not_found` (a recall failure, not a safety failure). Decoys have no
   expected ingredient, so the person picks nothing; a decoy passes only when the **list itself is empty**
   (outcome `no_candidates`) and the local outcome is not `matched`.
4. Fetch, parse, chunk, embed (E5b recipe) the picked label; answer two fixed questions
   ("What is {name} used for?", "What are the warnings for {name}?") with the default extractive mode.

## Gate (all must hold, no threshold loosened afterwards)
- G1: 0 wrong-product answers shown as correct. Wrong product = local false accept; or a fetched label whose SPL
  product names and title do not contain the expected ingredient; or any answer shown for a decoy.
- G2: every shown citation verified: its chunk id belongs to the picked label, its quote is a verbatim substring of
  that chunk text, and the answer's set id equals the picked set id.
- G3: 10 of 10 decoys rejected as defined in step 3.
- G4: median fetch-to-answer time (pick to first answer, cold cache) reported. No pass/fail threshold on it.

## Reported, not gated
Product-level result with Wilson 95% intervals: found (right label in the list), fetched, answered with at least
one citation. Each is out of 30. Network failures are reported as failures, not retried beyond the client's own
retry rule (one retry). Run once; if a run is disturbed (network down), it is reported as disturbed, not re-scored
after looking at results.

## Limits stated in advance
Typed names are correct spellings (no fuzzy matching). The picker is a script, not a person. Answer relevance is
not graded. DailyMed contents change daily, so the numbers are a snapshot on the run date.
