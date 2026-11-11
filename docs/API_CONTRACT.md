# API contract (draft, Pari finalises on Day 5)

All bodies are JSON and follow the Pydantic models in `src/common/schemas.py` (plus the template spec in `docs/GENERATION.md`). Ishanvi's mock files in `ui/mock/` mirror these responses exactly.

| Endpoint | Request | Response |
|---|---|---|
| `POST /products` | product fields | product record |
| `GET /products`, `GET /products/{id}` | none | product record(s) with label versions |
| `POST /products/{id}/template` | artwork file, slot list | template spec |
| `POST /analyze` | image or PDF, module, optional product id | LabelExtraction, matched product candidates, flags with evidence |
| `POST /changes` | product id, change text or structured field edit | proposed structured change, affected items, evidence, checklist |
| `POST /changes/{id}/confirm` | confirmed items | draft revision (SVG url, PDF url, barcode decision, change log, self-check result, layout problems) |
| `POST /reviews` | change or label id, decision (approve or return), comment | review record, new status |
| `GET /labels/{id}/package` | none | PDF at physical size, editable template, inspection report |
| `POST /verify-print` | photo, approved label id | VerificationResult (mismatches with boxes, or clearer scan requested) |
| `POST /chat` | question, product id | answer with source links, or refusal |
| `GET /reports/{id}` | none | PDF |

Status values for a change: draft, checked, reviewed, published.
Every flag has: kind, severity, message, observed, expected, evidence chunk ids, confidence, needs_human.
