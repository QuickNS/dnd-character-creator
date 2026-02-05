#!/usr/bin/env python3
"""
Pytest tests for CharacterBuilder functionality
"""

import pytest
from modules.character_builder import CharacterBuilder


@pytest.fixture
def character_builder():
    """Fixture providing a fresh CharacterBuilder for each test"""
    return CharacterBuilder()


def test_wood_elf_cantrip(character_builder):
    """Test that Wood Elf gets Druidcraft cantrip"""
    # Set species and lineage
    assert character_builder.set_species("Elf") is True
    assert character_builder.set_lineage("Wood Elf", spellcasting_ability="Wisdom") is True
    
    # Check character data
    character = character_builder.character_data
    assert character['species'] == 'Elf'
    assert character['lineage'] == 'Wood Elf'
    
    # Check that Druidcraft cantrip was added
    cantrips = character.get('spells', {}).get('cantrips', [])
    assert 'Druidcraft' in cantrips


def test_basic_character_creation(character_builder):
    """Test basic character creation flow"""
    # Test species setting
    assert character_builder.set_species("Human") is True
    assert character_builder.character_data['species'] == 'Human'
    
    # Test class setting
    assert character_builder.set_class("Fighter", 1) is True
    assert character_builder.character_data['class'] == 'Fighter'
    assert character_builder.character_data['level'] == 1


def test_level_progression(character_builder):
    """Test character level progression"""
    # Set up a basic character
    character_builder.set_species("Human")
    character_builder.set_class("Fighter", 1)
    
    # Test leveling up
    character_builder.set_class("Fighter", 2)
    assert character_builder.character_data['level'] == 2
    
    character_builder.set_class("Fighter", 5)
    assert character_builder.character_data['level'] == 5


def test_proficiencies_system(character_builder):
    """Test that proficiencies are properly applied"""
    character_builder.set_species("Human")
    character_builder.set_class("Fighter", 1)
    
    char_data = character_builder.character_data
    
    # Check that Fighter gets expected proficiencies
    armor_profs = char_data['proficiencies']['armor']
    assert 'Heavy armor' in armor_profs
    
    weapon_profs = char_data['proficiencies']['weapons']
    assert 'Martial weapons' in weapon_profs
    
    saving_throws = char_data['proficiencies']['saving_throws']
    assert 'Strength' in saving_throws
    assert 'Constitution' in saving_throws

def test_paladin_recommended_ability_scores(character_builder):
    """Test that Paladin uses predefined standard_array_assignment when 'recommended' is selected"""
    # Set up a basic Paladin
    character_builder.set_class('Paladin', 1)
    
    # Apply recommended ability scores (should use predefined assignment from JSON)
    character_builder.apply_choice('ability_scores_method', 'recommended')
    
    # Get the result
    result = character_builder.to_json()
    actual_scores = result['ability_scores']
    
    # Expected values from data/classes/paladin.json standard_array_assignment
    expected_scores = {
        "Strength": 15,
        "Dexterity": 10,
        "Constitution": 13,
        "Intelligence": 8,
        "Wisdom": 12,
        "Charisma": 14
    }
    
    # Verify all scores match
    for ability, expected_value in expected_scores.items():
        assert actual_scores.get(ability) == expected_value, \
            f"Expected {ability} to be {expected_value}, got {actual_scores.get(ability)}"


@pytest.mark.parametrize("class_name,expected_scores", [
    ("Wizard", {
        "Strength": 8,
        "Dexterity": 12,
        "Constitution": 13,
        "Intelligence": 15,
        "Wisdom": 14,
        "Charisma": 10
    }),
    ("Fighter", {
        "Strength": 15,
        "Dexterity": 14,
        "Constitution": 13,
        "Intelligence": 8,
        "Wisdom": 10,
        "Charisma": 12
    }),
    ("Cleric", {
        "Strength": 14,
        "Dexterity": 8,
        "Constitution": 13,
        "Intelligence": 10,
        "Wisdom": 15,
        "Charisma": 12
    }),
    ("Rogue", {
        "Strength": 12,
        "Dexterity": 15,
        "Constitution": 13,
        "Intelligence": 14,
        "Wisdom": 10,
        "Charisma": 8
    }),
    ("Paladin", {
        "Strength": 15,
        "Dexterity": 10,
        "Constitution": 13,
        "Intelligence": 8,
        "Wisdom": 12,
        "Charisma": 14
    }),
])
def test_class_recommended_ability_scores(class_name, expected_scores):
    """Test that all classes use their predefined standard_array_assignment correctly"""
    builder = CharacterBuilder()
    builder.set_class(class_name, 1)
    builder.apply_choice('ability_scores_method', 'recommended')
    
    result = builder.to_json()
    actual_scores = result['ability_scores']
    
    # Verify all scores match expected values from class JSON
    assert actual_scores == expected_scores, \
        f"{class_name} ability scores don't match. Expected {expected_scores}, got {actual_scores}"


