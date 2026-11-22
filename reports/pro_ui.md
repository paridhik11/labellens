# Professional page, simple workflow (ui/pro)

A new single-screen Professional page for the live demo: `http://127.0.0.1:8000/ui/pro/index.html` (served by `scripts/run_demo.py`, no new server). It runs the same API calls, in the same order and with the same fields, as the proven sequence in `scripts/demo_flow.py`. Every operation it calls is listed with its source in `docs/PRO_UI_API_MAP.md`. The old workspace (`ui/professional/`) and the public pages are unchanged and still pass their checks.

## Files

| File | Why |
|---|---|
| `ui/pro/index.html` | The page: top bar (product name, LIVE API indicator, Editor / Reviewer switch, Advanced view link), progress strip, demo banner. |
| `ui/pro/pro-api.js` | The only network code. X-User-Id header, Error bodies turned into `error: message`, X-Mock answers refused, 202 jobs polled at `GET /jobs/{job_id}` every 1.5 s (limit 300 s). |
| `ui/pro/pro.js` | State, the seven stages, the action wrapper (spinner, seconds counter, every button disabled while running, error text with Retry), camera, form prefill. |
| `ui/pro/pro.css` | Styles on top of `ui/css/base.css` (Figtree, one teal accent). Big buttons, works at 1280 and 1024 px. |
| `ui/pro/sample/golden_label.pdf` | Byte-identical copy of `golden/golden_label.pdf` (2.7 KB, DRAFT and TEST DATA marked). See decision 2. |
| `ui/pro/sample/test_device.json` | Byte-identical copy of `src/gen/templates/test_device.json`. See decision 3. |
| `ui/tools/pro_e2e.cjs` | Playwright end-to-end check (headed, real clicks, real API). |
| `docs/PRO_UI_API_MAP.md` | The 30 operations the page calls, written before the code. |
| `reports/pro_ui/` | 27 screenshots (JPEG, 900 px wide) and `results.json`. |
| `ui/index.html` | One line: a link to the new page. |

## Decisions (made without asking, as the task said)

