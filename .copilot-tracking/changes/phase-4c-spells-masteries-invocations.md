<!-- markdownlint-disable-file -->
# Phase 4c — Spells / Masteries / Invocations Pickers (Changes Log)

**Status:** COMPLETE — awaiting user approval.

## Summary

Added the three remaining nested-class pickers as a single
`ClassAdvancedChoices` panel mounted inside `ClassStep`. Pure frontend
work — backend `/api/v1/character/derived` already exposed the
`spell_management`, `mastery_management`, and `invocation_management`
view-models; this phase just wires them into the wizard.

Each sub-picker silently hides itself when the derived view returns
HTTP 400 ("not applicable to this build"), so a Fighter sees only
weapon masteries, a Wizard sees only spells, and a Warlock sees both
spells and invocations — all without hardcoded class lists.

## Files Modified

- `frontend/src/lib/api.ts` — added `api.character.derived(choices_made, view)`.
- `frontend/src/components/steps/ClassStep.tsx` — mount `ClassAdvancedChoices` after `ClassDetail`.

## Files Added

- `frontend/src/components/wizard/ClassAdvancedChoices.tsx` —
  - `SpellPicker` writes `spell_selections` (`{cantrips, spells, background_cantrips, background_spells}`); enforces caps from `data.limits.{cantrips,spells}` and from `data.background_requirements.{cantrips,spells}.count`.
  - `MasteryPicker` writes `weapon_mastery_selections` (`string[]`); enforces `max_masteries`; shows mastery name beside each weapon.
  - `InvocationPicker` writes `eldritch_invocation_selections` (`string[]`); enforces `max_invocations`; shows description.
  - All three use `ApiError.status === 400` to hide gracefully when not applicable.

## Verified

- `npm run typecheck` clean.
- `npm run build` clean (~370 kB JS / ~111 kB gzip; PWA precache 30 entries / 714 KiB).
- No backend changes; pytest regression unaffected.

## Pending / Next Actions

- Present Phase 4c for approval.
- Remaining migration: Phase 5b (PDF parity), Phase 6 (PWA + persistence), Phase 7 (cutover).

## Suggested Commit Message

```text
feat(frontend): Phase 4c — spells / masteries / invocations pickers

- Add api.character.derived(choices, view) wrapping POST /character/derived.
- ClassAdvancedChoices fetches spell_management, mastery_management,
  invocation_management; silently hides each when 400 (not applicable).
- SpellPicker writes spell_selections {cantrips, spells,
  background_cantrips, background_spells} with cap enforcement and
  background-spell sub-picker.
- MasteryPicker writes weapon_mastery_selections (string[]) capped by
  max_masteries, displaying mastery property beside each weapon.
- InvocationPicker writes eldritch_invocation_selections (string[])
  capped by max_invocations, with description.
- Mount inside ClassStep after the existing ClassDetail block.
- Verified: npm run typecheck clean, npm run build clean.
```
