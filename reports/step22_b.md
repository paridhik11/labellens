# Step 22b report: src/change/

Branch step22-change. Origin/main merged first (clean). Spec updated with the six review decisions.

**Built** (`src/change/`, no database, no CV imports):
- `fields.py`: 12 fields, aliases, value rules (14-digit UDI-DI with check digit, lot and serial 1 to 20 GS1 characters, expiry to ISO, numeric dates refused as ambiguous).
- `parser.py`: structured edit validation (unknown field and invalid value are `unassessed`; duplicate field and no-op raise `ChangeError`, record value wins on `old_value` mismatch) and the rules text parser (all clauses must parse, else nothing). Optional `EditProvider` interface, off by default, proposals must appear verbatim in the text.
- `barcode.py`: payload builder (all four AIs required, like the renderer) and the KEEP, REGENERATE, NEEDS_INPUT decision incl. `confirm_<field>`, the 830.50 model rule, placeholder refusal.
- `impact.py`: text, symbol, barcode, no-slot and no-template items. Every label with a barcode slot gets its barcode decision.
- `assess.py`: fixed field-to-section citations via the checker's `find_citation`; only rule-decided items (text refill, KEEP, confirmed REGENERATE) are not needs_human; a missing citation forces needs_human.

**Verified**
`python -m pytest -q tests/test_change.py -rs` -> `66 passed, 1 skipped` (skipped: renderer parity needs `zxingcpp`, not installed here, so that comparison did NOT run). `ruff check src/change tests/test_change.py` -> All checks passed.

**Not done / caveats**
- Not wired to the API yet (22c).
- Parser handles only the sentence shapes in the spec. Value runs to the end of the clause ("to LOT002 for all units" would be taken whole).
- Citations tested with a stub retriever, not the real corpus yet.
- Model change always waits for a new `udi_di` edit (no implicit keep).
