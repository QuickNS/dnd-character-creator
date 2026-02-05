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