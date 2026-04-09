---
description: 'Implements class features end-to-end using the agent chain: wiki-fetcher → data-author → data-validator → feature-implementer → test-writer'
---

Implement the class features for **{{ class_name }}** using the following agent chain:

## Step 1 — Fetch Wiki Data (@wiki-fetcher)

Ensure `wiki_data/classes/{{ class_name }}.json` and all subclass wiki files exist.
Run `python update_classes.py --class {{ class_name }}` if missing.

## Step 2 — Author Data Files (@data-author)

Update `data/classes/{{ class_name }}.json` and all subclass files under `data/subclasses/{{ class_name }}/`:
- Parse wiki content from `wiki_data/`
- Ensure all features use structured `effects` arrays (see `FEATURE_EFFECTS.md`)
- Verify `features_by_level` uses **objects** (never arrays)
- Validate against schemas: `python validate_data.py`

## Step 3 — Validate Data (@data-validator)

Run `python validate_data.py` and verify:
- Schema compliance for all modified files
- All mechanical features have `effects` arrays
- D&D 2024 accuracy (compare against wiki cache)

## Step 4 — Implement Handlers (@feature-implementer)

If any features require new effect types not yet in `CharacterBuilder._apply_effect()`:
- Add the handler generically
- Wire into the relevant calculation method
- Update `FEATURE_EFFECTS.md`

## Step 5 — Write Tests (@test-writer)

Create `tests/{{ class_name }}/test_{{ class_name }}_features.py`:
- Test each subclass with a full character build
- Verify effects, proficiencies, spells, and calculated values
- Run `pytest tests/ -x -q --tb=short`

## Step 6 — Update Backlog

Update `data/completeness/backlog.json` to mark {{ class_name }} features as validated.
