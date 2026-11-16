# API (contract, Step 19c)

The machine-readable contract is [`openapi.yaml`](openapi.yaml) (OpenAPI 3.1, JSON Schema 2020-12). This page explains it for people. If the two disagree, `openapi.yaml` wins and this page gets fixed. Step 20 implements part of it: the operations marked real in "Implementation status" below run against SQLite, and every other operation serves its mock JSON with the header `X-Mock: true`.

Entities and field meanings are in [`DATA_MODEL.md`](DATA_MODEL.md). Template and barcode rules are in [`TEMPLATE_SPEC.md`](TEMPLATE_SPEC.md). Shapes missing from `src/common/schemas.py` are listed in [`SCHEMA_CHANGE_REQUESTS.md`](SCHEMA_CHANGE_REQUESTS.md).

## Conventions

- **JSON everywhere**, except file uploads (`multipart/form-data`) and the files behind export URLs (PDF, SVG).
- **Errors** use one shape: `{error, message, details?}`, where `error` is a short code such as `not_found`, `hash_mismatch` or `needs_input`.
- **Long work returns 202 and a Job envelope.** Scan (`POST /scans`, `POST /public/scans`), generate (`POST /changes/{id}/generate`) and print verify (`POST /label-versions/{id}/print-verifications`) always answer `202` with `{job_id, kind, state, progress}`. Inspect and re-check answer `200` when the version already has a stored extraction (only the rules run) and `202` when the extraction must be computed first (Step 21). The UI polls `GET /jobs/{job_id}` and shows its loading state until `state` is `done` or `failed`. When `done`, `result_url` names the GET endpoint for the result (`/scans/{scan_id}`, `/artworks/{artwork_id}`, `/print-verifications/{verification_id}`, `/public/scans/{scan_id}`).
- **Users.** A minimal User (`user_id`, `name`, `role`: editor, reviewer or admin) is identified by the `X-User-Id` header, a stub with no login flow. `GET /me` returns it. Public endpoints, `/health`, `/jobs` and `/search` work without the header.
- **Versions are pinned.** Anything about one artwork uses `version_id`, the id of one immutable LabelVersion. `label_id` is the label family. Reports and published pages keep their `version_id` forever.
- **Status is derived, never sent.** No endpoint accepts a `status` field. The server computes it from the record trail (DATA_MODEL.md, "Status derivation") and returns `latest_review_id` so the UI can explain it.
- **Modules never mix.** `/search` requires `module` (`device` or `medicine`). Public endpoints live under `/public` and only use medicine data.
- **Drafts are marked.** Generated artwork has `draft_watermark: true` and the fixed disclaimer "Draft generated for review. Not a compliance determination." until an approval exists.

## Endpoints

### Professional workspace (tag `device`)

