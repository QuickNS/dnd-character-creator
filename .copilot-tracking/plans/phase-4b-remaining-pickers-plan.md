<!-- markdownlint-disable-file -->
# Phase 4b — Remaining Rich Pickers (Plan)

**Status:** IN PROGRESS — user approved option 1 from Phase 4 menu.

## Objective

Close out the `GenericStep` placeholders left after Phase 4 with rich
pickers for abilities, equipment, background skill replacement, and
origin/species feats. Spells/cantrips deferred to Phase 4c (depends on
class-spell-list integration not yet wired into the wizard).

## In Scope

- **`AbilitiesStep`**: standard-array vs point-buy toggle, per-ability
  inputs with live point-buy budget validation, background ASI
  (`background_bonuses`) sub-picker with suggested defaults.
- **`EquipmentStep`**: simple cart from `class_equipment` +
  `background_equipment` returned by `/character/preview-step`.
- **Background skill replacement picker**: extend `BackgroundStep`
  with a `ChoiceList` driven by `skill_replacement.options` /
  `.needed`.
- **Origin feat picker**: extend `BackgroundStep` to render
  `origin_feat_choices` (background's feat).
- **Species feat picker**: extend `SpeciesStep` to render
  `species_feat_choices`.

## Out of Scope (Phase 4c / Phase 5)

- Spells / cantrips picker (Phase 4c — needs `/catalog/spells/<class>`
  wired into preview-step or a new wizard endpoint).
- Maneuver picker (Phase 4c).
- Eldritch invocation picker (Phase 4c).
- Character sheet view (Phase 5).

## Files to Add

- `frontend/src/components/steps/AbilitiesStep.tsx`
- `frontend/src/components/steps/EquipmentStep.tsx`
- `frontend/src/components/wizard/FeatChoicesPicker.tsx` — generic
  renderer for the `{feat_name, feat_description, feat_benefits,
  choices: [{title, options, count, choices_made_key}]}` shape used by
  both origin and species feats.

## Files to Modify

- `frontend/src/components/wizard/StepRenderer.tsx` — dispatch to new
  steps.
- `frontend/src/components/steps/BackgroundStep.tsx` — render skill
  replacement `ChoiceList` + origin feat picker.
- `frontend/src/components/steps/SpeciesStep.tsx` — render species
  feat picker.

## Validation

- `npm run typecheck` clean.
- `npm run build` clean.
- No backend changes; pytest regression unaffected.

## Approval Gate

Present Phase 4b for approval before Phase 4c (spells/maneuvers/
invocations) or Phase 5 (sheet view).
