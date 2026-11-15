# Parth: technical contract review

These are implementation recommendations for Parth and Pari to review, not formal team approval or edits to the locked schemas.

| Request | Recommendation | Reason and condition |
|---|---|---|
| CR-2 | YES | Explicit templates and slots match the implemented millimetre geometry. Keep named slot IDs and supported limits. |
| CR-3 | YES | Immutable versions are needed. New revisions must not inherit approval. |
| CR-4 | YES | Keep extraction and human confirmations distinct. Missing confidence must not become confirmed data. |
| CR-5 | YES | A passed check must bind to the exact version and artifact fingerprint. Unrun OCR/symbol checks must remain visible. |
| CR-9 | YES | KEEP, REGENERATE and NEEDS_INPUT are implemented. Map legacy manifest names explicitly rather than silently reusing incompatible hashes. |
| CR-10 | YES | Reviewer authorization, role, exact artifact hash and passed check_id are enforced locally. Authentication remains the application's responsibility. |
| CR-11 | YES | Return per-field evidence and confidence, plus an uncertain/review state for unreadable fields. Never turn uncertain evidence into a positive match. |

No changes were made to src/common, src/ir, src/api, ui or docs/contracts. Pari still needs to accept the mappings and wire application APIs/storage. No real reviewer approval or publication was issued.

Deferred CV note: ten clear online photos have only LLM-labelled references. Exact extraction is name 1/10, lot 0/10, expiry 0/10. The human three-photo spot-check is deferred by Parth and NOT_RUN. Real-symbol accuracy and real approved-print accuracy are not established.