| Method and path | operationId | Purpose | Success | Other responses |
|---|---|---|---|---|
| `GET /products` | listProducts | Products screen list | 200 ProductList (may be empty) | |
| `POST /products` | registerProduct | Register a product, creates version 1 | 201 ProductDetail | 422 |
| `GET /products/{product_id}` | getProduct | Product, current record, templates, latest label of each family | 200 ProductDetail | 404 |
| `GET /products/{product_id}/versions` | listProductVersions | All product record versions | 200 | 404 |
| `POST /products/{product_id}/templates` | registerTemplate | Register a template or a new template version | 201 LabelTemplate | 422 CheckResult with layout findings |
| `GET /templates/{template_id}?version=` | getTemplate | One template version, latest by default | 200 LabelTemplate | 404 |
| `GET /products/{product_id}/history` | getProductHistory | Audit trail, newest first | 200 AuditEventList | |
| `POST /scans` | uploadScan | Upload a PDF or image, or a camera capture | 202 Job | 422 |
| `GET /scans/{scan_id}` | getScan | Scan state; `label_id` and `version_id` once done | 200 Scan | 404 |
| `GET /labels/{label_id}/versions` | listLabelVersions | L1, L2, L3 of one label family | 200 LabelVersionList | 404 |
| `GET /label-versions/{version_id}` | getLabelVersion | One version with derived status | 200 LabelVersion | 404 |
| `GET /label-versions/{version_id}/extraction` | getExtraction | Text, barcodes, symbols, unclear fields | 200 Extraction | 404 |
| `POST /label-versions/{version_id}/extraction/confirm` | confirmExtraction | "Confirm extraction" with corrections | 200 Extraction | |
| `POST /label-versions/{version_id}/inspect` | inspectLabel | Compare with the record and retrieved requirements | 200 CheckResult (kind `inspection`) | 202 Job, 404, 422 |
| `GET /check-results/{check_id}` | getCheckResult | One stored check result (the `result_url` of a finished inspect or re-check job) | 200 CheckResult | 404 |
| `POST /search` | searchEvidence | Evidence retrieval for one module | 200 SearchResponse | 422 |
| `POST /changes` | assessChange | Parse a change, list affected items and evidence | 201 ChangeAssessment | 422 |
| `GET /changes/{change_id}` | getChange | A change with derived status | 200 ChangeRequest | 404 |
| `POST /changes/{change_id}/confirm` | confirmChange | Confirm the parse and the checklist | 200 ChangeAssessment | |
| `GET /changes/{change_id}/affected` | listAffectedLabels | Affected labels and fields | 200 AffectedLabelList | |
| `POST /changes/{change_id}/generate` | generateArtwork | Fill the template, render a DRAFT | 202 Job | 409 NeedsInput or change_closed, 422 CheckResult |
| `GET /artworks/{artwork_id}` | getArtwork | Result of a generate job | 200 GeneratedArtwork | 404 |
| `POST /label-versions/{version_id}/recheck` | recheckArtwork | Closed-loop self-check and layout checks | 200 CheckResult (kind `self_check`) | 202 Job, 404, 409 not_generated |
| `GET /label-versions/{version_id}/reviews` | listReviews | Review history of a version | 200 ReviewList | |
| `POST /label-versions/{version_id}/reviews` | reviewArtwork | Approve, return or reject | 201 Review | 403 role_forbidden or self_approval_forbidden, 409 |
| `POST /label-versions/{version_id}/publish` | publishVersion | Publish an approved version | 201 PublishedPage | 409 |
| `GET /label-versions/{version_id}/exports` | getExports | PDF at physical size, editable SVG, report, QR | 200 ExportPackage | 404 |
| `GET /label-versions/{version_id}/print-verifications` | listPrintVerifications | Past print checks | 200 | |
| `POST /label-versions/{version_id}/print-verifications` | verifyPrint | Compare a print photo with the approved version | 202 Job | 409 not approved |
| `GET /print-verifications/{verification_id}` | getPrintVerification | Result of a print verify job | 200 PrintVerification | 404 |

### Public medicine mode (tag `public`)

| Method and path | operationId | Purpose | Success | Other responses |
|---|---|---|---|---|
| `POST /public/scans` | publicScan | Scan packaging, find reference label candidates | 202 Job | |
| `GET /public/scans/{scan_id}` | getPublicScan | Match candidates (picker when several) | 200 PublicMatchResult | 404 |
| `POST /public/ask` | askPublic | Ask about the matched label. `?mode=ai` starts a job (CR-21) | 200 AnswerResponse (answer or abstain); 202 Job (kind `ask`) with `mode=ai` | 422, 503 |
| `POST /ask` | askProfessional | Ask about the device regulations (CR-19). `?mode=ai` as above | 200 ProfessionalAnswerResponse; 202 Job (kind `ask`) with `mode=ai` | 422, 503 |
| `POST /search` with `module: medicine` | searchEvidence | Shared search endpoint, medicine data only | 200 SearchResponse | |

### Common

| Method and path | operationId | Purpose |
|---|---|---|
| `GET /health` | getHealth | Liveness, already implemented |
| `GET /jobs/{job_id}` | getJob | Poll a long job; drives every loading state |
| `GET /me` | getCurrentUser | The user named by the `X-User-Id` header stub |

## Key rules, with examples

### Search options

`SearchRequest.retrieval` is optional. Leaving it out means plain hybrid RRF: BM25 and dense rankings fused by reciprocal rank fusion (`src/ir/hybrid.py`). Hybrid ranked first under both graders in Step 13. In Step 14 its gain over BM25 was not significant at chunk level. Four optional flags exist for experiments, and all default to `false`. `stem` maps to the BM25 `stem` option and `prefix` to the dense `query_prefix` (Step 15a):

