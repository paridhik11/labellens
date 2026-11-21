# Demo script (about 5 minutes)

Click path for the golden package, checked against `scripts/demo_e2e.py` (20 of 20 stages PASS, no mock, no fallback) and the UI flow `ui/tools/e2e_golden.cjs`. All test data is marked as test data and every draft carries the DRAFT mark. Nothing here is a compliance determination.

## Before you start (once, not part of the 5 minutes)

```powershell
.venv312\Scripts\python.exe scripts\run_demo.py
```

Wait for the URLs. On a machine with no index store the first start builds the dense indexes (about 40 minutes); set `LABELLENS_INDEX_DIR` to an existing store to skip that. Then, in a second terminal, optionally `.venv312\Scripts\python.exe scripts\demo_e2e.py` as a smoke test. To drive the UI on the golden package, prepare it with:

```powershell
.venv312\Scripts\python.exe ui\tools\golden_setup.py --base http://127.0.0.1:8000 --out <folder>
```

It prints the product id and the label PDF path. Open `http://127.0.0.1:8000/ui/professional/index.html?mode=api&product=<product id>`. The badge at the top must read `api`, not `mock`. The user switch (top right) starts as the editor `usr_demo_editor`.

## Click path

| Min | Screen (sidebar) | Do | Say | Real or mock |
|---|---|---|---|---|
| 0:00 | D3 Upload or scan | Choose `golden_label.pdf`, click Upload. Wait for "Scan processed". | The system reads the label (text, barcode) with the real extractor. | Real |
| 0:40 | D4 Inspect | Open the extraction. Fix the unclear fields (model, lot) from the label text, click Confirm. | Nothing is trusted silently: unclear fields are corrected by a person, and each correction is recorded. | Real |
| 1:10 | D4 Inspect | Run inspection. | One `extraction_unreliable` finding: the rendered PDF page has no label boundary, so text checks are skipped and a human is asked. This first check has no citation. | Real |
| 1:40 | D6 Changes | Field `lot`, new value `LOT2`, Assess, then Confirm checklist. | The lot is encoded in the barcode, so the decision is REGENERATE. Rules decided this, not a language model. | Real (rule parser) |
| 2:20 | D6 Changes | Generate draft artwork. | The template is filled, never an image model. The draft is marked DRAFT and the new barcode is built from the new lot, with a test GS1 identifier. | Real renderer |
| 3:00 | D7 Review | Click the live re-check. | The rendered PDF is read back as an image. The finding `B-LOT barcode_mismatch` carries a citation (21 CFR 801.40, verbatim quote). Evidence comes from retrieval, the decision from the rule. | Real (e5b retrieval, falls back to hybrid) |
| 3:40 | D7 Review | Switch user to `usr_demo_reviewer`, add a comment, Approve. | Approval is bound to this exact PDF hash and a passed check. A new version would void it. | Real |
| 4:10 | D8 Export | Download the PDF. | Physical size, hash verified, DRAFT mark still on it: the approved variant is not built. | Real |
| 4:30 | `/public/medicine` | Type `Childrens Ibuprofen`, read the reference fields, ask `what are the warnings`. Then `Zzyzx Gummies` for the no-match case. | A separate public module, 30 reference products, passages with sources, abstains when unsure. | Real (extractive). The photo scan (`publicScan`) is a mock |

## Stages that use mocks, fallbacks or are not shown

- **Mock:** `publicScan` and `getPublicScan` (the public photo entry). Everything else answers from the real API; a mock response carries the header `X-Mock: true` and the UI badge says `mock`.
- **Optional, slow:** the AI answer (`/public/ask?mode=ai`, qwen2.5 3b through Ollama) takes about 30 to 40 s and falls back to the extractive passages. In the checked run it fell back with `verification_failed`. Skip it in a 5 minute demo.
- **Not shown:** print verification (D10) is real but measured on simulated photos only; multi-side scan does not exist.
- **If something fails live:** `demo_e2e.py` prints PASS, PASS (mock), FALLBACK or FAIL per stage. Say which one it is.
