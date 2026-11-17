# Schema change requests (Step 19a)

`src/common/schemas.py` is locked. Its header says changes need a PR that all three team members approve. Nothing here edits it. Each request below says what the contract needs that `schemas.py` lacks, what the API uses in the meantime, and what a future change would look like.

Interim rule: until a request is approved, the API and mock JSON define these shapes in `openapi.yaml`, and the mock test validates against the OpenAPI schema. Where a `schemas.py` class exists, the test also validates the mapped part with that class, so the locked models stay the single source of truth for the fields they cover.

The column "Parth" says whether the request touches Parth's modules (`src/cv`, `src/gen`). Those modules are on his branch (`cv-fixes`) and not yet on main. A "yes" means he should review the request, because his code reads or writes that shape today.

Status update, 2026-11-16: **CR-2, CR-3, CR-4, CR-5, CR-9, CR-10 and CR-11
accepted by Pari**, as explicitly confirmed in the task handoff. This records
acceptance of Parth's recommendations and does not itself edit shared schemas.
Other requests retain their existing status.

| Accepted request | Decision owner | Status |
|---|---|---|
| CR-2 | Pari | Accepted |
| CR-3 | Pari | Accepted |
| CR-4 | Pari | Accepted |
| CR-5 | Pari | Accepted |
| CR-9 | Pari | Accepted |
| CR-10 | Pari | Accepted |
| CR-11 | Pari | Accepted |

