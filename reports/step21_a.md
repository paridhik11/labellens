# Step 21a report: checker spec

**1. What I did.** I read the contracts, `schemas.py`, the CV extractor and consistency checker, the retrieval code, the API and the corpus, then wrote `docs/CHECKER_SPEC.md`. It has a rule table (16 rules in groups X, P, B, D, R, S), a precedence section, a citation procedure, the single retrieval setting, the 21b evaluation plan, and the gaps 21c will hit. No code was written.

**2. Files.** `docs/CHECKER_SPEC.md` (new, the spec). `reports/step21_a.md` (this report). Worktree `../labellens-checker`, branch `step21-checker`. Nothing committed.

**3. How it works.** Rules decide: each is deterministic and returns fail, needs_human, pass or not_applicable. Retrieval cites: each rule has a fixed query and a set of accepted sections. The first hit in the top 10 from an accepted section is cited, with a sentence copied verbatim from the chunk. If none qualifies there is no citation and `needs_human=True`. Symbol rules are needs_human in both directions while `symbol_detector_trusted` is False.

**4. How I verified it.** Spec only. Checked in `data/processed/regs.jsonl` (903 chunks, 435 device) that chunks exist for 801.1, 801.15, 801.18, 801.20, 801.40, 801.109 and 830.20 and read their text. Command: `python` script over `regs.jsonl` printing `chunk_id | section`; all ids in spec section 6 appeared. `git grep` found seeds 200, 201, 300 to 302 unused. No em dashes in the spec. Tests not run (no code).

**5. Check yourself.** (a) Section 3: severity and needs_human conditions per rule. (b) Section 9: the four open questions, mainly `passed` versus needs_human. (c) Section 8: no extraction table, no job store, `generateArtwork` mocked.

**6. Unsure or assumed.**
- Retrieval queries are untested; whether they rank the expected section is measured in 21b.
- GS1 check digit has no direct CFR text in the corpus, so B-GS1 is indirect.
- `rx_only` key in `extra` is my invention.
- `src/cv/barcode.py` imports cv2 and zxingcpp, which CI lacks, so I plan a small own `gs1.py` rather than importing it.
- You asked for Opus for planning; this session runs on Sonnet 5.5.
- The branch tracks origin/main, so push with an explicit `git push origin step21-checker`.
