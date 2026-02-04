from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import timedelta
from interactive_character_creator import CharacterCreator
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

def _extract_hp_bonuses_from_character(character):
    """Extract HP bonuses from character traits and features."""
    hp_bonuses = []
    
    # Check species traits
    species_data = character.get('species_data', {})
    traits = species_data.get('traits', {})
    
    # Look for Dwarven Toughness
    if 'Dwarven Toughness' in traits:
        hp_bonuses.append({
            "source": "Dwarven Toughness",
            "value": 1,
            "scaling": "per_level"
        })
    
    # Check other features (could be extended for class features, feats, etc.)
    features = character.get('features', {})
    
    # Check all feature categories for HP bonuses
    for category in ['class', 'species', 'lineage', 'background', 'feats']:
        category_features = features.get(category, [])
        for feature in category_features:
            # Look for HP-boosting features in character features
            feature_name = feature.get('name', '')
            feature_desc = feature.get('description', '')
            if 'HP' in feature_name or 'hit point' in feature_desc.lower():
                # Parse feature for HP bonuses (would need specific parsing logic)
                pass
    
    return hp_bonuses

# Initialize the character creator
character_creator = CharacterCreator()
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
            "physical_attributes": {
                "creature_type": "Humanoid",
                "size": "Medium",
                "speed": 30,
                "darkvision": 0
            },
            "choices_made": {},
            "step": "class"
        }

        if selected_alignment:
            character_data["choices_made"]["alignment"] = selected_alignment
        
        session.clear()  # Clear any existing session data
        session['character'] = character_data
        session.permanent = True
        session.modified = True
        
        print(f"Session created with character: {character_data['name']}")
        print(f"Session after save: {dict(session)}")
        
        # Instead of redirect, render the class selection page directly
        classes = dict(sorted(character_creator.classes.items()))
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
    classes = dict(sorted(character_creator.classes.items()))
    return render_template('choose_class.html', classes=classes)

@app.route('/select-class', methods=['POST'])
def select_class():
    """Handle class selection."""
    print(f"Select class accessed. Session keys: {list(session.keys())}")  # Debug
    
    class_name = request.form.get('class')
    if not class_name or class_name not in character_creator.classes:
        print(f"Invalid class selection: {class_name}")  # Debug
        return redirect(url_for('choose_class'))
    
    # Check if character exists in session
    if 'character' not in session:
        print("No character in session during class selection")  # Debug
        # Create a minimal character if session was lost
        character = {
            "name": "Character",
            "level": 1,
            "class": "",
            "background": "",
            "species": "",
            "lineage": "",
            "alignment": "",
            "ability_scores": {
                "Strength": 10, "Dexterity": 10, "Constitution": 10,
                "Intelligence": 10, "Wisdom": 10, "Charisma": 10
            },
            "skill_proficiencies": [],
            "languages": ["Common"],
            "equipment": [],
            "features": [],
            "physical_attributes": {
                "creature_type": "Humanoid",
                "size": "Medium",
                "speed": 30,
                "darkvision": 0
            },
            "choices_made": {},
            "step": "class"
        }
    else:
        character = session['character']
    
    character['class'] = class_name
    character['step'] = 'class_choices'  # Default next step
    
    # Check if subclass selection is needed first (level 3+ characters)
    character_level = character.get('level', 1)
    
    if character_level >= 3:
        class_data = character_creator.classes[class_name]
        subclass_level = class_data.get('subclass_selection_level', 3)
        
        if character_level >= subclass_level:
            character['step'] = 'subclass'
            session['character'] = character
            session.modified = True
            print(f"Class selected: {class_name}, redirecting to subclass selection")
            return redirect(url_for('choose_subclass'))
    
    session['character'] = character
    session.modified = True
    print(f"Class selected: {class_name}, redirecting to class choices")
    return redirect(url_for('class_choices'))

@app.route('/choose-subclass')
def choose_subclass():
    """Dedicated subclass selection step."""
    if 'character' not in session or session['character']['step'] != 'subclass':
        return redirect(url_for('index'))
    
    character = session['character']
    class_name = character.get('class', '')
    
    if not class_name or class_name not in character_creator.classes:
        return redirect(url_for('choose_class'))
    
    # Load subclasses for this class
    subclasses = character_creator.get_subclasses_for_class(class_name)
    
    if not subclasses:
        # No subclasses available, skip to class choices
        character['step'] = 'class_choices'
        session['character'] = character
        return redirect(url_for('class_choices'))
    
    return render_template('choose_subclass.html', 
                         subclasses=subclasses, 
                         class_name=class_name,
                         character_level=character.get('level', 1))

