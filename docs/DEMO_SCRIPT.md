# Demo script (about 6 minutes)

The click path for the live demo on the simple pages: the public medicine page (`/ui/public/index.html`) and the Professional workspace (`/ui/pro/index.html`), both on the live API. Everything below was rehearsed on the final code (`reports/final_polish.md` has the timings and screenshots). Test data is marked as test data, every draft carries the DRAFT mark, and nothing here is a compliance determination.

## Before you start (once, not part of the 6 minutes)

```powershell
.venv312\Scripts\python.exe scripts\run_demo.py --warm
```

- Wait for the URLs and for `warm-up: live DailyMed labels ready 4 of 4` (first time: about 3 to 4 minutes, needs internet; later starts: seconds, the labels are cached on disk). `--warm` prefetches the live DailyMed labels the demo uses (pregabalin, Zetia, metoprolol, Lopressor) so no first fetch (30 s to 2 minutes) happens on stage. It also loads the AI model into Ollama when Ollama runs (`warm-up: AI model: ... loaded`).
- Check the line `Tesseract found`: the photo scan needs it.
- Close heavy programs. On a loaded PC the photo reader can hit its time limit and the AI answer takes longer.
- Open the pages with Ctrl+F5 once so the browser loads the newest scripts.

## Click path

| Min | Page | Do | Say | Avoid |
|---|---|---|---|---|
| 0:00 | Home `/ui/` | Click **Open Public Mode**. | Two modules, kept apart: public medicine (21 CFR 201, 208, 211 and DailyMed labels) and professional devices (21 CFR 801, 820, 830). | |
| 0:10 | Public, Scan | **Upload a photo**: `demo_photos/public/04_barcode_aspirin.jpg`. About 3 s. "Is this Aspirin? We read NDC barcode ..." Click **Confirm**. | The NDC barcode decides; the page never confirms by itself. The photos are DailyMed package artwork with simulated camera conditions, not phone photos. | Do not call it "verified": the banner says authenticity is not verified. |
| 0:40 | Public, Ask | **Ask questions about this medicine**, type `how should I store it`, **Ask**. | Retrieval over this product's label only. With no language model the page shows "Closest passages from the label", the sentences retrieval ranked highest, each with its label section and a DailyMed link. Score and gate only in the small details line. | |
| 1:10 | Public, Scan | **Upload a photo**: `demo_photos/public/08_live_zetia.jpg` (about 20 to 30 s, a counter runs). | Zetia is not one of the 30 curated medicines. When the scan reads the name next to a strength it searches DailyMed and asks "Is this ...?"; **Confirm** fetches the label (seconds when warmed): "Fetched live from DailyMed, not in the curated set". This photo was not rehearsed with the new lookup: if no proposal appears, use the fallback on the right. | If the photo reader times out, use **Type the name**, `Zetia`, **Find**, **Search DailyMed**, **Use this label**. |
| 1:50 | Public, Ask | Type `metoprolol` as the medicine name and ask `how to store it`. "Pick a medicine first" appears and DailyMed is searched; click **Use this label** on the first entry, then ask again. Then ask `side effects`. | Storage answers from "16 HOW SUPPLIED/STORAGE AND HANDLING" with the "Store at 20° to 25°C" sentence; side effects from "6 ADVERSE REACTIONS". A question the label does not answer (for example `capital of France`) says "This label doesn't seem to answer that." with the passages folded. | Do not present the live label gate (0.02) as evaluated: it is a conservative probe-based threshold. |
| 2:30 | Home, then **Open Professional Workspace** | Products list (LIVE API badge). **Add label**, **Choose PDF or image**: `demo_photos/device/03_golden_blurry.jpg`, **Read label**. | Refused in about 2 s: the photo is too blurry, no label is created. Bad input never becomes a record. | |
| 2:50 | Pro, Add label | Click **Use sample Golden Pump label** (or choose `demo_photos/device/01_golden_label.pdf`), **Read label**, correct the highlighted fields (model `GP-100`, lot `LOT1`, expiry `2030-06-30`), **Save product**. | The reader fills the fields; highlighted ones need a person; "What the regulations require" shows the governing passage for each required element. | |
| 3:30 | Pro, Check | **Run check**. Scroll to **Findings by field**. | Each card: the product value, what the rules decided (rule id), and the top regulation passage for that field, filtered for this product (no latex condom section for a pump). Rules decide; retrieval explains. | Do not say "compliant": Pass means no rule found a problem. |
| 4:00 | Pro, Check | **Ask the regulations**, press the example **Expiration date**. Then **Ask with AI** on the same question (warmed: about 10 to 60 s; the page counts the seconds). | Passages: 21 CFR 801.18 first, each section once. The AI may only use those passages and a checker rejects unsupported sentences; on a timeout the page shows the passages with a note. | Do not wait in silence: talk about the passages while the AI runs. |
| 4:40 | Pro, Retrieval lab | **Retrieval lab**, first example. | The same query in all five systems (our BM25 and TF-IDF, dense, hybrid, E5b), labeled "raw retrieval, unfiltered". The table under it is the Step 18 evaluation (LLM grades). | |
| 5:00 | Pro, Change | **Change a detail**: lot `LOT2`, **Assess**, confirm the checklist, **Revise artwork**, **Generate**. | The lot is in the barcode, so the decision is REGENERATE; the template is filled (never an image model) and the draft carries DRAFT. | |
| 5:30 | Pro, Review and approve | Switch to **Reviewer**, **Run re-check**, read the finding cards, comment, **Approve**. | Approval is bound to this PDF hash and a passed re-check. A newer version voids it. | |
| 5:50 | Pro, Export | **Download PDF**, **Download findings report**. Optionally **Verify print** with a photo. | Physical size, hash checked in the browser, DRAFT mark kept. The report lists every finding with its rule id and cited passages. Print verification is measured on simulated photos only. | |

## If something goes wrong

- **API offline badge:** the server is not running; start `scripts/run_demo.py` again.
- **Photo reader timeout (about 55 s):** say the reader is slow on a busy CPU and use **Type the name**.
- **DailyMed unreachable:** the page says so; the curated 30 medicines and the professional workspace keep working.
- **AI answer timeout (180 s):** the passages are already shown with a note. That is the designed fallback.

## Things not to claim

- Not real phone photos: DailyMed package artwork with simulated camera conditions.
- The live-label gate (0.02) is a conservative threshold from a probe on one label, not evaluated.
- The AI answer is slow on CPU and optional; the default is extractive.
- Relevance grades are LLM grades except the 308-row human sample.
- Exports are DRAFT only; no approved variant is rendered.

## Other demo photos

`demo_photos/README.md` lists every photo with the expected result. `demo_photos/public/12_synthetic_lopressor.jpg` is a synthetic pack (placeholder NDC 12345-678-90) made by `demo_photos/make_lopressor_image.py`: no NDC resolves, the scan reads "LOPRESSOR" next to "50 mg" and asks "Is this LOPRESSOR (METOPROLOL TARTRATE) TABLET?".
