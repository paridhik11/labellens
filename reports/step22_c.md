# Step 22c report: API wiring

Branch step22-change.

**Built**
- `src/api/changes.py`: `POST /changes` parses (`edits`, or `raw_text` through the rules, or the optional provider on `app.state.edit_provider`, default None), creates the change, assesses it twice (as proposed, as if confirmed) and stores one assessment.
- Tables `change_assessments` and `change_confirmations` (append-only triggers). `Review.assessment_id` column (added to older databases by `_add_missing_columns`, which now skips tables that do not exist yet).
- `confirmChange` is real: 404, 409 `change_closed` and `nothing_to_confirm`, 422 `parse_not_confirmed`, `edits_not_supported`, `unknown_impact`. The first confirmation appends the confirmed assessment, so `confirm_lot` becomes REGENERATE through the API. `parse_state` is derived from confirmations.
- `listAffectedLabels` is real. Both fall back to the mock (`X-Mock: true`) for a change with no stored assessment, such as the seed's `chg_0002`.
- Approve needs a confirmed assessment (`409 change_not_confirmed`) when the change has one; a review stores the latest `assessment_id`.
- `openapi.yaml` (CR-18), one new mock (`assess_rules.json`), DATA_MODEL, API.md, SCREENS.md, SCHEMA_CHANGE_REQUESTS.
- Behaviour kept: unparseable text is `422 parser_not_implemented` with `details.issues`; unknown or invalid edits only gives `201` with `parser: not_implemented` and `unassessed_edits`.

**Verified**
`python -m pytest -q -m "not slow"` -> `544 passed, 4 skipped, 3 deselected in 38.00s` (first run had 7 failures from old assumptions, all updated and listed below). `ruff check src tests` -> All checks passed. New: `tests/test_api_changes.py` (15), contract run extended to every documented status of confirmChange and listAffectedLabels.

**Existing tests I changed (old behaviour was "not implemented")**: endpoints (assessed by rules, approve needs confirm), persistence (two new tables), mock-fallback count, mock citation metadata, SCREENS listing, old-database column test.

**Not verified / caveats**
- Real default retrieval (hybrid, dense model) was not exercised in these tests; they use bm25. Citation lookup failure is handled but the real-corpus citation hit rate per field is not measured.
- Renderer payload parity test still skipped (no `zxingcpp`).
- `generateArtwork` is still a mock, so nothing consumes REGENERATE yet.
