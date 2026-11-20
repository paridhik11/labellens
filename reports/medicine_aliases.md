# Medicine aliases result

Independent branch from origin/main. Sixty fresh names and threshold 0.65 were
committed at e0d8cef; candidate b6ffcb4 froze before one scoring run. No final
query tuning. Fixed E5b/BGE-large ran on CPU after an unscored MPS preload crash.

DailyMed expansion succeeded: 30 pinned human-medicine products, 618 chunks,
zero fetch/parse failures. Product/generic names and short SPL titles yielded
90 sourced alias entries before per-product deduplication. No handwritten brand
map was added. Missing brand equivalents are not invented.

Manufacturer is returned with per-value source URL, quote, XPath and XML hash.
The value is specifically the SPL labeler; evidence says physical manufacturer
is not established. Labelers can be repackagers/distributors. Source effective
dates are preserved in metadata. No device data or retrieval implementation changed.

| Fresh names | Correct matched | Wrong matched | Review | No match |
|---|---:|---:|---:|---:|
| Brand/description (15) | 9 | 0 | 6 | 0 |
| Generic (15) | 13 | 0 | 1 | 1 |
| Misspelled (15) | 9 | 0 | 3 | 3 |
| Decoys (15) | 0 | 0 | 0 | 15 |

Gate PASS: zero decoy matches or review candidates (0/15; Wilson 95% 0-20.4%).
Positives: 31/45 confidently correct, 10 review, 4 rejected. Authored names are
not photo-OCR accuracy; fifteen decoys cannot establish a zero population error
rate. The existing 0.65 threshold and review band were unchanged.

Rebuild: `python -m src.gen.medicine_metadata --expand` (pinned originals are
re-fetched if absent). Frozen names: src/gen/medicine_match_fresh.tsv. Full raw
scores: results/medicine_aliases_fresh60.jsonl. Human/photo evaluation remains separate.

Validation before main integration: 949 passed, 1 skipped, 5 deselected using
the full fast suite with offline model access; ruff src/tests clean. Threshold
and shared schemas were unchanged. Raw-score SHA-256 begins 7405856c26db0d5a.
After integrating the passing print branch: 952 passed, 1 skipped, 5 deselected;
ruff remained clean.
