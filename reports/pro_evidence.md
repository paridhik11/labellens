# Step 29: what changed, Evidence per field, button help

Branch `pro-evidence-changes`. UI only (`ui/pro/`), no backend change. No em dashes.

## What was built
1. **What changed.** `listProductVersions` and `getChange` are read after the product loads. Label versions has a "What changed" column and Activity history a "Detail" column: `L2: lot LOT1 -> LOT2 (change chg_...)`, `L1: first upload`, `Change requested: lot LOT1 -> LOT2`, `Record v2: lot LOT1 -> LOT2 (change ...)`. The text is a diff of two real record versions (empty and missing count as equal); a label version with no record change says so. The arrow is the character U+2192.
2. **Ask the regulations** (was "Evidence: search the device regulations").
   - One box, labelled "Regulation search (general)", sends the question to `askProfessional` (`POST /ask`). That route applies the scope rule and the Step 23 score gate (`e5b_top_score`, threshold 0.0315136, `data/rag/rag_config.json`), the same gate the public mode uses. Below the gate there are no passages and the page says: "No regulation passage answers this. Try a labeling question."
   - Three example buttons (expiration date, lot number, sterilization). Top 3 passages as compact cards (section, title, 2 line quote, "Open the regulation"); the rest of retrieval's top 10 under "Show more passages" (`POST /search`, only after the gate passed). Chunk ids and the gate score sit in a collapsed "details" row.
   - The old free "search" box (raw top 10 with no gate) is gone.
3. **Evidence for this field**, one button per record field (name, model, manufacturer, address, UDI-DI, sterilization, storage, lot, expiry, serial). The panel shows: 1. the record value, 2. the latest check result for that field from the real check result in this session (rules mapped in `FIELD_RULES`, which follows `src/checker/runner.py`; "No check has been run" when none; "No check rule looks at this field" for serial, storage, sterilization), 3. passages for one fixed question per field (`FIELD_QUESTION`, shown on the card). The card is titled "Evidence for <product name>" and says product facts come from the record and the check, regulation text from retrieval.
4. **Help text**, one line under Run check on L<n> ("Compares this label version with the product record using 16 rules."), Change a detail, Evidence and Refresh.

## Known gap, said plainly
The existing gate does not stop the example from the screenshot. `benefits of golden pump` scores 0.031545 against the threshold 0.031514, so it passes and shows the 3 closest passages (still labelled "Closest regulation passages ... no answer was written"). Clearly off-topic questions are stopped (`weather in Paris tomorrow` 0.01639, `best pizza recipe` 0.02649, `what is the capital of France` 0.02996). I did not add a second rule or move the threshold: the spec says the gate is weak (no abstention score reaches AUROC 0.90) and a rule fitted to one example would be overfitting. A lexical overlap rule does not help either (the top passages contain "pump" and "benefit"). Decision for Pari: leave it, or choose a rule and measure it.

## Verification
- `ui/tools/pro_e2e.cjs` on an isolated server (port 8020, throwaway database): 25/25 PASS, including the three new steps (Ask the regulations, what changed, ten fields). Real values from that run: first expiry passage `21 CFR 801.18`, lot panel `B-LOT:needs_human` with `21 CFR 801.40`, `name` and `model` and `serial` showed no passage (the gate stopped them), no response carried `X-Mock`.
- demo_e2e.py on the isolated server: 20 of 20 PASS, 0 fallback, no stage from mock JSON.
- Fast suite 1045 passed, 8 skipped, 5 deselected; ruff clean; `tests/test_pro_ui_static.py` (4 tests, ten fields have a question and a rule list, rule ids are real, no sample data or em dash in the evidence code, no threshold in the page).
- Browser look on `prd_f907c660` (Golden Pump, lot LOT1 to LOT2): Label versions reads `L2: lot LOT1 -> LOT2 (change chg_8c701078)` and `L1: first upload`.

## Unrelated finding
`product.version_created` in the audit log lists `changed_fields` for v2 that include fields that did not change (name, manufacturer, ...). The page does not use it (it diffs the versions), but the audit detail is misleading. Not touched.
