# Business Logic Refactoring Analysis
## Routes → CharacterBuilder Migration

This document identifies business logic currently in route modules that should be moved into the CharacterBuilder or related modules for better separation of concerns.

## Summary

**Routes should handle:** HTTP requests/responses, form data parsing, redirects, rendering templates  
**Builder should handle:** Character state, game rules, calculations, feature processing, data validation

---

## 1. languages.py - Language Selection Logic

### ❌ CURRENT (Lines 33-57)
```python
# Route module calculating languages
species_data = data_loader.species.get(character['species'], {})
class_data = data_loader.classes.get(character['class'], {})

base_languages = set(['Common'])

if 'languages' in species_data:
    base_languages.update(species_data['languages'])

if 'languages' in class_data:
    base_languages.update(class_data['languages'])

all_languages = ['Abyssal', 'Celestial', 'Common', ...]
available_languages = [lang for lang in all_languages if lang not in base_languages]
```

### ✅ SHOULD BE (CharacterBuilder)
```python
class CharacterBuilder:
    def get_language_options(self) -> dict:
        """Get base and available languages for character."""
        base_languages = self._calculate_base_languages()
        available_languages = self._calculate_available_languages(base_languages)
        return {
            'base_languages': sorted(base_languages),
            'available_languages': available_languages
        }
```

**Reason:** Language calculation is game rule logic, not HTTP handling.

---

## 2. ability_scores.py - Background ASI Options

### ❌ CURRENT (Lines 108-128)
```python
# Route module parsing background data
background_name = character['background']
background_data = data_loader.backgrounds.get(background_name, {})

total_points = 3
suggested = {}
ability_options = ["Strength", "Dexterity", ...]

if 'ability_score_increase' in background_data:
    asi_data = background_data['ability_score_increase']
    if 'suggested' in asi_data:
        suggested = asi_data['suggested']
    if 'options' in asi_data:
        bg_options = asi_data['options']
        ability_options = [ability for ability in [...] if ability in bg_options]
```

### ✅ SHOULD BE (CharacterBuilder)
```python
class CharacterBuilder:
    def get_background_asi_options(self) -> dict:
        """Get background ability score increase options."""
        background_name = self.character_data.get('background')
        # ... parse background data
        return {
            'total_points': 3,
            'suggested': suggested,
            'ability_options': ability_options
        }
```

**Reason:** Parsing game data structure is business logic, not presentation.

---

## 3. character_creation.py - Choice Reference System

### ❌ CURRENT (Lines 19-109)

**Multiple helper functions in route module:**
- `_resolve_choice_options()` - Resolves choices from internal/external/dynamic sources
- `_get_option_descriptions()` - Gets descriptions for choice options  
- `_load_external_choice_list()` - Loads external JSON choice data

### ✅ SHOULD BE (utils/choice_resolver.py or CharacterBuilder)
```python
class ChoiceResolver:
    """Handles the Choice Reference System for features."""
    
    def resolve_choice_options(self, choices_data: dict, character: dict, 
                               class_data: dict = None, subclass_data: dict = None) -> list:
        """Resolve choice options from various source types."""
        # Implementation from _resolve_choice_options
    
    def get_option_descriptions(self, feature_data: dict, choices_data: dict,
                               class_data: dict = None, subclass_data: dict = None) -> dict:
        """Get option descriptions from various sources."""
        # Implementation from _get_option_descriptions
    
    def load_external_choice_list(self, file_path: str, list_name: str) -> list:
        """Load choice options from external JSON file."""
        # Implementation from _load_external_choice_list
```

**Reason:** Core game system logic should not be in route handlers. These functions are reusable across multiple routes and should be centralized.

---

## 4. character_creation.py - Skill Selection Logic

### ❌ CURRENT (Lines 293-332)
```python
# Route module expanding "Any" skills
if 'skill_options' in class_data and 'skill_proficiencies_count' in class_data:
    skill_options = class_data['skill_options']
    if skill_options == ['Any'] or (len(skill_options) == 1 and skill_options[0] == 'Any'):
        skill_options = [
            'Acrobatics', 'Animal Handling', 'Arcana', 'Athletics', ...
        ]
    
    choices.append({
        'title': 'Skill Proficiencies',
        'type': 'skills',
        'options': skill_options,
        'count': class_data['skill_proficiencies_count'],
        # ...
    })
```

