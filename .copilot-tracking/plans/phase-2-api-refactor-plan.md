<!-- markdownlint-disable-file -->
# Phase 2 — Flask API Refactor Depth (Plan)

**Status:** COMPLETE — awaiting user approval to proceed to Phase 3.
**Approval to proceed:** Granted by user (selected option 1 to start Phase 2).
**Constraint:** Do NOT modify `CharacterBuilder` internals. Only refactor route-side code and add `/api/v1` endpoints.

## User Requests

- "1" — Approve Phases 0+1 → start Phase 2 (Flask API Refactor Depth).

## Objective

Move pure calculation / view-model logic out of Jinja-coupled routes into testable modules, and expose stateless equivalents under `/api/v1` so the React SPA can fetch the same derived data without depending on the Flask session.

## Scope (locked)

In scope:

- `routes/character_summary.py` — extract pure helpers (`_scale_cantrip_damage`, `_build_damage_cantrip_rows`) into a new module.
- Spell management view-model (currently mixed with session + file I/O) — derive a stateless function on a `CharacterBuilder` instance.
- Mastery management view-model — same pattern.
- Eldritch Invocation management view-model — same pattern.
- New `/api/v1/character/derived` endpoint accepting `{choices_made, view}` and returning the requested derived view.
- Tests in `tests/test_api_v1.py`.

Out of scope (deferred):

- POST persistence endpoints (spell/mastery/invocation save) — those mutate session state; deferred to Phase 6 (PWA + Persistence).
- Changes to `modules/character_builder.py` internals.
- Touching legacy Jinja routes other than to import the extracted helpers.

## Implementation Checklist

<!-- parallelizable: false -->

- [x] **Step 1 — Create `modules/derived_stats.py`** with pure functions:
  - `scale_cantrip_damage(base_dice: str, level: int) -> str`
  - `build_damage_cantrip_rows(character_data: dict) -> list[dict]`
  - `build_spell_management_view(builder) -> dict` (no session, no save)
  - `build_mastery_management_view(builder) -> dict`
  - `build_invocation_management_view(builder) -> dict`
- [x] **Step 2 — Refactor `routes/character_summary.py`** to import from `modules/derived_stats.py`. Remove the now-duplicated private helpers. Read endpoints continue to use the session.
- [x] **Step 3 — Add `/api/v1/character/derived`** in `routes/api/character.py`. Accepts `{choices_made, view}` where `view ∈ {"damage_cantrips","spell_management","mastery_management","invocation_management"}`. Returns the corresponding view dict.
- [x] **Step 4 — Tests** in `tests/test_api_v1.py`:
  - 400 on missing body / unknown view.
  - `damage_cantrips` happy path on a level-1 spellcaster character.
  - `spell_management` returns expected keys for a Wizard.
  - `mastery_management` returns expected keys for a Fighter.
  - `invocation_management` 400/empty for a non-Warlock; expected keys for a Warlock.
- [x] **Step 5 — Validate**: `pytest tests/test_api_v1.py` (29 passed), `pytest tests/` (1882 passed), `py_compile` on touched files.
- [x] **Step 6 — Update tracking artifacts**: mark plan complete, write `changes/phase-2-api-refactor.md`, update `RESUME.md`.

## Dependencies

- Existing `CharacterBuilder` API (`apply_choices`, `to_character`, `calculate_spellcasting_stats`, `calculate_weapon_mastery_stats`, `calculate_eldritch_invocation_stats`, `_load_spell_definition`).
- `data/spells/class_lists/<class>.json` for background spell list resolution.
- `data/equipment/weapons.json` for mastery property lookup.

## Success Criteria

- `tests/test_api_v1.py` still 22+ tests, all passing, with new tests added.
- `routes/character_summary.py` no longer contains private calc helpers; behavior unchanged on existing endpoints.
- `GET/POST /api/v1/character/derived` returns identical view-model dicts as the legacy session-coupled endpoints, given an equivalent `choices_made` payload.
- `RESUME.md` updated to reflect Phase 2 status and the next approval gate (Phase 3).
