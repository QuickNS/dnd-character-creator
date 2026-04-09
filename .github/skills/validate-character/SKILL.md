---
name: validate-character
description: "Validate a complete character build by rebuilding from choices and checking all calculated values: HP, AC, skills, proficiencies, spells, effects. Use when verifying character correctness or testing after changes."
---

# Validate Character

Workflow for validating that a character build produces correct calculated values.

## When to Use

- After implementing a new feature to verify it works in a full build
- Checking if a bug fix resolved a calculation issue
- Validating test character files are still correct
- Verifying a class/species combination works end-to-end

## Procedure

### 1. Choose or Create Character Choices

Use an existing test character or define choices:

```python
choices = {
    "character_name": "Test Character",
    "level": 3,
    "species": "Dwarf",
    "class": "Cleric",
    "subclass": "Light Domain",
    "background": "Acolyte",
    "ability_scores": {
        "Strength": 14, "Dexterity": 8, "Constitution": 15,
        "Intelligence": 10, "Wisdom": 16, "Charisma": 12
    },
    "background_bonuses": {"Wisdom": 2, "Constitution": 1}
}
```

Reference builds are in `test_characters/`:
- `test_characters/test_cleric_dwarf.json`
- `test_characters/test_figher_wood_elf.json`

### 2. Build via API

Use the stateless API endpoint:

```bash
curl -X POST http://localhost:5000/api/choices-to-character \
  -H 'Content-Type: application/json' \
  -d '{"choices_made": {...}}'
```

Or in Python:
```python
from modules.character_builder import CharacterBuilder

builder = CharacterBuilder()
builder.apply_choices(choices)
character = builder.to_character()
```

### 3. Verify Calculated Values

Check each category against expected values:

#### HP
```python
# HP = (hit_die at L1) + (avg at L2+) + (CON mod × level) + bonuses
# Dwarf Cleric L3: 8 + 5 + 5 + (2×3) + (1×3) = 27
assert character['combat_stats']['hit_points']['maximum'] == expected
```

#### Proficiencies
```python
assert set(['Light armor', 'Medium armor', 'Shields']).issubset(set(character['proficiencies']['armor']))
assert 'Wisdom' in character['proficiencies']['saving_throws']
```

#### Effects
```python
effects = character.get('effects', [])
# Check resistances
assert any(e['type'] == 'grant_damage_resistance' and e['damage_type'] == 'Poison' for e in effects)
# Check save advantages
assert any(e['type'] == 'grant_save_advantage' for e in effects)
```

#### Spells (for casters)
```python
cantrips = character['spells']['prepared']['cantrips']
assert 'Light' in cantrips  # Light Domain bonus cantrip
```

#### Skills
```python
skills = character.get('skills', {})
insight = skills.get('Insight', {})
assert insight.get('proficient') is True
```

### 4. Compare with Previous Build

If a reference character exists, diff the output:

```python
import json

with open('test_characters/test_cleric_dwarf.json') as f:
    reference = json.load(f)

# Compare key sections
assert character['combat_stats'] == reference['combat_stats']
assert character['proficiencies'] == reference['proficiencies']
```

### 5. Report

Summarize:
- All checks passed / failed
- Any unexpected values with expected vs actual
- Suggestions for fixes if failures found
