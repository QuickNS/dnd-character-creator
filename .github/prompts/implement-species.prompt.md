---
description: 'Implements species features end-to-end using the agent chain: wiki-fetcher → data-author → data-validator → feature-implementer → test-writer'
---

Implement the species features for **{{ species_name }}** using the following agent chain:

## Step 1 — Fetch Wiki Data (@wiki-fetcher)

Ensure `wiki_data/species/{{ species_name }}.json` exists.
Run `python update_species.py --species {{ species_name }}` if missing.

## Step 2 — Author Data Files (@data-author)

Update `data/species/{{ species_name }}.json` and any variant files under `data/species_variants/`:
- Parse wiki content from `wiki_data/`
- Ensure all traits use structured `effects` arrays (see `FEATURE_EFFECTS.md`)
- Species do NOT have ability score increases (D&D 2024)
- Validate against schemas

## Step 3 — Validate Data (@data-validator)

Run `python validate_data.py` and verify:
- Schema compliance for species file
- All mechanical traits have `effects` arrays
- No ability score increases in species data
- D&D 2024 accuracy

## Step 4 — Implement Handlers (@feature-implementer)

If any traits require new effect types:
- Add the handler in `CharacterBuilder._apply_effect()`
- Update `FEATURE_EFFECTS.md`

## Step 5 — Write Tests (@test-writer)

Create `tests/species/test_{{ species_name }}_traits.py`:
- Test species traits for effect application
- Verify with at least 2 different class combinations
- Run `pytest tests/ -x -q --tb=short`

## Step 6 — Update Backlog

Update `data/completeness/backlog.json` to mark {{ species_name }} as validated.