def test_all_classes_have_standard_array():
    """Ensure all classes define standard_array_assignment in their JSON data"""
    import json
    from pathlib import Path
    
    classes_dir = Path(__file__).parent.parent.parent / "data" / "classes"
    
    for class_file in classes_dir.glob("*.json"):
        with open(class_file, 'r') as f:
            class_data = json.load(f)
        
        class_name = class_data.get('name')
        assert 'standard_array_assignment' in class_data, \
            f"{class_name} is missing standard_array_assignment"
        
        assignment = class_data['standard_array_assignment']
        
        # Verify it has all 6 abilities
        expected_abilities = {'Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma'}
        actual_abilities = set(assignment.keys())
        assert actual_abilities == expected_abilities, \
            f"{class_name} standard_array_assignment is missing abilities: {expected_abilities - actual_abilities}"
        
        # Verify values are from standard array [15, 14, 13, 12, 10, 8]
        values = sorted(assignment.values(), reverse=True)
        expected_values = [15, 14, 13, 12, 10, 8]
        assert values == expected_values, \
            f"{class_name} standard_array_assignment has invalid values: {values}"


def test_manual_ability_score_assignment():
    """Test that manual ability score assignment works correctly"""
    builder = CharacterBuilder()
    builder.set_class('Wizard', 1)
    
    # Manually assign ability scores
    manual_scores = {
        "Strength": 10,
        "Dexterity": 14,
        "Constitution": 12,
        "Intelligence": 15,
        "Wisdom": 13,
        "Charisma": 8
    }
    
    builder.apply_choice('ability_scores', manual_scores)
    
    result = builder.to_json()
    actual_scores = result['ability_scores']
    
    # Verify manual assignment was used
    assert actual_scores == manual_scores, \
        f"Manual ability score assignment failed. Expected {manual_scores}, got {actual_scores}"


def test_ability_scores_all_use_standard_array_values():
    """Test that recommended scores always use valid standard array values"""
    standard_array = [15, 14, 13, 12, 10, 8]
    
    # Test multiple classes
    for class_name in ["Wizard", "Fighter", "Cleric", "Rogue", "Paladin", "Barbarian"]:
        builder = CharacterBuilder()
        builder.set_class(class_name, 1)
        builder.apply_choice('ability_scores_method', 'recommended')
        
        result = builder.to_json()
        actual_scores = result['ability_scores']
        actual_values = sorted(actual_scores.values(), reverse=True)
        
        assert actual_values == standard_array, \
            f"{class_name} recommended scores don't use standard array. Got {actual_values}"


def test_ability_scores_persist_through_serialization():
    """Test that ability scores are preserved through to_json/from_json"""
    builder = CharacterBuilder()
    builder.set_class('Paladin', 1)
    builder.apply_choice('ability_scores_method', 'recommended')
    
    # Serialize and deserialize
    json_data = builder.to_json()
    
    new_builder = CharacterBuilder()
    new_builder.from_json(json_data)
    
    # Verify scores are preserved
    expected_scores = {
        "Strength": 15,
        "Dexterity": 10,
        "Constitution": 13,
        "Intelligence": 8,
        "Wisdom": 12,
        "Charisma": 14
    }
    
    restored_data = new_builder.to_json()
    assert restored_data['ability_scores'] == expected_scores, \
        f"Ability scores not preserved through serialization. Expected {expected_scores}, got {restored_data['ability_scores']}"