```json
{"query": "expiration date format on device label", "module": "device", "k": 10,
 "retrieval": {"method": "hybrid_rrf", "stem": false, "prefix": false, "rerank": false, "expansion": false}}
```

`method` may also be `bm25`, `tfidf` or `dense` for comparisons. The response echoes the config it used, so a result can always be traced to its settings.

### Barcode decision and 409 needs_input

`generateArtwork` applies the TEMPLATE_SPEC rule. `KEEP` and `REGENERATE` start a job, and the finished GeneratedArtwork carries the decision inside `barcode_decision`. If an identifier is missing or an encoded change is unconfirmed, nothing is rendered: the server raises `IdentifierRequired` internally and returns `409`:

```json
{"error": "needs_input", "message": "A new UDI-DI is required for this change.",
 "barcode_decision": {"decision": "NEEDS_INPUT", "old_payload": "(01)00000000000000(17)281231(10)LOT001(21)SN001",
                      "new_payload": "", "symbology": "GS1_DataMatrix", "reason": "Model change needs a new UDI-DI",
                      "required_identifier": "udi_di"},
 "task": {"task_id": "tsk_0001", "title": "enter allocated identifier"}}
```

### Approval

`reviewArtwork` with `decision: approve` must send `check_id` (a CheckResult with `passed: true` for the same `version_id` and `artifact_sha256`) and the exact `artifact_sha256`. A mismatch returns `409 hash_mismatch` or `409 check_not_passed`. `return` and `reject` need a `comment`, and the resulting status is `draft`.

Further rules, all enforced by the server:

| Rule | Effect |
|---|---|
| Only `reviewer` or `admin` may review | Otherwise `403 role_forbidden` |
| The submitter of a change cannot approve it | `approve` by the change's `created_by` gives `403 self_approval_forbidden`. That user may still return or reject. |
| A new artwork version after approval voids the approval | Generating again creates a new version and a new hash. The old approval no longer counts, and the change needs review again (derived status `draft`, then `checked` once its self-check passes). Reviewing or publishing the old version through this change gives `409 version_superseded`. |
| Reject is terminal | `closed` becomes `true`. Generate, review and publish on the change give `409 change_closed`. A new change is needed. |
| Return is not terminal | The editor can regenerate. |

"Currently approved" must be read from the change status (`status` is `reviewed`), never from a version's own status, because a newer version voids an earlier approval and the old version still shows as approved in its own record.

### The "returned" case

`openapi.yaml` has a `returned` example under `GET /changes/{change_id}` and under the `201` of `POST /label-versions/{version_id}/reviews`. The change shows `status: draft` with `latest_review_id: rev_0002`, and that Review has `decision: return`. The status is not stored. It is read off the latest Review.

### Public answers and abstention

`askPublic` returns exactly one of:

- **Answer:** `{abstained: false, answer, sources[], based_on, banner}`. `sources` has at least one Citation, and each citation has `source_type` `cfr` or `label_section`.
- **Abstain:** `{abstained: true, reason, score_name, score, threshold, message, banner}` with no answer text. `reason` is one of:

| reason | When |
|---|---|
| `no_evidence` | Retrieval found nothing relevant in the public corpus or the matched label. |
| `low_confidence` | The abstention score is below the threshold. |
| `out_of_scope` | Medical advice, dosing for a person, or anything outside 21 CFR 201, 208, 211 and the matched label. |
| `needs_human_check` | Evidence conflicts or the product match is uncertain. |

Step 23: an abstain with `reason: needs_human_check` may carry `sources`, verbatim passages (CR-18). They are shown when the language model is off or its answer failed verification. They are not an answer. Step 23 reports a score below the threshold as `needs_human_check` with `score_name: e5b_top_score`; `no_evidence` and `low_confidence` are not produced. `score_name` is a free string (for example `hybrid_top_score`, the Step 16 primary score) so the score can be swapped later without changing the API. `score` and `threshold` are `null` when a scope rule, not a score, made the decision. The banner "Authenticity not verified. Based on a reference label match." is always present.

The public corpus is 21 CFR Parts 201, 208 and 211 only. The reference label corpus (DailyMed or openFDA) is not built yet.

