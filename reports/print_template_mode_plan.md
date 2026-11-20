# Frozen print-template-mode rules

Branch: print-template-mode, from origin/main. No CV2-default, checker-threshold
or shared-schema change. Read-only inspection preceded this plan; no evaluation
or tests ran before the plan commit.

Bind expected fields, GS1 payload and template specification to the approved
artwork version. Missing/unsupported template binding means rescan_needed,
never a fallback match. Locate the label, rectify at the template aspect ratio,
map each text slot into the corrected image, mask the 9 mm DRAFT band, and OCR
each crop independently. Expected strings are comparison inputs only, never OCR
hints. Project evidence boxes back into original-photo coordinates.

Use the existing 0.8 OCR confidence gate and existing field normalization.
A confident differing compared field means mismatch. Weak, missing, ambiguous
or clipped slot evidence means rescan_needed. Match requires every compared
field to pass with confident evidence and exactly matching decoded GS1 values.
Conflicting barcodes mean mismatch; absent/ambiguous barcode evidence rescans.
Symbols are outside this decision. Preserve API approval/current-version gates.

Debug only: seeds 5000-5047 and 7000-7007. Freeze candidate before final scoring.
Final seeds start at 9000, never used for debugging. Per clean/moderate/hard
condition: 16 correct prints and 16 different-label prints, distributing wrong
lot, expiry and product name; retain both text-only changes with unchanged
barcode and payload-changing cases. Never exclude failed/timeout cases.

Report confusion counts, false matches, correct matches, missed differences
and rescan rates with Wilson 95% intervals per condition. Gate: zero wrong-label
matches in every condition, and at least one correct match in clean and moderate.
One false match blocks merging this branch. No tuning/rescoring final seeds.
Run full fast pytest and ruff before no-ff promotion and public-API CI check.
