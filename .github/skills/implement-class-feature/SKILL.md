---
name: implement-class-feature
description: "Implement a D&D class or subclass feature end-to-end: verify wiki data, update JSON with effects, add effect handlers if needed, write tests. Use when adding class features, subclass features, or new effect types."
---

# Implement Class Feature

End-to-end workflow for implementing a class or subclass feature with full effects system integration.

## When to Use

- Adding a new class feature with mechanical effects
- Implementing subclass features (e.g., domain spells, subclass abilities)
- Adding a new effect type to the system
- Completing a partially-implemented class

## Procedure

### 1. Verify Source Material

Check that wiki data exists for the feature:

```bash
# Check cache
ls wiki_data/classes/{class_name}.json
ls wiki_data/subclasses/{class_name}/{subclass_slug}.json
```

If missing, fetch it:
```bash
python update_classes.py --class {class_name}
```

Parse `content.text` from the cached JSON to understand the feature's mechanics.

### 2. Identify Effect Types

Map the feature's mechanical benefits to effect types from [the catalog](./references/effect-type-catalog.md):

| Mechanic | Effect Type |
|---|---|
| Grants a cantrip | `grant_cantrip` |
| Always-prepared spell | `grant_spell` with `min_level` |
| Weapon/armor proficiency | `grant_weapon_proficiency` / `grant_armor_proficiency` |
| Skill proficiency | `grant_skill_proficiency` |
| Save advantage | `grant_save_advantage` |
| Damage resistance | `grant_damage_resistance` |
| AC bonus | `bonus_ac` |
| Damage bonus | `bonus_damage` |
| HP bonus | `bonus_hp` |
| Speed increase | `increase_speed` |

If no existing effect type fits, a new one must be added to `CharacterBuilder._apply_effect()`.

### 3. Update Data File

Edit the class or subclass JSON in `data/classes/` or `data/subclasses/`:

```json
"features_by_level": {
  "3": {
    "Feature Name": {
      "description": "Description from wiki.",
      "effects": [
        {"type": "effect_type", ...fields}
      ]
    }
  }
}
```

**Critical**: `features_by_level` values must be **objects**, never arrays.

### 4. Validate Schema

```bash
python validate_data.py
```

Fix any schema violations before proceeding.

### 5. Implement Effect Handler (if needed)

If a new effect type was required:

1. Add handler in `modules/character_builder.py` → `_apply_effect()`
2. Wire into the relevant calculation method
3. Update `FEATURE_EFFECTS.md` with the new type

### 6. Write Tests

Create tests in the appropriate directory under `tests/`:

```python
from modules.character_builder import CharacterBuilder

def test_feature_name_effect():
    builder = CharacterBuilder()
    builder.apply_choices({
        "character_name": "Test",
        "level": 3,
        "species": "...",
        "class": "...",
        "subclass": "...",
        "background": "...",
        "ability_scores": {...},
        "background_bonuses": {...}
    })
    character = builder.to_character()
    
    # Assert the effect was applied
    assert ...
```

### 7. Run Full Test Suite

```bash
pytest tests/ -x -q --tb=short
```

All tests must pass before the feature is considered complete.

## Reference Files

- [Effect Type Catalog](./references/effect-type-catalog.md) — All supported effect types
- `FEATURE_EFFECTS.md` — Canonical effect documentation
- `models/class_schema.json` — Class data schema
- `models/subclass_schema.json` — Subclass data schema