@app.route('/select-subclass', methods=['POST'])
def select_subclass():
    """Handle subclass selection and redirect to class choices."""
    if 'character' not in session:
        return redirect(url_for('index'))
        
    subclass_name = request.form.get('subclass')
    if not subclass_name:
        return redirect(url_for('choose_subclass'))
    
    character = session['character']
    character['subclass'] = subclass_name
    character['step'] = 'class_choices'
    session['character'] = character
    
    print(f"Subclass selected: {subclass_name}, redirecting to class choices")
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
    
    if class_name not in character_creator.classes:
        return redirect(url_for('choose_class'))
    
    class_data = character_creator.classes[class_name]
    
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
        subclass_data = character_creator.get_subclasses_for_class(class_name).get(subclass_name, {})
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
        armor_training_parts.extend(other_armor)
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
                            
                            # Load cantrip options
                            class_lower = spell_list.lower()
                            spell_file_path = f"spells/{class_lower}/0.json"
                            cantrip_options = _resolve_choice_options(
                                {'source': {'type': 'external', 'file': spell_file_path, 'list': 'spells'}},
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
                                    'option_descriptions': _get_option_descriptions(
                                        {'choices': {'source': {'type': 'external', 'file': spell_file_path, 'list': 'spells'}}},
                                        {'source': {'type': 'external', 'file': spell_file_path, 'list': 'spells'}},
                                        class_data,
                                        None
                                    )
                                }
                                choices.append(choice)
    
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
    print(f"Submit class choices accessed. Session keys: {list(session.keys())}")  # Debug
    
    if 'character' not in session:
        print("No character in session during submit class choices")  # Debug
        # Create a default character if session was lost
        character = {
            "name": "Character",
            "level": 1,
            "class": "Fighter",
            "background": "",
            "species": "",
            "lineage": "",
            "alignment": "",
            "ability_scores": {
                "Strength": 10, "Dexterity": 10, "Constitution": 10,
                "Intelligence": 10, "Wisdom": 10, "Charisma": 10
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
            "physical_attributes": {
                "creature_type": "Humanoid",
                "size": "Medium",
                "speed": 30,
                "darkvision": 0
            },
            "choices_made": {},
            "step": "background"
        }
    else:
        character = session['character']
    
    # Process form data
    print(f"Form data received: {dict(request.form.lists())}")  # Debug
    
    for key, values in request.form.lists():
        if key == 'skills':
            # Clear ALL class skill choices and rebuild from scratch to avoid background contamination
            # Remove all previous class skill choices
            old_skills = character['choices_made'].get('skill_choices', [])
            for old_skill in old_skills:
                if old_skill in character['skill_proficiencies']:
                    character['skill_proficiencies'].remove(old_skill)
            
            # Set new skill choices
            character['choices_made']['skill_choices'] = list(values)
            character['skill_proficiencies'].extend(values)
            print(f"Skills processed: {values}")  # Debug
            
            # Clean up any background skills that shouldn't be there
            # This fixes the issue where changing backgrounds leaves old skills
            background_name = character.get('background')
            if background_name and background_name in character_creator.backgrounds:
                bg_data = character_creator.backgrounds[background_name]
                bg_skills = bg_data.get('skill_proficiencies', [])
                # Remove any skills that are NOT from current background or class choices
                skills_to_keep = set(values) | set(bg_skills) if bg_skills else set(values)
                character['skill_proficiencies'] = [s for s in character['skill_proficiencies'] if s in skills_to_keep]
                print(f"Cleaned skill proficiencies to: {character['skill_proficiencies']}")  # Debug
            
        elif key.startswith('choice_'):
            choice_name = key.replace('choice_', '')
            if len(values) == 1:
                character['choices_made'][choice_name] = values[0]
                # Special handling for subclass selection
                if 'subclass' in choice_name.lower():
                    character['subclass'] = values[0]
                    print(f"Subclass set: {values[0]}")  # Debug
            else:
                character['choices_made'][choice_name] = values
            print(f"Feature choice '{choice_name}': {values}")  # Debug
    
    # Clear and re-add ALL class features up to character level
    class_name = character.get('class', '')
    character_level = character.get('level', 1)
    subclass_name = character.get('subclass')
    
    # Clear existing class features to avoid duplicates on re-submission
    character['features']['class'] = []
    
    if class_name and class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
        choices_made = character.get('choices_made', {})
        
        # Add all class features up to character level
        features_by_level = class_data.get('features_by_level', {})
        for level in range(1, character_level + 1):
            level_str = str(level)
            if level_str in features_by_level:
                level_features = features_by_level[level_str]
                for feature_name, feature_data in level_features.items():
                    # Handle choice-based features
                    if isinstance(feature_data, dict) and 'choices' in feature_data:
                        # Get the base description
                        base_description = feature_data.get('description', '')
                        
                        # Find the choice made for this feature
                        # Try multiple possible keys: the 'name' field from choices, the feature_name itself, and normalized versions
                        choice_key = feature_data['choices'].get('name', feature_name.lower().replace(' ', '_'))
                        chosen_option = choices_made.get(choice_key)
                        
                        # Also try the feature name as-is (for backward compatibility)
                        if not chosen_option:
                            chosen_option = choices_made.get(feature_name)
                        
                        # Also check for level-specific choice keys (e.g., weapon_mastery_4)
                        if not chosen_option:
                            level_specific_key = f"{choice_key}_{level}"
                            chosen_option = choices_made.get(level_specific_key)
                        
                        if chosen_option:
                            # Get detailed description from option_descriptions or internal list
                            option_desc = ""
                            choices_data = feature_data['choices']
                            source = choices_data.get('source', {})
                            
                            if source.get('type') == 'internal':
                                list_name = source.get('list', '')
                                if list_name in class_data:
                                    option_list = class_data[list_name]
                                    if isinstance(option_list, dict):
                                        if isinstance(chosen_option, list):
                                            # Multiple choices
                                            option_desc = ", ".join(chosen_option)
                                            detailed_descs = [option_list.get(opt, "") for opt in chosen_option if opt in option_list]
                                            if any(detailed_descs):
                                                option_desc += ": " + " | ".join(detailed_descs)
                                        else:
                                            # Single choice
                                            option_desc = option_list.get(chosen_option, chosen_option)
                                    else:
                                        option_desc = ", ".join(chosen_option) if isinstance(chosen_option, list) else chosen_option
                            else:
                                option_desc = ", ".join(chosen_option) if isinstance(chosen_option, list) else chosen_option
                            
                            # Ensure option_desc is a string
                            if isinstance(option_desc, dict):
                                # Extract description if it's a structured object
                                option_desc = option_desc.get('description', str(option_desc))
                            
                            # Create feature entry with choice details
                            feature_entry = {
                                "name": f"{feature_name}: {', '.join(chosen_option) if isinstance(chosen_option, list) else chosen_option}",
                                "description": f"{base_description}\n\nChosen: {option_desc}" if option_desc and isinstance(option_desc, str) else base_description,
                                "source": f"{class_name} Level {level}"
                            }
                            character['features']['class'].append(feature_entry)
                        continue
                    
                    # Non-choice features
                    feature_entry = {
                        "name": feature_name,
                        "description": feature_data if isinstance(feature_data, str) else feature_data.get('description', ''),
                        "source": f"{class_name} Level {level}"
                    }
                    character['features']['class'].append(feature_entry)
        
        # Add subclass features if subclass is selected
        if subclass_name:
            subclass_data = character_creator.get_subclasses_for_class(class_name).get(subclass_name, {})
            subclass_features = subclass_data.get('features_by_level', {})
            for level in range(1, character_level + 1):
                level_str = str(level)
                if level_str in subclass_features:
                    level_features = subclass_features[level_str]
                    for feature_name, feature_data in level_features.items():
                        # Handle choice-based subclass features
                        if isinstance(feature_data, dict) and 'choices' in feature_data:
                            base_description = feature_data.get('description', '')
                            choice_key = feature_data['choices'].get('name', f"subclass_{feature_name.lower().replace(' ', '_')}")
                            chosen_option = choices_made.get(choice_key)
                            
                            # Also try the feature name with "subclass_" prefix (for backward compatibility)
                            if not chosen_option:
                                chosen_option = choices_made.get(f"subclass_{feature_name}")
                            
                            if chosen_option:
                                option_desc = ""
                                choices_data = feature_data['choices']
                                source = choices_data.get('source', {})
                                
                                if source.get('type') == 'internal':
                                    list_name = source.get('list', '')
                                    if list_name in subclass_data:
                                        option_list = subclass_data[list_name]
                                        if isinstance(option_list, dict):
                                            if isinstance(chosen_option, list):
                                                option_desc = ", ".join(chosen_option)
                                                detailed_descs = [option_list.get(opt, "") for opt in chosen_option if opt in option_list]
                                                if any(detailed_descs):
                                                    option_desc += ": " + " | ".join(detailed_descs)
                                            else:
                                                option_desc = option_list.get(chosen_option, chosen_option)
                                        else:
                                            option_desc = ", ".join(chosen_option) if isinstance(chosen_option, list) else chosen_option
                                else:
                                    option_desc = ", ".join(chosen_option) if isinstance(chosen_option, list) else chosen_option
                                
                                feature_entry = {
                                    "name": f"{feature_name}: {', '.join(chosen_option) if isinstance(chosen_option, list) else chosen_option}",
                                    "description": f"{base_description}\n\nChosen: {option_desc}" if option_desc and not isinstance(subclass_data.get(source.get('list', '')), dict) else base_description + "\n\n" + option_desc,
                                    "source": f"{subclass_name} Level {level}"
                                }
                                character['features']['class'].append(feature_entry)
                            continue
                        
                        # Non-choice subclass features
                        feature_entry = {
                            "name": feature_name,
                            "description": feature_data if isinstance(feature_data, str) else feature_data.get('description', ''),
                            "source": f"{subclass_name} Level {level}"
                        }
                        character['features']['class'].append(feature_entry)
    
    print(f"DEBUG: Total class features added: {len(character['features']['class'])}")  # Debug
    print(f"DEBUG: Feature names: {[f['name'] for f in character['features']['class']]}")  # Debug
    print(f"DEBUG: Choices made: {character.get('choices_made', {})}")  # Debug
    
    # Initialize effects array if not exists
    if 'effects' not in character:
        character['effects'] = []
    
    # Collect effects from class features (non-choice features with effects)
    if class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
        features_by_level = class_data.get('features_by_level', {})
        for level in range(1, character_level + 1):
            level_str = str(level)
            if level_str in features_by_level:
                level_features = features_by_level[level_str]
                for feature_name, feature_data in level_features.items():
                    # Skip choice-based features (those are handled separately)
                    if isinstance(feature_data, dict) and 'choices' not in feature_data and 'effects' in feature_data:
                        for effect in feature_data.get('effects', []):
                            if isinstance(effect, dict):
                                min_level = effect.get('min_level')
                                if isinstance(min_level, int) and character.get('level', 1) < min_level:
                                    continue
                                effect_with_source = effect.copy()
                                effect_with_source['source'] = feature_name
                                # Check if effect already exists to avoid duplicates
                                existing = any(
                                    e.get('type') == effect_with_source.get('type') and 
                                    e.get('spell') == effect_with_source.get('spell') and
                                    e.get('source') == effect_with_source.get('source')
                                    for e in character['effects']
                                )
                                if not existing:
                                    character['effects'].append(effect_with_source)
                                    print(f"DEBUG: Added class feature effect: {effect_with_source}")
    
    # Collect effects from subclass features (non-choice features with effects)
    if subclass_name:
        subclass_data = character_creator.get_subclasses_for_class(class_name).get(subclass_name, {})
        subclass_features = subclass_data.get('features_by_level', {})
        for level in range(1, character_level + 1):
            level_str = str(level)
            if level_str in subclass_features:
                level_features = subclass_features[level_str]
                for feature_name, feature_data in level_features.items():
                    # Skip choice-based features (those are handled separately)
                    if isinstance(feature_data, dict) and 'choices' not in feature_data and 'effects' in feature_data:
                        for effect in feature_data.get('effects', []):
                            if isinstance(effect, dict):
                                min_level = effect.get('min_level')
                                if isinstance(min_level, int) and character.get('level', 1) < min_level:
                                    continue
                                effect_with_source = effect.copy()
                                effect_with_source['source'] = feature_name
                                # Check if effect already exists to avoid duplicates
                                existing = any(
                                    e.get('type') == effect_with_source.get('type') and 
                                    e.get('spell') == effect_with_source.get('spell') and
                                    e.get('source') == effect_with_source.get('source')
                                    for e in character['effects']
                                )
                                if not existing:
                                    character['effects'].append(effect_with_source)
                                    print(f"DEBUG: Added subclass feature effect: {effect_with_source}")
    
    # Clear ability bonuses and proficiencies before re-applying to avoid duplicates
    character['ability_bonuses'] = []
    character['weapon_proficiencies'] = []
    character['armor_proficiencies'] = []
    
    # Apply effects from all selected choices (generic, data-driven approach)
    # This handles grant_weapon_proficiency, grant_armor_proficiency, ability_bonus, etc.
    if class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
        
        for choice_key, choice_value in character.get('choices_made', {}).items():
            # Only process string-type single selections
            if not isinstance(choice_value, str):
                continue
            
            # Find this choice value in class_data and check for effects
            for data_key, data_dict in class_data.items():
                if isinstance(data_dict, dict) and choice_value in data_dict:
                    option_data = data_dict[choice_value]
                    if isinstance(option_data, dict) and 'effects' in option_data:
                        # Apply each effect
                        for effect in option_data.get('effects', []):
                            effect_type = effect.get('type')
                            
                            if effect_type == 'grant_weapon_proficiency':
                                # Add weapon proficiencies
                                proficiencies = effect.get('proficiencies', [])
                                if 'weapon_proficiencies' not in character:
                                    character['weapon_proficiencies'] = []
                                for prof in proficiencies:
                                    if prof not in character['weapon_proficiencies']:
                                        character['weapon_proficiencies'].append(prof)
                                        print(f"DEBUG: Added weapon proficiency: {prof}")
                            
                            elif effect_type == 'grant_armor_proficiency':
                                # Add armor proficiencies
                                proficiencies = effect.get('proficiencies', [])
                                if 'armor_proficiencies' not in character:
                                    character['armor_proficiencies'] = []
                                for prof in proficiencies:
                                    if prof not in character['armor_proficiencies']:
                                        character['armor_proficiencies'].append(prof)
                                        print(f"DEBUG: Added armor proficiency: {prof}")
                            
                            elif effect_type == 'ability_bonus':
                                # Store ability bonuses for later application
                                # These are conditional bonuses (like WIS bonus to INT checks)
                                if 'ability_bonuses' not in character:
                                    character['ability_bonuses'] = []
                                bonus_info = {
                                    'ability': effect.get('ability'),
                                    'skills': effect.get('skills', []),
                                    'value': effect.get('value'),
                                    'minimum': effect.get('minimum'),
                                    'source': f"{choice_value} ({data_key})"
                                }
                                character['ability_bonuses'].append(bonus_info)
                                print(f"DEBUG: Added ability bonus: {bonus_info}")
    
    # Check if any choices we just made trigger additional choices (via effects system)
    # If so, redirect back to class_choices to show the new choices
    has_pending_choices = False
    for choice_key, choice_value in character.get('choices_made', {}).items():
        # Only check string-type single selections (skip lists, dicts, etc.)
        if not isinstance(choice_value, str):
            continue
            
        # Scan class_data for any selected options with grant_cantrip_choice effects
        if class_name in character_creator.classes:
            class_data = character_creator.classes[class_name]
            for data_key, data_dict in class_data.items():
                if isinstance(data_dict, dict) and choice_value in data_dict:
                    option_data = data_dict[choice_value]
                    if isinstance(option_data, dict) and 'effects' in option_data:
                        for effect in option_data.get('effects', []):
                            if effect.get('type') == 'grant_cantrip_choice':
                                # Check if the bonus choice has been made
                                bonus_feature_name = f'{choice_value}_bonus_cantrip'
                                if bonus_feature_name not in character['choices_made']:
                                    has_pending_choices = True
                                    print(f"DEBUG: Pending bonus cantrip choice for {choice_value}")  # Debug
                                    break
                if has_pending_choices:
                    break
        if has_pending_choices:
            break
    
    if has_pending_choices:
        # Redirect back to class_choices to show the bonus cantrip choice
        session['character'] = character
        return redirect(url_for('class_choices'))
    
    character['step'] = 'background'
    session['character'] = character
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
    
    backgrounds = dict(sorted(character_creator.backgrounds.items()))
    return render_template('choose_background.html', backgrounds=backgrounds, character=character)

@app.route('/select-background', methods=['POST'])
def select_background():
    """Handle background selection."""
    background_name = request.form.get('background')
    if not background_name or background_name not in character_creator.backgrounds:
        return redirect(url_for('choose_background'))
    
    character = session['character']
    old_background = character.get('background')
    
    # If changing backgrounds, remove old background skills and features
    if old_background and old_background != background_name:
        old_background_data = character_creator.backgrounds.get(old_background, {})
        
        # Remove old background skills
        if 'skill_proficiencies' in old_background_data:
            old_skills = old_background_data['skill_proficiencies']
            if isinstance(old_skills, list):
                for skill in old_skills:
                    if skill in character['skill_proficiencies']:
                        character['skill_proficiencies'].remove(skill)
        
        # Remove old background features
        character['features']['background'] = [
            f for f in character['features']['background']
            if old_background not in f.get('source', '')
        ]
        
        # Remove old background feat
        character['features']['feats'] = [
            f for f in character['features']['feats']
            if f.get('source') != f"{old_background} Background"
        ]
    
    character['background'] = background_name
    
    # Apply new background skill proficiencies (only if not already there)
    background_data = character_creator.backgrounds[background_name]
    if 'skill_proficiencies' in background_data:
        background_skills = background_data['skill_proficiencies']
        if isinstance(background_skills, list):
            for skill in background_skills:
                if skill not in character['skill_proficiencies']:
                    character['skill_proficiencies'].append(skill)
        print(f"Applied background skills: {background_skills}")
    
    # Add background features (only if not already there)
    if 'features' in background_data:
        existing_feature_names = {f['name'] for f in character['features']['background']}
        for feature_name, feature_data in background_data['features'].items():
            if feature_name not in existing_feature_names:
                feature_entry = {
                    "name": feature_name,
                    "description": feature_data if isinstance(feature_data, str) else feature_data.get('description', ''),
                    "source": f"{background_name} Background"
                }
                character['features']['background'].append(feature_entry)
    
    # Add feat from background
    if 'feat' in background_data:
        feat_name = background_data['feat']
        # Extract base feat name (remove parenthetical specifications like "(Cleric)")
        base_feat_name = feat_name.split('(')[0].strip()
        
        # Check if feat already exists
        existing_feat_names = {f['name'] for f in character['features']['feats']}
        if feat_name not in existing_feat_names:
            # Try to load feat data
            feat_data = character_creator.feats.get(base_feat_name, {})
            
            if feat_data:
                feat_entry = {
                    "name": feat_name,  # Use full name with specification
                    "description": feat_data.get('description', ''),
                    "benefits": feat_data.get('benefits', []),
                    "source": f"{background_name} Background"
                }
                character['features']['feats'].append(feat_entry)
                print(f"Added feat: {feat_name}")
            else:
                # Feat data not found, add basic entry
                feat_entry = {
                    "name": feat_name,
                    "description": f"Feat granted by {background_name} background.",
                    "source": f"{background_name} Background"
                }
                character['features']['feats'].append(feat_entry)
                print(f"Added feat (no data): {feat_name}")
    
    character['step'] = 'species'
    
    session['character'] = character
    return redirect(url_for('choose_species'))

@app.route('/choose-species')
def choose_species():
    """Species selection step."""
    if 'character' not in session:
        return redirect(url_for('index'))
    
    character = session['character']
    # Ensure background is selected before accessing species
    if not character.get('background'):
        return redirect(url_for('choose_background'))
    
    # Update step to species when accessing this page
    session['character']['step'] = 'species'
    session.modified = True
    
    species = dict(sorted(character_creator.species.items()))
    return render_template('choose_species.html', species=species, character=character)

@app.route('/select-species', methods=['POST'])
def select_species():
    """Handle species selection."""
    species_name = request.form.get('species')
    if not species_name or species_name not in character_creator.species:
        return redirect(url_for('choose_species'))
    
    character = session['character']
    old_species = character.get('species')
    character['species'] = species_name
    
    # Store complete species data for HP calculation and other features
    species_data = character_creator.species[species_name]
    character['species_data'] = species_data
    
    # Ensure features is properly structured (handle legacy characters)
    if not isinstance(character.get('features'), dict):
        character['features'] = {
            "class": [],
            "species": [],
            "lineage": [],
            "background": [],
            "feats": []
        }
    
    # Clear old species features and effects if changing species (or reselecting same species)
    character['features']['species'] = []
    
    # Initialize effects array if not present
    if 'effects' not in character:
        character['effects'] = []
    
    # Process species traits and add to features
    if 'traits' in species_data:
        for trait_name, trait_data in species_data['traits'].items():
            if isinstance(trait_data, str):
                # Simple trait
                feature_entry = {
                    "name": trait_name,
                    "description": trait_data,
                    "source": f"{species_name} Species"
                }
                character['features']['species'].append(feature_entry)
            elif isinstance(trait_data, dict) and trait_data.get('type') != 'choice':
                # Complex trait (non-choice)
                description = trait_data.get('description', str(trait_data))
                feature_entry = {
                    "name": trait_name,
                    "description": description,
                    "source": f"{species_name} Species"
                }
                character['features']['species'].append(feature_entry)
                
                # Apply effects from this trait
                if 'effects' in trait_data:
                    for effect in trait_data['effects']:
                        if isinstance(effect, dict):
                            min_level = effect.get('min_level')
                            if isinstance(min_level, int) and character.get('level', 1) < min_level:
                                continue
                        effect_with_source = effect.copy()
                        effect_with_source['source'] = trait_name
                        character['effects'].append(effect_with_source)
    
    # Check if species has trait choices (like Keen Senses)
    species_data = character_creator.species[species_name]
    has_trait_choices = False
    
    if 'traits' in species_data:
        for trait_name, trait_data in species_data['traits'].items():
            if isinstance(trait_data, dict) and trait_data.get('type') == 'choice':
                has_trait_choices = True
                break
    
    if has_trait_choices:
        character['step'] = 'species_traits'
        session['character'] = character
        return redirect(url_for('choose_species_traits'))
    
    # Check if species has lineages
    species_data = character_creator.species[species_name]
    if species_data.get('lineages'):
        character['step'] = 'lineage'
        session['character'] = character
        return redirect(url_for('choose_lineage'))
    else:
        character['step'] = 'languages'
        session['character'] = character
        return redirect(url_for('choose_languages'))

@app.route('/choose-species-traits')
def choose_species_traits():
    """Species trait choice step (e.g., Keen Senses)."""
    if 'character' not in session or session['character']['step'] != 'species_traits':
        return redirect(url_for('index'))
    
    character = session['character']
    species_name = character['species']
    species_data = character_creator.species.get(species_name, {})
    
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
    """Handle species trait choices."""
    character = session['character']
    species_name = character['species']
    species_data = character_creator.species.get(species_name, {})
    
    # Process trait choices
    if 'traits' in species_data:
        for trait_name, trait_data in species_data['traits'].items():
            if isinstance(trait_data, dict) and trait_data.get('type') == 'choice':
                choice_key = f"trait_{trait_name.lower().replace(' ', '_')}"
                selected_option = request.form.get(choice_key)
                
                if selected_option:
                    # For skill-related traits, add to skill proficiencies
                    if trait_name == 'Keen Senses' and selected_option in ['Insight', 'Perception', 'Survival']:
                        if selected_option not in character['skill_proficiencies']:
                            character['skill_proficiencies'].append(selected_option)
                    
                    # Store the choice
                    if 'choices_made' not in character:
                        character['choices_made'] = {}
                    character['choices_made'][f'species_trait_{trait_name}'] = selected_option
                    print(f"Selected {trait_name}: {selected_option}")
    
    # Check if species has lineages
    species_data = character_creator.species[species_name]
    if species_data.get('lineages'):
        character['step'] = 'lineage'
        session['character'] = character
        return redirect(url_for('choose_lineage'))
    else:
        character['step'] = 'languages'
        session['character'] = character
        return redirect(url_for('choose_languages'))

@app.route('/choose-lineage')
def choose_lineage():
    """Lineage selection step."""
    if 'character' not in session or session['character']['step'] != 'lineage':
        return redirect(url_for('index'))
    
    character = session['character']
    species_name = character['species']
    
    # Get available lineages directly from species data
    species_data = character_creator.species.get(species_name, {})
    lineage_names = species_data.get('lineages', [])
    
    lineages = {}
    lineage_dir = Path(character_creator.data_dir) / 'species_variants'
    
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
    
    character = session['character']
    character['lineage'] = lineage_name
    
    # Apply lineage traits and modifications
    if lineage_name:
        # Convert lineage name to filename
        filename = lineage_name.lower().replace(' ', '_') + '.json'
        lineage_file = Path(character_creator.data_dir) / 'species_variants' / filename
        
        lineage_data = None
        try:
            if lineage_file.exists():
                with open(lineage_file, 'r') as f:
                    lineage_data = json.load(f)
                    print(f"Applying traits from: {filename}")  # Debug
            else:
                print(f"Warning: Lineage file not found: {filename}")  # Debug
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading lineage data: {e}")  # Debug
        
        # Ensure features is properly structured (handle legacy characters)
        if not isinstance(character.get('features'), dict):
            character['features'] = {
                "class": [],
                "species": [],
                "lineage": [],
                "background": [],
                "feats": []
            }

        # Clear old lineage features when changing lineage/reselecting
        character['features']['lineage'] = []

        # Initialize effects array if not present
        if 'effects' not in character:
            character['effects'] = []

        # Apply lineage modifications and traits
        if lineage_data:
            # Apply speed changes
            if 'speed' in lineage_data:
                character['physical_attributes']['speed'] = lineage_data['speed']
            
            # Apply darkvision changes
            if 'darkvision_range' in lineage_data:
                character['physical_attributes']['darkvision'] = lineage_data['darkvision_range']

            # Process lineage traits and add to features/effects
            traits = lineage_data.get('traits', {})
            if isinstance(traits, dict):
                for trait_name, trait_data in traits.items():
                    if isinstance(trait_data, str):
                        character['features']['lineage'].append({
                            "name": trait_name,
                            "description": trait_data,
                            "source": f"{lineage_name} Lineage"
                        })
                    elif isinstance(trait_data, dict):
                        description = trait_data.get('description', str(trait_data))
                        character['features']['lineage'].append({
                            "name": trait_name,
                            "description": description,
                            "source": f"{lineage_name} Lineage"
                        })

                        # Apply structured effects from this trait (generic, data-driven)
                        for effect in trait_data.get('effects', []) if isinstance(trait_data.get('effects', []), list) else []:
                            if isinstance(effect, dict):
                                min_level = effect.get('min_level')
                                if isinstance(min_level, int) and character.get('level', 1) < min_level:
                                    continue
                                effect_with_source = effect.copy()
                                effect_with_source['source'] = trait_name
                                character['effects'].append(effect_with_source)
            
            print(f"Applied lineage {lineage_name}: speed={character['physical_attributes']['speed']}, darkvision={character['physical_attributes']['darkvision']}")  # Debug
    
    if spellcasting_ability:
        character['spellcasting_ability'] = spellcasting_ability
        if 'choices_made' not in character:
            character['choices_made'] = {}
        character['choices_made']['lineage_spellcasting_ability'] = spellcasting_ability
    
    character['step'] = 'languages'
    
    session['character'] = character
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
    species_data = character_creator.species.get(character['species'], {})
    class_data = character_creator.classes.get(character['class'], {})
    
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
    character = session['character']
    
    # Get base languages
    species_data = character_creator.species.get(character['species'], {})
    class_data = character_creator.classes.get(character['class'], {})
    
    base_languages = set(['Common'])
    if 'languages' in species_data:
        base_languages.update(species_data['languages'])
    if 'languages' in class_data:
        base_languages.update(class_data['languages'])
    
    # Get selected additional languages
    additional_languages = request.form.getlist('languages')
    
    # Combine all languages
    all_languages = list(base_languages) + additional_languages
    character['languages'] = sorted(list(set(all_languages)))  # Remove duplicates and sort
    
    character['step'] = 'ability_scores'
    session['character'] = character
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
    class_data = character_creator.classes.get(class_name, {})
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
    character = session['character']
    assignment_method = request.form.get('assignment_method')
    
    if assignment_method == 'recommended':
        # Apply recommended allocation using existing logic
        class_name = character['class']
        class_data = character_creator.classes.get(class_name, {})
        
        # Handle both string and list formats for primary_ability
        primary_ability_data = class_data.get('primary_ability', '')
        if isinstance(primary_ability_data, list):
            primary_abilities = primary_ability_data
        elif isinstance(primary_ability_data, str):
            primary_abilities = primary_ability_data.split(', ') if primary_ability_data else []
        else:
            primary_abilities = []
        
        # Use the same logic from interactive_character_creator
        standard_array = [15, 14, 13, 12, 10, 8]
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        
        ability_mapping = {}
        remaining_values = standard_array.copy()
        remaining_abilities = abilities.copy()
        
        # Assign primary abilities first
        for primary_ability in primary_abilities:
            if primary_ability in remaining_abilities and remaining_values:
                ability_mapping[primary_ability] = remaining_values.pop(0)
                remaining_abilities.remove(primary_ability)
        
        # Assign Constitution next (if not already assigned)
        if "Constitution" in remaining_abilities and remaining_values:
            ability_mapping["Constitution"] = remaining_values.pop(0)
            remaining_abilities.remove("Constitution")
        
        # Assign remaining values
        for ability in remaining_abilities:
            if remaining_values:
                ability_mapping[ability] = remaining_values.pop(0)
        
        # Apply assignments
        for ability, score in ability_mapping.items():
            character["ability_scores"][ability] = score
            
        character['choices_made']['ability_scores'] = 'standard_array_recommended'
        
    else:  # manual
        # Get manual assignments from form
        for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            score = request.form.get(f'ability_{ability}')
            if score:
                character["ability_scores"][ability] = int(score)
        
        character['choices_made']['ability_scores'] = 'standard_array_manual'
    
    character['step'] = 'background_bonuses'
    session['character'] = character
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
    background_data = character_creator.backgrounds.get(background_name, {})
    
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
    character = session['character']
    assignment_method = request.form.get('assignment_method')
    
    if assignment_method == 'suggested':
        background_name = character['background']
        background_data = character_creator.backgrounds.get(background_name, {})
        
        if 'ability_score_increase' in background_data and 'suggested' in background_data['ability_score_increase']:
            suggested = background_data['ability_score_increase']['suggested']
            for ability, bonus in suggested.items():
                character["ability_scores"][ability] += bonus
            character['choices_made']['background_ability_score_assignment'] = suggested
    else:  # manual
        background_name = character['background']
        background_data = character_creator.backgrounds.get(background_name, {})
        
        # Get allowed ability options for this background
        allowed_abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]  # Default fallback
        if 'ability_score_increase' in background_data and 'options' in background_data['ability_score_increase']:
            allowed_abilities = background_data['ability_score_increase']['options']
        
        assignment = {}
        for ability in allowed_abilities:  # Only process allowed abilities
            bonus = request.form.get(f'bonus_{ability}')
            if bonus and int(bonus) > 0:
                bonus_val = int(bonus)
                character["ability_scores"][ability] += bonus_val
                assignment[ability] = bonus_val
        
        character['choices_made']['background_ability_score_assignment'] = assignment
    
    character['step'] = 'complete'
    session['character'] = character
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

                spell_list = effect.get('spell_list') or class_name
                if spell_list not in cantrip_cache:
                    cantrip_cache[spell_list] = _load_cantrips_for_spell_list(spell_list)

                cantrip_info = cantrip_cache.get(spell_list, {}).get(cantrip_name, {})
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
        
        # Load cantrip details from the spell file
        class_lower = class_name.lower()
        spell_file = Path(__file__).parent / "data" / "spells" / class_lower / "0.json"
        
        if spell_file.exists():
            try:
                with open(spell_file, 'r') as f:
                    spell_data = json.load(f)
                    all_cantrips = spell_data.get('spells', {})
                    
                    for cantrip_name in cantrips:
                        if cantrip_name in all_cantrips:
                            cantrip_info = all_cantrips[cantrip_name]
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
    if class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
        
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
                                            spell_file = Path(__file__).parent / "data" / "spells" / class_lower / "0.json"
                                            
                                            if spell_file.exists():
                                                try:
                                                    with open(spell_file, 'r') as f:
                                                        spell_data = json.load(f)
                                                        all_cantrips = spell_data.get('spells', {})
                                                        
                                                        if 0 not in spells_by_level:
                                                            spells_by_level[0] = []
                                                        
                                                        # Handle both single cantrip and list
                                                        cantrip_list = bonus_cantrips if isinstance(bonus_cantrips, list) else [bonus_cantrips]
                                                        
                                                        for cantrip_name in cantrip_list:
                                                            if cantrip_name in all_cantrips:
                                                                # Check for duplicates
                                                                existing_names = [s['name'] for s in spells_by_level[0]]
                                                                if cantrip_name not in existing_names:
                                                                    cantrip_info = all_cantrips[cantrip_name]
                                                                    spells_by_level[0].append({
                                                                        'name': cantrip_name,
                                                                        'school': cantrip_info.get('school', ''),
                                                                        'casting_time': cantrip_info.get('casting_time', ''),
                                                                        'range': cantrip_info.get('range', ''),
                                                                        'components': cantrip_info.get('components', ''),
                                                                        'duration': cantrip_info.get('duration', ''),
                                                                        'description': cantrip_info.get('description', ''),
                                                                        'source': f"{option_name} (from effects)"
                                                                    })
                                                except (json.JSONDecodeError, IOError) as e:
                                                    print(f"Warning: Could not load bonus cantrip details: {e}")
    
    # Add cantrips from subclass features (using structured effects system)
    subclass_name = character.get('subclass')
    if subclass_name and class_name:
        subclass_data = character_creator.get_subclasses_for_class(class_name).get(subclass_name, {})
        features_by_level = subclass_data.get('features_by_level', {})
        character_level = character.get('level', 1)
        
        # Load spell file once for efficiency
        class_lower = class_name.lower()
        spell_file = Path(__file__).parent / "data" / "spells" / class_lower / "0.json"
        all_cantrips = {}
        
        if spell_file.exists():
            try:
                with open(spell_file, 'r') as f:
                    spell_data = json.load(f)
                    all_cantrips = spell_data.get('spells', {})
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
                                if cantrip_name and cantrip_name in all_cantrips:
                                    # Initialize cantrip list if needed
                                    if 0 not in spells_by_level:
                                        spells_by_level[0] = []
                                    
                                    # Check if cantrip is not already in the list
                                    existing_names = [s['name'] for s in spells_by_level[0]]
                                    if cantrip_name not in existing_names:
                                        cantrip_info = all_cantrips[cantrip_name]
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
    
    # Get prepared spells if class is a spellcaster
    if class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
        if 'spell_slots_by_level' in class_data:
            character_level = character.get('level', 1)
            level_str = str(character_level)
            spell_slots = class_data['spell_slots_by_level'].get(level_str, [0]*9)
            
            # For each spell level with available slots, note that spells can be prepared
            for spell_level in range(1, 10):
                if spell_level - 1 < len(spell_slots) and spell_slots[spell_level - 1] > 0:
                    if spell_level not in spells_by_level:
                        spells_by_level[spell_level] = []
                    # Add a note about prepared spells
                    spells_by_level[spell_level].append({
                        'name': f'Prepared Spells (Level {spell_level})',
                        'description': f'You can prepare spells of this level from the {class_name} spell list. Available slots: {spell_slots[spell_level - 1]}',
                        'source': f"{class_name} Class",
                        'is_note': True
                    })
    
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
    
    # Gather weapon and armor proficiencies
    class_name = character.get('class')
    weapon_proficiencies = []
    armor_proficiencies = []
    
    if class_name and class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
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
    if background_name and background_name in character_creator.backgrounds:
        bg_data = character_creator.backgrounds[background_name]
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
    if class_name and class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
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
    if class_name and class_name in character_creator.classes:
        class_data = character_creator.classes[class_name]
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