# Schema change requests (Step 19a)

`src/common/schemas.py` is locked. Its header says changes need a PR that all three team members approve. Nothing here edits it. Each request below describes something the contract needs that `schemas.py` lacks, what the API uses in the meantime, and what a future change would look like.

Interim rule: until a request is approved, the API and mock JSON define these shapes in `openapi.yaml`, and the mock test validates against the OpenAPI schema. Where a `schemas.py` class exists, the test also validates the mapped part with that class, so the locked models stay the single source of truth for the fields they cover.

Status of every request: **proposed, not approved**.

| ID | Missing from `schemas.py` | Needed by | Proposed addition | Interim in the API |
|---|---|---|---|---|
| CR-1 | Product identity and version metadata: `created_at`, `created_by`, `source_change_id`, `supersedes_version`, `intended_market` | Product, ProductVersion, History screen | New `Product` model. Optional metadata on `ProductRecord` (`intended_market: list[str] = []`). | OpenAPI `Product` and `ProductVersion` wrap the existing `ProductRecord` fields unchanged. |
| CR-2 | `LabelTemplate` and `Slot` (size in mm, background, slots with bbox in mm, font, size, alignment, max lines, symbology) | Template setup, generation | New `Slot` and `LabelTemplate` models matching `docs/GENERATION.md`. | OpenAPI `LabelTemplate` and `Slot`. |
| CR-3 | `LabelVersion`: `kind`, `artwork_version`, `status`, files, `draft_watermark`, parent, template reference | Inspect, History, Export | New `LabelVersion` model. | OpenAPI `LabelVersion`. `label_id` and `version` reuse the `LabelExtraction` naming. |
| CR-4 | `Scan` and extraction wrapper: `scan_id`, `source`, `state`, `unclear_fields`, confirmation fields | Upload or scan, Inspect | New `Scan`. Optional `confirmed` fields on `LabelExtraction`. | OpenAPI `Scan` and `Extraction`, where `Extraction` embeds every `LabelExtraction` field unchanged. |
| CR-5 | `CheckResult`: kind, run time, counts, `passed` | Inspect, self-check, re-check | New `CheckResult` model with `findings: list[Flag]`. | OpenAPI `CheckResult`. `passed` is defined as zero critical findings. |
| CR-6 | Regulation citation on a finding: `Flag` only has `evidence_chunk_ids`, no section, title, URL or quote. Also no `field` or `bbox` on a flag. | Findings with regulation citations, Evidence screen | Optional `citations: list[Citation]`, `field: str`, `bbox` on `Flag`, and a new `Citation` model built from `Chunk`. | OpenAPI `Finding` = `Flag` fields plus optional `citations`, `field`, `bbox`. The mock test checks `evidence_chunk_ids` exist in the corpus and that each quote is a substring of its chunk text. |
| CR-7 | `ChangeRequest` holds one field edit only. No plain-language text, parse state, multiple edits or audit fields. | Assess a change | Optional `raw_text`, `parse_state`, `edits`, `created_at`, `created_by` on `ChangeRequest`. | OpenAPI `ChangeRequest` = existing four fields plus the optional ones. First edit stays in `field`, `old_value`, `new_value`. |
| CR-8 | `AffectedLabel` (impact item) | Change Impact screen, list affected labels and fields | New `AffectedLabel` model. | OpenAPI `AffectedLabel`. |
| CR-9 | `GeneratedArtwork`, `BarcodeDecision`, `ChangeLogEntry` | Generate, side by side, export | New models matching the shapes in `DATA_MODEL.md`. `BarcodeDecision.decision` is `Literal["KEEP", "REGENERATE", "NEEDS_INPUT"]`. | OpenAPI schemas of the same names. |
| CR-10 | `Review` (approval record): decision, reviewer, role, comment, `artifact_sha256` | Review and approve | New `Review` model. | OpenAPI `Review`. |
| CR-11 | `PrintVerification` with mismatches and quality | Print verification | New `PrintVerification` model. | OpenAPI `PrintVerification`. |
| CR-12 | `AuditEvent` | History, audit trail | New `AuditEvent` model. | OpenAPI `AuditEvent`. |
| CR-13 | Public mode models: `MedicineMatch`, `Question`, `Answer` with the abstain variant (`reason`, `score_name`, `score`, `threshold`) | Public product page, ask about this label | New models. `reason: Literal["no_evidence", "low_confidence", "out_of_scope", "needs_human_check"]`, `score_name: str` (free string on purpose). | OpenAPI `MedicineMatch`, `AnswerResponse` (oneOf answered, abstained). |
| CR-14 | `ChangeRequest.status` has no `returned` or `rejected` value | Review and approve | Either add `returned` or keep the current rule (a return writes a `Review` row and the change stays `draft`). | Current rule. No change needed unless the team prefers an explicit status. |

## Why not edit schemas.py now

The step brief marks it LOCKED and the working agreement says it needs your approval. The interim approach costs one thing: some shapes are defined in YAML before they exist as Pydantic models, so the test cannot check them with Python types. Promoting them later means converting each OpenAPI schema into a model and swapping the test to import it.

## Assumptions

1. None of these requests is approved. They are a list for the team, not a decision.
2. Optional fields added to existing models (CR-1, CR-4, CR-6, CR-7) are assumed to be backward compatible, because every existing field keeps its type and default.
3. CR-14 recommends doing nothing, to avoid touching `ChangeRequest.status`, which other code may already use.
4. Model names in the proposals are suggestions and can change in review.
