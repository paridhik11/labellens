# Professional page (ui/pro): API map

Every operation the new page `ui/pro/` calls. Nothing else is called. Sources: `docs/contracts/openapi.yaml` (line of the `operationId`), the proven call sequence in `scripts/demo_flow.py` and `scripts/demo_e2e.py` (line of the call), and the role checks in `src/api/routes.py` (the `writer` dependency, line 132, lets an editor or admin through and answers 403 `role_forbidden` to a reviewer).

Common to every request:

- Header `X-User-Id`: `usr_demo_editor` or `usr_demo_reviewer` (the page's Editor / Reviewer switch), set the same way as `ui/js/api.js` (`request`, line 20) and `demo_flow.Api.call` (line 52). `usr_demo_admin` is never used.
- Base URL: the origin the page is served from (`scripts/run_demo.py` mounts `ui/` at `/ui` on the API server).
- Errors: the body is the contract `Error` (`openapi.yaml` line 1299): `{error, message, details?}`. The page shows `error: message` and a Retry button.
- A response with the header `X-Mock: true` is shown as an error, never as data.
- Slow operations answer 202 with a `Job` (`openapi.yaml` line 1335). The page polls `GET /jobs/{job_id}` every 1.5 s until `state` is `done` or `failed` (limit 300 s), then reads `result_url`. `demo_flow.Api.wait` (line 66) does the same every 1 s.

## Operations

| # | Operation (openapi line) | Method and path | Request | Response fields the page uses | Role | Success | Proven in |
|---|---|---|---|---|---|---|---|
| 1 | getHealth (30) | GET /health | none, no header | `status` | anyone | 200 | demo_e2e.py 41 |
| 2 | getCurrentUser (47) | GET /me | header only | `user_id`, `name`, `role` | any demo user | 200 | demo_e2e.py 42 |
| 3 | getJob (64) | GET /jobs/{job_id} | none | `job_id`, `kind`, `state`, `progress`, `message`, `result_url`, `error` | anyone | 200 | demo_flow.py 69 |
| 4 | listProducts (85) | GET /products | none | `items[].product.product_id`, `.product.current_version`, `.record` (`name`, `model`, `manufacturer`, `version`, `extra`), `.label_count`, `.open_findings` | any demo user | 200 | run_demo.py 196 |
| 5 | registerProduct (96) | POST /products | JSON `ProductCreate` (line 1398): `name`, `model`, `manufacturer`, `manufacturer_address`, `udi_di`, `sterilization`, `storage`, `extra` {`lot`, `expiry`, `serial`}, `intended_market` | `product.product_id`, `record` | editor | 201 | demo_flow.py 175 |
| 6 | getProduct (116) | GET /products/{product_id} | none | `product`, `record`, `templates[]`, `labels[]` (latest `LabelVersion` of each family) | any demo user | 200 | contract only (read) |
| 7 | registerTemplate (156) | POST /products/{product_id}/templates | JSON `TemplateCreate` (line 1485): `size_mm`, `background: null`, `slots` | `template_id`, `version` | editor | 201 | demo_flow.py 178 |
| 8 | getProductHistory (216) | GET /products/{product_id}/history | none | `items[]`: `at`, `user_id`, `action`, `entity_type`, `entity_id` | any demo user | 200 | contract only (read) |
| 9 | uploadScan (233) | POST /scans | multipart: `file`, `source` (`upload` or `camera`), `product_id` | 202 `Job` with `result_url` `/scans/{scan_id}` | editor | 202 | demo_flow.py 189 |
| 10 | getScan (260) | GET /scans/{scan_id} (the job's `result_url`) | none | `state`, `label_id`, `version_id`, `error` | any demo user | 200 | demo_flow.py 192 |
| 11 | listLabelVersions (279) | GET /labels/{label_id}/versions | none | `versions[]`: `version_id`, `artwork_version`, `kind`, `status`, `draft_watermark`, `template_id`, `created_by`, `created_at`, `parent_version_id` | any demo user | 200 | contract only (read) |
| 12 | getLabelVersion (298) | GET /label-versions/{version_id} | none | `artwork_version`, `kind`, `status` | any demo user | 200 | contract only (read) |
| 13 | getExtraction (314) | GET /label-versions/{version_id}/extraction | none | `fields`, `unclear_fields`, `warnings`, `barcodes[]` (`type`, `raw`, `parsed`), `ocr_blocks[]`, `confirmed` | any demo user | 200 | demo_flow.py 196 |
| 14 | confirmExtraction (330) | POST /label-versions/{version_id}/extraction/confirm | JSON `ExtractionConfirm` (line 1625): `fields` | `fields`, `confirmed`, `confirmed_by` | editor | 200 | demo_flow.py 207 |
| 15 | inspectLabel (354) | POST /label-versions/{version_id}/inspect | no body (as demo_flow) | 200 `CheckResult`, or 202 `Job` whose `result_url` is `/check-results/{check_id}` | any demo user | 200 or 202 | demo_flow.py 214 |
| 16 | getCheckResult (387) | GET /check-results/{check_id} (a job's `result_url`) | none | `CheckResult` (line 1686): `check_id`, `kind`, `passed`, `critical_count`, `review_count`, `info_count`, `needs_human_count`, `findings[]` (`rule_id`, `kind`, `severity`, `message`, `field`, `observed`, `expected`, `needs_human`, `citations[]`), `coverage[]` (`rule_id`, `outcome`, `reason`), `retrieval_config`, `disclaimer` | any demo user | 200 | demo_flow.py 216 |
| 17 | searchEvidence (406) | POST /search | JSON `SearchRequest` (line 1729): `query`, `module: "device"`, `k: 10` (as `ui/js/api.js` line 117). Step 29: only used by "Show more passages" (after /ask has passed the gate) | `retrieval.method`, `hits[]` (`rank`, `doc_id`, `score`, `text`), `citations[]` | anyone | 200 | ui/js/api.js 117 (D5 screen) |
| 18 | askProfessional (1153) | POST /ask (extractive, no `mode`) | JSON `question` | answered: `answer`, `sources[]`; abstained: `reason`, `message`, `score_name`, `score`, `threshold`, `sources[]` | anyone | 200 | run_demo.py 189, ui/js/api.js 124 |
| 19 | assessChange (428) | POST /changes | JSON `ChangeCreate` (line 1769): `product_id`, `edits: [{field, new_value}]` | `change` (`change_id`, `field`, `old_value`, `new_value`, `parse_state`), `parser`, `affected[]` (`impact_id`, `item_kind`, `title`, `description`, `reason`, `suggestion`, `needs_human`, `rule_ids`, `evidence_chunk_ids`, `barcode_decision`), `citations[]`, `needs_human_review`, `unassessed_edits[]`, `assessment_id` | editor | 201 (422 `no_change`, `duplicate_field`) | demo_flow.py 229 |
| 20 | confirmChange (507) | POST /changes/{change_id}/confirm | JSON `ChangeConfirm` (line 1862): `parse_confirmed: true`, `decisions: [{impact_id, user_decision}]` | same `ChangeAssessment` (now with `user_decision` and confirmed barcode decisions) | editor | 200 | demo_flow.py 249 |
| 21 | generateArtwork (557) | POST /changes/{change_id}/generate | JSON `label_id`, `test_data: true` | 202 `Job`, `result_url` `/artworks/{artwork_id}`; 409 `NeedsInput` or `Error`; 422 `CheckResult` or `Error` | editor | 202 | demo_flow.py 255 |
| 22 | getArtwork (617) | GET /artworks/{artwork_id} (the job's `result_url`) | none | `version_id`, `label_id`, `svg_url`, `pdf_url`, `size_mm`, `draft_watermark`, `test_data`, `barcode_decision` (`decision`, `old_payload`, `new_payload`, `symbology`, `reason`, `required_identifier`), `change_log[]`, `layout_problems[]`, `self_check_id`, `artifact_sha256`, `disclaimer` | any demo user | 200 | demo_flow.py 258 |
| 23 | recheckArtwork (639) | POST /label-versions/{version_id}/recheck | no body | 200 `CheckResult` (kind `self_check`) or 202 `Job` | any demo user | 200 or 202 | demo_flow.py 267 |
| 24 | listReviews (665) | GET /label-versions/{version_id}/reviews | none | `items[]`: `decision`, `user_id`, `reviewer_role`, `comment`, `artifact_sha256`, `check_id`, `resulting_status`, `decided_at` | any demo user | 200 | contract only (read) |
| 25 | reviewArtwork (679) | POST /label-versions/{version_id}/reviews | JSON `ReviewCreate` (line 1951): `decision` (`approve` or `return`), `artifact_sha256`, `check_id` (approve), `comment` | `review_id`, `decision`, `resulting_status` | reviewer | 201 (403 `role_forbidden`, `self_approval_forbidden`; 409 `hash_mismatch`, `check_not_passed`, `version_superseded`, `change_closed`, `change_not_confirmed`; 422 `check_required`, `comment_required`) | demo_flow.py 283 |
| 26 | getExports (782) | GET /label-versions/{version_id}/exports | none | `status`, `draft_watermark`, `pdf` (`url`, `mime`, `sha256`, `size_mm`), `svg`, `report` | any demo user | 200 (404 `no_artifacts` for an uploaded version) | demo_flow.py 307 |
| 27 | downloadArtifact (805) | GET /artifacts/{artifact_sha256} | none | file bytes, header `X-Draft-Mark` | any demo user | 200 | demo_flow.py 308 |
| 28 | listPrintVerifications (837) | GET /label-versions/{version_id}/print-verifications | none | `items[]` (`PrintVerification`) | any demo user | 200 | contract only (read) |
| 29 | verifyPrint (859) | POST /label-versions/{version_id}/print-verifications | multipart: `photo` (PNG or JPEG), `condition` (`clean_print_scan`, `phone_photo`, `blur`, `glare`) | 202 `Job`, `result_url` `/print-verifications/{verification_id}`; 409 `not_approved`, `rejected`, `version_superseded`, `no_reference` | any demo user | 202 | contract (CR-26); `ui/js/render-d10.js` |
| 30 | getPrintVerification (902) | GET /print-verifications/{verification_id} (the job's `result_url`) | none | `outcome` (`match`, `mismatch`, `rescan_needed`), `rescan_reason`, `mismatches[]`, `fields[]` (`field`, `expected`, `observed`, `status`), `barcode` (`expected_payload`, `match`), `quality` | any demo user | 200 | contract only (read) |
| 31 | listProductVersions | GET /products/{product_id}/versions | none | `versions[]`: the record fields, `extra` (lot, expiry, serial), `version`, `source_change_id`, `supersedes_version` | any demo user | 200 | Step 29: the page diffs two record versions to write "lot LOT1 -> LOT2" in Label versions and Activity history |
| 32 | getChange | GET /changes/{change_id} | none | `field`, `old_value`, `new_value`, `status` | any demo user | 200 | Step 29: the "Change requested" line of Activity history |
| 33 | getCheckResult | GET /check-results/{check_id} | none | the CheckResult of a saved check | any demo user | 200 | Step 30: after a reload the page reads the newest saved check of the current version (ids come from the history) |
| 34 | askProfessional (mode=ai) | POST /ask?mode=ai, then GET /jobs/{job_id} | JSON `question` | 202 `Job` of kind `ask`; the done job carries `result` (`answer`, `model`, `model_used`, `latency_s`, `fallback_reason`) | anyone | 202 | Step 30: "Ask with AI (optional)" in Evidence (CR-21, `docs/AI_ANSWER.md`) |
| 35 | searchEvidence (method override) | POST /search with `retrieval.method` bm25, tfidf, dense, hybrid_rrf or e5b, `k: 5` | JSON | `hits[]`, `citations[]` | anyone | 200 | Step 30: the Retrieval lab runs one query through the five systems |

Rows marked "contract only (read)" are plain GET reads of objects the proven sequence creates; the page uses them to show state after a reload. All 35 rows are in `REAL_OPERATIONS` (`src/api/routes.py` line 70) or are `getHealth`.

## Static files (not API operations)

| Path | What it is | Why |
|---|---|---|
| GET /ui/pro/sample/golden_label.pdf | Byte-identical copy of `golden/golden_label.pdf` (sha256 `764a23f9...9835`, the renderer's deterministic output for `demo_flow.GOLDEN`, marked DRAFT and TEST DATA) | The "Use sample Golden Pump label" button uploads it through uploadScan. The browser cannot read `golden/` (not served, git-ignored). `ui/tools/pro_e2e.cjs` checks the copy is byte-identical to the file `ui/tools/golden_setup.py` renders. |
| GET /ui/pro/sample/test_device.json | Byte-identical copy of `src/gen/templates/test_device.json` | The template registered for a new product, exactly as `demo_flow.register_golden` (line 178) sends it. `src/` is not served. `pro_e2e.cjs` checks it is byte-identical. |

## Not used

publishVersion, getTemplate, listAffectedLabels, every public operation. No endpoint is called that is not in the table above.