### ✅ SHOULD BE (CharacterBuilder)
```python
class CharacterBuilder:
    def get_skill_choice_options(self) -> dict:
        """Get skill proficiency options for character's class."""
        class_data = self.data_loader.classes.get(self.character_data['class'])
        skill_options = self._expand_skill_options(class_data.get('skill_options', []))
        return {
            'options': skill_options,
            'count': class_data.get('skill_proficiencies_count', 0)
        }
    
    def _expand_skill_options(self, skill_options: list) -> list:
        """Expand 'Any' to all D&D skills."""
        if skill_options == ['Any'] or (len(skill_options) == 1 and skill_options[0] == 'Any'):
            return self.ALL_SKILLS  # Class constant
        return skill_options
```

**Reason:** Feature option resolution is game logic, not HTTP handling.

---

## 5. character_creation.py - Feature Processing Logic

### ❌ CURRENT (Lines 335-448)

**Massive feature processing in route:**
- Loops through all levels 1 to character level
- Processes class features_by_level
- Processes subclass features_by_level
- Resolves choices for each feature
- Builds all_features_by_level structure
- Builds choices array for form

**~115 lines of complex business logic in the route handler**

### ✅ SHOULD BE (CharacterBuilder)
```python
class CharacterBuilder:
    def get_available_features_and_choices(self) -> dict:
        """Get all features and choices for character's level."""
        features_by_level = {}
        choices = []
        
        # Process class features
        self._process_class_features(features_by_level, choices)
        
        # Process subclass features
        if self.character_data.get('subclass'):
            self._process_subclass_features(features_by_level, choices)
        
        return {
            'features_by_level': features_by_level,
            'choices': choices
        }
    
    def _process_class_features(self, features_by_level: dict, choices: list):
        """Process class features for all levels up to character level."""
        # Implementation
    
    def _process_subclass_features(self, features_by_level: dict, choices: list):
        """Process subclass features for all levels up to character level."""
        # Implementation
```

**Reason:** Feature processing is core character creation logic and far too complex for a route handler.

---

## 6. character_creation.py - Core Traits Building

### ❌ CURRENT (Lines 451-521)
```python
# Route building display data
core_traits = []

primary_ability = class_data.get('primary_ability', '')
if isinstance(primary_ability, list):
    primary_ability_value = _human_join(primary_ability, conjunction="or")
else:
    primary_ability_value = str(primary_ability)
core_traits.append({"label": "Primary Ability", "value": primary_ability_value})

# ... many more trait calculations
```

### ✅ MIXED - Some should stay, some should move

Keep presentation helpers like `_human_join()` in routes, but move data aggregation:

```python
class CharacterBuilder:
    def get_core_traits_data(self) -> dict:
        """Get core trait data (not formatted for display)."""
        return {
            'primary_ability': self._get_primary_ability(),
            'hit_die': self._get_hit_die(),
            'saving_throws': self._get_saving_throw_proficiencies(),
            'weapon_proficiencies': self._get_all_weapon_proficiencies(),
            'armor_proficiencies': self._get_all_armor_proficiencies(),
            # ... etc
        }
```

**Reason:** Data aggregation is business logic; formatting for display can stay in routes.

---

## 7. character_creation.py - Nested Choice Detection

### ❌ CURRENT (Lines 523-634)
```python
# Scanning for grant_cantrip_choice effects
for choice_key, choice_value in choices_made.items():
    if not isinstance(choice_value, str):
        continue
        
    for data_key, data_dict in class_data.items():
        if isinstance(data_dict, dict) and choice_value in data_dict:
            option_data = data_dict[choice_value]
            if isinstance(option_data, dict) and 'effects' in option_data:
                for effect in option_data.get('effects', []):
                    if effect.get('type') == 'grant_cantrip_choice':
                        # Complex nested choice logic...
```

**~110 lines of complex effect scanning logic**

### ✅ SHOULD BE (CharacterBuilder or ChoiceResolver)
```python
class ChoiceResolver:
    def get_nested_choices(self, character_data: dict, class_data: dict) -> list:
        """Get all nested choices triggered by selected options."""
        nested_choices = []
        
        for option_effect in self._scan_selected_option_effects(character_data, class_data):
            if option_effect['type'] == 'grant_cantrip_choice':
                nested_choices.append(self._create_cantrip_choice(option_effect))
            # ... other effect types
        
        return nested_choices
```

