| Screen | State | Mock file | Data source | Result | Notes |
|---|---|---|---|---|---|
| D1 Products | empty | professional/products/empty.json | api | pass |  |
| D1 Products | success | professional/products/success.json | api | pass |  |
| D1 Products | success | professional/product_detail/success.json | api | pass |  |
| D2 Template setup | success | professional/template_setup/success.json | x-mock | pass |  |
| D2 Template setup | failed_check | professional/template_setup/failed_check.json | x-mock | pass |  |
| D3 Upload or scan | loading | professional/upload/loading.json | x-mock | pass |  |
| D3 Upload or scan | failed | professional/upload/failed.json | x-mock | pass |  |
| D3 Upload or scan | success | professional/upload/success.json | x-mock | pass |  |
| D4 Inspect | success | professional/inspect/extraction_success.json | x-mock | pass |  |
| D4 Inspect | needs_review | professional/inspect/extraction_needs_review.json | x-mock | pass |  |
| D4 Inspect | loading | professional/inspect/loading.json | x-mock | pass |  |
| D4 Inspect | success | professional/inspect/success.json | x-mock | pass |  |
| D4 Inspect | failed_check | professional/inspect/failed_check.json | x-mock | pass |  |
| D4 Inspect | success | professional/inspect/extraction_confirmed.json | x-mock | pass |  |
| D5 Evidence | success | professional/evidence/success.json | x-mock | pass |  |
| D5 Evidence | empty | professional/evidence/empty.json | x-mock | pass |  |
| D5 Evidence | success | professional/ask/success.json | x-mock | pass |  |
| D5 Evidence | abstained | professional/ask/abstained_out_of_scope.json | x-mock | pass |  |
| D5 Evidence | abstained | professional/ask/abstained_needs_human_check.json | x-mock | pass |  |
| D6 Changes | success | professional/changes/assess_success.json | x-mock | pass |  |
| D6 Changes | needs_review | professional/changes/assess_needs_review.json | x-mock | pass |  |
| D6 Changes | rules | professional/changes/assess_rules.json | x-mock | pass |  |
| D6 Changes | success | professional/changes/affected_success.json | api | pass |  |
| D6 Changes | loading | professional/changes/generate_loading.json | x-mock | pass |  |
| D6 Changes | needs_review | professional/changes/generate_needs_input.json | x-mock | pass |  |
| D6 Changes | success | professional/changes/generated_success.json | x-mock | pass |  |
| D6 Changes | returned | professional/changes/change_returned.json | api | pass |  |
| D6 Changes | rejected | professional/changes/change_rejected.json | x-mock | pass |  |
| D6 Changes | success | professional/changes/confirm_success.json | x-mock | pass |  |
| D7 Review | success | professional/review/recheck_success.json | x-mock | pass |  |
| D7 Review | failed_check | professional/review/recheck_failed_check.json | x-mock | pass |  |
| D7 Review | empty | professional/review/empty.json | api | pass |  |
| D7 Review | approved | professional/review/approved.json | x-mock | pass |  |
| D7 Review | returned | professional/review/returned.json | x-mock | pass |  |
| D7 Review | failed | professional/review/self_approval_forbidden.json | x-mock | pass |  |
| D8 Export | success | professional/export/draft.json | x-mock | pass |  |
| D8 Export | approved | professional/export/approved.json | x-mock | pass |  |
| D8 Export | success | professional/export/publish_success.json | x-mock | pass |  |
| D9 History | success | professional/history/success.json | api | pass |  |
| D9 History | empty | professional/history/empty.json | x-mock | pass |  |
| D9 History | success | professional/history/label_versions.json | api | pass |  |
| D10 Print verification | empty | professional/print_verify/empty.json | api | pass |  |
| D10 Print verification | loading | professional/print_verify/loading.json | x-mock | pass |  |
| D10 Print verification | success | professional/print_verify/success.json | x-mock | pass |  |
| D10 Print verification | failed_check | professional/print_verify/failed_check.json | x-mock | pass |  |
| D10 Print verification | needs_review | professional/print_verify/needs_review.json | x-mock | pass |  |
| P1 Scan and Understand | empty | idle | x-mock | pass |  |
| P1 Scan and Understand | loading | public/scan/loading.json | x-mock | pass |  |
| P1 Scan and Understand | failed | public/scan/failed.json | x-mock | pass |  |
| P2 Product information | success | public/product/success.json | x-mock | pass |  |
| P2 Product information | needs_review | public/product/needs_review.json | x-mock | pass |  |
| P2 Product information | empty | public/product/empty.json | x-mock | pass |  |
| P2 Product information | live_candidates | public/live/search_candidates.json | x-mock | pass |  |
| P2 Product information | live_none | public/live/search_none.json | x-mock | pass |  |
| P2 Product information | live_offline | public/live/search_unavailable.json | x-mock | pass |  |
| P2 Product information | live_fetching | public/live/fetching.json | x-mock | pass |  |
| P2 Product information | live_fetch_failed | public/live/fetch_failed.json | x-mock | pass |  |
| P2 Product information | live_success | public/live/product.json | x-mock | pass |  |
| P3 Ask about this label | success | public/ask/success.json | x-mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_out_of_scope.json | x-mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_low_confidence.json | x-mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_no_evidence.json | x-mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_needs_human_check.json | x-mock | pass |  |
| P3 Ask about this label | ai_accepted | public/ask/ai_accepted.json | x-mock | pass |  |
| P3 Ask about this label | ai_done | public/ask/ai_job_done.json | x-mock | pass |  |
| P3 Ask about this label | ai_fallback_timeout | public/ask/ai_job_fallback_timeout.json | x-mock | pass |  |
| D5 Evidence | ai_accepted | professional/ask/ai_accepted.json | x-mock | pass |  |

| Click-through | Result | Notes |
|---|---|---|
| D6 confirm checklist button | pass |  |
| D6 generate draft button (mock) | pass |  |
| D9 audit and versions switch buttons | pass |  |
| D7 return needs a comment | pass |  |
| D7 approve is disabled when the re-check failed | pass |  |
| D7 draws each finding citation (section, title, quote) | pass |  |
| D8 download click | pass |  |
| D4 confirm button reaches a confirmed extraction (mock) | pass |  |
| D4 run inspection reaches the check result | pass |  |
| D4 unclear field is editable, confirmed field is not | pass |  |
| D5 ask click | pass |  |
