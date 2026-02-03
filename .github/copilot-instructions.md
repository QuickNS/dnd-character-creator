# Copilot Instructions for D&D 2024 Character Creator

## 🎯 Core Principles

### D&D 2024 Edition Compliance
- **ALWAYS** verify that features, mechanics, and rules come from D&D 2024 (One D&D), not 2014
- **NEVER** assume backwards compatibility with 2014 rules without explicit verification
- When in doubt, research the specific mechanic in official D&D 2024 sources
- Common 2014 vs 2024 differences to watch for:
  - Species no longer have ability score increases (moved to backgrounds)
  - Dwarf variants (Hill/Mountain) don't exist in 2024
  - Many spells, features, and mechanics have been updated or replaced
  - Class features and progression may differ significantly

# Reference Data

## Data Sources Priority (Use in this order)

1. **Primary Source**: `data/` directory - Application data files (structured JSON for character creation)
2. **Cached Source**: `wiki_data/` directory - Raw wiki content cached locally (text + HTML from D&D 2024 wiki)
3. **Live Source**: http://dnd2024.wikidot.com/ - Only use when data is missing from cache

### Data Source Workflow

When you need D&D 2024 data:

```
1. Check data/ directory first
   ├─ If exists and correct → Use it
   └─ If missing or needs update → Go to step 2

2. Check wiki_data/ directory (cached wiki content)
   ├─ If exists → Parse cached data and transform to data/ format
   └─ If missing → Go to step 3

3. Fetch from live wiki (http://dnd2024.wikidot.com/)
   ├─ Fetch data
   ├─ Save to wiki_data/ (cache for future use)
   └─ Transform to data/ format
```

### Using Cached Wiki Data

- **ALWAYS** check `wiki_data/classes/` and `wiki_data/subclasses/` before fetching from the wiki
- Cached files contain raw wiki content with timestamps (`fetched_at` field)
- Parse the `content.text` or `content.html` fields to extract D&D 2024 data
- This avoids repeated network requests and respects the wiki's rate limits

### Fetching New Data

If data is not in cache, use the `update_classes.py` script:

```bash
# Fetch only missing data for a specific class
python update_classes.py --class wizard

# Overwrite existing cached data
python update_classes.py --class wizard --overwrite

# Fetch all missing data
python update_classes.py

# Overwrite all cached data
python update_classes.py --overwrite
```

### Wiki URL Patterns

When fetching from live wiki (only if not cached):
- Classes: http://dnd2024.wikidot.com/barbarian:main (replace "barbarian" with class name in lowercase)
- Subclasses: http://dnd2024.wikidot.com/barbarian:path-of-the-berserker (format: `{class}:{subclass-name}`)
- Backgrounds: http://dnd2024.wikidot.com/background:acolyte
- Species: http://dnd2024.wikidot.com/species:elf
- Feats: http://dnd2024.wikidot.com/feat:alert
  
### Modular Architecture
- **Each aspect of character creation must be in its own module** with clear separation of concerns
- **Single Responsibility**: Each module handles one specific domain (ability scores, features, HP, variants, etc.)
- **Dependency Injection**: Modules should not directly instantiate other modules where possible
- **Interface Contracts**: Clear, documented APIs between modules
- **No Circular Dependencies**: Maintain clean dependency hierarchy

#### Current Module Structure
```
modules/
├── ability_scores.py       # Ability score management and calculations
├── feature_manager.py      # Feature tracking, parsing, and application
├── hp_calculator.py        # Hit point calculations with all bonuses
├── variant_manager.py      # Species variant system
└── character.py           # Character composition using above modules
```

### Extensibility Requirements
- **JSON-Driven Configuration**: All game data (classes, species, spells, etc.) in JSON files
- **Plugin Architecture**: New features should be addable without modifying core code
- **Pattern-Based Parsing**: Use configurable patterns for trait/feature recognition
- **Version Compatibility**: Support for future D&D content additions
- **Modular Data Loading**: Each data type in separate, clearly organized directories