| ID | Missing from `schemas.py` | Needed by | Proposed addition | Interim in the API | Parth |
|---|---|---|---|---|---|
| CR-1 | Product identity and version metadata: `created_at`, `created_by`, `source_change_id`, `supersedes_version`, `intended_market` | Product, ProductVersion, History screen | New `Product` model. Optional metadata on `ProductRecord` (`intended_market: list[str] = []`). | OpenAPI `Product` and `ProductVersion` wrap the existing `ProductRecord` fields unchanged. | no |
| CR-2 | `LabelTemplate` and `Slot` (size in mm, background, slots with bbox in mm, font, size, alignment, max lines, symbology, symbol name) | Template setup, generation | New `Slot` and `LabelTemplate` models matching `docs/GENERATION.md` and Parth's `src/gen/templates/test_device.json`. | OpenAPI `LabelTemplate` and `Slot`. | yes |
| CR-3 | `LabelVersion`: `version_id`, `kind`, `artwork_version`, `status`, files, `draft_watermark`, `parent_version_id`, template reference | Inspect, History, Export | New `LabelVersion` model. | OpenAPI `LabelVersion`. `label_id` and `artwork_version` reuse the `LabelExtraction` naming. | yes |
| CR-4 | `Scan` and extraction wrapper: `scan_id`, `source`, `state`, `version_id`, `unclear_fields`, confirmation fields | Upload or scan, Inspect | New `Scan`. Optional `confirmed` fields on `LabelExtraction`. | OpenAPI `Scan` and `Extraction`, where `Extraction` embeds every `LabelExtraction` field unchanged. | yes |
| CR-5 | `CheckResult`: kind, `version_id`, `artifact_sha256`, run time, counts, `passed` (CR-17 adds `needs_human_count` and `coverage`) | Inspect, self-check, re-check, approval | New `CheckResult` model with `findings: list[Flag]`. | OpenAPI `CheckResult`. `passed` is defined as zero critical findings. | yes |
| CR-6 | Regulation citation on a finding: `Flag` only has `evidence_chunk_ids`, no section, title, URL, quote or source type. Also no `field` or `bbox` on a flag. | Findings with regulation citations, Evidence screen, public answers | Optional `citations: list[Citation]`, `field: str`, `bbox` on `Flag`, and a new `Citation` model built from `Chunk` with `source_type: Literal["cfr", "label_section"]`. | OpenAPI `Finding` = `Flag` fields plus optional `citations`, `field`, `bbox`. The mock test checks `evidence_chunk_ids` exist in the corpus and that each `cfr` quote is a substring of its chunk text. | no |
| CR-7 | `ChangeRequest` holds one field edit only. No plain-language text, parse state, multiple edits, audit fields or link to the Review its status came from. | Assess a change, Review | Optional `raw_text`, `parse_state`, `edits`, `latest_review_id`, `closed` (true after a reject, which is terminal), `created_at`, `created_by` on `ChangeRequest`. | OpenAPI `ChangeRequest` = existing six fields plus the optional ones. First edit stays in `field`, `old_value`, `new_value`. | no |
| CR-8 | `AffectedLabel` (impact item), including the `version_id` it was assessed on | Change Impact screen, list affected labels and fields | New `AffectedLabel` model. | OpenAPI `AffectedLabel`. | no |
| CR-9 | `GeneratedArtwork`, `BarcodeDecision`, `ChangeLogEntry` | Generate, side by side, export | New models matching the shapes in `DATA_MODEL.md`. `BarcodeDecision.decision` is `Literal["KEEP", "REGENERATE", "NEEDS_INPUT"]`. `artifact_sha256` is the sha256 of the draft manifest. Parth's renderer currently writes `barcode_action` as `reused` or `generated`, which map to `KEEP` and `REGENERATE`. | OpenAPI schemas of the same names. | yes |
| CR-10 | `Review` (approval record): `version_id`, decision, `user_id` of the reviewer, `reviewer_role`, comment, `artifact_sha256`, `check_id` of the passed CheckResult that cleared it | Review and approve, print verification | New `Review` model. | OpenAPI `Review`. | yes |
| CR-11 | `PrintVerification` with mismatches, quality and the approved `version_id` | Print verification | New `PrintVerification` model. | OpenAPI `PrintVerification`. | yes |
| CR-12 | `AuditEvent` with `user_id` (or `system`) | History, audit trail | New `AuditEvent` model. | OpenAPI `AuditEvent`. | no |
| CR-13 | Public mode models: `MedicineMatch`, `Question`, `Answer` with the abstain variant (`reason`, `score_name`, `score`, `threshold`) | Public product page, ask about this label | New models. `reason: Literal["no_evidence", "low_confidence", "out_of_scope", "needs_human_check"]`, `score_name: str` (free string on purpose). | OpenAPI `MedicineMatch`, `AnswerResponse` (oneOf answered, abstained). | no |
| CR-14 | `ChangeRequest.status` has no `returned` or `rejected` value | Review and approve | Either add `returned` or keep the current rule: status is derived from the latest Review, so a return or reject shows `draft` with `latest_review_id` (see "Status derivation" in `DATA_MODEL.md`). | Current rule. No change needed unless the team prefers an explicit status. | no |
| CR-15 | `Report` and `PublishedPage` pinned to a `version_id` | Export, published product page and QR | New small models with a required, never-changing `version_id`. | OpenAPI `Report` and `PublishedPage`. | no |
| CR-16 | Minimal `User` (`user_id`, `name`, `role`: editor, reviewer, admin) and the rule that the submitter of a change cannot approve it | Review, audit, every write | New `User` model. No login model: the API uses an `X-User-Id` header stub. | OpenAPI `User`, `GET /me`, security scheme `UserHeader`. | no |
| CR-17 | `CheckResult.needs_human_count` and `CheckResult.coverage` (list of `RuleOutcome`: `rule_id`, `outcome`, `reason`), `Finding.rule_id`, and the product registration key `extra.rx_only` (Step 21) | Inspect, re-check, Review screen, checker | Additive. `schemas.py` is not edited: the checker uses a `Finding` subclass of `Flag` in `src/checker/models.py`. If the team wants the fields in `schemas.py`, add `rule_id` to `Flag` and a `RuleOutcome` model. `rx_only` needs no change, it lives in `ProductRecord.extra`. | OpenAPI `RuleOutcome`, `CheckResult`, `Finding`, `ProductCreate.extra`. | no |
| CR-18 | `AbstainedAnswer.sources` (optional list of `Citation`): verbatim passages shown when no answer was generated or it failed verification (Step 23) | Public ask, professional ask | Additive. Optional field on the abstain shape, no answer text is added, `reason` stays `needs_human_check`. Approved in Step 23 because nothing existing changed. | OpenAPI `AbstainedAnswer`, `ProfessionalAbstainedAnswer`. | no |
| CR-19 | New operation `askProfessional` (`POST /ask`, device module only) with `ProfessionalQuestionRequest`, `ProfessionalAnsweredAnswer`, `ProfessionalAbstainedAnswer`, `ProfessionalAnswerResponse`; plus `422` and `503` (`retrieval_unavailable`) documented on `askPublic` | Professional evidence screen | Additive: a new path and new schemas, no existing field changed. Same abstain reasons and score fields as public, no banner, no `based_on`. | OpenAPI as listed, mocks `professional/ask/*.json`. | no |
| CR-21 | Optional AI answer: `mode` query flag (`extractive` default, `ai`) on `askPublic` and `askProfessional`; `202` Job of new kind `ask`; `Job.result` (new `AskJobResult` with `answer`, `model`, `model_used`, `latency_s`, `fallback_reason` of `model_unavailable`, `timeout`, `verification_failed`) | Public ask, professional ask | Additive (Step 24c): the default call is unchanged. New enum value `ask` on `Job.kind`, new optional `Job.result`. Approved because nothing existing changed. | OpenAPI as listed, mocks `*/ask/ai_*.json`. | no |
| CR-22 | Generate, artwork and export: new operation `downloadArtifact` (`GET /artifacts/{artifact_sha256}`); `generateArtwork`, `getArtwork` and `getExports` real, with their error codes and `401`, `403`, `404`, `503` documented; `artifact_sha256` is the PDF hash; `self_check_id` is a `layout` check; new tables `generated_artworks` and `artifacts` | Generate, review, export | Additive (Step 24b): no field changed shape. Stored files keep the DRAFT mark after approval. | OpenAPI as listed, `src/api/artwork.py`. | no |
| CR-23 | Public medicine mode (Step 25a): new operation `matchMedicine` (`POST /public/match`, a product name in, `PublicMatchResult` out); `PublicMatchResult` gains optional `outcome` (`matched`, `needs_review`, `no_reference_match`), `score_name`, `score`, `threshold`, `message`, `sections` (summary, ingredients, warnings, sources); `MedicineMatch` gains optional `not_in_corpus` and `evidence`; `askPublic` with a reference `product_id` answers from that product's label chunks (`Citation.source_type` `label_section`) | Public scan result, public ask | Additive: every new field is optional, the default `askPublic` call with any other `product_id` is unchanged. | OpenAPI as listed, `src/api/medicine.py`. | no |
| CR-24 | `publishVersion` real (Step 25b): reviewer or admin, the latest review must approve this version's artifact hash; `200` on a repeat call; `403`, `404` and the `409` codes `not_approved`, `version_superseded`, `change_closed`, `hash_mismatch` documented; the page is served as HTML at `/versions/{version_id}` (outside the API schema) and its PDF at `/versions/{version_id}/label.pdf` | Review, export, QR | Additive: no field changed shape. The page URL is the payload already printed in the QR files. | OpenAPI as listed, `src/api/publish.py`. | no |
| CR-25 | `RetrievalConfig.method` accepts `e5b` (the frozen Step 18 system) (Step 25c). When E5b cannot be loaded a check falls back to plain hybrid RRF and its `retrieval_config` says `fallback_from: e5b` | Inspect, re-check, search | Additive enum value. Default stays `hybrid_rrf`; the demo server selects E5b with `LABELLENS_CHECKER_RETRIEVAL=e5b`. | OpenAPI `RetrievalConfig`, `src/checker/retrieval.py`. | no |
| CR-26 | Print verification real (Step 25b): `verifyPrint`, `getPrintVerification`, `listPrintVerifications`; `PrintVerification` gains optional `fields` (every compared field with observed text, OCR confidence, box) and `notes`; `verifyPrint` documents `401`, `404`, `422` and the `409` codes `not_approved`, `rejected`, `version_superseded`, `no_reference`; new table `print_verifications` | Print verification | Additive: no existing field changed shape. | OpenAPI as listed, `src/api/printverify.py`. | no |

