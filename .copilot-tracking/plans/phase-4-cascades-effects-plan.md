<!-- markdownlint-disable-file -->
# Phase 4 — Choice Cascades + Effects Display (Plan)

**Status:** IN PROGRESS — user approved option 1 from Phase 3 menu.

## Objective

Replace `GenericStep` placeholders for the four "selection-driven" steps
(class, species, background, languages) with rich pickers, add a generic
`ChoiceList` component for nested choices (skill picks, fighting style,
trait choices), and surface live computed effects from
`POST /api/v1/character/build` in an `EffectsPanel` mounted on every
step.

The Zustand store's cascade invalidation (added in Phase 3) does the
hard work; this phase exercises it via real UI.

## In Scope

- `EffectsPanel` (sticky side panel) — live HP/AC/proficiency
  bonus/speed/granted features from `/character/build`
- Generic `ChoiceList` component — handles `{title, options, count}`
  shape for skills, fighting style, trait choices, etc.
- `ClassStep` — class grid → subclass picker (when `needs_subclass`) →
  per-class skill choice + nested choices via `ChoiceList`
- `SpeciesStep` — species grid → lineage radio (when applicable) →
  trait choices
- `BackgroundStep` — background grid + skill-replacement notice
- `LanguagesStep` — multi-select from `available_languages`

## Out of Scope (deferred)

- Abilities point-buy / standard array UI (own phase — complex)
- Equipment cart UI (own phase — complex)
- Spell selection / cantrips (Phase 4b — depends on subclass choice)
- Origin feat picker (Phase 4b)
- Character sheet view (Phase 5)

These steps continue to use `GenericStep` for now.

## Files to Add

- `frontend/src/components/wizard/EffectsPanel.tsx`
- `frontend/src/components/wizard/ChoiceList.tsx`
- `frontend/src/components/steps/ClassStep.tsx`
- `frontend/src/components/steps/SpeciesStep.tsx`
- `frontend/src/components/steps/BackgroundStep.tsx`
- `frontend/src/components/steps/LanguagesStep.tsx`

## Files to Modify

- `frontend/src/components/wizard/StepRenderer.tsx` — dispatch new
  step components, mount `EffectsPanel`
- `frontend/src/lib/api.ts` — add `api.character.build` zod loosening
  if needed (already permissive; confirm)

## Validation

- `npm run typecheck` clean
- `npm run build` clean
- Backend regression untouched (no Python changes)

## Approval Gate

Present Phase 4 for approval before Phase 4b (spell/cantrip/feat
pickers) or Phase 5 (sheet view).
