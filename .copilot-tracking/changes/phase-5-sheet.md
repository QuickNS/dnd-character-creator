<!-- markdownlint-disable-file -->
# Phase 5 — Character Sheet View (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 4c (spells/maneuvers/invocations) or Phase 6 (PWA + persistence).

## Summary

Replaced the `Sheet.tsx` placeholder with a full read-only character
sheet rendered from `POST /api/v1/character/build`. Validates the
end-to-end pickers → builder → display loop. No backend changes.

## Files Modified

- `frontend/src/pages/Sheet.tsx` — full sheet:
  - Header (name, class/subclass, species/lineage, background, alignment)
  - Combat (HP, init, speed, passive perception, proficiency bonus, hit dice)
  - Abilities grid (score + modifier; reads `c.abilities[name]` then falls back to `c.ability_scores[name]`)
  - Skills (proficient indicator + signed bonus)
  - AC options (top option highlighted)
  - Attacks (name, attack bonus, damage)
  - Proficiencies (armor / weapons / tools)
  - Languages
  - Spells (grouped by level, slot summary)
  - Features (grouped by category from `c.features`)
  - Friendly fallback when `/character/build` errors mid-wizard

## Files Added

- None.

## Verified

- `npm run typecheck` clean.
- `npm run build` clean (~363 kB JS / ~108 kB gzip; PWA precache 30
  entries / 707 KiB).
- No backend changes; pytest regression unaffected.

## Pending / Next Actions

- Present Phase 5 for user approval.
- **Phase 4c**: spells/cantrips/maneuvers/invocations pickers.
- **Phase 6**: PWA + persistence story (offline assets, localStorage
  → Postgres migration shim).

## Suggested Commit Message

```text
feat(frontend): Phase 5 — read-only character sheet from /character/build

- Replace Sheet.tsx placeholder with full read-only sheet reading
  /api/v1/character/build output: header, combat, abilities, skills,
  AC options, attacks, proficiencies, languages, spells, features.
- Loose typing at the boundary (to_character() is too sprawling to
  fully type) with narrow helpers for safe field reads.
- Friendly mid-wizard fallback when build errors.
- Verified: npm run typecheck clean, npm run build clean.
```