## Roles and error codes

The caller is the user named by the `X-User-Id` header. Reads need a known user. Writes check the role:

| Operation | Allowed roles | Otherwise |
|---|---|---|
| `registerProduct`, `registerTemplate`, `assessChange` | `editor`, `admin` | `403 role_forbidden` |
| `reviewArtwork` | `reviewer`, `admin` | `403 role_forbidden` |

Error codes (body `{error, message, details?}`):

| Code | Status | When |
|---|---|---|
| `unknown_user` | 401 | `X-User-Id` header missing or no such user |
| `role_forbidden` | 403 | The user's role may not do this |
| `self_approval_forbidden` | 403 | The submitter of a change tried to approve it |
| `not_found` | 404 | Unknown product, template, label, version, change, check result or job |
| `validation_error` | 422 | Request body has the wrong shape |
| `check_required` | 422 | Approve without a `check_id` |
| `comment_required` | 422 | Return or reject without a comment |
| `parser_not_implemented` | 422 | `POST /changes` with `raw_text` only. Send structured `edits`. |
| `artifact_hash_required` | 422 | Generated artwork without its `artifact_sha256` |
| `hash_mismatch` | 409 | `artifact_sha256` is not the version's hash |
| `check_not_passed` | 409 | `check_id` is missing, failed, or belongs to another version or hash |
| `version_superseded` | 409 | A newer artwork version exists for the change |
| `change_closed` | 409 | The change was rejected |
| `template_product_mismatch` | 409 | The `template_id` belongs to another product |
| `label_product_mismatch` | 409 | The `label_id` belongs to another product |
| `needs_input` | 409 | Generate needs an identifier (see above) |
| `not_generated` | 409 | `recheckArtwork` on a version that is not generated artwork with an `artifact_sha256` |

### Inspection and coverage (Step 21)

`inspectLabel` and `recheckArtwork` run the checker described in [`../CHECKER_SPEC.md`](../CHECKER_SPEC.md): rules decide, retrieval cites, no LLM. A `CheckResult` of kind `inspection` or `self_check` carries:

- `findings`: **only problems**. A rule that passed raises nothing.
- `coverage`: one entry per rule (`rule_id`, `outcome` of `pass`, `fail`, `needs_human`, `not_applicable` or `not_checked`, `reason`), so "no finding" is never mistaken for "checked and fine".
- `needs_human_count`: the number of coverage entries with outcome `needs_human`.
- `passed`: still zero critical findings. It can be `true` while `needs_human_count` is above 0 (for example while the symbol detector is untrusted, every label has two symbol outcomes that need a person), so show both numbers. Passed is never a compliance verdict.
- `retrieval_config`: the settings the citations were found with.

The first inspect of a version starts a job (the extraction is computed with the CV extractor in blind mode and stored in the append-only `extractions` table). The job's states are rows of the append-only `jobs` table. Later inspects of the same version answer `200` at once. A job that cannot finish ends in state `failed` with an `error` such as `extractor_unavailable` (CV libraries not installed on the server), `artwork_not_found` (no image for the version) or `check_failed`. Job ids this server issues look like `job_1a2b3c4d`, and an unknown id of that form is `404`. Any other id (the scan and generate jobs are still mocks) is answered with the mock job and the header `X-Mock`.

A generated version's artwork is an SVG. The checker reads the rendered `label.png` that the renderer writes next to it. `recheckArtwork` copies the version's `artifact_sha256` into the self-check, so the approval rules of Step 20 (passed check, same version, same hash) work on it. The layout half of the re-check (text overflow and the like) is produced when artwork is generated, which is not real yet, so a real self-check holds checker findings only.

`/search` is real: bm25, tfidf, dense or hybrid RRF over one module's chunks, with one citation per hit. `rerank` and `expansion` answer `422` because no reranker or query expansion exists in `src/ir`.

## Implementation status (Step 20 and 21)

| Operation | Status |
|---|---|
| `getHealth`, `getCurrentUser`, `listProducts`, `registerProduct`, `getProduct`, `listProductVersions`, `registerTemplate`, `getTemplate`, `getProductHistory`, `listLabelVersions`, `getLabelVersion`, `assessChange`, `getChange`, `listReviews`, `reviewArtwork`, `inspectLabel`, `recheckArtwork`, `getJob`, `getCheckResult`, `searchEvidence` | Real (SQLite, retrieval). |
| Every other operation | Mock JSON, response header `X-Mock: true`. `?mock_state=<state>` picks another mock of the same operation. |

