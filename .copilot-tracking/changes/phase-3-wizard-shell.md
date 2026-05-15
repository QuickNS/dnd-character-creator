<!-- markdownlint-disable-file -->
# Phase 3 — Frontend Wizard Shell (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 4.

## Related Plan

- [.copilot-tracking/plans/phase-3-wizard-shell-plan.md](../plans/phase-3-wizard-shell-plan.md)

## Summary

Stood up the React SPA wizard shell on top of the Phase 1/2 REST API.
Adding a new wizard step in `routes/api/wizard.py` now propagates to the
sidebar + step renderer with no frontend changes (data-driven).

## Files Added

- `frontend/src/lib/api.ts` — typed fetch client + zod schemas for
  health, wizard (`/steps`, `/dependencies`), character
  (`/build`, `/validate`, `/preview-step`), and catalog
  (`/classes`, `/species`, `/backgrounds`). Exports `ApiError`.
- `frontend/src/lib/queryClient.ts` — shared `QueryClient`
  (60s staleTime, no refetch-on-focus, retry: 1).
- `frontend/src/store/characterStore.ts` — Zustand store with
  `setChoice` / `clearChoice` cascade invalidation driven by
  `/wizard/dependencies`, persisted to localStorage under
  `dnd-creator-character-v1`.
- `frontend/src/app/router.tsx` — `createBrowserRouter` with `/`,
  `/wizard`, `/wizard/:stepId`, `/sheet`, and `*` redirect.
- `frontend/src/app/providers.tsx` — `QueryClientProvider` wrapping
  `RouterProvider`.
- `frontend/src/components/layout/WizardLayout.tsx` — fetches steps +
  dependencies, hydrates the store, redirects `/wizard` → first step,
  renders sidebar + outlet.
- `frontend/src/components/wizard/StepSidebar.tsx` — numbered/checked
  step list driven by `/character/validate` results.
- `frontend/src/components/wizard/StepRenderer.tsx` — dispatches to
  `BasicsStep` for `basics`, `GenericStep` otherwise.
- `frontend/src/components/wizard/StepNav.tsx` — Prev/Next buttons.
- `frontend/src/components/steps/BasicsStep.tsx` — name + level inputs
  wired to `setChoice`.
- `frontend/src/components/steps/GenericStep.tsx` — placeholder that
  surfaces `/character/preview-step` payload as inspectable JSON behind
  a `<details>` (Phase 4 replaces with rich pickers).
- `frontend/src/pages/Home.tsx` — landing page.
- `frontend/src/pages/WizardIndex.tsx` — placeholder while redirecting.
- `frontend/src/pages/WizardStep.tsx` — resolves `:stepId` to a
  `WizardStep` and delegates to `StepRenderer`.
- `frontend/src/pages/Sheet.tsx` — Phase 5 placeholder.

## Files Modified

- `frontend/src/app/App.tsx` — replaced placeholder with `<Providers />`.

## Files Removed

- None.

## Verified

- `npm run typecheck` → clean (no errors).
- `npm run build` → ✓ built in 1.18s; PWA precache 30 entries / ~674 KiB;
  `dist/assets/index-*.js` 335.48 kB (gzip 102.82 kB).
- Backend regression untouched (no Python changes this phase).

## Pending / Next Actions

- Present Phase 3 for user approval.
- Phase 4 — Choice Cascades + Effects Display — requires explicit
  approval. Will replace `GenericStep` with rich per-step pickers
  (class cards, species selector with lineages, background skill
  resolution, ability score point-buy, equipment cart) and surface
  computed effects from `/character/build`.

## Suggested Commit Message

```text
feat(frontend): Phase 3 — wizard shell driven by /api/v1

- Add typed API client (src/lib/api.ts) with zod-validated responses
  for wizard/, character/, catalog/, and health endpoints.
- Add Zustand store (src/store/characterStore.ts) with cascade
  invalidation driven by /api/v1/wizard/dependencies and localStorage
  persistence under dnd-creator-character-v1.
- Add react-router routes (/, /wizard, /wizard/:stepId, /sheet) inside
  a QueryClientProvider; WizardLayout hydrates the store and renders
  the step sidebar with /character/validate-driven completion ticks.
- Add generic StepRenderer + a working Basics step; other steps render
  /character/preview-step payloads pending Phase 4 rich UI.
- Verified: npm run typecheck clean, npm run build clean (335 kB JS
  gzip 102 kB, PWA precache 30 entries).
```
