from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import timedelta
from modules.data_loader import DataLoader
from modules.character_builder import CharacterBuilder
from modules.hp_calculator import HPCalculator
from modules.character_sheet_converter import CharacterSheetConverter

app = Flask(__name__)
app.secret_key = 'dnd-character-creator-secret-key-2024'  # Change this in production

# Configure server-side sessions (filesystem)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Session
Session(app)

# ==================== CharacterBuilder Session Helpers ====================

def get_builder_from_session() -> CharacterBuilder:
    """Get CharacterBuilder from session, creating new one if needed."""
    if 'builder_state' in session:
        builder = CharacterBuilder()
        builder.from_json(session['builder_state'])
        return builder
    
    # Fall back to wizard session data if builder_state doesn't exist
    if 'character' in session:
        character_data = session['character']
        builder = CharacterBuilder()
        
        # Initialize builder with wizard's level and alignment
        if 'level' in character_data:
            builder.character_data['level'] = character_data['level']
        if 'alignment' in character_data:
            builder.character_data['alignment'] = character_data['alignment']
        if 'name' in character_data:
            builder.character_data['name'] = character_data['name']
        
        # Apply any choices already made in wizard
        if 'choices_made' in character_data and character_data['choices_made']:
            try:
                builder.apply_choices(character_data['choices_made'])
            except Exception as e:
                # If apply_choices fails, at least preserve the level
                print(f"Warning: Could not apply wizard choices: {e}")
        
        return builder
    
    return CharacterBuilder()

def save_builder_to_session(builder: CharacterBuilder):
    """Save CharacterBuilder state to session."""
    session['builder_state'] = builder.to_json()
    session['character'] = builder.to_json()  # Keep for compatibility
    session.modified = True

# ==================== Legacy Helper Functions ====================

def _extract_hp_bonuses_from_character(character):
    """Extract HP bonuses from character effects using the effects system."""
    hp_bonuses = []
    
    # Check effects array for bonus_hp effects
    effects = character.get('effects', [])
    for effect in effects:
        if isinstance(effect, dict) and effect.get('type') == 'bonus_hp':
            hp_bonuses.append({
                "source": effect.get('source', 'Unknown'),
                "value": effect.get('value', 0),
                "scaling": effect.get('scaling', 'flat')
            })
    
    return hp_bonuses

# Initialize the data loader
data_loader = DataLoader()
character_sheet_converter = CharacterSheetConverter()

def _resolve_choice_options(choices_data: dict, character: dict, class_data: dict | None = None, subclass_data: dict | None = None) -> list:
    """Resolve choice options from various source types in the Choice Reference System."""
    source = choices_data.get("source", {})
    source_type = source.get("type")
    
    if source_type == "internal":
        # Reference list within same JSON file (e.g., fighting_styles in Fighter, maneuvers in Battle Master)
        list_name = source.get("list", "")
        # Try subclass_data first (for subclass features), then class_data (for class features)
        data_source = subclass_data if subclass_data and list_name in subclass_data else class_data
        if data_source and list_name in data_source:
            choice_list = data_source[list_name]
            if isinstance(choice_list, dict):
                return list(choice_list.keys())
            elif isinstance(choice_list, list):
                return choice_list
        return []
    elif source_type == "external":
        # Reference specific external file
        file_path = source.get("file", "")
        list_name = source.get("list", "")
        return _load_external_choice_list(file_path, list_name)
    elif source_type == "external_dynamic":
        # Dynamic file based on previous choice
        file_pattern = source.get("file_pattern", "")
        depends_on = source.get("depends_on", "")
        list_name = source.get("list", "")
        
        # Get the dependency value from character's choices
        choices_made = character.get("choices_made", {})
        dependency_value = choices_made.get(depends_on)
        
        if dependency_value:
            file_path = file_pattern.format(**{depends_on: dependency_value})
            return _load_external_choice_list(file_path, list_name)
        return []
    elif source_type == "fixed_list":
        # Direct option list
        return source.get("options", [])
    
    return []

def _get_option_descriptions(feature_data: dict, choices_data: dict, class_data: dict | None = None, subclass_data: dict | None = None) -> dict:
    """Get option descriptions from various sources."""
    # First check if feature_data has option_descriptions field
    if 'option_descriptions' in feature_data:
        return feature_data['option_descriptions']
    
    # For internal sources, look for the list in the data
    source = choices_data.get("source", {})
    if source.get("type") == "internal":
        list_name = source.get("list", "")
        # Try subclass_data first, then class_data
        data_source = subclass_data if subclass_data and list_name in subclass_data else class_data
        if data_source and list_name in data_source:
            choice_list = data_source[list_name]
            if isinstance(choice_list, dict):
                # Extract descriptions from structured objects (e.g., divine_orders with effects)
                descriptions = {}
                for key, value in choice_list.items():
                    if isinstance(value, dict) and 'description' in value:
                        descriptions[key] = value['description']
                    elif isinstance(value, str):
                        descriptions[key] = value
                    else:
                        descriptions[key] = str(value)
                return descriptions
    
    return {}

def _load_external_choice_list(file_path: str, list_name: str) -> list:
    """Load choice options from external JSON file."""
    try:
        full_path = Path(__file__).parent / "data" / file_path
        if full_path.exists():
            with open(full_path, 'r') as f:
                data = json.load(f)
                choice_list = data.get(list_name, {})
                if isinstance(choice_list, dict):
                    return list(choice_list.keys())
                elif isinstance(choice_list, list):
                    return choice_list
        return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load choice list from {file_path}: {e}")
        return []

@app.route('/')
def index():
    """Main landing page for character creation."""
    return render_template('index.html')

# ==================== Quick Test & Rebuild API ====================

@app.route('/quick-test')
def quick_test():
    """
    Quick testing page to rebuild characters from choices_made JSON.
    Useful for development and testing - paste a choices_made dict to instantly
    see the character summary without going through the full wizard.
    """
    return render_template('quick_test.html')

