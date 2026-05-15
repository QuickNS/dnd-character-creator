<!-- markdownlint-disable-file -->
# Phase 4 — Choice Cascades + Effects Display (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 4b / Phase 5.

## Related Plan

- [.copilot-tracking/plans/phase-4-cascades-effects-plan.md](../plans/phase-4-cascades-effects-plan.md)

## Summary

Replaced `GenericStep` placeholders for **class**, **species**,
**background**, and **languages** with rich pickers backed by
`/api/v1/catalog/*` and `/api/v1/character/preview-step`. Added a
generic `ChoiceList` for nested choices (skill picks, fighting style,
species traits) and an `EffectsPanel` that polls
`POST /api/v1/character/build` and surfaces HP / AC / proficiency
bonus / speed / initiative / abilities / features in a sticky right
rail on every step.

The Phase 3 Zustand store's cascade invalidation now drives real UI:
changing class clears subclass + skill picks; changing species clears
lineage + trait choices.

## Files Added

- `frontend/src/components/wizard/EffectsPanel.tsx` — sticky panel
  posting `choices_made` to `/character/build`; renders core combat
  stats, abilities, and feature list. Treats build errors mid-wizard
  as a friendly hint, not a hard failure.
- `frontend/src/components/wizard/ChoiceList.tsx` — generic
  single/multi-select renderer for `{title, options, count}` shapes;
  caps multi-select at `count`, normalizes `string | {id|name|label,
  description}` option shapes.
- `frontend/src/components/steps/ClassStep.tsx` — class card grid →
  conditional subclass picker (when preview-step reports
  `needs_subclass`) → nested-choice list.
- `frontend/src/components/steps/SpeciesStep.tsx` — species card grid →
  lineage radio (when present) → trait-choice list.
- `frontend/src/components/steps/BackgroundStep.tsx` — background card
  grid + skill-overlap notice (full replacement picker deferred to
  Phase 4b).
- `frontend/src/components/steps/LanguagesStep.tsx` — base-language
  chips + multi-toggle for `available_languages`.

## Files Modified

- `frontend/src/components/wizard/StepRenderer.tsx` — switched from
  `if (basics) else generic` to a per-step dispatch covering basics,
  class, species, background, languages, and falling back to
  `GenericStep` for abilities/equipment/complete. Layout now a
  two-column grid with `EffectsPanel` in a sticky right rail.

## Files Removed

- None.

## Verified

- `npm run typecheck` → clean.
- `npm run build` → ✓ built in 1.05s; 349.48 kB JS / 105.80 kB gzip;
  PWA precache 30 entries / 690 KiB.
- No backend changes; pytest regression unaffected.

## Pending / Next Actions

- Present Phase 4 for user approval.
- **Phase 4b** (next logical scope): rich pickers for the steps that
  still use `GenericStep`:
  - Abilities: standard array / point-buy with background ASI
  - Equipment: starting-equipment cart from class + background
  - Spells / cantrips picker (dependent on class + level)
  - Origin feat + species feat picker
  - Background skill replacement picker
- **Phase 5**: character sheet view backed by `/character/build`.

## Suggested Commit Message

```text
feat(frontend): Phase 4 — rich pickers + live effects panel

- Add EffectsPanel: sticky right-rail that POSTs choices_made to
  /api/v1/character/build and surfaces HP/AC/PB/speed/init/abilities
  /features. Mid-wizard build failures rendered as a friendly hint.
- Add generic ChoiceList for {title, options, count} shapes (handles
  string | {id|name|label, description} options, caps multi-selects).
- Replace GenericStep for class/species/background/languages with rich
  pickers driven by /api/v1/catalog/* and /character/preview-step:
  - Class step: card grid + conditional subclass picker + nested choices.
  - Species step: card grid + lineage selector + trait choices.
  - Background step: card grid + skill-overlap notice.
  - Languages step: base chips + bonus multi-toggle.
- StepRenderer becomes a 2-col layout with per-step dispatch.
- Verified: npm run typecheck clean, npm run build clean (349 kB JS
  gzip 106 kB, PWA precache 30 entries).
```
