---
description: "Use when working with D&D feature effects, grant_spell, grant_cantrip, grant_proficiency, bonus_hp, bonus_ac, bonus_damage, damage resistance, save advantage, or any mechanical benefit in JSON data files or CharacterBuilder effect processing code."
applyTo: ["data/**/*.json", "modules/character_builder.py", "modules/feature_manager.py", "FEATURE_EFFECTS.md"]
---

# Effects System

## Cardinal Rule

**NEVER hardcode feature names or species names in application logic.**
All mechanical benefits MUST be defined as structured `effects` arrays in JSON data files and processed generically by `CharacterBuilder._apply_effect()`.

```python
# ❌ WRONG — hardcoded feature check
if feature_name == 'Dwarven Resilience':
    hp_bonus += level

# ✅ CORRECT — generic effect processing
if effect['type'] == 'bonus_hp' and effect.get('scaling') == 'per_level':
    hp_bonus += level * effect['value']
```

## Effect JSON Shape

Every effect is an object inside a feature's `effects` array:

```json
{
  "Feature Name": {
    "description": "Human-readable description.",
    "effects": [
      {"type": "<effect_type>", ...type-specific fields}
    ]
  }
}
```

## Quick Reference Table

| Effect Type | Required Fields | Optional Fields | Example Use |
|---|---|---|---|
| `grant_cantrip` | `spell` | `spell_list` | Light Domain bonus cantrip |
| `grant_spell` | `spell` | `level`, `min_level`, `spell_list`, `counts_against_limit` | Domain spells, lineage spells |
| `grant_spell_slots` | `level`, `count` | — | Bonus spell slots |
| `grant_weapon_proficiency` | `proficiencies` (array) | — | Protector martial weapons |
| `grant_armor_proficiency` | `proficiencies` (array) | — | Protector heavy armor |
| `grant_skill_proficiency` | `skills` (array) | — | Background skill grants |
| `grant_skill_expertise` | `skills` (array) | — | Rogue/Bard expertise |
| `grant_save_advantage` | `abilities` (array) | `condition`, `display` | Dwarven Resilience |
| `grant_save_proficiency` | `abilities` (array) | — | Class saving throws |
| `grant_damage_resistance` | `damage_type` | — | Poison, Fire, Necrotic |
| `grant_damage_immunity` | `damage_type` | — | Full immunity |
| `grant_condition_immunity` | `condition` | — | Charmed immunity |
| `bonus_ac` | `value` | `condition` | Defense fighting style |
| `bonus_damage` | `value` | `condition` | Dueling, Thrown Weapon |
| `bonus_attack` | `value` | `weapon_property` | Archery (+2 ranged) |
| `bonus_hp` | `value` | `scaling` (`per_level`) | Dwarven Toughness |
| `ability_bonus` | `ability`, `value` | `skills`, `minimum` | Thaumaturge WIS→INT |
| `grant_language` | `languages` (array) | — | Species languages |
| `grant_darkvision` | `range` | — | 60ft or 120ft |
| `increase_speed` | `value` | — | Wood Elf +5ft |
| `great_weapon_fighting` | — | — | Reroll 1s/2s on damage |
| `two_weapon_fighting_modifier` | — | — | Add ability mod to offhand |
| `unarmed_fighting` | — | — | Enhanced unarmed strikes |

## Spell Granting — Critical Format

**ALL spell granting MUST use effects arrays. NEVER use separate `spells` dicts.**

```json
// ❌ WRONG
{"Light Domain Spells": {"spells": {"3": ["Burning Hands"]}}}

// ✅ CORRECT
{
  "Light Domain Spells": {
    "description": "You always have certain spells prepared.",
    "effects": [
      {"type": "grant_spell", "spell": "Burning Hands", "min_level": 3},
      {"type": "grant_spell", "spell": "Faerie Fire", "min_level": 3}
    ]
  }
}
```

### Spell Storage Destinations
- Domain/subclass spells → `character['spells']['prepared']` (always prepared, use slots)
- Species/lineage spells → `character['spells']['prepared']` + `spell_metadata` (always prepared, 1/day free)

## Condition Strings for bonus_damage

| Condition Value | Meaning |
|---|---|
| `"one handed melee weapon"` | Melee, no Two-Handed, one weapon equipped (Dueling) |
| `"thrown weapon ranged attack"` | Thrown property, ranged attack roll (Thrown Weapon Fighting) |
| *(omitted)* | Applies to all attacks |

## Condition Strings for bonus_attack

| Field | Meaning |
|---|---|
| `weapon_property: "Ranged"` | Weapon category contains "Ranged" (Archery) |
| `weapon_property: "<name>"` | Weapon has that property in its properties list |

## Adding a New Effect Type

1. Define the JSON shape and add to this table
2. Add handler in `CharacterBuilder._apply_effect()`
3. Wire into the relevant calculation method (`calculate_weapon_attacks()`, `calculate_ac_options()`, etc.)
4. Add to `FEATURE_EFFECTS.md`
5. Write tests covering at least 2 different sources using the same effect type
