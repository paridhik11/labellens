# Public photo scan: KEPT (E), earlier candidates not kept

**KEPT:** real `publicScan` and `getPublicScan` (CR-27), camera and upload, retake gate, a loading state (spinner, "up to a minute"), a confirm step (a photo never confirms itself: "Is this X?", OCR lines, Confirm / Not this one / Type the name; label shown only after Confirm), and frozen method E.
**CANDIDATE, not kept:** A, B, C (dev: 20 of 45 decoys wrong). D (fresh set: 3 wrong, one confusable decoy shown as metformin).

Method: OCR every line, candidate strings, the unchanged matcher (0.65). E = D (a distinctive name word must be visible) plus: another product's ingredient word in the text makes a match a review. E was designed after D's fresh failure; protocols v1 to v4 were committed before scoring.

## Gate (E, scored once, 15 decoy products never used before)
- **Product level: 0 wrong of 15** (Wilson 95%: 0 to 20%). Photo level: 0 wrong of 45 (0 to 7.9%); 15 review, 17 not identified, **13 of 45 timed out**.
- **Latency: median 47.0 s, max 54.5 s** (p90 50.3 s), all under 60 s.
- Merge checks: fast suite 959 passed, ruff clean, demo_e2e 20/20, 61 states mock and api 0 failed, live flows 0 FAIL (golden 9/9), camera and confirm checks pass.

## Limits
- Real DailyMed artwork with simulated camera conditions, one source, software-read. **Real phone photos are unmeasured.**
- The lexicon holds these decoy names, and none is a combination of a reference product: easier than D's failing case.
- Correct identification was not measured fresh for E (D: 34 of 57, 46.7 to 71.4%).
- **Exposed re-run** of E on the older fresh set: stopped after 6 of 177 photos (`..._PARTIAL`), not a result; to run after the merge.
- The 50 CV4b device packs were exposed to an older name check; this method was never fitted to them.