#### Data Organization
```
data/                       # Application-ready structured data
├── classes/                # Character class definitions
├── subclasses/            # Subclass definitions organized by class
│   ├── fighter/
│   ├── wizard/
│   └── ...
├── species/               # Core species data (without variants)
├── species_variants/      # Species variant definitions where applicable
├── backgrounds/           # Background definitions with ability score increases
├── feats/                # Feat definitions with Choice Reference System
├── spells/               # Spell lists organized by class and level
│   ├── wizard_cantrips.json
│   ├── wizard_spells.json
│   ├── cleric_cantrips.json
│   └── ...
└── trait_patterns.json   # Configurable trait parsing patterns

wiki_data/                 # Cached wiki content (raw HTML/text)
├── classes/               # Raw wiki pages for base classes
│   ├── wizard.json        # Contains 'content.text' and 'content.html'
│   ├── fighter.json
│   └── ...
└── subclasses/           # Raw wiki pages for subclasses
    ├── wizard/
    │   ├── evoker.json
    │   └── ...
    └── fighter/
        ├── battle-master.json
        └── ...

models/                    # Data schemas and validation
├── class_schema.json      # JSON Schema for class data files
├── subclass_schema.json   # JSON Schema for subclass data files
└── README.md             # Schema documentation and examples
```

### Data Schema Compliance

**CRITICAL**: All data files MUST comply with the schemas defined in `models/` directory.

#### Class Data Files (`data/classes/*.json`)
- **Schema**: [models/class_schema.json](../models/class_schema.json)
- **Required Fields**: name, description, hit_die, primary_ability, saving_throw_proficiencies, subclass_selection_level, proficiency_bonus_by_level, features_by_level
- **Features Format**: `features_by_level` maps level (string) → **OBJECT** of feature_name → description (SAME AS SUBCLASSES)
  - ❌ **NEVER** use arrays: `"1": ["Feature1", "Feature2"]`
  - ✅ **ALWAYS** use objects: `"1": {"Feature1": "Description", "Feature2": "Description"}`
- **Spell Slots Format**: Arrays of exactly 9 integers (spell levels 1-9)

**Example Class Structure**:
```json
{
  "name": "Wizard",
  "description": "Masters of arcane magic",
  "hit_die": 6,
  "primary_ability": "Intelligence",
  "saving_throw_proficiencies": ["Intelligence", "Wisdom"],
  "subclass_selection_level": 3,
  "features_by_level": {
    "1": {
      "Spellcasting": "Cast spells using Intelligence as your spellcasting ability.",
      "Ritual Adept": "Cast Ritual spells from spellbook without preparing.",
      "Arcane Recovery": "Regain spell slots equal to half your Wizard level on Short Rest."
    },
    "2": {
      "Scholar": "Gain Expertise in Arcana, History, Investigation, Medicine, Nature, or Religion."
    }
  },
  "spell_slots_by_level": {
    "1": [2, 0, 0, 0, 0, 0, 0, 0, 0]
  }
}
```

#### Subclass Data Files (`data/subclasses/{class}/*.json`)
- **Schema**: [models/subclass_schema.json](../models/subclass_schema.json)
- **Required Fields**: name, class, description, source, features_by_level
- **Features Format**: `features_by_level` maps level (string) → **OBJECT** of feature_name → description
  - ❌ **NEVER** use arrays: `"3": ["Feature1", "Feature2"]`
  - ✅ **ALWAYS** use objects: `"3": {"Feature1": "Description", "Feature2": "Description"}`

**Example Subclass Structure**:
```json
{
  "name": "College of Lore",
  "class": "Bard",
  "description": "Bards who seek knowledge",
  "source": "Player's Handbook 2024",
  "features_by_level": {
    "3": {
      "Bonus Proficiencies": "Gain proficiency in three skills.",
      "Cutting Words": "Subtract Bardic Inspiration from enemy rolls."
    },
    "6": {
      "Magical Discoveries": "Learn two spells from other class lists."
    }
  }
}
```

#### Schema Validation
Before using any generated data:
1. Check against the schema in `models/` directory
2. Verify all required fields are present
3. Ensure correct data types (especially objects vs arrays)
4. Review examples in `models/README.md`

### Choice Reference System
The system uses a generic choice reference architecture to handle all character choices through JSON configuration:

#### Choice Types Supported
- **Internal References**: Choices from lists within the same JSON file (e.g., Battle Master maneuvers)
- **External Static References**: Choices from specific external files (e.g., Wizard spells for Eldritch Knight)
- **External Dynamic References**: File/list determined by previous choice (e.g., Magic Initiate spell class selection)
- **Fixed Lists**: Simple option lists defined inline (e.g., ability score choices)

