# App.py Modularization Plan

## Overview
Refactor app.py (1500+ lines) into modular blueprint-based structure for better maintainability.

## New Structure

```
dnd-character-creator/
├── app.py (main application file - simplified)
├── routes/
│   ├── __init__.py
│   ├── main.py (✅ CREATED)
│   ├── class_selection.py
│   ├── class_features.py
│   ├── background.py
│   ├── species.py
│   ├── ability_scores.py
│   └── summary.py
├── utils/
│   ├── __init__.py
│   └── choice_resolver.py (✅ CREATED)
└── modules/ (existing)
```

## Route Modules

### 1. main.py (✅ CREATED)
**Lines: 141-200, 1506-1524**
- `/` - index
- `/create` - create_character
- `/reset` - reset
- `/test-session` - test_session

### 2. class_selection.py
**Lines: 201-321**
- `/choose-class` - choose_class
- `/select-class` - select_class (POST)
- `/choose-subclass` - choose_subclass
- `/select-subclass` - select_subclass (POST)

### 3. class_features.py
**Lines: 322-786**
- `/class-choices` - class_choices
- `/submit-class-choices` - submit_class_choices (POST)

This is the LARGEST module (464 lines) with complex logic for:
- Displaying class and subclass features
- Resolving choice options
- Processing submitted choices
- Adding features to character

### 4. background.py
**Lines: 787-895**
- `/choose-background` - choose_background
- `/select-background` - select_background (POST)

### 5. species.py
**Lines: 896-1148**
- `/choose-species` - choose_species
- `/select-species` - select_species (POST)
- `/choose-species-traits` - choose_species_traits
- `/select-species-traits` - select_species_traits (POST)
- `/choose-lineage` - choose_lineage
- `/select-lineage` - select_lineage (POST)

### 6. languages.py
**Lines: 1149-1221**
- `/choose-languages` - choose_languages
- `/select-languages` - select_languages (POST)

### 7. ability_scores.py
**Lines: 1222-1415**
- `/assign-ability-scores` - assign_ability_scores
- `/submit-ability-scores` - submit_ability_scores (POST)
- `/background-bonuses` - background_bonuses
- `/submit-background-bonuses` - submit_background_bonuses (POST)
- `/choose-alignment` - choose_alignment
- `/select-alignment` - select_alignment (POST)

### 8. summary.py
**Lines: 1451-1505**
- `/character-summary` - character_summary
- `/download-character` - download_character
- `/api/character-sheet` - get_character_sheet_api

## Utilities Module

### choice_resolver.py (✅ CREATED)
**Lines: 63-139**
- `resolve_choice_options()` - Resolve choice options from Choice Reference System
- `get_option_descriptions()` - Get detailed descriptions for options
- `load_external_choice_list()` - Load choices from external JSON files

## Implementation Steps

### Phase 1: Create Route Blueprints
1. ✅ Create `routes/` and `utils/` directories
2. ✅ Create `routes/main.py` with basic routes
3. ✅ Create `utils/choice_resolver.py` with helper functions
4. Create remaining route modules (class_selection, class_features, etc.)

### Phase 2: Update app.py
1. Remove route definitions (keep only imports and app initialization)
2. Import and register all blueprints
3. Keep shared instances (character_creator, character_sheet_converter)
4. Update all `url_for()` calls to use blueprint prefixes (e.g., `url_for('main.index')`)

### Phase 3: Update Templates
1. Update all `url_for()` calls in templates to use blueprint names:
   - `url_for('index')` → `url_for('main.index')`
   - `url_for('choose_class')` → `url_for('class_selection.choose_class')`
   - etc.

### Phase 4: Testing
1. Test each route after migration
2. Verify session management works across blueprints
3. Check that all redirects work correctly
4. Verify form submissions

## Shared Resources

The following need to be accessible across all blueprints:

1. **CharacterCreator instance** - Pass via `current_app` or create in each blueprint
2. **CharacterSheetConverter instance** - Same as above
3. **Session management** - Flask's session works across blueprints automatically

### Solution: Application Factory Pattern

```python
# app.py
from flask import Flask
from modules.character_creator import CharacterCreator
from modules.character_sheet_converter import CharacterSheetConverter

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'
    
    # Store shared instances in app.config
    app.config['CHARACTER_CREATOR'] = CharacterCreator()
    app.config['SHEET_CONVERTER'] = CharacterSheetConverter()
    
    # Register blueprints
    from routes.main import main_bp
    from routes.class_selection import class_selection_bp
    # ... register all blueprints
    
    app.register_blueprint(main_bp)
    app.register_blueprint(class_selection_bp)
    # ... register all
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

```python
# In route modules
from flask import current_app

def some_route():
    character_creator = current_app.config['CHARACTER_CREATOR']
    # use character_creator...
```

## Benefits

1. **Maintainability**: Each module focuses on one aspect of character creation
2. **Testability**: Easier to unit test individual route modules
3. **Readability**: Smaller files are easier to understand
4. **Collaboration**: Multiple developers can work on different modules
5. **Debugging**: Easier to locate and fix issues

## Current Status

- ✅ Directories created (`routes/`, `utils/`)
- ✅ `utils/choice_resolver.py` created with helper functions
- ✅ `routes/main.py` created with basic routes
- ⏳ Remaining route modules need to be created
- ⏳ app.py needs to be refactored to use blueprints
- ⏳ Templates need `url_for()` updates

## Next Steps

1. Create remaining route blueprint files
2. Refactor app.py to register blueprints
3. Update template `url_for()` calls
4. Test thoroughly
