# Feature Effects System

## Overview
Features can grant various mechanical benefits through a structured "effects" array. This allows for consistent parsing and application of feature benefits without string searching.

## Effect Types

### Spellcasting Effects

#### grant_cantrip
Grants a specific cantrip to the character.

```json
{
  "type": "grant_cantrip",
  "spell": "Light",
  "spell_list": "Cleric"
}
```

#### grant_spell
Grants a specific spell that's always prepared.

```json
{
  "type": "grant_spell",
  "spell": "Shield",
  "level": 1,
  "spell_list": "Wizard"
}
```

#### grant_spell_slots
Grants additional spell slots.

```json
{
  "type": "grant_spell_slots",
  "level": 1,
  "count": 2
}
```

### Proficiency Effects

#### grant_weapon_proficiency
Grants weapon proficiencies.

```json
{
  "type": "grant_weapon_proficiency",
  "proficiencies": ["Martial weapons"]
}
```

#### grant_armor_proficiency
Grants armor proficiencies.

```json
{
  "type": "grant_armor_proficiency",
  "proficiencies": ["Heavy armor"]
}
```

#### grant_skill_proficiency
Grants skill proficiencies.

```json
{
  "type": "grant_skill_proficiency",
  "skills": ["Perception", "Insight"]
}
```

#### grant_skill_expertise
Grants expertise in skills.

```json
{
  "type": "grant_skill_expertise",
  "skills": ["Stealth"]
}
```

### Saving Throw Effects

#### grant_save_advantage
Grants advantage on saving throws.

```json
{
  "type": "grant_save_advantage",
  "abilities": ["Constitution"],
  "condition": "Poisoned",
  "display": "Advantage vs Poisoned condition"
}
```

**Properties:**
- `abilities`: Array of ability scores this applies to (e.g., ["Constitution", "Wisdom"])
- `condition`: (Optional) Specific condition this applies against (e.g., "Poisoned", "Charmed")
- `display`: Text to display in character sheet

**Example:** Dwarven Resilience
```json
{
  "type": "grant_save_advantage",
  "abilities": ["Constitution"],
  "condition": "Poisoned",
  "display": "Advantage vs Poisoned condition"
}
```

#### grant_save_proficiency
Grants proficiency in saving throws.

```json
{
  "type": "grant_save_proficiency",
  "abilities": ["Wisdom", "Charisma"]
}
```

### Resistance and Immunity Effects

#### grant_damage_resistance
Grants resistance to a damage type.

```json
{
  "type": "grant_damage_resistance",
  "damage_type": "Poison"
}
```

#### grant_damage_immunity
Grants immunity to a damage type.

```json
{
  "type": "grant_damage_immunity",
  "damage_type": "Fire"
}
```

#### grant_condition_immunity
Grants immunity to a condition.

```json
{
  "type": "grant_condition_immunity",
  "condition": "Charmed"
}
```

### Combat Effects

#### bonus_ac
Grants a bonus to AC.

**Implementation**: Applied in `calculate_ac_options()`. Only applies to armored AC options (checks if `equipped_armor` is not None).

**Example**: Defense fighting style
```json
{
  "type": "bonus_ac",
  "value": 1,
  "condition": "wearing armor"
}
```

#### bonus_damage
Grants a bonus to damage rolls.

**Implementation**: Applied in `calculate_weapon_attacks()`. Checks conditions against weapon properties:
- `"one handed melee weapon"`: Melee weapon without Two-Handed property, only one weapon equipped (Dueling)
- `"thrown weapon ranged attack"`: Weapon with Thrown property used for ranged attack (Thrown Weapon Fighting)
- No condition: Applies to all attacks

**Example**: Dueling fighting style
```json
{
  "type": "bonus_damage",
  "value": 2,
  "condition": "one handed melee weapon"
}
```

**Example**: Thrown Weapon Fighting
```json
{
  "type": "bonus_damage",
  "value": 2,
  "condition": "thrown weapon ranged attack"
}
```

#### bonus_attack
Grants a bonus to attack rolls.