**Reason:** Effect system logic is core business logic, not HTTP handling.

---

## 8. character_summary.py - Spell Gathering

### ❌ CURRENT (Lines 19-431)

**`_gather_character_spells()` function - 413 lines!**

Gathers spells from:
- Character effects (grant_cantrip, grant_spell)
- Prepared spells with metadata
- Known spells
- Class cantrips from choices
- Bonus cantrips from grant_cantrip_choice effects  
- Subclass cantrips from effects

### ✅ SHOULD BE (CharacterBuilder)
```python
class CharacterBuilder:
    def get_all_spells(self) -> dict:
        """Get all spells organized by level."""
        spells_by_level = {}
        
        self._gather_spells_from_effects(spells_by_level)
        self._gather_prepared_spells(spells_by_level)
        self._gather_known_spells(spells_by_level)
        self._gather_class_cantrips(spells_by_level)
        self._gather_bonus_cantrips(spells_by_level)
        self._gather_subclass_cantrips(spells_by_level)
        
        return spells_by_level
```

**Reason:** This is 100% business logic - spell data gathering has nothing to do with HTTP routing.

---

## 9. character_summary.py - Combat Stats Calculation

### ❌ CURRENT (Lines 500-565)
```python
# Route calculating combat stats
dex_modifier = (character.get('ability_scores', {}).get('Dexterity', 10) - 10) // 2
wis_modifier = (character.get('ability_scores', {}).get('Wisdom', 10) - 10) // 2

hit_die = 8  # Default
if class_name and class_name in data_loader.classes:
    class_data = data_loader.classes[class_name]
    hit_die = class_data.get('hit_die', 8)

combat_stats = {
    'initiative': dex_modifier,
    'armor_class': 10 + dex_modifier,
    'passive_perception': 10 + wis_modifier + ...,
    'hit_dice': f"{character.get('level', 1)}d{hit_die}"
}
```

### ✅ SHOULD BE (CharacterBuilder or CharacterSheetConverter)
```python
class CharacterSheetConverter:
    def _calculate_combat_stats(self, character: dict) -> dict:
        """Calculate all combat-related statistics."""
        return {
            'initiative': self._calculate_initiative(character),
            'armor_class': self._calculate_armor_class(character),
            'passive_perception': self._calculate_passive_perception(character),
            'hit_dice': self._calculate_hit_dice(character)
        }
```

**Reason:** Stat calculations are game mechanics, not presentation logic.

---

## 10. character_summary.py - Skill Modifier Calculation

### ❌ CURRENT (Lines 534-584)
```python
# Route calculating skill modifiers
skill_modifiers = []
proficiency_bonus = 2  # TODO: Calculate based on level

for skill_name, ability_name in all_skills:
    ability_score = character.get('ability_scores', {}).get(ability_name, 10)
    ability_modifier = (ability_score - 10) // 2
    
    is_proficient = skill_name in character.get('skill_proficiencies', [])
    prof_bonus = proficiency_bonus if is_proficient else 0
    
    # Check for special bonuses (like Thaumaturge's WIS to INT checks)
    special_bonus = 0
    for bonus in calculated_bonuses:
        if skill_name in bonus['skills']:
            special_bonus = bonus['value']
            break
    
    total_modifier = ability_modifier + prof_bonus + special_bonus
    # ... build skill_modifiers array
```

### ✅ SHOULD BE (CharacterSheetConverter)
```python
class CharacterSheetConverter:
    def _calculate_skill_modifiers(self, character: dict) -> list:
        """Calculate all skill modifiers including bonuses."""
        skill_modifiers = []
        
        for skill_name, ability_name in self.ALL_SKILLS:
            modifier = self._calculate_single_skill_modifier(
                character, skill_name, ability_name
            )
            skill_modifiers.append(modifier)
        
        return skill_modifiers
```

**Reason:** This is already being done in CharacterSheetConverter, but still duplicated in route.

---

## 11. species.py - Trait Option Extraction

