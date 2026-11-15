# Data model (contract, Step 19a)

This document lists every entity the API, the mock JSON and the database share. It is a contract, not an implementation. `src/common/schemas.py` is locked, so each field says whether it maps to a class in that file. Anything that does not map is `NONE` and points to a numbered request in `SCHEMA_CHANGE_REQUESTS.md` (CR-n).

Reading guide for the tables: `req` means required in API responses, `opt` means may be absent or empty. Types use JSON names (string, number, integer, boolean, array, object). All timestamps are ISO 8601 in UTC, for example `2026-11-15T09:30:00Z`.

## Conventions

- **Modules.** The professional device module and the public medicine module share infrastructure but not data. Every entity below belongs to the device module unless it sits in the "Public medicine mode" section. `Chunk.module` is `device` or `medicine`, and a device query never returns a medicine chunk.
- **IDs.** Opaque strings with a readable prefix (`prd_`, `tpl_`, `lbl_`, `scn_`, `ext_`, `chk_`, `chg_`, `imp_`, `art_`, `rev_`, `pvf_`, `evt_`). Clients never parse them. `Chunk.chunk_id` keeps its existing form, for example `fda_21cfr801_s801.1_c1`.
- **Nothing is overwritten.** Every edit creates a new version row. See "Version history rules".
- **Identifiers (GTIN, UDI-DI).** They come from the product record or an authorized user. LabelLens never generates them. When a change needs a new one the API returns a barcode decision of `NEEDS_INPUT` and the server code raises `IdentifierRequired` (defined in `schemas.py`).
- **Draft marking.** Every generated artwork carries a DRAFT watermark until an approval record exists.

## Entity overview and relations

```
Product 1---* ProductVersion            (ProductVersion is a ProductRecord plus metadata)
Product 1---* LabelTemplate             (one row per template version)
Product 1---* LabelVersion              (artwork L1, L2, ...)
LabelVersion *---1 ProductVersion       (which record the artwork was made from)
LabelVersion *---1 LabelTemplate        (template and version used)
Scan 1---0..1 Extraction                (one confirmed extraction per scan)
Extraction *---1 LabelVersion           (label_id)
CheckResult *---1 LabelVersion          (inspection, layout and self-check runs)
CheckResult 1---* Finding               (a Finding is a Flag plus citations)
Finding *---* Chunk                     (evidence_chunk_ids, citations)
ChangeRequest *---1 Product
ChangeRequest 1---* AffectedLabel       (impact items)
ChangeRequest 1---0..* GeneratedArtwork (each regeneration is a new row)
GeneratedArtwork 1---1 LabelVersion     (the draft it created)
LabelVersion 1---* Review               (approve, return or reject decisions)
LabelVersion 1---* PrintVerification    (only an approved version can be verified)
Any entity ---* AuditEvent              (append only)
```

---

## Product

Stable identity of a device. Its changing content lives in `ProductVersion`.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `product_id` | string | req | `ProductRecord.product_id` | Same value on every version. |
| `module` | string, `device` | req | `Chunk.module` values | Always `device` here. |
| `current_version` | integer | req | `ProductRecord.version` | Points at the latest ProductVersion. |
| `created_at` | timestamp | req | NONE (CR-1) | |
| `intended_market` | array of string | opt | NONE (CR-1) | For example `["US"]`. PRODUCT_SPEC lists it as part of the product record. |

## ProductVersion

Exactly the fields of `ProductRecord`, plus version metadata. Immutable once written.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `product_id` | string | req | `ProductRecord.product_id` | |
| `version` | integer, starts at 1 | req | `ProductRecord.version` | |
| `name` | string | req | `ProductRecord.name` | |
| `model` | string | opt | `ProductRecord.model` | Default empty string. |
| `manufacturer` | string | opt | `ProductRecord.manufacturer` | |
| `manufacturer_address` | string | opt | `ProductRecord.manufacturer_address` | |
| `udi_di` | string | opt | `ProductRecord.udi_di` | Allocated by the company. Empty means "not yet entered". |
| `sterilization` | string | opt | `ProductRecord.sterilization` | |
| `storage` | string | opt | `ProductRecord.storage` | |
| `extra` | object of string | opt | `ProductRecord.extra` | Free fields such as `ref`. |
| `created_at` | timestamp | req | NONE (CR-1) | |
| `created_by` | string (user id) | req | NONE (CR-1) | |
| `source_change_id` | string | opt | NONE (CR-1) | The ChangeRequest that produced this version. Empty for the first version. |
| `supersedes_version` | integer | opt | NONE (CR-1) | Previous version number. |

