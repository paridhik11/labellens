| Screen | State | Mock file | Result | Notes |
|---|---|---|---|---|
| D1 Products | empty | professional/products/empty.json | pass |  |
| D1 Products | success | professional/products/success.json | pass |  |
| D1 Products | success | professional/product_detail/success.json | pass |  |
| D2 Template setup | success | professional/template_setup/success.json | pass |  |
| D2 Template setup | failed_check | professional/template_setup/failed_check.json | pass |  |
| D3 Upload or scan | loading | professional/upload/loading.json | pass |  |
| D3 Upload or scan | failed | professional/upload/failed.json | pass |  |
| D3 Upload or scan | success | professional/upload/success.json | pass |  |
| D4 Inspect | success | professional/inspect/extraction_success.json | pass |  |
| D4 Inspect | needs_review | professional/inspect/extraction_needs_review.json | pass |  |
| D4 Inspect | loading | professional/inspect/loading.json | pass |  |
| D4 Inspect | success | professional/inspect/success.json | pass |  |
| D4 Inspect | failed_check | professional/inspect/failed_check.json | pass |  |
| D4 Inspect | success | professional/inspect/extraction_confirmed.json | pass |  |
| D5 Evidence | success | professional/evidence/success.json | pass |  |
| D5 Evidence | empty | professional/evidence/empty.json | pass |  |
| D5 Evidence | success | professional/ask/success.json | pass |  |
| D5 Evidence | abstained | professional/ask/abstained_out_of_scope.json | pass |  |
| D5 Evidence | abstained | professional/ask/abstained_needs_human_check.json | pass |  |
| D6 Changes | success | professional/changes/assess_success.json | pass |  |
| D6 Changes | needs_review | professional/changes/assess_needs_review.json | pass |  |
| D6 Changes | rules | professional/changes/assess_rules.json | pass |  |
| D6 Changes | success | professional/changes/affected_success.json | pass |  |
| D6 Changes | loading | professional/changes/generate_loading.json | pass |  |
| D6 Changes | needs_review | professional/changes/generate_needs_input.json | pass |  |
| D6 Changes | success | professional/changes/generated_success.json | pass |  |
| D6 Changes | returned | professional/changes/change_returned.json | pass |  |
| D6 Changes | rejected | professional/changes/change_rejected.json | pass |  |
| D6 Changes | success | professional/changes/confirm_success.json | pass |  |
| D7 Review | success | professional/review/recheck_success.json | pass |  |
| D7 Review | failed_check | professional/review/recheck_failed_check.json | pass |  |
| D7 Review | empty | professional/review/empty.json | pass |  |
| D7 Review | approved | professional/review/approved.json | pass |  |
| D7 Review | returned | professional/review/returned.json | pass |  |
| D7 Review | failed | professional/review/self_approval_forbidden.json | pass |  |
| D8 Export | success | professional/export/draft.json | pass |  |
| D8 Export | approved | professional/export/approved.json | pass |  |
| D8 Export | success | professional/export/publish_success.json | pass |  |
| D9 History | success | professional/history/success.json | pass |  |
| D9 History | empty | professional/history/empty.json | pass |  |
| D9 History | success | professional/history/label_versions.json | pass |  |
| D10 Print verification | empty | professional/print_verify/empty.json | pass |  |
| D10 Print verification | loading | professional/print_verify/loading.json | pass |  |
| D10 Print verification | success | professional/print_verify/success.json | pass |  |
| D10 Print verification | failed_check | professional/print_verify/failed_check.json | pass |  |
| D10 Print verification | needs_review | professional/print_verify/needs_review.json | pass |  |
| P1 Scan and Understand | empty | idle | pass |  |
| P1 Scan and Understand | loading | public/scan/loading.json | pass |  |
| P1 Scan and Understand | failed | public/scan/failed.json | pass |  |
| P2 Product information | success | public/product/success.json | pass |  |
| P2 Product information | needs_review | public/product/needs_review.json | pass |  |
| P2 Product information | empty | public/product/empty.json | pass |  |
| P3 Ask about this label | success | public/ask/success.json | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_out_of_scope.json | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_low_confidence.json | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_no_evidence.json | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_needs_human_check.json | pass |  |
| P3 Ask about this label | ai_accepted | public/ask/ai_accepted.json | pass |  |
| P3 Ask about this label | ai_done | public/ask/ai_job_done.json | pass |  |
| P3 Ask about this label | ai_fallback_timeout | public/ask/ai_job_fallback_timeout.json | pass |  |
| D5 Evidence | ai_accepted | professional/ask/ai_accepted.json | pass |  |
