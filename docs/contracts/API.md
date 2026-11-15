# API (contract, Step 19c)

The machine-readable contract is [`openapi.yaml`](openapi.yaml) (OpenAPI 3.1, JSON Schema 2020-12). This page explains it for people. If the two disagree, `openapi.yaml` wins and this page gets fixed. Nothing here is implemented yet: `src/api/main.py` only serves `GET /health`.

Entities and field meanings are in [`DATA_MODEL.md`](DATA_MODEL.md). Template and barcode rules are in [`TEMPLATE_SPEC.md`](TEMPLATE_SPEC.md). Shapes missing from `src/common/schemas.py` are listed in [`SCHEMA_CHANGE_REQUESTS.md`](SCHEMA_CHANGE_REQUESTS.md).

## Conventions

- **JSON everywhere**, except file uploads (`multipart/form-data`) and the files behind export URLs (PDF, SVG).
- **Errors** use one shape: `{error, message, details?}`, where `error` is a short code such as `not_found`, `hash_mismatch` or `needs_input`.
- **Long work returns 202 and a Job.** Scans, inspections, generation and re-checks may answer `202` with `{job_id, kind, state, progress}`. The UI polls `GET /jobs/{job_id}` and shows its loading state until `state` is `done` or `failed`. When `done`, `result_url` says where to fetch the result.
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
| `POST /scans` | uploadScan | Upload a PDF or image, or a camera capture | 202 Scan | 422 |
| `GET /scans/{scan_id}` | getScan | Scan state; `label_id` and `version_id` once done | 200 Scan | 404 |
| `GET /labels/{label_id}/versions` | listLabelVersions | L1, L2, L3 of one label family | 200 LabelVersionList | 404 |
| `GET /label-versions/{version_id}` | getLabelVersion | One version with derived status | 200 LabelVersion | 404 |
| `GET /label-versions/{version_id}/extraction` | getExtraction | Text, barcodes, symbols, unclear fields | 200 Extraction | 404 |
| `POST /label-versions/{version_id}/extraction/confirm` | confirmExtraction | "Confirm extraction" with corrections | 200 Extraction | |
| `POST /label-versions/{version_id}/inspect` | inspectLabel | Compare with the record and retrieved requirements | 200 CheckResult (kind `inspection`) | 202 Job |
| `POST /search` | searchEvidence | Evidence retrieval for one module | 200 SearchResponse | 422 |
| `POST /changes` | assessChange | Parse a change, list affected items and evidence | 201 ChangeAssessment | 422 |
| `GET /changes/{change_id}` | getChange | A change with derived status | 200 ChangeRequest | 404 |
| `POST /changes/{change_id}/confirm` | confirmChange | Confirm the parse and the checklist | 200 ChangeAssessment | |
| `GET /changes/{change_id}/affected` | listAffectedLabels | Affected labels and fields | 200 AffectedLabelList | |
| `POST /changes/{change_id}/generate` | generateArtwork | Fill the template, render a DRAFT | 201 GeneratedArtwork | 202 Job, 409 NeedsInput, 422 CheckResult |
| `POST /label-versions/{version_id}/recheck` | recheckArtwork | Closed-loop self-check and layout checks | 200 CheckResult (kind `self_check`) | 202 Job |
| `GET /label-versions/{version_id}/reviews` | listReviews | Review history of a version | 200 ReviewList | |
| `POST /label-versions/{version_id}/reviews` | reviewArtwork | Approve, return or reject | 201 Review | 403, 409 |
| `POST /label-versions/{version_id}/publish` | publishVersion | Publish an approved version | 201 PublishedPage | 409 |
| `GET /label-versions/{version_id}/exports` | getExports | PDF at physical size, editable SVG, report, QR | 200 ExportPackage | 404 |
| `GET /label-versions/{version_id}/print-verifications` | listPrintVerifications | Past print checks | 200 | |
| `POST /label-versions/{version_id}/print-verifications` | verifyPrint | Compare a print photo with the approved version | 201 PrintVerification | 409 not approved |

### Public medicine mode (tag `public`)

| Method and path | operationId | Purpose | Success | Other responses |
|---|---|---|---|---|
| `POST /public/scans` | publicScan | Scan packaging, find reference label candidates | 200 PublicMatchResult | 202 Job |
| `POST /public/ask` | askPublic | Ask about the matched label | 200 AnswerResponse (answer or abstain) | |
| `POST /search` with `module: medicine` | searchEvidence | Shared search endpoint, medicine data only | 200 SearchResponse | |

### Common

| Method and path | operationId | Purpose |
|---|---|---|
| `GET /health` | getHealth | Liveness, already implemented |
| `GET /jobs/{job_id}` | getJob | Poll a long job; drives every loading state |

## Key rules, with examples

### Search options

`SearchRequest.retrieval` is optional. Leaving it out means plain hybrid RRF: BM25 and dense rankings fused by reciprocal rank fusion (`src/ir/hybrid.py`). Hybrid ranked first under both graders in Step 13. In Step 14 its gain over BM25 was not significant at chunk level. Four optional flags exist for experiments, and all default to `false`. `stem` maps to the BM25 `stem` option and `prefix` to the dense `query_prefix` (Step 15a):

```json
{"query": "expiration date format on device label", "module": "device", "k": 10,
 "retrieval": {"method": "hybrid_rrf", "stem": false, "prefix": false, "rerank": false, "expansion": false}}
```

`method` may also be `bm25`, `tfidf` or `dense` for comparisons. The response echoes the config it used, so a result can always be traced to its settings.

### Barcode decision and 409 needs_input

`generateArtwork` applies the TEMPLATE_SPEC rule. `KEEP` and `REGENERATE` return `201` with the decision inside `barcode_decision`. If an identifier is missing or an encoded change is unconfirmed, nothing is rendered: the server raises `IdentifierRequired` internally and returns `409`:

```json
{"error": "needs_input", "message": "A new UDI-DI is required for this change.",
 "barcode_decision": {"decision": "NEEDS_INPUT", "old_payload": "(01)00000000000000(17)281231(10)LOT001(21)SN001",
                      "new_payload": "", "symbology": "GS1_DataMatrix", "reason": "Model change needs a new UDI-DI",
                      "required_identifier": "udi_di"},
 "task": {"task_id": "tsk_0001", "title": "enter allocated identifier"}}
```

### Approval

`reviewArtwork` with `decision: approve` must send `check_id` (a CheckResult with `passed: true` for the same `version_id` and `artifact_sha256`) and the exact `artifact_sha256`. A mismatch returns `409 hash_mismatch` or `409 check_not_passed`. `return` and `reject` need a `comment`, and the resulting status is `draft`.

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

`score_name` is a free string (for example `hybrid_top_score`, the Step 16 primary score) so the score can be swapped later without changing the API. `score` and `threshold` are `null` when a scope rule, not a score, made the decision. The banner "Authenticity not verified. Based on a reference label match." is always present.

The public corpus is 21 CFR Parts 201, 208 and 211 only. The reference label corpus (DailyMed or openFDA) is not built yet.

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
