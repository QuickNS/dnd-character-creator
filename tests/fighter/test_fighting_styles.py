"""Tests for Fighter fighting styles and their effects."""

import pytest
from modules.character_builder import CharacterBuilder


def test_archery_fighting_style_bonus():
    """Test that Archery fighting style grants +2 to ranged weapon attacks."""
    # Create level 3 Fighter with Archery fighting style
    builder = CharacterBuilder()
    
    choices = {
        "species": "Human",
        "class": "Fighter",
        "level": 3,
        "background": "Soldier",
        "ability_scores": {
            "Strength": 14,
            "Dexterity": 16,  # +3 modifier
            "Constitution": 14,
            "Intelligence": 10,
            "Wisdom": 12,
            "Charisma": 8,
        },
        "Fighting Style": "Archery",
        "subclass": "Champion",
    }
    
    builder.apply_choices(choices)
    
    # Add a longbow to test ranged weapon
    builder.character_data["equipment"] = {
        "weapons": [
            {
                "name": "Longbow",
                "properties": {
                    "category": "Martial Ranged",
                    "properties": ["Ammunition (range 150/600)", "Heavy", "Two-Handed"],
                    "damage": "1d8",
                    "damage_type": "Piercing",
                    "proficiency_required": "Martial weapons",  # Must match proficiency name
                },
            },
            {
                "name": "Longsword",
                "properties": {
                    "category": "Martial Melee",
                    "properties": ["Versatile (1d10)"],
                    "damage": "1d8",
                    "damage_type": "Slashing",
                    "proficiency_required": "Martial weapons",  # Must match proficiency name
                },
            },
        ]
    }
    
    # Get full character data (which calculates attacks with all bonuses)
    char_data = builder.to_character()
    attacks = char_data["attacks"]
    
    # Find longbow and longsword
    longbow = next(a for a in attacks if a["name"] == "Longbow")
    longsword = next(a for a in attacks if a["name"] == "Longsword")
    
    # Longbow should have +7 to hit (DEX 3 + Prof 2 + Archery 2)
    assert longbow["attack_bonus"] == 7, f"Expected +7, got +{longbow['attack_bonus']}"
    
    # Longsword should have +4 to hit (STR 2 + Prof 2, NO Archery bonus)
    assert longsword["attack_bonus"] == 4, f"Expected +4, got +{longsword['attack_bonus']}"


def test_archery_persists_across_serialization():
    """Test that Archery bonus persists when builder is saved/loaded from JSON."""
    # Create Fighter with Archery
    builder = CharacterBuilder()
    
    choices = {
        "species": "Elf",
        "lineage": "Wood Elf",
        "class": "Fighter",
        "level": 3,
        "background": "Soldier",
        "ability_scores": {
            "Strength": 14,
            "Dexterity": 16,
            "Constitution": 14,
            "Intelligence": 10,
            "Wisdom": 12,
            "Charisma": 8,
        },
        "Fighting Style": "Archery",
        "subclass": "Champion",
    }
    
    builder.apply_choices(choices)
    
    # Add weapons
    builder.character_data["equipment"] = {
        "weapons": [
            {
                "name": "Longbow",
                "properties": {
                    "category": "Martial Ranged",
                    "properties": ["Ammunition (range 150/600)", "Heavy", "Two-Handed"],
                    "damage": "1d8",
                    "damage_type": "Piercing",
                    "proficiency_required": "Martial weapons",  # Must match proficiency name
                },
            }
        ]
    }
    
    # Serialize to JSON
    char_json = builder.to_json()
    
    # Create new builder and load from JSON
    builder2 = CharacterBuilder()
    builder2.from_json(char_json)
    
    # Get character data with calculated attacks
    char_data = builder2.to_character()
    attacks = char_data["attacks"]
    longbow = next(a for a in attacks if a["name"] == "Longbow")
    
    # Should still have +7 (DEX 3 + Prof 2 + Archery 2)
    assert longbow["attack_bonus"] == 7, (
        f"Archery bonus not preserved across serialization: "
        f"expected +7, got +{longbow['attack_bonus']}"
    )


def test_defense_fighting_style():
    """Test that Defense fighting style is tracked in effects (implementation TBD)."""
    builder = CharacterBuilder()
    
    choices = {
        "species": "Human",
        "class": "Fighter",
        "level": 1,
        "background": "Soldier",
        "ability_scores": {
            "Strength": 16,
            "Dexterity": 14,
            "Constitution": 14,
            "Intelligence": 10,
            "Wisdom": 12,
            "Charisma": 8,
        },
        "Fighting Style": "Defense",
    }
    
    builder.apply_choices(choices)
    
    # Check that Defense effect is tracked
    defense_effects = [
        e for e in builder.applied_effects 
        if e.get("source") == "Defense"
    ]
    
    assert len(defense_effects) > 0, "Defense fighting style should create an effect"
    assert defense_effects[0]["type"] == "bonus_ac", (
        "Defense effect should be type 'bonus_ac'"
    )
