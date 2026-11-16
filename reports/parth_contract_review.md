# Parth: technical contract review

Update 2026-11-16: Pari accepted CR-2,3,4,5,9,10,11. Acceptance is recorded in docs/contracts/SCHEMA_CHANGE_REQUESTS.md. The technical conditions below remain; locked schemas were not edited.

| Request | Recommendation | Reason and condition |
|---|---|---|
| CR-2 | YES | Explicit templates and slots match the implemented millimetre geometry. Keep named slot IDs and supported limits. |
| CR-3 | YES | Immutable versions are needed. New revisions must not inherit approval. |
| CR-4 | YES | Keep extraction and human confirmations distinct. Missing confidence must not become confirmed data. |
| CR-5 | YES | A passed check must bind to the exact version and artifact fingerprint. Unrun OCR/symbol checks must remain visible. |
| CR-9 | YES | KEEP, REGENERATE and NEEDS_INPUT are implemented. Map legacy manifest names explicitly rather than silently reusing incompatible hashes. |
| CR-10 | YES | Reviewer authorization, role, exact artifact hash and passed check_id are enforced locally. Authentication remains the application's responsibility. |
| CR-11 | YES | Return per-field evidence and confidence, plus an uncertain/review state for unreadable fields. Never turn uncertain evidence into a positive match. |

No changes were made to src/common, src/ir, src/api, ui or docs/contracts. Pari owns app integration and step-24b snapshot mapping. No real reviewer approval or publication was issued.

Deferred CV note: ten clear online photos have only LLM-labelled references. Original exact extraction was name 1/10, lot 0/10, expiry 0/10; the frozen photo fix gives 1/10,7/10,3/10. Names and expiry remain weak. The human three-photo spot-check is deferred by Parth and NOT_RUN. Real-symbol accuracy and real approved-print accuracy are not established.
