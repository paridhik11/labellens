# Change assessment spec (Step 22a)

Status: approved with decisions (see section 11). 22b builds `src/change/`, 22c wires the API.

A change assessment takes one proposed change to a product record (for example "new lot LOT002" or "sterilization EO to gamma") and answers three questions: which labels and which parts of them are affected, what happens to each barcode, and what a human still has to decide. **Rules decide, retrieval cites, a human confirms.** No language model decides anything. An assessment never says a label is compliant, and it never changes a label: it produces a checklist that a person confirms before any artwork is generated (`docs/GENERATION.md`).

Read first: `docs/contracts/openapi.yaml` (`assessChange`, `listAffectedLabels`, `ChangeAssessment`, `AffectedLabel`, `BarcodeDecision`), `DATA_MODEL.md` (ChangeRequest, AffectedLabel), `TEMPLATE_SPEC.md` section 4 (GS1 rule), `docs/CHECKER_SPEC.md` (citation procedure).

## 1. Scope and layout

New package `src/change/`, pure functions with no database and no CV libraries (so CI can run it):

| Module | Job |
|---|---|
| `models.py` | `Edit`, `ParseResult`, `LabelContext`, `AffectedItem`, `BarcodeOutcome`, `Assessment` (plain dataclasses or pydantic, not `schemas.py`). |
| `fields.py` | The one table of supported fields (section 2), aliases, value normalisation and validation. |
| `parser.py` | Raw text to `Edit` list (section 3), plus the optional provider interface. |
| `impact.py` | Edits plus label contexts to affected items (section 4). |
| `barcode.py` | Payload builder and the KEEP, REGENERATE, NEEDS_INPUT decision (section 5). |
| `assess.py` | Orchestration, citations and needs_human (section 6). |

Allowed to reuse, not edit: `src/checker/gs1.py` (`parse_gs1`, `check_digit_ok`), `src/checker/citations.py` (`find_citation`, `Citation`), `src/checker/retrieval.py` (`default_retriever`, `module_chunks`). `src/gen/gs1.py` named in the brief does not exist. The GS1 builder is `record_content` in `src/gen/render.py`, which imports ReportLab and CV code, so 22b mirrors its payload rule in `src/change/barcode.py` and a test compares the two when the CV libraries are installed (same pattern as `tests/test_checker_gs1.py`).

Not touched: `src/common/schemas.py`, `src/ir` internals, `src/cv`, `src/gen`, `data/eval`.

## 2. Structured edit format

An edit is `{field, old_value, new_value}`, the contract's `FieldEdit`. `field` is a canonical name from this table. Anything else is an unknown field (section 7).

