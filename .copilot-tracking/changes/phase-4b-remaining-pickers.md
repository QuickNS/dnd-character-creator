<!-- markdownlint-disable-file -->
# Phase 4b — Remaining Rich Pickers (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 4c (spells/maneuvers/invocations) or Phase 5 (sheet view).

## Related Plan

- [.copilot-tracking/plans/phase-4b-remaining-pickers-plan.md](../plans/phase-4b-remaining-pickers-plan.md)

## Summary

Closed the remaining `GenericStep` placeholders for **abilities** and
**equipment**, and extended the existing **background** and **species**
steps with skill-replacement and feat-choice pickers backed by the
preview-step API. Spells/cantrips deferred to Phase 4c.

## Files Added

- `frontend/src/components/steps/AbilitiesStep.tsx` — standard-array vs
  point-buy toggle; per-ability inputs validated against the canonical
  D&D 2024 point-buy table (matches `modules/ability_scores.POINT_BUY_COSTS`,
  27-point budget, scores 8–15); inline budget readout; embedded
  `BackgroundAsiPicker` with `Use suggested` shortcut.
- `frontend/src/components/steps/EquipmentStep.tsx` — renders class +
  background `starting_equipment` from `/character/preview-step`;
  detects `[{ label, items }]` choice groups and renders them as
  pick-one cards under `choices_made.equipment_selections.<slot>`;
  plain string lists / strings rendered informationally; unknown
  shapes surfaced via collapsible JSON.
- `frontend/src/components/wizard/FeatChoicesPicker.tsx` — generic
  renderer for the
  `{feat_name, feat_description, feat_benefits, choices: [...]}` shape;
  delegates each choice to `ChoiceList` keyed by `choices_made_key`
  (e.g. `feat_Skilled_skills_or_tools`).

## Files Modified

- `frontend/src/components/steps/BackgroundStep.tsx` — replaced
  informational skill-overlap notice with a real `ChoiceList` (driven
  by `skill_replacement.options` / `.needed`); appended
  `FeatChoicesPicker` for the background's origin feat
  (`origin_feat_choices`).
- `frontend/src/components/steps/SpeciesStep.tsx` — appended
  `FeatChoicesPicker` for `species_feat_choices` (e.g. Human → Skilled).
- `frontend/src/components/wizard/StepRenderer.tsx` — added
  `abilities` → `AbilitiesStep` and `equipment` → `EquipmentStep`
  cases. `complete` (Summary) still falls back to `GenericStep`,
  which is the right behavior until Phase 5.

## Files Removed

- None.

## Verified

- `npm run typecheck` → clean.
- `npm run build` → ✓ built in 1.10s; 358.10 kB JS / 107.87 kB gzip;
  PWA precache 30 entries / 698.74 KiB.
- No backend changes; pytest regression unaffected.

## Pending / Next Actions

- Present Phase 4b for user approval.
- **Phase 4c** (next logical scope): spell list / cantrip / maneuver /
  invocation pickers. Requires either extending
  `/character/preview-step` for `class` to surface spell choices, or
  adding a dedicated `/character/spell-options` endpoint backed by
  `builder.get_class_features_and_choices()` + `/catalog/spells/<class>`.
- **Phase 5**: character sheet view backed by `/character/build`.

## Suggested Commit Message

```text
feat(frontend): Phase 4b — abilities, equipment, feat & skill-replacement pickers

- AbilitiesStep: standard-array vs point-buy toggle with live budget
  validation against the canonical 27-point D&D 2024 table; embedded
  background ASI picker with `Use suggested` shortcut.
- EquipmentStep: cart from class + background starting_equipment via
  /character/preview-step; supports `[{label, items}]` choice groups,
  string lists, and unknown shapes.
- FeatChoicesPicker: generic renderer for builder.get_feat_choices()
  shape; reused for both origin (background) and species feats via
  ChoiceList keyed by choices_made_key.
- BackgroundStep: real skill-replacement ChoiceList + origin feat
  picker.
- SpeciesStep: species feat picker.
- StepRenderer dispatches abilities/equipment to the new steps.
- Verified: npm run typecheck clean, npm run build clean (358 kB JS
  gzip 108 kB, PWA precache 30 entries).
```