1. **Reading a label before a product exists.** `uploadScan` needs a `product_id` (CR-20) and no endpoint edits a product record after registration. So "Read label" uploads to one internal intake record (`Label intake (internal, not a product)`, `extra.intake = "true"`, created once and reused), shows the extraction, and "Save product" then does exactly what `demo_flow.py` does: register the product with the confirmed values, register the template, upload the same file as the product's first label version, confirm the extraction. Cost: the label is read twice (about 15 s each for the golden PDF), and the intake record is a real product row. The new page hides it from its list and says how many are hidden; the old workspace still lists it. Save is resumable: if a step fails, Retry continues from the step that failed instead of registering a second product.
2. **Sample Golden Pump label.** `ui/tools/golden_setup.py` registers the product and renders the PDF in Python; the browser can do neither, and `golden/` is not served (and is git-ignored). The page fetches `ui/pro/sample/golden_label.pdf` and sends it through the real upload route, then the person reviews and saves. `pro_e2e.cjs` renders the golden label again with the real renderer and checks the copy is byte-identical (sha256 `764a23f9...`), so a renderer change would fail the check instead of drifting silently.
3. **Template.** `src/` is not served, so the template `demo_flow.register_golden` sends is copied to `ui/pro/sample/test_device.json` (checked byte-identical by `pro_e2e.cjs`). Every product added on this page gets this template (100 x 60 mm, the repo's only template without a background). A label of a different layout therefore gets revised artwork in this layout.
4. **Form prefill.** Words (name, manufacturer, address, model) come from the label text. Lot, expiry, serial and UDI-DI come from the decoded barcode (AI 10, 17, 21, 01) when there is one, because the decoder reads them exactly; when the printed text disagrees, the field is highlighted with both values. A "LOT: " or "EXP: " style prefix is removed for the record and put back when the label text is confirmed. Expiry from AI 17 (YYMMDD) is written as 20YY-MM-DD, the renderer's year range. Sterilization and storage are not printed on this template, so they start empty and highlighted. A missing UDI-DI stays empty (never made up).
5. **When the barcode decision appears.** A freshly uploaded label version has no template slots, so a change on it returns "no template field" items and no barcode decision (`I-NOSLOT`, `I-NOBARCODE`); the decision appears on the generated artwork (REGENERATE for a lot change). After one generation the label has a template, so the next change shows KEEP or REGENERATE at assessment. The page says this in plain words instead of inventing a decision. An unconfirmed encoded change (`NEEDS_INPUT` with `confirm_lot`) gets its own sentence: the new barcode is built after a person confirms.
6. **Approval.** Approve is enabled for the Reviewer only, but the page never decides whether approval is allowed: it sends the PDF hash and the check id of the re-check it ran (or no check id if none) and shows the API's refusal (`check_required`, `role_forbidden`, `version_superseded` and so on). The check id must come from a re-check in the same browser session, because no endpoint lists the checks of a version; the Review stage offers the re-check button for that.
7. **Not included:** publish, the AI answer, DailyMed, admin. Export downloads the stored PDF and recomputes its sha256 in the browser.
8. **Wording.** My own text never says "compliant". One API reason text does, in a negation ("This says what to update, not whether the result is compliant."); it is shown verbatim because the page does not rewrite server messages. The API disclaimer "Not a compliance determination." is also shown as sent.
9. **ui/CLAUDE.md** (written for the earlier mock-based UI) says data loads through `ui/js/data.js` mocks and commits go to `ishanvi-ui`. This task forbids mocks and asked for a branch, so the task wins. Its demo banner, the TEST label on the placeholder identifier and the DRAFT disclaimer are kept.

## Verification

Run against my own `scripts/run_demo.py --port 8020` from this checkout. Port 8000 was already taken by a demo server started from the nested, untracked copy `labellens/labellens/` (a different checkout, which does not serve this page); I did not stop it. Playwright's bundled Chromium does not start on this PC (Windows "side-by-side configuration is incorrect"), so `pro_e2e.cjs` uses the installed Google Chrome (`PW_CHANNEL=chrome`, a fresh temporary profile; it also falls back to it automatically). The existing UI tools were run through a scratch preload shim that does the same; they were not edited.

`pro_e2e.cjs`, 24 steps, 24 PASS (steps 1 to 23 in one run, step 24 with `ONLY=stopped` while I stopped the server):

| # | Step | Result | Seconds | Screenshot | What the page showed (real output) |
|---|---|---|---|---|---|
| 1 | sample files are byte-identical to their sources | PASS | 1 | - | golden PDF 764a23f9ceb0 rendered now = sample copy; template copy identical |
| 2 | open Products, LIVE API indicator | PASS | 0.3 | 01_products.jpg | 20 products listed; 1 internal intake record hidden; user Demo Editor (editor) |
| 3 | search filtering | PASS | 0.4 | 02_filter.jpg | golden -> 14 rows, nonsense -> no-match message, ExampleDevice -> 1 row |
| 4 | add sample Golden Pump (read, correct, save) | PASS | 29.3 | 03_read_sample.jpg, 04_saved.jpg | prd_5ffd705d; unclear highlighted: model, lot, expiry, sterilization, storage; prefilled lot LOT1, expiry 2030-06-30, udi 00000000000000, serial SN1, model empty (not read) |
| 5 | run check (inspect) | PASS | 0.4 | 05_check.jpg | No critical finding; 1 finding, it says a person must look; 3 human-review items; extraction_unreliable note shown |
| 6 | evidence search and question | PASS | 1.4 | 06_evidence.jpg | 10 passages, 10 citations; question abstained with closest passages |
| 7 | invalid value error and Retry | PASS | 2.2 | 07_invalid_value.jpg | "Not assessed (ambiguous_date): '03/04/2028' could be day first or month first. Write it as YYYY-MM-DD."; "no_change: lot already has this value ('LOT1'); nothing to change."; both Retry buttons re-sent the request |
| 8 | change lot to LOT2, confirm checklist | PASS | 1.9 | 08a_assess_lot.jpg, 08_change_lot.jpg | affected: linked_label, linked_label; barcode decision deferred to Generate (uploaded label); confirmed |
| 9 | generate revised artwork: barcode REGENERATE | PASS | 2.2 | 09_artwork_regenerate.jpg | lbv_c77e88bc; REGENERATE; DRAFT preview drawn |
| 10 | re-check the lot version | PASS | 19.9 | 10_recheck_lot.jpg | No critical finding; findings B-LOT, X-HEALTH; B-LOT cites 21 CFR 801.40 Form of a unique device identifier |
| 11 | change name: barcode KEEP, confirm | PASS | 1.6 | 11a_assess_name_keep.jpg, 11_change_name_keep.jpg | barcode KEEP at assessment |
| 12 | generate the name version (KEEP) | PASS | 2.2 | 12_artwork_keep.jpg | lbv_035181bc, barcode KEEP |
| 13 | blocked approval (no re-check yet) | PASS | 0.9 | 13_blocked_approval.jpg | check_required: An approval needs the check_id of a passed check. |
| 14 | reviewer: re-check, comment, approve | PASS | 18.8 | 14_approved.jpg | Recorded: approve by usr_demo_reviewer (rev_67f68251). Status is now reviewed. |
| 15 | export: download PDF, hash and DRAFT | PASS | 1 | 15_export.jpg | lbv_035181bc.pdf, 2753 bytes; sha256 computed in the browser matches the recorded hash; mark DRAFT, not for production / TEST DATA / DRAFT; 100 x 60 mm |
| 16 | print verification on a rasterized copy of the approved PDF | PASS | 2.3 | 16_print_verify.jpg | outcome match (a perfect digital render, not a photo of a real print) |
| 17 | history | PASS | 0 | 17_history.jpg | 32 events: review.approved, check.recorded, export.downloaded, artwork.generated, label.version_created, template.version_created, product.version_created, change.* , extraction.confirmed |
| 18 | second product: upload golden_label.pdf, type fields by hand | PASS | 33.4 | 18_read_by_hand.jpg, 19_saved_by_hand.jpg | prd_a003b45a; record shows the typed model HP-200 and sterilization Gamma |
| 19 | second product: change expiry, confirm | PASS | 1.7 | 20_change_by_hand.jpg | affected: linked_label, linked_label; confirmed |
| 20 | layout at 1024 px | PASS | 0.4 | 21_width_1024.jpg | scrollWidth 1009, no horizontal scroll |
| 21 | API unreachable (requests aborted in the browser) | PASS | 4.5 | 22_api_unreachable.jpg | "Cannot reach the LabelLens API at http://127.0.0.1:8020 (Failed to fetch). Check that scripts/run_demo.py is running, then press Retry."; indicator API offline; Retry loaded the list again |
| 22 | camera denied | PASS | 1.3 | 23_camera_denied.jpg | "Camera permission was denied. Allow the camera for this page in the browser settings, or upload a file instead."; upload still enabled |
| 23 | camera with a fake device (Chrome test camera) | PASS | 5.8 | 24_camera_fake_device.jpg | captured camera.png (52 KB, source camera); API answered retake_photo (blur, low contrast): the fake test pattern is not a label |
| 24 | server really stopped | PASS | 0.2 | 25_server_stopped.jpg | same "Cannot reach the LabelLens API" message, indicator API offline |

Other checks (all on the pro-ui branch, server on 8020):

- Fast tests: `python -m pytest -q -m "not slow"`: 1041 passed, 8 skipped, 5 deselected.
- Lint: `ruff check src tests`: All checks passed. (Running ruff also on `scripts` and `ui/tools` reports 65 errors that are already on main; this branch adds no Python.)
- `scripts/demo_e2e.py --base http://127.0.0.1:8020`: 20 passed, 0 fallback, 0 failed, no mock.
- `ui/tools/check_screens.cjs` (old workspace and public pages): mock mode 67 states, 0 failed, 11 click-throughs 0 failed; api mode the same.
- `ui/tools/live_flows.cjs` with `golden_setup.py`: 13 flows, 0 FAIL (golden package 9/9 stages through the old UI).
- Scan of the new files: no em dashes, no en dashes, no import or read of `src/api/mock`, no "compliant" in my text, every path called is in `docs/PRO_UI_API_MAP.md`.

## What does not work or was not tested

- **A real camera** was not tested (no camera on this PC session). Tested: permission denied, and Chrome's fake test camera through capture and upload.
- **Print verification** was tested only with a 300 dpi rendering of the approved PDF, which matches trivially. Real printed-label photos are unmeasured (as `docs/KNOWN_LIMITS.md` says).
- **Port 8000** was not used for the checks because another demo server (from the nested copy) was running there. Start the demo from this checkout so `/ui/pro/` is served.
- Text checks on the golden PDF are skipped by the checker (`extraction_unreliable`, no label edge on a rendered page); only barcode and symbol rules decide there. The page says so.
- The check id needed for approval lives in the browser session only: after a page reload, run the re-check again before approving.
- A product added from a label of another layout still gets the 100 x 60 mm test template.
- Adding a product reads the label twice (decision 1), about 30 s for the golden PDF.
