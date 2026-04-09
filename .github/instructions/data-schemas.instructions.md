---
description: "Use when creating or editing D&D game data JSON files: classes, subclasses, species, backgrounds, spells, feats. Covers required fields, data types, and the critical features_by_level object format."
applyTo: "data/**/*.json"
---

# Data File Schemas

All data files MUST comply with schemas in `models/`. Run `python validate_data.py` to check.

## Class Data (`data/classes/*.json`)

**Schema**: `models/class_schema.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✅ | Capitalized: "Wizard" |
| `description` | string | ✅ | |
| `hit_die` | integer | ✅ | One of: 6, 8, 10, 12 |
| `primary_ability` | string | ✅ | |
| `saving_throw_proficiencies` | array[2] | ✅ | Exactly 2 ability names |
| `subclass_selection_level` | integer | ✅ | 1, 2, or 3 |
| `proficiency_bonus_by_level` | object | ✅ | `"1"` → 2 through `"20"` → 6 |
| `features_by_level` | object | ✅ | **See critical format below** |
| `armor_proficiencies` | array | ❌ | |
| `weapon_proficiencies` | array | ❌ | |
| `spellcasting_ability` | string | ❌ | For casters only |
| `cantrips_by_level` | object | ❌ | `"1"` → count |
| `prepared_spells_by_level` | object | ❌ | `"1"` → count |
| `spell_slots_by_level` | object | ❌ | `"1"` → [9 integers] |

## Subclass Data (`data/subclasses/{class}/*.json`)

**Schema**: `models/subclass_schema.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✅ | "Light Domain" |
| `class` | string | ✅ | Parent class name |
| `description` | string | ✅ | |
| `source` | string | ✅ | "Player's Handbook 2024" |
| `features_by_level` | object | ✅ | **See critical format below** |

## Critical Format: `features_by_level`

Maps level (as **string**) → **OBJECT** of feature_name → description-or-object.

```json
// ❌ NEVER arrays
"features_by_level": {
  "1": ["Spellcasting", "Ritual Adept"]
}

// ✅ ALWAYS objects
"features_by_level": {
  "1": {
    "Spellcasting": "Cast spells using Intelligence.",
    "Ritual Adept": "Cast Ritual spells without preparing."
  }
}
```

### Feature Values

A feature value can be:
- **String**: Simple description (display-only)
- **Object**: Description + effects (mechanical benefit)

```json
"3": {
  "Bonus Cantrip": {
    "description": "You know the Light cantrip.",
    "effects": [
      {"type": "grant_cantrip", "spell": "Light"}
    ]
  },
  "Warding Flare": "React to impose disadvantage on an attack roll."
}
```

## Species Data (`data/species/*.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✅ | |
| `creature_type` | string | ✅ | Usually "Humanoid" |
| `size` | string | ✅ | "Small" or "Medium" |
| `speed` | integer | ✅ | Base walking speed |
| `darkvision` | integer | ❌ | Range in feet |
| `traits` | object | ✅ | Trait name → {description, effects?} |
| `languages` | array | ✅ | ["Common", ...] |

**Species do NOT have ability score increases** (those come from backgrounds in D&D 2024).

## Background Data (`data/backgrounds/*.json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | ✅ | |
| `ability_score_increase` | object | ✅ | `total`, `options`, `suggested` |
| `feat` | string | ✅ | Origin feat name |
| `skill_proficiencies` | array | ✅ | Exactly 2 skills |
| `starting_equipment` | object | ❌ | |

```json
"ability_score_increase": {
  "total": 3,
  "options": ["Strength", "Constitution", "Wisdom"],
  "suggested": {"Strength": 2, "Constitution": 1}
}
```

## Spell Definition (`data/spells/definitions/*.json`)

| Field | Type | Required |
|---|---|---|
| `name` | string | ✅ |
| `level` | integer | ✅ |
| `school` | string | ✅ |
| `casting_time` | string | ✅ |
| `range` | string | ✅ |
| `components` | string | ✅ |
| `duration` | string | ✅ |
| `description` | string | ✅ |
| `classes` | array | ✅ |
| `source` | string | ✅ |

## Validation

```bash
python validate_data.py          # Validate all files
```

The validator checks classes and subclasses against their JSON schemas and reports compliance with ✅/❌ indicators.