## LabelTemplate

Per product and template version. Full semantics are in `TEMPLATE_SPEC.md`. The JSON shape follows `docs/GENERATION.md`.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `template_id` | string | req | NONE (CR-2) | |
| `product_id` | string | req | `ProductRecord.product_id` | |
| `version` | integer | req | NONE (CR-2) | Increases on every template edit. |
| `size_mm` | object `{w, h}` of number | req | NONE (CR-2) | Physical label size in millimetres. |
| `background` | string (artwork file path) | req | NONE (CR-2) | Fixed content: logos, borders, fixed text. |
| `slots` | array of Slot | req | NONE (CR-2) | |
| `created_at`, `created_by` | timestamp, string | req | NONE (CR-2) | |

Slot:

| Field | Type | Req | Notes |
|---|---|---|---|
| `id` | string | req | Unique inside the template, becomes an SVG group id. |
| `type` | `text`, `symbol` or `barcode` | req | |
| `field` | string | req | Name of the product field shown. Text fields map to `ProductRecord` fields or keys of `extra`. |
| `bbox_mm` | array of 4 numbers `[x, y, w, h]` | req | Millimetres from the top left corner. Not pixels, so it differs from `OcrBlock.bbox`. |
| `font`, `size_pt`, `align`, `max_lines` | string, number, string, integer | text only | |
| `symbology` | string | barcode only | `GS1_DataMatrix` or `GS1_128`. |

## LabelVersion

One row per uploaded or generated artwork. Mockup names: "Product P1", "Artwork L2".

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `label_id` | string | req | `LabelExtraction.label_id` | Same id links to its extraction. |
| `product_id` | string | req | `ProductRecord.product_id` | |
| `artwork_version` | integer | req | `LabelExtraction.version` | The L1, L2, L3 counter for this label family. |
| `product_version` | integer | req | `ProductRecord.version` | Record the artwork was made against. |
| `template_id`, `template_version` | string, integer | opt | NONE (CR-2) | Absent for an uploaded label with no template yet. |
| `kind` | `uploaded` or `generated` | req | NONE (CR-3) | |
| `status` | `draft`, `checked`, `reviewed`, `published` | req | `ChangeRequest.status` values | Same four values. |
| `artwork_file` | string | req | NONE (CR-3) | Original upload or rendered SVG. |
| `pdf_file` | string | opt | NONE (CR-3) | PDF at physical size, generated labels only. |
| `draft_watermark` | boolean | req | NONE (CR-3) | True until an approval exists. |
| `parent_label_id` | string | opt | NONE (CR-3) | The label this one revises. |
| `created_at`, `created_by` | timestamp, string | req | NONE (CR-3) | |

## Scan

A single upload or camera capture before and during extraction.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `scan_id` | string | req | NONE (CR-4) | |
| `module` | `device` or `medicine` | req | `Chunk.module` values | Chooses the module, never both. |
| `source` | `upload` or `camera` | req | NONE (CR-4) | |
| `file` | object `{file_id, mime, sha256, pages}` | req | NONE (CR-4) | |
| `product_id` | string | opt | `ProductRecord.product_id` | Set when the user picked a product. |
| `state` | `queued`, `processing`, `done`, `failed` | req | NONE (CR-4) | Drives the loading state. |
| `label_id` | string | opt | `LabelExtraction.label_id` | Set when `done`. |
| `created_at` | timestamp | req | NONE (CR-4) | |

## Extraction

`LabelExtraction` as defined in `schemas.py`, wrapped with confirmation state.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `label_id` | string | req | `LabelExtraction.label_id` | |
| `version` | integer | req | `LabelExtraction.version` | |
| `fields` | object of string | req | `LabelExtraction.fields` | Field name to text read from the label. |
| `warnings` | array of string | req | `LabelExtraction.warnings` | |
| `barcodes` | array of BarcodeResult | req | `LabelExtraction.barcodes` | `{type, raw, parsed, bbox}` as in `BarcodeResult`. |
| `symbols` | array of SymbolDetection | req | `LabelExtraction.symbols` | `{name, iso_ref, bbox, conf}`. |
| `ocr_blocks` | array of OcrBlock | req | `LabelExtraction.ocr_blocks` | `{text, bbox, conf}`. Pixel coordinates of the original image. |
| `extraction_id`, `scan_id` | string | req | NONE (CR-4) | |
| `unclear_fields` | array of string | opt | NONE (CR-4) | Fields the user must confirm. |
| `confirmed`, `confirmed_by`, `confirmed_at` | boolean, string, timestamp | opt | NONE (CR-4) | Set by "Confirm extraction". |

