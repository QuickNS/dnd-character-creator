# Spell System Migration Guide

## Overview
The spell system has been restructured to eliminate duplication and provide better maintainability.

## New Structure

### Before (Old System)
```
data/spells/
├── druid/
│   ├── 0.json  # Druid cantrips with full spell details
│   ├── 1.json  # Druid 1st level spells with full spell details
│   └── 2.json  # Druid 2nd level spells with full spell details
├── wizard/
│   ├── 0.json  # Wizard cantrips with full spell details (DUPLICATED)
│   └── 1.json  # Wizard 1st level spells with full spell details (DUPLICATED)
└── cleric/
    └── 0.json  # Cleric cantrips with full spell details (DUPLICATED)
```

### After (New System)
```
data/spells/
├── definitions/          # Individual spell files (no duplication)
│   ├── longstrider.json
│   ├── light.json
│   ├── detect_magic.json
│   └── ...
└── class_lists/         # Class-specific spell lists (references only)
    ├── druid.json       # Lists spell names by level
    ├── wizard.json      # Lists spell names by level
    ├── cleric.json      # Lists spell names by level
    └── ...
```

## Usage Examples

### Loading Individual Spells
```python
from utils.spell_loader import SpellLoader

loader = SpellLoader()
longstrider = loader.get_spell("Longstrider")
print(longstrider["description"])  # "A creature you touch increases its Speed..."
print(longstrider["classes"])      # ["Bard", "Druid", "Ranger", "Wizard"]
```

### Loading Class Spell Lists
```python
# Get all Druid spells
druid_spells = loader.get_class_spells("Druid")

# Get only Druid cantrips
druid_cantrips = loader.get_class_spells("Druid", level=0)

# Get Druid 1st level spells
druid_1st = loader.get_class_spells("Druid", level=1)
```

### Loading Full Spell Details for a Class
```python
# Get full spell objects for all Druid 1st level spells
spell_details = loader.get_spell_details_for_class("Druid", level=1)
for spell in spell_details:
    print(f"{spell['name']}: {spell['description']}")
```

### Choice Reference System Integration
The new system works seamlessly with the existing Choice Reference System:

```json
{
  "spellcasting": {
    "choices": [
      {
        "type": "select_multiple",
        "count": 2,
        "name": "cantrips",
        "source": {
          "type": "external",
          "file": "spells/class_lists/wizard.json",
          "list": "cantrips"
        }
      }
    ]
  }
}
```

## Benefits

1. **No Duplication**: Each spell is defined once in `definitions/`
2. **Easy Maintenance**: Update spell details in one place
3. **Cross-Class Support**: Can easily see which classes have access to a spell
4. **Flexible References**: Class lists can reference any spell
5. **Backward Compatible**: Existing code can be updated incrementally

## Migration Steps

1. **Keep Old Files**: Don't delete old spell files until migration is complete
2. **Update Loading Code**: Replace direct file reads with SpellLoader calls
3. **Test Thoroughly**: Verify all spell-related features work correctly
4. **Clean Up**: Remove old spell files once everything is working

## File Format Examples

### Spell Definition (`definitions/longstrider.json`)
```json
{
  "name": "Longstrider",
  "level": 1,
  "school": "Transmutation",
  "casting_time": "1 action",
  "range": "Touch",
  "components": ["V", "S", "M"],
  "material": "a pinch of dirt",
  "duration": "1 hour",
  "description": "A creature you touch increases its Speed for the duration.",
  "classes": ["Bard", "Druid", "Ranger", "Wizard"],
  "source": "Player's Handbook 2024"
}
```

### Class List (`class_lists/druid.json`)
```json
{
  "class": "Druid",
  "cantrips": [
    "Druidcraft",
    "Guidance",
    "Mending"
  ],
  "spells_by_level": {
    "1": [
      "Longstrider",
      "Detect Magic"
    ],
    "2": [
      "Pass without Trace"
    ]
  }
}
```

## Next Steps

1. Update existing code that loads spells to use the new SpellLoader utility
2. Add more spell definitions as needed
3. Extend class lists for complete spell coverage
4. Update feature effects that grant spells to reference the new system