## Why not edit schemas.py now

The step brief marks it LOCKED, and the working agreement says it needs your approval. The interim approach costs one thing: some shapes are defined in YAML before they exist as Pydantic models, so the test cannot check them with Python types. Promoting them later means converting each OpenAPI schema into a model and switching the test to import it.

## Assumptions

1. The seven requests listed above are accepted by Pari. Other requests remain proposals unless separately recorded.
2. Optional fields added to existing models (CR-1, CR-4, CR-6, CR-7) are assumed to be backward compatible, because every existing field keeps its type and default.
3. CR-14 recommends doing nothing, to avoid touching `ChangeRequest.status`, which other code may already use.
4. Model names in the proposals are suggestions and can change in review.
5. The "Parth" column is based on reading his `cv-fixes` branch (template JSON, `src/gen/render.py` manifest and barcode reuse, `src/cv` extraction and verification). It may change once his code is merged to main.

## Differences from Parth's merged code (checked after merging main at 8e1aed8)

The mock test does not import `src/cv` or `src/gen`, so it still passes. Comparing the contract with the merged renderer (`src/gen/render.py`) and verifier (`src/cv/verify.py`) shows these differences. Nothing in `src/cv` or `src/gen` was edited. Each row needs a decision from Pari and Parth: change the contract, or change the code.

