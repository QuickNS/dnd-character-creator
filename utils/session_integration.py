"""
Flask/CharacterBuilder Integration Module

Helper functions to integrate CharacterBuilder with Flask sessions.
Provides backward compatibility while migrating to CharacterBuilder architecture.
"""

from typing import Dict, Any, Optional
from flask import session
from modules.character_builder import CharacterBuilder


def session_to_builder() -> Optional[CharacterBuilder]:
    """
    Convert Flask session data to CharacterBuilder instance.
    
    Returns:
        CharacterBuilder instance or None if no character in session
    """
    if 'character' not in session:
        return None
    
    character_data = session['character']
    
    # Always create a fresh builder - don't try to use from_json on session data
    # because session structure is different from CharacterBuilder's internal structure
    builder = CharacterBuilder()
    
    # Set name
    if 'name' in character_data:
        builder.character_data['name'] = character_data['name']
    
    # Set level
    if 'level' in character_data:
        builder.character_data['level'] = character_data['level']
    
    # Set species if present
    if character_data.get('species'):
        builder.set_species(character_data['species'])
        
        # Set lineage if present
        if character_data.get('lineage'):
            spellcasting_ability = character_data.get('spellcasting_ability')
            builder.set_lineage(character_data['lineage'], spellcasting_ability)
    
    # Set class if present
    if character_data.get('class'):
        level = character_data.get('level', 1)
        builder.set_class(character_data['class'], level)
        
        # Set subclass if present
        if character_data.get('subclass'):
            builder.set_subclass(character_data['subclass'])
    
    # Set background if present
    if character_data.get('background'):
        builder.set_background(character_data['background'])
    
    # Set abilities if present
    if character_data.get('ability_scores'):
        abilities = character_data['ability_scores']
        if isinstance(abilities, dict):
            # Handle both base scores and final scores
            base_scores = abilities.get('base', abilities)
            species_bonuses = abilities.get('species_bonuses', {})
            background_bonuses = abilities.get('background_bonuses', {})
            
            builder.set_abilities(base_scores, species_bonuses, background_bonuses)
    
    # Copy over any step info
    if 'step' in character_data:
        builder.character_data['step'] = character_data['step']
    
    return builder


def builder_to_session(builder: CharacterBuilder, update_session: bool = True) -> Dict[str, Any]:
    """
    Convert CharacterBuilder to session-compatible format.
    
    Args:
        builder: CharacterBuilder instance
        update_session: If True, update Flask session automatically
    
    Returns:
        Session-compatible character dictionary
    """
    character_data = builder.to_json()
    
    # Add legacy fields for backward compatibility
    if 'ability_scores' not in character_data and 'abilities' in character_data:
        # Check if abilities is a complex structure (from AbilityScores)
        abilities = character_data['abilities']
        if isinstance(abilities, dict):
            if 'base' in abilities or 'final' in abilities:
                # Use final scores if available, otherwise base
                character_data['ability_scores'] = abilities.get('final', abilities.get('base', {}))
            else:
                # Already flat, just copy
                character_data['ability_scores'] = abilities
    
    # Ensure ability_scores exists and is flat (not nested)
    if 'ability_scores' in character_data:
        scores = character_data['ability_scores']
        if isinstance(scores, dict) and any(isinstance(v, dict) for v in scores.values()):
            # Has nested structure, flatten it
            flat_scores = {}
            for ability, value in scores.items():
                if isinstance(value, dict):
                    # Take the numeric value from nested dict
                    flat_scores[ability] = value.get('final', value.get('base', 10))
                else:
                    flat_scores[ability] = value
            character_data['ability_scores'] = flat_scores
    
    # Flatten proficiencies for backward compatibility with old Flask routes
    if 'proficiencies' in character_data and isinstance(character_data['proficiencies'], dict):
        builder_skills = character_data['proficiencies'].get('skills', [])
        builder_languages = character_data['proficiencies'].get('languages', [])
        
        # Merge with existing session data instead of replacing
        # This preserves skills added by old Flask code (like class skill choices)
        if 'character' in session:
            existing_skills = session['character'].get('skill_proficiencies', [])
            existing_languages = session['character'].get('languages', [])
            
            # Merge lists, keeping unique values
            all_skills = list(set(existing_skills + builder_skills))
            all_languages = list(set(existing_languages + builder_languages))
            
            character_data['skill_proficiencies'] = all_skills
            character_data['languages'] = all_languages
        else:
            # No existing session data, just use builder data
            character_data['skill_proficiencies'] = builder_skills
            character_data['languages'] = builder_languages
        
        # Keep the nested structure too in case some code uses it
    
    # Ensure features structure exists and is in the correct format
    if 'features' not in character_data or not isinstance(character_data['features'], dict):
        character_data['features'] = {
            "class": [],
            "species": [],
            "lineage": [],
            "background": [],
            "feats": []
        }
    else:
        # Ensure all required categories exist
        for category in ["class", "species", "lineage", "background", "feats"]:
            if category not in character_data['features']:
                character_data['features'][category] = []
    
    # Preserve existing features from session (from old Flask routes)
    if 'character' in session and 'features' in session['character']:
        existing_features = session['character']['features']
        if isinstance(existing_features, dict):
            for category, feature_list in existing_features.items():
                if category in character_data['features']:
                    # Merge features, avoiding duplicates by name
                    existing_names = {f.get('name') for f in character_data['features'][category] if isinstance(f, dict)}
                    for feature in feature_list:
                        if isinstance(feature, dict) and feature.get('name') not in existing_names:
                            character_data['features'][category].append(feature)
    
    # Ensure physical_attributes structure exists
    if 'physical_attributes' not in character_data:
        character_data['physical_attributes'] = {
            "creature_type": "Humanoid",
            "size": "Medium",
            "speed": character_data.get('speed', 30),
            "darkvision": character_data.get('darkvision', 0)
        }
    
    # Ensure equipment list exists
    if 'equipment' not in character_data:
        character_data['equipment'] = []
    
    # Ensure choices_made dict exists
    if 'choices_made' not in character_data:
        character_data['choices_made'] = {}
    
    # Preserve choices_made from session (like skill_choices from class selection)
    if 'character' in session and 'choices_made' in session['character']:
        existing_choices = session['character']['choices_made']
        # Merge with builder choices, preserving existing values
        for key, value in existing_choices.items():
            if key not in character_data['choices_made']:
                character_data['choices_made'][key] = value
    
    # Preserve ability_bonuses from session (like Thaumaturge bonus)
    if 'character' in session and 'ability_bonuses' in session['character']:
        character_data['ability_bonuses'] = session['character']['ability_bonuses']
    
    if update_session:
        session['character'] = character_data
        session.modified = True
    
    return character_data


