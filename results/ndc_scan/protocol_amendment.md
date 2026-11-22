# NDC scan protocol amendment (committed before the re-run)

## The first scoring run is invalid
Run 1 (results in `run1_invalid/`, scored at commit `e85c5cb`, frozen config committed at `8c9b540`) is invalid as a test
of the method. The harness read the gate photos in parallel on a CPU it shared with two other jobs, so most photos
hit the reader's time budget before any text was read. The product reads one photo at a time.

Evidence (`run1_invalid/lines_*.jsonl`, `run1_invalid/read*.log`):
- Three harness reader processes ran together (2 OCR workers each, so up to 6 readers at once) on 12 physical cores
  (14 logical). At the same time another session was running its own photo-scan OCR worker and, at the end, a pytest run.
  Each reader runs RapidOCR (multi-threaded) and Tesseract.
- OCR complete: 10/45 unused decoys, 9/80 positive readings (duplicates included), 2/54 new set. Empty readings
  (0 lines): 33/45, 63/80, 50/54. Median wall time per photo 54 to 62 s, max 150 s.
- For comparison, one reader at a time: E's original dev reading had 85/108 complete, median 32.1 s, max 50.2 s; a
  single-reader re-read of the 57 positives done after run 1 (other session still busy) had 46/57 complete, median 32.5 s.
- Per-photo CPU time was not recorded in run 1. Only wall time and completeness are available.

## Re-run (once)
- Same frozen method: `src/` is byte-identical to commit `e85c5cb` (`git diff e85c5cb -- src` is empty), config
  `src/ndc/ndc_config.json` from `8c9b540` (tau 22.0, top 3). No change to code, thresholds, time budget (55 s, 50 s
  kill and 150 s harness timeout as in run 1), sets, gate or categories. The harness only added commands that do not
  change scoring (`rescore_quiet`, a file suffix) and the calibration script.
- Machine: every other job was stopped first (other session's OCR workers and pytest, no servers on 8000, 8011, 8021,
  8031). CPU idle at 0 to 17% before the run.
- Harness concurrency: 1 (one photo at a time). Calibration on 3 dev photos (`calibration_c3.json`, `calibration_c2.json`):
  alone 12.1 to 14.9 s; at concurrency 3 18.0 to 22.3 s (+37 to 52%); at concurrency 2 14.4 to 15.4 s (+3 to 19%). Line
  counts and completeness were the same, but per-photo time matched only at concurrency 1, so 1 is used.
- The new readings go to `lines_<set>.jsonl`, the scores to `final_rows.jsonl` and `final_summary.json`, scored once.
- Both runs are reported. Run 1 is marked invalid with this cause. The single-reader re-read of the positives
  (`supplementary/`) was scored by the same frozen code before this amendment. It is not a gate run, it covers
  positives only, and it is reported as supplementary only.
- Gate unchanged (protocol.md). Check 2 compares with E replayed on the same new readings and with E's recorded 13/45 timeouts.