| # | Topic | Contract (docs/contracts) | Merged code | Effect |
|---|---|---|---|---|
| D-1 | Symbology strings | `GS1_DataMatrix`, `GS1-128` | Same (`render.py` accepts exactly these) | Matches |
| D-2 | `symbol_name` | Required on symbol slots, any reference symbol | Required, but only `manufacturer` and `expiry` are supported, minimum 5 mm | The mock template's `sterile_eo` symbol would be flagged `symbol_size_or_type` by the current renderer |
| D-3 | Background | `background` is a path or `null` | Any non-null background is flagged `unsupported_background` | The mock template (with a background path) cannot be rendered yet |
| D-4 | DRAFT band | Top 6 mm reserved (TEMPLATE_SPEC default) | Slots with `y < 9` mm are flagged `watermark_overlap` | Slots at y 6 to 9 mm pass the contract but fail the renderer, including the mock template's `name` and `ref` slots at y = 8 |
| D-5 | Artifact hash | `artifact_sha256` is one string: sha256 of the draft manifest | The manifest has a key `artifact_sha256` holding a dict of per-file hashes (svg, pdf, preview). `verify.py` binds approval to sha256 of the manifest file as `reference_sha256` | Same meaning, different names. The API field means the manifest hash, not the manifest's own `artifact_sha256` dict |
| D-6 | Approval record | `Review` with `user_id`, `reviewer_role`, `artifact_sha256`, `check_id` | `verify.py` expects `{decision, reviewer, reference_sha256}` and no check id | An API Review must be mapped to that shape before print verification. `check_id` is not checked by the code |
| D-7 | Layout finding kinds | `slot_out_of_bounds`, `slot_overlap`, `font_too_small`, `required_field_empty`, `symbol_too_small`, `barcode_too_small` | `clipping`, `overlap`, `font_size`, `required_field`, `symbol_size_or_type`, `barcode_size`, plus `invalid_box`, `unsupported_characters`, `unavailable_font`, `unsupported_slot`, `invalid_size` | Kind strings differ. `Flag.kind` is a free string, so nothing breaks, but the UI should map them |
| D-8 | Extra code limits | Not in the contract | Barcode module at least 0.25 mm; printable ASCII text only | Worth adding to TEMPLATE_SPEC if the team keeps them |
| D-9 | Named SVG groups | `layer-background`, `layer-slots`, `slot-{id}`, `layer-watermark`, `layer-review` | Not emitted (ReportLab SVG without these ids) | Already listed as a gap in TEMPLATE_SPEC assumption 3 |
| D-10 | Barcode decision names | `KEEP`, `REGENERATE`, `NEEDS_INPUT` | `barcode_action` `reused` or `generated`. NEEDS_INPUT is an `IdentifierRequired` or `ValueError` | Matches, as described in CR-9 |
| D-11 | Test placeholder | `00000000000000` with `test_data` | Same, and refused without `test_mode` | Matches |

### Decisions on D-1 to D-11 (Step 20 Phase 0, decided by Pari)

Rule: the contract follows the merged code for D-2, D-4, D-7 and D-8. For D-3, D-5, D-6 and D-9 the contract stays as written and the difference is a documented gap in Parth's code. D-1, D-10 and D-11 already match. Only `docs/contracts` and `src/api/mock` changed. `src/cv` and `src/gen` are untouched.

