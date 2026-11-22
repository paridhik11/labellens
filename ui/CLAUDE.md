# UI Development Guidelines for LabelLens

LabelLens UI is a static web interface for medical product packaging information and label compliance.

## Hard Rules

1. Work only inside `ui/`. Never edit `docs/`, `src/`, `tests/`, `data/`, or `.github/`.
2. Never invent data. All mock data, fields, candidate structures, citations, and inspection findings must come directly from `src/api/mock/index.json` and its referenced mock files, or the official schema contracts.
3. All data loading must happen in `ui/js/data.js` via `CONFIG` and `loadScreen(screen, state)`.
4. Keep public medicine mode and professional device workspace strictly separate. They do not share views, data, or regulatory corpora (public mode uses 21 CFR 201, 208, 211; professional mode uses 21 CFR 801, 820, 830).
5. Demo banner on every page: "DEMO MODE: Sample data for course evaluation. Not for clinical use." Public screens must additionally display: "Authenticity not verified. Based on a reference label match."
6. Do not use em dashes in documentation, comments, or UI text. Use hyphens, colons, or parentheses instead.
7. Test identifiers must always be labelled TEST (e.g., GS1 test placeholder `(01)00000000000000 [TEST]`).
8. Mark all drafts clearly: generated artwork and draft previews must display a prominent DRAFT badge or watermark and the required disclaimer: "Draft generated for review. Not a compliance determination."
9. Branch safety: verify current branch with `git branch --show-current` before every commit; it must be `ishanvi-ui`. Never push directly to `main`.

## Running the UI Locally

Run an HTTP server from the repository root:
```bash
python -m http.server 8000
```
Then navigate in your browser to:
`http://localhost:8000/ui/` or `http://localhost:8000/ui/index.html`

With the demo: `python scripts/run_demo.py` serves the UI at `http://127.0.0.1:8000/ui/` next to the API (api mode by default: live calls, with the mock fallback marked X-Mock; `?mode=mock` for the static mocks).
Checks: `PLAYWRIGHT_DIR=<dir with node_modules/playwright> node ui/tools/check_screens.cjs [--shots]` (set `MODE=api` for api mode) and `ui/tools/live_flows.cjs`.

## Architecture Overview

- `ui/index.html`: Main shell with two distinct entry points (Public Medicine and Professional Device Workspace).
- `ui/css/base.css`: CSS variables, reset, typography, layout grid, and spacing derived from `docs/mockup/website_concept.png`.
- `ui/css/components.css`: Buttons, cards, badges, banners, navigation, tabs, label preview canvas, and floating dev panel styling.
- `ui/js/data.js`: Centralized data loader (`loadScreen`, `getStatesForScreen`, `CONFIG`) reading `/src/api/mock/index.json`.
- `ui/js/state-switcher.js`: Floating dev panel that dynamically discovers and displays only the mock states valid for the active screen.
- `ui/REPORT.md`: Consolidated log of UI step reports, notes, gaps, and pending backend integrations.
