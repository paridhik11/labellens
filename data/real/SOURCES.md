# Real-label sources and module separation

The legacy section records 60 medicine-artwork downloads. Every legacy entry is tagged `medicine` and excluded from device evaluation. These are not the new device/symbol benchmark. Symbol crops and tags are not provided for the legacy medicine catalog.

Images, XML, manifests, CSV files and derived crops stay local. Only this sources list is versioned under `data/real/`. Original file checksums and download URLs are retained in the local manifest. The existing fetch/rebuild script is `scripts/build_real_set.py`; its medicine collection must not be used as the device evaluation.

Rights: no blanket open license has been established for company-contributed artwork. Source notices remain in the originals. NLM attribution: Source: National Library of Medicine. Policy: https://www.nlm.nih.gov/web_policies.html#copyright

## Per-file sources

| Local image | Local XML | Module | Device evaluation | Source ZIP (exact version) | Rights/license |
|---|---|---|---|---|---|
| `images/9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3.jpg` | `source/9fdbaf5e-f88b-4d18-97df-0b2e8dddf377_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=9fdbaf5e-f88b-4d18-97df-0b2e8dddf377&version=3) | not established; company artwork |
| `images/f7962107-f79a-4a04-af8d-f7b989e51f2c_v5.jpg` | `source/f7962107-f79a-4a04-af8d-f7b989e51f2c_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=f7962107-f79a-4a04-af8d-f7b989e51f2c&version=5) | not established; company artwork |
| `images/b5e15dd1-6e99-411c-9183-8a4265eae404_v3.jpg` | `source/b5e15dd1-6e99-411c-9183-8a4265eae404_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=b5e15dd1-6e99-411c-9183-8a4265eae404&version=3) | not established; company artwork |
| `images/ac6bd863-c807-4863-9919-8f14a7571155_v1.jpg` | `source/ac6bd863-c807-4863-9919-8f14a7571155_v1.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=ac6bd863-c807-4863-9919-8f14a7571155&version=1) | not established; company artwork |
| `images/4f0d8da5-a75b-acc7-e063-6394a90ae839_v2.jpg` | `source/4f0d8da5-a75b-acc7-e063-6394a90ae839_v2.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=4f0d8da5-a75b-acc7-e063-6394a90ae839&version=2) | not established; company artwork |
| `images/61a9829b-4792-4caa-b75a-b84812f28d4a_v1.jpg` | `source/61a9829b-4792-4caa-b75a-b84812f28d4a_v1.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=61a9829b-4792-4caa-b75a-b84812f28d4a&version=1) | not established; company artwork |
| `images/409b5fcd-5880-4dda-85d8-26aeceb4f8ab_v6.jpg` | `source/409b5fcd-5880-4dda-85d8-26aeceb4f8ab_v6.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=409b5fcd-5880-4dda-85d8-26aeceb4f8ab&version=6) | not established; company artwork |
| `images/5c064fc8-0426-4608-90ee-93609a7e5547_v10.jpg` | `source/5c064fc8-0426-4608-90ee-93609a7e5547_v10.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=5c064fc8-0426-4608-90ee-93609a7e5547&version=10) | not established; company artwork |
| `images/944b3f78-3efa-484b-84f0-00ffe95c5dfb_v9.jpg` | `source/944b3f78-3efa-484b-84f0-00ffe95c5dfb_v9.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=944b3f78-3efa-484b-84f0-00ffe95c5dfb&version=9) | not established; company artwork |
| `images/9e8d684f-3ad5-43cd-b6ce-fb196747cc8e_v1.jpg` | `source/9e8d684f-3ad5-43cd-b6ce-fb196747cc8e_v1.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=9e8d684f-3ad5-43cd-b6ce-fb196747cc8e&version=1) | not established; company artwork |
| `images/eafa5b05-d692-48e7-a413-30f847547eb2_v8.jpg` | `source/eafa5b05-d692-48e7-a413-30f847547eb2_v8.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=eafa5b05-d692-48e7-a413-30f847547eb2&version=8) | not established; company artwork |
| `images/a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3.jpg` | `source/a519e355-84f0-40d1-b586-e6e8eadb5b0f_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=a519e355-84f0-40d1-b586-e6e8eadb5b0f&version=3) | not established; company artwork |
| `images/09990b2f-202e-b4df-e063-6394a90a055b_v4.jpg` | `source/09990b2f-202e-b4df-e063-6394a90a055b_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=09990b2f-202e-b4df-e063-6394a90a055b&version=4) | not established; company artwork |
| `images/e231c2f6-927c-1ab0-e053-2995a90a6121_v4.jpg` | `source/e231c2f6-927c-1ab0-e053-2995a90a6121_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=e231c2f6-927c-1ab0-e053-2995a90a6121&version=4) | not established; company artwork |
| `images/c9d1e26f-c95a-4991-95fa-9ed6ed484fe2_v5.jpg` | `source/c9d1e26f-c95a-4991-95fa-9ed6ed484fe2_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=c9d1e26f-c95a-4991-95fa-9ed6ed484fe2&version=5) | not established; company artwork |
| `images/77ed80a2-a482-4838-ac55-4865b5c31d9f_v17.jpg` | `source/77ed80a2-a482-4838-ac55-4865b5c31d9f_v17.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=77ed80a2-a482-4838-ac55-4865b5c31d9f&version=17) | not established; company artwork |
| `images/446ca466-a43c-0401-e063-6394a90ac0d1_v1.jpg` | `source/446ca466-a43c-0401-e063-6394a90ac0d1_v1.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=446ca466-a43c-0401-e063-6394a90ac0d1&version=1) | not established; company artwork |
| `images/5f8ca6ad-cb25-1abf-e053-2a91aa0aca99_v16.jpg` | `source/5f8ca6ad-cb25-1abf-e053-2a91aa0aca99_v16.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=5f8ca6ad-cb25-1abf-e053-2a91aa0aca99&version=16) | not established; company artwork |
| `images/25e4ee12-f43a-4c87-9e34-64e91d06a368_v2.jpg` | `source/25e4ee12-f43a-4c87-9e34-64e91d06a368_v2.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=25e4ee12-f43a-4c87-9e34-64e91d06a368&version=2) | not established; company artwork |
| `images/32dbec5e-044a-40b6-9b88-e1396c4b4b6e_v3.jpg` | `source/32dbec5e-044a-40b6-9b88-e1396c4b4b6e_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=32dbec5e-044a-40b6-9b88-e1396c4b4b6e&version=3) | not established; company artwork |
| `images/1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1.jpg` | `source/1a2124e6-aea2-40dd-bb8d-52c58405a67e_v1.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1a2124e6-aea2-40dd-bb8d-52c58405a67e&version=1) | not established; company artwork |
| `images/5b161f25-c578-4ff4-a931-ff3a1e681c50_v10.jpg` | `source/5b161f25-c578-4ff4-a931-ff3a1e681c50_v10.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=5b161f25-c578-4ff4-a931-ff3a1e681c50&version=10) | not established; company artwork |
| `images/9324e2eb-26fd-4f14-9f10-e5aa467306f4_v12.jpg` | `source/9324e2eb-26fd-4f14-9f10-e5aa467306f4_v12.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=9324e2eb-26fd-4f14-9f10-e5aa467306f4&version=12) | not established; company artwork |
| `images/45a0c910-7dd7-6a42-e063-6394a90a491c_v3.jpg` | `source/45a0c910-7dd7-6a42-e063-6394a90a491c_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=45a0c910-7dd7-6a42-e063-6394a90a491c&version=3) | not established; company artwork |
| `images/35a79458-79f6-44d6-b74c-b4f4aaf0dde0_v18.jpg` | `source/35a79458-79f6-44d6-b74c-b4f4aaf0dde0_v18.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=35a79458-79f6-44d6-b74c-b4f4aaf0dde0&version=18) | not established; company artwork |
| `images/c7381600-2e4c-4e7b-aa67-fe7d5fae7b40_v2.jpg` | `source/c7381600-2e4c-4e7b-aa67-fe7d5fae7b40_v2.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=c7381600-2e4c-4e7b-aa67-fe7d5fae7b40&version=2) | not established; company artwork |
| `images/4aec7f59-b429-4b0e-a779-8df1dd8f80d7_v5.jpg` | `source/4aec7f59-b429-4b0e-a779-8df1dd8f80d7_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=4aec7f59-b429-4b0e-a779-8df1dd8f80d7&version=5) | not established; company artwork |
| `images/50f3157b-5788-4b63-835a-e60c8dc33df9_v6.jpg` | `source/50f3157b-5788-4b63-835a-e60c8dc33df9_v6.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=50f3157b-5788-4b63-835a-e60c8dc33df9&version=6) | not established; company artwork |
| `images/34440532-03e1-4feb-b3e2-dab869edeb15_v3.jpg` | `source/34440532-03e1-4feb-b3e2-dab869edeb15_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=34440532-03e1-4feb-b3e2-dab869edeb15&version=3) | not established; company artwork |
| `images/6fe34d05-84a4-4254-aea6-77b52122ea18_v8.jpg` | `source/6fe34d05-84a4-4254-aea6-77b52122ea18_v8.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6fe34d05-84a4-4254-aea6-77b52122ea18&version=8) | not established; company artwork |
| `images/38543976-ccbe-4af9-b01d-ae102452d418_v6.jpg` | `source/38543976-ccbe-4af9-b01d-ae102452d418_v6.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=38543976-ccbe-4af9-b01d-ae102452d418&version=6) | not established; company artwork |
| `images/9fb3a3a8-8812-4238-b596-291b79085db9_v4.jpg` | `source/9fb3a3a8-8812-4238-b596-291b79085db9_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=9fb3a3a8-8812-4238-b596-291b79085db9&version=4) | not established; company artwork |
| `images/4af90b5d-f47a-4436-8e24-4cb7e5b758b3_v1.jpg` | `source/4af90b5d-f47a-4436-8e24-4cb7e5b758b3_v1.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=4af90b5d-f47a-4436-8e24-4cb7e5b758b3&version=1) | not established; company artwork |
| `images/0e1ec762-6de3-47b1-9717-55f8f3e3ca7f_v5.jpg` | `source/0e1ec762-6de3-47b1-9717-55f8f3e3ca7f_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=0e1ec762-6de3-47b1-9717-55f8f3e3ca7f&version=5) | not established; company artwork |
| `images/2c395111-c9c1-483e-a542-58b935ede689_v2.jpg` | `source/2c395111-c9c1-483e-a542-58b935ede689_v2.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=2c395111-c9c1-483e-a542-58b935ede689&version=2) | not established; company artwork |
| `images/6d5cecc9-5095-477b-bfc7-45b6e7e689f0_v3.jpg` | `source/6d5cecc9-5095-477b-bfc7-45b6e7e689f0_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6d5cecc9-5095-477b-bfc7-45b6e7e689f0&version=3) | not established; company artwork |
| `images/96a76906-58ad-40cd-be27-4ea254e298c5_v7.jpg` | `source/96a76906-58ad-40cd-be27-4ea254e298c5_v7.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=96a76906-58ad-40cd-be27-4ea254e298c5&version=7) | not established; company artwork |
| `images/e57531a7-2047-4531-acac-30bc8e3924fc_v3.jpg` | `source/e57531a7-2047-4531-acac-30bc8e3924fc_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=e57531a7-2047-4531-acac-30bc8e3924fc&version=3) | not established; company artwork |
| `images/58612053-9bb2-47fb-95f6-7945298380a6_v5.jpg` | `source/58612053-9bb2-47fb-95f6-7945298380a6_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=58612053-9bb2-47fb-95f6-7945298380a6&version=5) | not established; company artwork |
| `images/1b457b1d-0e80-4578-ba6f-dedf513fc962_v16.jpg` | `source/1b457b1d-0e80-4578-ba6f-dedf513fc962_v16.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1b457b1d-0e80-4578-ba6f-dedf513fc962&version=16) | not established; company artwork |
| `images/d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3.jpg` | `source/d8bd1779-d1c4-4dde-816d-ea72b37bb5cd_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=d8bd1779-d1c4-4dde-816d-ea72b37bb5cd&version=3) | not established; company artwork |
| `images/b34cd3ff-d0af-4852-b4ef-2a8b4a93aeae_v55.jpg` | `source/b34cd3ff-d0af-4852-b4ef-2a8b4a93aeae_v55.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=b34cd3ff-d0af-4852-b4ef-2a8b4a93aeae&version=55) | not established; company artwork |
| `images/67a190c3-7de0-4f57-be94-d6b8285e1220_v13.jpg` | `source/67a190c3-7de0-4f57-be94-d6b8285e1220_v13.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=67a190c3-7de0-4f57-be94-d6b8285e1220&version=13) | not established; company artwork |
| `images/287ceb12-e4d8-43c7-8cec-c4d23aa8fb12_v6.jpg` | `source/287ceb12-e4d8-43c7-8cec-c4d23aa8fb12_v6.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=287ceb12-e4d8-43c7-8cec-c4d23aa8fb12&version=6) | not established; company artwork |
| `images/570f8acc-ed6d-e789-e063-6294a90ab128_v2.jpg` | `source/570f8acc-ed6d-e789-e063-6294a90ab128_v2.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=570f8acc-ed6d-e789-e063-6294a90ab128&version=2) | not established; company artwork |
| `images/58eaab62-ac36-4080-8ded-9b472dddc617_v5.jpg` | `source/58eaab62-ac36-4080-8ded-9b472dddc617_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=58eaab62-ac36-4080-8ded-9b472dddc617&version=5) | not established; company artwork |
| `images/f8d50b4e-735d-4d91-a18d-be3537e46e99_v7.jpg` | `source/f8d50b4e-735d-4d91-a18d-be3537e46e99_v7.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=f8d50b4e-735d-4d91-a18d-be3537e46e99&version=7) | not established; company artwork |
| `images/43745d42-f859-4168-a2dd-2c8ae47ae590_v6.jpg` | `source/43745d42-f859-4168-a2dd-2c8ae47ae590_v6.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=43745d42-f859-4168-a2dd-2c8ae47ae590&version=6) | not established; company artwork |
| `images/5329614f-ae0b-4854-bb6f-ea0b7dae87c0_v4.jpg` | `source/5329614f-ae0b-4854-bb6f-ea0b7dae87c0_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=5329614f-ae0b-4854-bb6f-ea0b7dae87c0&version=4) | not established; company artwork |
| `images/10ee5bc0-509d-b549-e063-6394a90a5dca_v4.jpg` | `source/10ee5bc0-509d-b549-e063-6394a90a5dca_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=10ee5bc0-509d-b549-e063-6394a90a5dca&version=4) | not established; company artwork |
| `images/b2091281-a64a-190a-e053-2995a90a890a_v5.jpg` | `source/b2091281-a64a-190a-e053-2995a90a890a_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=b2091281-a64a-190a-e053-2995a90a890a&version=5) | not established; company artwork |
| `images/0faa3b41-a241-4aae-9cc8-e075728ff916_v4.jpg` | `source/0faa3b41-a241-4aae-9cc8-e075728ff916_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=0faa3b41-a241-4aae-9cc8-e075728ff916&version=4) | not established; company artwork |
| `images/f5bb0854-a477-4e59-914b-eeeaef92a596_v17.jpg` | `source/f5bb0854-a477-4e59-914b-eeeaef92a596_v17.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=f5bb0854-a477-4e59-914b-eeeaef92a596&version=17) | not established; company artwork |
| `images/1810ff8e-d505-bf9c-e063-6394a90a6540_v4.jpg` | `source/1810ff8e-d505-bf9c-e063-6394a90a6540_v4.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1810ff8e-d505-bf9c-e063-6394a90a6540&version=4) | not established; company artwork |
| `images/5328761e-59d3-ca7a-e063-6394a90ae810_v7.jpg` | `source/5328761e-59d3-ca7a-e063-6394a90ae810_v7.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=5328761e-59d3-ca7a-e063-6394a90ae810&version=7) | not established; company artwork |
| `images/3881afaf-8d0d-4154-85a8-79a3c7806b49_v6.jpg` | `source/3881afaf-8d0d-4154-85a8-79a3c7806b49_v6.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=3881afaf-8d0d-4154-85a8-79a3c7806b49&version=6) | not established; company artwork |
| `images/35a95bec-51b9-465b-aa93-ad26afb87be8_v9.jpg` | `source/35a95bec-51b9-465b-aa93-ad26afb87be8_v9.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=35a95bec-51b9-465b-aa93-ad26afb87be8&version=9) | not established; company artwork |
| `images/5ea3217d-845d-4781-b849-6b00babdc214_v5.jpg` | `source/5ea3217d-845d-4781-b849-6b00babdc214_v5.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=5ea3217d-845d-4781-b849-6b00babdc214&version=5) | not established; company artwork |
| `images/faae4d8e-1d33-4236-b380-7b2884c08812_v3.jpg` | `source/faae4d8e-1d33-4236-b380-7b2884c08812_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=faae4d8e-1d33-4236-b380-7b2884c08812&version=3) | not established; company artwork |
| `images/346141b5-b49d-489a-84eb-18df8b940460_v3.jpg` | `source/346141b5-b49d-489a-84eb-18df8b940460_v3.xml` | medicine | excluded | [source](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=346141b5-b49d-489a-84eb-18df8b940460&version=3) | not established; company artwork |

## Other local files

`manifest.json` stores original source URLs, UTC download dates, field evidence and hashes. `truth.csv` contains source-backed medicine fields, not human pixel transcriptions. `candidates.json` stores frozen discovery results. `README.md` records the legacy collection method. `.gitattributes` preserves original bytes when rebuilding. These files remain local and are not part of the device evaluation.

## Outstanding work

Collect about 20 actual medical-device labels with the target symbols. Include medicine packaging only when relevant symbols are present, tag its module separately and exclude it from device metrics. Any automated symbol tags must say `LLM-labelled`, with uncertainty. No device-symbol count or accuracy is claimed here.


## Reviewed DailyMed device-symbol collection (2026-11-16)

Rebuild from a clean checkout with the CV dependencies installed:

```sh
python scripts/real/fetch_dailymed.py
# Recheck saved fingerprints and regenerate crops without network:
python scripts/real/fetch_dailymed.py --offline
```

The originals, source ZIPs, crops and annotations.json are saved in ignored
`data/real/devices/`. Every annotation is **LLM-labelled**, visually assigned in this
session, not human truth. Coordinates are original-image pixels `[left, top, right, bottom]`,
with right/bottom excluded. No exhaustive absence labels, OCR, detector evaluation or
accuracy claim is supplied. All selected originals contain a visually reviewed symbol.
Counts: 20 images from 17 SPL records in eight label families, with 44 crops.
Fourteen crops have a side below 25 original pixels and are explicitly marked small;
this pixel threshold is a resolution flag, not a measured accuracy or quality score.
This is a development collection: similar manufacturer layouts must be grouped before
any train/test split. Repeated panels inside an image are counted once. Example-only Centurion
artworks were excluded from the final catalog. Blank or sample lot/date fields
in published artwork are not transcribed as real production values.
Drug-eluting implants and combination kits remain device-classified artwork here;
separate medicine-component panels were excluded after visual review.

No open license has been established for these company artworks. Public availability
is not a public-domain determination. Source: National Library of Medicine;
[rights policy](https://www.nlm.nih.gov/web_policies.html#copyright).

| Local image | Product | Family | Module | Symbols annotated | Exact source ZIP | Rights |
|---|---|---|---|---|---|---|
| `devices/images/device_01.jpg` | KeragelT | Molecular Biologicals | device | manufacturer, expiry, sterile_r | [v6](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=03158b35-ce56-4652-8723-ab57fa292268&version=6) | not established; company artwork |
| `devices/images/device_02.jpg` | StrataXRT | Stratpharma | device | manufacturer, sterile_r | [v2](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1659f62b-02fd-4dd0-8092-41e2a7b34d6b&version=2) | not established; company artwork |
| `devices/images/device_03.jpg` | Pressure activated safety lancets | Care Living | device | expiry, consult_instructions | [v2](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=d491f12b-f766-4c59-a92b-bcb465699ed0&version=2) | not established; company artwork |
| `devices/images/device_04.jpg` | StrataMark | Stratpharma | device | manufacturer, consult_instructions | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=274312bf-5db7-4512-accf-9bace6865171&version=1) | not established; company artwork |
| `devices/images/device_05.jpg` | Keramatrix | Molecular Biologicals | device | expiry, manufacturer, sterile_r | [v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=2a20cd23-bdcc-453e-a72c-de7c123b3db8&version=3) | not established; company artwork |
| `devices/images/device_06.jpg` | Wiley Spinal | Epimed | device | sterile_eo, expiry | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=2ddbb193-4e4f-4ff5-bac1-41d7b8e91260&version=1) | not established; company artwork |
| `devices/images/device_07.jpg` | ACL10SPSL12 | Clint | device | sterile_eo, do_not_reuse | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=3344ac69-fa69-4f91-ae08-b875574e6b08&version=1) | not established; company artwork |
| `devices/images/device_08.jpg` | StrataTriz | Stratpharma | device | manufacturer, consult_instructions | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=50f7848d-9fd4-4529-a567-1256888aa137&version=1) | not established; company artwork |
| `devices/images/device_09.jpg` | Keroxx | Molecular Biologicals | device | manufacturer, sterile_r, expiry | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=584f247b-1a6d-4082-82e8-a17d8015ff1b&version=1) | not established; company artwork |
| `devices/images/device_10.jpg` | ACL10SP | Clint | device | sterile_eo, do_not_reuse | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6527c5bc-8c8a-4c43-b7ac-03ad05801cf4&version=1) | not established; company artwork |
| `devices/images/device_11.jpg` | PROPEL | Intersect ENT | device | sterile_r, expiry, do_not_reuse | [v15](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1&version=15) | not established; company artwork |
| `devices/images/device_12.jpg` | PROPEL mini | Intersect ENT | device | sterile_r, expiry | [v15](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1&version=15) | not established; company artwork |
| `devices/images/device_13.jpg` | PROPEL contour | Intersect ENT | device | sterile_r, expiry | [v15](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1&version=15) | not established; company artwork |
| `devices/images/device_14.jpg` | V49663C-25 spinal kit | Smiths Medical | device | sterile_eo, manufacturer | [v2](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6e04f24a-a4ca-4e84-b3b3-7deba0b9cad0&version=2) | not established; company artwork |
| `devices/images/device_15.jpg` | StrataGRT | Stratpharma | device | manufacturer, sterile_r | [v2](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=732ad204-c969-40db-95c7-e5da5801f910&version=2) | not established; company artwork |
| `devices/images/device_16.jpg` | ACL5SP | Clint | device | sterile_eo, do_not_reuse | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=7a85a79e-a0b9-4e51-9dc2-01a6e3e0b2a5&version=1) | not established; company artwork |
| `devices/images/device_17.jpg` | ACL17SPG | Clint | device | sterile_eo, expiry | [v4](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=88f6e5e4-0179-41aa-854b-a148fe49fe58&version=4) | not established; company artwork |
| `devices/images/device_18.jpg` | StrataCTX | Stratpharma | device | manufacturer, sterile_r | [v1](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=e5f966d7-71d1-4324-ab02-3c841bd702f5&version=1) | not established; company artwork |
| `devices/images/device_19.jpg` | Aceso Ag dressing | NBGS | device | sterile_eo, do_not_reuse | [v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=ebff5325-d1d3-4f14-b575-9ccf9ab53896&version=3) | not established; company artwork |
| `devices/images/device_20.jpg` | Aceso Ag dressing carton | NBGS | device | sterile_eo, do_not_reuse | [v3](https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=ebff5325-d1d3-4f14-b575-9ccf9ab53896&version=3) | not established; company artwork |

### Rebuild catalog and original-pixel annotations

The collector reads this JSON directly; no untracked manifest is needed to rebuild.

<!-- device-catalog -->
```json
[
  {
    "id": "device_01",
    "product": "KeragelT",
    "family": "Molecular Biologicals",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "03158b35-ce56-4652-8723-ab57fa292268",
    "version": "6",
    "member": "keragelt-01.jpg",
    "size_px": [
      851,
      1451
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=03158b35-ce56-4652-8723-ab57fa292268&version=6",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=03158b35-ce56-4652-8723-ab57fa292268",
    "archive_sha256": "dcda848cd1a1b5d6fb1243ea50b3446bf077580f2fd7007f317ceca76bab3cfd",
    "image_sha256": "631ad126867570a885a5ef05faf48220a182c97a66bd75232ea22603ee221094",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          493,
          1192,
          537,
          1247
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          86,
          1136,
          111,
          1177
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          116,
          1218,
          165,
          1241
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_02",
    "product": "StrataXRT",
    "family": "Stratpharma",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "1659f62b-02fd-4dd0-8092-41e2a7b34d6b",
    "version": "2",
    "member": "StrataXRT Box Label.jpg",
    "size_px": [
      1350,
      974
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=1659f62b-02fd-4dd0-8092-41e2a7b34d6b&version=2",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1659f62b-02fd-4dd0-8092-41e2a7b34d6b",
    "archive_sha256": "50fc68adae83cfe0a6dc9f52fdbe28395108a133adc413ddfd5d6d25bf31ca36",
    "image_sha256": "163d389694730750609e5d8e0fe4769e084bc4d6d66c3cf829346bc6454752b1",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          460,
          597,
          479,
          616
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          317,
          604,
          349,
          619
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_03",
    "product": "Pressure activated safety lancets",
    "family": "Care Living",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "d491f12b-f766-4c59-a92b-bcb465699ed0",
    "version": "2",
    "member": "label pic.jpg",
    "size_px": [
      1179,
      769
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=d491f12b-f766-4c59-a92b-bcb465699ed0&version=2",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=d491f12b-f766-4c59-a92b-bcb465699ed0",
    "archive_sha256": "efd4d216d36c82989261ece519ad3f34b34d46c5c7b04eca221c166df6a7db8e",
    "image_sha256": "afad644b78a8ff47615ac449efaecb59245131d4d2b0abd44b9f3d5912d6dcd2",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          403,
          751,
          420,
          768
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "consult_instructions",
        "bbox_xyxy_px": [
          439,
          465,
          456,
          481
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_04",
    "product": "StrataMark",
    "family": "Stratpharma",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "274312bf-5db7-4512-accf-9bace6865171",
    "version": "1",
    "member": "StrataMark 50g box.jpg",
    "size_px": [
      2805,
      1976
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=274312bf-5db7-4512-accf-9bace6865171&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=274312bf-5db7-4512-accf-9bace6865171",
    "archive_sha256": "70bc139b9482d7839adf251e1bc8a7a66e16cd1c4f786b3565030d5f256c55bf",
    "image_sha256": "b51a49cdf0222ed5dc7b62762afa5d1834631a718ea3218df423d1b73e7fd02a",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          1163,
          1002,
          1221,
          1056
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "consult_instructions",
        "bbox_xyxy_px": [
          775,
          997,
          859,
          1081
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_05",
    "product": "Keramatrix",
    "family": "Molecular Biologicals",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "2a20cd23-bdcc-453e-a72c-de7c123b3db8",
    "version": "3",
    "member": "keramatrix-01.jpg",
    "size_px": [
      981,
      699
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=2a20cd23-bdcc-453e-a72c-de7c123b3db8&version=3",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2a20cd23-bdcc-453e-a72c-de7c123b3db8",
    "archive_sha256": "6e6658f861121033e94fbd60c125c0be8d796e718c8833aee63b753a4758de82",
    "image_sha256": "844759181a8fc5301094cea884e03ba3fe7e8115269bc5bb114891dab2cca194",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          40,
          386,
          82,
          458
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          756,
          603,
          796,
          649
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          82,
          476,
          164,
          503
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_06",
    "product": "Wiley Spinal",
    "family": "Epimed",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "2ddbb193-4e4f-4ff5-bac1-41d7b8e91260",
    "version": "1",
    "member": "_0826141950_002.jpg",
    "size_px": [
      1700,
      2200
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=2ddbb193-4e4f-4ff5-bac1-41d7b8e91260&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=2ddbb193-4e4f-4ff5-bac1-41d7b8e91260",
    "archive_sha256": "b5a9f4fae01340e7d4ff5309b3811e3070accce02757fc37b60c4c5b1ce7e395",
    "image_sha256": "f5c47723d6d0157c1afe3d3fda71572fb66e6f583eb2f67c1d8b81474896a9b3",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          628,
          270,
          748,
          322
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          408,
          864,
          442,
          922
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_07",
    "product": "ACL10SPSL12",
    "family": "Clint",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "3344ac69-fa69-4f91-ae08-b875574e6b08",
    "version": "1",
    "member": "ACL10SPSL12.jpg",
    "size_px": [
      2550,
      1650
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=3344ac69-fa69-4f91-ae08-b875574e6b08&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=3344ac69-fa69-4f91-ae08-b875574e6b08",
    "archive_sha256": "2f19462043fd003673a259ef69c67b6b43bf4420fb3752a663604d355ac1b1d1",
    "image_sha256": "80de1d61da3fe473b3ae295475204ef4a2c0f977e55bbd52cfa4d225d9f60acc",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Two duplicate printed panels count as one source image; only one panel annotated.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          763,
          1013,
          899,
          1064
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "do_not_reuse",
        "bbox_xyxy_px": [
          589,
          1006,
          644,
          1064
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_08",
    "product": "StrataTriz",
    "family": "Stratpharma",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "50f7848d-9fd4-4529-a567-1256888aa137",
    "version": "1",
    "member": "StratTriz 20g box.jpg",
    "size_px": [
      2757,
      1795
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=50f7848d-9fd4-4529-a567-1256888aa137&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=50f7848d-9fd4-4529-a567-1256888aa137",
    "archive_sha256": "8e3969435ff9c7ba59036c9c1544a1db99a028b13653dd64ff506ec67c7048f5",
    "image_sha256": "090b3d459ef36d31afb2ff8fe992f202f9ad1413b02c05af72d78c0dbf289008",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          1105,
          895,
          1160,
          948
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "consult_instructions",
        "bbox_xyxy_px": [
          742,
          895,
          822,
          963
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_09",
    "product": "Keroxx",
    "family": "Molecular Biologicals",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "584f247b-1a6d-4082-82e8-a17d8015ff1b",
    "version": "1",
    "member": "keroxx-01.jpg",
    "size_px": [
      979,
      986
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=584f247b-1a6d-4082-82e8-a17d8015ff1b&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=584f247b-1a6d-4082-82e8-a17d8015ff1b",
    "archive_sha256": "ee3341b14b4190f37b8825677d4883c8d639ce81e1af9795eab6d66ddf334a2b",
    "image_sha256": "5380389b506756bb2fe17be49b4476a6c25bb9f1a3ecbfc1aa8fbe65708e7f92",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          349,
          300,
          378,
          333
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          654,
          140,
          732,
          171
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          543,
          186,
          569,
          223
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_10",
    "product": "ACL10SP",
    "family": "Clint",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "6527c5bc-8c8a-4c43-b7ac-03ad05801cf4",
    "version": "1",
    "member": "ACL10SP.jpg",
    "size_px": [
      2550,
      1650
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6527c5bc-8c8a-4c43-b7ac-03ad05801cf4&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6527c5bc-8c8a-4c43-b7ac-03ad05801cf4",
    "archive_sha256": "1d35801105427860844bfe1b9c244dfe309d190aa3338b02f5effa78874399d4",
    "image_sha256": "d1c166e3ccdbce5d109756bce9e72c08f9f18eb2468ddb97dc86233611db1a18",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Two duplicate printed panels count as one source image; only one panel annotated.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          675,
          1043,
          797,
          1089
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "do_not_reuse",
        "bbox_xyxy_px": [
          533,
          1041,
          586,
          1092
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_11",
    "product": "PROPEL",
    "family": "Intersect ENT",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1",
    "version": "15",
    "member": "image-4.jpg",
    "size_px": [
      445,
      302
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1&version=15",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1",
    "archive_sha256": "f864bf8bfc2d7c758907e51772ea7eee5f5cd74b91c48640f0cfae252c5f6565",
    "image_sha256": "e8244757ddd1fccd1e342b918618c5e8bb95c467c0631a6df2e267d60a218814",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Drug-eluting device kit, classified MEDICAL DEVICE by SPL; sample lot/date values.",
    "symbols": [
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          100,
          194,
          142,
          210
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          8,
          214,
          23,
          233
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "do_not_reuse",
        "bbox_xyxy_px": [
          258,
          168,
          284,
          196
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_12",
    "product": "PROPEL mini",
    "family": "Intersect ENT",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1",
    "version": "15",
    "member": "image-5a.jpg",
    "size_px": [
      542,
      363
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1&version=15",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1",
    "archive_sha256": "f864bf8bfc2d7c758907e51772ea7eee5f5cd74b91c48640f0cfae252c5f6565",
    "image_sha256": "4004ff02db4db306be77d9bd7d8f2f166bc1f86314ffa6d0d2eecf4569df34dc",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Drug-eluting device kit, classified MEDICAL DEVICE by SPL; sample lot/date values.",
    "symbols": [
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          124,
          231,
          181,
          251
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          19,
          255,
          35,
          278
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_13",
    "product": "PROPEL contour",
    "family": "Intersect ENT",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1",
    "version": "15",
    "member": "image-6a.jpg",
    "size_px": [
      519,
      357
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1&version=15",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6befbf16-3f60-4ce8-94ec-5ce6a2b7f4e1",
    "archive_sha256": "f864bf8bfc2d7c758907e51772ea7eee5f5cd74b91c48640f0cfae252c5f6565",
    "image_sha256": "b94a4d2fcf93f885d987b31665f77b59083eff4bc85fb929a62fcf4e071efee6",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Drug-eluting device kit, classified MEDICAL DEVICE by SPL; sample lot/date values.",
    "symbols": [
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          118,
          229,
          175,
          249
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          18,
          251,
          34,
          274
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_14",
    "product": "V49663C-25 spinal kit",
    "family": "Smiths Medical",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "6e04f24a-a4ca-4e84-b3b3-7deba0b9cad0",
    "version": "2",
    "member": "V49663C-25.jpg",
    "size_px": [
      1650,
      844
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=6e04f24a-a4ca-4e84-b3b3-7deba0b9cad0&version=2",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=6e04f24a-a4ca-4e84-b3b3-7deba0b9cad0",
    "archive_sha256": "2c8a7f54dba3b0a65bf3d0d6def1fd44e61b40db2fa79aa66be0be8954bfbc7a",
    "image_sha256": "fe9dd75ceea70cea8235599ca0516ce5af86d934e448f7fe50fed9471872055b",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          720,
          640,
          848,
          684
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          86,
          649,
          117,
          681
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_15",
    "product": "StrataGRT",
    "family": "Stratpharma",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "732ad204-c969-40db-95c7-e5da5801f910",
    "version": "2",
    "member": "GRT 20 Box Label.jpg",
    "size_px": [
      1228,
      800
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=732ad204-c969-40db-95c7-e5da5801f910&version=2",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=732ad204-c969-40db-95c7-e5da5801f910",
    "archive_sha256": "6367b10e598df4443ca0242c5656988426fb29fc73328630651df6d200333d47",
    "image_sha256": "eeb02a371b02794bbc568a9ea7702bf0352c5a246224a16bbfd4732970752adb",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          493,
          379,
          520,
          404
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          315,
          383,
          358,
          404
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_16",
    "product": "ACL5SP",
    "family": "Clint",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "7a85a79e-a0b9-4e51-9dc2-01a6e3e0b2a5",
    "version": "1",
    "member": "ACL5SP.jpg",
    "size_px": [
      2550,
      1650
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=7a85a79e-a0b9-4e51-9dc2-01a6e3e0b2a5&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=7a85a79e-a0b9-4e51-9dc2-01a6e3e0b2a5",
    "archive_sha256": "8b17d3e0b9c42357af22e21849c31b8fc34b92c129821f0c973f6e7d0c28e15f",
    "image_sha256": "5d19260c70a632a2fba1ddf04fa10fab81a7d14ef7704480c0baf9be9025c95b",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Two duplicate printed panels count as one source image; only one panel annotated.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          730,
          1045,
          879,
          1101
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "do_not_reuse",
        "bbox_xyxy_px": [
          556,
          1038,
          626,
          1101
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_17",
    "product": "ACL17SPG",
    "family": "Clint",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "88f6e5e4-0179-41aa-854b-a148fe49fe58",
    "version": "4",
    "member": "ACL17SPG.jpg",
    "size_px": [
      1650,
      1275
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=88f6e5e4-0179-41aa-854b-a148fe49fe58&version=4",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=88f6e5e4-0179-41aa-854b-a148fe49fe58",
    "archive_sha256": "57ddd1dd80b025b48b31528bfabe0e18fa8fd98e6a7a2186ffa1e38b9354024e",
    "image_sha256": "ef9ed412bac9848a6cbbc84c347ae0e8cd208831206896deb19cae9b335abb6c",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples. Side-panel expiry is rotated.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          639,
          998,
          764,
          1044
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "expiry",
        "bbox_xyxy_px": [
          1377,
          464,
          1426,
          495
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_18",
    "product": "StrataCTX",
    "family": "Stratpharma",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "e5f966d7-71d1-4324-ab02-3c841bd702f5",
    "version": "1",
    "member": "StrataCTX Box Label.jpg",
    "size_px": [
      1350,
      970
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=e5f966d7-71d1-4324-ab02-3c841bd702f5&version=1",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e5f966d7-71d1-4324-ab02-3c841bd702f5",
    "archive_sha256": "889b115d4d0e3a8b8d313ba3e4678224bd1a1e87aa7b5af4553418cc111561de",
    "image_sha256": "7e913300e642a1db50ea7c71f97a5c77dbdd4e8175b7624e18a668f238d26009",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "manufacturer",
        "bbox_xyxy_px": [
          529,
          524,
          549,
          543
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "small: one side below 25 original pixels"
      },
      {
        "name": "sterile_r",
        "bbox_xyxy_px": [
          405,
          532,
          437,
          546
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "small: one side below 25 original pixels"
      }
    ]
  },
  {
    "id": "device_19",
    "product": "Aceso Ag dressing",
    "family": "NBGS",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "ebff5325-d1d3-4f14-b575-9ccf9ab53896",
    "version": "3",
    "member": "Silicone ag  pouch.jpg",
    "size_px": [
      3153,
      2764
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=ebff5325-d1d3-4f14-b575-9ccf9ab53896&version=3",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ebff5325-d1d3-4f14-b575-9ccf9ab53896",
    "archive_sha256": "1cfcd2e8eb37a72ef4666c02b3533122daa37656b9c5a65bd4692229fbd3ee9a",
    "image_sha256": "e41488d31e2e589bf399d38e4aa6a941ceb8ea785edf214b4346165d9108d4c1",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          1442,
          1485,
          1619,
          1560
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text. Method letter read visually; verify at original resolution.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "do_not_reuse",
        "bbox_xyxy_px": [
          1769,
          1482,
          1846,
          1563
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  },
  {
    "id": "device_20",
    "product": "Aceso Ag dressing carton",
    "family": "NBGS",
    "module": "device",
    "condition": "artwork_scan",
    "setid": "ebff5325-d1d3-4f14-b575-9ccf9ab53896",
    "version": "3",
    "member": "Silicone ag box.jpg",
    "size_px": [
      4752,
      3679
    ],
    "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&setid=ebff5325-d1d3-4f14-b575-9ccf9ab53896&version=3",
    "source_page": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=ebff5325-d1d3-4f14-b575-9ccf9ab53896",
    "archive_sha256": "1cfcd2e8eb37a72ef4666c02b3533122daa37656b9c5a65bd4692229fbd3ee9a",
    "image_sha256": "13781a75fa8d7818a4d488d8953256e43a112d5b8dc65c0e910bbebec9a45a90",
    "rights": "Open license not established; company-contributed artwork. Source: National Library of Medicine.",
    "notes": "Partial symbol annotations; related layouts are not independent samples.",
    "symbols": [
      {
        "name": "sterile_eo",
        "bbox_xyxy_px": [
          289,
          2099,
          483,
          2178
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      },
      {
        "name": "do_not_reuse",
        "bbox_xyxy_px": [
          622,
          2095,
          709,
          2182
        ],
        "origin": "LLM-labelled",
        "uncertainty": "Visual AI interpretation, not human reviewed; box includes small margin and may include adjacent text.",
        "resolution_note": "at least 25 original pixels on each side"
      }
    ]
  }
]
```

## Online photos for Task 4 (substitution accepted)

On 2026-11-16 Parth confirmed that Paridhi accepted online photographs as
substitutes for his own captures. These remain online photos, not Parth captures.
The original ten candidates below were inspected along with two additional views
of a decompression needle kit. References are LLM-labelled, saved locally in
`data/real_photos/online/transcriptions.csv`, with uncertainty in annotations.json.
Human review is recorded separately and is not inferred from this acceptance.

Five files are original downloads. Wikimedia rate-limited later originals with
HTTP 429 and recommended standard thumbnail sizes. Seven inputs therefore use
the server's 1280-pixel-wide thumbnails, explicitly listed below. Fingerprints
refer to the evaluated bytes, not to a larger original. No synthetic images or
local enhancements replace these inputs. The two needle-kit views are correlated,
and the two needle-holder views are correlated.

Twelve photos were inspected: seven have at least one readable target field,
and five have no reliable target-field reference and are unscored. Ten field
values were frozen before running OCR. Absence or unreadability is not a correct
extraction. Sterilization packaging accessories and non-English/historical labels
are identified per image; this is a small convenience sample, not a representative
medical-device accuracy benchmark. No medicine images are included.

License and author are taken from each original Commons file page/API. Keep
attribution and license links with any local copies or derivatives. The photograph
license does not establish an open license for depicted company artwork.

The next table preserves the initial discovery notes; evaluated status and file
representations appear in the table below it.

| Candidate / source and original download page | Author | Photo license | Initial discovery limitation | Module |
|---|---|---|---|---|
| [Epidural kit in sterile packaging](https://commons.wikimedia.org/wiki/File:Epidural_kit_in_sterile_packaging.jpg) | Sgroey | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | iPhone 11 metadata; device kit package; three fields unverified | device candidate |
| [Ethylene oxide sticker](https://commons.wikimedia.org/wiki/File:Ethylene_oxide_sterilisation_sticker_on_box_of_medical_supplies.jpg) | Sgroey | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Sterilization sticker; product/lot/expiry may be absent; camera not verified here | device candidate |
| [Curette in sterile packaging](https://commons.wikimedia.org/wiki/File:Curette_in_sterile_packaging.jpg) | Mikael Häggström | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | Device pouch; camera unknown; three fields unverified | device candidate |
| [Medical disposable packaging](https://commons.wikimedia.org/wiki/File:Medizinische_Einwegverpackung_06.JPG) | Werneuchen | Public-domain dedication by photographer on source page | Disposable materials; three fields unverified | device candidate |
| [Sterile dental instruments](https://commons.wikimedia.org/wiki/File:Sterile_instruments_ready_for_use.jpg) | Ptrump16 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Hospital reprocessing label; may use sterilization batch instead of manufacturer lot | device candidate |
| [MELAfol 502](https://commons.wikimedia.org/wiki/File:MELAfol_502.jpg) | Entrancess | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | Sterilization packaging material; may not suit device-field evaluation | device candidate |
| [Needle holder 01](https://commons.wikimedia.org/wiki/File:Mikrochirurgischer_Nadelhalter_01.JPG) | Werneuchen | Public-domain dedication by photographer on source page | Related to candidate 02; three fields unverified | device candidate |
| [Needle holder 02](https://commons.wikimedia.org/wiki/File:Mikrochirurgischer_Nadelhalter_02.JPG) | Werneuchen | Public-domain dedication by photographer on source page | Related to candidate 01; three fields unverified | device candidate |
| [Sterilization packaging materials](https://commons.wikimedia.org/wiki/File:Packaging_materials_for_sterilisation.jpg) | Ivanhoe | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | Panasonic DMC-FZ8 camera; wrapping materials, potentially unsuitable | device candidate |
| [Soviet glass syringe](https://commons.wikimedia.org/wiki/File:Soviet_glass_syringe.png) | im_tau | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Historical Russian packaging; language and missing lot/expiry may exclude it | device candidate |

### Evaluated photo files and pinned representations

| Local filename under data/real_photos/online | Source page | Evaluated download | Representation / dimensions | Rights / author | Readable fields | SHA-256 of evaluated file |
|---|---|---|---|---|---|---|
| `online_01.jpg` | [source](https://commons.wikimedia.org/wiki/File:Epidural_kit_in_sterile_packaging.jpg) | [download](https://upload.wikimedia.org/wikipedia/commons/2/29/Epidural_kit_in_sterile_packaging.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original) | original, 2138x3936 | CC BY-SA 4.0; Sgroey | none; unscored | `edd70662a3cb0cffc5d41ea241ba98021a30ab8c46dcd110e2ce246c7030838b` |
| `online_02.jpg` | [source](https://commons.wikimedia.org/wiki/File:Ethylene_oxide_sterilisation_sticker_on_box_of_medical_supplies.jpg) | [download](https://upload.wikimedia.org/wikipedia/commons/c/c3/Ethylene_oxide_sterilisation_sticker_on_box_of_medical_supplies.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original) | original, 1487x1487 | CC BY-SA 4.0; Sgroey | none; unscored | `ddeb5488c2a413748f5a53e5423563021e0e8260438ed2ac5af5d06e35fd8274` |
| `online_03.jpg` | [source](https://commons.wikimedia.org/wiki/File:Curette_in_sterile_packaging.jpg) | [download](https://upload.wikimedia.org/wikipedia/commons/2/28/Curette_in_sterile_packaging.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original) | original, 950x1600 | CC0; Mikael Häggström. When using this image in external works, it may be cited as: Häggström, Mikael (2014). "Medical gallery of Mikael Häggström 2014". WikiJournal of Medicine 1 (2). DOI:10.15347/wjm/2014.008. ISSN 2002-4436. Public Domain. or By Mikael Häggström, used with permission. | none; unscored | `82459e951e394ac2db925030dad429ac87858c5ca635df26a722a96c92efa5d0` |
| `online_04.jpg` | [source](https://commons.wikimedia.org/wiki/File:Medizinische_Einwegverpackung_06.JPG) | [download](https://upload.wikimedia.org/wikipedia/commons/1/13/Medizinische_Einwegverpackung_06.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original) | original, 1600x1200 | Public domain; Werneuchen | lot | `825dcb0b9f2a39ef1aca807b2660cf5a0250025e1f1064b2a7b90aa1a64e4da6` |
| `online_05.jpg` | [source](https://commons.wikimedia.org/wiki/File:Sterile_instruments_ready_for_use.jpg) | [download](https://upload.wikimedia.org/wikipedia/commons/4/40/Sterile_instruments_ready_for_use.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original) | original, 2976x3968 | CC BY-SA 4.0; Ptrump16 | product_name, expiry | `2c8f570fb3630e30ed926b7bb4df4b3b49881ff91e790fdc55992485cd4b44fa` |
| `online_06.jpg` | [source](https://commons.wikimedia.org/wiki/File:MELAfol_502.jpg) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9d/MELAfol_502.jpg/1280px-MELAfol_502.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x959 | CC BY-SA 4.0; Entrancess | product_name | `6fac65441a1eb6d05fdff41100aa1d6061cf312e040551905fed3e31d6306ca5` |
| `online_07.jpg` | [source](https://commons.wikimedia.org/wiki/File:Mikrochirurgischer_Nadelhalter_01.JPG) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/2/23/Mikrochirurgischer_Nadelhalter_01.JPG/1280px-Mikrochirurgischer_Nadelhalter_01.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x483 | Public domain; Werneuchen | none; unscored | `6f871ec85fe923c839106d6f1acac4d3fac09b5abee7026f99e504723a08c23a` |
| `online_08.jpg` | [source](https://commons.wikimedia.org/wiki/File:Mikrochirurgischer_Nadelhalter_02.JPG) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d3/Mikrochirurgischer_Nadelhalter_02.JPG/1280px-Mikrochirurgischer_Nadelhalter_02.JPG?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x960 | Public domain; Werneuchen | none; unscored | `3c0a6ba94a87a3b61c70ddd6c6ac3dd1b995ec9444a3f81766f0bbb56f6476cb` |
| `online_09.jpg` | [source](https://commons.wikimedia.org/wiki/File:Packaging_materials_for_sterilisation.jpg) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d9/Packaging_materials_for_sterilisation.jpg/1280px-Packaging_materials_for_sterilisation.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x900 | CC BY-SA 3.0; Ivanhoe | product_name | `d1634bd1546fdbde7524f4fbff4aec4b2a6f331c9756e96612f33e50bb813a8f` |
| `online_10.png` | [source](https://commons.wikimedia.org/wiki/File:Soviet_glass_syringe.png) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b1/Soviet_glass_syringe.png/1280px-Soviet_glass_syringe.png?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x1049 | CC BY 4.0; im_tau | product_name | `f814a63c4b56f8f914e02ae11f83ed83fdffd4cd3c611af672deb93aba3cf237` |
| `online_11.jpg` | [source](https://commons.wikimedia.org/wiki/File:Thoacic_Decompression_Needle_1.jpg) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cf/Thoacic_Decompression_Needle_1.jpg/1280px-Thoacic_Decompression_Needle_1.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x720 | CC BY-SA 4.0; Intropin (Mark Oniffrey) | product_name, expiry | `a0342a81ee4137b145eed0392e40dfb5df7a15ef006e8669214e42f2ea07496f` |
| `online_12.jpg` | [source](https://commons.wikimedia.org/wiki/File:Thoacic_Decompression_Needle_2.jpg) | [download](https://thumb.wikimedia.org/wikipedia/commons/thumb/9/96/Thoacic_Decompression_Needle_2.jpg/1280px-Thoacic_Decompression_Needle_2.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=thumbnail) | 1280px server thumbnail, 1280x720 | CC BY-SA 4.0; Intropin (Mark Oniffrey) | product_name, expiry | `5b416b754228c8877d4b603e939cb1fdb131a4b426a345422ffdd48c8a8f846c` |

The needle-kit views are by Intropin (Mark Oniffrey), licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/):
[view 1](https://commons.wikimedia.org/wiki/File:Thoacic_Decompression_Needle_1.jpg),
[view 2](https://commons.wikimedia.org/wiki/File:Thoacic_Decompression_Needle_2.jpg).

Reference decisions: 01 has several component devices but no identifiable outer kit
name; 02 is an indicator sticker; 03 is blurred; 07/08 show manufacturer and pouch
reference rather than an identifiable instrument name. These five are unscored.
04 has a readable lot but ambiguous dual dates; 05 is a Chinese hospital
reprocessing label; 06 and 09 are sterilization-packaging accessories; 10 is
historical Russian syringe packaging; 11/12 are two views of the same needle kits.
Do not infer absent lot/expiry values from dates, filenames or web descriptions.
