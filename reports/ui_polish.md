# UI polish (branch ui-polish)

Visual change only. No ids, data attributes, copy of banners or disclaimers changed.

## Choices
- Icons: all emoji removed from `ui/` (sidebar nav, empty states, scan and evidence cards). 16 monochrome inline SVG icons, stroke style, one weight (1.75), `currentColor`, text labels kept. Class `.icon` in `base.css`. The dev switcher's arrow glyphs became the words Expand and Collapse.
- Font: Figtree (variable, latin, one file, 20 KB) self-hosted at `ui/assets/fonts/figtree-latin-wght-normal.woff2` with the OFL licence beside it. Source: the `@fontsource-variable/figtree` 5.2.10 npm package. `font-display: swap`, system-ui fallback, no CDN. Body 16px, line-height 1.5, weights 400/500 body, 600/700 headings.
- Colour: text `#0F172A`, muted `#475569`, cool slate neutrals, one accent (teal `#0f6e70`) for actions, links, active nav and avatar. The former blue sidebar highlight became teal. Status colours stay distinct (danger red, warning amber, draft purple, info blue) and every badge keeps its text label.
- Contrast (WCAG ratio, computed): body 17.9, muted 7.6 on white and 6.9 on subtle slate, teal on white 6.0, badges: teal 5.3, danger 5.3, warning 6.8, draft white on purple 7.1, info 5.2. Fixed failures: muted `#64748b` on slate (4.3), danger badge (3.95), DEMO pill (4.2), warning notice icon (white on amber 2.1), error text on the dark dev box.
- Style: gradient logo mark flat, portal card border 2px to 1px, no hover lift, shadows removed or near invisible, radius 12 to 8. `--color-border-subtle` was used but never defined (key-value rows had no divider); now defined, so those rows get a thin divider.
- Dev State Switcher: it drives which mock state a screen renders, so it still runs, but it is hidden unless `?dev=1` and starts collapsed (`&devopen=1` starts it open). The three check scripts now open pages with `?dev=1&devopen=1`.
- `src/api/pages.py` line 17: med100 had not touched it, so "Only ten reference labels are loaded" became "Only a limited set of reference labels is loaded." (the count is changing on med100).
- Left alone on purpose: the red, orange and amber colours inside the D2 and D6 label mock-ups (they draw layout findings, not UI chrome).

## Checks (real run, worktree code, demo on port 8010 with the shared index store)
- `check_screens.cjs` mock: 61 states, 0 failed, 11 click-throughs.
- `check_screens.cjs` api (MODE=api): 61 states, 0 failed, 11 click-throughs.
- `live_flows.cjs` with PRODUCT, GOOD_FILE, BLUR_IMAGE and GOLDEN_JSON: 16 flows, 0 FAIL, 1 FALLBACK (publicScan is a mock), E2E golden 9/9.
- Screenshots (switcher hidden, mock mode): `ui/screenshots_polished/` (portal, P2, D1, D4, D6, D7).

## Not done
Not checked on a real phone or in Safari or Firefox (headless Chromium only). The old `ui/screenshots/` are unchanged and look different.
