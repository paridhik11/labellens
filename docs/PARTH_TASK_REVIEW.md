# Parth task review, 2026-11-15

This is a review of the GS1 and export work before the DailyMed dataset task.
The branch is `parth-gen`. These are local module checks, not a measured real-world
accuracy result or a statement that the entire application is integrated.

## Task 1: GS1

Reviewed the implementation, its requirement table in `src/gen/GS1_REVIEW.md` and
the tests. The module supports AIs 01, 17, 10 and optional 21, both input forms,
GS separators, check-digit/date/character validation, both barcode formats and
decode-back comparisons. Tests include 200 seeded inputs in each format.
The all-zero GTIN needs explicit test mode. Missing identifiers are not supplied
by the generator. Encoded changes require confirmation under the newer contract.

## Task 2: export

Reviewed the label model, template/ProductRecord adapter, writers, QR generation,
approval gate and tests. The PDF has measured physical dimensions and extractable
text. Barcode modules keep their configured physical width. SVG has the contract's
named layers and editable field IDs. The module supports simplified sterile
artwork in addition to manufacturer and expiry. Approval records require a
matching passed `check_id`, version, reference hash and authorized independent
reviewer. Both GS1 formats are decoded from independently rasterized 600 dpi PDFs.

Found and fixed one issue: `ProductRecord.extra` could replace core identity
fields when building exported text. Core values now take precedence. The new
regression test supplies conflicting auxiliary names and manufacturer values and
checks that the canonical product values survive.

## Actual verification

Before the fix:

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider tests/test_gs1.py tests/test_export.py
86 passed in 50.72s
```

After the fix and regression test:

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider tests/test_gs1.py tests/test_export.py
87 passed in 50.71s
```

Existing generator/CV regression suite (synthetic/unit inputs, not the new real set):

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider src/gen src/cv
233 passed in 114.78s (0:01:54)
```

## Limits retained in the handoff

- Actual Windows execution and physical-printer tests have not been run. Windows
  package downloads succeeded; that is not the same as a Windows runtime test.
- The exporter is a local API. The application's stored Review/CheckResult and
  generated-artwork manifest still need server-side mapping to the local snapshot
  and trusted authorization inputs. This module does not implement publication.
- Simplified symbols are synthetic artwork, not certified ISO artwork. The old
  CV detector and existing `src/gen/render.py` were not replaced by the exporter.
- Export source checks do not claim OCR, regulatory checking or real-label accuracy.
- Task 3 collects medicine artwork and source-backed fields. It does not run OCR,
  decode real barcodes, add symbol boxes or create human image transcriptions.
