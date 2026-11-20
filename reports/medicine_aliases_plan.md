# Frozen medicine-aliases protocol

Independent branch from origin/main. Keep threshold 0.65 and existing review
band. Do not alter retrieval implementation or shared schemas. Aliases and
labeler values must be extracted from hash-verified pinned SPL metadata, with
XPath, source URL, source hash and effective date per value. Preserve the
distinction between SPL labeler and physical manufacturer; the public field
must state its metadata role. Do not invent brand equivalents absent from SPL.

Expand toward 30 products using the existing one-command corpus rebuilder and
automatically pinned DailyMed discovery; retain current ten products and never
index device data. Source, download and metadata failures remain explicit.

Freeze the adjacent 60-name query file before scoring: 45 expected matches and
15 decoys, with brands/descriptions, generic formulations and misspellings.
Queries are authored examples, not real-photo accuracy. Run once at 0.65 after
candidate freeze; no tuning on these names. Decoy gate: zero outcome=matched
on decoys. Also report needs_review/no_reference_match and positive mistakes.
Failure blocks merging this branch, not the independently gated print branch.

Conservative gate interpretation: any surfaced decoy candidate, including
needs_review, blocks promotion; no_reference_match is required for all 15.
Labeler metadata populates the requested manufacturer field with explicit
evidence role "SPL labeler; physical manufacturer not established" and source URL.
No branded equivalent is invented when the pinned SPL only names a generic.

Pre-score environment choice: BGE-large preload on default MPS crashed before
query evaluation. CPU preload succeeded, with the same frozen model and E5b
recipe. Use CPU and one inference thread for reproducibility. No match query
was scored during setup. Expansion succeeded: 30 products, 618 chunks, zero
source failures. Metadata includes 90 alias records, including repeated strings;
runtime deduplicates aliases per product. Threshold remains exactly 0.65.