## CheckResult

One run of the checker, the layout checks or the closed-loop self-check against one label version.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `check_id` | string | req | NONE (CR-5) | |
| `label_id` | string | req | `LabelExtraction.label_id` | |
| `kind` | `inspection`, `layout`, `self_check` | req | NONE (CR-5) | |
| `run_at` | timestamp | req | NONE (CR-5) | |
| `findings` | array of Finding | req | `Flag` | |
| `critical_count`, `review_count`, `info_count` | integer | req | NONE (CR-5) | Derived from `findings[].severity`. |
| `passed` | boolean | req | NONE (CR-5) | True when zero critical findings (GENERATION.md "Pass means zero critical flags"). |

## Finding (a Flag with regulation citations)

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `flag_id` | string | req | `Flag.flag_id` | |
| `kind` | string | req | `Flag.kind` | `field_mismatch`, `barcode_mismatch`, `missing_symbol`, `missing_warning` and layout kinds such as `text_overflow`. |
| `severity` | `info`, `review`, `critical` | req | `Flag.severity` | |
| `message` | string | req | `Flag.message` | |
| `observed` | string | opt | `Flag.observed` | |
| `expected` | string | opt | `Flag.expected` | |
| `evidence_chunk_ids` | array of string | req | `Flag.evidence_chunk_ids` | Must be real ids from the corpus. |
| `confidence` | number 0 to 1 | req | `Flag.confidence` | |
| `needs_human` | boolean | req | `Flag.needs_human` | True when evidence is weak. The UI shows "Needs review", never a guess. |
| `citations` | array of Citation | opt | NONE (CR-6) | Regulation citation details, below. |
| `field` | string | opt | NONE (CR-6) | Field or slot the finding is about. |
| `bbox` | array of 4 numbers | opt | NONE (CR-6) | Box on the original image for highlighting. |

Citation (derived from a `Chunk`, so no text is invented):

| Field | Type | Maps to |
|---|---|---|
| `chunk_id` | string | `Chunk.chunk_id` |
| `source` | string | `Chunk.source` |
| `section` | string | `Chunk.section` (for example `801.18`) |
| `title` | string | `Chunk.title` |
| `url` | string | `Chunk.url` |
| `quote` | string | A verbatim excerpt of `Chunk.text`. |

## ChangeRequest

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `change_id` | string | req | `ChangeRequest.change_id` | |
| `product_id` | string | req | `ChangeRequest.product_id` | |
| `field` | string | req | `ChangeRequest.field` | For a multi-field change see `edits`. |
| `old_value` | string | opt | `ChangeRequest.old_value` | |
| `new_value` | string | req | `ChangeRequest.new_value` | |
| `status` | `draft`, `checked`, `reviewed`, `published` | req | `ChangeRequest.status` | A returned change stays `draft` and a Review row records the return. |
| `raw_text` | string | opt | NONE (CR-7) | Plain-language request as typed. |
| `parse_state` | `proposed` or `confirmed` | req | NONE (CR-7) | A parser proposes, the user confirms. |
| `edits` | array of `{field, old_value, new_value}` | opt | NONE (CR-7) | Extra fields beyond the first. |
| `created_at`, `created_by` | timestamp, string | req | NONE (CR-7) | |

## AffectedLabel (impact item)

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `impact_id` | string | req | NONE (CR-8) | |
| `change_id` | string | req | `ChangeRequest.change_id` | |
| `label_id` | string | req | `LabelExtraction.label_id` | The affected label, possibly a different label of the same product. |
| `slot_id` | string | opt | NONE (CR-8) | Affected slot, absent for a whole-label item such as "Instructions for use". |
| `item_kind` | `text`, `symbol`, `barcode`, `linked_label` | req | NONE (CR-8) | |
| `title`, `description` | string | req | NONE (CR-8) | Mockup: "Sterilization text". |
| `suggestion` | `review_suggested`, `edit_required`, `no_change` | req | NONE (CR-8) | |
| `evidence_chunk_ids` | array of string | req | `Flag.evidence_chunk_ids` | |
| `user_decision` | `pending`, `confirmed`, `dismissed` | req | NONE (CR-8) | The checklist the user confirms before any artwork changes. |