#### Choice Reference Schema
```json
{
  "choices": {
    "type": "select_multiple|select_single|select_or_replace",
    "count": 3,
    "name": "choice_identifier",
    "source": {
      "type": "internal|external|external_dynamic|fixed_list",
      "list": "list_name",
      "file": "path/to/file.json",
      "file_pattern": "spells/{class}_spells.json",
      "depends_on": "previous_choice_name",
      "options": ["Option1", "Option2"]
    },
    "restrictions": ["filter_criteria"],
    "optional": true,
    "additional_choices_by_level": {
      "7": {"count": 2, "replace_allowed": true}
    }
  }
}
```

#### Implementation Rules
1. **No Hardcoded Choice Logic**: All choice behavior must be defined in JSON configuration
2. **External References**: Spell lists, maneuver lists, and other choice sources should be in separate files
3. **Dynamic Resolution**: Choice files determined at runtime based on user selections
4. **Level Progression**: Natural handling of choices that expand at higher levels
5. **Replacement Support**: Features that allow changing choices (e.g., cantrip swapping on long rest)

### Output Format Goals
The system must be designed from the ground up to support multiple output formats:

#### 1. JSON Export
- Complete character data in structured JSON format
- Separate character state from calculated values
- Include metadata for version tracking and compatibility

#### 2. Character Sheet PDF
- Professional, print-ready character sheets
- Support for official D&D 2024 character sheet layouts
- Automatic field population with character data
- Equipment, spells, and features properly formatted

#### 3. Modular Cards
- **Character Info Card**: Basic stats, abilities, proficiencies
- **Weapon Cards**: Individual weapon statistics and special properties
- **Armor Cards**: Armor class, properties, and special effects
- **Spell Cards**: Spell details, components, and effects
- **Feature Cards**: Class features, traits, and abilities
- **Equipment Cards**: Non-combat items and tools

#### Technical Requirements for Output Formats
```python
# Each module should provide structured data access
class Character:
    def to_json(self) -> dict
    def to_character_sheet_data(self) -> dict
    def to_card_data(self) -> dict

# Separate formatting concerns from data
class CharacterExporter:
    def export_json(character: Character) -> str
    def export_pdf(character: Character) -> bytes
    def export_cards(character: Character) -> dict[str, bytes]
```

## 🏗️ Implementation Guidelines

### Code Organization
- **Clear Naming**: Use descriptive names that reflect D&D 2024 terminology
- **Type Hints**: All functions and methods must have proper type annotations
- **Documentation**: Docstrings explaining D&D rule references where applicable
- **Error Handling**: Graceful handling of invalid data or missing files

### Data Validation
- **Schema Validation**: JSON data should follow defined schemas
- **Rule Validation**: Ensure character builds follow D&D 2024 rules
- **Dependency Checking**: Verify prerequisites for features, feats, etc.
- **Level Validation**: Ensure features unlock at correct levels

### Testing Strategy
- **Unit Tests**: Each module tested independently
- **Integration Tests**: Character creation workflow testing
- **Rule Compliance Tests**: Verify D&D 2024 rule accuracy
- **Output Format Tests**: Verify all export formats work correctly

### Performance Considerations
- **Lazy Loading**: Load data files only when needed
- **Caching**: Cache parsed data for repeated use
- **Efficient Calculations**: Minimize redundant calculations
- **Memory Management**: Clean up temporary objects

## 📋 Development Workflow

### Before Adding New Features
1. **Research**: Verify the feature exists in D&D 2024 and understand its mechanics
2. **Design**: Plan which module(s) will handle the feature
3. **Data Structure**: Define JSON schema for any new data
4. **Implementation**: Write code following modular principles
5. **Testing**: Verify functionality and D&D 2024 compliance
6. **Documentation**: Update relevant documentation

### Code Review Checklist
- [ ] Uses D&D 2024 rules, not 2014
- [ ] Follows modular architecture principles
- [ ] Includes proper type hints and documentation
- [ ] Supports future extensibility
- [ ] Compatible with all target output formats
- [ ] Includes appropriate error handling
- [ ] Has corresponding tests

### Common Patterns

