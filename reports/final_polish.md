# Final polish for the live demo

Branch `final-polish` from `main` (ae365eb), merged into `main` locally, not pushed. Every number below was measured in this session on this PC (14 logical CPUs, 32 GB), server `scripts/run_demo.py --port 8040`, unless the line says otherwise. Indexes, scoring, qrels, evaluation files and the global gate (0.0315) are unchanged.

## Decisions taken without asking

- **Product filter lives on the server (CR-29, additive).** `POST /ask` takes an optional `product_id`; the server drops sections that only govern other products and keeps one chunk per section before anything is shown or sent to the model. The gate reads the unfiltered top hit, so it is unchanged. Table: 801.435 latex condoms (from the request), plus 801.430 tampons and 809.10 in vitro diagnostics, both seen in the rehearsal for Golden Pump.
- **Model-off answers are not abstentions on screen.** The wire format still says `abstained: true` (contract unchanged); the page decides the wording: score under the gate means "This label doesn't seem to answer that." (passages folded), anything else with passages means "Closest passages from the label" (or "Closest regulation passages"). Score and gate only in a small details line.
- **AI time limit 170 s on the server, 180 s wait on the pages.** A cold model needs about a minute to load. `scripts/run_demo.py` loads the model at start when Ollama runs.
- **The live cache key carries the chunking version** (`live_<id>_v<n>.c3.json`); old cache files are ignored and refetched.
- **Photo name lookup is strict.** A word counts only if it sits within two lines of a strength ("50 mg"), and a DailyMed label is proposed only if its product or generic name starts with that word. Loose versions proposed wrong labels ("PHARMACY" gave "GOOD NEIGHBOR PHARMACY NASAL ALLERGY", "drink" gave "DRINK EASE"), so I kept the strict one.
- **Photos with only below-threshold candidates** no longer list those candidates (no percentages); they go to the same name lookup.
- **Curated 30: no gate** (re-measured, see P2.9).
- **The Retrieval lab stays raw**, labelled "raw retrieval, unfiltered".
- **pro_e2e writes outside the repo** (`OUT`, default `<temp>/labellens_pro_e2e`). The leftover PNGs and the modified `results.json` from the earlier run were moved to the scratchpad and the tracked file restored before branching.
- **Windows background throttling:** the first server, started as a background shell process, needed 30 minutes to embed one label (about 1 core). The same encoding in a foreground process took 77 to 90 s. The rest of the session ran the server in a Terminal tab.

## Per item: before and after

