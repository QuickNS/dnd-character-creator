<!-- markdownlint-disable-file -->
# React SPA Migration Plan

**Status:** Approved by user ("approve all defaults"). Implementation underway.
**Approval gate rule:** Do NOT proceed past a phase boundary without explicit user approval.

## Goal

Revamp the D&D 2024 Character Creator as a modern React SPA while retaining the
existing Flask backend as a calculation and persistence API. Update the
devcontainer to support the revised tech stack.

## Locked Defaults

- **Frontend:** Vite + React 18 + TypeScript + Tailwind + shadcn/ui + Zustand + react-router-dom + @tanstack/react-query + vite-plugin-pwa
- **Backend:** Flask retained; new `/api/v1` REST surface; legacy Jinja routes left in place during migration
- **Theming:** dark base, red/gold accents, Cinzel display font, Inter body font
- **Persistence:** localStorage interim, forward-compatible with Postgres + auth later
- **Devcontainer:** add Node 20 feature, forward port 5173, `npm install` in postCreate
- **API base:** `/api/v1`; CORS enabled for `localhost:5173` in dev only

## Phases

### Phase 0 — Devcontainer + Frontend Scaffold (COMPLETE, awaiting approval)

- [x] Edit `.devcontainer/devcontainer.json` (Node 20 feature, port 5173, postCreate)
- [x] Scaffold `frontend/` (Vite + React + TS + Tailwind + PWA configs)
- [x] Rebuild devcontainer
- [x] Run `npm install` in `frontend/` inside container
- [x] Verify Vite dev server boots on 5173
- [x] Verify CORS handshake to Flask on 5000 (`Access-Control-Allow-Origin: http://localhost:5173`)
- [ ] Present Phase 0 for approval

### Phase 1 — REST API v1 (COMPLETE, awaiting approval)

- [x] Design `/api/v1` contract (catalog, character, wizard)
- [x] Create `routes/api/__init__.py` + register under `/api/v1`
- [x] Implement `routes/api/catalog.py` (species/classes/spells/items)
- [x] Implement `routes/api/character.py` (calculate/persist stubs)
- [x] Implement `routes/api/wizard.py` (schema + dependency graph)
- [x] Wire blueprints + CORS into `app.py`
- [x] Verify syntax via `py_compile`
- [x] Author pytest API tests (`tests/test_api_v1.py`, 22 tests)
- [x] Run tests inside devcontainer (22 passed in 0.29s)
- [ ] Document concrete response shapes (deferred — covered by tests)
- [ ] Present Phase 1 for approval

### Phase 2 — Flask API Refactor Depth (COMPLETE, awaiting approval)

Extract calculation logic from Jinja-coupled routes into pure functions exposed via `/api/v1`. Do not modify `CharacterBuilder` internals.

- [x] Extract pure helpers from `routes/character_summary.py` into `modules/derived_stats.py`
- [x] Refactor session-coupled spell/mastery/invocation read endpoints to delegate
- [x] Add stateless `POST /api/v1/character/derived` (4 view types)
- [x] Add 7 tests in `tests/test_api_v1.py` (29 passing total)
- [x] Verify full regression (`pytest tests/` → 1882 passed)
- [ ] Present Phase 2 for approval

### Phase 3 — Frontend Wizard Shell (COMPLETE, awaiting approval)

- [x] Typed API client + zod schemas (`src/lib/api.ts`)
- [x] QueryClient + provider wiring (`src/lib/queryClient.ts`, `src/app/providers.tsx`)
- [x] Zustand store with cascade invalidation + localStorage (`src/store/characterStore.ts`)
- [x] React Router routes `/`, `/wizard`, `/wizard/:stepId`, `/sheet`
- [x] WizardLayout with step sidebar driven by `/wizard/steps` + `/character/validate`
- [x] Generic `StepRenderer` + working `BasicsStep` + `GenericStep` placeholder
- [x] `npm run typecheck` + `npm run build` clean
- [ ] Present Phase 3 for approval

### Phase 4 — Choice Cascades + Effects Display (COMPLETE, awaiting approval)

- [x] `EffectsPanel` polling `POST /api/v1/character/build` (HP/AC/PB/speed/init/abilities/features)
- [x] Generic `ChoiceList` for `{title, options, count}` nested choices
- [x] `ClassStep`: class grid + conditional subclass picker + nested choices
- [x] `SpeciesStep`: species grid + lineage picker + trait choices
- [x] `BackgroundStep`: background grid + skill-overlap notice
- [x] `LanguagesStep`: base chips + bonus-language multi-toggle
- [x] `StepRenderer` 2-col layout with per-step dispatch + sticky `EffectsPanel`
- [x] `npm run typecheck` + `npm run build` clean
- [ ] Present Phase 4 for approval

