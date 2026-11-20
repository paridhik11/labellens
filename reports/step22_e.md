# Step 22e report: seed, citation hit@10, parity

**Seed.** `chg_0002` now has a stored assessment (real rules, no retriever, so no citations) and a confirmation made by the demo editor. Reason: a seeded confirmed assessment lets a reviewer approve the seeded L3 on the real server, and it comes from the same code path as any other change, not a canned payload. Test: `test_seeded_demo_change_can_be_approved_end_to_end` (approve L3, the Review stores the confirmed `assessment_id`, the change turns `reviewed`). Tests that relied on the seeded change having no assessment now create an older change directly.

**Citation hit@10** (`python -m src.change.measure_citations`, full table in `reports/step22_e_table.md`). One fixed query per requirement, accepted section as in `CHANGE_SPEC.md`, k = 10, device chunks only.

| Requirement | Frozen E5b rank | Plain hybrid rank |
|---|---|---|
| manufacturer, manufacturer_address (801.1) | 1, 1 | 1, 1 |
| udi_di (801.20) | 1 | 1 |
| model (830.50) | 2 | 2 |
| lot, serial, expiry (801.40) | 3, 3, 3 | 1, 1, 1 |
| expiry format (801.18) | 1 | 1 |
| rx_only (801.109) | 1 | 1 |

Both configs hit 9 of 9. Caveats: n is 1 per requirement, so this is a sanity check of the fixed queries, not a rate. Queries were fixed before running and not tuned. A hit means the accepted section was in the top 10, not that the quote is the best sentence. Sterilization, storage, name and ref have no citation by design. The API still uses plain hybrid (the checker only supports bge-small), so E5b is measured here but not wired in. The bge-large device cache took 29 minutes to build and is git-ignored.

**Parity.** `.venv-cv` (git-ignored, from `src/gen/requirements-cv.txt` plus API packages): `pytest tests/test_change.py` gave `67 passed`, none skipped, so `build_ais` equals the renderer's `record_content` payload.