| # | Before | After | Test |
|---|---|---|---|
| P1.1 | "what must a label show for the expiration date?" on Golden Pump listed 21 CFR 801.435 (latex condoms) twice, also in Ask with AI | 801.18 first, 801.435 gone, each section once, in the passages, in "Show more" and in the AI context; the AI answer cites 801.18 only. Retrieval lab labelled "raw retrieval, unfiltered" | `tests/test_applicability.py`, pro_e2e steps 06, 06b, 06c, 10c |
| P1.2 | Public: a name outside the 30 then Ask said "No label loaded" | "Pick a medicine first", DailyMed searched for the typed name at once, "Use this label" fetches it, ask again | `tests/test_final_polish_ui.py`, rehearsal P3 |
| P1.3 | metoprolol "how to store it": "Abstained: needs_human_check" beside score 0.0328 (gate 0.02) | Cause: not a stale cache or retrieval; the score passed the gate, the answer was the model-off extractive fallback (`provider_off`) which goes out as `abstained: true`, and the page printed that as "Abstained". Now "Closest passages from the label", first quote "Store at 20° to 25°C ...". The quote was also wrong (the reranker preferred "Tablets are available as follows" for the expanded query); quotes now use the person's own question (`quote_question`) | `tests/test_live_versioning.py`, `ui/tools/check_ask_panel.cjs`, rehearsal |
| P1.4 | First DailyMed fetch 34 to 131 s with little feedback | Fetch card shows "N s elapsed" every second plus the job message; `scripts/warm_demo_cache.py` and `run_demo.py --warm` prefetch pregabalin, Zetia, metoprolol, Lopressor. Warm run: Zetia 44.7 s, metoprolol 67.1 s, Lopressor 42.7 s, pregabalin 1.1 s (already cached); later fetches of these labels are about 1 to 2 s | `tests/test_warm_demo_cache.py` |
| P1.5 | AI wait 180 s only on the Pro page, server limit 90 s, no warm-up | Both pages wait 180 s with "Model is loading, first run can take about a minute" and elapsed seconds; server limit 170 s; model warmed at start. Measured through the API on Golden Pump: cold model (after `ollama stop`) 44.6 s, warm 15.2 s, both verified answers citing 801.18 only. In pro_e2e: 56.7 s (busy PC) and 13.7 s | `tests/test_ai_mode.py`, pro_e2e 06b, 06b2 |
| P2.6 | Per-field "Evidence for this field" buttons | "Findings by field" cards in Check and read-only in Review: field, product value, result, rule ids with outcomes, top passage (cited by the rule, or "Search used: ..." in grey), more behind "Show related passages", text clamped. "Run check" when no check exists. Export has a findings report (.txt) with every finding, rule id and cited passage | pro_e2e 10c, 13, 14, 15 |
| P2.7 | "Authenticity not verified" twice on P2; label citations "21 CFR labelling/34067-9/4" | Once (page header only); "Label section: <title>" with "View in label" everywhere in public mode | `tests/test_final_polish_ui.py`, rehearsal checks |
| P2.8 | A pack outside the 30 with no NDC in the table ended "Not identified"; Tesseract output decoded with the Windows code page | Synthetic `demo_photos/public/12_synthetic_lopressor.jpg` (NDC 12345-678-90): "Is this LOPRESSOR (METOPROLOL TARTRATE) tablet?" with Confirm, Not this one, Type the name; Confirm fetched the label in 1.9 s (warmed). Nothing is confirmed by itself; no candidate with a percentage. UTF-8 decoding: with the old decoding Python raised a decode error on Tesseract's closing quote, so that OCR engine failed on this image; now the lines read `LOPRESSOR®` and `“Keep out of reach of children”` | `ui/tools/check_name_guess.cjs`, `ui/tools/check_photo_lookup_live.cjs`, regression below |
| P2.9 | Live labels had no Adverse Reactions; "side effects" answered from other sections | 34084-4 chunked for live labels (warnings were already in); "side effects" adds "adverse reactions" for retrieval; metoprolol answers from "6.1 Clinical Trials Experience" and "6 ADVERSE REACTIONS". Curated gate re-measured: see below | `tests/test_live_versioning.py`, `scripts/measure_curated_gate.py` |
| P3.10 | "what is sterilization in medical?" showed three regulation passages as if they answered | General questions (no labeling words) fold their passages under "The regulations don't define this directly" when the top score is within 0.0005 of the gate or no top heading names the key term. Display only. "benefits of golden pump" also folds now | pro_e2e 06 |
| P3.11 | Landing card already opened `ui/pro/index.html` | Header has Home and "Advanced view" (old page); script cache versions bumped (`?v=34`); README names the two demo pages | pro_e2e |
| P3.12 | Demo script described the old multi-screen page | `docs/DEMO_SCRIPT.md` rewritten: order 04_barcode_aspirin, 08_live_zetia, device/03_golden_blurry, then the Golden Pump flow, with what to say and avoid. `docs/KNOWN_LIMITS.md` adds: package artwork not phone photos, live-label gate is a probe, photo lookup tuned on its own test lines, AI slow on CPU | review |
| P3.13 | CLAUDE.md said "Generated-with lines" | Rule names Co-Authored-By, Claude-Session and "Generated with Claude Code"; `.claude/settings.json` sets `attribution.commit` and `attribution.pr` to empty and `includeCoAuthoredBy` false. Nested `labellens/`: see below | review |

## P2.9 curated gate measurement

`scripts/measure_curated_gate.py --base http://127.0.0.1:8040`, 3 products, 8 on-topic and 8 off-topic questions each, gate 0.02:

| product | on-topic scores (scored) | on-topic under 0.02 | off-topic scores | off-topic under 0.02 |
|---|---|---|---|---|
| Childrens Ibuprofen | 0.0083 to 0.0225 (6) | 5 | 0.0062 to 0.0188 (8) | 8 |
| Atorvastatin Calcium | 0.0145 to 0.0259 (6) | 3 | 0.0051 to 0.0153 (8) | 8 |
| Amoxicillin | 0.0088 to 0.0264 (6) | 4 | 0.0083 to 0.0179 (8) | 8 |

12 of 18 scored on-topic questions would be folded (two per product are stopped by the scope rule and have no score). Decision: no gate, display "Closest passages from the label". Same numbers as `reports/abstain_display.md`.

## P2.8 photo checks

- **Name lookup on recorded OCR lines** (`ui/tools/check_photo_lookup_live.cjs`, live DailyMed, photos of the scan evaluation that the scan did not identify): decoys 39 photos, 8 proposed the right medicine, 0 wrong, 31 nothing; positives 11 photos, 4 right, 0 wrong, 7 nothing. Earlier, looser versions had 2 to 3 wrong proposals (above); the rule was adjusted on these same lines, so the numbers are optimistic.
- **Regression for the UTF-8 decoding fix** (re-read with the current reader, scored with the unchanged frozen decision `scripts/ndc_scan/evaluate.score_row`, compared with `results/ndc_scan/final_rows.jsonl`; output in the scratchpad, no evaluation file touched). Stopped early for the time limit:
  - Decoys, 45 of 45 photos: **0 wrong** before and after (review 20 to 20, not identified 19 to 17, timeout 6 to 8).
  - Positives, only 20 of 57 photos re-read: correct 14 to 13, review 3 to 2, not identified 3 to 2, timeout 0 to 3. All three changed photos became timeouts: the PC was busy with pro_e2e and the server during the re-read (reader killed at its limit), so this is load, not decoding. The other 37 positives were not re-read: **"positives must not drop" is not fully verified.**
  - 37 decoy photos and 13 re-read positives had non-ASCII text in their lines after the fix.

