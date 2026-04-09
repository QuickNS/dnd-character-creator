---
name: add-game-content
description: "Add a batch of D&D game content: multiple subclasses, backgrounds, feats, or spells. Use when populating missing data for an entire category or class."
---

# Add Game Content

Workflow for adding a batch of game content (e.g., all subclasses for a class, missing backgrounds, feat categories).

## When to Use

- Populating all subclasses for a class
- Adding missing backgrounds (Artisan, Farmer, Guard, etc.)
- Creating spell definition files
- Adding general feat data

## Procedure

### 1. Check Backlog

Read `data/completeness/backlog.json` to identify what's missing:

```bash
cat data/completeness/backlog.json | python -m json.tool
```

Or filter for a specific category:
```python
import json
with open('data/completeness/backlog.json') as f:
    backlog = json.load(f)

# Find missing subclasses for Ranger
ranger = backlog['classes']['Ranger']
for sc_name, sc_status in ranger['subclasses'].items():
    if not sc_status['features_validated']:
        print(f"  ❌ {sc_name}")
```

### 2. Fetch Wiki Data

Ensure wiki cache has the needed content:

```bash
python update_classes.py --class ranger
# Subclasses auto-fetched if class is fetched
```

For other content types, fetch manually:
```bash
# No script yet — use web fetch
```

### 3. Create Data Files from Templates

Use these templates as starting points:

#### Class Template
See [data file templates](./references/data-file-templates.md).

### 4. Add Effects

For each feature with mechanical benefits, add an `effects` array. Reference the effect type catalog in `.github/skills/implement-class-feature/references/effect-type-catalog.md`.

### 5. Validate

```bash
python validate_data.py
```

### 6. Write Tests

Create at least one integration test per class/species added:

```python
def test_new_subclass_features():
    builder = CharacterBuilder()
    builder.apply_choices({...})
    character = builder.to_character()
    # Assert key features are present
```

### 7. Update Backlog

After adding content, update `data/completeness/backlog.json` to reflect new status.

### 8. Run Full Suite

```bash
pytest tests/ -x -q --tb=short
```

## Reference Files

- [Data File Templates](./references/data-file-templates.md)
- `data/completeness/backlog.json` — Completeness tracking
- `models/class_schema.json`, `models/subclass_schema.json` — Schemas
