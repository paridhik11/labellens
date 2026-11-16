# Screens (contract, Step 19d)

Every screen in the website, its states, which endpoint feeds each state, and the mock JSON file that stands in for that response. Screens follow `docs/mockup/website_concept.png` and `docs/PRODUCT_SPEC.md`. Endpoints are `operationId`s in `openapi.yaml`. Mock files live under `src/api/mock/` and are listed with their schema in `src/api/mock/index.json`. `tests/test_mock_contracts.py` validates every one.

## State vocabulary

| State | Meaning on screen | Typical response |
|---|---|---|
| `empty` | Nothing yet: no products, no hits, no reviews | A list with zero items, or zero candidates |
| `loading` | Work in progress, spinner or progress bar | `202` Job envelope with `state` queued or processing, polled at `getJob` |
| `success` | Normal result | The endpoint's `200` or `201` body |
| `failed_check` | A check ran and found critical problems | CheckResult with `passed: false`, or a print verification `mismatch` |
| `needs_review` | The system will not guess; a person must look | Finding with `needs_human: true`, unclear fields, several product candidates, `rescan_needed`, or a NEEDS_HUMAN_REVIEW reason |
| `approved` | An approval record exists | Review with `decision: approve`, or an export with a QR |
| `abstained` | Public chatbot declines to answer | AbstainedAnswer with one of the four reasons |
| `failed` | The job itself failed (bad file, decoder crash) | Job with `state: failed` and an Error |

Every professional screen shows the signed-in user (`getCurrentUser`, mock `professional/session/me.json`). Every draft view shows the DRAFT mark and "Draft generated for review. Not a compliance determination."

## Public mode

The public corpus is 21 CFR 201, 208 and 211 only. The banner "Authenticity not verified. Based on a reference label match." shows on every public result.

### P1. Scan and Understand (mockup panel 1)
Camera or upload of medication packaging.

| State | Endpoint | Mock |
|---|---|---|
| empty | none (idle screen, no request yet) | none |
| loading | `publicScan` 202, then `getJob` | `public/scan/loading.json` |
| failed | `getJob` (state failed) | `public/scan/failed.json` |

### P2. Product information (mockup panel 2)
"Read from your photo" beside "From the reference label", tabs Summary, Ingredients, Warnings, Sources.

| State | Endpoint | Mock |
|---|---|---|
| success | `getPublicScan`, one candidate | `public/product/success.json` |
| needs_review | `getPublicScan`, several candidates (show the picker) | `public/product/needs_review.json` |
| empty | `getPublicScan`, no candidate ("No reference label found") | `public/product/empty.json` |

### P3. Ask about this label (chat box in panel 2)

| State | Endpoint | Mock |
|---|---|---|
| success | `askPublic`, cited answer | `public/ask/success.json` |
| abstained (out of scope) | `askPublic` | `public/ask/abstained_out_of_scope.json` |
| abstained (low confidence) | `askPublic` | `public/ask/abstained_low_confidence.json` |
| abstained (no evidence) | `askPublic` | `public/ask/abstained_no_evidence.json` |
| abstained (needs human check) | `askPublic` | `public/ask/abstained_needs_human_check.json` |

## Professional workspace

Left navigation: Products, Inspect, Evidence, Changes, History (mockup panels 3 and 4). Template setup, Review, Export and Print verification open from those.

### D1. Products

| State | Endpoint | Mock |
|---|---|---|
| empty | `listProducts`, zero items | `professional/products/empty.json` |
| success | `listProducts` | `professional/products/success.json` |
| success (one product) | `getProduct` | `professional/product_detail/success.json` |

### D2. Template setup (draw and name slots)

| State | Endpoint | Mock |
|---|---|---|
| success | `registerTemplate` 201 | `professional/template_setup/success.json` |
| failed_check | `registerTemplate` 422, layout findings such as a slot in the DRAFT band | `professional/template_setup/failed_check.json` |

### D3. Upload or scan a device label

| State | Endpoint | Mock |
|---|---|---|
| loading | `uploadScan` 202, then `getJob` | `professional/upload/loading.json` |
| failed | `getJob` (state failed) | `professional/upload/failed.json` |
| success | `getScan` (state done, `version_id` set) | `professional/upload/success.json` |

### D4. Inspect ("Label review", mockup panel 3)
Label image with highlighted boxes, extracted fields, findings with observed and reference values and evidence.

| State | Endpoint | Mock |
|---|---|---|
| success (extraction) | `getExtraction` | `professional/inspect/extraction_success.json` |
| needs_review (extraction) | `getExtraction` with `unclear_fields` ("Confirm extraction") | `professional/inspect/extraction_needs_review.json` |
| success (confirmed extraction) | `confirmExtraction` 200, unclear fields resolved | `professional/inspect/extraction_confirmed.json` |
| loading | `inspectLabel` 202, then `getJob` | `professional/inspect/loading.json` |
| success (inspection) | `inspectLabel` 200, `passed: true` | `professional/inspect/success.json` |
| failed_check | `inspectLabel` 200, expiry mismatch, needs review | `professional/inspect/failed_check.json` |

