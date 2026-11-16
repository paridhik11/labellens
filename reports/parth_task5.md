# Parth Task 5: symbols, SVG layers and checked approvals

## 1. What I did
Added sterile variants to the original generator as well as the exporter. Added named SVG layers and slot groups to the original renderer, preserving PDF geometry. Made print verification and export approval require matching reference, version, reviewer role and passed check_id evidence.

## 2. Files changed
- `src/gen/render.py`, `symbols.py`: sterile/EO/R artwork, named SVG groups and version/creator manifest fields.
- `src/export/approval.py`, `label_model.py`: shared approval records and gate.
- `src/cv/verify.py`: passed-check validation before extraction, retaining artifact integrity checks.
- `tests/test_approval.py`, `tests/test_gen_contracts.py`, `tests/test_export.py`, `src/cv/test_verify.py`: positive, failure, rendering and API-alias cases.
- Generator/export READMEs, this report and learning log: procedure and limits.

## 3. How it works
Approval needs an authorized reviewer other than the creator, a reviewer/admin role and a passed check for the same version and exact reference hash. Missing, stale, failed or conflicting evidence is refused before OCR. Canonical local names remain reviewer/reference_sha256 as clarified; API user_id/artifact_sha256 aliases are mapped without editing schemas. No review or passed check is issued automatically.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
358 passed, 3 deselected in 36.75s

/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider src/gen src/cv/test_verify.py
59 passed in 35.24s

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests
All checks passed!
```
The fast suite includes tests/test_mock_contracts.py. Jobs ran in the background to logs; finished results were checked once. Tests use synthetic approval fixtures, not real issued approvals.

## 5. What to check yourself
Check every legacy SVG slot/layer ID, sterile method text, missing/failed-check rejection and conflicting hash aliases. Confirm shared schemas/contracts are unchanged.

## 6. Assumptions and limits
The print verifier hashes generated manifest bytes; standalone export hashes its canonical Label snapshot. Do not interchange these references without explicit mapping and rechecking. Old manifests missing version/creator/check evidence need rechecking. Symbols are simplified synthetic artwork; the CV detector still has two original references. New real-device symbol evaluation and real-photo spot-checks remain outstanding.
