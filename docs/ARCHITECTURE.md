# D&D 2024 Character Creator - Architecture Overview

## System Components

### 1. **CharacterBuilder** - `modules/character_builder.py`
**Purpose**: The single, authoritative character creation engine.

**Key Methods**:
- `apply_choice(key, value)` - Apply a single choice with all its effects
- `apply_choices(choices_dict)` - Apply multiple choices at once
- `to_json()` - Export complete character as dictionary with flattened proficiencies
- `set_species()`, `set_class()`, etc. - Direct property setters

**Character Data Structure**:
- `character_data['spells']['cantrips']` - Known cantrips
- `character_data['spells']['prepared']` - Always prepared spells (domain + species)
- `character_data['spell_metadata']` - Tracks spell sources (for once-per-day display)
- `character_data['proficiencies']['weapons']`, `['armor']`, `['skills']`, `['languages']`
- `character_data['features'][category]` - Features organized by source (class, subclass, species, lineage, background, feats)

**Usage in Flask Wizard** (incremental):
```python
builder = CharacterBuilder()
builder.apply_choice('species', 'Dwarf')
builder.apply_choice('class', 'Cleric')
builder.apply_choice('divine_order', 'Protector')
# ... continue as user makes choices
character = builder.to_json()  # Flattens proficiencies for templates
```

**Usage in Quick Test / Batch** (all at once):
```python
builder = CharacterBuilder()
builder.apply_choices({
    'species': 'Dwarf',
    'class': 'Cleric',
    'level': 1,
    'divine_order': 'Protector',
    'skill_choices': ['Insight', 'Persuasion'],
    # ... all choices at once
})
character = builder.to_json()
```

**Both approaches produce identical results** - guaranteed consistency.

### 2. **Data Loading** - `modules/data_loader.py`
**Purpose**: Load all game data from JSON files in the `data/` directory.

**Class**: `DataLoader`
- Loads classes, subclasses, backgrounds, species, feats from JSON files
- Provides clean interface for accessing D&D 2024 game data
- Used by Flask web wizard

**Usage**:
```python
from modules.data_loader import DataLoader

data_loader = DataLoader()
classes = data_loader.classes
subclasses = data_loader.get_subclasses_for_class("Wizard")
```

### 3. **Flask Web Wizard** - `app.py`
**Purpose**: Web-based character creation wizard.

**Architecture**:
- Uses CharacterBuilder for all character operations
- Session stores CharacterBuilder state (serialized via pickle)
- Step-by-step guided creation
- Each form submission calls `builder.apply_choice()`

**Routes**:
- `/` - Landing page
- `/choose-class` - Class selection
- `/class-choices` - Class feature choices (skills, spells, divine order, etc.)
- `/choose-subclass` - Subclass selection
- `/choose-background` - Background selection
- `/choose-species` - Species selection
- `/choose-lineage` - Lineage/variant selection (if applicable)
- `/choose-languages` - Language selection
- `/assign-abilities` - Ability score assignment
- `/background-bonuses` - Background ability score bonuses
- `/character-summary` - Final character sheet display

**Session Helpers**:
```python
def get_builder_from_session() -> CharacterBuilder:
    """Retrieve CharacterBuilder from session"""
    
def save_builder_to_session(builder: CharacterBuilder):
    """Save CharacterBuilder to session"""
```

### 4. **Effects System** - Core Architecture Pattern
**Purpose**: Data-driven mechanical benefits without hardcoding.

**How It Works**:
1. Features define `effects` array in JSON
2. CharacterBuilder's `_apply_effect()` processes each effect
3. Effects modify character state (spells, proficiencies, bonuses, etc.)
4. Display layer reads from character state

**Example - Domain Spells**:
```json
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

**Result**:
- Spells added to `character['spells']['prepared']`
- Auto-generates HTML table showing spell availability by level
- Displays in Spellcasting section with "Always Prepared" badge

## Data Flow

### Web Wizard Flow
```
User Input → Flask Routes → CharacterBuilder.apply_choice() 
  → Effects Processing → Character State Update 
  → Session Storage → to_json() → Templates → Display
```

### Spell Display Flow
```
Feature with grant_spell effects → _apply_trait_effects() 
  → Adds to character['spells']['prepared']
  → Adds to spell_metadata (for once-per-day tracking)
  → _gather_character_spells() collects all spells
  → Template renders with badges (Always Prepared / 1/Day)
```

### Feature Display Flow
```
Feature Data → _apply_trait_effects()
  → Checks for grant_spell effects at multiple levels
  → Generates HTML table if multiple levels
  → Stores in character['features'][category]
  → Template renders with | safe filter (allows HTML)
```
choices_made.json → CharacterBuilder.apply_choices() → Character JSON
```

**All flows use the same CharacterBuilder engine** - guaranteed identical results.

## Character Data Structure

The application uses a **single, canonical character representation** based on CharacterBuilder's flat structure:

```json
{
  "name": "Character Name",
  "species": "Dwarf",
  "lineage": "Mountain Dwarf",
  "class": "Fighter",
  "subclass": "Champion",
  "background": "Soldier",
  "level": 3,
  "ability_scores": {"Strength": 16, "Dexterity": 14, ...},
  "speed": 30,
  "darkvision": 120,
  "creature_type": "Humanoid",
  "size": "Medium",
  "proficiencies": {
    "armor": [...],
    "weapons": [...],
    "skills": [...],
    "languages": [...]
  },
  "spells": {
    "cantrips": [...],
    "known": [...],
    "prepared": [...]
  },
  ...
}
```

