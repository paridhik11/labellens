# Step 25a: medicine product-name matching

Retriever: frozen E5b recipe over 10 product documents; decision: bge-large cosine of the top product. Queries are hand-written for this check; the threshold is fitted on them, so the figures below are a sanity check and not an error rate.

- worst positive cosine 0.7083, best negative cosine 0.5906, threshold = midpoint 0.65
- mean time per match after the models are loaded: 0.58 s

| kind | query | expected | top product | cosine | decision |
|---|---|---|---|---|---|
| exact | Pain Relief Extra Strength | Pain Relief Extra Strength | Pain Relief Extra Strength | 0.7311 | accept |
| exact | Childrens Ibuprofen | Childrens Ibuprofen | Childrens Ibuprofen | 0.7766 | accept |
| exact | Loratadine | Loratadine | Loratadine | 0.7319 | accept |
| exact | Omeprazole | Omeprazole | Omeprazole | 0.7443 | accept |
| exact | FAMOTIDINE | FAMOTIDINE | FAMOTIDINE | 0.7083 | accept |
| exact | Amoxicillin | Amoxicillin | Amoxicillin | 0.7253 | accept |
| exact | METFORMIN HYDROCHLORIDE | METFORMIN HYDROCHLORIDE | METFORMIN HYDROCHLORIDE | 0.8139 | accept |
| exact | Atorvastatin Calcium | Atorvastatin Calcium | Atorvastatin Calcium | 0.8130 | accept |
| exact | Levothyroxine Sodium | Levothyroxine Sodium | Levothyroxine Sodium | 0.7707 | accept |
| exact | ALBUTEROL SULFATE | ALBUTEROL SULFATE | ALBUTEROL SULFATE | 0.7385 | accept |
| noisy | tylenol extra strength acetaminophen caplets | Pain Relief Extra Strength | Pain Relief Extra Strength | 0.8157 | accept |
| noisy | Omeprazole 20 mg delayed release tablets | Omeprazole | Omeprazole | 0.7555 | accept |
| noisy | Famotadine oral suspension | FAMOTIDINE | FAMOTIDINE | 0.8081 | accept |
| noisy | Amoxicilin 500mg capsules | Amoxicillin | Amoxicillin | 0.7940 | accept |
| noisy | metformin | METFORMIN HYDROCHLORIDE | METFORMIN HYDROCHLORIDE | 0.7272 | accept |
| noisy | levothyroxine 75 mcg | Levothyroxine Sodium | Levothyroxine Sodium | 0.7929 | accept |
| noisy | atorvastatin 40 mg tablets | Atorvastatin Calcium | Atorvastatin Calcium | 0.7136 | accept |
| noisy | childrens loratadine allergy relief | Loratadine | Loratadine | 0.7880 | accept |
| negative | Losartan potassium tablets | (none) | Levothyroxine Sodium | 0.5468 | no_reference_match |
| negative | Lipitor | (none) | Atorvastatin Calcium | 0.5875 | no_reference_match |
| negative | Lisinopril | (none) | Loratadine | 0.5796 | no_reference_match |
| negative | Aspirin 81 mg | (none) | Amoxicillin | 0.5770 | no_reference_match |
| negative | Vitamin C gummies | (none) | Omeprazole | 0.5861 | no_reference_match |
| negative | Advil | (none) | Childrens Ibuprofen | 0.5850 | no_reference_match |
| negative | Cetirizine | (none) | Loratadine | 0.5906 | no_reference_match |
| negative | Ozempic pen | (none) | Childrens Ibuprofen | 0.4973 | no_reference_match |
| negative | Sertraline 50 mg | (none) | Pain Relief Extra Strength | 0.5880 | no_reference_match |
| negative | Prednisone | (none) | Atorvastatin Calcium | 0.5226 | no_reference_match |
| negative | Zzyzx Gummies | (none) | Childrens Ibuprofen | 0.5556 | no_reference_match |
| negative | Digital thermometer | (none) | Pain Relief Extra Strength | 0.5034 | no_reference_match |

Wrong decisions at threshold 0.65: 0 of 30.
