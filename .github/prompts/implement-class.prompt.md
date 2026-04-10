---
description: 'Implements class features end-to-end using the agent chain: wiki-fetcher → data-author → data-validator → feature-implementer → test-writer, with automatic branch management and PR creation'
---

Implement the class features for **{{ class_name }}** using the following agent chain:

## Step 1 — Create Branch

Create and switch to a new branch `class/{{ class_name }}` from `main`:
- Run `git checkout main && git pull`
- Run `git checkout -b class/{{ class_name }}`

## Step 2 — Fetch Wiki Data (@wiki-fetcher)

Ensure `wiki_data/classes/{{ class_name }}.json` and all subclass wiki files exist.
Run `python update_classes.py --class {{ class_name }}` if missing.

## Step 3 — Author Data Files (@data-author)

Update `data/classes/{{ class_name }}.json` and all subclass files under `data/subclasses/{{ class_name }}/`:
- Parse wiki content from `wiki_data/`
- Ensure all features use structured `effects` arrays (see `FEATURE_EFFECTS.md`)
- Verify `features_by_level` uses **objects** (never arrays)
- Validate against schemas: `python validate_data.py`

## Step 4 — Validate Data (@data-validator)

Run `python validate_data.py` and verify:
- Schema compliance for all modified files
- All mechanical features have `effects` arrays
- D&D 2024 accuracy (compare against wiki cache)

## Step 5 — Implement Handlers (@feature-implementer)

If any features require new effect types not yet in `CharacterBuilder._apply_effect()`:
- Add the handler generically
- Wire into the relevant calculation method
- Update `FEATURE_EFFECTS.md`

## Step 6 — Write Tests (@test-writer)

Create `tests/{{ class_name }}/test_{{ class_name }}_features.py`:
- Test each subclass with a full character build
- Verify effects, proficiencies, spells, and calculated values
- Run `pytest tests/ -x -q --tb=short`

## Step 7 — Update Backlog

Update `data/completeness/backlog.json` to mark {{ class_name }} features as validated.

## Step 8 — Push, Create PR, and Merge

Commit all changes, push, create a PR, and merge:
- Run `git add -A && git commit -m "feat({{ class_name }}): implement class and subclass features"`
- Run `git push -u origin class/{{ class_name }}`
- Use `mcp_github_create_pull_request` to create a PR:
  - Title: `feat({{ class_name }}): implement class and subclass features`
  - Base: `main`, Head: `class/{{ class_name }}`
  - Body: summary of added/updated data files, new effect handlers, and tests
- Use `mcp_github_merge_pull_request` to merge the PR (squash merge, delete_branch: true)
- Run `git checkout main && git pull && git branch -d class/{{ class_name }}`