Limits of the real operations (an older `data/api/labellens.db` gets the new `check_results` columns added on start; delete it to re-seed): `registerTemplate` validates the shape only, so the layout findings (`422 CheckResult`) are not produced yet. `assessChange` stores a structured change and answers `parser: not_implemented` with an empty `affected` list, `checklist_complete: false` and a `needs_human_review` message, so an unchecked change cannot be mistaken for a clean one. `listAffectedLabels` is a mock until an impact analysis exists.

## Mapping from the old draft

`docs/API_CONTRACT.md` (Day 5 draft) is superseded by this page:

| Old | New |
|---|---|
| `POST /analyze` | `POST /scans`, then `GET .../extraction` and `POST .../inspect` |
| `POST /changes/{id}/confirm` returning the draft | `POST /changes/{id}/confirm`, then `POST /changes/{id}/generate` |
| `POST /reviews` | `POST /label-versions/{version_id}/reviews` |
| `GET /labels/{id}/package`, `GET /reports/{id}` | `GET /label-versions/{version_id}/exports` |
| `POST /verify-print` | `POST /label-versions/{version_id}/print-verifications` |
| `POST /chat` | `POST /public/ask` |

## Assumptions

1. Paths and names are new proposals. No client code depends on the old draft yet.
2. A single JSON `exports` endpoint returns URLs for the binary files. Serving and signing those URLs is an implementation detail left out of this contract.
3. Authentication is not modelled yet. `403` on review is the only place authorization appears. Login is a later step.
4. `score` and `threshold` may be `null` for rule-based `out_of_scope` decisions. This is my reading of "include score_name, score, threshold"; tell me if you want them always numeric.
5. The abstention score is provisional. Step 16 measured hybrid top score AUROC 0.985 [0.930, 1.000] on 20 LLM-graded medicine queries over CFR chunks only. Public label-based answers have no abstention validation.
6. The `rerank` and `expansion` flags describe planned experiments. No reranker or expansion module exists in `src/ir` yet, so a server may answer `422` for them until one does.
7. `/search` is shared by both modules but always filtered by `module`. This keeps one retrieval interface (`search(query, k)`) as AGENTS.md requires.
8. The all-zero sha256 in the review examples is a placeholder in documentation, not a real hash.
9. `X-User-Id` is trusted as given. It is a development stub, not security. Any real deployment needs a login and session before it is exposed.
10. Inspect and re-check may answer 200 or 202. Scan, generate and print verify always answer 202.

## Change assessment (Step 22, CR-18)

- `POST /changes` takes `edits` (structured, canonical field names or aliases) or `raw_text` (rules parser, English sentence shapes listed in `docs/CHANGE_SPEC.md`). Edits win if both are given. 201 `ChangeAssessment` with `parser: rules` or `llm` (the optional provider, off by default), `affected`, `citations`, `unassessed_edits`, `assessment_id`. `parser: not_implemented` when nothing could be assessed (only unknown or invalid edits): `affected` is empty because nothing was checked.
- Refusals: `422 parser_not_implemented` (text that cannot be parsed without guessing, with `details.status` and `details.issues`), `422 no_change` (new value equals the current value), `422 duplicate_field`.
- `GET /changes/{id}/affected` returns the stored items with current `user_decision`.
- `POST /changes/{id}/confirm` appends a confirmation. First confirmation also appends the confirmed assessment, so a barcode decision `NEEDS_INPUT` with `required_identifier: confirm_lot` becomes `REGENERATE` when nothing else blocks it. Errors: 409 `change_closed`, 409 `nothing_to_confirm`, 422 `parse_not_confirmed`, 422 `edits_not_supported`, 422 `unknown_impact`.
- `POST /label-versions/{id}/reviews` with `approve` returns `409 change_not_confirmed` when the change has an assessment nobody confirmed.
- A change with no stored assessment (older changes, the seed) keeps the mock for `affected` and `confirm` (`X-Mock: true`).
