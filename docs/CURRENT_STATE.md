# D&D 2024 Character Creator - Current State

**Last Updated**: 2026-02-06

## 🎯 Project Overview

A web-based D&D 2024 character creator with a data-driven architecture that uses a structured effects system for all mechanical benefits. The system ensures consistency between display and game mechanics through a unified CharacterBuilder engine.

**Key Architectural Principle**: CharacterBuilder is the single source of truth for ALL character calculations. Routes and API endpoints are pure consumers that call `builder.to_character()` and pass the complete calculated character data to templates or export formats.

## ✅ Completed Features

### Core Architecture
- **Single Source of Truth**: CharacterBuilder is the only engine for character creation AND all calculations
- **Calculation Centralization**: ALL calculations (skills, saves, AC, attacks, HP) happen in CharacterBuilder methods
- **Routes as Consumers**: Flask routes/API call `to_character()` and pass results to templates - NO calculations in routes
- **Effects System**: All mechanical benefits (proficiencies, spells, bonuses, etc.) defined via structured effects in JSON
- **Data-Driven Design**: No hardcoded lists - check against data files (e.g., weapons.json for weapon detection)
- **Unified Approach**: Web wizard, API, JSON export, and PDF generation all use the same CharacterBuilder engine

### Web Wizard (Flask)
- **Complete Character Creation Flow**: Class → Subclass → Background → Species → Lineage → Abilities → Summary
- **Step-by-Step Guidance**: Each step validates and stores choices incrementally
- **Session Management**: CharacterBuilder state serialized in Flask sessions
- **Dynamic Choice Forms**: Automatically generated from feature choice configurations
- **Nested Choices**: Support for choices that trigger additional choices (e.g., Divine Order → Thaumaturge → bonus cantrip)

### Effects System - Fully Implemented
All effect types working and documented:

**Spells:**
- `grant_cantrip` - Grant specific cantrips
- `grant_spell` - Grant leveled spells (always prepared)
- Automatic spell table generation for multi-level spell grants
- Spell metadata tracking (domain vs. species spells)

**Proficiencies:**
- `grant_weapon_proficiency` - Weapon proficiencies
- `grant_armor_proficiency` - Armor proficiencies
- `grant_skill_proficiency` - Skill proficiencies
- `grant_skill_expertise` - Skill expertise
- `grant_language` - Language proficiencies

