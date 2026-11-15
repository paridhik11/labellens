# Step 22a report: change assessment spec

Branch: step22-change (worktree `../labellens-change`, from origin/main a67029b). Plan only, no code.

**What I did.** Read CLAUDE.md, the contracts, CHECKER_SPEC, `src/checker`, `src/api` and the GS1 code, then wrote `docs/CHANGE_SPEC.md`: edit format, rules parser with an optional off-by-default provider interface, impact table, barcode decision table, needs_human and citation rules, failure cases, API mapping and test plan.

**Findings while reading**
- `src/gen/gs1.py` does not exist. The GS1 parser is `src/checker/gs1.py`; the payload builder is `record_content` in `src/gen/render.py` (imports CV code), so 22b mirrors it.
- The contract blocks the brief: `parser` allows only `not_implemented` or `mock`, and `AffectedLabel` has no needs_human flag or barcode decision. Proposed CR-18 (additive, optional).
- Corpus has 21 CFR 830.50(a) (new model needs new DI), used for a `model` edit rule. No section for sterilization or storage, so those get no citation and stay needs_human.
- A text-only request that cannot be parsed returns 422 `parser_not_implemented`, because a ChangeRequest needs `field` and `new_value`.
- Assessment-time edits are always unconfirmed and `confirmChange` stays a mock, so REGENERATE is tested in code but not reachable through the API in 22c.

**Verified.** `grep -c "—"` on the spec: 0 em dashes. Nothing run beyond that (no code).

**Decisions for you:** approve CR-18; `confirm_<field>` as `required_identifier` for unconfirmed encoded changes; serial required (renderer) vs optional (TEMPLATE_SPEC); `udi_di` old==new as acknowledgement; store assessments in a new append-only table.
