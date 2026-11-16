# Parth Task 2: PDF, SVG and QR export

## 1. What I did
Verified the existing exporters against TEMPLATE_SPEC and the updated checklist. Fixed export of a product field appearing in multiple slots while keeping SVG IDs unique. Added explicit tests for PDF size from the template, every named slot group and QR generation without a network connection.

## 2. Files created or changed
- `src/export/label_model.py`: permit repeated fields in separately named slots.
- `src/export/svg.py`: preserve every slot group; emit each field alias only once.
- `tests/test_export.py`: template dimensions/groups, repeated fields and offline QR tests.
- `src/export/README.md`: explain repeated-field behavior.
- `reports/parth_task2.md`, `docs/LEARNING_LOG.md`: results and review record.

## 3. How it works
A 100 x 60 mm template produces the same PDF page size, with a maximum measured metadata error of 0.0000142 mm, below 0.1 mm. All 9 template slots have matching `slot-{id}` groups beneath `layer-slots`. Separate slots may print the same field without duplicate SVG IDs. QR generation encodes the supplied published-page URL literally, without visiting it. Existing PDF/QR implementation changes were unnecessary.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
........................................................................ [ 21%]
........................................................................ [ 42%]
........................................................................ [ 64%]
........................................................................ [ 85%]
................................................                         [100%]
336 passed, 3 deselected in 32.04s

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests
All checks passed!
```

Jobs ran in the background to `/tmp/labellens_task2_fast.log` and `/tmp/labellens_task2_lint.log`; completed results were checked once. Also generated and visually reviewed a draft sample. Tests compare two actual template sizes and verify every slot ID, metadata and repeated text occurrence.

## 5. What to check yourself
- The real-template dimension and slot-group assertions.
- Both repeated-field slot groups and the test that rejects QR network connections.

## 6. Assumptions and limits
Installed already-declared fast-suite packages in the CV Conda environment; requirements were not changed. Slow tests were excluded as requested. Windows runtime, physical printing and later contract approval-field integration are not established by this export check. Branch: `parth-gen`.
