# CharacterBuilder - Testing & Development Guide

## Overview

The `CharacterBuilder` class is a **Flask-independent**, **stateful** character creation system that can be used for:
- ✅ Unit testing without web interface
- ✅ Automated testing scripts
- ✅ API endpoints
- ✅ CLI tools
- ✅ Debugging specific character states

## Why CharacterBuilder?

### Before (Problems)
- Had to click through entire web wizard to test features
- Couldn't easily test specific character states
- Hard to reproduce bugs
- No automated testing possible
- Tightly coupled to Flask/sessions

### After (Solutions)
- Create any character state in seconds with code
- Automated, repeatable tests
- Easy debugging of specific scenarios
- Reusable in multiple contexts
- Clear separation of business logic from web layer

## Quick Start

### Basic Usage

```python
from modules.character_builder import CharacterBuilder

# Create a builder
builder = CharacterBuilder()

# Set species and lineage
builder.set_species("Elf")
builder.set_lineage("Wood Elf", spellcasting_ability="Wisdom")

# Set class and level
builder.set_class("Ranger", level=3)

# Set background
builder.set_background("Sage")

# Set ability scores
builder.set_abilities({
    "STR": 10,
    "DEX": 16,
    "CON": 14,
    "INT": 12,
    "WIS": 15,
    "CHA": 8
})

# Check results
print(builder.get_cantrips())  # ['Druidcraft']
print(builder.get_spells())     # ['Longstrider']
print(builder.character_data['speed'])  # 35
```

### Quick Create (For Testing)

```python
# One-liner character creation
builder = CharacterBuilder.quick_create(
    species="Elf",
    lineage="Wood Elf",
    char_class="Ranger",
    background="Sage",
    abilities={"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8},
    level=3,
    spellcasting_ability="Wisdom"
)

# Character is fully built and ready
assert builder.is_complete()
```

## Testing Examples

### Test a Specific Feature

```python
def test_wood_elf_gets_druidcraft():
    """Test that Wood Elf receives Druidcraft cantrip"""
    builder = CharacterBuilder()
    builder.set_species("Elf")
    builder.set_lineage("Wood Elf", spellcasting_ability="Wisdom")
    
    cantrips = builder.get_cantrips()
    assert "Druidcraft" in cantrips
    assert builder.character_data['speed'] == 35
```

### Test Level-Based Features

```python
def test_level_3_spell_grant():
    """Test spells granted at specific levels"""
    # Level 1 - shouldn't have Longstrider
    builder_l1 = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8},
        level=1
    )
    assert "Longstrider" not in builder_l1.get_spells()
    
    # Level 3 - should have Longstrider
    builder_l3 = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8},
        level=3
    )
    assert "Longstrider" in builder_l3.get_spells()
```

### Test Character Export

```python
def test_character_export():
    """Test exporting to different formats"""
    builder = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8}
    )
    
    # Export to JSON
    json_data = builder.to_json()
    
    # Export to Character object
    char_obj = builder.to_character()
    
    # Round-trip test
    builder2 = CharacterBuilder()
    builder2.from_json(json_data)
    assert builder2.character_data['species'] == builder.character_data['species']
```

## Available Methods

### Setup Methods

| Method | Description |
|--------|-------------|
| `set_species(name)` | Set character species |
| `set_lineage(name, spellcasting_ability)` | Set lineage/variant |
| `set_class(name, level)` | Set class and level |
| `set_subclass(name)` | Set subclass |
| `set_background(name)` | Set background |
| `set_abilities(scores)` | Set ability scores |

### Query Methods

| Method | Description |
|--------|-------------|
| `get_cantrips()` | Get list of cantrips |
| `get_spells()` | Get list of known spells |
| `get_proficiencies(type)` | Get proficiencies by type |
| `get_current_step()` | Get current creation step |
| `is_complete()` | Check if character is complete |
| `validate()` | Validate character data |

### Export Methods

| Method | Description |
|--------|-------------|
| `to_json()` | Export as JSON dictionary |
| `to_character()` | Convert to Character object |
| `from_json(data)` | Import from JSON |

### Factory Methods

| Method | Description |
|--------|-------------|
| `quick_create(...)` | Create complete character in one call |

## Running Tests

### Run All Tests
```bash
python test_character_builder.py
```

### Run Specific Test
```python
python -c "from test_character_builder import test_wood_elf_cantrip; test_wood_elf_cantrip()"
```

## Integration with Flask

