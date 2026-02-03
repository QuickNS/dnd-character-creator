# D&D 2024 Character Sheet JSON Model Implementation Plan

## Overview
This document outlines the comprehensive JSON model for D&D 2024 character sheets and the plan to update our current character creation system.

## Key Sections of the Character Sheet

### 1. Character Information (Header)
- **character_name**: Character's name
- **class_level**: Combined class and level (e.g., "Fighter 3")
- **background**: Character background
- **player_name**: Player's name
- **species**: Character species (race)
- **lineage**: Subspecies/variant (if applicable)
- **alignment**: Character alignment
- **experience_points**: Current XP

### 2. Ability Scores (Left Column)
Each ability score contains:
- **score**: Raw ability score (8-20 typically)
- **modifier**: Calculated modifier (-5 to +5 typically)
- **saving_throw**: Total saving throw bonus
- **saving_throw_proficient**: Whether proficient in this save

### 3. Skills (Left Column)
Each skill contains:
- **proficient**: Whether character has proficiency
- **expertise**: Whether character has expertise (double proficiency)
- **bonus**: Total skill bonus (ability modifier + proficiency + other bonuses)

### 4. Combat Stats (Center)
- **armor_class**: Total AC including armor, dex, and bonuses
- **initiative**: Initiative modifier
- **speed**: Movement speed in feet
- **hit_point_maximum**: Max HP
- **current_hit_points**: Current HP
- **temporary_hit_points**: Temporary HP
- **hit_dice**: Total and remaining hit dice
- **death_saves**: Success and failure marks

### 5. Proficiencies and Languages (Center)
- **languages**: All known languages
- **armor**: Armor proficiencies
- **weapons**: Weapon proficiencies  
- **tools**: Tool proficiencies
- **proficiency_bonus**: Current proficiency bonus

### 6. Attacks and Spellcasting (Center)
- **attacks**: Each attack with bonus, damage, and type
- **spellcasting**: Spell save DC, attack bonus, slots, etc.

### 7. Equipment (Center/Right)
- **armor**: Equipped armor with AC and properties
- **weapons**: All weapons with damage and properties
- **other_equipment**: General equipment with quantities
- **money**: Currency in all denominations

### 8. Features and Traits (Right)
Organized by source:
- **class**: Class features by level
- **species**: Species traits and abilities
- **background**: Background features
- **feats**: Additional feats

### 9. Spells (Right/Back)
- **cantrips**: Known cantrips
- **prepared_spells**: All known/prepared spells by level

### 10. Character Details (Back)
- **age**, **height**, **weight**: Physical characteristics
- **appearance**: Physical description
- **backstory**: Character background story
- **allies_organizations**: Important connections
- **additional_features_traits**: Extra notes
- **treasure**: Important treasures/heirlooms

## Current vs Target Model Comparison

### What We Have Now:
```json
{
  "name": "string",
  "level": 1,
  "class": "string", 
  "ability_scores": {"Strength": 10, ...},
  "features": {"class": [], "species": [], ...},
  "skills": ["skill1", "skill2"],
  "languages": ["Common"]
}
```

### What We Need:
```json
{
  "character_info": {...},
  "ability_scores": {"strength": {"score": 16, "modifier": 3, "saving_throw": 6, ...}},
  "skills": {"athletics": {"proficient": true, "expertise": false, "bonus": 5}},
  "combat_stats": {...},
  "equipment": {...},
  "spells": {...}
}
```

## Implementation Priorities

### Phase 1: Core Structure (High Priority)
1. **Ability Scores**: Expand to include modifiers and saving throws
2. **Skills**: Convert from array to detailed objects with bonuses
3. **Combat Stats**: Add AC, initiative, HP calculations
4. **Proficiencies**: Organize armor, weapons, tools, languages

### Phase 2: Character Details (Medium Priority)  
1. **Character Info**: Structured header information
2. **Physical Characteristics**: Age, height, weight, appearance
3. **Equipment**: Detailed armor, weapons, and gear tracking
4. **Money**: Currency tracking

### Phase 3: Advanced Features (Lower Priority)
1. **Spellcasting**: Full spell system with slots and prepared spells
2. **Attacks**: Calculated attack bonuses and damage
3. **Meta Data**: Creation tracking and choices made

## Calculation Requirements

### Derived Values That Need Calculation:
- **Ability Modifiers**: (score - 10) / 2
- **Saving Throws**: modifier + (proficiency_bonus if proficient)
- **Skill Bonuses**: ability_modifier + (proficiency_bonus if proficient) + (proficiency_bonus if expertise)
- **Armor Class**: 10 + dex_modifier + armor_bonus + shield_bonus + other_bonuses
- **Initiative**: dex_modifier + other_bonuses
- **Hit Points**: class_hit_die + con_modifier + other_bonuses (per level)
- **Proficiency Bonus**: Based on character level (2 at levels 1-4, 3 at 5-8, etc.)

## Migration Strategy

### Step 1: Create Calculation Modules
- `ability_score_calculator.py`: Calculate modifiers and saves
- `skill_calculator.py`: Calculate skill bonuses with proficiency
- `combat_calculator.py`: Calculate AC, initiative, HP
- `proficiency_calculator.py`: Handle proficiency bonuses

### Step 2: Update Character Creation Flow
- Modify character initialization to use new structure
- Update each step to populate correct sections
- Add calculation calls at appropriate points

### Step 3: Create Character Sheet Exporters
- `character_sheet_data.py`: Convert internal format to sheet format
- `pdf_exporter.py`: Generate fillable PDF character sheets
- `json_exporter.py`: Export complete character sheet JSON

### Step 4: Update Frontend
- Modify templates to display new calculated values
- Add sections for equipment, spells, etc.
- Update character summary to show all sheet information

This comprehensive model ensures we can generate accurate, complete D&D 2024 character sheets in any format.