## Test counts

- Fast suite: `python -m pytest -q -m "not slow"`: 1096 passed, 8 skipped, 5 deselected (before the last small commits; re-run at the end below).
- `ruff check src tests`: clean.
- `ui/tools/check_ask_panel.cjs`: all passed. `ui/tools/check_name_guess.cjs`: all passed.
- pro_e2e (live API, port 8040): run 1 26 steps, 2 FAIL (a test bug: passages inside a closed details have no `innerText`, so two hidden titles both read "" and looked like a duplicate section; print verification failed only because export was skipped after it). Fixed the test; run 2: 31 steps, 0 FAIL.
- demo_e2e with the AI stage: 20 of 20 PASS, no fallback data; stage 19 (public AI answer) ended `verification_failed` after 20.7 s and showed the passages (the designed fallback).

Final fast suite on the merged code: 1097 passed, 8 skipped, 5 deselected (257.9 s); ruff clean.

## Rehearsal

Server on port 8040, Terminal tab, screenshots in `C:/Users/parid/AppData/Local/Temp/labellens_final_polish/` (outside the repo). Each screenshot was opened and looked at.

| step | seconds | seen |
|---|---|---|
| Golden Pump: add sample label (read, correct, save), pro_e2e | 34.5 | prefilled GP-100, LOT1, 2030-06-30; required panel 5 of 5 with passages |
| Check (inspect) | 0.4 | one extraction_unreliable finding, cards with rule ids and passages |
| Ask the regulations, expiry example | 4.2 for four questions | 801.18 first, no 801.435, no repeated section; sterilization and golden pump questions folded |
| Ask with AI (warm) | 15.4 (answer 13.7) | verified answer, cites 801.18 only |
| Retrieval lab | 4.3 | five systems, labelled raw |
| Lot to LOT2, assess, generate | 1.8 + 2.3 | REGENERATE, DRAFT preview |
| Reviewer re-check and approve | 11.2 | approved, cards read-only |
| Export | 1.2 | hash matches, DRAFT kept, findings report 30 lines |
| Print verification | 2.6 | match |
| Public: 12_synthetic_lopressor photo | 29.6, Confirm 1.9 | "Is this LOPRESSOR (METOPROLOL TARTRATE) tablet?", then the live label |
| Public P3: metoprolol before a pick | instant | "Pick a medicine first", DailyMed searched |
| Public P3: metoprolol "how to store it" | 1.4 | "Closest passages from the label", "Store at 20° to 25°C ..." |
| Public P3: metoprolol "side effects" | 1.4 | 6.1 Clinical Trials Experience, 6 ADVERSE REACTIONS |
| Public P3: "what is the capital of France" | 0.4 | "This label doesn't seem to answer that.", folded |

Problems found in the screenshots and fixed: the evidence card said "used for the match" on an unidentified photo (now no match markers); an empty "Read from your photo" box (now a sentence); 809.10 in vitro diagnostics among the pump passages (now filtered); old "about 40 s" AI text; missing full stop before "Read:" on cards; export list indent.

**Not rehearsed (time limit):** the full set of demo photos (04_barcode_aspirin, 08_live_zetia, the other public photos) and the device photos through the rehearsal driver (`ui/tools/rehearse_public.cjs` is ready for it), and a quiet-machine timing of the photo reader. The blur refusal was seen through pro_e2e (camera fake device: "The photo is too blurry to read", 6.5 s), not with `device/03_golden_blurry.jpg` itself.

## Nested `labellens/` folder

An untracked full clone of this repository inside the repository: its own `.git`, remote `https://github.com/paridhik11/labellens`, HEAD 614b9f2 (Merge remote-tracking branch 'origin/main', after "step 27: public mode demo fixes"), its own `.venv312`. It is an old copy, not used by anything here. Not deleted (as asked); it is the only entry `git status` shows.

## Remaining limits

- Demo photos are DailyMed package artwork with simulated camera conditions or synthetic images, not phone photos.
- The live-label gate (0.02) is a probe on one label, not evaluated; curated products have no gate.
- The photo name lookup was adjusted on the same recorded OCR lines it was measured on; real use may find fewer names.
- AI mode is slow on CPU (warm about 14 to 15 s, cold about 45 s, more on a busy PC) and optional.
- On a busy PC the photo reader hits its time limit (about 55 s); the demo script says to close other programs.
- Product applicability is a hand table of three sections, not a general model of which sections apply.
