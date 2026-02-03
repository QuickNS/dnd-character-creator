#!/usr/bin/env python3
"""Test script for manual ability score assignment"""

from interactive_character_creator import CharacterCreator
import json

def test_manual_assignment():
    creator = CharacterCreator()
    
    # Create a test character with minimal setup
    character = {
        "name": "TestChar",
        "level": 1,
        "class": "Wizard",
        "background": "Hermit", 
        "species": "Human",
        "ability_scores": {
            "Strength": 10,
            "Dexterity": 10,
            "Constitution": 10,
            "Intelligence": 10,
            "Wisdom": 10,
            "Charisma": 10
        },
        "choices_made": {}
    }
    
    print("=== Testing Manual Standard Array Assignment ===")
    print("Standard array: 15, 14, 13, 12, 10, 8")
    print("For Wizard class (Intelligence primary)")
    print()
    
    # Mock user input for manual assignment
    print("Simulating manual assignment:")
    print("15 → Intelligence (primary ability)")
    print("14 → Constitution (survivability)")
    print("13 → Dexterity (AC)")
    print("12 → Wisdom (perception)")
    print("10 → Strength")
    print("8 → Charisma")
    
    # Apply manual assignment directly
    ability_mapping = {
        "Intelligence": 15,
        "Constitution": 14,
        "Dexterity": 13,
        "Wisdom": 12,
        "Strength": 10,
        "Charisma": 8
    }
    
    for ability, score in ability_mapping.items():
        character["ability_scores"][ability] = score
    
    print("\nResult:")
    for ability, score in character["ability_scores"].items():
        modifier = (score - 10) // 2
        sign = "+" if modifier >= 0 else ""
        print(f"  {ability}: {score} ({sign}{modifier})")

if __name__ == "__main__":
    test_manual_assignment()