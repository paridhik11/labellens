# Schema change requests (Step 19a)

`src/common/schemas.py` is locked. Its header says changes need a PR that all three team members approve. Nothing here edits it. Each request below says what the contract needs that `schemas.py` lacks, what the API uses in the meantime, and what a future change would look like.

Interim rule: until a request is approved, the API and mock JSON define these shapes in `openapi.yaml`, and the mock test validates against the OpenAPI schema. Where a `schemas.py` class exists, the test also validates the mapped part with that class, so the locked models stay the single source of truth for the fields they cover.

The column "Parth" says whether the request touches Parth's modules (`src/cv`, `src/gen`). Those modules are on his branch (`cv-fixes`) and not yet on main. A "yes" means he should review the request, because his code reads or writes that shape today.

Status of every request: **proposed, not approved**.

| ID | Missing from `schemas.py` | Needed by | Proposed addition | Interim in the API | Parth |
|---|---|---|---|---|---|
| CR-1 | Product identity and version metadata: `created_at`, `created_by`, `source_change_id`, `supersedes_version`, `intended_market` | Product, ProductVersion, History screen | New `Product` model. Optional metadata on `ProductRecord` (`intended_market: list[str] = []`). | OpenAPI `Product` and `ProductVersion` wrap the existing `ProductRecord` fields unchanged. | no |
| CR-2 | `LabelTemplate` and `Slot` (size in mm, background, slots with bbox in mm, font, size, alignment, max lines, symbology, symbol name) | Template setup, generation | New `Slot` and `LabelTemplate` models matching `docs/GENERATION.md` and Parth's `src/gen/templates/test_device.json`. | OpenAPI `LabelTemplate` and `Slot`. | yes |
| CR-3 | `LabelVersion`: `version_id`, `kind`, `artwork_version`, `status`, files, `draft_watermark`, `parent_version_id`, template reference | Inspect, History, Export | New `LabelVersion` model. | OpenAPI `LabelVersion`. `label_id` and `artwork_version` reuse the `LabelExtraction` naming. | yes |
| CR-4 | `Scan` and extraction wrapper: `scan_id`, `source`, `state`, `version_id`, `unclear_fields`, confirmation fields | Upload or scan, Inspect | New `Scan`. Optional `confirmed` fields on `LabelExtraction`. | OpenAPI `Scan` and `Extraction`, where `Extraction` embeds every `LabelExtraction` field unchanged. | yes |
| CR-5 | `CheckResult`: kind, `version_id`, `artifact_sha256`, run time, counts, `passed` | Inspect, self-check, re-check, approval | New `CheckResult` model with `findings: list[Flag]`. | OpenAPI `CheckResult`. `passed` is defined as zero critical findings. | yes |
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

## Why not edit schemas.py now

The step brief marks it LOCKED, and the working agreement says it needs your approval. The interim approach costs one thing: some shapes are defined in YAML before they exist as Pydantic models, so the test cannot check them with Python types. Promoting them later means converting each OpenAPI schema into a model and switching the test to import it.

## Assumptions

1. None of these requests is approved. They are a list for the team, not a decision.
2. Optional fields added to existing models (CR-1, CR-4, CR-6, CR-7) are assumed to be backward compatible, because every existing field keeps its type and default.
3. CR-14 recommends doing nothing, to avoid touching `ChangeRequest.status`, which other code may already use.
4. Model names in the proposals are suggestions and can change in review.
5. The "Parth" column is based on reading his `cv-fixes` branch (template JSON, `src/gen/render.py` manifest and barcode reuse, `src/cv` extraction and verification). It may change once his code is merged to main.