**Deferred to Phase 4b** (still on `GenericStep`): abilities point-buy, equipment cart, spell/cantrip picker, origin/species feat picker, background skill replacement picker.

### Phase 4b — Remaining Rich Pickers (COMPLETE, awaiting approval)

- [x] `AbilitiesStep`: standard-array vs point-buy with live 27-point validation
- [x] Background ASI sub-picker with `Use suggested` shortcut
- [x] `EquipmentStep`: cart from class + background `starting_equipment`
- [x] Background skill-replacement `ChoiceList`
- [x] `FeatChoicesPicker` reused for origin + species feats
- [x] `npm run typecheck` + `npm run build` clean
- [ ] Present Phase 4b for approval

**Deferred to Phase 4c**: spells/cantrips picker, maneuver picker, eldritch invocation picker.

### Phase 5 — Character Sheet View + PDF Parity (COMPLETE)

- [x] `Sheet.tsx` reads `/api/v1/character/build` and renders header / combat / abilities / skills / AC / attacks / proficiencies / languages / spells / features
- [x] Friendly fallback while wizard is incomplete
- [x] `npm run typecheck` + `npm run build` clean
- [x] PDF parity (background-image overlay, desktop-only gating) — shipped in Phase 5b
- [ ] Present Phase 5 for approval

### Phase 5b — Printable PDF-Parity Sheet (COMPLETE, awaiting approval)

- [x] `/sheet/pdf` renders 8.5×11in canvas with `sheet1.png`/`sheet2.png` background and read-only overlay fields
- [x] Weapons + damage cantrips wired through `/api/v1/character/derived?view=damage_cantrips`
- [x] Desktop-only gate (<900px viewport shows friendly message)
- [x] `window.print()` toolbar; print stylesheet matches legacy template
- [x] Sheet PNGs copied to `frontend/public/pdf_template/`; excluded from PWA precache via `workbox.globIgnores`
- [x] `npm run typecheck` + `npm run build` clean
- [ ] Present Phase 5b for approval

### Phase 6 — PWA + Persistence (COMPLETE, awaiting approval)

- [x] `PersistenceAdapter` interface + `LocalStoragePersistence` impl with versioned migration shim (`frontend/src/lib/persistence.ts`)
- [x] `rosterStore` (Zustand) wrapping the adapter (`frontend/src/store/rosterStore.ts`)
- [x] Character store bumped to `version: 1` with defensive `migrate`
- [x] `UpdatePrompt` using `virtual:pwa-register/react` — reload + offline-ready toasts, hourly update check
- [x] `OfflineIndicator` pill driven by `navigator.onLine`
- [x] Home page "Saved Characters" section: save current, list, load, delete
- [x] `npm run typecheck` + `npm run build` clean
- [ ] Present Phase 6 for approval

### Phase 7 — Cutover + Legacy Quarantine (IN PROGRESS)

Serve the built React bundle from Flask at `/`, mount the existing
Jinja UI under `/legacy/*` so it remains available as a side-by-side
comparison tool, and tighten CORS to production posture.
**Do NOT remove the legacy routes** — they share the same
`CharacterBuilder` + session, which is exactly what makes the
comparison useful.

- [ ] Re-register all legacy blueprints (`index`, `load_character`,
      `starter_characters`, `character_creation`, `background`,
      `species`, `languages`, `ability_scores`, `equipment`,
      `character_summary`) with `url_prefix="/legacy"`. The API
      (`/api/v1`) and test API (`/api/test`) blueprints stay put.
- [ ] Add a Flask catch-all that serves `frontend/dist/index.html` for
      any unmatched path (and `dist/<asset>` for built assets), so the
      SPA owns `/`, `/wizard*`, `/sheet*`, etc. in production.
- [ ] Add cross-links: "Try the new UI →" in the legacy navbar,
      "Compare with legacy →" on the SPA Home page.
- [ ] Tighten CORS: keep the dev-only `localhost:5173` allowance
      gated by `FLASK_ENV=development`; no change needed once SPA is
      same-origin.
- [ ] Update tests that hit hardcoded legacy URLs to use the
      `/legacy/...` prefix.
- [ ] Run pytest regression + frontend `npm run build`.
- [ ] Present Phase 7 for approval.

The legacy site stays mounted indefinitely as a comparison surface;
removing it is deferred to a future phase only when explicitly
requested.

## Approval Gates

After each phase: present completed work + validation results, then wait for explicit user approval before starting the next phase.
