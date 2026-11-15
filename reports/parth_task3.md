# Parth Task 3: pinned device artwork and symbol crops

## 1. What I did
Collected 20 public device-label artworks from 17 DailyMed records across eight label families. Visually inspected and cropped 44 symbols in six classes, marking every guess LLM-labelled with uncertainty. Excluded medicine-component panels and example-only Centurion artwork. Preserved the old 60 medicine sources separately and kept image binaries local.

## 2. Files created or changed
- `scripts/real/fetch_dailymed.py`: downloads pinned versions, verifies fingerprints and device metadata, rebuilds crops.
- `tests/test_device_real_set.py`: offline tests for provenance, coordinates, source identity, retries and reproducibility.
- `data/real/SOURCES.md`: source URLs, rights, original-pixel boxes and rebuild catalog.
- This report and `docs/LEARNING_LOG.md`: checks and limitations.

## 3. How it works
A crop is a rectangle copied from the original image. SHA-256 is a file fingerprint: changed downloads fail verification. The catalog alone rebuilds originals and annotations; no hidden local manifest is needed. Counts: manufacturer 9, expiry 9, sterile-R 9, sterile-EO 8, single-use 6, instructions 3. Fourteen crops have a side below 25 original pixels and are flagged small. Annotations cover selected symbols, not every symbol or absence.

## 4. How I verified it
Background jobs completed; actual commands and output:
```text
/opt/anaconda3/envs/labellens-cv/bin/python /tmp/ll_clean_device_checkout_final/scripts/real/fetch_dailymed.py
{"evaluation": "NOT_RUN", "images": 20, "module": "device", "symbol_crops": 44, "tags": "LLM-labelled"}
```
The isolated copy contained only the script and catalog, initially no data. All rebuilt originals and crops matched local bytes. An earlier attempt timed out; bounded retries were added and tested.
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 77%]
........................................................................ [ 96%]
.............                                                            [100%]
373 passed, 3 deselected in 38.00s

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real
All checks passed!
```

## 5. What you should check yourself
Inspect crop boxes and the small/rotated symbols. Check device/medicine separation and per-source rights. Confirm only SOURCES.md is tracked under data/real.

## 6. What I am unsure about or assumed
All 20 images contain visually identifiable symbol candidates; human review and detector/blind-mode accuracy are NOT_RUN. Related layouts require grouped evaluation. Public availability does not establish an open artwork license. Three slow tests were excluded. No dependencies were added.
