# Phase 7 — Cutover + Legacy Quarantine

**Status:** COMPLETE
**Approach:** Keep the legacy Jinja UI mounted under `/legacy/*` for side-by-side comparison instead of removing it. The new React SPA owns `/` and all unprefixed routes (the `/api/v1/*` REST API is unchanged).

## Goals

- Cut over `/` to serve the React SPA from `frontend/dist/`.
- Preserve full legacy access at `/legacy/*` so users can browse the old flow as a comparison reference.
- Surface visible cross-links in both UIs so it's obvious how to switch.
- Keep all existing test coverage green.

## Changes

### Backend

- **routes/__init__.py**
  - Added `LEGACY_PREFIX = "/legacy"`.
  - Mounted all 10 legacy HTML blueprints with `url_prefix=LEGACY_PREFIX`:
    `index_bp`, `load_character_bp`, `starter_characters_bp`, `character_creation_bp`, `background_bp`, `species_bp`, `languages_bp`, `ability_scores_bp`, `equipment_bp`, `character_summary_bp`.
  - Left `test_api_bp` (`/api/test`) and `api_v1_bp` (`/api/v1`) unprefixed — these are the JSON contract for the SPA.
  - Net effect: every legacy route is reachable at `/legacy/<original-path>` (e.g. `/legacy/character-summary`, `/legacy/api/rebuild-character`). Templates use `url_for(<blueprint>.<endpoint>)` so internal links resolve automatically.

- **app.py**
  - Imported `Path`, `send_from_directory`, `jsonify`.
  - Added `_SPA_DIR = Path(__file__).parent / "frontend" / "dist"`.
  - Added `serve_spa(path)` catch-all on `/` and `/<path:path>`:
    - If `frontend/dist/` does not exist → returns a 503 JSON payload telling the operator to run `cd frontend && npm run build`.
    - If a file matching the requested path exists → served via `send_from_directory` (handles hashed assets, manifest, sw.js, icons).
    - Otherwise → falls back to `index.html` so React Router can handle deep links like `/wizard/level`.
  - The catch-all is registered last; Flask's URL map gives blueprint routes (e.g. `/legacy/...`, `/api/v1/...`) precedence, so the SPA only catches what nothing else owns.

### Frontend

- **frontend/src/pages/Home.tsx**
  - Added a `Compare with legacy →` button in the action row (alongside Continue Wizard / View Sheet). Renders as `<a href="/legacy/">` because it leaves the React Router scope.

### Templates (legacy)

- **templates/base.html**
  - Brand badge: appended a small `LEGACY` pill to the navbar brand so it's obvious which UI is loaded.
  - Added a `Try the new UI` nav link pointing to `/`. Sits next to the existing Start Over link.

### Tests

- Bulk-prefixed every legacy URL referenced in tests with `/legacy`. 54 substitutions across:
  - `tests/test_edit_flow.py` (40+ paths — `/edit/*`, `/character-summary`, `/api/rebuild-character`, `/api/character-sheet`, `/select-class`, `/submit-class-choices`, `/choose-*`, `/select-languages`, `/submit-ability-scores`, `/assign-ability-scores`)
  - `tests/species/test_species_feat_choices_route.py` (`/species-feat-choices`, `/submit-species-feat-choices`, `/select-species-traits`)
  - `tests/core/test_flask_integration.py` (`/create`, `/select-*`, `/submit-class-choices`, `/character-summary`)
  - `tests/test_api.py` (`/api/choices-to-character` → `/legacy/api/choices-to-character`)
- Updated one redirect-target assertion in `test_edit_without_session_redirects_to_index` from `("/", "http://localhost/")` to `("/legacy/", "http://localhost/legacy/")` because the legacy `index.index` endpoint now lives under `/legacy/`.

### Plan & tracking

- `.copilot-tracking/plans/react-spa-migration-plan.md` — Phase 7 reframed from "Cutover + Cleanup (remove legacy)" to "Cutover + Legacy Quarantine (keep legacy mounted under /legacy)".
- `.copilot-tracking/RESUME.md` — same wording update.

## Validation

- `pytest tests/` → **1882 passed** (full suite, includes Phase 7 changes).
- `cd frontend && npm run build` → green (TypeScript + Vite). Bundle size unchanged from Phase 6 (~420 kB JS, ~29 kB CSS, 44 PWA precache entries).
- Manual contract check: legacy template `url_for()` calls resolve to `/legacy/...` automatically (no template edits needed beyond the navbar additions). The `/api/v1/*` REST surface and the `/api/test/*` SPA-debug surface remain unchanged.

## Routing summary (post-Phase 7)

| Prefix          | Owner           | Notes                                                            |
| --------------- | --------------- | ---------------------------------------------------------------- |
| `/`             | React SPA       | `frontend/dist/index.html` + assets, served by `serve_spa`       |
| `/wizard/*`     | React SPA       | Client-side route, falls back to `index.html`                    |
| `/sheet`, `/sheet/pdf` | React SPA | Client-side                                                      |
| `/api/v1/*`     | Flask blueprint | REST API consumed by SPA                                         |
| `/api/test/*`   | Flask blueprint | SPA debug helpers                                                |
| `/legacy/*`     | Flask Jinja UI  | All 10 legacy blueprints (HTML + their internal `/api/...` ones) |
| `/static/*`     | Flask static    | Legacy CSS/JS/images                                             |

## Known limitations

- Legacy `load_character_bp` mixes HTML routes (`/load-character`) with helper JSON routes (`/api/rebuild-character`, `/api/choices-to-character`, `/api/character-sheet`). Under the prefix these become `/legacy/api/...`, which is awkward but functionally correct — they're internal to the legacy UI. Not worth splitting in this phase.
- The legacy navbar still says "D&D 2024 Character Creator" with only a small `LEGACY` badge. If users miss the badge they may not realize they're in the comparison UI; the badge color (`bg-secondary`) was chosen to be visible without overpowering the brand. Revisit if user feedback indicates confusion.

## Next

- Phase 7 is complete pending user approval.
- Open question for follow-up phases: when (if ever) to retire `/legacy/*` entirely. Suggest revisiting once SPA reaches feature parity and the comparison tool is no longer being actively used.
