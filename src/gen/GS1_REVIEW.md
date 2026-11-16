# Task 1: GS1 module review

Reviewed on 2026-11-15. Scope: `src/gen/gs1.py` and `tests/test_gs1.py`.
The export integration belongs to Task 2.

## Requirements and review findings

| Requirement | Implementation and evidence |
|---|---|
| Parse AIs 01, 17, 10 and 21 | Parenthesized and raw strings; variable values stop at ASCII GS or end of input. Tests include a different AI order, duplicates, unsupported AIs and truncation. |
| Validate GTIN | Exactly 14 ASCII digits and GS1 Mod-10 check digit. An independent fixed check-digit fixture supplements seeded fixtures. This does not verify allocation or ownership. |
| Validate expiry | Real YYMMDD date for healthcare. Explicit `healthcare=False` permits day 00 as month-end. Century uses the GS1 49-years-past to 50-years-future reference-year window; tests pin the reference date. |
| Validate lot and serial | 1 to 20 characters, GS1 character set 82. Tests cover every allowed character, both maximum-length fields and forbidden characters. |
| Human-readable text | `build_hri` returns display text with parenthesized AIs; `EncodedBarcode.hri` supplies it to the caller. This display is not an unambiguous serialization when data contains literal AI-like parentheses. Use `build_element_string` for lossless interchange; escape literal parentheses when supplying parenthesized input. |
| Generate two barcode formats | `encode_gs1` returns a NumPy image, SVG, display text and validated fields. Both GS1 DataMatrix and GS1-128 are exercised. Human-readable text is supplied separately because native writer placement varies by symbology. |
| Decode every encoded symbol | The encoder requires exactly one GS1 decode of the requested format. It compares parsed fields and exact decoded bytes against the intended canonical element string. Failure tests inject missing, wrong-format, non-GS1 and mismatched decodes. |
| At least 200 random round trips | Seed 1701, 200 payloads in each format: 400 generated symbols, with and without serial values. Test-only generated identifiers are not allocated production identifiers. |
| KEEP / REGENERATE / NEEDS_INPUT | Matching data and symbology give KEEP. Changed encoded fields require explicit per-field confirmation; absent values and invalid data give NEEDS_INPUT. Changed symbology regenerates. No caller values are filled or guessed. |
| Missing identifier | The encoder raises the existing `IdentifierRequired`; decision logic returns NEEDS_INPUT. All-zero GTIN encoding requires `test_data=True`. The caller must put TEST DATA and DRAFT on label artwork. |

The newer `docs/contracts/TEMPLATE_SPEC.md` requires confirmation for every
changed encoded field. That supersedes the original brief's simpler lot and
expiry rule. Confirmation keys are `confirmed_gtin_change`,
`confirmed_expiry_change`, `confirmed_lot_change`, `confirmed_serial_change`.
The `confirmed` mapping may be positional or named, matching the requested API.

## Encoder choice and Windows evidence

Use the already pinned `zxing-cpp==3.1.1`. Its Python wrapper provides image and
SVG writing plus GS1 encoding, and is already the project's decoder. No new
dependency, Ghostscript installation or external barcode service is needed.
Compared with adding treepoem, this reuses the current package and avoids an
external Ghostscript executable. A bwip-js service or JavaScript runtime would
add another runtime or network dependency to this Python module.

The official PyPI release provides Python 3.12 Windows x86-64 and ARM64 wheels.
The following command was run successfully on this Mac, downloading the Windows
x86-64 wheel without compiling or changing the installed environment:

```sh
/opt/anaconda3/envs/labellens-cv/bin/python -m pip download --no-cache-dir --only-binary=:all: --no-deps --platform win_amd64 --python-version 312 --implementation cp --abi abi3 --dest /tmp/labellens-gs1-win-wheels zxing-cpp==3.1.1
```

Output included:

```text
Saved /private/tmp/labellens-gs1-win-wheels/zxing_cpp-3.1.1-cp312-abi3-win_amd64.whl
Successfully downloaded zxing-cpp
```

An earlier restricted-network attempt failed to resolve PyPI; retrying with
network access succeeded. A Windows runtime/install test was not performed.
To close that platform check, run in a normal user's Windows Python 3.12 venv:

```powershell
python -m pip install --only-binary=:all: zxing-cpp==3.1.1 numpy pydantic pytest
python -m pytest -q tests/test_gs1.py
```

This is packaging evidence, not a claim of an executed Windows test.

## Sources

- GS1 General Specifications 26.0, sections 3.2 (AI table), 3.4.7 (expiry),
  7.8 (separators), 7.9 (check digits), 7.11 (character set 82),
  7.12 (century): https://ref.gs1.org/standards/genspecs/26.0.0/
- Python writing API: https://github.com/zxing-cpp/zxing-cpp/blob/v3.1.1/wrappers/python/README.md
- Windows package files: https://pypi.org/project/zxing-cpp/3.1.1/#files
- Treepoem installation requirements: https://github.com/adamchainz/treepoem#installation

## Executed checks

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider src/gen tests/test_gs1.py
113 passed in 79.10s (0:01:19)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src/gen tests/test_gs1.py
All checks passed!
```

The implementation and local review checks are complete. The actual Windows
runtime check remains unexecuted; export integration remains Task 2.
