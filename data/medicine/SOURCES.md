# Medicine corpus sources

Source: National Library of Medicine, DailyMed. Medicine only, excluded from device evaluation.
Rebuild: `python -m scripts.real.build_medicine_corpus`. Use `--offline` with cached sources.
Corpus and original XML stay local. This pinned catalog is versioned.
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
    "xml_sha256": "f0e07ec4c884a666e65725b330fca839797c237446f44ee36847eb334cf35a9a"
  },
  {
    "product_name": "Childrens Ibuprofen",
    "setid": "0faa3b41-a241-4aae-9cc8-e075728ff916",
    "version": 4,
    "effective_date": "2026-10-29",
    "fetched": "2026-11-16",
    "xml_sha256": "f7c0e0ac3f102efa38418223f88cfab753201c89d9cbe608bccd2f7316c3b874"
  },
  {
    "product_name": "Loratadine",
    "setid": "3881afaf-8d0d-4154-85a8-79a3c7806b49",
    "version": 6,
    "effective_date": "2026-10-27",
    "fetched": "2026-11-16",
    "xml_sha256": "d715476e8cc48da36ad33b9cfb4a7e6df7aabee88775f45f55b58cbced643b56"
  },
  {
    "product_name": "Omeprazole",
    "setid": "346141b5-b49d-489a-84eb-18df8b940460",
    "version": 3,
    "effective_date": "2026-10-26",
    "fetched": "2026-11-16",
    "xml_sha256": "516ea2d452c8e9f63691dbc578e4c8ecdd7d74c1f59df378e93d8879ad876ba3"
  },
  {
    "product_name": "FAMOTIDINE",
    "setid": "446ca466-a43c-0401-e063-6394a90ac0d1",
    "version": 1,
    "effective_date": "2025-11-25",
    "fetched": "2026-11-16",
    "xml_sha256": "43703e68e50c05fa0c2a4cd33012ef72db67dd85b684209036732b75127e161b"
  },
  {
    "product_name": "Amoxicillin",
    "setid": "2c395111-c9c1-483e-a542-58b935ede689",
    "version": 2,
    "effective_date": "2026-09-01",
    "fetched": "2026-11-16",
    "xml_sha256": "b28f89e64fe7b5b7a275d84c69bda94154939dca0f62667554404868007d7410"
  },
  {
    "product_name": "METFORMIN HYDROCHLORIDE",
    "setid": "d8bd1779-d1c4-4dde-816d-ea72b37bb5cd",
    "version": 3,
    "effective_date": "2026-09-02",
    "fetched": "2026-11-16",
    "xml_sha256": "fcdd2f811c825f99de3455ecbba04f13db0fe3b4e879a99406ada55dd5ec50ef"
  },
  {
    "product_name": "Atorvastatin Calcium",
    "setid": "a519e355-84f0-40d1-b586-e6e8eadb5b0f",
    "version": 3,
    "effective_date": "2026-09-17",
    "fetched": "2026-11-16",
    "xml_sha256": "92d8443a03132cf30fa3b24032db8b5cdf1d6b33a40f6b13e5889c51141739d6"
  },
  {
    "product_name": "Levothyroxine Sodium",
    "setid": "1a2124e6-aea2-40dd-bb8d-52c58405a67e",
    "version": 1,
    "effective_date": "2026-10-01",
    "fetched": "2026-11-16",
    "xml_sha256": "ad00fde790816333b37c2d046aa645d16c1033160078b76ed40d1c5f4d0025c8"
  },
  {
    "product_name": "ALBUTEROL SULFATE",
    "setid": "1810ff8e-d505-bf9c-e063-6394a90a6540",
    "version": 4,
    "effective_date": "2026-09-22",
    "fetched": "2026-11-16",
    "xml_sha256": "7982bd7ec1de5be710d5aaae536840a6396f1eeddd485735212ef5b786e4ecb1"
  }
]
```