| # | Decision | What changed or what stays | Owner |
|---|---|---|---|
| D-1 | Matches | Nothing. | none |
| D-2 | Contract follows code | `symbol_name` is `manufacturer` or `expiry` only, minimum 5 mm (TEMPLATE_SPEC, DATA_MODEL, an enum in `openapi.yaml`). The mock templates replace the `sterile_eo` slot with an `mfr_symbol` slot (`manufacturer`), and the sterilization symbol impact item no longer points at a slot. Sterilization and other symbols are future work for Parth. | Parth (future symbols) |
| D-3 | Documented difference, decided | Contract keeps `background` as a path or `null`. The renderer rejects non-null backgrounds for now. Parth fixes it. | Parth |
| D-4 | Contract follows code | DRAFT band is the top 9 mm. The mock template slots `name` and `ref` moved from y = 8 to y = 10 mm, and the failed-check mock says 9 mm. | none |
| D-5 | Documented difference, decided | Contract keeps one `artifact_sha256` string, the sha256 of the manifest file. His per-file hash dict stays internal and he maps it to that single hash. | Parth |
| D-6 | Documented difference, decided | Contract keeps `Review` with `user_id`, `reviewer_role`, `artifact_sha256`, `check_id`. His approval record lacks `check_id` and uses other names, so he adds them. | Parth |
| D-7 | Contract follows code, partly | `clipping` and `overlap` replace `slot_out_of_bounds` and `slot_overlap` (TEMPLATE_SPEC, failed-check mock). The other kind names (`font_too_small`, `required_field_empty`, `symbol_too_small`, `barcode_too_small`) still differ from the code and are not decided yet. | open |
| D-8 | Contract follows code | TEMPLATE_SPEC adds: barcode module at least 0.25 mm (kind `barcode_size`) and printable ASCII only (kind `unsupported_characters`). Both kind names are the code's. | none |
| D-9 | Documented difference, decided | Contract keeps `layer-*` and `slot-{id}` groups. Parth emits them. | Parth |
| D-10 | Matches | Nothing. | none |
| D-11 | Matches | Nothing. | none |

## CR-18 Change assessment fields (approved, Step 22)

Additive. `ChangeAssessment.parser` gains `rules` and `llm`; `ChangeAssessment` gains `unassessed_edits` and `assessment_id`; `AffectedLabel` gains `needs_human`, `reason`, `rule_ids` and `barcode_decision`; `Review` gains `assessment_id`; `confirmChange` is real and documents 401, 403, 404, 409, 422. New append-only tables `change_assessments` and `change_confirmations`. `schemas.py` untouched. Does not touch Parth's code.

## CR-20 Upload, scan and extraction errors (additive, Step 24a)

No schema field changes. `uploadScan`, `getScan`, `getExtraction` and `confirmExtraction` now document `401`, `403`, `404` and `422` where they apply, and the Error code list gains the upload codes: `unsupported_media_type`, `file_too_large`, `image_too_large`, `invalid_file` (422 on upload) and `retake_photo`, `extractor_unavailable`, `scan_failed` (inside `Scan.error` and `Job.error` when the state is `failed`). `retake_photo` carries `details: {reasons, metrics, thresholds}` with reasons `blur`, `low_contrast` or `glare`.

Two behaviours the real server fixes where the contract was open: `product_id` is required on upload (a scan creates a label version, which belongs to a product), and file errors use 422 with a specific code, not 413 or 415, so the response set stays small. A confirmation appends a new extraction row (new `extraction_id`) and a confirmation row; `GET extraction` returns the newest row, with `confirmed: true` and no unclear fields after a confirmation.

## CR-21 Optional AI answer (approved, Step 24c)

Additive. `POST /public/ask` and `POST /ask` accept `?mode=ai`. The default (`extractive`) is the unchanged 200. With `ai` they answer 202 with a `Job` of kind `ask`; `GET /jobs/{job_id}` returns the job and, when done, `result` (`AskJobResult`). The model is qwen2.5 3b with the structured-output config of Step 23e. The job never fails because of the model: Ollama missing or failing gives `fallback_reason: model_unavailable`, no answer within 90 seconds gives `timeout`, a reply that fails the citation checks gives `verification_failed`; in each case `answer` holds the extractive passages. Only a retrieval system that cannot be built ends the job `failed` (`retrieval_unavailable`). Limits are in `docs/AI_ANSWER.md`.

## CR-22 Generate, artwork and export (additive, Step 24b)