| Canonical `field` | Lives in | Aliases accepted | Encoded in barcode | Value rule |
|---|---|---|---|---|
| `name` | `ProductRecord.name` | `product_name`, `device name` | no | non-empty text |
| `model` | `ProductRecord.model` | `model number` | no (see 830.50 rule) | non-empty text |
| `manufacturer` | `ProductRecord.manufacturer` | `mfr` | no | non-empty text |
| `manufacturer_address` | `ProductRecord.manufacturer_address` | `address`, `mfr address` | no | non-empty text |
| `udi_di` | `ProductRecord.udi_di` | `udi`, `udi-di`, `gtin`, `device identifier` | **AI 01** | exactly 14 ASCII digits with a valid GS1 mod 10 check digit. Never padded or repaired. |
| `sterilization` | `ProductRecord.sterilization` | `sterilisation`, `sterilization method` | no | non-empty text |
| `storage` | `ProductRecord.storage` | `storage conditions` | no | non-empty text |
| `lot` | `extra["lot"]` | `batch`, `lot number` | **AI 10** | 1 to 20 characters from the GS1 character set (`gs1.VARIABLE_CHARACTERS`) |
| `expiry` | `extra["expiry"]` | `expiry date`, `expiration date`, `exp` | **AI 17** | real calendar date, stored as ISO `YYYY-MM-DD` (year 2000 to 2099, the renderer's range) |
| `serial` | `extra["serial"]` | `serial number`, `sn` | **AI 21** | 1 to 20 characters, GS1 character set |
| `ref` | `extra["ref"]` | `reference`, `ref number` | no | non-empty text |
| `rx_only` | `extra["rx_only"]` | `prescription only`, `rx` | no | `true` or `false` (yes, no, on, off accepted and normalised) |

Normalisation (same for structured and parsed edits): trim, collapse inner whitespace, keep case and wording as typed (no controlled vocabulary for sterilization: `EO` stays `EO`). An expiry given as `30 April 2028` or `2028-04-30` becomes `2028-04-30`. A numeric date such as `03/04/2028` is **ambiguous** (day first or month first) and is refused, not guessed.

`old_value` handling: if omitted it is filled from the pinned current product record (what `routes.py` does today for record fields, extended to the `extra` keys). If given and different from the record, the **record wins** and the response carries the warning `old_value_mismatch` (the typed value is shown, so a person can see which one is stale). `old_value` never changes what the barcode rule compares: that always uses the record.

Edit-set rules: the same canonical field twice is refused (`duplicate_field`). An edit whose `new_value` equals the current record value (after normalisation) is a no-op and is **rejected** with the message "`<field>` already has this value; nothing to change" (API: `422 no_change`). There is no implicit keep and no acknowledgement edit: to keep an identifier, send no `udi_di` edit.

## 3. Parser

### 3.1 Rules path (default)

Input `raw_text`, output `ParseResult{edits, status, issues}` with `status` one of `parsed`, `ambiguous`, `unknown`, `empty`. Deterministic, English only, regular expressions plus the alias table.

1. Split into clauses on newlines, `;`, and `" and "` only when the text after `and` starts with a field name or alias. "Update the address and lot" is one clause with two fields, which is ambiguous (3.3), not two edits.
2. In each clause find the field mention (longest alias first). Zero mentions: `unknown`. Two different fields: `ambiguous`.
3. Find the value with the first matching pattern, in this order:
   - `from <old> to <new>`, `<old> -> <new>`, `<old> => <new>`
   - `to <new>` after a verb (`change`, `update`, `set`, `replace`)
   - `<field> is now <new>`, `new <field> is <new>`, `<field>: <new>`
   - quoted text wins over unquoted text.
   Value patterns used to check the candidate: GTIN (14 digits), ISO or textual date for `expiry`, `[A-Za-z0-9._/-]{1,20}` for lot, serial and ref, free text for the others. A candidate that fails its field's value rule is `invalid_value`, not silently trimmed.
4. Exactly one field and one new value per clause, or the clause is not parsed. If any clause is not parsed, the **whole request** is not parsed: partial parses of one sentence are how a wrong lot number gets into a label.
5. Parsed edits are returned with `parse_state = proposed`. A person confirms them (`confirmChange`).

### 3.2 Optional LLM path (off by default)

```python
class EditProvider(Protocol):
    """Proposes edits from text. Returns raw proposals only; the parser validates them."""
    def propose_edits(self, raw_text: str, fields: tuple[str, ...]) -> list[dict[str, str]]: ...
```

- Off unless `ChangeSettings.llm_provider` is set (default `None`, environment variable `LABELLENS_CHANGE_PROVIDER` not set). 22b ships the interface and a fake provider for tests. **No real provider, no network call, no API key is added in Step 22.**
- It runs only after the rules path returned `unknown` or `ambiguous`, never instead of it, and never for structured `edits`.
- Every proposal is passed through the same field table, aliases and value rules as section 2. Additionally each `new_value` (and `old_value` when given) must appear **verbatim** in `raw_text` (case-insensitive, whitespace collapsed), otherwise the proposal is dropped. This is the guard against an invented lot number or identifier.
- Provider exception, timeout or empty answer: fall back to the rules result (not parsed), never raise to the client.
- Result is reported as `parser: llm`, `parse_state: proposed`. The provider has no access to the impact or barcode code, and its output never marks anything confirmed.
- Privacy note for later: enabling a provider sends the raw text outside the system, so it needs an explicit setting and a line in the README.

### 3.3 Ambiguous text, concretely

Refused with the issue listed (no guess): two candidate fields in one clause ("change the model and lot to X"), two candidate new values, a numeric date, "change the sterilization" with no value, "new lot" with no lot, a negation ("do not change the lot"), a request that names a field but gives a value that fails its rule.

## 4. Impact rule

Inputs: the validated edits, the product's current record, and one `LabelContext` per **label family of the product** (the latest `LabelVersion` of each `label_id`, its template version if it has one, and its latest stored extraction if any). Older versions are history and are not assessed.

For each edit and each label the rule produces zero or more `AffectedItem`s (the contract's `AffectedLabel` without ids):

| Field | Text slot match | Symbol slot match | Barcode | Other |
|---|---|---|---|---|
| `name` | slot with `field` in (`name`, `product_name`) | none | no | |
| `model`, `ref` | slot with that `field` | none | `model`: 830.50 rule (section 5.3) | |
| `manufacturer`, `manufacturer_address` | slot with that `field` | slot with `symbol_name = manufacturer`, item `symbol` | no | |
| `sterilization` | slot with `field = sterilization` | **no sterilization symbol exists** in the supported `symbol_name` set, so no slot can match. If any label has a text slot for the field the item says the symbol cannot be assessed from the template. | no | |
| `storage` | slot with `field = storage` | none | no | |
| `expiry` | slot with `field = expiry` | slot with `symbol_name = expiry`, item `symbol` | AI 17 | |
| `lot`, `serial` | slot with that `field` | none | AI 10, AI 21 | |
| `udi_di` | slot with `field = udi_di` | none | AI 01 | |
| `rx_only` | slot with `field = rx_only` (rare) | none | no | Usually printed in fixed artwork. See "no matching field". |

Matching is by exact slot `field` after alias resolution. A slot's `type` must be right (a `text` slot for text, `symbol` for symbols, `barcode` for the barcode).

Item construction, per matching slot:

- **Text slot**: `item_kind = text`, `slot_id = slot.id`, `suggestion = edit_required` (the slot is bound to this field, so it must be refilled; this is a fact about the template, not a compliance claim).
- **Symbol slot**: `item_kind = symbol`, `suggestion = review_suggested`. The symbol image itself does not depend on the value, so the rule cannot say it must change. A person decides.
- **Barcode slot**: one `barcode` item per label when any edit touches an encoded field (section 5), with the `BarcodeDecision` attached. `suggestion = no_change` for KEEP, `edit_required` for REGENERATE, `review_suggested` for NEEDS_INPUT.
- **No matching slot on a label** (the field is not a slot of its template, the label has no template because it was uploaded, or the template row cannot be found): one `linked_label` item, no `slot_id`, `suggestion = review_suggested`, `needs_human = true`, reason "no template field for `<field>` on this label; if the text is part of the fixed background LabelLens cannot update it". LabelLens never edits fixed background artwork.
- **Product has no label at all**: no items, and the assessment says so in `needs_human_review` (an empty list must never read as "nothing is affected").

Every item carries the reason in plain words and the rule id (`I-TEXT`, `I-SYMBOL`, `I-BARCODE`, `I-NOSLOT`, `I-NOLABEL`).

## 5. Barcode rule

Implements `TEMPLATE_SPEC.md` section 4 for assessment time.

### 5.1 Payload

`build_payload(record) -> str` returns the human-readable element string `(01)<udi_di>(17)<YYMMDD>(10)<lot>(21)<serial>` from `udi_di`, `extra.expiry`, `extra.lot`, `extra.serial`, in the order and formats of `TEMPLATE_SPEC.md`. It validates with `src/checker/gs1.py`. All four values are required, because `record_content` in the merged renderer raises when expiry, lot or serial is empty, so a REGENERATE that the renderer would then refuse is never promised. (`TEMPLATE_SPEC.md` says serial is optional "where used"; the renderer is stricter. This spec follows the renderer and lists the gap in section 9.) A missing or invalid value raises an internal `PayloadUnbuildable(missing=[...])` listing the first problem field. The function never fills a gap.

`old_payload` is built from the product record version the label was made against (`LabelVersion.product_version`). `new_payload` is built from that record with the edits applied. If a stored extraction has a decoded barcode whose raw payload differs from `old_payload`, the item gets the warning `printed_barcode_differs_from_record` and `needs_human = true`: the printed barcode is the truth about what is on the label, and the record is only a proxy for it.

### 5.2 Decision (first match wins)

| # | Condition | Decision | Notes |
|---|---|---|---|
| 1 | The label has no barcode slot (no template, or none in it) | no barcode decision, a `linked_label` or text item with `needs_human` | Cannot regenerate what the template does not describe. |
| 2 | No edit touches `udi_di`, `expiry`, `lot` or `serial`, and no `model` edit applies (5.3) | `KEEP` | `old_payload` is set when buildable, otherwise empty. `reason` says the encoded fields are untouched. |
| 3 | `new_payload` cannot be built | `NEEDS_INPUT` | `required_identifier` is the first missing or invalid field in this order: `udi_di`, `expiry`, `lot`, `serial`. `new_payload` empty. Server side this is the case where `IdentifierRequired` would be raised at generation. |
| 4 | `new_payload == old_payload` and the symbology is unchanged | `KEEP` | Safety net: with no-op edits rejected this should not occur, but the comparison stays so KEEP is never claimed for a changed payload. |
| 5 | Payloads differ and **every** changed encoded field is confirmed | `REGENERATE` | `new_payload` set, symbology from the slot. |
| 6 | Payloads differ and at least one changed encoded field is not confirmed | `NEEDS_INPUT` | `required_identifier = confirm_<field>` (for example `confirm_lot`). The new payload is shown so the person sees what they are confirming. |

"Confirmed" means the change has `parse_state = confirmed` (the person pressed Confirm). At assessment time every change is `proposed`, so through `POST /changes` an encoded change lands on row 6, and REGENERATE becomes reachable only when `confirmChange` is real. In 22c `confirmChange` stays a mock, so the API will not return REGENERATE yet. The pure function takes `confirmed: bool` so 22b tests row 5 and the later confirm step only has to call it again.

The placeholder identifier `00000000000000` is never accepted as a new value at assessment time. It can sit in an unchanged payload (row 4 or 2 gives KEEP, with a note in `reason` that the label carries the test placeholder).

### 5.3 The 830.50 rule for `model`

`21 CFR 830.50(a)` (chunk `fda_21cfr830_s830.50`, checked in the corpus) says a change that results in a new version or model needs a new device identifier. When an edit changes `model` and no `udi_di` edit is present:

- decision `NEEDS_INPUT`, `required_identifier = udi_di`, reason "the model changed; a new model normally needs a new UDI-DI (21 CFR 830.50(a)). Send the allocated identifier as a `udi_di` edit." LabelLens does not decide whether a rename counts as a new model, and it has no implicit way to say the old identifier still applies (a no-op edit is rejected). A model change therefore always waits for a new identifier. If the model is only being corrected and the identifier stays, that is a person's decision outside this tool for now (section 10).
- A `udi_di` edit with a new value clears the condition and the normal rows 3 to 6 apply.

### 5.4 Worked examples (all synthetic, same as `TEMPLATE_SPEC.md`)

Record: `udi_di 00000000000000`, expiry `2028-12-31`, lot `LOT001`, serial `SN001`.

| Edit | Rows | Decision | Why |
|---|---|---|---|
| address changes | 2 | KEEP | encoded fields untouched |
| sterilization EO to gamma | 2 | KEEP | text slot refilled, barcode untouched |
| lot `LOT001` to `LOT002`, proposed | 3, 6 | NEEDS_INPUT, `confirm_lot` | payload changes, not yet confirmed |
| same, confirmed | 5 | REGENERATE | |
| expiry `2028-12-31` to `2029-12-31`, proposed | 6 | NEEDS_INPUT, `confirm_expiry` | matches the TEMPLATE_SPEC example |
| model changed, no `udi_di` edit | 5.3 | NEEDS_INPUT, `udi_di` | |
| `udi_di` edited to `1234567890123` (13 digits) | 3 | NEEDS_INPUT, `udi_di` | not 14 digits, never padded |
| record has no lot, edit changes expiry | 3 | NEEDS_INPUT, `lot` | the new payload cannot be built |
| `udi_di` old equal to new | none | rejected `no_change` | no implicit keep |

## 6. needs_human and citations per affected item

Each item carries `needs_human` and, when a requirement applies, citations (the response's `citations` array is de-duplicated, each item lists its chunk ids in `evidence_chunk_ids`).

**needs_human is false only when a rule decided the item and its citation requirement is met.** The rule-decided items are exactly: a text slot bound to the edited field (`I-TEXT`, edit_required), a barcode KEEP, and a barcode REGENERATE with confirmed edits. Everything else is needs_human: symbol items, `linked_label` items, NEEDS_INPUT, items with a printed-barcode warning, items on an edit with `old_value_mismatch`, and any item where a citation is expected but none was retrieved.

Requirement per field (fixed queries and accepted sections, written now and not tuned later; sections verified to exist in `data/processed/regs.jsonl` on 2026-11-16 by listing the device corpus):

| Field | Query (fixed string) | Accepted section | Strength |
|---|---|---|---|
| `manufacturer`, `manufacturer_address` | the checker's `_Q_MFR` | 801.1 | direct |
| `udi_di` | `_Q_UDI` | 801.20 | direct |
| `model` | "changes that require use of a new device identifier new version or model" | 830.50 | direct |
| `lot`, `serial` | `_Q_PI` | 801.40 | direct |
| `expiry` | `_Q_PI`, and `_Q_DATE` for the format | 801.40, 801.18 | direct |
| `rx_only` | `_Q_RX` | 801.109 | direct |
| `name`, `ref` | none: internal consistency, no regulation applies | none | none |
| `sterilization`, `storage` | **none configured.** No section of the device corpus has sterile or storage in its title, and a plausible wrong citation is worse than none | none | none |

Citation procedure is the checker's (`find_citation`): retrieve with the configured retriever (default hybrid RRF, `k = 10`), take the top hit from an accepted section, quote verbatim, never attach a section outside the accepted set. A field with strength `none` simply has no citation and a message saying why. A cited field with no retrieved hit gets `needs_human = true` and "No supporting regulation passage was retrieved." Citation queries are fixed strings and do not contain label content.

Wording rule for every item and for `needs_human_review`: describe what to update or confirm. Never write "compliant", "approved", "no further action" or similar. `checklist_complete` is `true` only when every item has `user_decision` of `confirmed` or `dismissed`, and is therefore `false` right after assessment, and `false` when there are no items.

## 7. Failure cases

| Case | Detection | Result |
|---|---|---|
| Unknown field in `edits` | field not in the table after alias resolution | Not assessed. Listed in `unassessed_edits` with reason `unknown_field` and the list of supported fields. If it was the only edit: `parser: not_implemented`. If other edits are fine: they are assessed, `parser: rules`, and `needs_human_review` names the skipped edit. |
| Ambiguous text | section 3.3 | `422 parser_not_implemented` for a text-only request, with the issues in `details` and a hint to send structured `edits`. Reason it is an error and not a 201: a ChangeRequest needs a `field` and `new_value`, and the rules will not guess them. |
| Text parsed but a value is invalid | value rule fails | Same as ambiguous: 422, issue `invalid_value` naming the field. |
| Structured edit with an invalid value | value rule fails | Not assessed, `unassessed_edits` reason `invalid_value`. A udi_di that fails its check digit also gives barcode `NEEDS_INPUT` on every affected barcode (`required_identifier = udi_di`) so it cannot be missed. |
| No matching template field | section 4 | `linked_label` item, `needs_human`. |
| No labels registered for the product | zero label contexts | Empty `affected`, `needs_human_review` says no label exists. |
| Label has no template (uploaded only) | `template_id` is null | `linked_label` item per edit, `needs_human`, no barcode decision. |
| Template row missing in the database | lookup returns none | treated as no template, same item, warning text names the template id. |
| `old_value_mismatch` | section 2 | warning in `needs_human_review`. |
| `no_change` (new equals current record value), `duplicate_field` | section 2 | 422 with that code. |
| Retriever raises or returns no accepted hit | exception or `find_citation` is None | no citation, item `needs_human`, assessment still returned. |
| LLM provider fails | exception, timeout, empty | rules result stands. |
| Change on a closed change or unknown product | existing checks | existing 404 or 409 behaviour, unchanged. |

## 8. API mapping (22c)

1. `POST /changes` (editor or admin, already enforced): parse (`edits` as given, or `raw_text` through the parser), create the ChangeRequest as today (first edit in `field`, rest in `edits`, `parse_state = proposed`), run the assessment **twice** (as proposed, and as if confirmed), store one assessment, return `201 ChangeAssessment` with `parser: rules` (or `llm`), `affected`, `citations`, `checklist_complete: false`, and `needs_human_review` whenever anything was skipped, warned about or left to a human. When nothing could be handled the response keeps `parser: not_implemented` with an empty `affected` and a message that says it.
2. **Append-only `change_assessments`** (`seq`, `assessment_id` `asm_xxxxxxxx`, `change_id`, `parent_assessment_id`, `payload` JSON with items, citations, warnings and the confirmed variant of the barcode decisions, `created_at`). Same UPDATE and DELETE triggers, audit event `change.assessed`. Stored instead of recomputed because label versions and templates move on, and the checklist a person confirms must be the one they were shown. `impact_id` is deterministic (hash of change, label family, slot or kind, field), so a later assessment of the same change keeps the same ids.
3. **Real `confirmChange`** (`POST /changes/{id}/confirm`, editor or admin) with an **append-only `change_confirmations`** table (`seq`, `confirmation_id`, `change_id`, `assessment_id` it confirms, `decisions` JSON, `created_by`, `created_at`). Rules, first failure wins: 404 unknown change; 409 `change_closed`; 422 `parse_not_confirmed` when `parse_confirmed` is false; 422 `edits_not_supported` when `edits` is sent (a changed edit set is a new change, because ChangeRequest rows are immutable); 422 `unknown_impact` for an `impact_id` not in the assessment. A change with no stored assessment (seeded or older) keeps the mock, as `getJob` does. On success a **new assessment row** is appended: the stored confirmed variant, `parent_assessment_id` = the one confirmed, so barcode decisions of `confirm_<field>` become REGENERATE when nothing else blocks them. `parse_state` of the change is derived as `confirmed` once a confirmation exists. `user_decision` of each item is derived from the latest confirmation (default `pending`). A person may confirm in several requests, each one appends.
4. **Approval points at an assessment.** `Review` gains an optional `assessment_id`, filled by the server from the latest assessment of the change. For an `approve` of a version whose change has an assessment, the latest assessment must have been confirmed (`409 change_not_confirmed`). Changes with no assessment (seed, older) are unaffected.
5. `GET /changes/{id}/affected`: stored items of the latest assessment with their current `user_decision`; mock with `X-Mock: true` for a change without an assessment.
6. `generateArtwork` stays a mock. Everything else stays as it is.
7. Contract tests validate every real response against `openapi.yaml`, as in Steps 20d and 21c.

### Contract additions (CR-18, approved)

| Schema | Addition |
|---|---|
| `ChangeAssessment.parser` | add `rules`, `llm` |
| `ChangeAssessment` | `unassessed_edits` (array of `{field, reason}`), `assessment_id` |
| `AffectedLabel` | `needs_human`, `reason`, `rule_ids`, `barcode_decision` (only on `item_kind: barcode`) |
| `Review` | `assessment_id` |
| `confirmChange` | real 200, plus 404, 409, 422 documented |

`schemas.py` is not touched. Docs updated with it: `DATA_MODEL.md`, `API.md`, `SCHEMA_CHANGE_REQUESTS.md` (CR-18), one mock for the `rules` state.

## 9. Tests planned for 22b (synthetic products and label versions only)

- Fields: every alias, every value rule (valid and invalid), numeric date ambiguity, normalisation.
- Parser rules path: each pattern, clause splitting, ambiguous (two fields, two values, no value, negation), unknown field, invalid value, empty text. LLM path: fake provider returning a valid proposal, an invented value (dropped), a bad field (dropped), an exception (falls back), disabled by default (never called).
- Impact: each table row, no matching slot, label without template, product without labels, two labels with different templates.
- Barcode: each of the six rows and the 830.50 branch, `udi_di` acknowledgement, placeholder in an unchanged payload, placeholder as a new value refused, printed-barcode mismatch warning, payload parity with `record_content` when CV libraries exist (skipped otherwise).
- Assessment: needs_human rules (only rule-decided items are false), citation attached for a cited field, missing citation forces needs_human, a stub retriever with no accepted hit, wording check (no "compliant"), `checklist_complete` false.

## 10. Limits and assumptions

- The old payload comes from the product record, not from decoding the printed label, unless a stored extraction disagrees (flagged).
- Text in the fixed background cannot be seen or edited. The assessment says so for every field with no slot.
- One synthetic template family, text slots only for the fields in section 2, two symbols supported.
- US 21 CFR Parts 801 and 830 only. Sterilization and storage have no cited requirement because the corpus has none.
- The parser handles plain English sentences of the shapes listed. It is not a language understanding system, and it refuses anything else.
- Assessment-time confirmation is false (section 5.2). REGENERATE appears only on the confirmed variant, stored when the change is confirmed (section 8).
- A model change always waits for a new `udi_di` edit (section 5.3).
- The serial rule follows the renderer (required), not `TEMPLATE_SPEC.md` ("where used").
- No claim about compliance, adequacy of the new wording, or whether a change needs FDA notification.

## 11. Decisions taken after review of 22a

1. CR-18 approved (section 8).
2. Unconfirmed encoded change: `required_identifier = confirm_<field>`.
3. Serial is required, matching the renderer.
4. Same old and new value is a no-op and is rejected with a clear message. No implicit keep.
5. New append-only `change_assessments` table. Approval points at an assessment id.
6. `confirmChange` is real in 22c (append-only confirmation rows), so REGENERATE is reachable through the API.
