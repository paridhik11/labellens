# Confirmed real-photo symbol evaluation

Condition: photo. Ten original online device-package images, previously exposed.
References: AI-assisted, human-confirmed by reviewer identifier parth2, reported
by Parth on 2026-11-20. This was assisted, unblinded annotation, not independently
witnessed review. Manufacturer excludes outlined date-of-manufacture icons.

Protocol: deployed v1 `detect_symbols_blind`, original upright RGB images,
unchanged defaults, no crop, orientation search or threshold tuning. This tests
the standalone detector, not the full extractor's rectified-image path.
Each photo/category is one presence decision; repeated instances are collapsed.
No pixel-box localization score is possible from these references.

| Category | Supported | TP | FP | FN | TN | Recall |
|---|---|---:|---:|---:|---:|---:|
| Manufacturer | yes | 0 | 0 | 4 | 6 | 0/4 |
| Hourglass | yes | 0 | 0 | 9 | 1 | 0/9 |
| Sterile EO | no | 0 | 0 | 8 | 2 | 0/8 |
| Sterile R | no | 0 | 0 | 1 | 9 | 0/1 |
| Do not reuse | no | 0 | 0 | 9 | 1 | 0/9 |
| Consult instructions | no | 0 | 0 | 5 | 5 | 0/5 |

TP: present/detected; FP: absent/detected; FN: present/missed; TN: absent/not
detected. Unsupported rows measure missing capability. Precision is undefined
because there were zero predictions. No exceptions or detector changes occurred.

Missed manufacturer photos: 04,06,09,10. Missed hourglass photos: all except 05.
This negative result establishes weak transfer for this protocol, not general
device accuracy. Localization, instance counts and unseen-photo testing remain.

Reproduce: `python -m scripts.cv_experiments.eval_confirmed_symbols --output data/real_photos/confirmed_symbols_v1.json`.
Output is immutable. Raw detections and source fingerprints stay local in that
JSON; the committed config pins the ten inputs and annotations.
