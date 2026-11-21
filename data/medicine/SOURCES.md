# Medicine corpus sources

Source: National Library of Medicine, DailyMed. Medicine only, excluded from device evaluation.
Rebuild: `python -m scripts.real.build_medicine_corpus`. Use `--offline` with cached sources.
Corpus text and product metadata are versioned. Original XML stays local.
The catalog now pins 100 products and 2440 chunks (30 earlier, 70 from `data/medicine/med100_candidates.tsv`, see `reports/med100.md`). Rebuild metadata with
`python -m src.gen.medicine_metadata --expand`; it re-fetches pinned originals
when absent. Aliases come from SPL product/generic names and short titles.
Labeler is sourced from author/representedOrganization/name. It can be a
repackager or distributor, so the manufacturer response evidence states its
role as SPL labeler rather than asserting a physical manufacturing site.
Every metadata value retains its pinned source URL, XPath, hash and effective date.
These are selected product labels, not a clinical knowledge base or a representative drug sample.
Public access does not establish a blanket license for company label artwork.
Policy: https://www.nlm.nih.gov/web_policies.html#copyright
API: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm

The effective date is the SPL document effectiveTime, not its download date.
Sections: indications/description/package labelling, warnings/contraindications/precautions, dosage.
No text is generated, summarized or offered as medical advice. Retrieval integration and evaluation NOT_RUN.

| Product | Effective date | Pinned source |
|---|---|---|
| Pain Relief Extra Strength | 2026-11-10 | [SPL v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=9fdbaf5e-f88b-4d18-97df-0b2e8dddf377&version=3) |
| Childrens Ibuprofen | 2026-10-29 | [SPL v4](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=0faa3b41-a241-4aae-9cc8-e075728ff916&version=4) |
| Loratadine | 2026-10-27 | [SPL v6](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=3881afaf-8d0d-4154-85a8-79a3c7806b49&version=6) |
| Omeprazole | 2026-10-26 | [SPL v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=346141b5-b49d-489a-84eb-18df8b940460&version=3) |
| FAMOTIDINE | 2025-11-25 | [SPL v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=446ca466-a43c-0401-e063-6394a90ac0d1&version=1) |
| Amoxicillin | 2026-09-01 | [SPL v2](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=2c395111-c9c1-483e-a542-58b935ede689&version=2) |
| METFORMIN HYDROCHLORIDE | 2026-09-02 | [SPL v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=d8bd1779-d1c4-4dde-816d-ea72b37bb5cd&version=3) |
| Atorvastatin Calcium | 2026-09-17 | [SPL v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=a519e355-84f0-40d1-b586-e6e8eadb5b0f&version=3) |
| Levothyroxine Sodium | 2026-10-01 | [SPL v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1a2124e6-aea2-40dd-bb8d-52c58405a67e&version=1) |
| ALBUTEROL SULFATE | 2026-09-22 | [SPL v4](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1810ff8e-d505-bf9c-e063-6394a90a6540&version=4) |

