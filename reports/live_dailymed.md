# Live DailyMed lookup (CR-28)

Branch `live-dailymed`. Protocol `reports/live_dailymed_protocol.md` was committed before scoring (8e60e64), with one
amendment before any eval name was run (38724e3, see below). Scored once on 2026-11-22. Other jobs (a docs session and a
scan re-run) were running on this machine during the run, so every timing is pessimistic and noisy.

## Result (30 fresh products, 10 decoys; none in the 30 curated or 100 med100 sets)
| Measure | Result |
|---|---|
| Right label in the candidate list | 29/30 (97%, Wilson 95% 83 to 99%) |
| Fetched, parsed, indexed | 29/30 (97%, 83 to 99%) |
| Passages with a citation shown | 27/30 (90%, 74 to 97%) |
| Wrong-product answers shown as correct (40 queries) | 0 |
| Shown citations failing verification | 0 (29 products checked) |
| Decoys rejected | 10/10 (100%, 72 to 100%) |
| Median fetch-to-answer, cold | 30.7 s (p90 200 s, max 356 s) |

Gate G1 to G3 passed, G4 reported. Per item rows: `results/live_dailymed.md` and `.jsonl`.

## What the numbers do not show
- OTC 11/12 found, Rx 16/18 shown. "Prevacid 24HR" returned no candidate (DailyMed's name search is a substring match on
  its own titles, and there is no fuzzy matching). Xanax and amiodarone were fetched but the reranker showed no sentence
  (rerank gate), so nothing was shown: a safe miss, not a wrong answer.
- The picker is a script that takes the first listed label with the expected ingredient in its title. A person may pick
  differently; the system never picks. "Wrong product" was defined by ingredient presence in the fetched SPL, not by a
  person judging the label for the pack in hand (brand, strength, labeler are not compared).
- Answer relevance was not graded; only that the passages are verbatim parts of the picked label. Extractive mode returns
  an abstention-shaped body with quotes (`provider_off`), so "answered" means passages shown (protocol amendment).
- Fetch time is dominated by embedding the label with bge-large on CPU: big Rx labels (methotrexate 356 s, risperidone
  269 s, ropinirole 200 s) are slow on a busy machine; small OTC labels take 5 to 16 s. The UI waits up to 10 minutes.
- Decoys were invented names, three device brands and three veterinary brands. DailyMed's search is restricted to human
  Rx and OTC labels, so these return empty lists by construction; this tests the filter, not fuzzy rejection.
- Typed correct spellings only. DailyMed contents change daily; this is a snapshot.

## Choices
- Search: `spls.json?drug_name=...&doctype=` for the two human SPL types (8 s timeout), max 10 candidates, DailyMed order.
  Never ranked, never auto-picked, even when one candidate.
- Fetch: `getFile.cfm` zip (40 s, 40 MB cap), one SPL XML, checks human label, set id and version equal to the pick.
  Parsed with the curated corpus rules; unlike the curated build only labelling or warnings text is required.
- Cache: `data/api/live_dailymed/<product_id>.json` (git-ignored), chunk hashes re-checked on load. Live products do not
  enter the curated corpus, the matcher or the 30-product indexes.
- Answers: extractive path over that label's chunks (E5b recipe over the label only). Every citation checked verbatim
  against the label chunks, else the answer becomes an abstention. Every live answer and page carries "Fetched live from
  DailyMed, not in the curated set", set id, version, effective date and fetch date.
- Offline, timeout or API error: 200 `unavailable` with a plain message naming the 30 curated medicines; fetch failures
  are failed jobs with `details.reason`. Never a mock in api mode. Tests use recorded fixtures only.
- Contract: CR-28 (3 operations, Job kind `live_fetch`, `live_selected`, optional `live`, `match_confidence` optional).
  UI states: live_candidates, live_none, live_offline, live_fetching, live_fetch_failed, live_success.

## Pre-merge suite
Run on the branch before merge, server on port 8011 (not 8000: a docs session and a scan re-run were using the machine).
- Fast tests: full run 979 passed, 9 skipped, 1 failed (`test_real_operations_never_carry_x_mock` did not list the
  three new operations); fixed, that file and the contract and live files re-run: 131 passed, 1 skipped. Not a second
  full run. ruff clean.
- UI states 67 (61 before plus 6 live states), mock and api mode: 0 failed. live_flows 13 flows 0 FAIL (golden e2e 9/9),
  camera_check ALL PASSED, confirm_check ALL PASSED, new `ui/tools/live_check.cjs` all PASS (real network).
- demo_e2e.py: 20 of 20 PASS, no mock, no fallback.
- A first run of the live flows and demo_e2e failed (D5 timeout, stages 15 to 19) because that server was started with
  `--skip-indexes`, so the 618-chunk medicine index was being encoded from scratch; restarted with the index store, all passed.