### D5. Evidence

| State | Endpoint | Mock |
|---|---|---|
| success | `searchEvidence` (module device, default hybrid RRF) | `professional/evidence/success.json` |
| empty | `searchEvidence`, zero hits | `professional/evidence/empty.json` |
| success | `askProfessional`, cited answer | `professional/ask/success.json` |
| abstained (out of scope) | `askProfessional` | `professional/ask/abstained_out_of_scope.json` |
| abstained (needs human check, with quotes) | `askProfessional` | `professional/ask/abstained_needs_human_check.json` |

### D6. Changes ("Change impact", mockup panel 4)
Proposed change, affected items with suggestions, current against draft preview, timeline Draft, Checked, Reviewed, Published.

| State | Endpoint | Mock |
|---|---|---|
| success (assessment) | `assessChange` 201 | `professional/changes/assess_success.json` |
| success (confirmed checklist) | `confirmChange` 200, every item confirmed or dismissed | `professional/changes/confirm_success.json` |
| rules (assessment, barcode waits for confirmation) | `assessChange` 201 with `parser: rules` | `professional/changes/assess_rules.json` |
| needs_review (assessment) | `assessChange` with a NEEDS_HUMAN_REVIEW reason | `professional/changes/assess_needs_review.json` |
| success (affected list) | `listAffectedLabels` | `professional/changes/affected_success.json` |
| loading (generate) | `generateArtwork` 202, then `getJob` | `professional/changes/generate_loading.json` |
| needs_review (identifier) | `generateArtwork` 409 NeedsInput | `professional/changes/generate_needs_input.json` |
| success (draft) | `getArtwork` | `professional/changes/generated_success.json` |
| returned | `getChange`, status derived `draft` from a return | `professional/changes/change_returned.json` |
| rejected | `getChange`, `closed: true` | `professional/changes/change_rejected.json` |

### D7. Review and approval

| State | Endpoint | Mock |
|---|---|---|
| success (re-check) | `recheckArtwork` 200, `passed: true` | `professional/review/recheck_success.json` |
| failed_check (re-check) | `recheckArtwork` 200, text overflow | `professional/review/recheck_failed_check.json` |
| empty | `listReviews`, zero items | `professional/review/empty.json` |
| approved | `reviewArtwork` 201, approve with `check_id` | `professional/review/approved.json` |
| returned | `reviewArtwork` 201, return with comment | `professional/review/returned.json` |
| failed (self approval) | `reviewArtwork` 403 | `professional/review/self_approval_forbidden.json` |

### D8. Export (download)

| State | Endpoint | Mock |
|---|---|---|
| success (draft) | `getExports` on an unreviewed version: DRAFT watermark, no QR | `professional/export/draft.json` |
| approved | `getExports` on a published version: PDF, SVG, report, QR | `professional/export/approved.json` |
| success (published) | `publishVersion` 201, page pinned to the version | `professional/export/publish_success.json` |

### D9. History

| State | Endpoint | Mock |
|---|---|---|
| success (audit) | `getProductHistory` | `professional/history/success.json` |
| success (versions) | `listLabelVersions` | `professional/history/label_versions.json` |
| empty | `getProductHistory`, zero events | `professional/history/empty.json` |

### D10. Print verification

| State | Endpoint | Mock |
|---|---|---|
| empty | `listPrintVerifications`, zero items | `professional/print_verify/empty.json` |
| loading | `verifyPrint` 202, then `getJob` | `professional/print_verify/loading.json` |
| success | `getPrintVerification`, `match` | `professional/print_verify/success.json` |
| failed_check | `getPrintVerification`, `mismatch` with boxes | `professional/print_verify/failed_check.json` |
| needs_review | `getPrintVerification`, `rescan_needed` (glare) | `professional/print_verify/needs_review.json` |

## Coverage check

Each required state appears at least once: empty (P2, D1, D5, D7, D9, D10), loading (P1, D3, D4, D6, D10), success (all), failed_check (D2, D4, D7, D10), needs_review (P2, D4, D6, D10), approved (D7, D8), abstained (P3, all four reasons).

## Assumptions

1. The idle "empty" state of the scan screens needs no API call, so it has no mock.
2. "Needs review" for public product matching means several candidates, so the user must pick. The match score alone never decides for the user.
3. `failed` (the job itself broke) is an extra state beyond the brief's list, because the polling design needs it.
4. Mock names are fixed here. Ishanvi and the UI build against these paths, and renaming one means updating `index.json` and this table.
5. Screen numbering (P1 to P3, D1 to D10) is mine. PRODUCT_SPEC lists six screen groups, and this table splits them where states differ.