**Implementation**: Applied in `calculate_weapon_attacks()`. Checks conditions against weapon category or properties:
- `weapon_property: "Ranged"`: Applies if weapon category contains "Ranged" (Archery)
- `weapon_property: "<property>"`: Applies if weapon has that property in its properties list
- No condition: Applies to all attacks

**Example**: Archery fighting style
```json
{
  "type": "bonus_attack",
  "value": 2,
  "weapon_property": "Ranged"
}
```

### Ability Score Effects

#### ability_bonus
Grants a bonus to ability checks.

```json
{
  "type": "ability_bonus",
  "ability": "Intelligence",
  "skills": ["Arcana", "Religion"],
  "value": "wisdom_modifier",
  "minimum": 1
}
```

### Miscellaneous Effects

#### grant_language
Grants language proficiencies.

```json
{
  "type": "grant_language",
  "languages": ["Elvish", "Dwarvish"]
}
```

#### increase_speed
Increases movement speed.

```json
{
  "type": "increase_speed",
  "value": 10
}
```

#### grant_darkvision
Grants or improves darkvision.

```json
{
  "type": "grant_darkvision",
  "range": 60
}
```

#### bonus_hp
Grants a bonus to hit points.

```json
{
  "type": "bonus_hp",
  "value": 1,
  "scaling": "per_level"
}
```

**Properties:**
- `value`: The amount of HP bonus to grant
- `scaling`: (Optional) How the bonus scales. Use "per_level" for bonuses that apply at each level (like Dwarven Toughness)

**Example:** Dwarven Toughness
```json
{
  "type": "bonus_hp",
  "value": 1,
  "scaling": "per_level"
}
```

## Feature Structure

Features can include an `effects` array alongside their description:

```json
"Bonus Cantrip": {
  "description": "You know the Light cantrip.",
  "effects": [
    {
      "type": "grant_cantrip",
      "spell": "Light",
      "spell_list": "Cleric"
    }
  ]
}
```

## Multiple Effects

A single feature can grant multiple effects:

```json
"Divine Order - Protector": {
  "description": "You gain proficiency with Martial weapons and training with Heavy armor.",
  "effects": [
    {
      "type": "grant_weapon_proficiency",
      "proficiencies": ["Martial weapons"]
    },
    {
      "type": "grant_armor_proficiency",
      "proficiencies": ["Heavy armor"]
    }
  ]
}
```

## External Effect References

Features that are shared across multiple classes (like Fighting Styles) should be stored in separate data files and referenced using the choice reference system:

### Example: Fighting Styles

**In class data (e.g., fighter.json):**
```json
"Fighting Style": {
  "description": "You adopt a particular style of fighting as your specialty.",
  "choices": {
    "type": "select_single",
    "count": 1,
    "name": "fighting_style",
    "source": {
      "type": "external",
      "file": "fighting_styles.json",
      "list": "fighting_styles"
    },
    "optional": false
  }
}
```

**In external data file (data/fighting_styles.json):**
```json
{
  "fighting_styles": {
    "Archery": {
      "description": "You gain a +2 bonus to attack rolls you make with ranged weapons.",
      "effects": [
        {
          "type": "bonus_attack",
          "value": 2,
          "weapon_property": "Ranged"
        }
      ]
    },
    "Defense": {
      "description": "While you are wearing armor, you gain a +1 bonus to AC.",
      "effects": [
        {
          "type": "bonus_ac",
          "value": 1,
          "condition": "wearing armor"
        }
      ]
    }
  }
}
```

This approach allows:
- Reuse across Fighter, Paladin, Ranger, and feats
- Single source of truth for fighting style mechanics
- Easy updates to all classes when fighting styles change
- Consistent behavior across all sources

## Implementation Notes

1. Effects are optional - features without effects are display-only
2. Effects should be processed when the feature is gained
3. Effects should be reversible (for changing choices)
4. The system should gracefully handle unknown effect types
5. Complex features may still require custom code, but common patterns should use this system
6. External references are loaded automatically when applying choices
