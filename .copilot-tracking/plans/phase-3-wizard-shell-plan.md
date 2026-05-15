<!-- markdownlint-disable-file -->
# Phase 3 — Frontend Wizard Shell (Plan)

**Status:** IN PROGRESS — user approved option 1 from Phase 5 menu.

## Objective

Stand up the React SPA wizard shell driven by `/api/v1/wizard/*` and
`/api/v1/character/*` endpoints. No deep per-step UX yet — that lands in
Phase 4. Goal is: typed API client, react-query data plumbing, Zustand
store with cascade invalidation + localStorage persistence, react-router
routes, shadcn-style layout, and a generic `StepRenderer` that consumes
`/wizard/steps` + `/character/preview-step` + `/character/validate`.

## Scope

In scope:

- Typed API client (`src/lib/api.ts`) + zod schemas for wizard contract
- `QueryClientProvider` wiring (`src/lib/queryClient.ts`)
- Zustand store with `setChoice(key, value)` that cascades invalidation
  using `/wizard/dependencies` and persists to localStorage
- React Router routes: `/`, `/wizard`, `/wizard/:stepId`, `/sheet`
- Wizard layout with step sidebar, breadcrumb, prev/next nav
- Generic `StepRenderer` that renders any step from server metadata
- Minimal but functional Basics step (name + level inputs)
- Other steps render preview-step JSON behind a `<details>` for now
- Build + dev-boot verification

Out of scope (deferred to Phase 4 / 5):

- Per-step rich pickers (class cards, species portraits, ability score
  point-buy UI, equipment cart)
- Choice cascade rich UI (rendered as plain selects in this phase)
- Character sheet view (Phase 5)

## Files to Add

- `frontend/src/lib/api.ts` — fetch wrappers + zod types
- `frontend/src/lib/queryClient.ts` — QueryClient instance
- `frontend/src/store/characterStore.ts` — Zustand store
- `frontend/src/app/router.tsx` — RouterProvider
- `frontend/src/app/providers.tsx` — QueryClientProvider + Router
- `frontend/src/components/layout/WizardLayout.tsx`
- `frontend/src/components/wizard/StepRenderer.tsx`
- `frontend/src/components/wizard/StepSidebar.tsx`
- `frontend/src/components/wizard/StepNav.tsx`
- `frontend/src/pages/Home.tsx`
- `frontend/src/pages/WizardIndex.tsx`
- `frontend/src/pages/WizardStep.tsx`
- `frontend/src/pages/Sheet.tsx`
- `frontend/src/components/steps/BasicsStep.tsx`
- `frontend/src/components/steps/GenericStep.tsx`

## Files to Modify

- `frontend/src/app/App.tsx` — replace placeholder with `<Providers />`
- `frontend/src/main.tsx` — no change expected

## Validation

- `npm run typecheck` clean
- `npm run build` clean
- `npm run dev` boots; browsing `/wizard/basics` renders shell;
  manually filling Basics persists across reload (localStorage).

## Dependencies

All required deps already present in `frontend/package.json` (verified):
react-router-dom, @tanstack/react-query, zustand, zod, @radix-ui/*,
class-variance-authority, clsx, tailwind-merge.

## Approval Gate

After Phase 3 completes, present for approval before Phase 4 (Choice
Cascades + Effects Display).
