# Generic Choice Reference System

## Overview

This system allows features, feats, and other character elements to reference choices from internal lists (within the same JSON file) or external lists (from separate files) without hardcoding specific logic for each case.

## Choice Reference Types

### 1. Internal References
References a list within the same JSON file.

```json
{
  "choices": {
    "type": "select_multiple",
    "count": 3,
    "source": {
      "type": "internal",
      "list": "maneuvers"
    }
  }
}
```

### 2. External Static References  
References a specific list in another file.

```json
{
  "choices": {
    "type": "select_multiple",
    "count": 2,
    "source": {
      "type": "external",
      "file": "spells/wizard_cantrips.json",
      "list": "cantrips"
    }
  }
}
```

### 3. External Dynamic References
References a file/list determined by another choice.

```json
{
  "choices": [
    {
      "type": "select_single",
      "name": "spell_list_class", 
      "source": {
        "type": "fixed_list",
        "options": ["Wizard", "Cleric", "Sorcerer"]
      }
    },
    {
      "type": "select_multiple",
      "count": 2,
      "name": "cantrips",
      "source": {
        "type": "external_dynamic",
        "file_pattern": "spells/{spell_list_class}_cantrips.json",
        "list": "cantrips", 
        "depends_on": "spell_list_class"
      }
    }
  ]
}
```

### 4. Fixed List References
Direct list in the choice definition.

```json
{
  "choices": {
    "type": "select_single",
    "source": {
      "type": "fixed_list",
      "options": ["Intelligence", "Wisdom", "Charisma"]
    }
  }
}
```

## Choice Types

### Selection Types
- `select_single`: Choose one option
- `select_multiple`: Choose multiple options
- `select_or_replace`: Choose new or replace existing options

### Common Properties
- `type`: The selection type
- `count`: Number of choices (for multiple selection)
- `name`: Identifier for this choice group
- `source`: Where to find the available options
- `restrictions`: Additional filtering (e.g., spell schools)
- `optional`: Whether the choice can be skipped

## Advanced Features

### Level-Based Progression
```json
{
  "choices": {
    "type": "select_multiple",
    "count": 3,
    "source": {"type": "internal", "list": "maneuvers"},
    "additional_choices_by_level": {
      "7": {"count": 2, "replace_allowed": true},
      "10": {"count": 2, "replace_allowed": true}, 
      "15": {"count": 2, "replace_allowed": true}
    }
  }
}
```

### Conditional Choices
```json
{
  "choices": {
    "type": "select_multiple",
    "count": 2,
    "source": {"type": "external", "file": "spells/wizard_spells.json"},
    "restrictions": ["Abjuration", "Evocation"],
    "condition": "level >= 3"
  }
}
```

### Replacement Options
```json
{
  "choices": {
    "type": "select_or_replace",
    "count": 1,
    "source": {"type": "internal", "list": "maneuvers"},
    "replace_existing": true,
    "replace_condition": "long_rest"
  }
}
```

## File Structure Examples

### Data Directory Structure
```
data/
├── classes/
├── subclasses/
├── backgrounds/ 
├── feats/
└── spells/
    ├── wizard_cantrips.json
    ├── wizard_spells.json
    ├── cleric_cantrips.json
    └── cleric_spells.json
```

### Spell List File Format
```json
{
  "name": "Wizard Cantrips",
  "spell_list_type": "cantrips", 
  "class": "Wizard",
  "cantrips": {
    "Fire Bolt": {
      "school": "Evocation",
      "description": "...",
      "components": "V, S"
    }
  }
}
```

## Implementation Benefits

1. **Generic Logic**: One system handles all choice types
2. **External References**: Spell lists, maneuver lists, feat lists can be separate files
3. **Dynamic Resolution**: Choice files determined at runtime based on user selections
4. **Extensible**: Easy to add new choice types and sources
5. **Validation**: System can validate choices against available options
6. **Level Progression**: Natural handling of choices that expand at higher levels

## Real-World Examples

### Battle Master Maneuvers
- **Problem**: Combat Superiority says "choose maneuvers" but doesn't list them
- **Solution**: Reference internal "maneuvers" list, with level progression

### Magic Initiate (Wizard)
- **Problem**: Need cantrips/spells from wizard list, which should be separate file
- **Solution**: External reference to wizard spell files

### Eldritch Knight Spells
- **Problem**: Need wizard spells with school restrictions (Abjuration/Evocation)
- **Solution**: External reference with restriction filters

### High Elf Cantrip
- **Problem**: Choose wizard cantrip, replaceable on long rest
- **Solution**: External reference with replacement options

This system replaces hardcoded choice logic with declarative configuration, making the system extensible and maintainable while supporting all current and future choice scenarios.