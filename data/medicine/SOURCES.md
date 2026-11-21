# Medicine corpus sources

Source: National Library of Medicine, DailyMed. Medicine only, excluded from device evaluation.
Rebuild: `python -m scripts.real.build_medicine_corpus`. Use `--offline` with cached sources.
Corpus text and product metadata are versioned. Original XML stays local.
The catalog now pins 30 products and 618 chunks. Rebuild metadata with
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
  },
  {
    "product_name": "Aspirin",
    "setid": "c3099892-a8cd-4574-a6f9-041e59e2feae",
    "version": 11,
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "xml_sha256": "328a406aba96a3fe2298c173c93283b9ec75dcaf04a860f2b331bc434e9819b7"
  },
  {
    "product_name": "Berkley and Jensen Allergy Relief",
    "setid": "caa22bcb-6617-4724-8dcb-e63bfeef41a9",
    "version": 6,
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "xml_sha256": "32ee7a60f484dabcee83c8dc3671ec41a25b21f94bcc7af40c6a968b0a784158"
  },
  {
    "product_name": "Losartan Potassium",
    "setid": "6286ea54-2350-49fc-8f37-4b979bd7f986",
    "version": 9,
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "xml_sha256": "27257387e110c7c6814991cc7a99ab779447072896d274fd753abe5027cee8ab"
  },
  {
    "product_name": "Lisinopril",
    "setid": "b17cd16b-8d0a-4cfa-bd48-2529983fcd12",
    "version": 7,
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "xml_sha256": "382ff54d38bc4a74aa72a157cfd5838ee01b335a3381f21a9a646b95a3a3902b"
  },
  {
    "product_name": "Sertraline Hydrochloride",
    "setid": "687ebdc4-6946-454e-8d46-3207488ccf32",
    "version": 13,
    "effective_date": "2026-11-05",
    "fetched": "2026-11-21",
    "xml_sha256": "4feb28bb1ad4959a064d6025cd381989baaac693cf784e49e70e237ee068424c"
  },
  {
    "product_name": "PredniSONE",
    "setid": "318fdf0d-c03a-4b48-a380-b7bb630363fb",
    "version": 7,
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "xml_sha256": "28921aeb11bde4a33e48dd74f9505ce7467230c05dd8b7e61ac286da7df224e5"
  },
  {
    "product_name": "Gabapentin",
    "setid": "3f1535d9-6c3b-4355-a2ef-eb6ee33054a5",
    "version": 1,
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "xml_sha256": "8fb466058aac6299190fb9081ae6fcc5b349aba32a294a2db446200605bc0fa9"
  },
  {
    "product_name": "Escitalopram",
    "setid": "de803217-6d32-4ef8-afe7-02462f37bf0c",
    "version": 3,
    "effective_date": "2026-11-12",
    "fetched": "2026-11-21",
    "xml_sha256": "70b7dbaf471e9d43870736781c6b595db503902b417c4fc90db7fe5a3e592c95"
  },
  {
    "product_name": "Amlodipine Besylate",
    "setid": "d889c656-f024-4e18-b83c-68a7707945d8",
    "version": 1,
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "xml_sha256": "75fc6cad90a1290f8c22436a93c0b23c9ad9cd22db35f560758020efea924e1d"
  },
  {
    "product_name": "Doxycycline Hyclate",
    "setid": "a569ba80-ffea-40b2-9fbe-a42810b1fccb",
    "version": 34,
    "effective_date": "2025-06-26",
    "fetched": "2026-11-21",
    "xml_sha256": "11426d1bb985b72dedcbab87f7c74e1f5b47ded459f223acf640ca2135d6f184"
  },
  {
    "product_name": "FUROSEMIDE",
    "setid": "15e4c3a3-7d64-471e-bfdf-6156731e24aa",
    "version": 7,
    "effective_date": "2026-11-16",
    "fetched": "2026-11-21",
    "xml_sha256": "5f1094cdfad9d14741ff8386a16e7660f2c088848d8ee513622ed1c96ac4a016"
  },
  {
    "product_name": "Naproxen",
    "setid": "307aa67f-53b9-4c60-a328-091bbf6338d4",
    "version": 9,
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "xml_sha256": "f0ab799964b7346f9f3a3a6241958fdfb03dd0e5e3e0e4a2ce89daee5c473333"
  },
  {
    "product_name": "Fluoxetine",
    "setid": "b4831735-6731-473a-b4f0-1f4a67aa7120",
    "version": 8,
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "xml_sha256": "2f0411631fc25b69f995b1c499c17f671a9860d5fcf176255840addd2a4d1a07"
  },
  {
    "product_name": "Cephalexin",
    "setid": "a6b5edf2-1ef8-46b7-977a-8c303900f3f0",
    "version": 17,
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "xml_sha256": "0a71b5fe534fee57f24b34a90927a8daaf79cbf1d78fc71eadb58515808c742a"
  },
  {
    "product_name": "Clopidogrel",
    "setid": "4cd07a3c-9673-4aa0-b76a-d79df2399ee1",
    "version": 11,
    "effective_date": "2026-11-11",
    "fetched": "2026-11-21",
    "xml_sha256": "89f0772ee7d379ee19653fc1454814047691880e55ea15eade68bd5fe55ff7a8"
  },
  {
    "product_name": "Protonix I.V.",
    "setid": "3cde88e6-28f2-4cbe-8c3f-770b05cc0e1b",
    "version": 15,
    "effective_date": "2026-11-06",
    "fetched": "2026-11-21",
    "xml_sha256": "3971881d35861a5c2d1b2e83df9b89e8c45137cc4cfdc5dff51828116e8f9a78"
  },
  {
    "product_name": "valsartan and hydrochlorothiazide",
    "setid": "176b400b-2b4e-481d-b6c4-0f99e4c711c3",
    "version": 3,
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "xml_sha256": "6521c7736cfb90f02a3ab2c67b324720b11efb168bd1e4242013429676cf1003"
  },
  {
    "product_name": "Allopurinol",
    "setid": "682dd8b8-fc6e-47c5-95b7-82d7ad96b750",
    "version": 14,
    "effective_date": "2026-11-05",
    "fetched": "2026-11-21",
    "xml_sha256": "c6c9c576d1c4e7695bfd3da18cdbfb1b828b8c94720ea3d230dd0233955e137e"
  },
  {
    "product_name": "Montelukast Sodium",
    "setid": "c9ec1996-6a54-4622-b8a6-57dea49f6b35",
    "version": 23,
    "effective_date": "2026-11-10",
    "fetched": "2026-11-21",
    "xml_sha256": "a7d9755c49e1db68096737515caae41814568a2432606a19364a4138d543ae18"
  },
  {
    "product_name": "Rosuvastatin Calcium",
    "setid": "02797697-300a-43db-92cf-9b78f08626be",
    "version": 7,
    "effective_date": "2026-11-17",
    "fetched": "2026-11-21",
    "xml_sha256": "277e1d0861b0115d3cccb0d6e47c8cb12ed1ee5d5fc330a40ed0cde084b643cc"
  }
]
```
