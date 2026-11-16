# Step 24b: generateArtwork and export

**Done.** `generateArtwork`, `getArtwork`, `getExports` are real, plus new `downloadArtifact` (CR-22; CR-21 was taken by the AI answer on main, so mine is CR-22, and I fixed three upload mentions that said CR-21 to CR-20).

**How it works.** `src/api/artwork.py` refuses in the request (closed change, unconfirmed assessment, NEEDS_INPUT with a `task_<reason>` code, layout failure as a 422 CheckResult) before any job exists. The 202 job renders PDF, SVG, QR and a report through `src/api/engine.py` (Parth's renderer behind an interface, lazy imports), stores `data/api/artifacts/<sha256>.<ext>` atomically, and appends everything in one transaction (product version, template version, new draft label version, layout check, artwork and file rows). Old versions are never touched.

**Choices.**
- `artifact_sha256` = sha256 of the PDF bytes.
- Approval of generated artwork needs a `self_check` (the re-check), not the layout check, plus the exact hash and a confirmed assessment. A new version voids it.
- Stored files keep `DRAFT, not for production` after approval (no approved variant is rendered), so `draft_watermark` stays true. Downloads are re-hashed and carry `X-Draft-Mark`.
- QR is stored but served only for a published version (publish is still a mock; the base URL is a placeholder).
- One edit per generation, or a model edit with its new udi_di.
- A template with a background image is refused (gap D-5).

**Verified.** `ruff check src tests` clean. Fast suite (CI-like env, no renderer libraries) exit 0. Renderer env: 218 passed, 5 skipped (e2e, generate, contract, handoff, export, revise, persistence). The e2e uses the real renderer: scan, inspect, change, confirm, generate, re-check, approve, export, regenerate.

**Not done or not verified.** The e2e extractor is a stub, so no OCR read the rendered PDF. A product version is created at generation, so a rejected change leaves one. No approved (unmarked) render. Publish, print verification unchanged.