### ❌ CURRENT (Lines 84-120)
```python
# Route extracting trait choice options
trait_choices = {}
if 'traits' in species_data:
    for trait_name, trait_data in species_data['traits'].items():
        if isinstance(trait_data, dict) and trait_data.get('type') == 'choice':
            choices_data = trait_data.get('choices', {})
            source_data = choices_data.get('source', {})
            options = source_data.get('options', [])
            
            trait_choices[trait_name] = {
                'description': trait_data.get('description', ''),
                'options': options,
                'count': choices_data.get('count', 1)
            }
```

### ✅ SHOULD BE (CharacterBuilder or ChoiceResolver)
```python
class ChoiceResolver:
    def get_species_trait_choices(self, species_name: str) -> dict:
        """Get trait choice options for species."""
        species_data = self.data_loader.species.get(species_name, {})
        trait_choices = {}
        
        for trait_name, trait_data in species_data.get('traits', {}).items():
            if self._is_choice_trait(trait_data):
                trait_choices[trait_name] = self._extract_trait_choice(trait_data)
        
        return trait_choices
```

**Reason:** Parsing structured data is business logic, not HTTP handling.

---

## Priority Recommendations

### 🔴 **HIGH PRIORITY** (Core business logic, heavily duplicated)

1. **Character Creation Choice System** (character_creation.py)
   - Move `_resolve_choice_options`, `_get_option_descriptions`, `_load_external_choice_list`
   - Create `utils/choice_resolver.py` or add to CharacterBuilder
   - ~200 lines of critical business logic

2. **Spell Gathering** (character_summary.py)
   - Move `_gather_character_spells()` to CharacterBuilder
   - 413 lines of pure business logic
   - Affects character summary display

3. **Feature Processing** (character_creation.py)
   - Move feature/choice enumeration logic to CharacterBuilder
   - ~115 lines in class_choices route
   - Core character creation logic

### 🟡 **MEDIUM PRIORITY** (Business logic, some duplication)

4. **Skill/Saving Throw Calculations** (character_summary.py)
   - Already in CharacterSheetConverter, remove from route
   - ~80 lines duplicated

5. **Language Options** (languages.py)
   - Move to CharacterBuilder
   - ~25 lines of logic

6. **Background ASI Options** (ability_scores.py)
   - Move to CharacterBuilder
   - ~20 lines of parsing logic

### 🟢 **LOW PRIORITY** (Minor improvements)

7. **Species Trait Parsing** (species.py)
   - Move to ChoiceResolver
   - ~40 lines of logic

8. **Core Traits Data** (character_creation.py)
   - Move data gathering to CharacterBuilder
   - Keep formatting in route
   - ~70 lines mixed logic

---

## Implementation Strategy

### Phase 1: Extract Choice System
1. Create `utils/choice_resolver.py`
2. Move all `_resolve_choice_options` related functions
3. Update character_creation.py to use ChoiceResolver
4. Test class/subclass choice flows

### Phase 2: Move Spell Logic
1. Add `get_all_spells()` to CharacterBuilder
2. Move `_gather_character_spells` logic
3. Update character_summary.py to call builder method
4. Test spell display

### Phase 3: Move Feature Processing
1. Add `get_available_features_and_choices()` to CharacterBuilder
2. Move feature enumeration logic from class_choices route
3. Update route to call builder method
4. Test class choices page

### Phase 4: Clean Up Calculations
1. Remove duplicate skill/save calculation from routes
2. Ensure CharacterSheetConverter is used consistently
3. Move any remaining calculation logic

### Phase 5: Small Refactorings
1. Language options → CharacterBuilder
2. Background ASI → CharacterBuilder  
3. Species traits → ChoiceResolver

---

## Benefits

✅ **Separation of Concerns** - Routes handle HTTP, builder handles game logic  
✅ **Testability** - Business logic can be unit tested independently  
✅ **Reusability** - Logic can be reused across routes and APIs  
✅ **Maintainability** - Changes to game rules only affect builder, not routes  
✅ **Consistency** - Single source of truth for calculations  
✅ **Readability** - Routes become simple and focused

---

## Estimated Impact

- **Lines to move:** ~1,000+ lines of business logic
- **Files to refactor:** 5 route modules + CharacterBuilder + new ChoiceResolver
- **Testing required:** Extensive - all character creation flows
- **Breaking changes:** None (internal refactoring only)