**Combat & Abilities:**
- `ability_bonus` - Conditional ability bonuses (e.g., Thaumaturge's WIS to INT)
- `bonus_hp` - Hit point bonuses with scaling (e.g., Dwarven Toughness)
- `grant_save_advantage` - Advantage on saving throws
- `grant_save_proficiency` - Saving throw proficiencies
- `grant_damage_resistance` / `grant_damage_immunity` - Damage resistances/immunities

### Feature Display System
- **Choice-Specific Descriptions**: Features show actual choice descriptions, not generic prompts
- **Nested Choice Display**: Bonus choices append to parent features (e.g., "Divine Order: Thaumaturge\n\nBonus Cantrip: Guidance")
- **Spell Tables**: Multi-level spell grants display as HTML tables with ✓/🔒 indicators
- **Source Attribution**: Features tagged with source (Cleric, Light Domain, High Elf, etc.)
- **Scaling Support**: Template variables replaced with level-appropriate values
- **HTML Rendering**: Feature descriptions support HTML (tables, formatting)

### Spell System
- **Unified Format**: All spell grants use effects system (domain, species, class)
- **Storage Categories**:
  - `cantrips` - Known cantrips
  - `prepared` - Always prepared spells (domain + species)
  - `spell_metadata` - Tracks sources for badge display
- **Display Badges**:
  - "Always Prepared" (green) - Domain/subclass spells
  - "1/Day (No Slot)" (blue) - Species/lineage spells
  - Both badges for species spells
- **Spell Slots Display**: Shows all available slots with Long Rest recovery note
- **Spell Details**: School, casting time, range, components, duration, description

### Character Summary Display
- **Complete Character Sheet**: All stats, proficiencies, features, spells
- **Pre-Calculated Values**: All values calculated by CharacterBuilder's `to_character()` method
  - Skill modifiers (all 18 skills)
  - Saving throws (all 6 abilities)
  - Combat stats (AC options, initiative, speed, HP)
  - Weapon attacks (attack bonus, damage, properties, mastery)
  - Proficiency bonus
  - Ability modifiers
- **Organized Sections**: Grouped by category (class, subclass, species, background, feats)
- **Proficiencies**: Weapons, armor (Shields always last), skills, languages
- **Ability Bonuses**: Special bonuses displayed with context (e.g., "+3 to Intelligence (Arcana, Religion)")
- **Feature Filtering**: "Choose..." placeholder features excluded from display
- **Equipment Categorization**: Data-driven weapon detection (checks weapons.json, not hardcoded keywords)

### PDF Character Sheet Export
- **PDF Generation**: Fill PDF character sheet from CharacterBuilder data
- **Field Mapping**: Configuration-driven field mapping (200+ PDF fields)
- **Custom Formatting**: Override system for special features (checkboxes, usage trackers)
- **Server-Side Calculations**: All stats calculated server-side before PDF generation
- **Download Route**: `/download-character-pdf` for downloading filled sheets
- **PDF Writer Module**: `utils/pdf_writer.py` (300+ lines)
- **Template System**: Support for {placeholders} in custom formatting

**Supported Sections**:
- Basic Info (name, class, level, background, species)
- Ability Scores (raw scores)
- Ability Modifiers (calculated +/- values)
- Saving Throws (with proficiency bonuses)
- Skills (all 18 skills with modifiers)
- Combat Stats (AC, initiative, speed, HP, hit dice)
- Proficiencies (weapons, armor, tools, languages)
- Spell Slots (by level)
- Features & Traits (with custom formatting)

**Custom Formatting Examples**:
- Second Wind → "Second Wind (uses: ☐ / 1 per short rest)"
- Action Surge → "Action Surge (uses: ☐ / 1 per short rest)"
- Channel Divinity → "Channel Divinity (uses: {uses} per long rest)"
- Rage → "Rage (uses: ☐☐☐ / 3 per long rest)"

### Data Validation
- **JSON Schemas**: Defined for classes and subclasses in `models/` directory
- **Schema Compliance**: All data files follow structured formats
- **Consistent Patterns**: Unified approach to choices, effects, scaling

## 📂 Project Structure

```
dnd-character-creator/
├── modules/                    # Core business logic
│   ├── character_builder.py   # Main character creation engine (1,206 lines)
│   ├── ability_scores.py      # Ability score management
│   ├── feature_manager.py     # Feature tracking
│   ├── hp_calculator.py       # Hit point calculations
│   ├── variant_manager.py     # Species variant system
│   └── data_loader.py         # JSON data loading
├── utils/                      # Utilities
│   ├── pdf_writer.py          # PDF character sheet generation (300+ lines)
│   └── inspect_pdf.py         # PDF field inspection tool
├── app.py                      # Flask web application (1,950+ lines)
├── data/                       # Structured game data
│   ├── classes/               # 12 base classes
│   ├── subclasses/            # Organized by class
│   ├── species/               # Base species (10 species)
│   ├── species_variants/      # Lineages (10 variants)
│   ├── backgrounds/           # 10 backgrounds
│   ├── feats/                 # Feat definitions
│   └── spells/
│       ├── definitions/       # Individual spell files
│       └── class_lists/       # Class spell list references
├── pdf_template/              # PDF character sheet template
│   ├── character-sheet.pdf    # Empty PDF form (200+ fields)
│   ├── field_mapping_config.json # Field mapping configuration
│   └── README.md              # PDF generation documentation
├── wiki_data/                 # Cached D&D 2024 wiki content
│   ├── classes/               # Raw wiki pages
│   └── subclasses/            # Raw wiki pages
├── models/                    # JSON schemas and validation
│   ├── class_schema.json      # Class data schema
│   ├── subclass_schema.json   # Subclass data schema
│   └── README.md              # Schema documentation
├── templates/                 # Jinja2 templates
├── static/                    # CSS, images
└── docs/                      # Documentation
    ├── ARCHITECTURE.md        # System architecture overview
    ├── FEATURE_EFFECTS.md     # Effects system documentation
    ├── FEATURE_SCALING.md     # Feature scaling system
    ├── spell_migration_guide.md # Spell system migration
    ├── character_builder_guide.md # CharacterBuilder usage
    └── character_sheet_model_plan.md # Character model structure
```

## 🔧 Technical Architecture

### CharacterBuilder Engine
**Location**: `modules/character_builder.py`

**Core Methods**:
- `apply_choice(key, value)` - Apply single choice
- `apply_choices(dict)` - Batch apply choices
- `to_json()` - Export flattened character dict for templates

**Character Data Structure**:
```python
{
    'name': str,
    'species': str,
    'lineage': str,
    'class': str,
    'subclass': str,
    'background': str,
    'level': int,
    'alignment': str,
    'ability_scores': {...},
    'features': {
        'class': [...],
        'subclass': [...],
        'species': [...],
        'lineage': [...],
        'background': [...],
        'feats': [...]
    },
    'spells': {
        'cantrips': [...],
        'prepared': [...],
        'known': [...],
        'slots': {...}
    },
    'spell_metadata': {
        'spell_name': {'source': 'species|subclass', 'once_per_day': bool}
    },
    'proficiencies': {
        'weapons': [...],
        'armor': [...],
        'skills': [...],
        'languages': [...],
        'saving_throws': [...]
    },
    'choices_made': {...}  # All user selections
}
```

### Data Flow
1. **User Input** → Flask route handler
2. **Route** → `CharacterBuilder.apply_choice()`
3. **Builder** → Loads data from JSON → Processes effects → Updates character state
4. **State** → Saved to session (pickled CharacterBuilder)
5. **Display** → `builder.to_json()` → Flattens for templates → Renders HTML

### Effects Processing
1. Feature loaded from JSON with `effects` array
2. `_apply_trait_effects()` iterates through effects
3. `_apply_effect()` dispatches to specific handlers by type
4. Character state updated (spells, proficiencies, bonuses, etc.)
5. Feature description enhanced (spell tables, choices, etc.)
6. Feature added to `character['features'][category]`

## 📊 Current Data Coverage

### Complete & Tested
- ✅ **Cleric**: All features, Divine Order, Light Domain, scaling
- ✅ **Elf Lineages**: High Elf, Drow, Wood Elf (unified spell format)
- ✅ **Backgrounds**: 10 backgrounds with ability bonuses and features
- ✅ **Spell System**: Unified effects-based granting

### Implemented But Needs Verification
- 🟨 **Other Classes**: 11 classes (Fighter, Wizard, Rogue, etc.) - need testing
- 🟨 **Other Subclasses**: Multiple subclasses per class - need testing
- 🟨 **Other Species**: 9 species (Dwarf, Human, Tiefling, etc.) - need testing
- 🟨 **Other Lineages**: Need to unify spell format like Elf lineages

### Known Issues
- ⚠️ **Druid**: Mentions non-existent 2024 abilities - needs data regeneration
- ⚠️ **Tiefling Variants**: Need testing and possible fixes
- ⚠️ **Spellcasting Ability Choice**: Lineages offer INT/WIS/CHA choice - not implemented in wizard

## 🎯 Next Steps

### High Priority
1. **Missing Spell Definitions**: Create files for all referenced spells (Arcane Eye, Wall of Fire, Flame Strike, Scrying, etc.)
2. **Spellcasting Ability Choice**: Implement wizard step for species that offer INT/WIS/CHA choice
3. **Druid Data**: Regenerate from D&D 2024 sources
4. **Tiefling Variants**: Test and fix if needed

### Medium Priority
1. **Conflict Resolution**: Detect duplicate skills/cantrips and offer alternatives
2. **Other Class Scaling**: Apply scaling system to Rogue, Barbarian, Monk, etc.
3. **Data Validation**: Automated validation against schemas
4. **Comprehensive Testing**: Test all classes, subclasses, species combinations

### Future Enhancements
1. **Spell Preparation**: Interface for choosing prepared spells from class list
2. **PDF Export**: Character sheet and spell cards
3. **Multiclassing**: Support for multiclass characters
4. **Rest Mechanics**: Track resource usage and recovery
5. **Homebrew Support**: Interface for custom content

## 📝 Documentation Status

### Up-to-Date
- ✅ `ARCHITECTURE.md` - System architecture
- ✅ `FEATURE_EFFECTS.md` - Effects system reference
- ✅ `FEATURE_SCALING.md` - Scaling system
- ✅ `.github/copilot-instructions.md` - Development guidelines
- ✅ `things_to_fix.md` - TODO list
- ✅ `CURRENT_STATE.md` - This file

### Needs Update
- 🟨 `character_builder_guide.md` - Usage examples could be expanded
- 🟨 `character_sheet_model_plan.md` - May be outdated

## 🧪 Testing

### Coverage
- ✅ CharacterBuilder basic operations
- ✅ Effects system (all types)
- ✅ Flask wizard flow (class → summary)
- ✅ Cleric + Light Domain
- ✅ Spell display and badges
- ✅ Proficiency display
- ✅ Feature display with tables

### Not Yet Tested
- ⏸️ Other classes in wizard
- ⏸️ Multiclass scenarios
- ⏸️ Edge cases (duplicate proficiencies, etc.)
- ⏸️ All subclass combinations

## 📈 Code Metrics

- **Total Lines**: ~15,000 lines
- **Core Engine**: CharacterBuilder (1,206 lines)
- **Flask App**: 1,912 lines
- **Code Removed**: 1,702 lines (old API, rebuild script, CLI)
- **Data Files**: 100+ JSON files
- **Documentation**: 8 markdown files

## 🔐 Design Principles

1. **Data-Driven**: All game mechanics in JSON, not code
2. **Effects-Based**: No hardcoded feature logic
3. **Single Source**: CharacterBuilder is the only truth
4. **Consistent Format**: Same patterns across all data
5. **Template-Friendly**: Flattened data structure for display
6. **Extensible**: New features added via JSON without code changes