The CharacterBuilder can be easily integrated into Flask routes:

### Example Flask Route

```python
@app.route('/api/character/create', methods=['POST'])
def api_create_character():
    """Create character from JSON payload"""
    data = request.json
    
    builder = CharacterBuilder()
    builder.set_species(data['species'])
    
    if 'lineage' in data:
        builder.set_lineage(data['lineage'], data.get('spellcasting_ability'))
    
    builder.set_class(data['class'], data.get('level', 1))
    builder.set_background(data['background'])
    builder.set_abilities(data['abilities'])
    
    return jsonify(builder.to_character())
```

### Working with CharacterBuilder in Routes

```python
from utils.route_helpers import get_builder_from_session, save_builder_to_session

@app.route('/my-route')
def my_route():
    """Example route using CharacterBuilder from session"""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    # Get complete character data with all calculations
    character_data = builder.to_character()
    
    # Pass to template - no calculations needed
    return render_template('my_template.html', character=character_data)
```

## Character Data Structure

The `character_data` dictionary contains:

```python
{
    'name': str,
    'species': str,
    'species_data': dict,
    'lineage': str,
    'lineage_data': dict,
    'class': str,
    'class_data': dict,
    'subclass': str,
    'subclass_data': dict,
    'background': str,
    'background_data': dict,
    'level': int,
    'abilities': {
        'base': dict,
        'species_bonuses': dict,
        'background_bonuses': dict,
        'final': dict
    },
    'features': list,
    'choices_made': dict,
    'spells': {
        'cantrips': list,
        'known': list,
        'prepared': list,
        'slots': dict
    },
    'proficiencies': {
        'armor': list,
        'weapons': list,
        'tools': list,
        'skills': list,
        'languages': list,
        'saving_throws': list
    },
    'speed': int,
    'darkvision': int,
    'resistances': list,
    'immunities': list,
    'step': str  # Current creation step
}
```

## Effects System

The CharacterBuilder automatically applies effects from species, lineages, classes, and backgrounds:

### Supported Effect Types

- `grant_cantrip` - Grants a cantrip
- `grant_spell` - Grants a spell (with level requirements)
- `grant_weapon_proficiency` - Grants weapon proficiencies
- `grant_armor_proficiency` - Grants armor proficiencies
- `grant_skill_proficiency` - Grants skill proficiencies
- `grant_damage_resistance` - Grants damage resistance
- `grant_darkvision` - Grants or improves darkvision
- `increase_speed` - Increases movement speed

### Effect Application Example

Wood Elf lineage data:
```json
{
  "traits": {
    "Druidcraft": {
      "description": "You know the Druidcraft cantrip.",
      "effects": [
        {
          "type": "grant_cantrip",
          "spell": "Druidcraft"
        }
      ]
    }
  }
}
```

Automatically applied when lineage is set:
```python
builder.set_lineage("Wood Elf")
# Druidcraft is now in builder.get_cantrips()
```

## Best Practices

### ✅ Do This
- Use `quick_create()` for simple test scenarios
- Test specific features in isolation
- Use meaningful test names that describe what's being tested
- Validate character data after building
- Test edge cases (level 1 vs level 3, etc.)

### ❌ Don't Do This
- Don't test through Flask routes if you can test the CharacterBuilder directly
- Don't create incomplete characters without validation
- Don't assume effects are applied - verify them
- Don't test multiple unrelated features in one test

## Troubleshooting

### Issue: Species/lineage not found
**Solution**: Verify JSON files exist in `data/species/` or `data/species_variants/`

### Issue: Effects not applying
**Solution**: Check that the effect type is supported in `_apply_effect()` method

### Issue: Level-based features not working
**Solution**: Ensure effects have `min_level` property and level is set correctly

### Issue: Validation failing
**Solution**: Check required fields are set and ability scores are valid (1-20)

## Next Steps

1. **Add more tests** for other species, classes, and features
2. **Create API endpoints** using CharacterBuilder
3. **Add CLI tool** for command-line character creation
4. **Integrate with existing Flask routes** to use CharacterBuilder internally
5. **Add CI/CD tests** to run automatically on commits

## Resources

- **Test Script**: `test_character_builder.py`
- **Module**: `modules/character_builder.py`
- **Data Files**: `data/species/`, `data/classes/`, `data/backgrounds/`, etc.
- **Effects Documentation**: `FEATURE_EFFECTS.md`

---

**Need help?** Check the test scripts for examples or refer to the CharacterBuilder source code documentation.