def init_character_builder() -> CharacterBuilder:
    """
    Initialize a new CharacterBuilder and set up session.
    
    Returns:
        Fresh CharacterBuilder instance
    """
    builder = CharacterBuilder()
    builder.character_data['step'] = 'background'  # Start with background per app flow
    builder_to_session(builder)
    return builder


def update_character_field(field: str, value: Any):
    """
    Update a single character field in both builder and session.
    
    Args:
        field: Field name to update
        value: New value for field
    """
    builder = session_to_builder()
    if builder:
        builder.character_data[field] = value
        builder_to_session(builder)
    elif 'character' in session:
        # Fallback to direct session update
        session['character'][field] = value
        session.modified = True


def get_character_field(field: str, default: Any = None) -> Any:
    """
    Get a character field value from session.
    
    Args:
        field: Field name to get
        default: Default value if field not found
    
    Returns:
        Field value or default
    """
    if 'character' not in session:
        return default
    return session['character'].get(field, default)


def apply_species_with_builder(species_name: str) -> bool:
    """
    Apply species selection using CharacterBuilder.
    
    Args:
        species_name: Name of species to apply
    
    Returns:
        True if successful, False otherwise
    """
    builder = session_to_builder()
    if not builder:
        return False
    
    success = builder.set_species(species_name)
    if success:
        builder_to_session(builder)
    return success


def apply_lineage_with_builder(lineage_name: str, spellcasting_ability: Optional[str] = None) -> bool:
    """
    Apply lineage selection using CharacterBuilder.
    
    Args:
        lineage_name: Name of lineage to apply
        spellcasting_ability: Optional spellcasting ability choice
    
    Returns:
        True if successful, False otherwise
    """
    builder = session_to_builder()
    if not builder:
        return False
    
    success = builder.set_lineage(lineage_name, spellcasting_ability)
    if success:
        builder_to_session(builder)
    return success


def apply_class_with_builder(class_name: str, level: int = 1) -> bool:
    """
    Apply class selection using CharacterBuilder.
    
    Args:
        class_name: Name of class to apply
        level: Character level
    
    Returns:
        True if successful, False otherwise
    """
    builder = session_to_builder()
    if not builder:
        return False
    
    success = builder.set_class(class_name, level)
    if success:
        builder_to_session(builder)
    return success


def apply_subclass_with_builder(subclass_name: str) -> bool:
    """
    Apply subclass selection using CharacterBuilder.
    
    Args:
        subclass_name: Name of subclass to apply
    
    Returns:
        True if successful, False otherwise
    """
    builder = session_to_builder()
    if not builder:
        return False
    
    success = builder.set_subclass(subclass_name)
    if success:
        builder_to_session(builder)
    return success


def apply_background_with_builder(background_name: str) -> bool:
    """
    Apply background selection using CharacterBuilder.
    
    Args:
        background_name: Name of background to apply
    
    Returns:
        True if successful, False otherwise
    """
    builder = session_to_builder()
    if not builder:
        return False
    
    success = builder.set_background(background_name)
    if success:
        builder_to_session(builder)
    return success


def apply_abilities_with_builder(abilities: Dict[str, int], 
                                 species_bonuses: Optional[Dict[str, int]] = None,
                                 background_bonuses: Optional[Dict[str, int]] = None) -> bool:
    """
    Apply ability scores using CharacterBuilder.
    
    Args:
        abilities: Base ability scores
        species_bonuses: Optional species bonuses
        background_bonuses: Optional background bonuses
    
    Returns:
        True if successful, False otherwise
    """
    builder = session_to_builder()
    if not builder:
        return False
    
    success = builder.set_abilities(abilities, species_bonuses, background_bonuses)
    if success:
        builder_to_session(builder)
    return success


def validate_character() -> Dict[str, Any]:
    """
    Validate current character in session.
    
    Returns:
        Validation results with errors and warnings
    """
    builder = session_to_builder()
    if not builder:
        return {'errors': ['No character in session'], 'warnings': []}
    
    return builder.validate()