#### Choice Reference Implementation
```python
def resolve_choice_source(choice_config: dict, previous_choices: dict = None) -> list:
    """Resolve choice options from various source types"""
    source = choice_config.get("source", {})
    source_type = source.get("type")
    
    if source_type == "internal":
        # Reference list within same JSON file
        return self._get_internal_list(source["list"])
    elif source_type == "external":
        # Reference specific external file
        return self._load_external_list(source["file"], source["list"])
    elif source_type == "external_dynamic":
        # Dynamic file based on previous choice
        file_path = source["file_pattern"].format(**previous_choices)
        return self._load_external_list(file_path, source["list"])
    elif source_type == "fixed_list":
        # Direct option list
        return source["options"]
    
    return []

def apply_choice_restrictions(options: list, restrictions: list) -> list:
    """Filter options based on restrictions (e.g., spell schools)"""
    if not restrictions:
        return options
    
    return [opt for opt in options if meets_restrictions(opt, restrictions)]
```

#### Spell List File Format
```python
# data/spells/wizard_cantrips.json
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

#### Feature with Choices
```python
# In JSON data files
{
  "Combat Superiority": {
    "description": "You learn maneuvers...",
    "choices": {
      "type": "select_multiple",
      "count": 3,
      "source": {"type": "internal", "list": "maneuvers"},
      "additional_choices_by_level": {
        "7": {"count": 2, "replace_allowed": true}
      }
    }
  }
}
```

#### Loading Game Data
```python
def _load_data(self, data_type: str) -> Dict[str, Dict[str, Any]]:
    """Load data following standard pattern"""
    data_dir = self.data_dir / data_type
    data = {}
    
    if data_dir.exists():
        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    file_data = json.load(f)
                    name = file_data.get("name")
                    if name:
                        data[name] = file_data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load {json_file}: {e}")
    
    return data
```

#### Feature Application
```python
def apply_feature(self, feature_name: str, feature_data: dict, source: str) -> None:
    """Apply feature following standard pattern"""
    # Validate feature data
    # Parse feature effects
    # Apply mechanical bonuses
    # Track feature source
    # Log for debugging
```

## 🎮 D&D 2024 Specific Guidelines

### Data File Standards
- **Always use Choice Reference System** for any feature that involves player selection
- **Separate choice lists** from feature descriptions (e.g., maneuvers in separate list)
- **External spell files** must follow standard schema with school, components, description
- **Level progression choices** should use `additional_choices_by_level` structure
- **Replacement mechanics** (like cantrip swapping) should use `replace_allowed: true`

### Choice Reference Examples

#### Battle Master Maneuvers
```json
{
  "Combat Superiority": {
    "description": "You learn three maneuvers...",
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
  },
  "maneuvers": {
    "Disarming Attack": "When you hit a creature...",
    "Feinting Attack": "As a Bonus Action..."
  }
}
```

#### Magic Initiate Feat
```json
{
  "choices": [
    {
      "type": "select_single",
      "name": "spell_list_class",
      "source": {"type": "fixed_list", "options": ["Wizard", "Cleric", "Druid"]}
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

#### Eldritch Knight Spells with Restrictions
```json
{
  "Spellcasting": {
    "description": "You augment your martial prowess...",
    "choices": [
      {
        "type": "select_multiple",
        "count": 2,
        "name": "cantrips",
        "source": {"type": "external", "file": "spells/wizard_cantrips.json", "list": "cantrips"}
      },
      {
        "type": "select_multiple",
        "count": 3,
        "name": "1st_level_spells",
        "source": {"type": "external", "file": "spells/wizard_spells.json", "list": "1st_level"},
        "restrictions": ["Abjuration", "Evocation"]
      }
    ]
  }
}
```

### Species System
- No ability score increases from species (use backgrounds instead)
- Focus on traits, resistances, and special abilities
- Variants only exist for: Elf, Tiefling, Dragonborn, Gnome (verify others)
- Each species provides consistent base features

### Class System
- Use 2024 class progression tables
- Verify subclass availability and features
- Implement proper spell slot progression for casters
- Handle multiclassing according to 2024 rules

### Background System
- Backgrounds provide ability score increases (+2/+1 or +1/+1/+1)
- Include skill proficiencies and special features
- Support background-specific feat options

### Feat System
- Implement 2024 feat prerequisites and effects
- Support level 1 feat option from backgrounds
- Handle feat scaling and improvements

## 🔄 Continuous Improvement

### Regular Reviews
- Monitor D&D 2024 updates and errata
- Refactor modules as patterns emerge
- Optimize for new output format requirements
- Update data schemas as needed

### Future Considerations
- Digital integration (D&D Beyond compatibility)
- Homebrew content support
- Campaign-specific customizations
- Multi-character party management

---

**Remember**: When implementing any feature, always ask "Does this follow D&D 2024 rules?" and "How does this fit into our modular, extensible architecture?"