## GeneratedArtwork

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `artwork_id` | string | req | NONE (CR-9) | |
| `change_id` | string | req | `ChangeRequest.change_id` | |
| `label_id` | string | req | `LabelExtraction.label_id` | The new draft label version. |
| `template_id`, `template_version` | string, integer | req | NONE (CR-9) | |
| `svg_url`, `pdf_url` | string | req | NONE (CR-9) | PDF is vector at `size_mm`. |
| `size_mm` | object `{w, h}` | req | NONE (CR-9) | |
| `draft_watermark` | boolean | req | NONE (CR-9) | True until approved. |
| `barcode_decision` | BarcodeDecision | req | NONE (CR-9) | See below. |
| `change_log` | array of ChangeLogEntry | req | NONE (CR-9) | Who, what, why, rules fired, evidence. |
| `layout_problems` | array of string | req | NONE (CR-9) | Also reported as Findings in the self-check. |
| `self_check_id` | string | req | NONE (CR-9) | A CheckResult of kind `self_check`. |
| `artifact_sha256` | string | req | NONE (CR-9) | Hash of the rendered package. The approval binds to it. |
| `disclaimer` | string | req | NONE (CR-9) | Fixed text: "Draft generated for review. Not a compliance determination." |

BarcodeDecision: `decision` (`KEEP`, `REGENERATE`, `NEEDS_INPUT`), `old_payload`, `new_payload` (string, may be empty), `symbology`, `reason`, `required_identifier` (string, set when `NEEDS_INPUT`, for example `udi_di`). Rule text is in `TEMPLATE_SPEC.md`.

ChangeLogEntry: `at`, `actor`, `field`, `old_value`, `new_value`, `reason`, `rules_fired` (array of string), `evidence_chunk_ids` (array of string).

## Review (approval record)

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `review_id` | string | req | NONE (CR-10) | |
| `label_id` | string | req | `LabelExtraction.label_id` | |
| `change_id` | string | opt | `ChangeRequest.change_id` | |
| `decision` | `approve`, `return`, `reject` | req | NONE (CR-10) | |
| `reviewer_id`, `reviewer_role` | string | req | NONE (CR-10) | Role must be authorized to approve. |
| `comment` | string | req for `return` and `reject` | NONE (CR-10) | |
| `artifact_sha256` | string | req | NONE (CR-10) | Must equal the GeneratedArtwork hash. Prevents approving something other than what was reviewed. |
| `resulting_status` | `draft`, `checked`, `reviewed`, `published` | req | `ChangeRequest.status` values | |
| `decided_at` | timestamp | req | NONE (CR-10) | |

Publication is a separate request from approval where possible. A label is `published` only when a Review with `decision = approve` exists for its exact `artifact_sha256`.

## PrintVerification

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `verification_id` | string | req | NONE (CR-11) | |
| `label_id` | string | req | `LabelExtraction.label_id` | Must be an approved label. |
| `photo_file` | object `{file_id, mime, sha256}` | req | NONE (CR-11) | |
| `condition` | `clean_print_scan`, `phone_photo`, `blur`, `glare` | req | NONE (CR-11) | Metrics are reported per condition, never blended. |
| `outcome` | `match`, `mismatch`, `rescan_needed` | req | NONE (CR-11) | |
| `mismatches` | array of `{field, expected, observed, bbox}` | req | NONE (CR-11) | |
| `barcode` | `{expected_payload, decoded, match}` | opt | `BarcodeResult` for the decoded part | |
| `quality` | `{blur, glare, confidence}` numbers 0 to 1 | req | NONE (CR-11) | Low values produce `rescan_needed`. |
| `rescan_reason` | string | opt | NONE (CR-11) | |
| `created_at` | timestamp | req | NONE (CR-11) | |

## AuditEvent

Append only. Never updated or deleted.

