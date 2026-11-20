# Step 22d report: log and state

- `docs/LEARNING_LOG.md`: entries for 22b and 22c (22a was added earlier).
- `CLAUDE.md`: Step 22 line in the current state (not merged, limits listed).
- Reports `reports/step22_a.md` to `step22_d.md`, each under 400 words.

**Branch state:** `step22-change` has origin/main merged (Step 17 and 18), then 22a spec, 22b code, 22c API. Nothing merged into main, nothing pushed to any other branch.

**Verified:** full fast suite 544 passed, 4 skipped; ruff clean (see 22c).

**Open items for you**
1. Merge step22-change into main when ready (CI not yet checked after the last push).
2. Parth: the contract now expects `generateArtwork` to consume a confirmed assessment's barcode decision; no `src/gen` change was made.
3. Measure citation hit rate per field with the real hybrid retriever (not done).
4. Install `zxingcpp` in a venv to run the payload parity test.
5. A model change always waits for a new udi_di edit; revisit if a rename without a new DI is common.
