<!-- markdownlint-disable-file -->
# RESUME POINTER — React SPA Migration

**Read this file FIRST in any new Copilot session.**

All session state for the React SPA migration lives under `.copilot-tracking/`.
Conversational context is disposable; this folder is the source of truth.

## Current Status (post-devcontainer-rebuild)

- **Active plan:** [.copilot-tracking/plans/react-spa-migration-plan.md](plans/react-spa-migration-plan.md)
- **Phase 0 (devcontainer + frontend scaffold):** COMPLETE — Vite boots on 5173, Flask on 5000, CORS verified.
- **Phase 1 (REST API v1):** COMPLETE — `tests/test_api_v1.py` 22/22 passing.
- **Phase 2 (Flask API Refactor Depth):** COMPLETE — `modules/derived_stats.py` extracted; `POST /api/v1/character/derived` added; 29/29 API tests, 1882/1882 full suite passing.
- **Phase 3 (Frontend Wizard Shell):** COMPLETE — typed API client, Zustand store with cascade invalidation + localStorage, react-router shell, generic step renderer, Basics step working, `npm run typecheck` + `npm run build` green.
- **Phase 4 (Choice Cascades + Effects Display):** COMPLETE — rich pickers for class/species/background/languages, generic `ChoiceList` for nested choices, `EffectsPanel` polling `/character/build`. Typecheck + build green.
- **Phase 4b (Remaining Rich Pickers):** COMPLETE — `AbilitiesStep` (standard-array + point-buy + background ASI), `EquipmentStep` (starting-equipment cart), background skill-replacement picker, origin/species feat pickers via `FeatChoicesPicker`. Typecheck + build green.
- **Phase 5 (Character Sheet View):** COMPLETE — read-only sheet at `/sheet` rendering header / combat / abilities / skills / AC / attacks / proficiencies / languages / spells / features from `/api/v1/character/build`. Typecheck + build green.
- **Phase 4c (Spells / Masteries / Invocations Pickers):** COMPLETE — `ClassAdvancedChoices` panel inside `ClassStep` wires `/character/derived` (spell_management, mastery_management, invocation_management) into pickers writing `spell_selections`, `weapon_mastery_selections`, `eldritch_invocation_selections`; silently hides when 400. Typecheck + build green.
- **Awaiting:** explicit user approval to proceed to Phase 5b (PDF parity) or Phase 6 (PWA + persistence).

## Resume Procedure

1. Read [plans/react-spa-migration-plan.md](plans/react-spa-migration-plan.md) for the 7-phase roadmap and approval gates.
2. Read [changes/phase-0-scaffold.md](changes/phase-0-scaffold.md) for what was scaffolded and what is still pending.
3. Read [changes/phase-1-api.md](changes/phase-1-api.md) for REST API v1 status.
4. Read [changes/phase-2-api-refactor.md](changes/phase-2-api-refactor.md) for derived view-model extraction and `/api/v1/character/derived`.
5. Read [changes/phase-3-wizard-shell.md](changes/phase-3-wizard-shell.md) for the React wizard shell.
6. Read [changes/phase-4-cascades-effects.md](changes/phase-4-cascades-effects.md) for rich pickers + effects panel.
7. Read [changes/phase-4b-remaining-pickers.md](changes/phase-4b-remaining-pickers.md) for abilities/equipment/feat/skill-replacement pickers.
8. Read [changes/phase-5-sheet.md](changes/phase-5-sheet.md) for the read-only character sheet.
9. Read [changes/phase-4c-spells-masteries-invocations.md](changes/phase-4c-spells-masteries-invocations.md) for the spell/mastery/invocation pickers.
10. Verify on-disk reality matches the changes logs by listing `frontend/src/`, `routes/api/`, `modules/derived_stats.py`, and re-reading `.devcontainer/devcontainer.json`.
11. Continue from the **Next Actions** block in whichever phase log is in progress.

## Operating Rules (carry over from prior session)

- Do NOT proceed past a phase boundary without explicit user approval.
- All state goes into `.copilot-tracking/`. Do not rely on chat memory.
- Frontend uses **npm + Node 20** (devcontainer feature), NOT pnpm.
- Flask runs on 5000, Vite on 5173. CORS is enabled for `/api/*` from `localhost:5173` only when `FLASK_ENV=development` or `app.debug`.
- API base path: `/api/v1`. Health check: `GET /api/v1/health`.

## Decisions Locked (do not relitigate)

- Stack: Vite + React + TS + Tailwind + shadcn/ui + Zustand + react-router + react-query + Vite PWA plugin.
- Theming: dark base, red/gold accents, Cinzel display, Inter body.
- Backend: Flask retained as calculation + persistence engine; SPA consumes `/api/v1`.
- Persistence: localStorage interim, forward-compatible with future Postgres + auth.
- Devcontainer: Node 20 feature added, port 5173 forwarded, `npm install` in postCreate.