<!-- medicine-catalog -->
```json
[
  {
    "product_name": "Pain Relief Extra Strength",
    "setid": "9fdbaf5e-f88b-4d18-97df-0b2e8dddf377",
    "version": 3,
    "effective_date": "2026-11-10",
    "fetched": "2026-11-16",
    "xml_sha256": "f0e07ec4c884a666e65725b330fca839797c237446f44ee36847eb334cf35a9a",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9fdbaf5e-f88b-4d18-97df-0b2e8dddf377&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/5",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s5_c1"
        ]
      },
      {
        "section": "warnings/42229-5/7",
        "title": "Liver warning",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s7_c1"
        ]
      },
      {
        "section": "warnings/42229-5/8",
        "title": "Allergy alert",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s8_c1"
        ]
      },
      {
        "section": "warnings/50570-1/9",
        "title": "Do not use",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s9_c1"
        ]
      },
      {
        "section": "warnings/50569-3/10",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s10_c1"
        ]
      },
      {
        "section": "warnings/50568-5/11",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s11_c1"
        ]
      },
      {
        "section": "warnings/50566-9/12",
        "title": "Stop use and ask a doctor if",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s12_c1"
        ]
      },
      {
        "section": "warnings/53414-9/13",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "Overdose warning",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s15_c1"
        ]
      },
      {
        "section": "dosage/34068-7/16",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s16_c1"
        ]
      },
      {
        "section": "labelling/51945-4/19",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3_s19_c1"
        ]
      }
    ]
  },
  {
    "product_name": "Childrens Ibuprofen",
    "setid": "0faa3b41-a241-4aae-9cc8-e075728ff916",
    "version": 4,
    "effective_date": "2026-10-29",
    "fetched": "2026-11-16",
    "xml_sha256": "f7c0e0ac3f102efa38418223f88cfab753201c89d9cbe608bccd2f7316c3b874",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=0faa3b41-a241-4aae-9cc8-e075728ff916&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/5",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s5_c1"
        ]
      },
      {
        "section": "warnings/42229-5/7",
        "title": "Allergy alert",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s7_c1"
        ]
      },
      {
        "section": "warnings/42229-5/8",
        "title": "Stomach bleeding warning",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s8_c1"
        ]
      },
      {
        "section": "warnings/42229-5/9",
        "title": "Heart attack and stroke warning",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "Sore throat warning",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s10_c1"
        ]
      },
      {
        "section": "warnings/50570-1/11",
        "title": "Do not use",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s11_c1"
        ]
      },
      {
        "section": "warnings/50569-3/12",
        "title": "Ask a doctor before use if",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s12_c1"
        ]
      },
      {
        "section": "warnings/50568-5/13",
        "title": "Ask a doctor or pharmacist before use if the child is",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s13_c1"
        ]
      },
      {
        "section": "warnings/50567-7/14",
        "title": "When using this product",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s14_c1"
        ]
      },
      {
        "section": "warnings/50566-9/15",
        "title": "Stop use and ask a doctor if",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s15_c1"
        ]
      },
      {
        "section": "warnings/50565-1/16",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s16_c1"
        ]
      },
      {
        "section": "dosage/34068-7/17",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s17_c1"
        ]
      },
      {
        "section": "labelling/51945-4/22",
        "title": "PRINCIPAL DISPLAY PANEL - 120 mL Bottle Carton",
        "chunk_ids": [
          "dailymed_0faa3b41-a241-4aae-9cc8-e075728ff916_v4_s22_c1"
        ]
      }
    ]
  },
  {
    "product_name": "Loratadine",
    "setid": "3881afaf-8d0d-4154-85a8-79a3c7806b49",
    "version": 6,
    "effective_date": "2026-10-27",
    "fetched": "2026-11-16",
    "xml_sha256": "d715476e8cc48da36ad33b9cfb4a7e6df7aabee88775f45f55b58cbced643b56",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3881afaf-8d0d-4154-85a8-79a3c7806b49&version=6",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/5",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s5_c1"
        ]
      },
      {
        "section": "warnings/50570-1/7",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s7_c1"
        ]
      },
      {
        "section": "warnings/50569-3/8",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s8_c1"
        ]
      },
      {
        "section": "warnings/50567-7/9",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s9_c1"
        ]
      },
      {
        "section": "warnings/50566-9/10",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s10_c1"
        ]
      },
      {
        "section": "warnings/53414-9/11",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s11_c1"
        ]
      },
      {
        "section": "warnings/50565-1/12",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s12_c1"
        ]
      },
      {
        "section": "dosage/34068-7/13",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s13_c1"
        ]
      },
      {
        "section": "labelling/51945-4/18",
        "title": "PRINCIPAL DISPLAY PANEL - 120 mL Bottle Carton",
        "chunk_ids": [
          "dailymed_3881afaf-8d0d-4154-85a8-79a3c7806b49_v6_s18_c1"
        ]
      }
    ]
  },
  {
    "product_name": "Omeprazole",
    "setid": "346141b5-b49d-489a-84eb-18df8b940460",
    "version": 3,
    "effective_date": "2026-10-26",
    "fetched": "2026-11-16",
    "xml_sha256": "516ea2d452c8e9f63691dbc578e4c8ecdd7d74c1f59df378e93d8879ad876ba3",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=346141b5-b49d-489a-84eb-18df8b940460&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/5",
        "title": "Use",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s5_c1"
        ]
      },
      {
        "section": "warnings/42229-5/7",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s7_c1"
        ]
      },
      {
        "section": "warnings/50570-1/8",
        "title": "Do not use if you have",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s8_c1"
        ]
      },
      {
        "section": "warnings/50569-3/9",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s9_c1"
        ]
      },
      {
        "section": "warnings/50568-5/10",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s10_c1"
        ]
      },
      {
        "section": "warnings/50566-9/11",
        "title": "Stop use and ask a doctor if",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s11_c1"
        ]
      },
      {
        "section": "warnings/53414-9/12",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s12_c1"
        ]
      },
      {
        "section": "warnings/50565-1/13",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s13_c1"
        ]
      },
      {
        "section": "dosage/34068-7/14",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s14_c1"
        ]
      },
      {
        "section": "labelling/51945-4/19",
        "title": "PRINCIPAL DISPLAY PANEL - 20 mg Tablet Bottle Carton",
        "chunk_ids": [
          "dailymed_346141b5-b49d-489a-84eb-18df8b940460_v3_s19_c1"
        ]
      }
    ]
  },
  {
    "product_name": "FAMOTIDINE",
    "setid": "446ca466-a43c-0401-e063-6394a90ac0d1",
    "version": 1,
    "effective_date": "2025-11-25",
    "fetched": "2026-11-16",
    "xml_sha256": "43703e68e50c05fa0c2a4cd33012ef72db67dd85b684209036732b75127e161b",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=446ca466-a43c-0401-e063-6394a90ac0d1&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s2_c1"
        ]
      },
      {
        "section": "dosage/34068-7/4",
        "title": "2.1 Recommended Dosage in Adults",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s4_c1",
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s4_c2"
        ]
      },
      {
        "section": "dosage/34068-7/5",
        "title": "2.2 Recommended Dosage in Pediatric Patients",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s5_c1",
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s5_c2"
        ]
      },
      {
        "section": "dosage/34068-7/6",
        "title": "2.3 Recommended Dosage in Adults with Renal Impairment",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s6_c1",
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s6_c2"
        ]
      },
      {
        "section": "dosage/34068-7/7",
        "title": "2.4 Administration Instructions",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s7_c1"
        ]
      },
      {
        "section": "warnings/34070-3/9",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s9_c1"
        ]
      },
      {
        "section": "warnings/43685-7/11",
        "title": "5.1 Central Nervous System Adverse Reactions",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s11_c1"
        ]
      },
      {
        "section": "warnings/43685-7/12",
        "title": "5.2 Concurrent Gastric Malignancy",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s12_c1"
        ]
      },
      {
        "section": "labelling/34089-3/26",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s26_c1"
        ]
      },
      {
        "section": "warnings/34076-0/42",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s42_c1"
        ]
      },
      {
        "section": "labelling/51945-4/43",
        "title": "PACKAGE LABEL PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_446ca466-a43c-0401-e063-6394a90ac0d1_v1_s43_c1"
        ]
      }
    ]
  },
  {
    "product_name": "Amoxicillin",
    "setid": "2c395111-c9c1-483e-a542-58b935ede689",
    "version": 2,
    "effective_date": "2026-09-01",
    "fetched": "2026-11-16",
    "xml_sha256": "b28f89e64fe7b5b7a275d84c69bda94154939dca0f62667554404868007d7410",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2c395111-c9c1-483e-a542-58b935ede689&version=2",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s3_c1",
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s3_c2",
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s3_c3"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Dosage for Adults and Pediatric Patients Aged 3 Months (12 weeks) and Older",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s6_c1",
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s6_c2"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Dosage in Pediatric Patients Aged Less than 12 Weeks (3 months)",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Dosage for H. pylori Infection in Adults",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Dosage in Renal Impairment for Adults and Pediatric Patients Aged 3 Months and Older and Weight Greater than 40 kg",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s9_c1"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Anaphylactic Reactions",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Severe Cutaneous Adverse Reactions",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Clostridioides difficile -Associated Diarrhea (CDAD)",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Development of Drug-Resistant Bacteria",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Skin Rash in Patients with Mononucleosis",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s17_c1"
        ]
      },
      {
        "section": "labelling/34089-3/36",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s36_c1"
        ]
      },
      {
        "section": "warnings/34076-0/47",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s47_c1",
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s47_c2"
        ]
      },
      {
        "section": "labelling/51945-4/48",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 500 mg (30 Capsule Bottle)",
        "chunk_ids": [
          "dailymed_2c395111-c9c1-483e-a542-58b935ede689_v2_s48_c1"
        ]
      }
    ]
  },
  {
    "product_name": "METFORMIN HYDROCHLORIDE",
    "setid": "d8bd1779-d1c4-4dde-816d-ea72b37bb5cd",
    "version": 3,
    "effective_date": "2026-09-02",
    "fetched": "2026-11-16",
    "xml_sha256": "fcdd2f811c825f99de3455ecbba04f13db0fe3b4e879a99406ada55dd5ec50ef",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=d8bd1779-d1c4-4dde-816d-ea72b37bb5cd&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: LACTIC ACIDOSIS",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS & USAGE",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Adult Dosage",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Pediatric Dosage for Metformin Hydrochloride Tablets",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Recommendations for Use in Renal Impairment",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Discontinuation for Iodinated Contrast Imaging Procedures",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s8_c1"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.1 Lactic Acidosis",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s12_c1",
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s12_c2",
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s12_c3",
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s12_c4",
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s12_c5"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.2 Vitamin B12 Deficiency",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5. 3 Hypoglycemia with Concomitant Use with Insulin and Insulin Secretagogues",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.4 Macrovascular Outcomes",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s15_c1"
        ]
      },
      {
        "section": "labelling/34089-3/29",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s29_c1"
        ]
      },
      {
        "section": "warnings/34076-0/40",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s40_c1",
          "dailymed_d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3_s40_c2"
        ]
      }
    ]
  },
  {
    "product_name": "Atorvastatin Calcium",
    "setid": "a519e355-84f0-40d1-b586-e6e8eadb5b0f",
    "version": 3,
    "effective_date": "2026-09-17",
    "fetched": "2026-11-16",
    "xml_sha256": "92d8443a03132cf30fa3b24032db8b5cdf1d6b33a40f6b13e5889c51141739d6",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a519e355-84f0-40d1-b586-e6e8eadb5b0f&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Important Dosage Information",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.2 Recommended Dosage in Adult Patients",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.3 Recommended Dosage in Pediatric Patients 10 Years of Age and Older with HeFH",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.4 Recommended Dosage in Pediatric Patients 10 Years of Age and Older with HoFH",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.5 Dosage Modifications Due to Drug Interactions",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s8_c1"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.1 Myopathy and Rhabdomyolysis",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s12_c1",
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s12_c2"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.2 Immune-Mediated Necrotizing Myopathy",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.3 Hepatic Dysfunction",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.4 Increases in HbA1c and Fasting Serum Glucose Levels",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.5 Increased Risk of Hemorrhagic Stroke in Patients on Atorvastatin Calcium Tablets 80 mg with Recent Hemorrhagic Stroke",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s16_c1"
        ]
      },
      {
        "section": "labelling/34089-3/32",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s32_c1"
        ]
      },
      {
        "section": "warnings/34076-0/48",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s48_c1",
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s48_c2"
        ]
      },
      {
        "section": "labelling/51945-4/50",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3_s50_c1"
        ]
      }
    ]
  },
  {
    "product_name": "Levothyroxine Sodium",
    "setid": "1a2124e6-aea2-40dd-bb8d-52c58405a67e",
    "version": 1,
    "effective_date": "2026-10-01",
    "fetched": "2026-11-16",
    "xml_sha256": "ad00fde790816333b37c2d046aa645d16c1033160078b76ed40d1c5f4d0025c8",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1a2124e6-aea2-40dd-bb8d-52c58405a67e&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: NOT FOR TREATMENT OF OBESITY OR FOR WEIGHT LOSS",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Important Considerations for Dosing",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s7_c1",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s7_c2"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Recommended Dosage and Titration",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s8_c1",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s8_c2",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s8_c3",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s8_c4"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Monitoring TSH and/or Thyroxine (T4) Levels",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s9_c1",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s9_c2"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Serious Risks Related to Overtreatment or Undertreatment with Levothyroxine sodium tablets",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Cardiac Adverse Reactions in the Elderly and in Patients with Underlying Cardiovascular Disease",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Myxedema Coma",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Acute Adrenal Crisis in Patients with Concomitant Adrenal Insufficiency",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Worsening of Diabetic Control",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Decreased Bone Mineral Density Associated with Thyroid Hormone Over-Replacement",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s18_c1"
        ]
      },
      {
        "section": "labelling/34089-3/37",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s37_c1"
        ]
      },
      {
        "section": "warnings/34076-0/45",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s45_c1",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s45_c2",
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s45_c3"
        ]
      },
      {
        "section": "labelling/51945-4/46",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1_s46_c1"
        ]
      }
    ]
  },
  {
    "product_name": "ALBUTEROL SULFATE",
    "setid": "1810ff8e-d505-bf9c-e063-6394a90a6540",
    "version": 4,
    "effective_date": "2026-09-22",
    "fetched": "2026-11-16",
    "xml_sha256": "7982bd7ec1de5be710d5aaae536840a6396f1eeddd485735212ef5b786e4ecb1",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1810ff8e-d505-bf9c-e063-6394a90a6540&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/5",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s5_c1"
        ]
      },
      {
        "section": "warnings/34070-3/6",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s6_c1"
        ]
      },
      {
        "section": "warnings/34071-1/7",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s7_c1"
        ]
      },
      {
        "section": "warnings/34072-9/9",
        "title": "General",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s9_c1"
        ]
      },
      {
        "section": "warnings/34076-0/10",
        "title": "Information for Patients",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s10_c1"
        ]
      },
      {
        "section": "dosage/34068-7/19",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s19_c1"
        ]
      },
      {
        "section": "labelling/51945-4/23",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL-0.083% (2.5 mg/3 mL)-Pouch Label (1 Vial)",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s23_c1"
        ]
      },
      {
        "section": "labelling/51945-4/24",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL-0.083%(2.5 mg/3 mL)-Pouch Label (5 Vials)",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s24_c1"
        ]
      },
      {
        "section": "labelling/51945-4/25",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL-0.083%(2.5 mg/3 mL)-Container-Carton Label (25 Vials)",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s25_c1"
        ]
      },
      {
        "section": "labelling/51945-4/26",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL-0.083%(2.5 mg/3 mL)-Container-Carton Label (30 Vials)",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s26_c1"
        ]
      },
      {
        "section": "labelling/51945-4/27",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL-0.083%(2.5 mg/3 mL)-Container-Carton Label (60 Vials)",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s27_c1"
        ]
      },
      {
        "section": "labelling/51945-4/28",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL-0.083%(2.5 mg/3 mL)-Container-Carton Label (30 Individually Wrapped Vials)",
        "chunk_ids": [
          "dailymed_1810ff8e-d505-bf9c-e063-6394a90a6540_v4_s28_c1"
        ]
      }
    ]
  },
  {
    "setid": "c3099892-a8cd-4574-a6f9-041e59e2feae",
    "version": 11,
    "product_name": "Aspirin",
    "xml_sha256": "328a406aba96a3fe2298c173c93283b9ec75dcaf04a860f2b331bc434e9819b7",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c3099892-a8cd-4574-a6f9-041e59e2feae&version=11",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/4",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s4_c1"
        ]
      },
      {
        "section": "warnings/34071-1/5",
        "title": "Warnings",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s5_c1"
        ]
      },
      {
        "section": "warnings/50570-1/6",
        "title": "Do not use",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s6_c1"
        ]
      },
      {
        "section": "warnings/50569-3/7",
        "title": "Ask a doctor before use if",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s7_c1"
        ]
      },
      {
        "section": "warnings/50568-5/8",
        "title": "Ask a doctor or pharmacist before use if you are",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s8_c1"
        ]
      },
      {
        "section": "warnings/50566-9/9",
        "title": "Stop use and ask a doctor if",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s9_c1"
        ]
      },
      {
        "section": "warnings/53414-9/10",
        "title": "If pregnant or breast-feeding,",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s10_c1"
        ]
      },
      {
        "section": "warnings/50565-1/11",
        "title": "Keep out of reach of children.",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s11_c1"
        ]
      },
      {
        "section": "dosage/34068-7/12",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s12_c1"
        ]
      },
      {
        "section": "labelling/51945-4/16",
        "title": "Principal display panel",
        "chunk_ids": [
          "dailymed_c3099892-a8cd-4574-a6f9-041e59e2feae_v11_s16_c1"
        ]
      }
    ]
  },
  {
    "setid": "caa22bcb-6617-4724-8dcb-e63bfeef41a9",
    "version": 6,
    "product_name": "Berkley and Jensen Allergy Relief",
    "xml_sha256": "32ee7a60f484dabcee83c8dc3671ec41a25b21f94bcc7af40c6a968b0a784158",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=caa22bcb-6617-4724-8dcb-e63bfeef41a9&version=6",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/4",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s4_c1"
        ]
      },
      {
        "section": "warnings/50570-1/6",
        "title": "Do not use",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s6_c1"
        ]
      },
      {
        "section": "warnings/50569-3/7",
        "title": "Ask a doctor before use if you have",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s7_c1"
        ]
      },
      {
        "section": "warnings/50567-7/9",
        "title": "When using this product",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s9_c1"
        ]
      },
      {
        "section": "warnings/50566-9/10",
        "title": "Stop use and ask a doctor if",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s10_c1"
        ]
      },
      {
        "section": "warnings/53414-9/11",
        "title": "If pregnant or breast-feeding:",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s11_c1"
        ]
      },
      {
        "section": "warnings/50565-1/12",
        "title": "Keep out of reach of children.",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s12_c1"
        ]
      },
      {
        "section": "dosage/34068-7/13",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s13_c1"
        ]
      },
      {
        "section": "labelling/51945-4/17",
        "title": "Principal Display Panel",
        "chunk_ids": [
          "dailymed_caa22bcb-6617-4724-8dcb-e63bfeef41a9_v6_s17_c1"
        ]
      }
    ]
  },
  {
    "setid": "6286ea54-2350-49fc-8f37-4b979bd7f986",
    "version": 9,
    "product_name": "Losartan Potassium",
    "xml_sha256": "27257387e110c7c6814991cc7a99ab779447072896d274fd753abe5027cee8ab",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6286ea54-2350-49fc-8f37-4b979bd7f986&version=9",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: FETAL TOXICITY",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Hypertension",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s4_c1",
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s4_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Hypertensive Patients with Left Ventricular Hypertrophy",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Nephropathy in Type 2 Diabetic Patients",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Hypertension",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Hypertensive Patients with Left Ventricular Hypertrophy",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Nephropathy in Type 2 Diabetic Patients",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Dosage Modifications in Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Preparation of Suspension (for 200 mL of a 2.5 mg/mL suspension)",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s12_c1"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Hypotension in Volume - or Salt-Depleted Patients",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Renal Function Deterioration",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Hyperkalemia",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s19_c1"
        ]
      },
      {
        "section": "labelling/34089-3/37",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s37_c1"
        ]
      },
      {
        "section": "warnings/34076-0/49",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s49_c1"
        ]
      },
      {
        "section": "labelling/51945-4/51",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_6286ea54-2350-49fc-8f37-4b979bd7f986_v9_s51_c1"
        ]
      }
    ]
  },
  {
    "setid": "b17cd16b-8d0a-4cfa-bd48-2529983fcd12",
    "version": 7,
    "product_name": "Lisinopril",
    "xml_sha256": "382ff54d38bc4a74aa72a157cfd5838ee01b335a3381f21a9a646b95a3a3902b",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b17cd16b-8d0a-4cfa-bd48-2529983fcd12&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: FETAL TOXICITY",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Hypertension",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s4_c1",
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s4_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Heart Failure",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Reduction of Mortality in Acute Myocardial Infarction",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Hypertension",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s8_c1",
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Heart Failure",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Reduction of Mortality in Acute Myocardial Infarction",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Dose in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s11_c1"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 Angioedema and Anaphylactoid Reactions",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s16_c1",
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Hypotension",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.5 Hyperkalemia",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.6 Hepatic Failure",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.7 Risk of Allergic Reactions due to Tartrazine",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s21_c1"
        ]
      },
      {
        "section": "labelling/34089-3/42",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s42_c1"
        ]
      },
      {
        "section": "warnings/34076-0/54",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s54_c1",
          "dailymed_b17cd16b-8d0a-4cfa-bd48-2529983fcd12_v7_s54_c2"
        ]
      }
    ]
  },
  {
    "setid": "687ebdc4-6946-454e-8d46-3207488ccf32",
    "version": 13,
    "product_name": "Sertraline Hydrochloride",
    "xml_sha256": "4feb28bb1ad4959a064d6025cd381989baaac693cf784e49e70e237ee068424c",
    "effective_date": "2026-11-05",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=687ebdc4-6946-454e-8d46-3207488ccf32&version=13",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Dosage in Patients with MDD, OCD, PD, PTSD, and SAD",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Dosage in Patients with PMDD",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Screen for Bipolar Disorder Prior to Starting Sertraline Hydrochloride Tablets",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Dosage Modifications in Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Switching Patients to or from a Monoamine Oxidase Inhibitor Antidepressant",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.6 Discontinuation of Treatment with Sertraline Hydrochloride Tablets",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s10_c1"
        ]
      },
      {
        "section": "warnings/34070-3/12",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.1 Suicidal Thoughts and Behaviors in Pediatric and Young Adult Patients",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s14_c1",
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s14_c2"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.2 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s15_c1",
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s15_c2"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.3 Increased Risk of Bleeding",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.4 Activation of Mania or Hypomania",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.5 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.6 Seizures",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.7 Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.8 Hyponatremia",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.9 False-Positive Effects on Screening Tests for Benzodiazepines",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.10 QTc Prolongation",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.11 Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s24_c1"
        ]
      },
      {
        "section": "labelling/34089-3/43",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s43_c1"
        ]
      },
      {
        "section": "warnings/34076-0/58",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s58_c1",
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s58_c2",
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s58_c3"
        ]
      },
      {
        "section": "labelling/51945-4/60",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_687ebdc4-6946-454e-8d46-3207488ccf32_v13_s60_c1"
        ]
      }
    ]
  },
  {
    "setid": "318fdf0d-c03a-4b48-a380-b7bb630363fb",
    "version": 7,
    "product_name": "PredniSONE",
    "xml_sha256": "28921aeb11bde4a33e48dd74f9505ce7467230c05dd8b7e61ac286da7df224e5",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=318fdf0d-c03a-4b48-a380-b7bb630363fb&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/5",
        "title": "INDICATIONS",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1. Endocrine Disorders",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "2. Rheumatic Disorders",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "3. Collagen Diseases",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s8_c1"
        ]
      },
      {
        "section": "labelling/42229-5/9",
        "title": "4. Dermatologic Diseases",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s9_c1"
        ]
      },
      {
        "section": "labelling/42229-5/10",
        "title": "5. Allergic States",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s10_c1"
        ]
      },
      {
        "section": "labelling/42229-5/11",
        "title": "6. Ophthalmic Diseases",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s11_c1"
        ]
      },
      {
        "section": "labelling/42229-5/12",
        "title": "7. Respiratory Diseases",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s12_c1"
        ]
      },
      {
        "section": "labelling/42229-5/13",
        "title": "8. Hematologic Disorders",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s13_c1"
        ]
      },
      {
        "section": "labelling/42229-5/14",
        "title": "9. Neoplastic Diseases",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s14_c1"
        ]
      },
      {
        "section": "labelling/42229-5/15",
        "title": "10. Edematous States",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s15_c1"
        ]
      },
      {
        "section": "labelling/42229-5/16",
        "title": "11. Gastrointestinal Diseases",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s16_c1"
        ]
      },
      {
        "section": "labelling/42229-5/17",
        "title": "12. Nervous System",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s17_c1"
        ]
      },
      {
        "section": "labelling/42229-5/18",
        "title": "13. Miscellaneous",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s18_c1"
        ]
      },
      {
        "section": "warnings/34070-3/19",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s19_c1"
        ]
      },
      {
        "section": "warnings/34071-1/20",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s20_c1",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s20_c2",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s20_c3",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s20_c4"
        ]
      },
      {
        "section": "warnings/34072-9/22",
        "title": "General Precautions",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s22_c1",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s22_c2"
        ]
      },
      {
        "section": "dosage/34068-7/33",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s33_c1",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s33_c2"
        ]
      },
      {
        "section": "dosage/42229-5/34",
        "title": "Multiple Sclerosis",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s34_c1"
        ]
      },
      {
        "section": "dosage/42229-5/35",
        "title": "ADT \u00ae (Alternate Day Therapy)",
        "chunk_ids": [
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s35_c1",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s35_c2",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s35_c3",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s35_c4",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s35_c5",
          "dailymed_318fdf0d-c03a-4b48-a380-b7bb630363fb_v7_s35_c6"
        ]
      }
    ]
  },
  {
    "setid": "3f1535d9-6c3b-4355-a2ef-eb6ee33054a5",
    "version": 1,
    "product_name": "Gabapentin",
    "xml_sha256": "8fb466058aac6299190fb9081ae6fcc5b349aba32a294a2db446200605bc0fa9",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3f1535d9-6c3b-4355-a2ef-eb6ee33054a5&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Dosage for Postherpetic Neuralgia",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Dosage for Epilepsy with Partial Onset Seizures",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Dosage Adjustment in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s7_c1",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s7_c2"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Dosage in Elderly",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Administration Information",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s9_c1"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)/Multiorgan Hypersensitivity",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Anaphylaxis and Angioedema",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Effects on Driving and Operating Heavy Machinery",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Somnolence/Sedation and Dizziness",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s16_c1",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Suicidal Behavior and Ideation",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s17_c1",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s17_c2",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s17_c3",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s17_c4"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Increased Risk of Seizures and Other Adverse Reactions with Abrupt or Rapid Discontinuation",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.7 Status Epilepticus",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.8 Respiratory Depression",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.9 Neuropsychiatric Adverse Reactions (Pediatric Patients 3 to 12 Years of Age)",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.10 Tumorigenic Potential",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s22_c1"
        ]
      },
      {
        "section": "labelling/34089-3/42",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s42_c1"
        ]
      },
      {
        "section": "warnings/34076-0/52",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s52_c1",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s52_c2",
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s52_c3"
        ]
      },
      {
        "section": "labelling/51945-4/54",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_3f1535d9-6c3b-4355-a2ef-eb6ee33054a5_v1_s54_c1"
        ]
      }
    ]
  },
  {
    "setid": "de803217-6d32-4ef8-afe7-02462f37bf0c",
    "version": 3,
    "product_name": "Escitalopram",
    "xml_sha256": "70b7dbaf471e9d43870736781c6b595db503902b417c4fc90db7fe5a3e592c95",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=de803217-6d32-4ef8-afe7-02462f37bf0c&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNINGS: SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.3 Administration Information",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.4 Screen for Bipolar Disorder Prior to Starting Escitalopram Tablets",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.5 Recommended Dosage for Specific Populations",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.6 Discontinuation of Treatment with Escitalopram Tablets",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.7 Switching Patients to or from a Monoamine Oxidase Inhibitor (MAOI) Antidepressant",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s15_c1"
        ]
      },
      {
        "section": "warnings/34070-3/17",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.2 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s20_c1",
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s20_c2"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.3 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.4 Seizures",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.5 Activation of Mania or Hypomania",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.6 Hyponatremia",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.7 Increased Risk of Bleeding",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.8 Interference with Cognitive and Motor Performance",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.9 Angle Closure Glaucoma",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.10 Use in Patients with Concomitant Illness",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.11 Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s29_c1"
        ]
      },
      {
        "section": "labelling/34089-3/66",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s66_c1"
        ]
      },
      {
        "section": "warnings/34076-0/81",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s81_c1",
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s81_c2",
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s81_c3",
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s81_c4"
        ]
      },
      {
        "section": "labelling/51945-4/93",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 10 mg",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s93_c1"
        ]
      },
      {
        "section": "labelling/51945-4/94",
        "title": "Package/Label Display Panel \u2013 Blister \u2013 10 mg",
        "chunk_ids": [
          "dailymed_de803217-6d32-4ef8-afe7-02462f37bf0c_v3_s94_c1"
        ]
      }
    ]
  },
  {
    "setid": "d889c656-f024-4e18-b83c-68a7707945d8",
    "version": 1,
    "product_name": "Amlodipine Besylate",
    "xml_sha256": "75fc6cad90a1290f8c22436a93c0b23c9ad9cd22db35f560758020efea924e1d",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=d889c656-f024-4e18-b83c-68a7707945d8&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Hypertension",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s3_c1",
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s3_c2"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Coronary Artery Disease (CAD)",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Adults",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Children",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s7_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Hypotension",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Increased Angina or Myocardial Infarction",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Patients with Hepatic Failure",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s15_c1"
        ]
      },
      {
        "section": "labelling/34089-3/28",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_d889c656-f024-4e18-b83c-68a7707945d8_v1_s28_c1"
        ]
      }
    ]
  },
  {
    "setid": "a569ba80-ffea-40b2-9fbe-a42810b1fccb",
    "version": 34,
    "product_name": "Doxycycline Hyclate",
    "xml_sha256": "11426d1bb985b72dedcbab87f7c74e1f5b47ded459f223acf640ca2135d6f184",
    "effective_date": "2025-06-26",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a569ba80-ffea-40b2-9fbe-a42810b1fccb&version=34",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/12",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s12_c1"
        ]
      },
      {
        "section": "labelling/42229-5/13",
        "title": "Treatment :",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s13_c1",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s13_c2",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s13_c3"
        ]
      },
      {
        "section": "labelling/42229-5/14",
        "title": "Prophylaxis:",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s14_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s15_c1"
        ]
      },
      {
        "section": "warnings/34071-1/16",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s16_c1",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s16_c2",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s16_c3",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s16_c4"
        ]
      },
      {
        "section": "warnings/34072-9/18",
        "title": "General",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s18_c1"
        ]
      },
      {
        "section": "warnings/34076-0/19",
        "title": "Information For Patients",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s19_c1",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s19_c2",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s19_c3"
        ]
      },
      {
        "section": "dosage/34068-7/30",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s30_c1",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s30_c2",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s30_c3",
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s30_c4"
        ]
      },
      {
        "section": "labelling/51945-4/34",
        "title": "Principal Display Panel",
        "chunk_ids": [
          "dailymed_a569ba80-ffea-40b2-9fbe-a42810b1fccb_v34_s34_c1"
        ]
      }
    ]
  },
  {
    "setid": "15e4c3a3-7d64-471e-bfdf-6156731e24aa",
    "version": 7,
    "product_name": "FUROSEMIDE",
    "xml_sha256": "5f1094cdfad9d14741ff8386a16e7660f2c088848d8ee513622ed1c96ac4a016",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=15e4c3a3-7d64-471e-bfdf-6156731e24aa&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "BOXED WARNING",
        "chunk_ids": [
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s2_c1"
        ]
      },
      {
        "section": "labelling/34089-3/3",
        "title": "\ufeffDESCRIPTION",
        "chunk_ids": [
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/5",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s5_c1"
        ]
      },
      {
        "section": "warnings/34070-3/6",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s6_c1"
        ]
      },
      {
        "section": "warnings/34071-1/7",
        "title": "\ufeffWARNINGS",
        "chunk_ids": [
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s7_c1",
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s7_c2"
        ]
      },
      {
        "section": "dosage/34068-7/11",
        "title": "\ufeffDOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s11_c1",
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s11_c2",
          "dailymed_15e4c3a3-7d64-471e-bfdf-6156731e24aa_v7_s11_c3"
        ]
      }
    ]
  },
  {
    "setid": "307aa67f-53b9-4c60-a328-091bbf6338d4",
    "version": 9,
    "product_name": "Naproxen",
    "xml_sha256": "f0ab799964b7346f9f3a3a6241958fdfb03dd0e5e3e0e4a2ce89daee5c473333",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=307aa67f-53b9-4c60-a328-091bbf6338d4&version=9",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: RISK OF SERIOUS CARDIOVASCULAR AND GASTROINTESTINAL EVENTS",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 General Dosing Instructions",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Rheumatoid Arthritis, Osteoarthritis and Ankylosing Spondylitis",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Polyarticular Juvenile Idiopathic Arthritis",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Management of Pain, Primary Dysmenorrhea, and Acute Tendonitis and Bursitis",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.5 Acute Gout",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.6 Non-Interchangeability with Other Formulations of Naproxen",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s11_c1"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Cardiovascular Thrombotic Events",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s15_c1",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s15_c2",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s15_c3"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 Gastrointestinal Bleeding, Ulceration, and Perforation",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s16_c1",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Hypertension",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.5 Heart Failure and Edema",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.6 Renal Toxicity and Hyperkalemia",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s20_c1",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s20_c2"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.7 Anaphylactic Reactions",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.8 Exacerbation of Asthma Related to Aspirin Sensitivity",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.9 Serious Skin Reactions",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.10 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.11 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s25_c1",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s25_c2"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.12 Hematologic Toxicity",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.13 Masking of Inflammation and Fever",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.14 Long-Term Use and Laboratory Monitoring",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s28_c1"
        ]
      },
      {
        "section": "labelling/34089-3/42",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s42_c1"
        ]
      },
      {
        "section": "warnings/34076-0/51",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s51_c1",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s51_c2",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s51_c3",
          "dailymed_307aa67f-53b9-4c60-a328-091bbf6338d4_v9_s51_c4"
        ]
      }
    ]
  },
  {
    "setid": "b4831735-6731-473a-b4f0-1f4a67aa7120",
    "version": 8,
    "product_name": "Fluoxetine",
    "xml_sha256": "2f0411631fc25b69f995b1c499c17f671a9860d5fcf176255840addd2a4d1a07",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b4831735-6731-473a-b4f0-1f4a67aa7120&version=8",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Major Depressive Disorder",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s6_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s6_c2"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Obsessive Compulsive Disorder",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s7_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s7_c2"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Bulimia Nervosa",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Panic Disorder",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.5 Fluoxetine and Olanzapine in Combination: Depressive Episodes Associated with Bipolar I Disorder",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s10_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.6 Fluoxetine and Olanzapine in Combination: Treatment Resistant Depression",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s11_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s11_c2"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.7 Dosing in Specific Populations",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s12_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s12_c2"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.8 Discontinuation of Treatment",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.9 Switching a Patient To or From a Monoamine Oxidase Inhibitor (MAOI) Intended to Treat Psychiatric Disorders",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.10 Use of Fluoxetine with Other MAOIs such as Linezolid or Methylene Blue",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s15_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s15_c2"
        ]
      },
      {
        "section": "warnings/34070-3/17",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "4.1 Monoamine Oxidase Inhibitors (MAOIs)",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "4.2 Other Contraindications",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s19_c1"
        ]
      },
      {
        "section": "warnings/43685-7/20",
        "title": "5 WARNINGS AND PRECAUTIONS",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.1 Suicidal Thoughts and Behaviors in Children, Adolescents, and Young Adults",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s21_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s21_c2",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s21_c3",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s21_c4",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s21_c5"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.2 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s22_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s22_c2"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.3 Allergic Reactions and Rash",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s23_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s23_c2"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.4 Screening Patients for Bipolar Disorder and Monitoring for Mania/Hypomania",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s24_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s24_c2"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.5 Seizures",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.6 Altered Appetite and Weight",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.7 Increased Risk of Bleeding",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.8 Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.9 Hyponatremia",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.10 Anxiety and Insomnia",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.11 QT Prolongation",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s31_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s31_c2"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.12 Use in Patients with Concomitant Illness",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s32_c1"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.13 Potential for Cognitive and Motor Impairment",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.14 Long Elimination Half-Life",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.15 Discontinuation Adverse Reactions",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s35_c1"
        ]
      },
      {
        "section": "warnings/42229-5/36",
        "title": "5.16 Fluoxetine and Olanzapine in Combination",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s36_c1"
        ]
      },
      {
        "section": "warnings/42229-5/37",
        "title": "5.17 Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s37_c1"
        ]
      },
      {
        "section": "labelling/34089-3/59",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s59_c1"
        ]
      },
      {
        "section": "warnings/34076-0/76",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c1",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c2",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c3",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c4",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c5",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c6",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c7",
          "dailymed_b4831735-6731-473a-b4f0-1f4a67aa7120_v8_s76_c8"
        ]
      }
    ]
  },
  {
    "setid": "a6b5edf2-1ef8-46b7-977a-8c303900f3f0",
    "version": 17,
    "product_name": "Cephalexin",
    "xml_sha256": "0a71b5fe534fee57f24b34a90927a8daaf79cbf1d78fc71eadb58515808c742a",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a6b5edf2-1ef8-46b7-977a-8c303900f3f0&version=17",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Respiratory Tract Infections",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Otitis Media",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Skin and Skin Structure Infections",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.4 Bone Infections",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.5 Genitourinary Tract Infections",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.6 Usage",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.1 Adults and Pediatric Patients at Least 15 Years of Age",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.2 Pediatric Patients (over 1 year of age)",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.3 Dosage Adjustments in Adult and Pediatric Patients at Least 15 Years of Age with Renal Impairment",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s12_c1"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Clostridium difficile-Associated Diarrhea",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Direct Coombs\u2019 Test Seroconversion",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Seizure Potential",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.5 Prolonged Prothrombin Time",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.6 Development of Drug-Resistant Bacteria",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s21_c1"
        ]
      },
      {
        "section": "labelling/34089-3/35",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s35_c1"
        ]
      },
      {
        "section": "warnings/34076-0/43",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s43_c1",
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s43_c2"
        ]
      },
      {
        "section": "labelling/51945-4/44",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_a6b5edf2-1ef8-46b7-977a-8c303900f3f0_v17_s44_c1"
        ]
      }
    ]
  },
  {
    "setid": "4cd07a3c-9673-4aa0-b76a-d79df2399ee1",
    "version": 11,
    "product_name": "Clopidogrel",
    "xml_sha256": "89f0772ee7d379ee19653fc1454814047691880e55ea15eade68bd5fe55ff7a8",
    "effective_date": "2026-11-11",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=4cd07a3c-9673-4aa0-b76a-d79df2399ee1&version=11",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/42229-5/3",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.1 Acute Coronary Syndrome (ACS)",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Recent MI, Recent Stroke, or Established Peripheral Arterial Disease",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Acute Coronary Syndrome",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Recent MI, Recent Stroke, or Established Peripheral Arterial Disease",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "4.1 Active Bleeding",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "4.2 Hypersensitivity",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Diminished Antiplatelet Activity in Patients with Impaired CYP2C19 Function",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 General Risk of Bleeding",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Discontinuation of Clopidogrel Tablets",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Thrombotic Thrombocytopenic Purpura (TTP)",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s18_c1"
        ]
      },
      {
        "section": "warnings/43685-7/19",
        "title": "5.5 Cross-Reactivity among Thienopyridines",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s19_c1"
        ]
      },
      {
        "section": "labelling/34089-3/40",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s40_c1",
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s40_c2"
        ]
      },
      {
        "section": "warnings/34076-0/53",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s53_c1",
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s53_c2"
        ]
      },
      {
        "section": "labelling/51945-4/55",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_4cd07a3c-9673-4aa0-b76a-d79df2399ee1_v11_s55_c1"
        ]
      }
    ]
  },
  {
    "setid": "3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b",
    "version": 15,
    "product_name": "Protonix I.V.",
    "xml_sha256": "3971881d35861a5c2d1b2e83df9b89e8c45137cc4cfdc5dff51828116e8f9a78",
    "effective_date": "2026-11-06",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b&version=15",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Recommended Dosage for GERD Associated with a History of EE",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s5_c1",
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s5_c2"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Preparation and Administration Instructions for GERD Associated with a History of EE",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s8_c1",
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.5 Compatibility Information",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s14_c1"
        ]
      },
      {
        "section": "warnings/34070-3/16",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.1 Presence of Gastric Malignancy",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.2 Injection Site Reactions",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.3 Potential for Exacerbation of Zinc Deficiency",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.4 Acute Tubulointerstitial Nephritis",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.5 Clostridioides difficile- Associated Diarrhea",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.6 Bone Fracture",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.7 Severe Cutaneous Adverse Reactions",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.8 Cutaneous and Systemic Lupus Erythematosus",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s25_c1",
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s25_c2"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.9 Hepatic Effects",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.10 Hypomagnesemia and Mineral Metabolism",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.11 Fundic Gland Polyps",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.12 Interference with Investigations for Neuroendocrine Tumors",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.13 Interference with Urine Screen for THC",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.14 Concomitant Use of PROTONIX I.V. with Methotrexate",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s31_c1"
        ]
      },
      {
        "section": "labelling/34089-3/51",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s51_c1"
        ]
      },
      {
        "section": "warnings/42229-5/86",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s86_c1"
        ]
      },
      {
        "section": "warnings/42229-5/87",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s87_c1"
        ]
      },
      {
        "section": "warnings/42229-5/88",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s88_c1"
        ]
      },
      {
        "section": "labelling/51945-4/90",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b_v15_s90_c1"
        ]
      }
    ]
  },
  {
    "setid": "176b400b-2b4e-481d-b6c4-0f99e4c711c3",
    "version": 3,
    "product_name": "valsartan and hydrochlorothiazide",
    "xml_sha256": "6521c7736cfb90f02a3ab2c67b324720b11efb168bd1e4242013429676cf1003",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=176b400b-2b4e-481d-b6c4-0f99e4c711c3&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: FETAL TOXICITY",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s3_c1",
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s3_c2",
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s3_c3",
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s3_c4"
        ]
      },
      {
        "section": "dosage/unknown/5",
        "title": "2.1 General Considerations",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s5_c1"
        ]
      },
      {
        "section": "dosage/unknown/6",
        "title": "2.2 Add-On Therapy",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s6_c1"
        ]
      },
      {
        "section": "dosage/unknown/7",
        "title": "2.3 Replacement Therapy",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s7_c1"
        ]
      },
      {
        "section": "dosage/unknown/8",
        "title": "2.4 Initial Therapy",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s8_c1"
        ]
      },
      {
        "section": "dosage/unknown/9",
        "title": "2.5 Use with Other Antihypertensive Drugs",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s9_c1"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s11_c1"
        ]
      },
      {
        "section": "warnings/unknown/13",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s13_c1"
        ]
      },
      {
        "section": "warnings/unknown/14",
        "title": "5.2 Hypotension in Volume- and/or Salt-Depleted Patients",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s14_c1"
        ]
      },
      {
        "section": "warnings/unknown/15",
        "title": "5.3 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s15_c1"
        ]
      },
      {
        "section": "warnings/unknown/16",
        "title": "5.4 Hypersensitivity Reaction",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s16_c1"
        ]
      },
      {
        "section": "warnings/unknown/17",
        "title": "5.5 Systemic Lupus Erythematosus",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s17_c1"
        ]
      },
      {
        "section": "warnings/unknown/18",
        "title": "5.6 Lithium Interaction",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s18_c1"
        ]
      },
      {
        "section": "warnings/unknown/19",
        "title": "5.7 Potassium Abnormalities",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s19_c1"
        ]
      },
      {
        "section": "warnings/unknown/20",
        "title": "5.8 Acute Myopia and Secondary Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s20_c1"
        ]
      },
      {
        "section": "warnings/unknown/21",
        "title": "5.9 Metabolic Disturbances",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s21_c1"
        ]
      },
      {
        "section": "labelling/34089-3/34",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s34_c1",
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s34_c2"
        ]
      },
      {
        "section": "warnings/34076-0/45",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s45_c1",
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s45_c2"
        ]
      },
      {
        "section": "labelling/51945-4/49",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_176b400b-2b4e-481d-b6c4-0f99e4c711c3_v3_s49_c1"
        ]
      }
    ]
  },
  {
    "setid": "682dd8b8-fc6e-47c5-95b7-82d7ad96b750",
    "version": 14,
    "product_name": "Allopurinol",
    "xml_sha256": "c6c9c576d1c4e7695bfd3da18cdbfb1b828b8c94720ea3d230dd0233955e137e",
    "effective_date": "2026-11-05",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=682dd8b8-fc6e-47c5-95b7-82d7ad96b750&version=14",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Recommended Testing Prior to Treatment Initiation",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.2 Recommended Prophylaxis for Gout Flares",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.3 Recommended Dosage for Gout",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s6_c1",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s6_c2",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s6_c3"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.4 Recommended Dosage for Hyperuricemia Associated with Cancer Therapy",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.5 Recommended Dosage for Management of Recurrent Calcium Oxalate Calculi in Hyperuricosuric Patients",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.6 Recommended Dosage in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s9_c1",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s9_c2",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s9_c3"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Skin Rash and Hypersensitivity",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s13_c1",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s13_c2"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Gout Flares",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Nephrotoxicity",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s15_c1",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s15_c2"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Myelosuppression",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Potential Effect on Driving and Use of Machinery",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s18_c1"
        ]
      },
      {
        "section": "labelling/34089-3/29",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s29_c1"
        ]
      },
      {
        "section": "warnings/34076-0/38",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s38_c1",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s38_c2",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s38_c3",
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s38_c4"
        ]
      },
      {
        "section": "labelling/51945-4/39",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_682dd8b8-fc6e-47c5-95b7-82d7ad96b750_v14_s39_c1"
        ]
      }
    ]
  },
  {
    "setid": "c9ec1996-6a54-4622-b8a6-57dea49f6b35",
    "version": 23,
    "product_name": "Montelukast Sodium",
    "xml_sha256": "a7d9755c49e1db68096737515caae41814568a2432606a19364a4138d543ae18",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c9ec1996-6a54-4622-b8a6-57dea49f6b35&version=23",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: SERIOUS NEUROPSYCHIATRIC EVENTS",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s2_c1",
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s2_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.1 Asthma",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Exercise-Induced Bronchoconstriction (EIB)",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.3 Allergic Rhinitis",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.4 Limitations of Use",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.1 Asthma",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.2 Exercise-Induced Bronchoconstriction (EIB)",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.3 Allergic Rhinitis",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.4 Asthma and Allergic Rhinitis",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s13_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.1 Neuropsychiatric Events",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s17_c1",
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s17_c2"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.2 Acute Asthma",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.3 Concomitant Corticosteroid Use",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.4 Aspirin Sensitivity",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.5 Eosinophilic Conditions",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s21_c1"
        ]
      },
      {
        "section": "labelling/34089-3/34",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/47",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s47_c1",
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s47_c2"
        ]
      },
      {
        "section": "warnings/42229-5/48",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s48_c1"
        ]
      },
      {
        "section": "labelling/51945-4/50",
        "title": "",
        "chunk_ids": [
          "dailymed_c9ec1996-6a54-4622-b8a6-57dea49f6b35_v23_s50_c1"
        ]
      }
    ]
  },
  {
    "setid": "02797697-300a-43db-92cf-9b78f08626be",
    "version": 7,
    "product_name": "Rosuvastatin Calcium",
    "xml_sha256": "277e1d0861b0115d3cccb0d6e47c8cb12ed1ee5d5fc330a40ed0cde084b643cc",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=02797697-300a-43db-92cf-9b78f08626be&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s3_c1"
        ]
      },
      {
        "section": "dosage/unknown/5",
        "title": "2.1 General Dosage and Administration Information",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s5_c1"
        ]
      },
      {
        "section": "dosage/unknown/6",
        "title": "2.2 Recommended Dosage in Adult Patients",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s6_c1"
        ]
      },
      {
        "section": "dosage/unknown/7",
        "title": "2.3 Recommended Dosage in Pediatric Patients",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s7_c1"
        ]
      },
      {
        "section": "dosage/unknown/8",
        "title": "2.4 Dosing in Asian Patients",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s8_c1"
        ]
      },
      {
        "section": "dosage/unknown/9",
        "title": "2.5 Recommended Dosage in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s9_c1"
        ]
      },
      {
        "section": "dosage/unknown/10",
        "title": "2.6 Dosage Modifications Due to Drug Interactions",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s10_c1",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s10_c2"
        ]
      },
      {
        "section": "warnings/34070-3/12",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s12_c1"
        ]
      },
      {
        "section": "warnings/unknown/14",
        "title": "5.1 Myopathy and Rhabdomyolysis",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s14_c1",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s14_c2"
        ]
      },
      {
        "section": "warnings/unknown/15",
        "title": "5.2 Immune-Mediated Necrotizing Myopathy",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s15_c1"
        ]
      },
      {
        "section": "warnings/unknown/16",
        "title": "5.3 Hepatic Dysfunction",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s16_c1"
        ]
      },
      {
        "section": "warnings/unknown/17",
        "title": "5.4 Proteinuria and Hematuria",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s17_c1"
        ]
      },
      {
        "section": "warnings/unknown/18",
        "title": "5.5 Increases in HbA1c and Fasting Serum Glucose Levels",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s18_c1"
        ]
      },
      {
        "section": "labelling/34089-3/35",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s35_c1"
        ]
      },
      {
        "section": "warnings/34076-0/45",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c1",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c2",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c3",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c4",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c5",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c6",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c7",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c8",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c9",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c10",
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s45_c11"
        ]
      },
      {
        "section": "labelling/51945-4/46",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_02797697-300a-43db-92cf-9b78f08626be_v7_s46_c1"
        ]
      }
    ]
  },
  {
    "setid": "2ad0606c-7a90-44bd-a75d-d256de30fbcf",
    "version": 7,
    "product_name": "Metoprolol Tartrate",
    "xml_sha256": "2789e37e4ba975518eb4f2e44b5b7fba618565bb0908e74ce12c2bf5b4ea77b8",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2ad0606c-7a90-44bd-a75d-d256de30fbcf&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Hypertension",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s3_c1",
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s3_c2"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Angina Pectoris",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Myocardial Infarction",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.1 Hypertension",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.2 Angina Pectoris",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.3 Myocardial Infarction",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s9_c1"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Abrupt Cessation of Therapy",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Heart Failure",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Bronchospastic Disease",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Pheochromocytoma",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Major Surgery",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Hypoglycemia",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.7 Thyrotoxicosis",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.8 Risk of Anaphylactic Reaction",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.9 Peripheral Vascular Disease",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s21_c1"
        ]
      },
      {
        "section": "labelling/34089-3/39",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s39_c1"
        ]
      },
      {
        "section": "warnings/34076-0/52",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_2ad0606c-7a90-44bd-a75d-d256de30fbcf_v7_s52_c1"
        ]
      }
    ]
  },
  {
    "setid": "fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75",
    "version": 2,
    "product_name": "Bupropion Hydrochloride",
    "xml_sha256": "1c731785abcc0a664bf971312dca4078641785da4e973dce4201648ef3864209",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75&version=2",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 General Instructions for Use",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s5_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s5_c2"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Dose Adjustment in Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Dose Adjustment in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Switching a Patient to or from a Monoamine Oxidase Inhibitor (MAOI) Antidepressant",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Use of Bupropion Hydrochloride Tablets with Reversible MAOIs Such as Linezolid or Methylene Blue",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s9_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s9_c2"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s11_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s11_c2"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Suicidal Thoughts and Behaviors in Children, Adolescents, and Young Adults",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s13_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s13_c2",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s13_c3",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s13_c4",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s13_c5"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Neuropsychiatric Adverse Events and Suicide Risk in Smoking Cessation Treatment",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s14_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s14_c2"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Seizure",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s15_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s15_c2"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Hypertension",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s16_c1",
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Activation of Mania/Hypomania",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Psychosis and Other Neuropsychiatric Reactions",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.7 Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.8 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s20_c1"
        ]
      },
      {
        "section": "labelling/34089-3/45",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s45_c1"
        ]
      },
      {
        "section": "labelling/51945-4/55",
        "title": "PRINCIPAL DISPLAY LABEL - 75 mg BOTTLE LABEL",
        "chunk_ids": [
          "dailymed_fbb587fa-75c0-4f4d-8eaf-f0e7ba8b5c75_v2_s55_c1"
        ]
      }
    ]
  },
  {
    "setid": "5bacc909-6b02-4815-85ef-55fd25b1b1f7",
    "version": 9,
    "product_name": "Hydrochlorothiazide",
    "xml_sha256": "0a06c74032ffd98124a51275087480b2f5c03c834ef6056f455c3991b00b55a1",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5bacc909-6b02-4815-85ef-55fd25b1b1f7&version=9",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/8",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s8_c1",
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s8_c2"
        ]
      },
      {
        "section": "warnings/34070-3/9",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s9_c1"
        ]
      },
      {
        "section": "warnings/34071-1/10",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s10_c1"
        ]
      },
      {
        "section": "warnings/34076-0/12",
        "title": "Information for Patients:",
        "chunk_ids": [
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s12_c1"
        ]
      },
      {
        "section": "dosage/34068-7/20",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_5bacc909-6b02-4815-85ef-55fd25b1b1f7_v9_s20_c1"
        ]
      }
    ]
  },
  {
    "setid": "602d3866-7ff4-71aa-e063-6294a90a9521",
    "version": 1,
    "product_name": "Trazodone HCL",
    "xml_sha256": "704237cbfce91b6baa1a1e533d5a444340dd18738164dbe6b8c98d7d32bf75ae",
    "effective_date": "2026-11-13",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=602d3866-7ff4-71aa-e063-6294a90a9521&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s3_c1"
        ]
      },
      {
        "section": "dosage/34068-7/4",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s4_c1",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s4_c2"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s5_c1"
        ]
      },
      {
        "section": "warnings/43685-7/6",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c1",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c2",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c3",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c4",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c5",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c6",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c7",
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s6_c8"
        ]
      },
      {
        "section": "labelling/34089-3/12",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_602d3866-7ff4-71aa-e063-6294a90a9521_v1_s12_c1"
        ]
      }
    ]
  },
  {
    "setid": "f6b6aeab-bedd-4254-8811-4f65cf8a351f",
    "version": 23,
    "product_name": "Tamsulosin Hydrochloride",
    "xml_sha256": "923012e910d87e2c6deaba01ad00ef3f5211eb70b16ad6ebafc69f39a79cb65e",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=f6b6aeab-bedd-4254-8811-4f65cf8a351f&version=23",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s2_c1"
        ]
      },
      {
        "section": "dosage/34068-7/3",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s3_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s5_c1"
        ]
      },
      {
        "section": "warnings/42229-5/7",
        "title": "5.1 Orthostasis",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s7_c1"
        ]
      },
      {
        "section": "warnings/42229-5/8",
        "title": "5.2 Drug Interactions",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s8_c1",
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s8_c2"
        ]
      },
      {
        "section": "warnings/42229-5/9",
        "title": "5.3 Priapism",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.4 Screening for Prostate Cancer",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.5 Intraoperative Floppy Iris Syndrome",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s11_c1",
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s11_c2"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.6 Sulfa Allergy",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s12_c1"
        ]
      },
      {
        "section": "labelling/34089-3/33",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s33_c1"
        ]
      },
      {
        "section": "warnings/34076-0/42",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s42_c1",
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s42_c2"
        ]
      },
      {
        "section": "labelling/51945-4/44",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 0.4 mg Blister Carton (3 x 10 Unit-dose)",
        "chunk_ids": [
          "dailymed_f6b6aeab-bedd-4254-8811-4f65cf8a351f_v23_s44_c1"
        ]
      }
    ]
  },
  {
    "setid": "41a133ef-e461-48ad-8221-b735bdd0ec25",
    "version": 5,
    "product_name": "ELIQUIS",
    "xml_sha256": "59c50ea5d9f96b0ae42e634154d03bdce8f9885b8de8b182f4039e66b8b12c40",
    "effective_date": "2026-09-24",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=41a133ef-e461-48ad-8221-b735bdd0ec25&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: (A) PREMATURE DISCONTINUATION OF ELIQUIS INCREASES THE RISK OF THROMBOTIC EVENTS (B) SPINAL/EPIDURAL HEMATOMA",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s2_c1",
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s2_c2"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Reduction of Risk of Stroke and Systemic Embolism in Nonvalvular Atrial Fibrillation",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Prophylaxis of Deep Vein Thrombosis Following Hip or Knee Replacement Surgery",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Treatment of Deep Vein Thrombosis",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.4 Treatment of Pulmonary Embolism",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.5 Reduction in the Risk of Recurrence of DVT and PE",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "Reduction of Risk of Stroke and Systemic Embolism in Patients with Nonvalvular Atrial Fibrillation",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "Prophylaxis of Deep Vein Thrombosis Following Hip or Knee Replacement Surgery",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "Treatment of DVT and PE",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "Reduction in the Risk of Recurrence of DVT and PE",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s14_c1"
        ]
      },
      {
        "section": "dosage/34068-7/15",
        "title": "2.2 Missed Dose",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s15_c1"
        ]
      },
      {
        "section": "dosage/34068-7/16",
        "title": "2.3 Temporary Interruption for Surgery and Other Interventions",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s16_c1"
        ]
      },
      {
        "section": "dosage/34068-7/17",
        "title": "2.4 Converting from or to ELIQUIS",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s17_c1"
        ]
      },
      {
        "section": "dosage/34068-7/18",
        "title": "2.5 Combined P-gp and Strong CYP3A4 Inhibitors",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s18_c1"
        ]
      },
      {
        "section": "dosage/42229-5/19",
        "title": "2.6 Administration Options",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s19_c1"
        ]
      },
      {
        "section": "warnings/34070-3/21",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s21_c1"
        ]
      },
      {
        "section": "warnings/43685-7/23",
        "title": "5.1 Increased Risk of Thrombotic Events after Premature Discontinuation",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s23_c1"
        ]
      },
      {
        "section": "warnings/43685-7/24",
        "title": "5.2 Bleeding",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "Reversal of Anticoagulant Effect",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.3 Spinal/Epidural Anesthesia or Puncture",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s26_c1"
        ]
      },
      {
        "section": "warnings/43685-7/27",
        "title": "5.4 Patients with Prosthetic Heart Valves",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.5 Acute PE in Hemodynamically Unstable Patients or Patients who Require Thrombolysis or Pulmonary Embolectomy",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.6 Increased Risk of Thrombosis in Patients with Triple Positive Antiphospholipid Syndrome",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s29_c1"
        ]
      },
      {
        "section": "labelling/34089-3/58",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s58_c1"
        ]
      },
      {
        "section": "warnings/34076-0/88",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s88_c1",
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s88_c2"
        ]
      },
      {
        "section": "labelling/51945-4/92",
        "title": "PRINCIPAL DISPLAY PANEL - 5 mg",
        "chunk_ids": [
          "dailymed_41a133ef-e461-48ad-8221-b735bdd0ec25_v5_s92_c1"
        ]
      }
    ]
  },
  {
    "setid": "c85d6d02-6cf6-4995-a590-cfca302ea0c9",
    "version": 1,
    "product_name": "Simvastatin",
    "xml_sha256": "4ef2b017788b34c093e4a4af6cd2bf29cf1bb09979f34f773f9203b8d0b43308",
    "effective_date": "2026-11-03",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c85d6d02-6cf6-4995-a590-cfca302ea0c9&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Important Dosage and Administration Information",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Recommended Dosage in Adult Patients",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Recommended Dosage in Pediatric Patients 10 Years of Age and Older with HeFH",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Recommended Dosage in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Dosage Modifications Due to Drug Interactions",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s12_c1"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Myopathy and Rhabdomyolysis",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s18_c1",
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s18_c2"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.2 Immune-Mediated Necrotizing Myopathy",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.3 Hepatic Dysfunction",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.4 Increases in HbA1c and Fasting Serum Glucose Levels",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s21_c1"
        ]
      },
      {
        "section": "labelling/34089-3/45",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s45_c1"
        ]
      },
      {
        "section": "warnings/34076-0/70",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s70_c1"
        ]
      },
      {
        "section": "warnings/42229-5/71",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s71_c1"
        ]
      },
      {
        "section": "warnings/42229-5/72",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s72_c1"
        ]
      },
      {
        "section": "warnings/42229-5/73",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s73_c1"
        ]
      },
      {
        "section": "warnings/42229-5/74",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s74_c1"
        ]
      },
      {
        "section": "warnings/42229-5/75",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s75_c1"
        ]
      },
      {
        "section": "warnings/42229-5/76",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_c85d6d02-6cf6-4995-a590-cfca302ea0c9_v1_s76_c1"
        ]
      }
    ]
  },
  {
    "setid": "20ec4646-9d1c-41c9-93f6-754b3a4f234f",
    "version": 8,
    "product_name": "meloxicam",
    "xml_sha256": "53b233bff78e4196f05cead21d6c684ddfc7fe53def4fb61cc09b2e6909e4cd2",
    "effective_date": "2026-11-09",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=20ec4646-9d1c-41c9-93f6-754b3a4f234f&version=8",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/42229-5/3",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s3_c1"
        ]
      },
      {
        "section": "labelling/unknown/6",
        "title": "1.1 Osteoarthritis (OA)",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s6_c1"
        ]
      },
      {
        "section": "labelling/unknown/7",
        "title": "1.2 Rheumatoid Arthritis (RA)",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s7_c1"
        ]
      },
      {
        "section": "labelling/unknown/8",
        "title": "1.3 Juvenile Rheumatoid Arthritis (JRA) Pauciarticular and Polyarticular Course",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s8_c1"
        ]
      },
      {
        "section": "dosage/unknown/10",
        "title": "2.1 General Dosing Instructions",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s10_c1"
        ]
      },
      {
        "section": "dosage/unknown/11",
        "title": "2.2 Osteoarthritis",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s11_c1"
        ]
      },
      {
        "section": "dosage/unknown/12",
        "title": "2.3 Rheumatoid Arthritis",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s12_c1"
        ]
      },
      {
        "section": "dosage/unknown/13",
        "title": "2.4 Juvenile Rheumatoid Arthritis (JRA) Pauciarticular and Polyarticular Course",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s13_c1"
        ]
      },
      {
        "section": "dosage/unknown/14",
        "title": "2.5 Renal Impairment",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s14_c1"
        ]
      },
      {
        "section": "dosage/unknown/15",
        "title": "2.6 Non-Interchangeability with Other Formulations of Meloxicam",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s19_c1"
        ]
      },
      {
        "section": "warnings/unknown/21",
        "title": "5.1 Cardiovascular Thrombotic Events",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s21_c1",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s21_c2",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s21_c3"
        ]
      },
      {
        "section": "warnings/unknown/22",
        "title": "5.2 Gastrointestinal Bleeding, Ulceration, and Perforation",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s22_c1",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s22_c2"
        ]
      },
      {
        "section": "warnings/unknown/23",
        "title": "5.3 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s23_c1"
        ]
      },
      {
        "section": "warnings/unknown/24",
        "title": "5.4 Hypertension",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s24_c1"
        ]
      },
      {
        "section": "warnings/unknown/25",
        "title": "5.5 Heart Failure and Edema",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s25_c1"
        ]
      },
      {
        "section": "warnings/unknown/26",
        "title": "5.6 Renal Toxicity and Hyperkalemia",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s26_c1",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s26_c2"
        ]
      },
      {
        "section": "warnings/unknown/27",
        "title": "5.7 Anaphylactic Reactions",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s27_c1"
        ]
      },
      {
        "section": "warnings/unknown/28",
        "title": "5.8 Exacerbation of Asthma Related to Aspirin Sensitivity",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s28_c1"
        ]
      },
      {
        "section": "warnings/42228-7/29",
        "title": "5.9 Serious Skin Reactions",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s29_c1"
        ]
      },
      {
        "section": "warnings/unknown/30",
        "title": "5.10 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s30_c1"
        ]
      },
      {
        "section": "warnings/unknown/31",
        "title": "5.11 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s31_c1",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s31_c2"
        ]
      },
      {
        "section": "warnings/unknown/32",
        "title": "5.12 Hematologic Toxicity",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s32_c1"
        ]
      },
      {
        "section": "warnings/unknown/33",
        "title": "5.13 Masking of Inflammation and Fever",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s33_c1"
        ]
      },
      {
        "section": "warnings/unknown/34",
        "title": "5.14 Laboratory Monitoring",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s34_c1"
        ]
      },
      {
        "section": "labelling/42229-5/52",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s52_c1"
        ]
      },
      {
        "section": "warnings/42229-5/64",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s64_c1",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s64_c2",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s64_c3",
          "dailymed_20ec4646-9d1c-41c9-93f6-754b3a4f234f_v8_s64_c4"
        ]
      }
    ]
  },
  {
    "setid": "ac903bda-76af-4aba-9c8a-ebf7066e05ee",
    "version": 18,
    "product_name": "Duloxetine",
    "xml_sha256": "3495bce63fd57d84c83cae7c9dd57c83ed9b174cfc8fe9a0e61fdc9016d3de96",
    "effective_date": "2026-11-13",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ac903bda-76af-4aba-9c8a-ebf7066e05ee&version=18",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Dosage for Treatment of Major Depressive Disorder in Adults",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Dosage for Treatment of Generalized Anxiety Disorder",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s8_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Dosage for Treatment of Diabetic Peripheral Neuropathic Pain in Adults",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.5 Dosage for Treatment of Fibromyalgia",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.6 Dosage for Treatment of Chronic Musculoskeletal Pain in Adults",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.7 Dosage in Patients with Hepatic Impairment or Severe Renal Impairment",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.8 Discontinuing Duloxetine Delayed-Release Capsules",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.9 Switching a Patient to or from a Monoamine Oxidase Inhibitor (MAOI) Intended to Treat Psychiatric Disorders",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.10 Use of Duloxetine Delayed-Release Capsules with Other MAOIs such as Linezolid or Methylene Blue",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s15_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s15_c2"
        ]
      },
      {
        "section": "warnings/34070-3/17",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.1 Suicidal Thoughts and Behaviors in Children, Adolescents, and Young Adults",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s19_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s19_c2",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s19_c3",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s19_c4",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s19_c5",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s19_c6"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.2 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s20_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s20_c2"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.3 Orthostatic Hypotension, Falls and Syncope",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s21_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s21_c2"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.4 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s22_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s22_c2"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.5 Increased Risk of Bleeding",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.6 Severe Skin Reactions",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.7 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.8 Activation of Mania/Hypomania",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.9 Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.10 Seizures",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.11 Increases in Blood Pressure",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.12 Clinically Important Drug Interactions",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s30_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s30_c2"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.13 Hyponatremia",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.14 Use in Patients with Concomitant Illness",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s32_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s32_c2"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.15 Urinary Hesitation and Retention",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.16 Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s34_c1"
        ]
      },
      {
        "section": "labelling/34089-3/72",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s72_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s72_c2"
        ]
      },
      {
        "section": "warnings/34076-0/87",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c1",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c2",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c3",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c4",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c5",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c6",
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s87_c7"
        ]
      },
      {
        "section": "labelling/51945-4/89",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_ac903bda-76af-4aba-9c8a-ebf7066e05ee_v18_s89_c1"
        ]
      }
    ]
  },
  {
    "setid": "0930965b-80e3-4a0c-bffc-14ac32a47894",
    "version": 35,
    "product_name": "Carvedilol",
    "xml_sha256": "b824f731c65c18cbd6aaccaea46b397e9ff3f04f906ecbdaf25bb62365d7f543",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=0930965b-80e3-4a0c-bffc-14ac32a47894&version=35",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Heart Failure",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Left Ventricular Dysfunction following Myocardial Infarction",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Hypertension",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s5_c1"
        ]
      },
      {
        "section": "dosage/34068-7/6",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.1 Heart Failure",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s7_c1",
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s7_c2"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.2 Left Ventricular Dysfunction following Myocardial Infarction",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.3 Hypertension",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.4 Hepatic Impairment",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s10_c1"
        ]
      },
      {
        "section": "warnings/34070-3/12",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.1 Cessation of Therapy",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.2 Bradycardia",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.3 Hypotension",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s16_c1",
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.4 Heart Failure/Fluid Retention",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.5 Non-allergic Bronchospasm",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.6 Effects on Blood Sugar",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.7 Peripheral Vascular Disease",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.8 Deterioration of Renal Function",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.9 Major Surgery",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.10 Thyrotoxicosis",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.11 Pheochromocytoma",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.12 Prinzmetal's Variant Angina",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.13 Risk of Anaphylactic Reaction",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.14 Intraoperative Floppy Iris Syndrome",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s27_c1"
        ]
      },
      {
        "section": "labelling/34089-3/47",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s47_c1"
        ]
      },
      {
        "section": "warnings/34076-0/62",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s62_c1"
        ]
      },
      {
        "section": "labelling/51945-4/64",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 6.25 mg",
        "chunk_ids": [
          "dailymed_0930965b-80e3-4a0c-bffc-14ac32a47894_v35_s64_c1"
        ]
      }
    ]
  },
  {
    "setid": "a9fc7091-b3ce-45fd-8d89-aeebdd81c327",
    "version": 20,
    "product_name": "Buspirone Hydrochloride",
    "xml_sha256": "3b6b29099666ea3e811fa8423e75411aea7ee5571925713969372e51ee78f7ad",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=a9fc7091-b3ce-45fd-8d89-aeebdd81c327&version=20",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s2_c1",
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s2_c2"
        ]
      },
      {
        "section": "labelling/34067-9/9",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s9_c1",
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s9_c2"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s10_c1"
        ]
      },
      {
        "section": "warnings/34071-1/11",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s12_c1",
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s12_c2"
        ]
      },
      {
        "section": "dosage/34068-7/73",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s73_c1"
        ]
      },
      {
        "section": "dosage/42229-5/74",
        "title": "Switching a Patient To or From a Monoamine Oxidase Inhibitor (MAOI) Antidepressant",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s74_c1"
        ]
      },
      {
        "section": "dosage/42229-5/75",
        "title": "Use of Buspirone with (Reversible) MAOIs, Such as Linezolid or Methylene Blue",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s75_c1",
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s75_c2"
        ]
      },
      {
        "section": "labelling/51945-4/79",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_a9fc7091-b3ce-45fd-8d89-aeebdd81c327_v20_s79_c1"
        ]
      }
    ]
  },
  {
    "setid": "5fecf4b2-67fe-a7e9-e063-6394a90a793e",
    "version": 1,
    "product_name": "Venlafaxine",
    "xml_sha256": "64cc740d5e6f455296d16c25513cce16c183074e38e64253fdc3ee1509aae1d4",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5fecf4b2-67fe-a7e9-e063-6394a90a793e&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/42229-5/3",
        "title": "Suicidality and Antidepressant Drugs",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s3_c1"
        ]
      },
      {
        "section": "labelling/34089-3/4",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s4_c1"
        ]
      },
      {
        "section": "labelling/34067-9/12",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s12_c1",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s12_c2"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "Clinical Worsening and Suicide Risk",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s15_c1",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s15_c2",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s15_c3",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s15_c4",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s15_c5"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "Screening Patients for Bipolar Disorder",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s17_c1",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s17_c2"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "Sustained Hypertension",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s19_c1",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s19_c2"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/34076-0/36",
        "title": "Information for Patients",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s36_c1"
        ]
      },
      {
        "section": "dosage/42229-5/97",
        "title": "Initial Treatment",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s97_c1"
        ]
      },
      {
        "section": "dosage/42229-5/99",
        "title": "Treatment of Pregnant Women During the Third Trimester",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s99_c1"
        ]
      },
      {
        "section": "dosage/42229-5/100",
        "title": "Dosage for Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s100_c1"
        ]
      },
      {
        "section": "dosage/42229-5/101",
        "title": "Dosage for Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s101_c1"
        ]
      },
      {
        "section": "dosage/42229-5/102",
        "title": "Dosage for Elderly Patients",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s102_c1"
        ]
      },
      {
        "section": "dosage/42229-5/103",
        "title": "Maintenance Treatment",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s103_c1",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s103_c2"
        ]
      },
      {
        "section": "dosage/42229-5/104",
        "title": "Discontinuing Venlafaxine Tablets",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s104_c1"
        ]
      },
      {
        "section": "dosage/42229-5/105",
        "title": "Switching a Patient To or From a Monoamine Oxidase Inhibitor (MAOI) Intended to Treat Psychiatric Disorders",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s105_c1"
        ]
      },
      {
        "section": "dosage/42229-5/106",
        "title": "Use of Venlafaxine Tablets With Other MAOls, Such as Linezolid or Methylene Blue",
        "chunk_ids": [
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s106_c1",
          "dailymed_5fecf4b2-67fe-a7e9-e063-6394a90a793e_v1_s106_c2"
        ]
      }
    ]
  },
  {
    "setid": "9f0e33bd-65f8-446a-886f-e7e16a142ce5",
    "version": 4,
    "product_name": "Tramadol Hydrochloride",
    "xml_sha256": "a179e2d1a7d2e48b1fb02f30fccffa944f242adc99a628862f7c4aef5f225ea0",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9f0e33bd-65f8-446a-886f-e7e16a142ce5&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: SERIOUS AND LIFE-THREATENING RISKS FROM USE OF TRAMADOL HYDROCHLORIDE TABLETS",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s2_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s2_c2",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s2_c3"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Important Dosage and Administration Instructions",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s6_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s6_c2"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Patient Access to an Opioid Overdose Reversal Agent for the Emergency Treatment of Opioid Overdose",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Initial Dosage",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s8_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Titration and Maintenance of Therapy",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.5 Safe Reduction or Discontinuation of tramadol hydrochloride tablets",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s10_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s10_c2",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s10_c3",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s10_c4"
        ]
      },
      {
        "section": "warnings/34070-3/12",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.1 Addiction, Abuse, and Misuse",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s14_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s14_c2"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.2 Life-Threatening Respiratory Depression",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s15_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s15_c2",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s15_c3"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.3 Risks from Concomitant Use with Benzodiazepines or Other CNS Depressants",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s16_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.4 Neonatal Opioid Withdrawal Syndrome",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.5 Risk Evaluation and Mitigation Strategy (REMS)",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s18_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s18_c2"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.6 Ultra-Rapid Metabolism of Tramadol and Other Risk Factors for Life-threatening Respiratory Depression in Children",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s19_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s19_c2",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s19_c3"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.7 Risks of Interactions with Drugs Affecting Cytochrome P450 Isoenzymes",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s20_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s20_c2",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s20_c3"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.8 Opioid-Induced Hyperalgesia and Allodynia",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.9 Serotonin Syndrome Risk",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.10 Increased Risk of Seizure",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.11 Suicide Risk",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.12 Life-Threatening Respiratory Depression in Patients with Chronic Pulmonary Disease or in Elderly, Cachectic, or Debilitated Patients",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.13 Adrenal Insufficiency",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.14 Severe Hypotension",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.15 Risks of use in Patients with Increased Intracranial Pressure, Brain Tumors, Head Injury, or Impaired Consciousness",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.16 Risks of Gastrointestinal Complications",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.17 Anaphylaxis and Other Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.18 Withdrawal",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.19 Risks of Driving and Operating Machinery",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s32_c1"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.20 Hyponatremia",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.21 Hypoglycemia",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s34_c1"
        ]
      },
      {
        "section": "labelling/34089-3/51",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s51_c1"
        ]
      },
      {
        "section": "warnings/34076-0/60",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c1",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c2",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c3",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c4",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c5",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c6",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c7",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c8",
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s60_c9"
        ]
      },
      {
        "section": "labelling/51945-4/62",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_9f0e33bd-65f8-446a-886f-e7e16a142ce5_v4_s62_c1"
        ]
      }
    ]
  },
  {
    "setid": "8f41912e-12ce-4174-a0fb-cfb4888d8d58",
    "version": 9,
    "product_name": "HYDROXYZINE HYDROCHLORIDE",
    "xml_sha256": "05a55901d07281a2e0c591fcd98edb5b57b26138e03ad6ffb18c955039732fc9",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8f41912e-12ce-4174-a0fb-cfb4888d8d58&version=9",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_8f41912e-12ce-4174-a0fb-cfb4888d8d58_v9_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_8f41912e-12ce-4174-a0fb-cfb4888d8d58_v9_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_8f41912e-12ce-4174-a0fb-cfb4888d8d58_v9_s5_c1"
        ]
      },
      {
        "section": "warnings/34080-2/7",
        "title": "Nursing Mothers",
        "chunk_ids": [
          "dailymed_8f41912e-12ce-4174-a0fb-cfb4888d8d58_v9_s7_c1"
        ]
      },
      {
        "section": "dosage/34068-7/13",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_8f41912e-12ce-4174-a0fb-cfb4888d8d58_v9_s13_c1"
        ]
      },
      {
        "section": "labelling/51945-4/15",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_8f41912e-12ce-4174-a0fb-cfb4888d8d58_v9_s15_c1"
        ]
      }
    ]
  },
  {
    "setid": "2fa30bdb-f60e-40a7-98b4-c346bc85d539",
    "version": 7,
    "product_name": "Ondansetron Hydrochloride",
    "xml_sha256": "9327bb99a9e9e198d1d98aa1b589313a6742819ae29e1e34178768a04ac54044",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2fa30bdb-f60e-40a7-98b4-c346bc85d539&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Recommended Dosage",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s4_c1",
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s4_c2"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.2 Dosage in Hepatic Impairment",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s5_c1"
        ]
      },
      {
        "section": "warnings/34070-3/7",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s7_c1"
        ]
      },
      {
        "section": "warnings/42229-5/9",
        "title": "5.1 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.2 QT Prolongation",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.3 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s11_c1",
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s11_c2"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.4 Myocardial Ischemia",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.5 Masking of Progressive Ileus and Gastric Distension",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s13_c1"
        ]
      },
      {
        "section": "labelling/34089-3/32",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s32_c1"
        ]
      },
      {
        "section": "warnings/34076-0/44",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s44_c1",
          "dailymed_2fa30bdb-f60e-40a7-98b4-c346bc85d539_v7_s44_c2"
        ]
      }
    ]
  },
  {
    "setid": "34e57aff-dc4b-4631-9d57-31020244835d",
    "version": 4,
    "product_name": "Cyclobenzaprine Hydrochloride",
    "xml_sha256": "8e0a0bb32be31b0e6e14c424aeb72de4812d1e8a6aa80d758c6349beb9770f80",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=34e57aff-dc4b-4631-9d57-31020244835d&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s2_c1",
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s2_c2"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s5_c1"
        ]
      },
      {
        "section": "warnings/34071-1/6",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s6_c1",
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s6_c2"
        ]
      },
      {
        "section": "dosage/34068-7/11",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s11_c1"
        ]
      },
      {
        "section": "labelling/51945-4/14",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_34e57aff-dc4b-4631-9d57-31020244835d_v4_s14_c1"
        ]
      }
    ]
  },
  {
    "setid": "ae0dcb4e-63df-459c-8e60-0caa817b8135",
    "version": 5,
    "product_name": "SPIRONOLACTONE",
    "xml_sha256": "5415e784ca8792551c0881e004c683c49ccc839bc6b4374e37a4d357429cc015",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ae0dcb4e-63df-459c-8e60-0caa817b8135&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Heart Failure",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Hypertension",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s4_c1",
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s4_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Edema Associated with Hepatic Cirrhosis or Nephrotic Syndrome",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.4 Primary Hyperaldosteronism",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 General Considerations",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Treatment of Heart Failure",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Treatment of Essential Hypertension",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Treatment of Edema",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Treatment of Primary Hyperaldosteronism",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s12_c1"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Hyperkalemia",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Hypotension and Worsening Renal Function",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Electrolyte and Metabolic Abnormalities",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Gynecomastia",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s19_c1"
        ]
      },
      {
        "section": "labelling/34089-3/38",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s38_c1"
        ]
      },
      {
        "section": "warnings/34076-0/49",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s49_c1"
        ]
      },
      {
        "section": "labelling/51945-4/50",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 25 mg (100 Tablets Bottle)",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s50_c1"
        ]
      },
      {
        "section": "labelling/51945-4/51",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 50 mg (100 Tablets Bottle)",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s51_c1"
        ]
      },
      {
        "section": "labelling/51945-4/52",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 100 mg (100 Tablets Bottle)",
        "chunk_ids": [
          "dailymed_ae0dcb4e-63df-459c-8e60-0caa817b8135_v5_s52_c1"
        ]
      }
    ]
  },
  {
    "setid": "c4da6de7-9ab1-4fcf-88f3-fe785019e6e7",
    "version": 13,
    "product_name": "Estradiol",
    "xml_sha256": "ba2abc1522a92f8dfd4c73c6f2b1a3f35672b74e5d6b601ba815aff922c6e4d9",
    "effective_date": "2026-10-30",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c4da6de7-9ab1-4fcf-88f3-fe785019e6e7&version=13",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: ENDOMETRIAL CANCER WITH UNOPPOSED ESTROGEN IN WOMEN WITH A UTERUS",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Treatment of Moderate to Severe Symptoms of Vulvar and Vaginal Atrophy Due to Menopause",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.4 Prevention of Postmenopausal Osteoporosis",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.1 Important Use Information",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s10_c1",
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.2 Treatment of Moderate to Severe Vasomotor Symptoms due to Menopause",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.3 Treatment of Moderate to Severe Symptoms of Vulvar and Vaginal Atrophy due to Menopause",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.5 Prevention of Postmenopausal Osteoporosis",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.6 Application Instructions",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s15_c1"
        ]
      },
      {
        "section": "warnings/34070-3/17",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.1 Cardiovascular Disorders",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s19_c1",
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s19_c2",
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s19_c3"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.2 Malignant Neoplasms",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s20_c1",
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s20_c2",
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s20_c3"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.3 Risks Associated with Co-administration of Estrogen Plus Progestogen",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.4 Gallbladder Disease",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.5 Hypercalcemia",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.6 Visual Abnormalities",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.7 Elevated Blood Pressure",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.8 Exacerbation of Hypertriglyceridemia",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.9 Hepatic Impairment and/or Past History of Cholestatic Jaundice",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.10 Exacerbation of Hypothyroidism",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.11 Fluid Retention",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.12 Hypocalcemia",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.13 Malignant Transformation of Endometriosis",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.14 Severe Anaphylactic/Anaphylactoid Reactions and Angioedema",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s32_c1"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.15 Exacerbation of Other Conditions",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.16 Laboratory Tests",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.17 Drug-Laboratory Test Interactions",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s35_c1"
        ]
      },
      {
        "section": "labelling/34089-3/46",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s46_c1",
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s46_c2"
        ]
      },
      {
        "section": "warnings/34076-0/62",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s62_c1"
        ]
      },
      {
        "section": "labelling/51945-4/65",
        "title": "Estradiol Transdermal System 0.025 mg/day",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s65_c1"
        ]
      },
      {
        "section": "labelling/51945-4/66",
        "title": "Estradiol Transdermal System 0.0375 mg/day",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s66_c1"
        ]
      },
      {
        "section": "labelling/51945-4/67",
        "title": "Estradiol Transdermal System 0.075 mg/day",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s67_c1"
        ]
      },
      {
        "section": "labelling/51945-4/68",
        "title": "Estradiol Transdermal System 0.05 mg/day",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s68_c1"
        ]
      },
      {
        "section": "labelling/51945-4/69",
        "title": "Estradiol Transdermal System 0.1 mg/day",
        "chunk_ids": [
          "dailymed_c4da6de7-9ab1-4fcf-88f3-fe785019e6e7_v13_s69_c1"
        ]
      }
    ]
  },
  {
    "setid": "c829b7bf-1a12-44b2-b5ce-fd44a1f0d333",
    "version": 24,
    "product_name": "Glipizide",
    "xml_sha256": "bebf7a28be9bb21e50c9233e8399c59011d823760bc4e1b78140e4d23cd4a0b0",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c829b7bf-1a12-44b2-b5ce-fd44a1f0d333&version=24",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/7",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s7_c1"
        ]
      },
      {
        "section": "warnings/34070-3/8",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s8_c1"
        ]
      },
      {
        "section": "warnings/34071-1/9",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s9_c1",
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s9_c2"
        ]
      },
      {
        "section": "warnings/34072-9/11",
        "title": "General",
        "chunk_ids": [
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s11_c1",
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s11_c2"
        ]
      },
      {
        "section": "dosage/34068-7/24",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s24_c1",
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s24_c2",
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s24_c3",
          "dailymed_c829b7bf-1a12-44b2-b5ce-fd44a1f0d333_v24_s24_c4"
        ]
      }
    ]
  },
  {
    "setid": "625fad5b-8817-4773-a2fc-20b662140e6e",
    "version": 4,
    "product_name": "Zolpidem Tartrate",
    "xml_sha256": "5fc62636600036bdd14c209810edaa4b57b46857264a317ad0a700634f3fa8e2",
    "effective_date": "2026-11-11",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=625fad5b-8817-4773-a2fc-20b662140e6e&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: COMPLEX SLEEP BEHAVIORS",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Dosage in Adults",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Special Populations",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Use with CNS Depressants",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Administration",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s8_c1"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.1 Complex Sleep Behaviors",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.2 CNS-Depressant Effects and Next-Day Impairment",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s13_c1",
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s13_c2"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.3 Need to Evaluate for Comorbid Diagnoses",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.4 Severe Anaphylactic and Anaphylactoid Reactions",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.5 Abnormal Thinking and Behavioral Changes",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.6 Use in Patients with Depression",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.7 Respiratory Depression",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.8 Precipitation of Hepatic Encephalopathy",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.9 Withdrawal Effects",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s20_c1"
        ]
      },
      {
        "section": "labelling/34089-3/41",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s41_c1"
        ]
      },
      {
        "section": "warnings/34076-0/52",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s52_c1",
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s52_c2",
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s52_c3",
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s52_c4"
        ]
      },
      {
        "section": "labelling/51945-4/54",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL - Label 12.5 mg",
        "chunk_ids": [
          "dailymed_625fad5b-8817-4773-a2fc-20b662140e6e_v4_s54_c1"
        ]
      }
    ]
  },
  {
    "setid": "70cd448a-2921-4c69-bdf2-5a6ce883bd07",
    "version": 18,
    "product_name": "Lamotrigine",
    "xml_sha256": "1a32e1cf87c055762ef5a8fc9f1e11dba948b9568ebe59b19728c55c39354889",
    "effective_date": "2026-10-28",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=70cd448a-2921-4c69-bdf2-5a6ce883bd07&version=18",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: SERIOUS SKIN RASHES",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s3_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s3_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.1 Epilepsy",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Bipolar Disorder",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 General Dosing Considerations",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c2",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c3",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c4",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c5",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c6",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c7",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c8",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s8_c9"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Epilepsy \u2013 Adjunctive Therapy",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c2",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c3",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c4",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c5",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c6",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s9_c7"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Epilepsy \u2013 Conversion from Adjunctive Therapy to Monotherapy",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s10_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Bipolar Disorder",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s11_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s11_c2",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s11_c3",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s11_c4",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s11_c5"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Serious Skin Rashes [see Boxed Warning]",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s16_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s16_c2",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s16_c3"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Hemophagocytic Lymphohistiocytosis",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Multiorgan Hypersensitivity Reactions and Organ Failure",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s18_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s18_c2"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Cardiac Rhythm and Conduction Abnormalities",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.5 Blood Dyscrasias",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.6 Suicidal Behavior and Ideation",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s21_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s21_c2",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s21_c3",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s21_c4"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.7 Aseptic Meningitis",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s22_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s22_c2"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.8 Potential Medication Errors",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.9 Concomitant Use with Estrogen-Containing Products, Including Oral Contraceptives",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.10 Withdrawal Seizures",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.11 Status Epilepticus",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.12 Addition of Lamotrigine Tablets to a Multidrug Regimen that Includes Valproate",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.13 Binding in the Eye and Other Melanin-Containing Tissues",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.14 Laboratory Tests",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s29_c1"
        ]
      },
      {
        "section": "labelling/34089-3/45",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s45_c1"
        ]
      },
      {
        "section": "warnings/34076-0/56",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s56_c1",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s56_c2",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s56_c3",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s56_c4",
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s56_c5"
        ]
      },
      {
        "section": "labelling/51945-4/58",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_70cd448a-2921-4c69-bdf2-5a6ce883bd07_v18_s58_c1"
        ]
      }
    ]
  },
  {
    "setid": "0a967468-3869-4c8c-849f-9fc3a8dcc489",
    "version": 9,
    "product_name": "Citalopram",
    "xml_sha256": "38011542f1f184a36a9c11fe9b7fa2cc0eb479fadac7c5f26908602a4b4a3e01",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=0a967468-3869-4c8c-849f-9fc3a8dcc489&version=9",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Recommended Dosage",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Screen for Bipolar Disorder Prior to Starting Citalopram Tablets",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Recommended Dosage for Specific Populations",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Dosage Modifications with Concomitant Use of CYP2C19 Inhibitors",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.5 Switching Patients to or from a Monoamine Oxidase Inhibitor Antidepressant",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.6 Discontinuing Treatment with Citalopram Tablets",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s11_c1"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Suicidal Thoughts and Behavior in Adolescents and Young Adults",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s15_c1",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s15_c2"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 QT-Prolongation and Torsade de Pointes",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s16_c1",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s16_c2",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s16_c3"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s17_c1",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s17_c2"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Increased Risk of Bleeding",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.5 Activation of Mania or Hypomania",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.6 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.7 Seizures",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.8 Angle-closure Glaucoma",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.9 Hyponatremia",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.10 Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s24_c1"
        ]
      },
      {
        "section": "labelling/34089-3/39",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s39_c1"
        ]
      },
      {
        "section": "warnings/34076-0/49",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s49_c1",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s49_c2",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s49_c3",
          "dailymed_0a967468-3869-4c8c-849f-9fc3a8dcc489_v9_s49_c4"
        ]
      }
    ]
  },
  {
    "setid": "1760ccdc-46f7-4182-a563-96b13212cb7e",
    "version": 8,
    "product_name": "Pregabalin",
    "xml_sha256": "96bdc127386189844260b29983e31a44ab44d136e65110eba85117b118981223",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1760ccdc-46f7-4182-a563-96b13212cb7e&version=8",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Neuropathic Pain Associated with Diabetic Peripheral Neuropathy in Adults",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Postherpetic Neuralgia in Adults",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Adjunctive Therapy for Partial-Onset Seizures in Patients 1 Month of Age and Older",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s8_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Management of Fibromyalgia in Adults",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.6 Neuropathic Pain Associated with Spinal Cord Injury in Adults",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.7 Dosing for Adult Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s11_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s11_c2",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s11_c3"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Angioedema",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 Hypersensitivity",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Suicidal Behavior and Ideation",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s17_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s17_c2",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s17_c3"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Increased Risk of Adverse Reactions with Abrupt or Rapid Discontinuation",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.5 Respiratory Depression",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.6 Dizziness and Somnolence",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s20_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s20_c2"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.7 Peripheral Edema",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s21_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s21_c2"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.8 Weight Gain",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s22_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s22_c2"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.9 Tumorigenic Potential",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.10 Ophthalmological Effects",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.11 Creatine Kinase Elevations",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.12 Decreased Platelet Count",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.13 PR Interval Prolongation",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s27_c1"
        ]
      },
      {
        "section": "labelling/34089-3/44",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s44_c1"
        ]
      },
      {
        "section": "warnings/34076-0/58",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s58_c1",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s58_c2",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s58_c3",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s58_c4",
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s58_c5"
        ]
      },
      {
        "section": "labelling/51945-4/60",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_1760ccdc-46f7-4182-a563-96b13212cb7e_v8_s60_c1"
        ]
      }
    ]
  },
  {
    "setid": "6cb41b00-0589-42d0-9e3e-230385768875",
    "version": 1,
    "product_name": "Azithromycin",
    "xml_sha256": "3a0a8662d633c8607ccb5ecd75c8d2c9cc24b88ac9296dfeee88c8a0f2793dfb",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6cb41b00-0589-42d0-9e3e-230385768875&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Indications in Adult Patients",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Indications in Pediatric Patients",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Limitations of Use",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.4 Usage",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Recommended Dosage for Adult Patients",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Recommended Dosage for Pediatric Patients",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s9_c1",
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s9_c2",
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s9_c3",
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s9_c4"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Pediatric Dosage Guidelines for Pharyngitis/Tonsillitis",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Preparation Instructions for Azithromycin for Oral Suspension",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "4.1 Hypersensitivity",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "4.2 Hepatic Dysfunction",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.1 Hypersensitivity",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.2 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.3 Infantile Hypertrophic Pyloric Stenosis (IHPS)",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.4 QT Prolongation",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.5 Cardiovascular Death",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.6 Clostridioides difficile -Associated Diarrhea",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.7 Exacerbation of Myasthenia Gravis",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.8 Risk of Antibacterial Resistance in Sexually Transmitted Infections",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.9 Development of Drug-Resistant Bacteria",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s25_c1"
        ]
      },
      {
        "section": "labelling/34089-3/44",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s44_c1",
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s44_c2"
        ]
      },
      {
        "section": "warnings/34076-0/59",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s59_c1",
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s59_c2"
        ]
      },
      {
        "section": "labelling/51945-4/61",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_6cb41b00-0589-42d0-9e3e-230385768875_v1_s61_c1"
        ]
      }
    ]
  },
  {
    "setid": "fa152ce7-6c07-4aaf-9374-932ce81d0cf9",
    "version": 5,
    "product_name": "Pravastatin sodium",
    "xml_sha256": "f14efdc02f9c46ae71a3467b2783a51bf3cea5d9ed8d2aada49674b50f50edcd",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=fa152ce7-6c07-4aaf-9374-932ce81d0cf9&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Important Dosage and Administration Information",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.2 Recommended Dosage in Adult Patients",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.3 Recommended Dosage in Pediatric Patients 8 Years of Age and Older with HeFH",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.4 Recommended Dosage in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.5 Dosage and Administration Modifications Due to Drug Interactions",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s8_c1"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.1 Myopathy and Rhabdomyolysis",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s12_c1",
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s12_c2"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.2 Immune-Mediated Necrotizing Myopathy",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.3 Hepatic Dysfunction",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.4 Increases in HbA1c and Fasting Serum Glucose Levels",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s15_c1"
        ]
      },
      {
        "section": "labelling/34089-3/30",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s30_c1"
        ]
      },
      {
        "section": "warnings/34076-0/39",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s39_c1",
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s39_c2"
        ]
      },
      {
        "section": "labelling/51945-4/40",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_fa152ce7-6c07-4aaf-9374-932ce81d0cf9_v5_s40_c1"
        ]
      }
    ]
  },
  {
    "setid": "7ea2fdf1-4fda-47a7-8110-62fb6468c989",
    "version": 4,
    "product_name": "Valsartan",
    "xml_sha256": "d993a98400a40b34009c83df5f3ebd8452d8bc0b41d018908d6e2208ada60333",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=7ea2fdf1-4fda-47a7-8110-62fb6468c989&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: FETAL TOXICITY",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Hypertension",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s4_c1",
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s4_c2",
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s4_c3"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Heart Failure",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Post-Myocardial Infarction",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Important Dosage and Preparation Information",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s8_c1",
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Adult Hypertension",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Pediatric Hypertension 1 to 16 Years of Age",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Heart Failure",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Post-Myocardial Infarction",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.6 Missed Dose",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s13_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.2 Hypotension",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.3 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.4 Hyperkalemia",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s20_c1"
        ]
      },
      {
        "section": "labelling/34089-3/37",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s37_c1"
        ]
      },
      {
        "section": "warnings/34076-0/50",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s50_c1"
        ]
      },
      {
        "section": "labelling/51945-4/52",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 40 mg",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s52_c1"
        ]
      },
      {
        "section": "labelling/51945-4/53",
        "title": "Package/Label Display Panel \u2013 Blister \u2013 40 mg",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s53_c1"
        ]
      },
      {
        "section": "labelling/51945-4/54",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 80 mg",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s54_c1"
        ]
      },
      {
        "section": "labelling/51945-4/55",
        "title": "Package/Label Display Panel \u2013 Blister \u2013 80 mg",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s55_c1"
        ]
      },
      {
        "section": "labelling/51945-4/56",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 160 mg",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s56_c1"
        ]
      },
      {
        "section": "labelling/51945-4/57",
        "title": "Package/Label Display Panel \u2013 Blister \u2013 160 mg",
        "chunk_ids": [
          "dailymed_7ea2fdf1-4fda-47a7-8110-62fb6468c989_v4_s57_c1"
        ]
      }
    ]
  },
  {
    "setid": "174e45e0-45bb-48b7-9e60-8f6cfc1d22bb",
    "version": 9,
    "product_name": "Zetia",
    "xml_sha256": "c4268abb225aa77f6ab15ab5a6314e5a6ac6882c24e7c6bd0bce6eb89e390598",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=174e45e0-45bb-48b7-9e60-8f6cfc1d22bb&version=9",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s3_c1"
        ]
      },
      {
        "section": "dosage/34068-7/4",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/6",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s6_c1"
        ]
      },
      {
        "section": "warnings/42229-5/8",
        "title": "5.1 Risks Associated with Combination Treatment with a Statin, Fenofibrate, or Other LDL-C Lowering Therapies",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s8_c1"
        ]
      },
      {
        "section": "warnings/42229-5/9",
        "title": "5.2 Liver Enzymes",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.3 Myopathy/Rhabdomyolysis",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s10_c1"
        ]
      },
      {
        "section": "labelling/34089-3/27",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s27_c1"
        ]
      },
      {
        "section": "warnings/34076-0/48",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s48_c1"
        ]
      },
      {
        "section": "warnings/42229-5/49",
        "title": "",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s49_c1"
        ]
      },
      {
        "section": "labelling/51945-4/51",
        "title": "PRINCIPAL DISPLAY PANEL - 10 mg Tablet Bottle Label",
        "chunk_ids": [
          "dailymed_174e45e0-45bb-48b7-9e60-8f6cfc1d22bb_v9_s51_c1"
        ]
      }
    ]
  },
  {
    "setid": "5dbffab4-d287-f0e3-e063-6394a90a311d",
    "version": 6,
    "product_name": "Diclofenac Sodium",
    "xml_sha256": "192c2cb347eb04dcf5844f6820f8631d34043718d81baa93ea8562e3b470feb3",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5dbffab4-d287-f0e3-e063-6394a90a311d&version=6",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/4",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s4_c1"
        ]
      },
      {
        "section": "warnings/34071-1/5",
        "title": "Warnings",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s5_c1"
        ]
      },
      {
        "section": "warnings/50570-1/6",
        "title": "Do not use",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s6_c1"
        ]
      },
      {
        "section": "warnings/50569-3/7",
        "title": "Ask a doctor before use if",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s7_c1"
        ]
      },
      {
        "section": "warnings/50568-5/8",
        "title": "Ask a doctor or pharmacist before use if you are",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s8_c1"
        ]
      },
      {
        "section": "warnings/50567-7/9",
        "title": "When using this product",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s9_c1"
        ]
      },
      {
        "section": "warnings/50566-9/10",
        "title": "Stop use and ask a doctor if",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s10_c1"
        ]
      },
      {
        "section": "warnings/53414-9/11",
        "title": "If pregnant or breast-feeding,",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s11_c1"
        ]
      },
      {
        "section": "warnings/50565-1/12",
        "title": "Keep out of reach of children.",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s12_c1"
        ]
      },
      {
        "section": "dosage/34068-7/13",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s13_c1"
        ]
      },
      {
        "section": "labelling/51945-4/17",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 1% w/w tube Label (100 g Tube)",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s17_c1"
        ]
      },
      {
        "section": "labelling/51945-4/18",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 1% w/w Tube Carton Label (100 g tube)",
        "chunk_ids": [
          "dailymed_5dbffab4-d287-f0e3-e063-6394a90a311d_v6_s18_c1"
        ]
      }
    ]
  },
  {
    "setid": "601b8b7e-763f-2466-e063-6294a90aa688",
    "version": 1,
    "product_name": "Propranolol Hydrochloride",
    "xml_sha256": "5f492bd5ff561af2f442b8e78821cc3f05048a50e85ed2218e8fa8766503c51f",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=601b8b7e-763f-2466-e063-6294a90aa688&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s3_c1"
        ]
      },
      {
        "section": "labelling/unknown/25",
        "title": "Hypertension",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s25_c1"
        ]
      },
      {
        "section": "labelling/unknown/26",
        "title": "Angina Pectoris Due to Coronary Atherosclerosis",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s26_c1"
        ]
      },
      {
        "section": "labelling/unknown/27",
        "title": "Atrial Fibrillation",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s27_c1"
        ]
      },
      {
        "section": "labelling/unknown/28",
        "title": "Myocardial Infarction",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s28_c1"
        ]
      },
      {
        "section": "labelling/unknown/29",
        "title": "Migraine",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s29_c1"
        ]
      },
      {
        "section": "labelling/unknown/30",
        "title": "Essential Tremor",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s30_c1"
        ]
      },
      {
        "section": "labelling/unknown/31",
        "title": "Hypertrophic Subaortic Stenosis",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s31_c1"
        ]
      },
      {
        "section": "labelling/unknown/32",
        "title": "Pheochromocytoma",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s32_c1"
        ]
      },
      {
        "section": "warnings/34070-3/33",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s33_c1"
        ]
      },
      {
        "section": "warnings/unknown/35",
        "title": "Angina Pectoris",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s35_c1"
        ]
      },
      {
        "section": "warnings/unknown/36",
        "title": "Hypersensitivity and Skin Reactions",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s36_c1"
        ]
      },
      {
        "section": "warnings/unknown/37",
        "title": "Cardiac Failure",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s37_c1"
        ]
      },
      {
        "section": "warnings/unknown/38",
        "title": "Nonallergic Bronchospasm (e.g., Chronic Bronchitis, Emphysema)",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s38_c1"
        ]
      },
      {
        "section": "warnings/unknown/39",
        "title": "Major Surgery",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s39_c1"
        ]
      },
      {
        "section": "warnings/unknown/40",
        "title": "Diabetes and Hypoglycemia",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s40_c1"
        ]
      },
      {
        "section": "warnings/unknown/41",
        "title": "Thyrotoxicosis",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s41_c1"
        ]
      },
      {
        "section": "warnings/unknown/42",
        "title": "Wolff-Parkinson-White Syndrome",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s42_c1"
        ]
      },
      {
        "section": "warnings/unknown/43",
        "title": "Pheochromocytoma",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s43_c1"
        ]
      },
      {
        "section": "dosage/unknown/57",
        "title": "General",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s57_c1"
        ]
      },
      {
        "section": "dosage/unknown/58",
        "title": "Hypertension",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s58_c1"
        ]
      },
      {
        "section": "dosage/unknown/59",
        "title": "Angina Pectoris",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s59_c1"
        ]
      },
      {
        "section": "dosage/unknown/60",
        "title": "Atrial Fibrillation",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s60_c1"
        ]
      },
      {
        "section": "dosage/unknown/61",
        "title": "Myocardial Infarction",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s61_c1"
        ]
      },
      {
        "section": "dosage/unknown/62",
        "title": "Migraine",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s62_c1"
        ]
      },
      {
        "section": "dosage/unknown/63",
        "title": "Essential Tremor",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s63_c1"
        ]
      },
      {
        "section": "dosage/unknown/64",
        "title": "Hypertrophic Subaortic Stenosis",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s64_c1"
        ]
      },
      {
        "section": "dosage/unknown/65",
        "title": "Pheochromocytoma",
        "chunk_ids": [
          "dailymed_601b8b7e-763f-2466-e063-6294a90aa688_v1_s65_c1"
        ]
      }
    ]
  },
  {
    "setid": "70d7a585-7a46-4eac-b2b5-2ac5b98d9882",
    "version": 7,
    "product_name": "Atenolol",
    "xml_sha256": "6d6c4aa52ead3594ab29573e90ad3d6d63eb5e8be08b9911826577264b4f0390",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=70d7a585-7a46-4eac-b2b5-2ac5b98d9882&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "Hypertension",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s8_c1",
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s8_c2"
        ]
      },
      {
        "section": "labelling/42229-5/9",
        "title": "Angina Pectoris Due to Coronary Atherosclerosis",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s9_c1"
        ]
      },
      {
        "section": "labelling/42229-5/10",
        "title": "Acute Myocardial Infarction",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s10_c1"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "Cardiac Failure",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "In Patients Without a History of Cardiac Failure",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s14_c1"
        ]
      },
      {
        "section": "warnings/34066-1/15",
        "title": "",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "Concomitant Use of Calcium Channel Blockers",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "Bronchospastic Diseases",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "Major Surgery",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "Hypoglycemia",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "Thyrotoxicosis",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "Untreated Pheochromocytoma",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "Pregnancy and Fetal Injury",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s22_c1",
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s22_c2"
        ]
      },
      {
        "section": "warnings/34072-9/24",
        "title": "General",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s24_c1"
        ]
      },
      {
        "section": "dosage/42229-5/48",
        "title": "Hypertension",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s48_c1"
        ]
      },
      {
        "section": "dosage/42229-5/49",
        "title": "Angina Pectoris",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s49_c1"
        ]
      },
      {
        "section": "dosage/42229-5/50",
        "title": "Acute Myocardial Infarction",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s50_c1",
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s50_c2"
        ]
      },
      {
        "section": "dosage/42229-5/51",
        "title": "Elderly Patients or Patients With Renal Impairment",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s51_c1",
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s51_c2"
        ]
      },
      {
        "section": "dosage/42229-5/52",
        "title": "Cessation of Therapy in Patients With Angina Pectoris",
        "chunk_ids": [
          "dailymed_70d7a585-7a46-4eac-b2b5-2ac5b98d9882_v7_s52_c1"
        ]
      }
    ]
  },
  {
    "setid": "b99f7199-e407-442d-849f-6a1c4837e12f",
    "version": 7,
    "product_name": "celecoxib",
    "xml_sha256": "c1b6fbbd75b170bf9d72eeb023fdf810f591df017c4a250719418f7fb89b4a84",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b99f7199-e407-442d-849f-6a1c4837e12f&version=7",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: RISK OF SERIOUS CARDIOVASCULAR AND GASTROINTESTINAL EVENTS",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.1 Osteoarthritis(OA)",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Rheumatoid Arthritis(RA)",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.3 Juvenile Rheumatoid Arthritis(JRA)",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.4 Ankylosing Spondylitis(AS)",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s8_c1"
        ]
      },
      {
        "section": "labelling/42229-5/9",
        "title": "1.5 Acute Pain",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s9_c1"
        ]
      },
      {
        "section": "labelling/42229-5/10",
        "title": "1.6 Primary Dysmenorrhea",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.1 General Dosing Instructions",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.2 Osteoarthritis",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.3 Rheumatoid Arthritis",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.4 Juvenile Rheumatoid Arthritis",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s15_c1"
        ]
      },
      {
        "section": "dosage/42229-5/16",
        "title": "2.5 Ankylosing Spondylitis",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s16_c1"
        ]
      },
      {
        "section": "dosage/42229-5/17",
        "title": "2.6 Management of Acute Pain and Treatment of Primary Dysmenorrhea",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s17_c1"
        ]
      },
      {
        "section": "dosage/42229-5/18",
        "title": "2.7 Special Populations",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s18_c1"
        ]
      },
      {
        "section": "warnings/34070-3/20",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.1 Cardiovascular Thrombotic Events",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s22_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s22_c2",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s22_c3",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s22_c4"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.2 Gastrointestinal Bleeding, Ulceration, and Perforation",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s23_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s23_c2",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s23_c3"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.3 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.4 Hypertension",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.5 Heart Failure and Edema",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s26_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s26_c2"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.6 Renal Toxicity and Hyperkalemia",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s27_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s27_c2"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.7 Anaphylactic Reactions",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.8 Exacerbation of Asthma Related to Aspirin Sensitivity",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.9 Serious Skin Reactions",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.10 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.11 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s32_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s32_c2"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.12 Hematologic Toxicity",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.13 Masking of Inflammation and Fever",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.14 Laboratory Monitoring",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s35_c1"
        ]
      },
      {
        "section": "warnings/42229-5/36",
        "title": "5.15 Disseminated Intravascular Coagulation (DIC)",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s36_c1"
        ]
      },
      {
        "section": "warnings/42229-5/37",
        "title": "5.16 Risk of Allergic Reactions to Tartrazine",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s37_c1"
        ]
      },
      {
        "section": "labelling/34089-3/52",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s52_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s52_c2"
        ]
      },
      {
        "section": "warnings/34076-0/70",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s70_c1",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s70_c2",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s70_c3",
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s70_c4"
        ]
      },
      {
        "section": "labelling/51945-4/72",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_b99f7199-e407-442d-849f-6a1c4837e12f_v7_s72_c1"
        ]
      }
    ]
  },
  {
    "setid": "e482a50d-db15-4407-85c9-160c88e8a657",
    "version": 14,
    "product_name": "Finasteride",
    "xml_sha256": "99c21f751868d9c8c9afd9464c0ff1fc6871b8e0d6c522f4ec9136e79b4386b4",
    "effective_date": "2026-10-14",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e482a50d-db15-4407-85c9-160c88e8a657&version=14",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Monotherapy",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Combination with Alpha-Blocker",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Limitations of Use",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s5_c1"
        ]
      },
      {
        "section": "dosage/34068-7/6",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.1 Monotherapy",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.2 Combination with Alpha-Blocker",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s8_c1"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.1 Effects on Prostate Specific Antigen (PSA) and the Use of PSA in Prostate Cancer Detection",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s12_c1",
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s12_c2"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.2 Increased Risk of High-Grade Prostate Cancer",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.3 Exposure of Females - Risk to Male Fetus",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.4 Pediatric Patients and Females",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.5 Effect on Semen Characteristics",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.6 Consideration of Other Urological Conditions",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s17_c1"
        ]
      },
      {
        "section": "labelling/34089-3/33",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s33_c1"
        ]
      },
      {
        "section": "warnings/34076-0/45",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s45_c1",
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s45_c2"
        ]
      },
      {
        "section": "labelling/51945-4/47",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_e482a50d-db15-4407-85c9-160c88e8a657_v14_s47_c1"
        ]
      }
    ]
  },
  {
    "setid": "6562eb60-0d70-4909-bd07-88d5c9241516",
    "version": 16,
    "product_name": "Quetiapine Fumarate",
    "xml_sha256": "85e01a119d7f47fc6c7c3d423daf391f5350a03de6d53e54599d4d2747aa98b6",
    "effective_date": "2026-10-15",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6562eb60-0d70-4909-bd07-88d5c9241516&version=16",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: INCREASED MORTALITY IN ELDERLY PATIENTS WITH DEMENTIA-RELATED PSYCHOSIS; and SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Schizophrenia",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Bipolar Disorder",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s5_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s5_c2"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Adjunctive Treatment of Major Depressive Disorder (MDD)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.4 Special Considerations in Treating Pediatric Schizophrenia and Bipolar I Disorder",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.2 Recommended Dosing",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s10_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.3 Dose Modifications in Elderly Patients",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.4 Dose Modifications in Hepatically Impaired Patients",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.5 Dose Modifications when used with CYP3A4 Inhibitors",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.6 Dose Modifications when used with CYP3A4 Inducers",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.7 Re-initiation of Treatment in Patients Previously Discontinued",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s15_c1"
        ]
      },
      {
        "section": "dosage/42229-5/16",
        "title": "2.8 Switching Patients from Seroquel Tablets to Quetiapine Extended-Release Tablets",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s16_c1"
        ]
      },
      {
        "section": "dosage/42229-5/17",
        "title": "2.9 Switching from Antipsychotics",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s17_c1"
        ]
      },
      {
        "section": "warnings/34070-3/19",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.1 Increased Mortality in Elderly Patients with Dementia-Related Psychosis",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.2 Suicidal Thoughts and Behaviors in Adolescents and Young Adults",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s22_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s22_c2",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s22_c3",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s22_c4",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s22_c5"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.3 Cerebrovascular Adverse Reactions, Including Stroke, in Elderly Patients with Dementia-Related Psychosis",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.4 Neuroleptic Malignant Syndrome (NMS)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s24_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s24_c2"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.5 Metabolic Changes",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c2",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c3",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c4",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c5",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c6",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c7",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c8",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c9",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c10",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c11",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c12",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c13",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c14",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s25_c15"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.6 Tardive Dyskinesia",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s26_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s26_c2"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.7 Hypotension",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.8 Falls",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.9 Increases in Blood Pressure (Children and Adolescents)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s29_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s29_c2"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.10 Leukopenia, Neutropenia, and Agranulocytosis",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.11 Cataracts",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.12 QT Prolongation",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s32_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s32_c2"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.13 Seizures",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.14 Hypothyroidism",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s34_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s34_c2",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s34_c3",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s34_c4"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.15 Hyperprolactinemia",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s35_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s35_c2"
        ]
      },
      {
        "section": "warnings/42229-5/36",
        "title": "5.16 Potential for Cognitive and Motor Impairment",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s36_c1"
        ]
      },
      {
        "section": "warnings/42229-5/37",
        "title": "5.17 Body Temperature Regulation",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s37_c1"
        ]
      },
      {
        "section": "warnings/42229-5/38",
        "title": "5.18 Dysphagia",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s38_c1"
        ]
      },
      {
        "section": "warnings/42229-5/39",
        "title": "5.19 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s39_c1"
        ]
      },
      {
        "section": "warnings/42229-5/40",
        "title": "5.20 Anticholinergic (antimuscarinic) Effects",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s40_c1"
        ]
      },
      {
        "section": "labelling/34089-3/61",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s61_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s61_c2"
        ]
      },
      {
        "section": "warnings/34076-0/74",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s74_c1",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s74_c2",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s74_c3",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s74_c4",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s74_c5",
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s74_c6"
        ]
      },
      {
        "section": "labelling/51945-4/76",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 50 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s76_c1"
        ]
      },
      {
        "section": "labelling/51945-4/77",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 150 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s77_c1"
        ]
      },
      {
        "section": "labelling/51945-4/78",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 200 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s78_c1"
        ]
      },
      {
        "section": "labelling/51945-4/79",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 300 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s79_c1"
        ]
      },
      {
        "section": "labelling/51945-4/80",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 400 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_6562eb60-0d70-4909-bd07-88d5c9241516_v16_s80_c1"
        ]
      }
    ]
  },
  {
    "setid": "84ef7b29-dd48-43d3-bda8-d6337bc22891",
    "version": 21,
    "product_name": "Clonidine Hydrochloride",
    "xml_sha256": "c54225517639ca4b8995af7d79274676a9aad0379c163f32b70e5702cfa1a075",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=84ef7b29-dd48-43d3-bda8-d6337bc22891&version=21",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s5_c1"
        ]
      },
      {
        "section": "warnings/34071-1/6",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s6_c1",
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s6_c2"
        ]
      },
      {
        "section": "dosage/34068-7/10",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s10_c1"
        ]
      },
      {
        "section": "labelling/51945-4/12",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_84ef7b29-dd48-43d3-bda8-d6337bc22891_v21_s12_c1"
        ]
      }
    ]
  },
  {
    "setid": "b6752b08-4c93-4e5f-895d-40f189bd356d",
    "version": 5,
    "product_name": "Aripiprazole",
    "xml_sha256": "9102666244e738f5b85f21865e8ed850af47fdfc308c646a25f85c599f1f2809",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b6752b08-4c93-4e5f-895d-40f189bd356d&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: INCREASED MORTALITY IN ELDERLY PATIENTS WITH DEMENTIA-RELATED PSYCHOSIS AND SUICIDAL THOUGHTS AND BEHAVIORS WITH ANTIDEPRESSANT DRUGS",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Schizophrenia",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s5_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s5_c2"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Bipolar I Disorder",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.4 Irritability Associated with Autistic Disorder",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.5 Tourette's Disorder",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.6 Dosage Adjustments for Cytochrome P450 Considerations",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s9_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s9_c2"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Increased Mortality in Elderly Patients with Dementia-Related Psychosis",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Cerebrovascular Adverse Events, Including Stroke",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Suicidal Thoughts and Behaviors in Children, Adolescents, and Young Adults",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s15_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s15_c2",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s15_c3",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s15_c4",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s15_c5"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Neuroleptic Malignant Syndrome (NMS)",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s16_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 Tardive Dyskinesia",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s17_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s17_c2"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Metabolic Changes",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c2",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c3",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c4",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c5",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c6",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c7",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c8",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c9",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s18_c10"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s19_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s19_c2",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s19_c3"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.7 Pathological Gambling and Other Compulsive Behaviors",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.8 Orthostatic Hypotension",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.9 Falls",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.10 Leukopenia, Neutropenia, and Agranulocytosis",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.11 Seizures/Convulsions",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.12 Potential for Cognitive and Motor Impairment",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.13 Body Temperature Regulation",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.14 Suicide",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.15 Dysphagia",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s28_c1"
        ]
      },
      {
        "section": "labelling/34089-3/48",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s48_c1"
        ]
      },
      {
        "section": "warnings/34076-0/62",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s62_c1",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s62_c2",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s62_c3",
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s62_c4"
        ]
      },
      {
        "section": "labelling/51945-4/64",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_b6752b08-4c93-4e5f-895d-40f189bd356d_v5_s64_c1"
        ]
      }
    ]
  },
  {
    "setid": "69f9c6f8-a8df-4ddf-8fb1-2768eb099ada",
    "version": 1,
    "product_name": "Alendronate Sodium",
    "xml_sha256": "72414ddd8e5783995d785a85387fbb26ac8f896a50279fd0cc2eac2d0e04aaac",
    "effective_date": "2026-10-30",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=69f9c6f8-a8df-4ddf-8fb1-2768eb099ada&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Treatment of Osteoporosis in Postmenopausal Women",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Prevention of Osteoporosis in Postmenopausal Women",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Treatment to Increase Bone Mass in Men with Osteoporosis",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.4 Treatment of Glucocorticoid-Induced Osteoporosis",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.5 Treatment of Paget's Disease of Bone",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s8_c1"
        ]
      },
      {
        "section": "labelling/42229-5/9",
        "title": "1.6 Important Limitations of Use",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.1 Treatment of Osteoporosis in Postmenopausal Women",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.2 Prevention of Osteoporosis in Postmenopausal Women",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.3 Treatment to Increase Bone Mass in Men with Osteoporosis",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.4 Treatment of Glucocorticoid-Induced Osteoporosis",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.5 Treatment of Paget's Disease of Bone",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s15_c1"
        ]
      },
      {
        "section": "dosage/42229-5/16",
        "title": "2.6 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s16_c1"
        ]
      },
      {
        "section": "dosage/42229-5/17",
        "title": "2.7 Recommendations for Calcium and Vitamin D Supplementation",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s17_c1"
        ]
      },
      {
        "section": "dosage/42229-5/18",
        "title": "2.8 Administration Instructions for Missed Doses",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s18_c1"
        ]
      },
      {
        "section": "warnings/34070-3/20",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.1 Upper Gastrointestinal Adverse Reactions",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s22_c1",
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s22_c2"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.2 Mineral Metabolism",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.3 Musculoskeletal Pain",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.4 Osteonecrosis of the Jaw",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.5 Atypical Fractures Including Femoral Fractures",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s26_c1",
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s26_c2"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.6 Renal Impairment",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.7 Glucocorticoid-Induced Osteoporosis",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s28_c1"
        ]
      },
      {
        "section": "labelling/34089-3/44",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s44_c1"
        ]
      },
      {
        "section": "labelling/51945-4/72",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s72_c1"
        ]
      },
      {
        "section": "labelling/51945-4/73",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s73_c1"
        ]
      },
      {
        "section": "labelling/51945-4/74",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s74_c1"
        ]
      },
      {
        "section": "labelling/51945-4/75",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s75_c1"
        ]
      },
      {
        "section": "labelling/51945-4/76",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s76_c1"
        ]
      },
      {
        "section": "labelling/51945-4/77",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s77_c1"
        ]
      },
      {
        "section": "labelling/51945-4/78",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s78_c1"
        ]
      },
      {
        "section": "labelling/51945-4/79",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s79_c1"
        ]
      },
      {
        "section": "labelling/51945-4/80",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s80_c1"
        ]
      },
      {
        "section": "labelling/51945-4/81",
        "title": "",
        "chunk_ids": [
          "dailymed_69f9c6f8-a8df-4ddf-8fb1-2768eb099ada_v1_s81_c1"
        ]
      }
    ]
  },
  {
    "setid": "3f99b26b-79b9-4efb-aa2c-2868e1e126c8",
    "version": 5,
    "product_name": "Topiramate",
    "xml_sha256": "995ae4a4a6f39429921b1256acdaf3453719fc8f3334c3c396e0837d105ad7fe",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3f99b26b-79b9-4efb-aa2c-2868e1e126c8&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Monotherapy Epilepsy",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Adjunctive Therapy Epilepsy",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Migraine",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Dosing in Monotherapy Epilepsy",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s8_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Dosing in Adjunctive Therapy Epilepsy",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s9_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s9_c2"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Dosing for the Preventive Treatment of Migraine",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Administration Information",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Dosing in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.6 Dosing in Patients Undergoing Hemodialysis",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s13_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.1 Acute Myopia and Secondary Angle Closure Glaucoma Syndrome",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.2 Visual Field Defects",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.3 Oligohidrosis and Hyperthermia",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.4 Metabolic Acidosis",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s20_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s20_c2",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s20_c3",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s20_c4"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.5 Suicidal Behavior and Ideation",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s21_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s21_c2",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s21_c3"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.6 Cognitive/Neuropsychiatric Adverse Reactions",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s22_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s22_c2",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s22_c3",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s22_c4"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.7 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.8 Withdrawal of Antiepileptic Drugs",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.9 Decrease in Bone Mineral Density",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.10 Negative Effects on Growth (Height and Weight)",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.11 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)/Multiorgan Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.12 Serious Skin Reactions",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.13 Anaphylaxis and Angioedema",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.14 Hyperammonemia and Encephalopathy (Without and With Concomitant Valproic Acid Use)",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s30_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s30_c2"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.15 Kidney Stones",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s31_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s31_c2"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.16 Hypothermia with Concomitant Valproic Acid Use",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s32_c1"
        ]
      },
      {
        "section": "labelling/34089-3/54",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s54_c1"
        ]
      },
      {
        "section": "warnings/34076-0/68",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s68_c1",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s68_c2",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s68_c3",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s68_c4",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s68_c5",
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s68_c6"
        ]
      },
      {
        "section": "labelling/51945-4/70",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_3f99b26b-79b9-4efb-aa2c-2868e1e126c8_v5_s70_c1"
        ]
      }
    ]
  },
  {
    "setid": "25db7cc0-604c-3d6b-e063-6394a90a337f",
    "version": 6,
    "product_name": "Tizanidine",
    "xml_sha256": "14940da8b7aa68eff301f3f929b681e091a19bac90a3acb9f4f167da5cb1b26e",
    "effective_date": "2026-11-13",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=25db7cc0-604c-3d6b-e063-6394a90a337f&version=6",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Dosing Information",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s4_c1",
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s4_c2"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.2 Dosing in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.3 Dosing in Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.4 Drug Discontinuation",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s7_c1"
        ]
      },
      {
        "section": "warnings/34070-3/9",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.1 Hypotension",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.2 Risk of Liver Injury",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.3 Sedation",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.4 Hallucinosis/Psychotic-Like Symptoms",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.5 Interaction with CYP1A2 Inhibitors",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.6 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.7 Increased Risk of Adverse Reactions in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.8 Withdrawal Adverse Reactions",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s18_c1"
        ]
      },
      {
        "section": "labelling/34089-3/41",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s41_c1"
        ]
      },
      {
        "section": "warnings/34076-0/49",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s49_c1",
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s49_c2"
        ]
      },
      {
        "section": "labelling/51945-4/51",
        "title": "PRINCIPAL DISPLAY PANEL - 4mg",
        "chunk_ids": [
          "dailymed_25db7cc0-604c-3d6b-e063-6394a90a337f_v6_s51_c1"
        ]
      }
    ]
  },
  {
    "setid": "204592ba-a68f-452a-9987-1b33b7b6c4d5",
    "version": 106,
    "product_name": "olmesartan medoxomil / amlodipine besylate / hydrochlorothiazide",
    "xml_sha256": "4443f1baed1387c9b613a91eff5c721df83f1fc9c8217072c204afab363b198f",
    "effective_date": "2026-11-11",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=204592ba-a68f-452a-9987-1b33b7b6c4d5&version=106",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: FETAL TOXICITY",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s3_c1",
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s3_c2",
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s3_c3"
        ]
      },
      {
        "section": "dosage/34068-7/4",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/6",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s6_c1"
        ]
      },
      {
        "section": "warnings/42229-5/8",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s8_c1"
        ]
      },
      {
        "section": "warnings/42229-5/9",
        "title": "5.2 Hypotension in Volume-or Salt-Depleted Patients",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.3 Increased Angina and/or Myocardial Infarction",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.4 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s11_c1",
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s11_c2"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.5 Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.6 Electrolyte and Metabolic Imbalances",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.7 Postsympathectomy Patients",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.8 Systemic Lupus Erythematosus",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.9 Acute Myopia and Secondary Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.10 Sprue-like Enteropathy",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s17_c1"
        ]
      },
      {
        "section": "labelling/34089-3/34",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s34_c1",
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s34_c2",
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s34_c3"
        ]
      },
      {
        "section": "warnings/34076-0/44",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s44_c1",
          "dailymed_204592ba-a68f-452a-9987-1b33b7b6c4d5_v106_s44_c2"
        ]
      }
    ]
  },
  {
    "setid": "29ec1221-04d8-4b21-822e-2779fcaae62c",
    "version": 3,
    "product_name": "Amitriptyline Hydrochloride",
    "xml_sha256": "7829c001c49710123fa4f40f84ee69017c01abf5acc1cd701a794c88e70e8cdc",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=29ec1221-04d8-4b21-822e-2779fcaae62c&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s3_c1",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s3_c2"
        ]
      },
      {
        "section": "labelling/34067-9/5",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s5_c1"
        ]
      },
      {
        "section": "warnings/34070-3/6",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s6_c1"
        ]
      },
      {
        "section": "warnings/34071-1/7",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c1",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c2",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c3",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c4",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c5",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c6",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c7",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c8",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c9",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c10",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s7_c11"
        ]
      },
      {
        "section": "dosage/34068-7/12",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s12_c1",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s12_c2",
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s12_c3"
        ]
      },
      {
        "section": "labelling/51945-4/17",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s17_c1"
        ]
      },
      {
        "section": "labelling/51945-4/18",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_29ec1221-04d8-4b21-822e-2779fcaae62c_v3_s18_c1"
        ]
      }
    ]
  },
  {
    "setid": "e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd",
    "version": 4,
    "product_name": "Rivaroxaban",
    "xml_sha256": "f1704f526f3325256d72831653740e7f1108068e5ddc5be606bf45a03a9d759e",
    "effective_date": "2026-10-21",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s3_c1",
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s3_c2"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.7 Reduction of Risk of Major Cardiovascular Events in Patients with Coronary Artery Disease (CAD)",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.8 Reduction of Risk of Major Thrombotic Vascular Events in Patients with Peripheral Artery Disease (PAD), Including Patients after Lower Extremity Revascularization due to Symptomatic PAD",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.1 Recommended Dosage in Adults",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Switching to and from Rivaroxaban Tablets",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s10_c1",
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Discontinuation for Surgery and other Interventions",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Missed Dose",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.6 Administration Options",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s13_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.1 Increased Risk of Thrombotic Events after Premature Discontinuation",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.2 Risk of Bleeding",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s18_c1",
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s18_c2"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.3 Spinal/Epidural Anesthesia or Puncture",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s19_c1",
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s19_c2"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.4 Use in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.5 Use in Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.6 Use with P-gp and Strong CYP3A Inhibitors or Inducers",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.7 Risk of Pregnancy-Related Hemorrhage",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.8 Patients with Prosthetic Heart Valves",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.9 Acute PE in Hemodynamically Unstable Patients or Patients Who Require Thrombolysis or Pulmonary Embolectomy",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.10 Increased Risk of Thrombosis in Patients with Triple Positive Antiphospholipid Syndrome",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s26_c1"
        ]
      },
      {
        "section": "warnings/34072-9/40",
        "title": "8.5 Geriatric Use",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s40_c1"
        ]
      },
      {
        "section": "labelling/34089-3/44",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s44_c1"
        ]
      },
      {
        "section": "warnings/34076-0/55",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s55_c1",
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s55_c2",
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s55_c3"
        ]
      },
      {
        "section": "labelling/51945-4/57",
        "title": "PACKAGE LABEL - 60s",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s57_c1"
        ]
      },
      {
        "section": "labelling/51945-4/58",
        "title": "PACKAGE LABEL - 500s",
        "chunk_ids": [
          "dailymed_e98f6d83-5172-97a1-ee41-5d7d1d8ba2fd_v4_s58_c1"
        ]
      }
    ]
  },
  {
    "setid": "3f4e5db8-5bfb-4b24-8465-9757cbaad2be",
    "version": 3,
    "product_name": "FENOFIBRATE",
    "xml_sha256": "3bd483a9bdba5bb1286af1deceff50ab1651b1022040c1e7e085edb8fc2ee9b5",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3f4e5db8-5bfb-4b24-8465-9757cbaad2be&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Primary Hypercholesterolemia or Mixed Dyslipidemia",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Severe Hypertriglyceridemia",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Important Limitations of Use",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 General Considerations",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Primary Hypercholesterolemia or Mixed Dyslipidemia",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Severe Hypertriglyceridemia",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Geriatric Patients",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s12_c1"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Mortality and Coronary Heart Disease Morbidity",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s16_c1",
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s16_c2",
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s16_c3",
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s16_c4"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s17_c1",
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s17_c2"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Myopathy and Rhabdomyolysis",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Serum Creatinine",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.5 Cholelithiasis",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.6 Coumarin Anticoagulants",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.7 Pancreatitis",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.8 Hematologic Changes",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "Acute Hypersensitivity",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "Delayed Hypersensitivity",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.10 Venothromboembolic Disease",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.11 Paradoxical Decreases in HDL Cholesterol Levels",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s28_c1"
        ]
      },
      {
        "section": "labelling/34089-3/49",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s49_c1"
        ]
      },
      {
        "section": "warnings/34076-0/72",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s72_c1",
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s72_c2"
        ]
      },
      {
        "section": "labelling/51945-4/73",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_3f4e5db8-5bfb-4b24-8465-9757cbaad2be_v3_s73_c1"
        ]
      }
    ]
  },
  {
    "setid": "ab6c4a4b-97b3-3631-e053-2a95a90a614a",
    "version": 3,
    "product_name": "Paroxetine",
    "xml_sha256": "f164146ac37f29c4f8aa48fe98fa619ea205034b8e3dbb0f2477ae4011c8916e",
    "effective_date": "2026-01-01",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ab6c4a4b-97b3-3631-e053-2a95a90a614a&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "BOXED WARNING",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s4_c1"
        ]
      },
      {
        "section": "dosage/unknown/6",
        "title": "2.1 Administration Information",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s6_c1"
        ]
      },
      {
        "section": "dosage/unknown/7",
        "title": "2.2 Recommended Dosage for MDD, OCD, PD, and PTSD",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s7_c1"
        ]
      },
      {
        "section": "dosage/unknown/8",
        "title": "2.3 Recommended Dosage for SAD and GAD",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s8_c1"
        ]
      },
      {
        "section": "dosage/unknown/9",
        "title": "2.4 Screen for Bipolar Disorder Prior to Starting Paroxetine Tablets",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s9_c1"
        ]
      },
      {
        "section": "dosage/unknown/10",
        "title": "2.5 Recommended Dosage for Elderly Patients, Patients with Severe Renal Impairment, and Patients with Severe Hepatic Impairment",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s10_c1"
        ]
      },
      {
        "section": "dosage/unknown/11",
        "title": "2.6 Switching Patients to or From a Monoamine Oxidase Inhibitor (MAOI)",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s11_c1"
        ]
      },
      {
        "section": "dosage/unknown/12",
        "title": "2.7 Discontinuation of Treatment With Paroxetine Tablets",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s12_c1"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s14_c1"
        ]
      },
      {
        "section": "warnings/unknown/16",
        "title": "5.1 Suicidal Thoughts and Behaviors in Adolescents and Young Adults",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s16_c1",
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s16_c2"
        ]
      },
      {
        "section": "warnings/unknown/17",
        "title": "5.2 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s17_c1",
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s17_c2"
        ]
      },
      {
        "section": "warnings/unknown/18",
        "title": "5.3 Drug Interactions Leading to QT Prolongation",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s18_c1"
        ]
      },
      {
        "section": "warnings/unknown/19",
        "title": "5.4 Embryofetal Toxicity",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s19_c1"
        ]
      },
      {
        "section": "warnings/unknown/20",
        "title": "5.5 Increased Risk of Bleeding",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s20_c1"
        ]
      },
      {
        "section": "warnings/unknown/21",
        "title": "5.6 Activation of Mania or Hypomania",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s21_c1"
        ]
      },
      {
        "section": "warnings/unknown/22",
        "title": "5.7 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s22_c1"
        ]
      },
      {
        "section": "warnings/unknown/23",
        "title": "5.8 Seizures",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s23_c1"
        ]
      },
      {
        "section": "warnings/unknown/24",
        "title": "5.9 Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s24_c1"
        ]
      },
      {
        "section": "warnings/unknown/25",
        "title": "5.10 Hyponatremia",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s25_c1"
        ]
      },
      {
        "section": "warnings/unknown/26",
        "title": "5.11 Reduction of Efficacy of Tamoxifen",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s26_c1"
        ]
      },
      {
        "section": "warnings/unknown/27",
        "title": "5.12 Bone Fracture",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s27_c1"
        ]
      },
      {
        "section": "warnings/unknown/28",
        "title": "5.13 Sexual Dysfunction",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s28_c1"
        ]
      },
      {
        "section": "labelling/34089-3/41",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s41_c1"
        ]
      },
      {
        "section": "warnings/34076-0/56",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s56_c1",
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s56_c2",
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s56_c3",
          "dailymed_ab6c4a4b-97b3-3631-e053-2a95a90a614a_v3_s56_c4"
        ]
      }
    ]
  },
  {
    "setid": "73b8e5ab-86f8-44f8-b290-346acb81c9ae",
    "version": 3,
    "product_name": "Warfarin Sodium",
    "xml_sha256": "cc193e19c8e8fcec957f096c8d6c4e99265393005b2d1abb0b6348cdd18c83e3",
    "effective_date": "2026-11-09",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=73b8e5ab-86f8-44f8-b290-346acb81c9ae&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: BLEEDING RISK",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.1 Individualized Dosing",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.2 Recommended Target INR Ranges and Durations for Individual Indications",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s13_c1"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.3 Initial and Maintenance Dosing",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s14_c1"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s15_c1"
        ]
      },
      {
        "section": "dosage/42229-5/16",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s16_c1"
        ]
      },
      {
        "section": "dosage/42229-5/17",
        "title": "2.4 Monitoring to Achieve Optimal Anticoagulation",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s17_c1"
        ]
      },
      {
        "section": "dosage/42229-5/18",
        "title": "2.5 Renal Impairment",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s18_c1"
        ]
      },
      {
        "section": "dosage/42229-5/19",
        "title": "2.6 Missed Dose",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s19_c1"
        ]
      },
      {
        "section": "dosage/42229-5/20",
        "title": "2.7 Treatment During Dentistry and Surgery",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s20_c1"
        ]
      },
      {
        "section": "dosage/42229-5/22",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s22_c1"
        ]
      },
      {
        "section": "dosage/42229-5/23",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s23_c1"
        ]
      },
      {
        "section": "warnings/34070-3/25",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s25_c1",
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s25_c2"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.1 Hemorrhage",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.2 Tissue Necrosis",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.3 Calciphylaxis",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.4 Acute Kidney Injury",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.5 Systemic Atheroemboli and Cholesterol Microemboli",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.6 Limb Ischemia, Necrosis, and Gangrene in Patients with HIT and HITTS",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s32_c1"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.7 Use in Pregnant Women with Mechanical Heart Valves",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.8 Other Clinical Settings with Increased Risks",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.9 Endogenous Factors Affecting INR",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s35_c1"
        ]
      },
      {
        "section": "labelling/34089-3/64",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s64_c1",
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s64_c2"
        ]
      },
      {
        "section": "warnings/34076-0/85",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s85_c1"
        ]
      },
      {
        "section": "warnings/42229-5/86",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s86_c1",
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s86_c2"
        ]
      },
      {
        "section": "warnings/42229-5/87",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s87_c1"
        ]
      },
      {
        "section": "warnings/42229-5/88",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s88_c1"
        ]
      },
      {
        "section": "warnings/42229-5/89",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s89_c1"
        ]
      },
      {
        "section": "labelling/51945-4/92",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_73b8e5ab-86f8-44f8-b290-346acb81c9ae_v3_s92_c1"
        ]
      }
    ]
  },
  {
    "setid": "495f22cc-18d4-4264-9313-7ab20e7b5bc9",
    "version": 6,
    "product_name": "Valacyclovir Hydrochloride",
    "xml_sha256": "4841aa3051581f576f885847a5514688406cb13dbad8e5abba3446c7c29c502e",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=495f22cc-18d4-4264-9313-7ab20e7b5bc9&version=6",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Adult Patients",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s4_c1",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s4_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Pediatric Patients",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Limitations of Use",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s6_c1"
        ]
      },
      {
        "section": "dosage/34068-7/7",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Adult Dosing Recommendations",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s8_c1",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s8_c2"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Pediatric Dosing Recommendations",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Extemporaneous Preparation of Oral Suspension",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s10_c1",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s11_c1",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s11_c2",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s11_c3"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Thrombotic Thrombocytopenic Purpura/Hemolytic Uremic Syndrome (TTP/HUS)",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 Acute Renal Failure",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Central Nervous System Effects",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Severe Cutaneous Adverse Reactions",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s18_c1"
        ]
      },
      {
        "section": "labelling/34089-3/31",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s31_c1"
        ]
      },
      {
        "section": "warnings/34076-0/44",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s44_c1",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s44_c2",
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s44_c3"
        ]
      },
      {
        "section": "labelling/51945-4/46",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_495f22cc-18d4-4264-9313-7ab20e7b5bc9_v6_s46_c1"
        ]
      }
    ]
  },
  {
    "setid": "5e55526f-bb34-4b67-85ea-b2765e8066bb",
    "version": 2,
    "product_name": "Methocarbamol",
    "xml_sha256": "aaf7ec945c3140dcec6df156e2564725985c3bd67a9b383cd62ff7dfec96a8db",
    "effective_date": "2026-11-05",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5e55526f-bb34-4b67-85ea-b2765e8066bb&version=2",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/7",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s7_c1"
        ]
      },
      {
        "section": "warnings/34070-3/8",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s8_c1"
        ]
      },
      {
        "section": "warnings/34071-1/9",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "Use i n Activities Requiring Mental Alertness",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s10_c1"
        ]
      },
      {
        "section": "warnings/34076-0/12",
        "title": "Information for Patients",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s12_c1"
        ]
      },
      {
        "section": "dosage/34068-7/22",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_5e55526f-bb34-4b67-85ea-b2765e8066bb_v2_s22_c1"
        ]
      }
    ]
  },
  {
    "setid": "850566b1-0c8e-42bc-85fa-c8ee710f34ba",
    "version": 2,
    "product_name": "Diltiazem Hydrochloride",
    "xml_sha256": "58c228efa2c1425c32cf8246443a49e61c9dcad2e7de5288697b8e00edaf9ca4",
    "effective_date": "2026-11-04",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=850566b1-0c8e-42bc-85fa-c8ee710f34ba&version=2",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s2_c1",
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s2_c2"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s5_c1"
        ]
      },
      {
        "section": "warnings/34071-1/6",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s6_c1",
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s6_c2"
        ]
      },
      {
        "section": "warnings/34072-9/8",
        "title": "General",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s8_c1"
        ]
      },
      {
        "section": "dosage/34068-7/17",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s17_c1",
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s17_c2"
        ]
      },
      {
        "section": "labelling/51945-4/19",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s19_c1",
          "dailymed_850566b1-0c8e-42bc-85fa-c8ee710f34ba_v2_s19_c2"
        ]
      }
    ]
  },
  {
    "setid": "95755a7b-4a9f-45ea-a381-d3f661150efe",
    "version": 28,
    "product_name": "Baclofen",
    "xml_sha256": "6c29082cb6b89d324a83493b9ee7717ac916727c345d60354acb48b81c19a203",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=95755a7b-4a9f-45ea-a381-d3f661150efe&version=28",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_95755a7b-4a9f-45ea-a381-d3f661150efe_v28_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_95755a7b-4a9f-45ea-a381-d3f661150efe_v28_s4_c1"
        ]
      },
      {
        "section": "warnings/34071-1/6",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_95755a7b-4a9f-45ea-a381-d3f661150efe_v28_s6_c1",
          "dailymed_95755a7b-4a9f-45ea-a381-d3f661150efe_v28_s6_c2"
        ]
      },
      {
        "section": "dosage/34068-7/11",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_95755a7b-4a9f-45ea-a381-d3f661150efe_v28_s11_c1"
        ]
      },
      {
        "section": "labelling/51945-4/13",
        "title": "Package/Label Display Panel",
        "chunk_ids": [
          "dailymed_95755a7b-4a9f-45ea-a381-d3f661150efe_v28_s13_c1"
        ]
      }
    ]
  },
  {
    "setid": "1bf70380-8272-4c0d-8841-d39ef2772351",
    "version": 13,
    "product_name": "Sumatriptan Succinate",
    "xml_sha256": "7969ee602d5ac6681bd987ad92c32f63bf736a6f012b64a10e063f09f815cc0c",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1bf70380-8272-4c0d-8841-d39ef2772351&version=13",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Dosing Information",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "Use after Sumatriptan Injection",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Dosing in Patients with Hepatic Impairment",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s6_c1"
        ]
      },
      {
        "section": "warnings/34070-3/8",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s8_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.1 Myocardial Ischemia, Myocardial Infarction, and Prinzmetal\u2019s Angina",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.2 Arrhythmias",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.3 Chest, Throat, Neck, and/or Jaw Pain/Tightness/Pressure",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.4 Cerebrovascular Events",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.5 Other Vasospasm Reactions",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.6 Medication Overuse Headache",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.7 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.8 Increase in Blood Pressure",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.9 Anaphylactic/Anaphylactoid Reactions",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.10 Seizures",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s19_c1"
        ]
      },
      {
        "section": "labelling/34089-3/43",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s43_c1"
        ]
      },
      {
        "section": "warnings/34076-0/74",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s74_c1",
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s74_c2",
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s74_c3"
        ]
      },
      {
        "section": "labelling/51945-4/76",
        "title": "PRICIPAL DISPLAY PANEL \u2013 25 mg",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s76_c1"
        ]
      },
      {
        "section": "labelling/51945-4/77",
        "title": "PRICIPAL DISPLAY PANEL \u2013 50 mg",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s77_c1"
        ]
      },
      {
        "section": "labelling/51945-4/78",
        "title": "PRICIPAL DISPLAY PANEL \u2013 100 mg",
        "chunk_ids": [
          "dailymed_1bf70380-8272-4c0d-8841-d39ef2772351_v13_s78_c1"
        ]
      }
    ]
  },
  {
    "setid": "b1a6714a-cdeb-4502-b44b-a4f08cc1cde1",
    "version": 1,
    "product_name": "Esomeprazole Magnesium",
    "xml_sha256": "fbe026a9796e7988d8f262f54817b9e565dc1d2681a8574869d0af26199179ab",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b1a6714a-cdeb-4502-b44b-a4f08cc1cde1&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Healing of Erosive Esophagitis (EE)",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Maintenance of Healing of EE",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Treatment of Symptomatic GERD",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.4 Risk Reduction of Nonsteroidal Anti-Inflammatory Drugs (NSAID)-Associated Gastric Ulcer",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.5 Helicobacter pylori Eradication to Reduce the Risk of Duodenal Ulcer Recurrence",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.6 Pathological Hypersecretory Conditions Including Zollinger-Ellison Syndrome",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.1 Recommended Dosage in Adults by Indication",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s10_c1",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s10_c2"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.2 Recommended Dosage in Pediatric Patients by Indication",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.3 Preparation and Administration Instructions",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s12_c1",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s12_c2"
        ]
      },
      {
        "section": "warnings/34070-3/14",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Presence of Gastric Malignancy",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Acute Tubulointerstitial Nephritis",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Clostridium difficile -Associated Diarrhea",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Bone Fracture",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.5 Severe Cutaneous Adverse Reactions",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.6 Cutaneous and Systemic Lupus Erythematosus",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s21_c1",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s21_c2"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.7 Interaction with Clopidogrel",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.8 Cyanocobalamin (Vitamin B-12) Deficiency",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.9 Hypomagnesemia and Mineral Metabolism",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.10 Interaction with St. John\u2019s Wort or Rifampin",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.11 Interactions with Diagnostic Investigations for Neuroendocrine Tumors",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.12 Interaction with Methotrexate",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.13 Fundic Gland Polyps",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s28_c1"
        ]
      },
      {
        "section": "labelling/34089-3/40",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s40_c1",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s40_c2"
        ]
      },
      {
        "section": "warnings/34076-0/59",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s59_c1",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s59_c2",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s59_c3",
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s59_c4"
        ]
      },
      {
        "section": "labelling/51945-4/61",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_b1a6714a-cdeb-4502-b44b-a4f08cc1cde1_v1_s61_c1"
        ]
      }
    ]
  },
  {
    "setid": "58e9b4c6-531f-49c4-a640-6953e70892fe",
    "version": 16,
    "product_name": "Mirtazapine",
    "xml_sha256": "bd93460a64c9f16daf494ae9959d2df180ad07304c08dad9b70098a033617c3e",
    "effective_date": "2026-10-21",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=58e9b4c6-531f-49c4-a640-6953e70892fe&version=16",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: SUICIDAL THOUGHTS AND BEHAVIORS",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Recommended Dosage",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.3 Screen for Bipolar Disorder Prior to Starting Mirtazapine Tablets",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.4 Switching Patients to or from a Monoamine Oxidase Inhibitor Antidepressant",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.5 Dosage Modifications Due to Drug Interactions",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.6 Discontinuation of Mirtazapine Tablets Treatment",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s9_c1"
        ]
      },
      {
        "section": "warnings/34070-3/11",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.1 Suicidal Thoughts and Behaviors in Adolescents and Young Adults",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s13_c1",
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s13_c2"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.2 Agranulocytosis",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.3 Serotonin Syndrome",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s15_c1",
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s15_c2"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.4 Angle-Closure Glaucoma",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.5 QT Prolongation and Torsades de Pointes",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.6 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.7 Increased Appetite and Weight Gain",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.8 Somnolence",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.9 Activation of Mania or Hypomania",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.10 Seizures",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.11 Elevated Cholesterol and Triglycerides",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.12 Hyponatremia",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.13 Transaminase Elevations",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.14 Discontinuation Syndrome",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.15 Use in Patients with Concomitant Illness",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s27_c1"
        ]
      },
      {
        "section": "labelling/34089-3/39",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s39_c1"
        ]
      },
      {
        "section": "warnings/34076-0/48",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s48_c1",
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s48_c2",
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s48_c3",
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s48_c4"
        ]
      },
      {
        "section": "labelling/51945-4/50",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 15 mg (30 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s50_c1"
        ]
      },
      {
        "section": "labelling/51945-4/51",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 7.5 mg (30 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s51_c1"
        ]
      },
      {
        "section": "labelling/51945-4/52",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 30 mg (30 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s52_c1"
        ]
      },
      {
        "section": "labelling/51945-4/53",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 45 mg (30 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_58e9b4c6-531f-49c4-a640-6953e70892fe_v16_s53_c1"
        ]
      }
    ]
  },
  {
    "setid": "5feca839-8554-739b-e063-6394a90a4e65",
    "version": 1,
    "product_name": "Levetiracetam",
    "xml_sha256": "ccad3cc22833dd4a9decddface1a01b43f4b50bee8c3d9fa2478d8df480d4fab",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5feca839-8554-739b-e063-6394a90a4e65&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/4",
        "title": "1.1 Partial-Onset Seizures",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.2 Myoclonic Seizures in Patients with Juvenile Myoclonic Epilepsy",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.3 Primary Generalized Tonic-Clonic Seizures",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Dosing for Partial-Onset Seizures",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s9_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s9_c2",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s9_c3"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Dosing for Myoclonic Seizures in Patients 12 Years of Age and Older With Juvenile Myoclonic Epilepsy",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Dosing for Primary Generalized Tonic-Clonic Seizures",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Dosage Adjustments in Adult Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.6 Discontinuation of Levetiracetam Tablets",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.1 Behavioral Abnormalities and Psychotic Symptoms",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s17_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s17_c2",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s17_c3"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.2 Suicidal Behavior and Ideation",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s18_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s18_c2",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s18_c3"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.3 Somnolence and Fatigue",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s19_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s19_c2"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.4 Anaphylaxis and Angioedema",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.5 Serious Dermatological Reactions",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.6 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS) /Multiorgan Hypersensitivity",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.7 Coordination Difficulties",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.8 Withdrawal Seizures",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.9 Hematologic Abnormalities",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s25_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s25_c2"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.10 Increase in Blood Pressure",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.11 Seizure Control During Pregnancy",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s27_c1"
        ]
      },
      {
        "section": "labelling/34089-3/41",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s41_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s41_c2"
        ]
      },
      {
        "section": "warnings/34076-0/55",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s55_c1",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s55_c2",
          "dailymed_5feca839-8554-739b-e063-6394a90a4e65_v1_s55_c3"
        ]
      }
    ]
  },
  {
    "setid": "415bd983-86f3-4f38-917a-9805024f31cb",
    "version": 13,
    "product_name": "Tadalafil",
    "xml_sha256": "b22e5c435aba5387bda0cff92bcda10fc275bfa28756c78336a391412c40dcdf",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=415bd983-86f3-4f38-917a-9805024f31cb&version=13",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/42229-5/3",
        "title": "1.1 Erectile Dysfunction",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Benign Prostatic Hyperplasia",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Erectile Dysfunction and Benign Prostatic Hyperplasia",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.4 Limitation of Use",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s6_c1"
        ]
      },
      {
        "section": "dosage/34068-7/7",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.1 Tadalafil Tablets for Use as Needed for Erectile Dysfunction",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.2 Tadalafil tablets for Once Daily Use for Erectile Dysfunction",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.3 Tadalafil Tablets for Once Daily Use for Benign Prostatic Hyperplasia",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.4 Tadalafil Tablets for Once Daily Use for Erectile Dysfunction and Benign Prostatic Hyperplasia",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s11_c1"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.5 Use with Food",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s12_c1"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.6 Use in Specific Populations",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s13_c1",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s13_c2"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.7 Concomitant Medications",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s14_c1",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s14_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "4.1 Nitrates",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "4.2 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "4.3 Concomitant Guanylate Cyclase (GC) Stimulators",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s19_c1"
        ]
      },
      {
        "section": "warnings/43685-7/20",
        "title": "5 WARNINGS AND PRECAUTIONS",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.1 Cardiovascular",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s21_c1",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s21_c2",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s21_c3"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.2 Potential for Drug Interactions When Taking Tadalafil tablets for Once Daily Use",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.3 Prolonged Erection",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.4 Effects on the Eye",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s24_c1",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s24_c2"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "5.5 Sudden Hearing Loss",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s25_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.6 Alpha-blockers and Antihypertensives",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s26_c1",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s26_c2"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.7 Renal Impairment",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s27_c1",
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s27_c2"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.8 Hepatic Impairment",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.9 Alcohol",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.10 Concomitant Use of Potent Inhibitors of Cytochrome P450 3A4 (CYP3A4)",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.11 Combination With Other PDE5 Inhibitors or Erectile Dysfunction Therapies",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.12 Effects on Bleeding",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s32_c1"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.13 Counseling Patients About Sexually Transmitted Diseases",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.14 Consideration of Other Urological Conditions Prior to Initiating Treatment for BPH",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.15 Risk of Allergic Reactions due to Tartrazine",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s35_c1"
        ]
      },
      {
        "section": "labelling/34089-3/52",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s52_c1"
        ]
      },
      {
        "section": "warnings/34076-0/66",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s66_c1"
        ]
      },
      {
        "section": "warnings/42229-5/67",
        "title": "17.1 Nitrates",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s67_c1"
        ]
      },
      {
        "section": "warnings/42229-5/68",
        "title": "17.2 Guanylate Cyclase (GC) Stimulators",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s68_c1"
        ]
      },
      {
        "section": "warnings/42229-5/69",
        "title": "17.3 Cardiovascular Considerations",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s69_c1"
        ]
      },
      {
        "section": "warnings/42229-5/70",
        "title": "17.4 Concomitant Use with Drugs Which Lower Blood Pressure",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s70_c1"
        ]
      },
      {
        "section": "warnings/42229-5/71",
        "title": "17.5 Potential for Drug Interactions When Taking tadalafil tablets for Once Daily Use",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s71_c1"
        ]
      },
      {
        "section": "warnings/42229-5/72",
        "title": "17.6 Priapism",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s72_c1"
        ]
      },
      {
        "section": "warnings/42229-5/73",
        "title": "17.7 Sudden Loss of Vision",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s73_c1"
        ]
      },
      {
        "section": "warnings/42229-5/74",
        "title": "17.8 Sudden Hearing Loss",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s74_c1"
        ]
      },
      {
        "section": "warnings/42229-5/75",
        "title": "17.9 Alcohol",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s75_c1"
        ]
      },
      {
        "section": "warnings/42229-5/76",
        "title": "17.10 Sexually Transmitted Disease",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s76_c1"
        ]
      },
      {
        "section": "warnings/42229-5/77",
        "title": "17.11 Recommended Administration",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s77_c1"
        ]
      },
      {
        "section": "labelling/51945-4/79",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_415bd983-86f3-4f38-917a-9805024f31cb_v13_s79_c1"
        ]
      }
    ]
  },
  {
    "setid": "86c1bdae-c749-4ec3-90f6-7ebe8e76c461",
    "version": 32,
    "product_name": "Nifedipine",
    "xml_sha256": "5a384e44600d0e0fd80831220bdc4c03a9648dd6ec919d3a69d70d38255fa1d1",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=86c1bdae-c749-4ec3-90f6-7ebe8e76c461&version=32",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s3_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "System Components and Performance",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/15",
        "title": "I. Vasospastic Angina",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s15_c1"
        ]
      },
      {
        "section": "labelling/42229-5/16",
        "title": "II. Chronic Stable Angina (Classical Effort-Associated Angina)",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s16_c1"
        ]
      },
      {
        "section": "labelling/42229-5/17",
        "title": "III. Hypertension",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s17_c1",
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s17_c2"
        ]
      },
      {
        "section": "warnings/34070-3/18",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "Excessive Hypotension",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "Increased Angina and/or Myocardial Infarction",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "Beta Blocker Withdrawal",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "Congestive Heart Failure",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "Gastrointestinal Obstruction Requiring Surgery",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s24_c1"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "Gastrointestinal Ulcers",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s25_c1"
        ]
      },
      {
        "section": "warnings/34072-9/27",
        "title": "General-Hypotension",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "Peripheral Edema",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s28_c1"
        ]
      },
      {
        "section": "warnings/34076-0/29",
        "title": "Information for Patients",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s29_c1"
        ]
      },
      {
        "section": "dosage/34068-7/45",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s45_c1",
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s45_c2"
        ]
      },
      {
        "section": "dosage/42229-5/46",
        "title": "Co-Administration with Other Antianginal Drugs",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s46_c1"
        ]
      },
      {
        "section": "labelling/51945-4/48",
        "title": "PRINCIPAL DISPLAY PANEL - 30MG",
        "chunk_ids": [
          "dailymed_86c1bdae-c749-4ec3-90f6-7ebe8e76c461_v32_s48_c1"
        ]
      }
    ]
  },
  {
    "setid": "0c7f9bd0-6c0a-4521-b77a-3582faa96874",
    "version": 3,
    "product_name": "Hydralazine Hydrochloride",
    "xml_sha256": "da5745c7982256c269c421b43afa02679191741a49d97766d24e278c58026d61",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=0c7f9bd0-6c0a-4521-b77a-3582faa96874&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_0c7f9bd0-6c0a-4521-b77a-3582faa96874_v3_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_0c7f9bd0-6c0a-4521-b77a-3582faa96874_v3_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_0c7f9bd0-6c0a-4521-b77a-3582faa96874_v3_s5_c1"
        ]
      },
      {
        "section": "warnings/34071-1/6",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_0c7f9bd0-6c0a-4521-b77a-3582faa96874_v3_s6_c1"
        ]
      },
      {
        "section": "dosage/34068-7/18",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_0c7f9bd0-6c0a-4521-b77a-3582faa96874_v3_s18_c1"
        ]
      },
      {
        "section": "labelling/51945-4/20",
        "title": "PACKAGE LABEL.PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_0c7f9bd0-6c0a-4521-b77a-3582faa96874_v3_s20_c1"
        ]
      }
    ]
  },
  {
    "setid": "2794f86b-d521-414b-8154-5dd1e2519653",
    "version": 17,
    "product_name": "Glimepiride",
    "xml_sha256": "67b1c28f6da87d9912fff5376b7532f8d642cd787cdf75f21b803ba7d029661d",
    "effective_date": "2026-11-13",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2794f86b-d521-414b-8154-5dd1e2519653&version=17",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Recommended Dosing",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/6",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s6_c1"
        ]
      },
      {
        "section": "warnings/42229-5/9",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.2 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.3 Hemolytic Anemia",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.4 Increased Risk of Cardiovascular Mortality with Sulfonylureas",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s12_c1",
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s12_c2"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.5 Macrovascular Outcomes",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s13_c1"
        ]
      },
      {
        "section": "labelling/34089-3/34",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/62",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s62_c1"
        ]
      },
      {
        "section": "labelling/51945-4/64",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_2794f86b-d521-414b-8154-5dd1e2519653_v17_s64_c1"
        ]
      }
    ]
  },
  {
    "setid": "8d252dab-e868-42d3-95ea-69423d909e84",
    "version": 12,
    "product_name": "Pioglitazone Hydrochloride and Metformin Hydrochloride",
    "xml_sha256": "0734e20fa1475f020a6c0c1019643f4c42cf92eea15ac9666518689a3d781363",
    "effective_date": "2026-10-14",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8d252dab-e868-42d3-95ea-69423d909e84&version=12",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: CONGESTIVE HEART FAILURE and LACTIC ACIDOSIS",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s3_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s3_c2"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.1 Important Dosage and Administration Information",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Recommended Dosage and Administration",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s7_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s7_c2"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Recommendations for Use in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.4 Recommendations for Congestive Heart Failure",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/10",
        "title": "2.5 Coadministration with Strong CYP2C8 Inhibitors",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s10_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.6 Discontinuation for Iodinated Contrast Imaging Procedures",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s11_c1"
        ]
      },
      {
        "section": "warnings/34070-3/13",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.1 Congestive Heart Failure",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.2 Lactic Acidosis",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s16_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s16_c2",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s16_c3",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s16_c4",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s16_c5"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.3 Edema",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.4 Hypoglycemia with Concomitant Use with Insulin or Insulin Secretagogues",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.5 Hepatic Effects",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s19_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s19_c2"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.6 Urinary Bladder Tumors",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s20_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s20_c2",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s20_c3"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.7 Fractures",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.8 Macular Edema",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.9 Vitamin B 12 Deficiency",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s23_c1"
        ]
      },
      {
        "section": "labelling/34089-3/45",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s45_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s45_c2"
        ]
      },
      {
        "section": "warnings/34076-0/57",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s57_c1",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s57_c2",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s57_c3",
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s57_c4"
        ]
      },
      {
        "section": "labelling/51945-4/59",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 15 mg/500 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s59_c1"
        ]
      },
      {
        "section": "labelling/51945-4/60",
        "title": "PACKAGE LABEL-PRINCIPAL DISPLAY PANEL - 15 mg/850 mg (60 Tablet Bottle)",
        "chunk_ids": [
          "dailymed_8d252dab-e868-42d3-95ea-69423d909e84_v12_s60_c1"
        ]
      }
    ]
  },
  {
    "setid": "5ca218af-b3f4-512a-e063-6394a90a3ec6",
    "version": 1,
    "product_name": "HYDROXYCHLOROQUINE SULFATE",
    "xml_sha256": "e2a1ba88322ecb4e44fd86d38f69f27d3314c3314073e9b389eb270852876563",
    "effective_date": "2026-09-29",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5ca218af-b3f4-512a-e063-6394a90a3ec6&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/unknown/4",
        "title": "1.1 Malaria",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s4_c1"
        ]
      },
      {
        "section": "labelling/unknown/5",
        "title": "1.2 Rheumatoid Arthritis",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s5_c1"
        ]
      },
      {
        "section": "labelling/unknown/6",
        "title": "1.3 Systemic Lupus Erythematosus",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s6_c1"
        ]
      },
      {
        "section": "labelling/unknown/7",
        "title": "1.4 Chronic Discoid Lupus Erythematosus",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s7_c1"
        ]
      },
      {
        "section": "dosage/unknown/9",
        "title": "2.1 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s9_c1"
        ]
      },
      {
        "section": "dosage/unknown/10",
        "title": "2.2 Dosage for Malaria in Adult and Pediatric Patients",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s10_c1",
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s10_c2"
        ]
      },
      {
        "section": "dosage/unknown/11",
        "title": "2.3 Dosage for Rheumatoid Arthritis in Adults",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s11_c1"
        ]
      },
      {
        "section": "dosage/unknown/12",
        "title": "2.4 Dosage for Systemic Lupus Erythematosus in Adults",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s12_c1"
        ]
      },
      {
        "section": "dosage/unknown/13",
        "title": "2.5 Dosage for Chronic Discoid Lupus Erythematosus in Adults",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/34070-3/15",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/unknown/17",
        "title": "5.1 Cardiomypathy and Ventricular Arrhythmias",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s17_c1",
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s17_c2"
        ]
      },
      {
        "section": "warnings/unknown/18",
        "title": "5.2 Retinal Toxicity",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s18_c1",
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s18_c2"
        ]
      },
      {
        "section": "warnings/unknown/19",
        "title": "5.3 Serious Skin Reactions",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/unknown/20",
        "title": "5.4 Worsening of Psoriasis",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/unknown/21",
        "title": "5.5 Risks Associated with Use in Porphyria",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s21_c1",
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s21_c2"
        ]
      },
      {
        "section": "warnings/unknown/22",
        "title": "5.6 Hematologic Toxicity",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s22_c1"
        ]
      },
      {
        "section": "warnings/unknown/23",
        "title": "5.7 Hemolytic Anemia Associated with G6PD Deficiency",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s23_c1"
        ]
      },
      {
        "section": "warnings/unknown/24",
        "title": "5.8 Skeletal Muscle Myopathy or Neuropathy",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s24_c1"
        ]
      },
      {
        "section": "warnings/unknown/25",
        "title": "5.9 Neuropsychiatric Reactions Including Suicidality",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s25_c1"
        ]
      },
      {
        "section": "warnings/unknown/26",
        "title": "5.10 Hypoglycemia",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s26_c1"
        ]
      },
      {
        "section": "warnings/unknown/27",
        "title": "5.11 Renal Toxicity",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s27_c1"
        ]
      },
      {
        "section": "labelling/34089-3/49",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s49_c1"
        ]
      },
      {
        "section": "warnings/34076-0/59",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s59_c1",
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s59_c2",
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s59_c3"
        ]
      },
      {
        "section": "labelling/51945-4/61",
        "title": "PRINCIPAL DISPLAY PANEL - 200mg",
        "chunk_ids": [
          "dailymed_5ca218af-b3f4-512a-e063-6394a90a3ec6_v1_s61_c1"
        ]
      }
    ]
  },
  {
    "setid": "ce4afef1-22c1-4a1c-a102-a32fb6a2e045",
    "version": 3,
    "product_name": "Nitrofurantoin Macrocrystals",
    "xml_sha256": "2fa02a4d9fc392a7c991d8be396c521f612a3bd9766eec0dd477039c394b1d50",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ce4afef1-22c1-4a1c-a102-a32fb6a2e045&version=3",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/6",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s6_c1",
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s6_c2"
        ]
      },
      {
        "section": "warnings/34070-3/7",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s7_c1"
        ]
      },
      {
        "section": "warnings/34071-1/8",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s8_c1",
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s8_c2",
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s8_c3"
        ]
      },
      {
        "section": "dosage/34068-7/12",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s12_c1"
        ]
      },
      {
        "section": "labelling/51945-4/14",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 50 mg 50UD",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s14_c1"
        ]
      },
      {
        "section": "labelling/51945-4/15",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 50 mg 100UD",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s15_c1"
        ]
      },
      {
        "section": "labelling/51945-4/16",
        "title": "Package/Label Display Panel \u2013 Blister \u2013 50 mg",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s16_c1"
        ]
      },
      {
        "section": "labelling/51945-4/17",
        "title": "Package/Label Display Panel \u2013 Carton \u2013 100 mg",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s17_c1"
        ]
      },
      {
        "section": "labelling/51945-4/18",
        "title": "Package/Label Display Panel \u2013 Blister \u2013 100 mg",
        "chunk_ids": [
          "dailymed_ce4afef1-22c1-4a1c-a102-a32fb6a2e045_v3_s18_c1"
        ]
      }
    ]
  },
  {
    "setid": "b52bdaf7-3b54-4165-9ab0-9dfa08170e47",
    "version": 23,
    "product_name": "clindamycin phosphate",
    "xml_sha256": "b371679d311afea46a1a9b97495c043e70bd0f3f640d89cf923379d5853d9806",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b52bdaf7-3b54-4165-9ab0-9dfa08170e47&version=23",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/3",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s3_c1"
        ]
      },
      {
        "section": "labelling/34067-9/11",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s11_c1"
        ]
      },
      {
        "section": "warnings/34070-3/12",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s12_c1"
        ]
      },
      {
        "section": "warnings/34071-1/13",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s13_c1",
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s13_c2"
        ]
      },
      {
        "section": "warnings/34072-9/15",
        "title": "General",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s15_c1"
        ]
      },
      {
        "section": "warnings/34076-0/16",
        "title": "Information for the Patient:",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s16_c1"
        ]
      },
      {
        "section": "dosage/34068-7/31",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s31_c1"
        ]
      },
      {
        "section": "labelling/51945-4/38",
        "title": "PRINCIPAL DISPLAY PANEL - 40 gram Tube Label",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s38_c1"
        ]
      },
      {
        "section": "labelling/51945-4/39",
        "title": "PRINCIPAL DISPLAY PANEL - 40 gram Tube Carton",
        "chunk_ids": [
          "dailymed_b52bdaf7-3b54-4165-9ab0-9dfa08170e47_v23_s39_c1"
        ]
      }
    ]
  },
  {
    "setid": "5723eaf9-8659-4730-b792-4e4c33690ccb",
    "version": 28,
    "product_name": "Ciprofloxacin",
    "xml_sha256": "2fc161647e4be43f8d52412d9a7c61b9551b1231a65dbca4c562683a5f0fbe73",
    "effective_date": "2026-10-15",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5723eaf9-8659-4730-b792-4e4c33690ccb&version=28",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: SERIOUS ADVERSE REACTIONS INCLUDING TENDINITIS, TENDON RUPTURE, PERIPHERAL NEUROPATHY, CENTRAL NERVOUS SYSTEM EFFECTS AND EXACERBATION OF MYASTHENIA GRAVIS",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.1 Skin and Skin Structure Infections",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Bone and Joint Infections",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s6_c1"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.3 Complicated Intra-Abdominal Infections",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.4 Infectious Diarrhea",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s8_c1"
        ]
      },
      {
        "section": "labelling/42229-5/9",
        "title": "1.5 Typhoid Fever (Enteric Fever)",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s9_c1"
        ]
      },
      {
        "section": "labelling/42229-5/10",
        "title": "1.6 Uncomplicated Cervical and Urethral Gonorrhea",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s10_c1"
        ]
      },
      {
        "section": "labelling/42229-5/11",
        "title": "1.7 Inhalational Anthrax (Post-Exposure)",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s11_c1"
        ]
      },
      {
        "section": "labelling/42229-5/12",
        "title": "1.8 Plague",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s12_c1"
        ]
      },
      {
        "section": "labelling/42229-5/13",
        "title": "1.9 Chronic Bacterial Prostatitis",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s13_c1"
        ]
      },
      {
        "section": "labelling/42229-5/14",
        "title": "1.10 Lower Respiratory Tract Infections",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s14_c1"
        ]
      },
      {
        "section": "labelling/42229-5/15",
        "title": "1.11 Urinary Tract Infections",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s15_c1",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s15_c2"
        ]
      },
      {
        "section": "labelling/42229-5/16",
        "title": "1.12 Acute Sinusitis",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s16_c1"
        ]
      },
      {
        "section": "labelling/42229-5/17",
        "title": "1.13 Usage",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s17_c1"
        ]
      },
      {
        "section": "dosage/34068-7/18",
        "title": "2 DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s18_c1"
        ]
      },
      {
        "section": "dosage/42229-5/19",
        "title": "2.1 Dosage in Adults",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s19_c1",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s19_c2"
        ]
      },
      {
        "section": "dosage/42229-5/20",
        "title": "2.2 Dosage in Pediatric Patients",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s20_c1"
        ]
      },
      {
        "section": "dosage/42229-5/21",
        "title": "2.3 Dosage Modifications in Patients with Renal Impairment",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s21_c1",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s21_c2"
        ]
      },
      {
        "section": "dosage/42229-5/22",
        "title": "2.4 Important Administration Instructions",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "4.1 Hypersensitivity",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s26_c1"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "4.2 Tizanidine",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s27_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.1 Disabling and Potentially Irreversible Serious Adverse Reactions Including Tendinitis and Tendon Rupture, Peripheral Neuropathy, and Central Nervous System Effects",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.2 Tendinitis and Tendon Rupture",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s30_c1",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s30_c2"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.3 Peripheral Neuropathy",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.4 Central Nervous System Effects",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s32_c1",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s32_c2"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.5 Exacerbation of Myasthenia Gravis",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.6 Other Serious and Sometimes Fatal Adverse Reactions",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.7 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s35_c1"
        ]
      },
      {
        "section": "warnings/42229-5/36",
        "title": "5.8 Hepatotoxicity",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s36_c1"
        ]
      },
      {
        "section": "warnings/42229-5/37",
        "title": "5.9 Risk of Aortic Aneurysm and Dissection",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s37_c1"
        ]
      },
      {
        "section": "warnings/42229-5/38",
        "title": "5.10 Serious Adverse Reactions with Concomitant Theophylline",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s38_c1"
        ]
      },
      {
        "section": "warnings/42229-5/39",
        "title": "5.11 Clostridioides difficile-As sociated Diarrhea",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s39_c1"
        ]
      },
      {
        "section": "warnings/42229-5/40",
        "title": "5.12 Prolongation of the QT Interval",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s40_c1"
        ]
      },
      {
        "section": "warnings/42229-5/41",
        "title": "5.13 Musculoskeletal Disorders in Pediatric Patients and Arthropathic Effects inAnimals",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s41_c1"
        ]
      },
      {
        "section": "warnings/42229-5/42",
        "title": "5.14 Photosensitivity/Phototoxicity",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s42_c1"
        ]
      },
      {
        "section": "warnings/42229-5/43",
        "title": "5.15 Development of Drug Resistant Bacteria",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s43_c1"
        ]
      },
      {
        "section": "warnings/42229-5/44",
        "title": "5.16 Potential Risks with Concomitant Use of Drugs Metabolized by Cytochrome P450 1A2 Enzymes",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s44_c1"
        ]
      },
      {
        "section": "warnings/42229-5/45",
        "title": "5.17 Interference with Timely Diagnosis of Syphilis",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s45_c1"
        ]
      },
      {
        "section": "warnings/42229-5/46",
        "title": "5.18 Crystalluria",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s46_c1"
        ]
      },
      {
        "section": "warnings/42229-5/47",
        "title": "5.19 Blood Glucose Disturbances",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s47_c1"
        ]
      },
      {
        "section": "labelling/34089-3/61",
        "title": "1 1 DESCRIPTION",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s61_c1"
        ]
      },
      {
        "section": "warnings/34076-0/75",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c1",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c2",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c3",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c4",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c5",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c6",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c7",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c8",
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s75_c9"
        ]
      },
      {
        "section": "labelling/51945-4/77",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_5723eaf9-8659-4730-b792-4e4c33690ccb_v28_s77_c1"
        ]
      }
    ]
  },
  {
    "setid": "2f7d84d4-1085-4243-be88-442eecb85205",
    "version": 15,
    "product_name": "Metronidazole",
    "xml_sha256": "9739a75b0b81d82f9da191b4236a6cfde0f027ece9e0bf0ec91718e8bf033fda",
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2f7d84d4-1085-4243-be88-442eecb85205&version=15",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s3_c1"
        ]
      },
      {
        "section": "labelling/34089-3/4",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s4_c1"
        ]
      },
      {
        "section": "labelling/34067-9/15",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s15_c1",
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s15_c2",
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s15_c3",
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s15_c4"
        ]
      },
      {
        "section": "warnings/unknown/17",
        "title": "Hypersensitivity",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s17_c1"
        ]
      },
      {
        "section": "warnings/unknown/18",
        "title": "Psychotic Reaction with Disulfiram",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s18_c1"
        ]
      },
      {
        "section": "warnings/unknown/19",
        "title": "Interaction with Alcohol",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s19_c1"
        ]
      },
      {
        "section": "warnings/unknown/20",
        "title": "Cockayne Syndrome",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s20_c1"
        ]
      },
      {
        "section": "warnings/unknown/22",
        "title": "Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s22_c1"
        ]
      },
      {
        "section": "warnings/unknown/23",
        "title": "Severe Cutaneous Adverse Reactions",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s23_c1"
        ]
      },
      {
        "section": "warnings/unknown/24",
        "title": "Central and Peripheral Nervous System Effects",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s24_c1"
        ]
      },
      {
        "section": "warnings/34076-0/27",
        "title": "Information for Patients",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s27_c1",
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s27_c2"
        ]
      },
      {
        "section": "dosage/unknown/37",
        "title": "Trichomoniasis:",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s37_c1",
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s37_c2"
        ]
      },
      {
        "section": "dosage/unknown/38",
        "title": "Amebiasis",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s38_c1"
        ]
      },
      {
        "section": "dosage/unknown/39",
        "title": "Anaerobic Bacterial Infections",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s39_c1"
        ]
      },
      {
        "section": "dosage/unknown/40",
        "title": "Dosage Adjustments",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s40_c1"
        ]
      },
      {
        "section": "labelling/51945-4/42",
        "title": "PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_2f7d84d4-1085-4243-be88-442eecb85205_v15_s42_c1"
        ]
      }
    ]
  },
  {
    "setid": "126406ae-1fdc-df20-e063-6294a90a2718",
    "version": 4,
    "product_name": "Fluconazole",
    "xml_sha256": "6e4738a0f280cad0e6ea0d561f1c009be78f7caf22cc2f567bbe0c98e0691f6d",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=126406ae-1fdc-df20-e063-6294a90a2718&version=4",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/9",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s9_c1"
        ]
      },
      {
        "section": "warnings/34070-3/12",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s12_c1"
        ]
      },
      {
        "section": "warnings/34071-1/13",
        "title": "WARNINGS",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s13_c1",
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s13_c2"
        ]
      },
      {
        "section": "warnings/34072-9/15",
        "title": "General",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s15_c1",
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s15_c2"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s16_c1"
        ]
      },
      {
        "section": "dosage/42229-5/32",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s32_c1"
        ]
      },
      {
        "section": "dosage/42229-5/33",
        "title": "dosage",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s33_c1",
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s33_c2",
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s33_c3"
        ]
      },
      {
        "section": "dosage/42229-5/34",
        "title": "Dosage and Administration in Children:",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s34_c1",
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s34_c2"
        ]
      },
      {
        "section": "dosage/42229-5/35",
        "title": "Dosage In Patients With Impaired Renal Function:",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s35_c1",
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s35_c2"
        ]
      },
      {
        "section": "dosage/42229-5/36",
        "title": "Administration",
        "chunk_ids": [
          "dailymed_126406ae-1fdc-df20-e063-6294a90a2718_v4_s36_c1"
        ]
      }
    ]
  },
  {
    "setid": "5fa4920c-ec29-b879-e063-6294a90adcad",
    "version": 1,
    "product_name": "Sildenafil",
    "xml_sha256": "264e2f2ef8a69e77e7bea2b96d43309f89f6609d98641334fed4a3e801bfd011",
    "effective_date": "2026-11-06",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=5fa4920c-ec29-b879-e063-6294a90adcad&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS & USAGE",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s3_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Dosage Information",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Use with Food",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Dosage Adjustments in Specific Situations",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.4 Dosage Adjustments Due to Drug Interactions",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s8_c1"
        ]
      },
      {
        "section": "dosage/42229-5/9",
        "title": "2.5 Dosage Adjustments in Special Populations",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "4.1 Nitrates",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "4.2 Hypersensitivity Reactions",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "4.3 Concomitant Guanylate Cyclase (GC) Stimulators",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.1 Cardiovascular",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s16_c1",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s16_c2"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.2 Prolonged Erection and Priapism",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s17_c1"
        ]
      },
      {
        "section": "warnings/42229-5/18",
        "title": "5.3 Effects on the Eye",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s18_c1",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s18_c2"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.4 Hearing Loss",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.5 Hypotension when Co-administered with Alpha-blockers or Anti-hypertensives",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s20_c1",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s20_c2"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.6 Adverse Reactions with the Concomitant Use of Ritonavir",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s21_c1"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.7 Combination with other PDE5 Inhibitors or Other Erectile Dysfunction Therapies",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.8 Effects on Bleeding",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s23_c1"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "5.9 Counseling Patients About Sexually Transmitted Diseases",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s24_c1"
        ]
      },
      {
        "section": "labelling/34089-3/42",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s42_c1"
        ]
      },
      {
        "section": "warnings/34076-0/51",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c1",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c2",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c3",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c4",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c5",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c6",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c7",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c8",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c9",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c10",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c11",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c12",
          "dailymed_5fa4920c-ec29-b879-e063-6294a90adcad_v1_s51_c13"
        ]
      }
    ]
  },
  {
    "setid": "603c07bb-61bf-410f-8abf-01ef09d61c14",
    "version": 1,
    "product_name": "donepezil hydrochloride",
    "xml_sha256": "0baf5d2cca0c27de86f3ab0681900b95d563864898d30b49f70174abefb80300",
    "effective_date": "2026-09-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=603c07bb-61bf-410f-8abf-01ef09d61c14&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/2",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s2_c1"
        ]
      },
      {
        "section": "dosage/42229-5/4",
        "title": "2.1 Dosing in Mild to Moderate Alzheimer's Disease",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s4_c1"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.2 Dosing in Moderate to Severe Alzheimer\u2019s Disease",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.3 Administration Information",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s6_c1"
        ]
      },
      {
        "section": "warnings/34070-3/8",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s8_c1"
        ]
      },
      {
        "section": "warnings/42229-5/10",
        "title": "5.1 Anesthesia",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.2 Cardiovascular Conditions",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.3 Nausea and Vomiting",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.4 Peptic Ulcer Disease and GI Bleeding",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.6 Genitourinary Conditions",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.7 Neurological Conditions: Seizures",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.8 Pulmonary Conditions",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s16_c1"
        ]
      },
      {
        "section": "labelling/34089-3/37",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s37_c1"
        ]
      },
      {
        "section": "warnings/34076-0/70",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s70_c1"
        ]
      },
      {
        "section": "labelling/51945-4/72",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s72_c1"
        ]
      },
      {
        "section": "labelling/51945-4/73",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_603c07bb-61bf-410f-8abf-01ef09d61c14_v1_s73_c1"
        ]
      }
    ]
  },
  {
    "setid": "0f692652-4451-4eef-901d-1e6aadc43847",
    "version": 1,
    "product_name": "Olanzapine",
    "xml_sha256": "e0da33bd158e3d77794c201d0e4b21fa1519cefc77c30d45ae5ea641d744e6e2",
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=0f692652-4451-4eef-901d-1e6aadc43847&version=1",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/3",
        "title": "WARNING: INCREASED MORTALITY IN ELDERLY PATIENTS WITH DEMENTIA-RELATED PSYCHOSIS",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s3_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s3_c2"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.1 Schizophrenia",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s5_c1"
        ]
      },
      {
        "section": "labelling/42229-5/6",
        "title": "1.2 Bipolar I Disorder (Manic or Mixed Episodes)",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s6_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s6_c2"
        ]
      },
      {
        "section": "labelling/42229-5/7",
        "title": "1.3 Special Considerations in Treating Pediatric Schizophrenia and Bipolar I Disorder",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s7_c1"
        ]
      },
      {
        "section": "labelling/42229-5/8",
        "title": "1.5 Olanzapine and Fluoxetine in Combination: Depressive Episodes Associated with Bipolar I Disorder",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s8_c1"
        ]
      },
      {
        "section": "labelling/42229-5/9",
        "title": "1.6 Olanzapine and Fluoxetine in Combination: Treatment Resistant Depression",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s9_c1"
        ]
      },
      {
        "section": "dosage/42229-5/11",
        "title": "2.1 Schizophrenia",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s11_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s11_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s11_c3"
        ]
      },
      {
        "section": "dosage/42229-5/12",
        "title": "2.2 Bipolar I Disorder (Manic or Mixed Episodes)",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s12_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s12_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s12_c3"
        ]
      },
      {
        "section": "dosage/42229-5/13",
        "title": "2.5 Olanzapine and Fluoxetine in Combination: Depressive Episodes Associated with Bipolar I Disorder",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s13_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s13_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s13_c3"
        ]
      },
      {
        "section": "dosage/42229-5/14",
        "title": "2.6 Olanzapine and Fluoxetine in Combination: Treatment Resistant Depression",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s14_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s14_c2"
        ]
      },
      {
        "section": "dosage/42229-5/15",
        "title": "2.7 Olanzapine and Fluoxetine in Combination: Dosing in Special Populations",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s15_c1"
        ]
      },
      {
        "section": "warnings/34070-3/17",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s17_c1"
        ]
      },
      {
        "section": "warnings/43685-7/18",
        "title": "5 WARNINGS AND PRECAUTIONS",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s18_c1"
        ]
      },
      {
        "section": "warnings/42229-5/19",
        "title": "5.1 Elderly Patients with Dementia-Related Psychosis",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s19_c1"
        ]
      },
      {
        "section": "warnings/42229-5/20",
        "title": "5.2 Suicide",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s20_c1"
        ]
      },
      {
        "section": "warnings/42229-5/21",
        "title": "5.3 Neuroleptic Malignant Syndrome (NMS)",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s21_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s21_c2"
        ]
      },
      {
        "section": "warnings/42229-5/22",
        "title": "5.4 Drug Reaction with Eosinophilia and Systemic Symptoms (DRESS)",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s22_c1"
        ]
      },
      {
        "section": "warnings/42229-5/23",
        "title": "5.5 Metabolic Changes",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s23_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s23_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s23_c3",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s23_c4",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s23_c5"
        ]
      },
      {
        "section": "warnings/42229-5/24",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s24_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s24_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s24_c3",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s24_c4",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s24_c5",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s24_c6"
        ]
      },
      {
        "section": "warnings/42229-5/25",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s25_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s25_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s25_c3",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s25_c4",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s25_c5"
        ]
      },
      {
        "section": "warnings/42229-5/26",
        "title": "5.6 Tardive Dyskinesia",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s26_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s26_c2"
        ]
      },
      {
        "section": "warnings/42229-5/27",
        "title": "5.7 Orthostatic Hypotension",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s27_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s27_c2"
        ]
      },
      {
        "section": "warnings/42229-5/28",
        "title": "5.8 Falls",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s28_c1"
        ]
      },
      {
        "section": "warnings/42229-5/29",
        "title": "5.9 Leukopenia, Neutropenia, and Agranulocytosis",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s29_c1"
        ]
      },
      {
        "section": "warnings/42229-5/30",
        "title": "5.10 Dysphagia",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s30_c1"
        ]
      },
      {
        "section": "warnings/42229-5/31",
        "title": "5.11 Seizures",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s31_c1"
        ]
      },
      {
        "section": "warnings/42229-5/32",
        "title": "5.12 Potential for Cognitive and Motor Impairment",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s32_c1"
        ]
      },
      {
        "section": "warnings/42229-5/33",
        "title": "5.13 Body Temperature Regulation",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s33_c1"
        ]
      },
      {
        "section": "warnings/42229-5/34",
        "title": "5.14 Anticholinergic (antimuscarinic) Effects",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s34_c1"
        ]
      },
      {
        "section": "warnings/42229-5/35",
        "title": "5.15 Hyperprolactinemia",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s35_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s35_c2",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s35_c3"
        ]
      },
      {
        "section": "warnings/42229-5/36",
        "title": "5.16 Use in Combination with Fluoxetine, Lithium, or Valproate",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s36_c1"
        ]
      },
      {
        "section": "warnings/42229-5/37",
        "title": "5.17 Laboratory Tests",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s37_c1"
        ]
      },
      {
        "section": "labelling/34089-3/57",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s57_c1"
        ]
      },
      {
        "section": "warnings/34076-0/69",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s69_c1"
        ]
      },
      {
        "section": "warnings/42229-5/70",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s70_c1"
        ]
      },
      {
        "section": "warnings/42229-5/71",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s71_c1"
        ]
      },
      {
        "section": "warnings/42229-5/72",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s72_c1"
        ]
      },
      {
        "section": "warnings/42229-5/73",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s73_c1"
        ]
      },
      {
        "section": "warnings/42229-5/74",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s74_c1"
        ]
      },
      {
        "section": "warnings/42229-5/75",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s75_c1"
        ]
      },
      {
        "section": "warnings/42229-5/76",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s76_c1"
        ]
      },
      {
        "section": "warnings/42229-5/77",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s77_c1"
        ]
      },
      {
        "section": "warnings/42229-5/78",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s78_c1"
        ]
      },
      {
        "section": "warnings/42229-5/79",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s79_c1"
        ]
      },
      {
        "section": "warnings/42229-5/80",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s80_c1",
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s80_c2"
        ]
      },
      {
        "section": "warnings/42229-5/81",
        "title": "warnings",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s81_c1"
        ]
      },
      {
        "section": "labelling/51945-4/84",
        "title": "labelling",
        "chunk_ids": [
          "dailymed_0f692652-4451-4eef-901d-1e6aadc43847_v1_s84_c1"
        ]
      }
    ]
  },
  {
    "setid": "cf79ac74-017e-4fb4-85d3-4ea944080e89",
    "version": 15,
    "product_name": "MECLIZINE",
    "xml_sha256": "aa098888de930f745137a7e51a0754c90e2fbb3e7558fe3651f725d0010d1c74",
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=cf79ac74-017e-4fb4-85d3-4ea944080e89&version=15",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34067-9/4",
        "title": "Uses",
        "chunk_ids": [
          "dailymed_cf79ac74-017e-4fb4-85d3-4ea944080e89_v15_s4_c1"
        ]
      },
      {
        "section": "warnings/34071-1/5",
        "title": "Warnings",
        "chunk_ids": [
          "dailymed_cf79ac74-017e-4fb4-85d3-4ea944080e89_v15_s5_c1"
        ]
      },
      {
        "section": "warnings/50567-7/6",
        "title": "When using this product",
        "chunk_ids": [
          "dailymed_cf79ac74-017e-4fb4-85d3-4ea944080e89_v15_s6_c1"
        ]
      },
      {
        "section": "warnings/53414-9/7",
        "title": "If pregnant or breast-feeding,",
        "chunk_ids": [
          "dailymed_cf79ac74-017e-4fb4-85d3-4ea944080e89_v15_s7_c1"
        ]
      },
      {
        "section": "warnings/50565-1/8",
        "title": "Keep out of reach of children.",
        "chunk_ids": [
          "dailymed_cf79ac74-017e-4fb4-85d3-4ea944080e89_v15_s8_c1"
        ]
      },
      {
        "section": "dosage/34068-7/9",
        "title": "Directions",
        "chunk_ids": [
          "dailymed_cf79ac74-017e-4fb4-85d3-4ea944080e89_v15_s9_c1"
        ]
      }
    ]
  },
  {
    "setid": "1a7b373a-9b74-4b9d-93fb-081614222e30",
    "version": 19,
    "product_name": "Benazepril Hydrochloride",
    "xml_sha256": "a35cae28a6c6af3959c65c232a2074edcd7667a088b6bce6f4538c999c15d4ab",
    "effective_date": "2026-11-11",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1a7b373a-9b74-4b9d-93fb-081614222e30&version=19",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s2_c1"
        ]
      },
      {
        "section": "labelling/34067-9/3",
        "title": "1 INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s3_c1",
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s3_c2"
        ]
      },
      {
        "section": "dosage/42229-5/5",
        "title": "2.1 Recommended Dosage",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s5_c1",
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s5_c2"
        ]
      },
      {
        "section": "dosage/42229-5/6",
        "title": "2.2 Dose Adjustment for Renal Impairment",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s6_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.3 Preparation of Suspension (for 150 mL of a 2 mg/mL Suspension)",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s7_c1"
        ]
      },
      {
        "section": "warnings/34070-3/9",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s9_c1"
        ]
      },
      {
        "section": "warnings/42229-5/11",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s11_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.2 Angioedema and Anaphylactoid Reactions",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s12_c1",
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s12_c2"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.3 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s13_c1"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.4 Hypotension",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.5 Hyperkalemia",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.6 Hepatic Failure",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s16_c1"
        ]
      },
      {
        "section": "labelling/34089-3/35",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s35_c1"
        ]
      },
      {
        "section": "warnings/34076-0/44",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s44_c1",
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s44_c2"
        ]
      },
      {
        "section": "labelling/51945-4/45",
        "title": "PACKAGE/LABEL PRINCIPAL DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_1a7b373a-9b74-4b9d-93fb-081614222e30_v19_s45_c1"
        ]
      }
    ]
  },
  {
    "setid": "8cd22728-34b4-4e55-8339-580138fe46d8",
    "version": 5,
    "product_name": "Acyclovir",
    "xml_sha256": "7542c6fa1cf5acb6fff60c9a3446c749b1b358f5572b7551b66636ddccbc6b1a",
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8cd22728-34b4-4e55-8339-580138fe46d8&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "labelling/34089-3/2",
        "title": "DESCRIPTION",
        "chunk_ids": [
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s2_c1",
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s2_c2",
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s2_c3",
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s2_c4"
        ]
      },
      {
        "section": "labelling/34067-9/4",
        "title": "INDICATIONS AND USAGE",
        "chunk_ids": [
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s4_c1"
        ]
      },
      {
        "section": "warnings/34070-3/5",
        "title": "CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s5_c1"
        ]
      },
      {
        "section": "warnings/34071-1/6",
        "title": "WARNING",
        "chunk_ids": [
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s6_c1"
        ]
      },
      {
        "section": "dosage/34068-7/10",
        "title": "DOSAGE AND ADMINISTRATION",
        "chunk_ids": [
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s10_c1",
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s10_c2",
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s10_c3"
        ]
      },
      {
        "section": "labelling/51945-4/12",
        "title": "PAKAGE LABEL PRINCIPLE DISPLAY PANEL",
        "chunk_ids": [
          "dailymed_8cd22728-34b4-4e55-8339-580138fe46d8_v5_s12_c1"
        ]
      }
    ]
  },
  {
    "setid": "9391b8d8-2217-4838-8976-1a5ad90ef4ca",
    "version": 5,
    "product_name": "Enalapril maleate oral solution",
    "xml_sha256": "0329d42042cc58102a3de20597db03eac408e8b3e31139b0fc27135d56568377",
    "effective_date": "2026-11-02",
    "fetched": "2026-11-21",
    "url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9391b8d8-2217-4838-8976-1a5ad90ef4ca&version=5",
    "module": "medicine",
    "sections": [
      {
        "section": "warnings/34066-1/2",
        "title": "WARNING: FETAL TOXICITY",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s2_c1"
        ]
      },
      {
        "section": "labelling/42229-5/4",
        "title": "1.2 Heart Failure",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s4_c1"
        ]
      },
      {
        "section": "labelling/42229-5/5",
        "title": "1.3 Asymptomatic Left Ventricular Dysfunction",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s5_c1"
        ]
      },
      {
        "section": "dosage/42229-5/7",
        "title": "2.2 Heart Failure",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s7_c1"
        ]
      },
      {
        "section": "dosage/42229-5/8",
        "title": "2.3 Asymptomatic Left Ventricular Dysfunction",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s8_c1"
        ]
      },
      {
        "section": "warnings/34070-3/10",
        "title": "4 CONTRAINDICATIONS",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s10_c1"
        ]
      },
      {
        "section": "warnings/42229-5/12",
        "title": "5.1 Fetal Toxicity",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s12_c1"
        ]
      },
      {
        "section": "warnings/42229-5/13",
        "title": "5.2 Angioedema and Anaphylactoid Reactions",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s13_c1",
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s13_c2"
        ]
      },
      {
        "section": "warnings/42229-5/14",
        "title": "5.3 Hypotension",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s14_c1"
        ]
      },
      {
        "section": "warnings/42229-5/15",
        "title": "5.4 Hepatic Failure",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s15_c1"
        ]
      },
      {
        "section": "warnings/42229-5/16",
        "title": "5.5 Impaired Renal Function",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s16_c1"
        ]
      },
      {
        "section": "warnings/42229-5/17",
        "title": "5.6 Hyperkalemia",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s17_c1"
        ]
      },
      {
        "section": "labelling/34089-3/37",
        "title": "11 DESCRIPTION",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s37_c1"
        ]
      },
      {
        "section": "warnings/34076-0/48",
        "title": "17 PATIENT COUNSELING INFORMATION",
        "chunk_ids": [
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s48_c1",
          "dailymed_9391b8d8-2217-4838-8976-1a5ad90ef4ca_v5_s48_c2"
        ]
      }
    ]
  }
]
```