| Field | Type | Req | Maps to | Notes |
|---|---|---|---|---|
| `event_id` | string | req | NONE (CR-12) | |
| `at` | timestamp | req | NONE (CR-12) | |
| `actor` | string | req | NONE (CR-12) | User id, or `system`. |
| `action` | string | req | NONE (CR-12) | For example `product.version_created`, `artwork.generated`, `review.approved`, `export.downloaded`. |
| `entity_type`, `entity_id` | string | req | NONE (CR-12) | |
| `version_before`, `version_after` | integer | opt | NONE (CR-12) | |
| `details` | object | opt | NONE (CR-12) | |

## Referenced but not detailed here

`Chunk` and `Hit` (used by evidence and search) map to `Chunk` and `Hit` in `schemas.py` with no change. `Report` (inspection report PDF) and `PublishedPage` (the page a supplementary QR opens) appear in PRODUCT_SPEC's core tables. In the API they are exports of a label version and carry only a URL and a `label_id`, so they do not need their own tables in this contract.

## Public medicine mode

Separate data, rules and results from the device module.

- **Corpus.** The public reference corpus is 21 CFR Parts 201, 208 and 211 only (plus the matched label, see below). Questions outside these sources must be answered with an abstain (`out_of_scope`), not with device-module content.
- All public-mode shapes below are `NONE` in `schemas.py` (CR-13). `Citation` reuses `Chunk` fields.
- **MedicineMatch**: `product_name`, `dosage_form`, `active_substance`, `pack_size`, `manufacturer`, `reference_label_url`, `match_confidence` (number), `read_from_photo` (object of string), `from_reference_label` (object of string). The banner "Authenticity not verified. Based on a reference label match." is a required constant.
- **Question**: `question` (string), `product_id` (string). **Answer** is one of two shapes, discriminated by `abstained`:
  - `abstained = false`: `answer` (string), `sources` (array of Citation), `based_on` (string, the matched label).
  - `abstained = true`: `reason` (one of `no_evidence`, `low_confidence`, `out_of_scope`, `needs_human_check`), `score_name` (free string, so the score can change later), `score` (number), `threshold` (number), `message` (string, plain language), no `answer`.
  The abstention score is provisional. Step 16 measured the hybrid top score at AUROC 0.985 [0.930, 1.000] on 20 LLM-graded queries, which is a small sample.

## Version history rules

1. **Append only.** An edit to a product, template, label, change or review inserts a new row with the next version number. No UPDATE of content columns. Status columns on the newest label row may move forward through `draft`, `checked`, `reviewed`, `published`, and each move writes an AuditEvent.
2. **Version numbers are per entity family and gapless.** Product versions 1, 2, 3 for a product. Artwork versions L1, L2, L3 for a label family. Template versions per template.
3. **A version records its inputs.** A LabelVersion stores the `product_version` and `template_version` it was built from. A GeneratedArtwork stores the `change_id`. This lets the History screen replay what produced each artwork.
4. **Published and approved versions are immutable.** A fix is a new version that supersedes the old one. The old one stays readable.
5. **Approval binds to bytes.** A Review stores `artifact_sha256`. If the artwork changes, the hash changes and the earlier approval no longer applies.
6. **A returned change** keeps the artwork as it was, writes a Review (`decision = return`, comment) and leaves the ChangeRequest at `draft`. The next regeneration creates a new GeneratedArtwork and a new LabelVersion.
7. **Reads pin a version.** Every read endpoint accepts a version where relevant, and the QR page links a specific version.

## Assumptions

1. The entity list in the Step 19 brief is complete. `Report` and `PublishedPage` are treated as exports, not tables.
2. `size_mm` and `bbox_mm` are millimetres from the top left corner. Pixel boxes (`OcrBlock.bbox`, `SymbolDetection.bbox`) keep the coordinates of the original image, as `schemas.py` already does.
3. A returned change stays `draft` instead of adding a `returned` status, because `ChangeRequest.status` is locked to four values. A `returned` value is deferred to a change request only if the team wants it.
4. Prefixed opaque ids are acceptable. `schemas.py` only types ids as strings.
5. The Citation object is derived from the existing `Chunk` fields and a verbatim quote, so no new text source is introduced.
6. Authorization (who counts as an authorized reviewer) is checked by the server and recorded as `reviewer_role`. This contract does not define the role list.
7. The abstention score is provisional and may be replaced, which is why `score_name` is a free string.
8. The public corpus is limited to 21 CFR 201, 208 and 211 as stated in the project brief. If DailyMed or openFDA labels are added later, `out_of_scope` handling must be revisited.
