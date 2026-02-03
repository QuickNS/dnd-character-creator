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

```json
{
  "type": "bonus_ac",
  "value": 1,
  "condition": "while wearing armor"
}
```

#### bonus_damage
Grants a bonus to damage rolls.

```json
{
  "type": "bonus_damage",
  "value": "1d8",
  "damage_type": "radiant",
  "condition": "once per turn"
}
```

#### bonus_attack
Grants a bonus to attack rolls.

```json
{
  "type": "bonus_attack",
  "value": 2,
  "condition": "with ranged weapons"
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

## Implementation Notes

1. Effects are optional - features without effects are display-only
2. Effects should be processed when the feature is gained
3. Effects should be reversible (for changing choices)
4. The system should gracefully handle unknown effect types
5. Complex features may still require custom code, but common patterns should use this system

## Future Extensions

- Condition-based effects (e.g., "when bloodied", "on first hit")
- Scaling effects (e.g., "bonus increases at level 5")
- Resource-based effects (e.g., "uses per long rest")
- Temporary effects (e.g., buffs, reactions)