@app.route('/api/rebuild-character', methods=['POST'])
def api_rebuild_character():
    """
    API endpoint to rebuild a character from a choices_made dictionary.
    Uses CharacterBuilder to create character from choices.
    
    POST body should be JSON with:
    {
        "choices_made": { ... }  # choices_made must include "level" field
    }
    
    Returns the rebuilt character and stores it in session.
    """
    from modules.character_builder import CharacterBuilder
    
    data = request.get_json()
    if not data or 'choices_made' not in data:
        return jsonify({"error": "Missing choices_made in request body"}), 400
    
    choices_made = data['choices_made']
    
    try:
        # Create character using CharacterBuilder
        builder = CharacterBuilder()
        builder.apply_choices(choices_made)
        
        # Mark as complete
        builder.character_data['step'] = 'complete'
        
        # Get character JSON
        character = builder.to_json()
        
        # Store in session
        session['character'] = character
        session.permanent = True
        session.modified = True
        
        return jsonify({
            "success": True,
            "message": "Character rebuilt successfully",
            "character": character,
            "redirect_url": "/character-summary"
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create', methods=['GET', 'POST'])
def create_character():
    """Start character creation process."""
    alignments = [
        "Unaligned",
        "Lawful Good", "Neutral Good", "Chaotic Good",
        "Lawful Neutral", "True Neutral", "Chaotic Neutral",
        "Lawful Evil", "Neutral Evil", "Chaotic Evil",
    ]

    if request.method == 'POST':
        selected_alignment = request.form.get('alignment', '').strip()
        if selected_alignment and selected_alignment not in alignments:
            selected_alignment = ""

        # Initialize character data
        character_data = {
            "name": request.form.get('name', 'Unnamed Character'),
            "level": int(request.form.get('level', 1)),
            "class": "",
            "background": "",
            "species": "",
            "lineage": "",
            "alignment": selected_alignment,
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 10, 
                "Constitution": 10,
                "Intelligence": 10,
                "Wisdom": 10,
                "Charisma": 10
            },
            "skill_proficiencies": [],
            "languages": ["Common"],
            "equipment": [],
            "features": {
                "class": [],
                "species": [],
                "lineage": [],
                "background": [],
                "feats": []
            },
            "creature_type": "Humanoid",
            "size": "Medium",
            "speed": 30,
            "darkvision": 0,
            "choices_made": {
                "character_name": request.form.get('name', 'Unnamed Character'),
                "level": int(request.form.get('level', 1))
            },
            "step": "class"
        }

        if selected_alignment:
            character_data["choices_made"]["alignment"] = selected_alignment
        
        session.clear()  # Clear any existing session data
        session['character'] = character_data
        session.permanent = True
        session.modified = True
        print(f"DEBUG choices_made after create: {character_data['choices_made']}")
        
        print(f"Session created with character: {character_data['name']}")
        print(f"Session after save: {dict(session)}")
        
        # Instead of redirect, render the class selection page directly
        classes = dict(sorted(data_loader.classes.items()))
        return render_template('choose_class.html', classes=classes, character_created=True)
    
    return render_template('create_character.html', alignments=alignments)

@app.route('/choose-class')
def choose_class():
    """Class selection step."""
    print(f"Choose class accessed. Session keys: {list(session.keys())}")  # Debug
    if 'character' not in session:
        print("No character in session, redirecting to index")  # Debug
        return redirect(url_for('index'))
    
    character = session['character']
    print(f"Character found: {character.get('name', 'Unknown')}")  # Debug
    classes = dict(sorted(data_loader.classes.items()))
    return render_template('choose_class.html', classes=classes)

@app.route('/select-class', methods=['POST'])
def select_class():
    """Handle class selection."""
    class_name = request.form.get('class')
    if not class_name or class_name not in data_loader.classes:
        return redirect(url_for('choose_class'))
    
    builder = get_builder_from_session()
    builder.apply_choice('class', class_name)
    
    # Check if subclass selection is needed first (level 3+ characters)
    character_level = builder.character_data.get('level', 1)
    
    if character_level >= 3:
        class_data = data_loader.classes[class_name]
        subclass_level = class_data.get('subclass_selection_level', 3)
        
        if character_level >= subclass_level:
            save_builder_to_session(builder)
            # Update step in session character
            session['character']['step'] = 'subclass'
            session.modified = True
            return redirect(url_for('choose_subclass'))
    
    save_builder_to_session(builder)
    # Update step in session character
    session['character']['step'] = 'class_choices'
    session.modified = True
    return redirect(url_for('class_choices'))

@app.route('/choose-subclass')
def choose_subclass():
    """Dedicated subclass selection step."""
    if 'character' not in session or session['character']['step'] != 'subclass':
        return redirect(url_for('index'))
    
    character = session['character']
    class_name = character.get('class', '')
    
    if not class_name or class_name not in data_loader.classes:
        return redirect(url_for('choose_class'))
    
    # Load subclasses for this class
    subclasses = data_loader.get_subclasses_for_class(class_name)
    
    if not subclasses:
        # No subclasses available, skip to class choices
        character['step'] = 'class_choices'
        session['character'] = character
    print(f"DEBUG choices_made after subclass selection: {character.get('choices_made', {})}")
    return render_template('choose_subclass.html', 
                         subclasses=subclasses, 
                         class_name=class_name,
                         character_level=character.get('level', 1))

@app.route('/select-subclass', methods=['POST'])
def select_subclass():
    """Handle subclass selection and redirect to class choices."""
    subclass_name = request.form.get('subclass')
    if not subclass_name:
        return redirect(url_for('choose_subclass'))
    
    builder = get_builder_from_session()
    builder.apply_choice('subclass', subclass_name)
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'class_choices'
    session.modified = True
    return redirect(url_for('class_choices'))

@app.route('/class-choices')
def class_choices():
    """Display all class and subclass features with choices."""
    print(f"Class choices accessed. Session keys: {list(session.keys())}")  # Debug
    
    if 'character' not in session:
        print("No character in session during class choices")  # Debug
        return redirect(url_for('index'))
    
    character = session['character']
    class_name = character.get('class', 'Fighter')
    character_level = character.get('level', 1)
    subclass_name = character.get('subclass')
    choices_made = character.get('choices_made', {})
    
    if class_name not in data_loader.classes:
        return redirect(url_for('choose_class'))
    
    class_data = data_loader.classes[class_name]
    
    # Collect all features by level (both class and subclass)
    all_features_by_level = {}
    choices = []
    
    # Add skill selection (level 1)
    if 'skill_options' in class_data and 'skill_proficiencies_count' in class_data:
        if 1 not in all_features_by_level:
            all_features_by_level[1] = []
        all_features_by_level[1].append({
            'name': 'Skill Proficiencies',
            'type': 'choice',
            'description': f'Choose {class_data["skill_proficiencies_count"]} skill proficiencies from the available options.',
            'level': 1,
            'source': 'Class'
        })
        
        # Expand "Any" to all available skills
        skill_options = class_data['skill_options']
        if skill_options == ['Any'] or (len(skill_options) == 1 and skill_options[0] == 'Any'):
            skill_options = [
                'Acrobatics', 'Animal Handling', 'Arcana', 'Athletics', 'Deception',
                'History', 'Insight', 'Intimidation', 'Investigation', 'Medicine',
                'Nature', 'Perception', 'Performance', 'Persuasion', 'Religion',
                'Sleight of Hand', 'Stealth', 'Survival'
            ]
        
        choices.append({
            'title': 'Skill Proficiencies',
            'type': 'skills',
            'description': f'Choose {class_data["skill_proficiencies_count"]} skill proficiencies from the available options.',
            'options': skill_options,
            'count': class_data['skill_proficiencies_count'],
            'required': True,
            'level': 1
        })
    
    # Get class features
    features_by_level = class_data.get('features_by_level', {})
    
    # Get subclass features if subclass is selected
    subclass_features = {}
    subclass_data = {}
    if subclass_name:
        subclass_data = data_loader.get_subclasses_for_class(class_name).get(subclass_name, {})
        subclass_features = subclass_data.get('features_by_level', {})
    
    # Process all levels up to character level
    for level in range(1, character_level + 1):
        level_str = str(level)
        
        # Initialize level if not exists
        if level not in all_features_by_level:
            all_features_by_level[level] = []
        
        # Add class features for this level
        # Both classes and subclasses use the same format: level -> {feature_name: description}
        level_features = features_by_level.get(level_str, {})
        
        for feature_name, feature_data in level_features.items():
            if isinstance(feature_data, dict) and 'choices' in feature_data:
                # Choice-based feature
                all_features_by_level[level].append({
                    'name': feature_name,
                    'type': 'choice',
                    'description': feature_data.get('description', ''),
                    'level': level,
                    'source': 'Class'
                })
                
                # Add to choices for form processing
                choices_data = feature_data['choices']
                if isinstance(choices_data, list):
                    # Multiple choices
                    for idx, choice_item in enumerate(choices_data):
                        choice = {
                            'title': f'{feature_name} - {choice_item.get("name", f"Choice {idx+1}")} (Level {level})',
                            'type': 'feature',
                            'description': feature_data.get('description', ''),
                            'options': _resolve_choice_options(choice_item, character, class_data, None),
                            'count': choice_item.get('count', 1),
                            'required': not choice_item.get('optional', False),
                            'level': level,
                            'feature_name': f'{feature_name}_{choice_item.get("name", f"choice_{idx}")}',
                            'option_descriptions': _get_option_descriptions(feature_data, choice_item, class_data, None)
                        }
                        if 'subclass' not in feature_name.lower():
                            choices.append(choice)
                else:
                    # Single choice
                    choice = {
                        'title': f'{feature_name} (Level {level})',
                        'type': 'feature',
                        'description': feature_data.get('description', ''),
                        'options': _resolve_choice_options(choices_data, character, class_data, None),
                        'count': choices_data.get('count', 1),
                        'required': not choices_data.get('optional', False),
                        'level': level,
                        'feature_name': feature_name,
                        'option_descriptions': _get_option_descriptions(feature_data, choices_data, class_data, None)
                    }
                    if 'subclass' not in feature_name.lower():
                        choices.append(choice)
            else:
                # Feature without choices (simple string description)
                all_features_by_level[level].append({
                    'name': feature_name,
                    'type': 'info',
                    'description': feature_data if isinstance(feature_data, str) else feature_data.get('description', ''),
                    'level': level,
                    'source': 'Class'
                })
        
        # Add subclass features for this level
        if subclass_name and level_str in subclass_features:
            subclass_level_features = subclass_features[level_str]
            for feature_name, feature_data in subclass_level_features.items():
                if isinstance(feature_data, dict) and 'choices' in feature_data:
                    # Choice-based subclass feature
                    all_features_by_level[level].append({
                        'name': feature_name,
                        'type': 'choice',
                        'description': feature_data.get('description', ''),
                        'level': level,
                        'source': subclass_name
                    })
                    
                    # Add to choices for form processing
                    choices_data = feature_data['choices']
                    if isinstance(choices_data, list):
                        for idx, choice_item in enumerate(choices_data):
                            choice = {
                                'title': f'{feature_name} - {choice_item.get("name", f"Choice {idx+1}")} ({subclass_name}, Level {level})',
                                'type': 'feature',
                                'description': feature_data.get('description', ''),
                                'options': _resolve_choice_options(choice_item, character, class_data, subclass_data),
                                'count': choice_item.get('count', 1),
                                'required': not choice_item.get('optional', False),
                                'level': level,
                                'feature_name': f'subclass_{feature_name}_{choice_item.get("name", f"choice_{idx}")}',
                                'option_descriptions': _get_option_descriptions(feature_data, choice_item, class_data, subclass_data)
                            }
                            choices.append(choice)
                    else:
                        choice = {
                            'title': f'{feature_name} ({subclass_name}, Level {level})',
                            'type': 'feature',
                            'description': feature_data.get('description', ''),
                            'options': _resolve_choice_options(choices_data, character, class_data, subclass_data),
                            'count': choices_data.get('count', 1),
                            'required': not choices_data.get('optional', False),
                            'level': level,
                            'feature_name': f'subclass_{feature_name}',
                            'option_descriptions': _get_option_descriptions(feature_data, choices_data, class_data, subclass_data)
                        }
                        choices.append(choice)
                else:
                    # Non-choice subclass feature
                    description = feature_data if isinstance(feature_data, str) else feature_data.get('description', '')
                    all_features_by_level[level].append({
                        'name': feature_name,
                        'type': 'info',
                        'description': description,
                        'level': level,
                        'source': subclass_name
                    })

    def _human_join(items: list[str], conjunction: str = "and") -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        return ", ".join(items[:-1]) + f", {conjunction} " + items[-1]

    # Build "Core <Class> Traits" table rows
    core_traits: list[dict[str, str]] = []

    primary_ability = class_data.get('primary_ability', '')
    if isinstance(primary_ability, list):
        primary_ability_value = _human_join(primary_ability, conjunction="or")
    else:
        primary_ability_value = str(primary_ability)
    core_traits.append({"label": "Primary Ability", "value": primary_ability_value})

    hit_die = class_data.get('hit_die')
    if hit_die:
        core_traits.append({"label": "Hit Point Die", "value": f"D{hit_die} per {class_name} level"})

    saving_throws = class_data.get('saving_throw_proficiencies', [])
    if saving_throws:
        core_traits.append({"label": "Saving Throw Proficiencies", "value": _human_join(list(saving_throws), conjunction="and")})

    skill_count = class_data.get('skill_proficiencies_count')
    skill_options = class_data.get('skill_options', [])
    if skill_count and skill_options:
        core_traits.append({
            "label": "Skill Proficiencies",
            "value": f"Choose {skill_count}: {_human_join(list(skill_options), conjunction='or')}"
        })

    # Weapon proficiencies: combine base class proficiencies with any from effects
    weapon_proficiencies = list(class_data.get('weapon_proficiencies', []))
    # Add any additional weapon proficiencies from character effects
    if 'weapon_proficiencies' in character:
        for prof in character['weapon_proficiencies']:
            if prof not in weapon_proficiencies:
                weapon_proficiencies.append(prof)
    
    if weapon_proficiencies:
        weapon_items = list(weapon_proficiencies)
        if all(isinstance(w, str) and w.lower().endswith(' weapons') for w in weapon_items):
            categories = [w[:-8] for w in weapon_items]  # strip " weapons"
            core_traits.append({"label": "Weapon Proficiencies", "value": f"{_human_join(categories, conjunction='and')} weapons"})
        else:
            core_traits.append({"label": "Weapon Proficiencies", "value": _human_join(weapon_items, conjunction="and")})

    # Armor proficiencies: combine base class proficiencies with any from effects
    armor_proficiencies = list(class_data.get('armor_proficiencies', []))
    # Add any additional armor proficiencies from character effects
    if 'armor_proficiencies' in character:
        for prof in character['armor_proficiencies']:
            if prof not in armor_proficiencies:
                armor_proficiencies.append(prof)
    
    if armor_proficiencies:
        armor_items = list(armor_proficiencies)
        armor_types = []
        other_armor = []
        for item in armor_items:
            if isinstance(item, str) and item.lower().endswith(' armor'):
                armor_types.append(item[:-6])  # strip " armor"
            else:
                other_armor.append(item)

        armor_order = ["Light", "Medium", "Heavy"]
        ordered_armor_types = [a for a in armor_order if a in armor_types] + [a for a in armor_types if a not in armor_order]
        armor_training_parts: list[str] = []
        if ordered_armor_types:
            armor_training_parts.append(f"{_human_join(ordered_armor_types, conjunction='and')} armor")
        # Add other armor items (excluding Shields) first
        other_armor_no_shields = [item for item in other_armor if item != 'Shields']
        armor_training_parts.extend(other_armor_no_shields)
        # Always add Shields last if present
        if 'Shields' in other_armor:
            armor_training_parts.append('Shields')
        core_traits.append({"label": "Armor Training", "value": _human_join(armor_training_parts, conjunction="and")})

    starting_equipment = class_data.get('starting_equipment')
    if starting_equipment:
        core_traits.append({"label": "Starting Equipment", "value": str(starting_equipment)})
    
    # Check choices_made for any selections that have effects granting additional choices
    # This is generic and data-driven - ANY choice with grant_cantrip_choice effect will work
    for choice_key, choice_value in choices_made.items():
        # Only check string-type single selections (skip lists, dicts, etc.)
        if not isinstance(choice_value, str):
            continue
            
        # Scan through class_data to find where this choice_value exists as an option
        for data_key, data_dict in class_data.items():
            if isinstance(data_dict, dict) and choice_value in data_dict:
                # Found the option! Check if it has effects
                option_data = data_dict[choice_value]
                if isinstance(option_data, dict) and 'effects' in option_data:
                    for effect in option_data.get('effects', []):
                        if effect.get('type') == 'grant_cantrip_choice':
                            # This selected option grants a bonus cantrip choice!
                            cantrip_count = effect.get('count', 1)
                            spell_list = effect.get('spell_list', class_name)
                            
                            # Load cantrip options from new spell structure
                            class_lower = spell_list.lower()
                            spell_file_path = f"spells/class_lists/{class_lower}.json"
                            cantrip_options = _resolve_choice_options(
                                {'source': {'type': 'external', 'file': spell_file_path, 'list': 'cantrips'}},
                                character,
                                class_data,
                                None
                            )
                            
                            # Create unique feature name based on the option that grants it
                            bonus_feature_name = f'{choice_value}_bonus_cantrip'
                            
                            # Only add if not already in choices
                            if not any(c.get('feature_name') == bonus_feature_name for c in choices):
                                choice = {
                                    'title': f'{choice_value} - Bonus Cantrip (Level 1)',
                                    'type': 'feature',
                                    'description': f'Choose {cantrip_count} additional cantrip from the {spell_list} spell list.',
                                    'options': cantrip_options,
                                    'count': cantrip_count,
                                    'required': True,
                                    'level': 1,
                                    'feature_name': bonus_feature_name,
                                    'depends_on': choice_key,  # Mark which choice triggers this
                                    'depends_on_value': choice_value,  # Mark which value triggers this
                                    'is_nested': True,  # Flag as nested choice for template
                                    'option_descriptions': _get_option_descriptions(
                                        {'choices': {'source': {'type': 'external', 'file': spell_file_path, 'list': 'cantrips'}}},
                                        {'source': {'type': 'external', 'file': spell_file_path, 'list': 'cantrips'}},
                                        class_data,
                                        None
                                    )
                                }
                                choices.append(choice)
                                print(f"DEBUG: Added bonus cantrip choice: {bonus_feature_name}, options: {len(cantrip_options)}")  # Debug
    
    # ALSO scan for POTENTIAL nested choices even if not yet selected
    # This ensures nested choices render on first page load for dynamic show/hide
    for data_key, data_dict in class_data.items():
        if isinstance(data_dict, dict):
            for option_key, option_data in data_dict.items():
                if isinstance(option_data, dict) and 'effects' in option_data:
                    for effect in option_data.get('effects', []):
                        if effect.get('type') == 'grant_cantrip_choice':
                            # This option would grant a bonus cantrip if selected
                            cantrip_count = effect.get('count', 1)
                            spell_list = effect.get('spell_list', class_name)
                            
                            class_lower = spell_list.lower()
                            spell_file_path = f"spells/class_lists/{class_lower}.json"
                            cantrip_options = _resolve_choice_options(
                                {'source': {'type': 'external', 'file': spell_file_path, 'list': 'cantrips'}},
                                character,
                                class_data,
                                None
                            )
                            
                            bonus_feature_name = f'{option_key}_bonus_cantrip'
                            
                            # Find which choice contains this option
                            parent_choice_name = None
                            for existing_choice in choices:
                                if existing_choice.get('type') == 'feature' and option_key in existing_choice.get('options', []):
                                    parent_choice_name = existing_choice.get('feature_name')
                                    break
                            
                            # Only add if not already present and we found the parent
                            if parent_choice_name and not any(c.get('feature_name') == bonus_feature_name for c in choices):
                                choice = {
                                    'title': f'{option_key} - Bonus Cantrip (Level 1)',
                                    'type': 'feature',
                                    'description': f'Choose {cantrip_count} additional cantrip from the {spell_list} spell list.',
                                    'options': cantrip_options,
                                    'count': cantrip_count,
                                    'required': True,
                                    'level': 1,
                                    'feature_name': bonus_feature_name,
                                    'depends_on': parent_choice_name,
                                    'depends_on_value': option_key,
                                    'is_nested': True,
                                    'option_descriptions': {},
                                }
                                choices.append(choice)
                                print(f"DEBUG: Pre-added potential nested choice: {bonus_feature_name}")

    return render_template('class_choices.html', 
                         character=character, 
                         choices=choices,
                         all_features_by_level=all_features_by_level,
                         character_level=character_level,
                         core_traits=core_traits,
                         choices_made=choices_made)

@app.route('/submit-class-choices', methods=['POST'])
def submit_class_choices():
    """Process class choice submissions."""
    builder = get_builder_from_session()
    
    # Collect all choices from the form
    choices = {}
    
    # Process skill selections
    skills = request.form.getlist('skills')
    if skills:
        choices['skill_choices'] = skills
    
    # Process feature choices
    for key, values in request.form.lists():
        if key.startswith('choice_'):
            choice_name = key.replace('choice_', '')
            choices[choice_name] = values[0] if len(values) == 1 else values
    
    # Apply all choices at once
    if choices:
        builder.apply_choices(choices)
    
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'background'
    session.modified = True
    return redirect(url_for('choose_background'))

@app.route('/choose-background')
def choose_background():
    """Background selection step."""
    if 'character' not in session:
        print("DEBUG: No character in session, redirecting to index")  # Debug
        return redirect(url_for('index'))
    
    character = session['character']
    # Ensure class is selected before accessing backgrounds
    if not character.get('class'):
        print("DEBUG: No class selected, redirecting to choose_class")  # Debug
        return redirect(url_for('choose_class'))
    
    # Update step to background when accessing this page
    character['step'] = 'background'
    session.modified = True
    print("DEBUG: Updated step to 'background'")  # Debug
    
    backgrounds = dict(sorted(data_loader.backgrounds.items()))
    return render_template('choose_background.html', backgrounds=backgrounds, character=character)

@app.route('/select-background', methods=['POST'])
def select_background():
    """Handle background selection."""
    background_name = request.form.get('background')
    if not background_name or background_name not in data_loader.backgrounds:
        return redirect(url_for('choose_background'))
    
    builder = get_builder_from_session()
    builder.apply_choice('background', background_name)
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'species'
    session.modified = True
    return redirect(url_for('choose_species'))

@app.route('/choose-species')
def choose_species():
    """Species selection step."""
    builder = get_builder_from_session()
    character = builder.to_json()
    
    if not character.get('background'):
        return redirect(url_for('choose_background'))
    
    character['step'] = 'species'
    save_builder_to_session(builder)
    
    species = dict(sorted(data_loader.species.items()))
    return render_template('choose_species.html', species=species, character=character)

@app.route('/select-species', methods=['POST'])
def select_species():
    """Handle species selection using CharacterBuilder."""
    species_name = request.form.get('species')
    if not species_name or species_name not in data_loader.species:
        return redirect(url_for('choose_species'))
    
    builder = get_builder_from_session()
    builder.apply_choice('species', species_name)
    
    # Handle species trait choices (like Keen Senses, Elven Lineage)
    species_data = data_loader.species[species_name]
    if 'traits' in species_data:
        for trait_name, trait_data in species_data['traits'].items():
            if isinstance(trait_data, dict) and trait_data.get('type') == 'choice':
                choice_key = f'species_trait_{trait_name}'
                selected_option = request.form.get(choice_key)
                
                if selected_option:
                    builder.apply_choice(choice_key, selected_option)
    
    save_builder_to_session(builder)
    
    # Update session step
    session['character']['step'] = 'lineage' if species_data.get('lineages') else 'languages'
    session.modified = True
    
    # Check if species has lineages
    if species_data.get('lineages'):
        return redirect(url_for('choose_lineage'))
    else:
        return redirect(url_for('choose_languages'))

@app.route('/choose-species-traits')
def choose_species_traits():
    """Species trait choice step (e.g., Keen Senses)."""
    if 'character' not in session or session['character']['step'] != 'species_traits':
        return redirect(url_for('index'))
    
    character = session['character']
    species_name = character['species']
    species_data = data_loader.species.get(species_name, {})
    
    # Find trait choices and extract options
    trait_choices = {}
    if 'traits' in species_data:
        for trait_name, trait_data in species_data['traits'].items():
            if isinstance(trait_data, dict) and trait_data.get('type') == 'choice':
                # Extract options from the nested structure
                choices_data = trait_data.get('choices', {})
                source_data = choices_data.get('source', {})
                options = source_data.get('options', [])
                
                # Create a simplified structure for the template
                trait_choices[trait_name] = {
                    'description': trait_data.get('description', ''),
                    'options': options,
                    'count': choices_data.get('count', 1)
                }
    
    return render_template('choose_species_traits.html', 
                         character=character, 
                         trait_choices=trait_choices)

@app.route('/select-species-traits', methods=['POST'])
def select_species_traits():
    """Handle species trait choices using CharacterBuilder."""
    builder = get_builder_from_session()
    character = builder.to_json()
    species_name = character.get('species')
    
    if not species_name:
        return redirect(url_for('choose_species'))
    
    species_data = data_loader.species.get(species_name, {})
    
    # Process trait choices
    if 'traits' in species_data:
        for trait_name, trait_data in species_data['traits'].items():
            if isinstance(trait_data, dict) and trait_data.get('type') == 'choice':
                choice_key = f"trait_{trait_name.lower().replace(' ', '_')}"
                selected_option = request.form.get(choice_key)
                
                if selected_option:
                    builder.apply_choice(f'species_trait_{trait_name}', selected_option)
    
    save_builder_to_session(builder)
    
    # Check if species has lineages
    if species_data.get('lineages'):
        return redirect(url_for('choose_lineage'))
    else:
        return redirect(url_for('choose_languages'))

@app.route('/choose-lineage')
def choose_lineage():
    """Lineage selection step."""
    builder = get_builder_from_session()
    character = builder.to_json()
    
    if character.get('step') != 'lineage' and not character.get('species'):
        return redirect(url_for('index'))
    
    character = session['character']
    species_name = character['species']
    
    # Get available lineages directly from species data
    species_data = data_loader.species.get(species_name, {})
    lineage_names = species_data.get('lineages', [])
    
    lineages = {}
    lineage_dir = Path(data_loader.data_dir) / 'species_variants'
    
    print(f"Loading lineages for {species_name}: {lineage_names}")  # Debug
    
    for lineage_name in lineage_names:
        # Convert lineage name to filename (replace spaces with underscores, lowercase)
        filename = lineage_name.lower().replace(' ', '_') + '.json'
        lineage_file = lineage_dir / filename
        
        try:
            if lineage_file.exists():
                with open(lineage_file, 'r') as f:
                    lineage_data = json.load(f)
                    lineages[lineage_name] = lineage_data
                    print(f"Loaded lineage: {lineage_name} from {filename}")  # Debug
            else:
                print(f"Warning: Lineage file not found: {filename}")  # Debug
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading lineage {lineage_name}: {e}")  # Debug
    
    print(f"Total lineages loaded: {len(lineages)}")  # Debug
    
    # Debug: Check spellcasting ability detection
    for name, lineage in lineages.items():
        spellcasting_choices = lineage.get('spellcasting_ability_choices', [])
        print(f"Lineage {name}: spellcasting_ability_choices = {spellcasting_choices}")  # Debug
    
    return render_template('choose_lineage.html', character=character, lineages=lineages)

@app.route('/select-lineage', methods=['POST'])
def select_lineage():
    """Handle lineage selection."""
    lineage_name = request.form.get('lineage')
    spellcasting_ability = request.form.get('spellcasting_ability')
    
    builder = get_builder_from_session()
    
    # Apply lineage choice
    if lineage_name:
        builder.apply_choice('lineage', lineage_name)
    
    # Apply spellcasting ability choice if provided
    if spellcasting_ability:
        builder.apply_choice('lineage_spellcasting_ability', spellcasting_ability)
    
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'languages'
    session.modified = True
    return redirect(url_for('choose_languages'))

@app.route('/choose-languages')
def choose_languages():
    """Language selection step."""
    if 'character' not in session:
        return redirect(url_for('index'))
    
    # Allow access if step is 'languages' or we're navigating back from later steps  
    character_step = session['character'].get('step')
    if character_step not in ['languages', 'ability_scores', 'background_bonuses', 'complete']:
        return redirect(url_for('index'))
    
    # Update step to languages when accessing this page
    session['character']['step'] = 'languages'
    session.modified = True
    
    character = session['character']
    
    # Get base languages from species and class
    species_data = data_loader.species.get(character['species'], {})
    class_data = data_loader.classes.get(character['class'], {})
    
    # Start with common languages
    base_languages = set(['Common'])
    
    # Add species languages
    if 'languages' in species_data:
        base_languages.update(species_data['languages'])
    
    # Add class languages if any
    if 'languages' in class_data:
        base_languages.update(class_data['languages'])
    
    # Available languages to choose from
    all_languages = [
        'Abyssal', 'Celestial', 'Common', 'Deep Speech', 'Draconic', 'Dwarvish',
        'Elvish', 'Giant', 'Gnomish', 'Goblin', 'Halfling', 'Infernal',
        'Orc', 'Primordial', 'Sylvan', 'Undercommon'
    ]
    
    # Languages available for selection (not already known)
    available_languages = [lang for lang in all_languages if lang not in base_languages]
    
    return render_template('choose_languages.html', 
                         character=character,
                         base_languages=sorted(base_languages),
                         available_languages=available_languages)

@app.route('/select-languages', methods=['POST'])
def select_languages():
    """Handle language selection."""
    selected_languages = request.form.getlist('languages')
    
    builder = get_builder_from_session()
    builder.apply_choice('languages', selected_languages)
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'ability_scores'
    session.modified = True
    return redirect(url_for('assign_ability_scores'))

@app.route('/assign-ability-scores')
def assign_ability_scores():
    """Ability score assignment step."""
    if 'character' not in session:
        return redirect(url_for('index'))
    
    character = session['character']
    
    # Allow access if we're at ability_scores step or later
    if character.get('step') not in ['ability_scores', 'background_bonuses', 'complete']:
        return redirect(url_for('index'))
    
    character = session['character']
    class_name = character['class']
    
    # Get class recommendations
    class_data = data_loader.classes.get(class_name, {})
    primary_ability_data = class_data.get('primary_ability', '')
    
    # Handle both string and list formats for primary_ability
    if isinstance(primary_ability_data, list):
        primary_abilities = primary_ability_data
    elif isinstance(primary_ability_data, str):
        primary_abilities = primary_ability_data.split(', ') if primary_ability_data else []
    else:
        primary_abilities = []
    
    standard_array = [15, 14, 13, 12, 10, 8]
    
    # Calculate recommended allocation
    abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    recommended_allocation = {}
    remaining_values = standard_array.copy()
    remaining_abilities = abilities.copy()
    
    # Assign primary abilities first
    for primary_ability in primary_abilities:
        if primary_ability in remaining_abilities and remaining_values:
            recommended_allocation[primary_ability] = remaining_values.pop(0)
            remaining_abilities.remove(primary_ability)
    
    # Assign Constitution next (if not already assigned)
    if "Constitution" in remaining_abilities and remaining_values:
        recommended_allocation["Constitution"] = remaining_values.pop(0)
        remaining_abilities.remove("Constitution")
    
    # Assign remaining values
    for ability in remaining_abilities:
        if remaining_values:
            recommended_allocation[ability] = remaining_values.pop(0)
    
    return render_template('assign_ability_scores.html', 
                         character=character, 
                         primary_abilities=primary_abilities,
                         standard_array=standard_array,
                         recommended_allocation=recommended_allocation)

@app.route('/submit-ability-scores', methods=['POST'])
def submit_ability_scores():
    """Process ability score assignment."""
    assignment_method = request.form.get('assignment_method')
    
    builder = get_builder_from_session()
    
    if assignment_method == 'recommended':
        # Use recommended ability scores for the class
        builder.apply_choice('ability_scores_method', 'recommended')
    else:  # manual
        # Get manual assignments from form
        manual_scores = {}
        for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            score = request.form.get(f'ability_{ability}')
            if score:
                manual_scores[ability] = int(score)
        
        builder.apply_choice('ability_scores', manual_scores)
    
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'background_bonuses'
    session.modified = True
    return redirect(url_for('background_bonuses'))

@app.route('/background-bonuses')
def background_bonuses():
    """Background ability score bonuses step."""
    if 'character' not in session:
        return redirect(url_for('index'))
    
    character = session['character']
    
    # Allow access if we're at background_bonuses step or later
    if character.get('step') not in ['background_bonuses', 'complete']:
        return redirect(url_for('index'))
    
    character = session['character']
    background_name = character['background']
    background_data = data_loader.backgrounds.get(background_name, {})
    
    # Calculate available points and suggested allocation
    total_points = 3  # D&D 2024 standard
    suggested = {}
    ability_options = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]  # Default fallback
    
    if 'ability_score_increase' in background_data:
        asi_data = background_data['ability_score_increase']
        if 'suggested' in asi_data:
            suggested = asi_data['suggested']
        if 'options' in asi_data:
            # Keep the background-specific abilities but ensure they're in standard D&D order
            bg_options = asi_data['options']
            ability_options = [ability for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"] if ability in bg_options]
    
    return render_template('background_bonuses.html', 
                         character=character,
                         total_points=total_points,
                         suggested=suggested,
                         ability_options=ability_options)

@app.route('/submit-background-bonuses', methods=['POST'])
def submit_background_bonuses():
    """Process background ability score bonuses."""
    assignment_method = request.form.get('assignment_method')
    
    builder = get_builder_from_session()
    
    if assignment_method == 'suggested':
        # Use suggested background bonuses
        builder.apply_choice('background_bonuses_method', 'suggested')
    else:  # manual
        # Get manual background bonus assignments from form
        manual_bonuses = {}
        for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            bonus = request.form.get(f'bonus_{ability}')
            if bonus and int(bonus) > 0:
                manual_bonuses[ability] = int(bonus)
        
        builder.apply_choice('background_bonuses', manual_bonuses)
    
    save_builder_to_session(builder)
    
    # Update session step
    character = session['character']
    character['step'] = 'complete'
    session.modified = True
    return redirect(url_for('character_summary'))

def _gather_character_spells(character: dict) -> dict:
    """Gather all spells known by the character from various sources."""
    import json
    from pathlib import Path
    
    spells_by_level = {}
    choices_made = character.get('choices_made', {})
    class_name = character.get('class', '')
    
    # DEBUG: Check effects array
    effects = character.get('effects', [])
    print(f"DEBUG _gather_character_spells: Effects count: {len(effects)}")
    if effects:
        for i, effect in enumerate(effects[:10]):  # First 10
            if effect.get('type') in ['grant_cantrip', 'grant_spell']:
                print(f"DEBUG _gather_character_spells: Effect {i}: type={effect.get('type')}, spell={effect.get('spell')}, source={effect.get('source')}")

    def _load_cantrips_for_spell_list(spell_list_name: str) -> dict:
        """Load cantrip details for a given spell list name (e.g., 'Wizard')."""
        if not spell_list_name:
            return {}
        spell_file = Path(__file__).parent / "data" / "spells" / spell_list_name.lower() / "0.json"
        if not spell_file.exists():
            return {}
        try:
            with open(spell_file, 'r') as f:
                spell_data = json.load(f)
                return spell_data.get('spells', {})
        except (json.JSONDecodeError, IOError):
            return {}

    # 1) Add spells granted directly via character effects (generic, data-driven)
    effects = character.get('effects', [])
    if isinstance(effects, list):
        cantrip_cache: dict[str, dict] = {}
        spell_cache_by_level: dict[tuple[str, int], dict] = {}
        for effect in effects:
            if not isinstance(effect, dict):
                continue

            min_level = effect.get('min_level')
            if isinstance(min_level, int) and character.get('level', 1) < min_level:
                continue

            effect_type = effect.get('type')
            if effect_type == 'grant_cantrip':
                cantrip_name = effect.get('spell')
                if not cantrip_name:
                    continue

                # Avoid duplicates
                if 0 in spells_by_level and any(s.get('name') == cantrip_name for s in spells_by_level[0]):
                    continue

                # Load cantrip details from definitions folder
                cantrip_file = Path(__file__).parent / "data" / "spells" / "definitions" / f"{cantrip_name.lower().replace(' ', '_')}.json"
                cantrip_info = {}
                if cantrip_file.exists():
                    try:
                        with open(cantrip_file, 'r') as cf:
                            cantrip_info = json.load(cf)
                    except (json.JSONDecodeError, IOError):
                        pass
                
                if 0 not in spells_by_level:
                    spells_by_level[0] = []

                spells_by_level[0].append({
                    'name': cantrip_name,
                    'school': cantrip_info.get('school', ''),
                    'casting_time': cantrip_info.get('casting_time', ''),
                    'range': cantrip_info.get('range', ''),
                    'components': cantrip_info.get('components', ''),
                    'duration': cantrip_info.get('duration', ''),
                    'description': cantrip_info.get('description', ''),
                    'source': effect.get('source', 'Effects')
                })

            elif effect_type == 'grant_spell':
                spell_name = effect.get('spell')
                spell_level = effect.get('level')
                if not spell_name or not isinstance(spell_level, int):
                    continue

                # Avoid duplicates
                if spell_level in spells_by_level and any(s.get('name') == spell_name for s in spells_by_level[spell_level]):
                    continue

                spell_list = effect.get('spell_list') or class_name
                cache_key = (spell_list, spell_level)
                if cache_key not in spell_cache_by_level:
                    spell_file = Path(__file__).parent / "data" / "spells" / spell_list.lower() / f"{spell_level}.json"
                    if spell_file.exists():
                        try:
                            with open(spell_file, 'r') as f:
                                spell_data = json.load(f)
                                spell_cache_by_level[cache_key] = spell_data.get('spells', {})
                        except (json.JSONDecodeError, IOError):
                            spell_cache_by_level[cache_key] = {}
                    else:
                        spell_cache_by_level[cache_key] = {}

                spell_info = spell_cache_by_level.get(cache_key, {}).get(spell_name, {})
                if spell_level not in spells_by_level:
                    spells_by_level[spell_level] = []

                spells_by_level[spell_level].append({
                    'name': spell_name,
                    'school': spell_info.get('school', ''),
                    'casting_time': spell_info.get('casting_time', ''),
                    'range': spell_info.get('range', ''),
                    'components': spell_info.get('components', ''),
                    'duration': spell_info.get('duration', ''),
                    'description': spell_info.get('description', ''),
                    'source': effect.get('source', 'Effects')
                })
    
    # 2) Add spells from character['spells']['prepared'] (domain/species spells - always prepared)
    prepared_spells = character.get('spells', {}).get('prepared', [])
    spell_metadata = character.get('spell_metadata', {})
    
    if isinstance(prepared_spells, list):
        for spell_name in prepared_spells:
            if not spell_name or not isinstance(spell_name, str):
                continue
            
            # Try to load spell details to determine level
            spell_file = Path(__file__).parent / "data" / "spells" / "definitions" / f"{spell_name.lower().replace(' ', '_')}.json"
            spell_level = 1  # Default to 1st level if we can't determine
            spell_info = {}
            
            if spell_file.exists():
                try:
                    with open(spell_file, 'r') as f:
                        spell_info = json.load(f)
                        spell_level = spell_info.get('level', 1)
                except (json.JSONDecodeError, IOError):
                    pass
            
            # Check if spell already exists in the list
            if spell_level not in spells_by_level:
                spells_by_level[spell_level] = []
            
            if not any(s.get('name') == spell_name for s in spells_by_level[spell_level]):
                # Get metadata for this spell
                metadata = spell_metadata.get(spell_name, {})
                once_per_day = metadata.get('once_per_day', False)
                
                spells_by_level[spell_level].append({
                    'name': spell_name,
                    'school': spell_info.get('school', ''),
                    'casting_time': spell_info.get('casting_time', ''),
                    'range': spell_info.get('range', ''),
                    'components': spell_info.get('components', ''),
                    'duration': spell_info.get('duration', ''),
                    'description': spell_info.get('description', ''),
                    'source': 'Always Prepared',
                    'always_prepared': True,  # Flag for template display
                    'once_per_day': once_per_day  # Flag for species/lineage spells
                })
    
    # 3) Add spells from character['spells']['known'] (other known spells)
    known_spells = character.get('spells', {}).get('known', [])
    if isinstance(known_spells, list):
        for spell_name in known_spells:
            if not spell_name or not isinstance(spell_name, str):
                continue
            
            # Try to load spell details to determine level
            spell_file = Path(__file__).parent / "data" / "spells" / "definitions" / f"{spell_name.lower().replace(' ', '_')}.json"
            spell_level = 1  # Default to 1st level if we can't determine
            spell_info = {}
            
            if spell_file.exists():
                try:
                    with open(spell_file, 'r') as f:
                        spell_info = json.load(f)
                        spell_level = spell_info.get('level', 1)
                except (json.JSONDecodeError, IOError):
                    pass
            
            # Check if spell already exists in the list
            if spell_level not in spells_by_level:
                spells_by_level[spell_level] = []
            
            if not any(s.get('name') == spell_name for s in spells_by_level[spell_level]):
                spells_by_level[spell_level].append({
                    'name': spell_name,
                    'school': spell_info.get('school', ''),
                    'casting_time': spell_info.get('casting_time', ''),
                    'range': spell_info.get('range', ''),
                    'components': spell_info.get('components', ''),
                    'duration': spell_info.get('duration', ''),
                    'description': spell_info.get('description', ''),
                    'source': 'Known Spells'
                })
    
    # Get class cantrips from choices
    # Cantrips may be stored under different keys depending on the feature name
    cantrips = choices_made.get('cantrips', [])
    if not cantrips:
        # Try looking for "Spellcasting" feature (common for most spellcasters)
        cantrips = choices_made.get('Spellcasting', [])
    if not cantrips:
        # Try other common feature names
        for key in ['spellcasting', 'Spellcasting', 'cantrips', 'Cantrips']:
            if key in choices_made:
                potential_cantrips = choices_made[key]
                if isinstance(potential_cantrips, list):
                    cantrips = potential_cantrips
                    break
    
    if cantrips:
        if 0 not in spells_by_level:
            spells_by_level[0] = []
        
        print(f"DEBUG _gather_character_spells: Found cantrips in choices_made: {cantrips}")
        
        # Load cantrip details from the spell file (new structure)
        class_lower = class_name.lower()
        spell_file = Path(__file__).parent / "data" / "spells" / "class_lists" / f"{class_lower}.json"
        
        print(f"DEBUG _gather_character_spells: Looking for spell file at: {spell_file}")
        
        if spell_file.exists():
            try:
                with open(spell_file, 'r') as f:
                    spell_data = json.load(f)
                    # New structure: cantrips is a simple array of names
                    available_cantrips = spell_data.get('cantrips', [])
                    
                    print(f"DEBUG _gather_character_spells: Available cantrips: {available_cantrips}")
                    
                    for cantrip_name in cantrips:
                        if cantrip_name in available_cantrips:
                            # Check for duplicates before adding
                            existing_names = [s['name'] for s in spells_by_level[0]]
                            if cantrip_name not in existing_names:
                                # Load details from definitions folder
                                cantrip_file = Path(__file__).parent / "data" / "spells" / "definitions" / f"{cantrip_name.lower().replace(' ', '_')}.json"
                                cantrip_info = {}
                                if cantrip_file.exists():
                                    try:
                                        with open(cantrip_file, 'r') as cf:
                                            cantrip_info = json.load(cf)
                                    except (json.JSONDecodeError, IOError):
                                        pass
                                
                                spells_by_level[0].append({
                                    'name': cantrip_name,
                                    'school': cantrip_info.get('school', ''),
                                    'casting_time': cantrip_info.get('casting_time', ''),
                                    'range': cantrip_info.get('range', ''),
                                    'components': cantrip_info.get('components', ''),
                                    'duration': cantrip_info.get('duration', ''),
                                    'description': cantrip_info.get('description', ''),
                                    'source': f"{class_name} Class"
                                })
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load cantrip details: {e}")
    
    # Add bonus cantrips from ANY choice with grant_cantrip_choice effects (generic, data-driven)
    if class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        
        # Scan all keys in class_data for option lists that might have effects
        for data_key, data_value in class_data.items():
            if isinstance(data_value, dict):
                # This could be a choice list (e.g., divine_orders, fighting_styles, etc.)
                for option_name, option_data in data_value.items():
                    if isinstance(option_data, dict) and 'effects' in option_data:
                        # Check if this option was selected
                        # The choice key could be data_key (e.g., "divine_order") or various formats
                        # We need to check if this option_name appears in any choice
                        for choice_key, choice_value in choices_made.items():
                            if choice_value == option_name:
                                # This option was selected! Check for grant_cantrip_choice effects
                                for effect in option_data.get('effects', []):
                                    if effect.get('type') == 'grant_cantrip_choice':
                                        # Look for the bonus cantrip choice in choices_made
                                        bonus_cantrip_key = f'{option_name}_bonus_cantrip'
                                        bonus_cantrips = choices_made.get(bonus_cantrip_key)
                                        
                                        if bonus_cantrips:
                                            spell_list = effect.get('spell_list', class_name)
                                            class_lower = spell_list.lower()
                                            spell_file = Path(__file__).parent / "data" / "spells" / "class_lists" / f"{class_lower}.json"
                                            
                                            print(f"DEBUG _gather_character_spells: Bonus cantrips from {option_name}: {bonus_cantrips}")
                                            
                                            if spell_file.exists():
                                                try:
                                                    with open(spell_file, 'r') as f:
                                                        spell_data = json.load(f)
                                                        available_cantrips = spell_data.get('cantrips', [])
                                                        
                                                        if 0 not in spells_by_level:
                                                            spells_by_level[0] = []
                                                        
                                                        # Handle both single cantrip and list
                                                        cantrip_list = bonus_cantrips if isinstance(bonus_cantrips, list) else [bonus_cantrips]
                                                        
                                                        for cantrip_name in cantrip_list:
                                                            if cantrip_name in available_cantrips:
                                                                # Check for duplicates
                                                                existing_names = [s['name'] for s in spells_by_level[0]]
                                                                if cantrip_name not in existing_names:
                                                                    # Load details from definitions folder
                                                                    cantrip_file = Path(__file__).parent / "data" / "spells" / "definitions" / f"{cantrip_name.lower().replace(' ', '_')}.json"
                                                                    cantrip_info = {}
                                                                    if cantrip_file.exists():
                                                                        try:
                                                                            with open(cantrip_file, 'r') as cf:
                                                                                cantrip_info = json.load(cf)
                                                                        except (json.JSONDecodeError, IOError):
                                                                            pass
                                                                    
                                                                    spells_by_level[0].append({
                                                                        'name': cantrip_name,
                                                                        'school': cantrip_info.get('school', ''),
                                                                        'casting_time': cantrip_info.get('casting_time', ''),
                                                                        'range': cantrip_info.get('range', ''),
                                                                        'components': cantrip_info.get('components', ''),
                                                                        'duration': cantrip_info.get('duration', ''),
                                                                        'description': cantrip_info.get('description', ''),
                                                                        'source': f"{option_name} ({data_key})"
                                                                    })
                                                except (json.JSONDecodeError, IOError) as e:
                                                    print(f"Warning: Could not load bonus cantrip details: {e}")
    
    # Add cantrips from subclass features (using structured effects system)
    subclass_name = character.get('subclass')
    if subclass_name and class_name:
        subclass_data = data_loader.get_subclasses_for_class(class_name).get(subclass_name, {})
        features_by_level = subclass_data.get('features_by_level', {})
        character_level = character.get('level', 1)
        
        # Load spell file once for efficiency (new structure)
        class_lower = class_name.lower()
        spell_file = Path(__file__).parent / "data" / "spells" / "class_lists" / f"{class_lower}.json"
        available_cantrips = []
        
        if spell_file.exists():
            try:
                with open(spell_file, 'r') as f:
                    spell_data = json.load(f)
                    available_cantrips = spell_data.get('cantrips', [])
            except (json.JSONDecodeError, IOError):
                pass
        
        # Check each level up to character level for effects
        for level in range(1, character_level + 1):
            level_str = str(level)
            if level_str in features_by_level:
                level_features = features_by_level[level_str]
                for feature_name, feature_data in level_features.items():
                    # Check if feature has structured effects
                    if isinstance(feature_data, dict) and 'effects' in feature_data:
                        effects = feature_data.get('effects', [])
                        for effect in effects:
                            if effect.get('type') == 'grant_cantrip':
                                cantrip_name = effect.get('spell')
                                if cantrip_name and cantrip_name in available_cantrips:
                                    # Initialize cantrip list if needed
                                    if 0 not in spells_by_level:
                                        spells_by_level[0] = []
                                    
                                    # Check if cantrip is not already in the list
                                    existing_names = [s['name'] for s in spells_by_level[0]]
                                    if cantrip_name not in existing_names:
                                        # Load details from definitions folder
                                        cantrip_file = Path(__file__).parent / "data" / "spells" / "definitions" / f"{cantrip_name.lower().replace(' ', '_')}.json"
                                        cantrip_info = {}
                                        if cantrip_file.exists():
                                            try:
                                                with open(cantrip_file, 'r') as cf:
                                                    cantrip_info = json.load(cf)
                                            except (json.JSONDecodeError, IOError):
                                                pass
                                        
                                        spells_by_level[0].append({
                                            'name': cantrip_name,
                                            'school': cantrip_info.get('school', ''),
                                            'casting_time': cantrip_info.get('casting_time', ''),
                                            'range': cantrip_info.get('range', ''),
                                            'components': cantrip_info.get('components', ''),
                                            'duration': cantrip_info.get('duration', ''),
                                            'description': cantrip_info.get('description', ''),
                                            'source': f"{subclass_name} (Level {level})"
                                        })
    
    # TODO: Add spells from feats, species, class features, and other sources using effects system
    
    return spells_by_level

@app.route('/character-summary')
def character_summary():
    """Display final character summary."""
    if 'character' not in session or session['character']['step'] != 'complete':
        return redirect(url_for('index'))
    
    character = session['character']
    
    # Convert to comprehensive character sheet format
    comprehensive_character = character_sheet_converter.convert_to_character_sheet(character)
    
    # Add max_hp to character object for template compatibility
    character['max_hp'] = comprehensive_character['combat_stats']['hit_point_maximum']
    
    # Gather all spells from various sources
    spells_by_level = _gather_character_spells(character)
    
    # Get class name for later use
    class_name = character.get('class')
    
    # Calculate spell slots for spellcasters
    spell_slots = {}
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        if 'spell_slots_by_level' in class_data:
            character_level = character.get('level', 1)
            level_str = str(character_level)
            slots_array = class_data['spell_slots_by_level'].get(level_str, [0]*9)
            
            # Create a dict of spell level -> slot count (only non-zero)
            for spell_level in range(1, 10):
                if spell_level - 1 < len(slots_array) and slots_array[spell_level - 1] > 0:
                    spell_slots[spell_level] = slots_array[spell_level - 1]
    
    # Gather weapon and armor proficiencies
    weapon_proficiencies = []
    armor_proficiencies = []
    
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        weapon_proficiencies = list(class_data.get('weapon_proficiencies', []))
        armor_proficiencies = list(class_data.get('armor_proficiencies', []))
    
    # Add proficiencies from effects
    if 'weapon_proficiencies' in character:
        for prof in character['weapon_proficiencies']:
            if prof not in weapon_proficiencies:
                weapon_proficiencies.append(prof)
    
    if 'armor_proficiencies' in character:
        for prof in character['armor_proficiencies']:
            if prof not in armor_proficiencies:
                armor_proficiencies.append(prof)
    
    # Sort armor proficiencies: Light, Medium, Heavy armor types first, then other items, Shields last
    def sort_armor_proficiencies(profs):
        armor_order = ["Light armor", "Medium armor", "Heavy armor"]
        shields = [p for p in profs if p == "Shields"]
        ordered = [p for p in armor_order if p in profs]
        other = [p for p in profs if p not in armor_order and p != "Shields"]
        return ordered + other + shields
    
    armor_proficiencies = sort_armor_proficiencies(armor_proficiencies)
    
    # Calculate ability bonuses (like Thaumaturge's WIS bonus to INT checks)
    calculated_bonuses = []
    if 'ability_bonuses' in character:
        for bonus_info in character['ability_bonuses']:
            # Calculate the bonus value
            if bonus_info.get('value') == 'wisdom_modifier':
                wis_score = character.get('ability_scores', {}).get('Wisdom', 10)
                wis_modifier = (wis_score - 10) // 2
                bonus_value = max(wis_modifier, bonus_info.get('minimum', 0))
            else:
                bonus_value = bonus_info.get('value', 0)
            
            calculated_bonuses.append({
                'ability': bonus_info.get('ability'),
                'skills': bonus_info.get('skills', []),
                'value': bonus_value,
                'source': bonus_info.get('source')
            })
    
    print(f"DEBUG character_summary: ability_bonuses in character = {'ability_bonuses' in character}")
    print(f"DEBUG character_summary: calculated_bonuses = {calculated_bonuses}")
    print(f"DEBUG character_summary: Wisdom score = {character.get('ability_scores', {}).get('Wisdom', 10)}")
    
    # Build skill sources map to show where proficiencies come from
    skill_sources = {}
    
    # Get class skill choices
    class_skills = character.get('choices_made', {}).get('skill_choices', [])
    for skill in class_skills:
        if isinstance(skill, str):
            skill_sources[skill] = f"{class_name}"
    
    # Get background skills
    background_name = character.get('background')
    if background_name and background_name in data_loader.backgrounds:
        bg_data = data_loader.backgrounds[background_name]
        bg_skills = bg_data.get('skill_proficiencies', [])
        for skill in bg_skills:
            if isinstance(skill, str):
                skill_sources[skill] = f"{background_name}"
    
    # Calculate all skill modifiers with bonuses
    all_skills = [
        ('Acrobatics', 'Dexterity'), ('Animal Handling', 'Wisdom'), ('Arcana', 'Intelligence'),
        ('Athletics', 'Strength'), ('Deception', 'Charisma'), ('History', 'Intelligence'),
        ('Insight', 'Wisdom'), ('Intimidation', 'Charisma'), ('Investigation', 'Intelligence'),
        ('Medicine', 'Wisdom'), ('Nature', 'Intelligence'), ('Perception', 'Wisdom'),
        ('Performance', 'Charisma'), ('Persuasion', 'Charisma'), ('Religion', 'Intelligence'),
        ('Sleight of Hand', 'Dexterity'), ('Stealth', 'Dexterity'), ('Survival', 'Wisdom')
    ]
    
    skill_modifiers = []
    proficiency_bonus = 2  # TODO: Calculate based on level
    
    for skill_name, ability_name in all_skills:
        ability_score = character.get('ability_scores', {}).get(ability_name, 10)
        ability_modifier = (ability_score - 10) // 2
        
        is_proficient = skill_name in character.get('skill_proficiencies', [])
        prof_bonus = proficiency_bonus if is_proficient else 0
        
        # Check for special bonuses
        special_bonus = 0
        bonus_source = ''
        for bonus in calculated_bonuses:
            if skill_name in bonus['skills']:
                special_bonus = bonus['value']
                bonus_source = bonus['source']
                break
        
        total_modifier = ability_modifier + prof_bonus + special_bonus
        
        skill_modifiers.append({
            'name': skill_name,
            'ability': ability_name,
            'ability_score': ability_score,
            'ability_modifier': ability_modifier,
            'proficiency_bonus': prof_bonus,
            'is_proficient': is_proficient,
            'proficiency_source': skill_sources.get(skill_name, ''),
            'special_bonus': special_bonus,
            'bonus_source': bonus_source,
            'total_modifier': total_modifier
        })
    
    # Calculate combat stats
    dex_modifier = (character.get('ability_scores', {}).get('Dexterity', 10) - 10) // 2
    wis_modifier = (character.get('ability_scores', {}).get('Wisdom', 10) - 10) // 2
    
    # Get hit die from class data
    hit_die = 8  # Default
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        hit_die = class_data.get('hit_die', 8)
    
    combat_stats = {
        'initiative': dex_modifier,
        'armor_class': 10 + dex_modifier,  # Base AC without equipment
        'passive_perception': 10 + wis_modifier + (proficiency_bonus if 'Perception' in character.get('skill_proficiencies', []) else 0),
        'hit_dice': f"{character.get('level', 1)}d{hit_die}"
    }
    
    # Calculate saving throw modifiers
    saving_throws = []
    abilities_order = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
    
    # Get class saving throw proficiencies
    saving_throw_profs = []
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        saving_throw_profs = class_data.get('saving_throw_proficiencies', [])
    
    for ability_name in abilities_order:
        ability_score = character.get('ability_scores', {}).get(ability_name, 10)
        ability_modifier = (ability_score - 10) // 2
        
        is_proficient = ability_name in saving_throw_profs
        prof_bonus = proficiency_bonus if is_proficient else 0
        
        total_modifier = ability_modifier + prof_bonus
        
        # Check for special conditions using effects system
        special_notes = []
        
        # Check effects for grant_save_advantage
        if 'effects' in character:
            for effect in character['effects']:
                if effect.get('type') == 'grant_save_advantage':
                    # Check if this effect applies to current ability
                    affected_abilities = effect.get('abilities', [])
                    if ability_name in affected_abilities:
                        display_text = effect.get('display', 'Advantage')
                        source = effect.get('source', '')
                        if source:
                            special_notes.append(f"{display_text} (from {source})")
                        else:
                            special_notes.append(display_text)
        
        saving_throws.append({
            'ability': ability_name,
            'ability_score': ability_score,
            'ability_modifier': ability_modifier,
            'proficiency_bonus': prof_bonus,
            'is_proficient': is_proficient,
            'total_modifier': total_modifier,
            'special_notes': special_notes
        })
    
    # Store both formats in session
    session['character'] = character
    session['character_sheet'] = comprehensive_character
    session.modified = True
    
    return render_template('character_summary.html', 
                         character=character,
                         character_sheet=comprehensive_character,
                         spells_by_level=spells_by_level,
                         spell_slots=spell_slots,
                         weapon_proficiencies=weapon_proficiencies,
                         armor_proficiencies=armor_proficiencies,
                         ability_bonuses=calculated_bonuses,
                         skill_modifiers=skill_modifiers,
                         saving_throws=saving_throws,
                         combat_stats=combat_stats)

@app.route('/download-character')
def download_character():
    """Download character as comprehensive JSON file."""
    if 'character' not in session:
        return redirect(url_for('index'))
    
    character = session['character']
    
    # Convert to comprehensive character sheet format
    comprehensive_character = character_sheet_converter.convert_to_character_sheet(character)
    
    filename = f"{comprehensive_character['character_info']['character_name'].lower().replace(' ', '_')}_character.json"
    
    response = app.response_class(
        response=json.dumps(comprehensive_character, indent=2),
        status=200,
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/api/character-sheet')
def api_character_sheet():
    """Return comprehensive character sheet as JSON API response."""
    if 'character' not in session:
        return jsonify({"error": "No character in session"}), 400
    
    character = session['character']
    comprehensive_character = character_sheet_converter.convert_to_character_sheet(character)
    
    return jsonify(comprehensive_character)

@app.route('/download-character-pdf')
def download_character_pdf():
    """Download character as filled PDF character sheet."""
    if 'character' not in session or session['character']['step'] != 'complete':
        return redirect(url_for('index'))
    
    from utils.pdf_writer import generate_character_sheet_pdf
    from flask import send_file
    import io
    
    # Get character builder from session
    builder = get_builder_from_session()
    character = builder.to_json()
    
    # Add calculated values from character_summary
    character_sheet = character_sheet_converter.convert_to_character_sheet(session['character'])
    
    # Extract combat stats
    character['combat_stats'] = character_sheet['combat_stats']
    character['max_hp'] = character_sheet['combat_stats']['hit_point_maximum']
    
    # Extract saving throws from ability_scores
    ability_scores = character_sheet.get('ability_scores', {})
    saving_throws = {}
    for ability, data in ability_scores.items():
        saving_throws[ability.title()] = {
            'modifier': data.get('modifier', 0),
            'proficient': data.get('saving_throw_proficient', False),
            'total': data.get('saving_throw', 0)
        }
    character['saving_throws'] = saving_throws
    
    # Extract skill modifiers from skills
    skills = character_sheet.get('skills', {})
    skill_modifiers = {}
    for skill, data in skills.items():
        skill_name = skill.replace('_', ' ').title()
        skill_modifiers[skill_name] = {
            'modifier': data.get('bonus', 0),
            'proficient': data.get('proficient', False),
            'expertise': data.get('expertise', False),
            'total': data.get('bonus', 0)
        }
    character['skill_modifiers'] = skill_modifiers
    
    # Calculate spell slots
    class_name = character.get('class')
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        if 'spell_slots_by_level' in class_data:
            character_level = character.get('level', 1)
            level_str = str(character_level)
            slots_array = class_data['spell_slots_by_level'].get(level_str, [0]*9)
            
            spell_slots = {}
            for spell_level in range(1, 10):
                if spell_level - 1 < len(slots_array) and slots_array[spell_level - 1] > 0:
                    spell_slots[spell_level] = slots_array[spell_level - 1]
            character['spell_slots'] = spell_slots
    
    # Generate PDF
    pdf_bytes = generate_character_sheet_pdf(character)
    
    # Create filename
    char_name = character.get('name', 'character').replace(' ', '_')
    filename = f"{char_name}_character_sheet.pdf"
    
    # Return as downloadable file
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.route('/character-sheet')
def character_sheet():
    """Display fillable HTML character sheet."""
    if 'character' not in session or session['character']['step'] != 'complete':
        return redirect(url_for('index'))
    
    # Get character builder from session
    builder = get_builder_from_session()
    character = builder.to_json()
    
    # Get comprehensive character sheet data (all calculations already done)
    character_sheet_data = character_sheet_converter.convert_to_character_sheet(session['character'])
    
    # Extract ability modifiers (already calculated)
    ability_modifiers = {}
    for ability, data in character_sheet_data.get('ability_scores', {}).items():
        modifier = data.get('modifier', 0)
        # Capitalize ability name to match template expectations (Strength, Dexterity, etc.)
        ability_modifiers[ability.capitalize()] = f"{'+' if modifier >= 0 else ''}{modifier}"
    
    # Extract combat stats (already calculated)
    combat_stats = character_sheet_data['combat_stats']
    
    # Extract saving throws (already calculated)
    ability_scores_data = character_sheet_data.get('ability_scores', {})
    saving_throws = {}
    for ability, data in ability_scores_data.items():
        saving_throws[ability.title()] = {
            'modifier': data.get('modifier', 0),
            'proficient': data.get('saving_throw_proficient', False),
            'total': data.get('saving_throw', 0)
        }
    
    # Extract skill modifiers (already calculated)
    skills_data = character_sheet_data.get('skills', {})
    skill_modifiers = {}
    for skill, data in skills_data.items():
        skill_name = skill.replace('_', ' ').title()
        skill_modifiers[skill_name] = {
            'modifier': data.get('bonus', 0),
            'proficient': data.get('proficient', False),
            'expertise': data.get('expertise', False),
            'total': data.get('bonus', 0)
        }
    
    # Get size from character data (already determined by builder)
    size = character.get('size', 'Medium')
    
    # Get passive perception (already calculated - 10 + perception bonus)
    perception_data = skills_data.get('perception', {})
    passive_perception = 10 + perception_data.get('bonus', 0)
    
    # Get proficiency bonus (already calculated in combat_stats)
    proficiency_bonus = combat_stats.get('proficiency_bonus', 2)
    
    # Extract features (already organized by category)
    features = character_sheet_data.get('features_and_traits', {})
    
    return render_template('character_sheet_pdf.html',
                         character=character,
                         ability_modifiers=ability_modifiers,
                         combat_stats=combat_stats,
                         saving_throws=saving_throws,
                         skill_modifiers=skill_modifiers,
                         size=size,
                         passive_perception=passive_perception,
                         proficiency_bonus=proficiency_bonus,
                         features=features)

@app.route('/reset')
def reset():
    """Reset character creation session."""
    session.clear()
    # Render a page that clears sessionStorage before redirecting
    return render_template('reset.html')

@app.route('/test-session')
def test_session():
    """Test route to check session functionality."""
    if 'test_counter' not in session:
        session['test_counter'] = 0
    session['test_counter'] += 1
    session.permanent = True
    session.modified = True
    return f"Session test - Counter: {session['test_counter']}, Session keys: {list(session.keys())}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)