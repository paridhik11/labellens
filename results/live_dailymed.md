# Live DailyMed lookup: fresh-set result (scored once)

Run date 2026-11-22. Protocol: `reports/live_dailymed_protocol.md` (committed before scoring). Other jobs (a docs session and a scan re-run) were running on this machine, so the timings are not clean.

| Measure | Result |
|---|---|
| Right label in the candidate list (found) | 29/30 (97%, Wilson 95% 83 to 99%) |
| Fetched, parsed and indexed | 29/30 (97%, Wilson 95% 83 to 99%) |
| Answered with at least one citation | 27/30 (90%, Wilson 95% 74 to 97%) |
| Wrong-product answers shown as correct (all 40 queries) | 0 |
| Products with a citation that failed verification | 0 of 29 checked |
| Decoys rejected (empty list, no local accept) | 10/10 (100%, Wilson 95% 72 to 100%) |
| Median fetch-to-answer (cold, products that were answered) | 30.7 s (min 4.6, max 355.9, n=29) |

## Gate

- G1 zero wrong-product answers shown as correct: **PASS** (0)
- G2 every shown citation verified: **PASS** (0 products with a failure)
- G3 decoys rejected 10 of 10: **PASS** (10/10)
- G4 median fetch-to-answer reported: yes

**Gate decision: PASSED**

## Per item

| id | typed | class | local | list | found | answered | fetch-to-answer s | note |
|---|---|---|---|---|---|---|---|---|
| p01 | Benadryl | otc | no_reference_match | candidates (10/30) | True | True | 8.84 |  |
| p02 | Allegra | otc | no_reference_match | candidates (10/18) | True | True | 5.93 |  |
| p03 | Mucinex | otc | no_reference_match | candidates (10/168) | True | True | 8.11 |  |
| p04 | Imodium | otc | no_reference_match | candidates (5/5) | True | True | 16.01 |  |
| p05 | Dulcolax | otc | no_reference_match | candidates (10/17) | True | True | 6.61 |  |
| p06 | Sudafed | otc | no_reference_match | candidates (10/21) | True | True | 14.72 |  |
| p07 | Prevacid 24HR | otc | no_reference_match | no_candidates (0/0) | False | False |  |  |
| p08 | Tums | otc | no_reference_match | candidates (10/34) | True | True | 8.14 |  |
| p09 | Gas-X | otc | no_reference_match | candidates (8/8) | True | True | 4.61 |  |
| p10 | Monistat | otc | no_reference_match | candidates (10/21) | True | True | 9.41 |  |
| p11 | Rogaine | otc | no_reference_match | candidates (5/5) | True | True | 10.27 |  |
| p12 | Afrin | otc | no_reference_match | candidates (10/16) | True | True | 6.95 |  |
| p13 | levofloxacin | rx | no_reference_match | candidates (10/145) | True | True | 126.06 |  |
| p14 | methotrexate | rx | no_reference_match | candidates (10/49) | True | True | 355.9 |  |
| p15 | lithium carbonate | rx | no_reference_match | candidates (10/88) | True | True | 16.79 |  |
| p16 | risperidone | rx | no_reference_match | candidates (10/118) | True | True | 268.66 |  |
| p17 | Xanax | rx | no_reference_match | candidates (5/5) | True | False | 95.46 |  |
| p18 | clonazepam | rx | no_reference_match | candidates (10/148) | True | True | 70.72 |  |
| p19 | ramipril | rx | no_reference_match | candidates (10/55) | True | True | 60.42 |  |
| p20 | amiodarone | rx | no_reference_match | candidates (10/62) | True | False | 72.83 |  |
| p21 | tamoxifen | rx | no_reference_match | candidates (10/18) | True | True | 88.58 |  |
| p22 | letrozole | rx | no_reference_match | candidates (10/28) | True | True | 49.43 |  |
| p23 | oxybutynin | rx | no_reference_match | candidates (10/120) | True | True | 22.13 |  |
| p24 | lorazepam | rx | no_reference_match | candidates (10/172) | True | True | 38.79 |  |
| p25 | ropinirole | rx | no_reference_match | candidates (10/82) | True | True | 200.33 |  |
| p26 | terbinafine | rx | no_reference_match | candidates (10/108) | True | True | 25.15 |  |
| p27 | sucralfate | rx | no_reference_match | candidates (10/88) | True | True | 34.87 |  |
| p28 | haloperidol | rx | no_reference_match | candidates (10/137) | True | True | 104.15 |  |
| p29 | prochlorperazine | rx | no_reference_match | candidates (10/85) | True | True | 105.69 |  |
| p30 | isosorbide mononitrate | rx | no_reference_match | candidates (10/63) | True | True | 30.74 |  |
| d01 | Zorvanex | invented | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d02 | Quillacor | invented | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d03 | Brenvitol Plus | invented | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d04 | Lumexiprine | invented | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d05 | Dexcom G7 | device | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d06 | Accu-Chek Guide | device | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d07 | DreamStation CPAP | device | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d08 | Rimadyl | veterinary | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d09 | Apoquel | veterinary | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
| d10 | Heartgard | veterinary | no_reference_match | no_candidates (0) | - | rejected=True | - |  |