**Note**: Physical attributes like `speed`, `darkvision`, `creature_type`, and `size` are stored at the top level (flat structure), not nested under `physical_attributes`. This ensures consistency across all parts of the application.

## Why This Architecture?

### Separation of Concerns
- **DataLoader**: Pure data loading, no business logic
- **CharacterBuilder**: All character creation logic, single source of truth
- **Flask Wizard**: Web UI and user flow management
- **REST API**: Stateless API wrapper around CharacterBuilder

### Single Code Path
- Wizard and API both use CharacterBuilder
- Incremental (wizard) or batch (API) application of choices
- Same CharacterBuilder → Same results → No inconsistencies

### Extensibility
- Add new features to `CharacterBuilder` → Automatically available everywhere
- Update JSON data files → Automatically reflected in all interfaces
- Add new UI flows → Same CharacterBuilder underneath

## PDF Character Sheet Generation

### PDF Writer Module - `utils/pdf_writer.py`
**Purpose**: Generate filled PDF character sheets from character data.

**Key Class**: `PDFCharacterSheetWriter`

**Methods**:
- `create_character_sheet(character)` - Generate filled PDF from character dict
- `_prepare_character_data(character)` - Transform character data to PDF field values
- `_format_features(features)` - Apply custom formatting overrides
- `_calculate_modifier(score)` - Calculate ability modifier
- `_format_modifier(modifier)` - Format with +/- sign

**Configuration Files**:
- `pdf_template/field_mapping_config.json` - Maps PDF fields to character attributes
- `pdf_template/character-sheet.pdf` - Empty PDF form template

**Field Mapping Structure**:
```json
{
  "basic_info": {
    "CharacterName": "name",
    "ClassLevel": "class_level",
    "Background": "background"
  },
  "ability_scores": {
    "STR": "abilities.Strength",
    "DEX": "abilities.Dexterity"
  },
  "custom_formatting": {
    "Second Wind": "Second Wind (uses: ☐ / 1 per short rest)",
    "Action Surge": "Action Surge (uses: ☐ / 1 per short rest)"
  }
}
```

**Custom Formatting System**:
- Override default feature text for specific features
- Support for checkbox trackers `☐` for limited-use abilities
- Template substitution: `{uses}` → actual uses value
- Example: "Second Wind" → "Second Wind (uses: ☐ / 1 per short rest)"

**Flask Integration**:
```python
@app.route('/download-character-pdf')
def download_character_pdf():
    builder = get_builder_from_session()
    character = builder.to_json()
    
    # Add calculated values
    character['combat_stats'] = {...}
    character['saving_throws'] = {...}
    character['skill_modifiers'] = {...}
    
    # Generate PDF
    pdf_bytes = generate_character_sheet_pdf(character)
    return send_file(io.BytesIO(pdf_bytes), ...)
```

**Data Flow**:
1. CharacterBuilder creates character dict
2. Character sheet converter adds calculated values
3. PDF writer transforms to field values
4. Apply custom formatting overrides
5. Fill PDF form fields
6. Return PDF bytes for download

**Advantages**:
- Reuses existing CharacterBuilder data
- Custom formatting for special features
- Consistent with JSON export
- All calculations server-side

## File Organization

```
modules/
├── data_loader.py          # Game data loading
├── character_builder.py    # SINGLE CHARACTER CREATION ENGINE
│   ├── apply_choice()      # Apply single choice
│   ├── apply_choices()     # Apply choice dictionary
│   └── to_json()           # Export character
├── hp_calculator.py        # Hit point calculations
├── character_sheet_converter.py  # Character sheet formatting
└── ...

utils/
├── pdf_writer.py           # PDF character sheet generation
├── inspect_pdf.py          # PDF field inspection tool
└── ...

pdf_template/
├── character-sheet.pdf     # Empty PDF form template
└── field_mapping_config.json  # Field mapping configuration

routes/
├── main.py                 # Main Flask routes (wizard)
├── class_selection.py      # Class selection routes
└── ...

app.py                      # Main Flask application (uses CharacterBuilder)
```

## Migration History

### Before (v1.0)
- CLI tool in interactive_character_creator.py
- rebuild_character_from_choices.py duplicated logic
- Multiple ways to create characters

### After (v2.0) - **Current Architecture**
- `CharacterBuilder` is the **single source of truth**
- `apply_choices()` method for batch operations
- `apply_choice()` method for incremental operations
- Wizard and API both use CharacterBuilder
- CLI tool removed
- rebuild module removed
- **One character format, one creation engine**

### PDF Export (v2.5) - **Current**
- PDF character sheet generation added
- Field mapping configuration system
- Custom formatting for features
- Server-side calculations included in PDF

## Future Improvements

1. **Refine PDF field mappings** - Verify actual PDF layout matches configuration
2. **Expand custom formatting** - Add more features with special formatting
3. **Multi-page PDF support** - Handle overflow for features/spells
4. **PDF optimization** - Compression and font embedding
5. **Spell card generation** - Separate PDF for spell cards
6. **Modular card exports** - Weapon cards, armor cards, etc.
