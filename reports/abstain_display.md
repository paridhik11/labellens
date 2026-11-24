# Abstain display in "Ask about its label" (public mode)

Repro: live DailyMed metoprolol (set id 17dbdf5f-d032-472a-9568-67689b08ef09, version 17), question "how to store it". Before: abstained with the text "No language model is running", score 0.0164, three unrelated dosing passages shown.

## Cause
1. The live label parser dropped How Supplied (LOINC 34069-5) and Storage and Handling (44425-7), so the label had 22 chunks and none about storage.
2. Live labels were asked with no score gate (`threshold=None`). A question with no shared wording scores 0.0164 (one retrieval system's rank-1 vote, 1/61) and fell through to the "no language model" fallback, which says nothing about relevance.

## Changes
- `src/api/live_dailymed.py`: `LIVE_CATEGORIES` adds the two storage codes for live labels only (the curated corpus and `CATEGORIES` are unchanged). Cache files carry `parser_version` 2; older cache files are fetched again on the next pick. `LABEL_GATE = 0.02` for one label's own retrieval. A gate miss keeps the closest quotes for a folded view. The AI answer job asks with `gated=False`, so "Ask AI" is still a real next step.
- `src/rag/pipeline.py`: in medicine mode a gate miss says "This label doesn't seem to answer that." The "No language model is running" text is only for `provider_off`. Professional text unchanged.
- `src/rag/query_rewrite.py`: "it", "its", "this" become the medicine name; storage-type words add "storage and handling, how supplied, store at". Retrieval only; the shown question is unchanged.
- `ui/js/ask-panel.js`: a low-confidence abstention (score under threshold) folds the passages behind "Show closest passages (low confidence)". DailyMed label citations read "Label section: <section title>" with "View in label"; regulation passages keep "21 CFR ..." and "View regulation".
- Tests: `tests/test_abstain_display.py`, `ui/tools/check_ask_panel.cjs`.

## Result on the repro (live, real models, port 8020)
| question | score | message | passages |
| --- | --- | --- | --- |
| how to store it | 0.0328 | no language model text (above the gate, answers from the storage section) | first passage is "16 HOW SUPPLIED/STORAGE AND HANDLING" |
| storage temperature | 0.0328 | same | "Store at 20 to 25 C ..." |
| how to repair a car engine | 0.0164 | This label doesn't seem to answer that. | folded |
| what is the capital of France | 0.0164 | This label doesn't seem to answer that. | folded |

The exact old failure (a label with no storage section) is the unit test `test_repro_gate_miss_says_the_label_does_not_answer`.

## Limits
- `LABEL_GATE` 0.02 comes from one label and 8 questions (off-topic 0.0164, on-topic 0.0306 to 0.0328). It is not tuned or evaluated. A question with some shared word but no real answer (for example "who makes the moon landing", 0.0307) passes the gate.
- The curated 30 products still ask without a gate; the same display problem can appear there.
- Adverse reactions (LOINC 34084-4) is also not chunked for live labels; "side effects" answers from other sections.
- Abstention metrics (`results/step16_abstention.md`, `step18_final.md`) are computed on the regulation corpus; that code path is unchanged (the gate branch still returns no quotes there).
- Live cache files made before this change need a new search and pick.
