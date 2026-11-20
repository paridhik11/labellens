| Screen | State | Mock file | Data source | Result | Notes |
|---|---|---|---|---|---|
| D1 Products | empty | professional/products/empty.json | mock | pass |  |
| D1 Products | success | professional/products/success.json | mock | pass |  |
| D1 Products | success | professional/product_detail/success.json | mock | pass |  |
| D2 Template setup | success | professional/template_setup/success.json | mock | pass |  |
| D2 Template setup | failed_check | professional/template_setup/failed_check.json | mock | pass |  |
| D3 Upload or scan | loading | professional/upload/loading.json | mock | pass |  |
| D3 Upload or scan | failed | professional/upload/failed.json | mock | pass |  |
| D3 Upload or scan | success | professional/upload/success.json | mock | pass |  |
| D4 Inspect | success | professional/inspect/extraction_success.json | mock | pass |  |
| D4 Inspect | needs_review | professional/inspect/extraction_needs_review.json | mock | pass |  |
| D4 Inspect | loading | professional/inspect/loading.json | mock | pass |  |
| D4 Inspect | success | professional/inspect/success.json | mock | pass |  |
| D4 Inspect | failed_check | professional/inspect/failed_check.json | mock | pass |  |
| D4 Inspect | success | professional/inspect/extraction_confirmed.json | mock | pass |  |
| D5 Evidence | success | professional/evidence/success.json | mock | pass |  |
| D5 Evidence | empty | professional/evidence/empty.json | mock | pass |  |
| D5 Evidence | success | professional/ask/success.json | mock | pass |  |
| D5 Evidence | abstained | professional/ask/abstained_out_of_scope.json | mock | pass |  |
| D5 Evidence | abstained | professional/ask/abstained_needs_human_check.json | mock | pass |  |
| D6 Changes | success | professional/changes/assess_success.json | mock | pass |  |
| D6 Changes | needs_review | professional/changes/assess_needs_review.json | mock | pass |  |
| D6 Changes | rules | professional/changes/assess_rules.json | mock | pass |  |
| D6 Changes | success | professional/changes/affected_success.json | mock | pass |  |
| D6 Changes | loading | professional/changes/generate_loading.json | mock | pass |  |
| D6 Changes | needs_review | professional/changes/generate_needs_input.json | mock | pass |  |
| D6 Changes | success | professional/changes/generated_success.json | mock | pass |  |
| D6 Changes | returned | professional/changes/change_returned.json | mock | pass |  |
| D6 Changes | rejected | professional/changes/change_rejected.json | mock | pass |  |
| D6 Changes | success | professional/changes/confirm_success.json | mock | pass |  |
| D7 Review | success | professional/review/recheck_success.json | mock | pass |  |
| D7 Review | failed_check | professional/review/recheck_failed_check.json | mock | pass |  |
| D7 Review | empty | professional/review/empty.json | mock | pass |  |
| D7 Review | approved | professional/review/approved.json | mock | pass |  |
| D7 Review | returned | professional/review/returned.json | mock | pass |  |
| D7 Review | failed | professional/review/self_approval_forbidden.json | mock | pass |  |
| D8 Export | success | professional/export/draft.json | mock | pass |  |
| D8 Export | approved | professional/export/approved.json | mock | pass |  |
| D8 Export | success | professional/export/publish_success.json | mock | pass |  |
| D9 History | success | professional/history/success.json | mock | pass |  |
| D9 History | empty | professional/history/empty.json | mock | pass |  |
| D9 History | success | professional/history/label_versions.json | mock | pass |  |
| D10 Print verification | empty | professional/print_verify/empty.json | mock | pass |  |
| D10 Print verification | loading | professional/print_verify/loading.json | mock | pass |  |
| D10 Print verification | success | professional/print_verify/success.json | mock | pass |  |
| D10 Print verification | failed_check | professional/print_verify/failed_check.json | mock | pass |  |
| D10 Print verification | needs_review | professional/print_verify/needs_review.json | mock | pass |  |
| P1 Scan and Understand | empty | idle | mock | pass |  |
| P1 Scan and Understand | loading | public/scan/loading.json | mock | pass |  |
| P1 Scan and Understand | failed | public/scan/failed.json | mock | pass |  |
| P2 Product information | success | public/product/success.json | mock | pass |  |
| P2 Product information | needs_review | public/product/needs_review.json | mock | pass |  |
| P2 Product information | empty | public/product/empty.json | mock | pass |  |
| P3 Ask about this label | success | public/ask/success.json | mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_out_of_scope.json | mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_low_confidence.json | mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_no_evidence.json | mock | pass |  |
| P3 Ask about this label | abstained | public/ask/abstained_needs_human_check.json | mock | pass |  |
| P3 Ask about this label | ai_accepted | public/ask/ai_accepted.json | mock | pass |  |
| P3 Ask about this label | ai_done | public/ask/ai_job_done.json | mock | pass |  |
| P3 Ask about this label | ai_fallback_timeout | public/ask/ai_job_fallback_timeout.json | mock | pass |  |
| D5 Evidence | ai_accepted | professional/ask/ai_accepted.json | mock | pass |  |

| Click-through | Result | Notes |
|---|---|---|
| D6 confirm checklist button | pass |  |
| D6 generate draft button (mock) | pass |  |
| D9 audit and versions switch buttons | pass |  |
| D7 return needs a comment | pass |  |
| D7 approve is disabled when the re-check failed | pass |  |
| D8 download click | pass |  |
| D4 confirm button reaches a confirmed extraction (mock) | pass |  |
| D4 run inspection reaches the check result | pass |  |
| D4 unclear field is editable, confirmed field is not | pass |  |
| D5 ask click | pass |  |