New operation `downloadArtifact` (`GET /artifacts/{artifact_sha256}`) that serves a stored file after re-hashing it. `generateArtwork`, `getArtwork` and `getExports` are real and document `401`, `403`, `404`, `503` where they apply, and `409` and `422` list their error codes (`nothing_assessed`, `template_required`, `stale_change`, `barcode_decision_mismatch`, `unsupported_edits`, `unsupported_template`, `template_background_unsupported`, `product_incomplete`, `generation_refused`, `no_artifacts`, `artifact_missing`, `not_published`). No existing field changed shape. Four things the real server fixes where the contract was open:

- `artifact_sha256` is the sha256 of the PDF bytes (it was "the draft manifest"; the merged renderer writes no manifest).
- `GeneratedArtwork.self_check_id` is a `layout` CheckResult written with the draft. Approval of generated artwork needs a `self_check` (the re-check), and `layout` checks do not count for the derived status, so a fresh draft is `draft`, not `checked`.
- Stored files keep the DRAFT mark even after approval (no approved variant is rendered), so `draft_watermark` stays true for generated versions.
- New append-only tables `generated_artworks` and `artifacts`. A generation creates a product version with `source_change_id`, a template version (one per generation) and the draft label version, in one transaction.

`schemas.py` untouched. Does not touch Parth's code. Still open: D-3, D-5 (a template with a background image is refused with `template_background_unsupported`), D-6 and D-9, and rendering an approved variant without the DRAFT band.

## CR-23 Public medicine mode (additive, Step 25a)

`POST /public/match` takes a product name (typed, or read from a photo by the extractor) and answers with the nearest of the ten reference products or `no_reference_match`. Ranking is the frozen E5b recipe over ten small product documents; the accept decision is the bge-large cosine of the top product against a threshold (0.65, fitted on 30 hand-written names, `results/step25_medicine_match.md`). Between 0.65 and 0.70, or when the second product is within 0.02, the outcome is `needs_review`. Reference fields (dosage form, active substance, pack size) are derived from the product's own label text, each with the chunk and the verbatim words it came from; a field no rule found is left out and named in `not_in_corpus`. The manufacturer is never in the corpus text, so it is `not_in_corpus` for every product (nothing was fetched or typed in). `sections` holds up to 3 summary chunks (uses), 3 ingredient chunks (the description section, else the package panel text, said in `ingredients_note`), up to 6 warning chunks and the pinned DailyMed source. `askPublic` with a reference `product_id` retrieves only inside that product's chunks (no score gate: rank scores are not comparable in a pool of 15), says `based_on` the DailyMed label, and shows extractive passages unless a model is on. Image scans (`publicScan`) are still a mock.

## CR-24 publishVersion (additive, Step 25b)

Publishing creates a `PublishedPage` pinned to the version. It needs the latest review of that exact version to be an approval of its own `artifact_sha256`, an open change, and the version to still be the change's latest (a newer version voids the approval, as for review). A repeat call returns the same page with `200`. The stored files of a generated version still carry the DRAFT mark, and the public page says so. The QR files become downloadable once the version is published.

## CR-25 E5b as a checker retrieval method (additive, Step 25c)

`e5b` is a new value of `RetrievalConfig.method`. The default is unchanged, so every earlier evaluation reproduces. See `reports/step25.md` for the load and check times that justified using it in the demo.

## CR-26 Print verification (additive, Step 25b)

`POST /label-versions/{id}/print-verifications` takes a photo (PNG or JPEG) and a condition and answers 202 with a Job of kind `print_verify`. The request refuses an unapproved version before any job exists. The job runs the quality gate (a photo that is too blurry or has glare ends as `rescan_needed`, not as a failed job), then the CV extractor and the comparison steps of `src.cv.print_verify` (blind OCR with post-correction, exact per-field compare after key removal, barcode values). `src.cv.verify_print` itself is not called: its gate binds an approval to the sha256 of a legacy manifest file while this API binds approval to the sha256 of the PDF (CR-22), so the two can never agree and no approval record is fabricated to satisfy it. The API enforces the approval gate. Symbols are not compared because the detector is not trusted. Outcome mapping: `MATCH` is match, `MISMATCH` is mismatch, `NEEDS_HUMAN_REVIEW` is `rescan_needed` with a reason. `quality.blur` and `quality.glare` are display numbers derived from the gate's measurements; `quality.confidence` is the weakest OCR confidence among compared fields.
