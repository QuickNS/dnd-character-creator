<!-- markdownlint-disable-file -->
# Phase 2 — Flask API Refactor Depth (Changes Log)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 3.

## Related Plan

- [.copilot-tracking/plans/phase-2-api-refactor-plan.md](../plans/phase-2-api-refactor-plan.md)

## Summary

Extracted pure calculation / view-model logic from `routes/character_summary.py`
into `modules/derived_stats.py`, then exposed the same view-models as a single
stateless endpoint at `POST /api/v1/character/derived` for the React SPA.
`CharacterBuilder` internals were not modified.

## Files Added

- `modules/derived_stats.py` — pure view-model functions:
  - `scale_cantrip_damage(base_dice, level)`
  - `build_damage_cantrip_rows(character_data)`
  - `build_spell_management_view(builder)`
  - `build_mastery_management_view(builder)`
  - `build_invocation_management_view(builder)`
  Plus shared `ORDINAL_TO_INT` mapping. No Flask / session imports.

## Files Modified

- `routes/character_summary.py`
  - Removed inline `_scale_cantrip_damage` and `_build_damage_cantrip_rows`; re-exported the latter as a backward-compat alias to the new module function.
  - `api_spell_management_data`, `api_mastery_management_data`, `api_invocation_management_data` now delegate to `build_*_management_view`. Endpoints retain identical JSON output and 400/500 semantics.
  - Net delta: -340 lines of route logic, behavior preserved.
- `routes/api/character.py`
  - Added `POST /api/v1/character/derived`. Body: `{choices_made, view}` where view ∈ `{damage_cantrips, spell_management, mastery_management, invocation_management}`. Returns `{view, data}`. 400 on missing body, unknown view, or unmet prereq (e.g. invocations on a non-Warlock).
- `tests/test_api_v1.py`
  - Added `TestCharacterDerived` (7 tests): missing body, unknown view, damage-cantrip shape, spell-management for cleric, spell-management 400 on non-caster, mastery-management for fighter, invocation-management 400 on non-warlock.

## Files Removed

- None.

## Verified

- `python -m pytest tests/test_api_v1.py` → **29 passed in 0.39s** (was 22).
- `python -m pytest tests/` → **1882 passed in 2.98s** (full regression green).
- No edits to `modules/character_builder.py` (constraint honored).

## Pending / Next Actions

- Present Phase 2 for user approval.
- Phase 3 — Frontend Wizard Shell — requires explicit approval.

## Open Questions (deferred to Phase 6)

- POST persistence endpoints (`/api/v1/character/save-spell-selections`, `/api/v1/character/save-mastery-selections`, `/api/v1/character/save-invocation-selections`) intentionally NOT added in Phase 2; they will be designed alongside the localStorage→Postgres persistence story in Phase 6.

## Suggested Commit Message

```text
feat(api): Phase 2 — extract derived view-models, add /api/v1/character/derived

- Add modules/derived_stats.py with pure view-model functions for damage
  cantrips, spell management, mastery management, eldritch invocations.
- Refactor routes/character_summary.py to delegate to derived_stats; behavior
  preserved, ~340 lines of inline logic removed.
- Add POST /api/v1/character/derived returning the same view-models from a
  stateless choices_made payload (for the React SPA).
- Add 7 tests in tests/test_api_v1.py (29 passing; 1882 total green).
```
