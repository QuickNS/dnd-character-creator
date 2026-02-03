#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interactive_character_creator import CharacterCreator
import json

def test_choice_resolution():
    """Test that the Choice Reference System is working for Battle Master."""
    
    # Load the character creator
    creator = CharacterCreator()
    
    # Get Battle Master subclass data
    fighter_subclasses = creator.get_subclasses_for_class('Fighter')
    battle_master = fighter_subclasses.get('Battle Master', {})
    
    print("=== Battle Master Data ===")
    print(f"Available: {'Yes' if battle_master else 'No'}")
    
    if battle_master:
        features_by_level = battle_master.get('features_by_level', {})
        level_3_features = features_by_level.get('3', {})
        
        print(f"\nLevel 3 features: {list(level_3_features.keys())}")
        
        combat_superiority = level_3_features.get('Combat Superiority', {})
        if combat_superiority:
            print(f"\nCombat Superiority type: {type(combat_superiority)}")
            print(f"Has 'choices': {'choices' in combat_superiority}")
            
            if 'choices' in combat_superiority:
                choices_data = combat_superiority['choices']
                print(f"Choices data: {json.dumps(choices_data, indent=2)}")
                
                # Check if maneuvers exist
                maneuvers = battle_master.get('maneuvers', {})
                print(f"\nManeuvers available: {len(maneuvers)}")
                print(f"First few maneuvers: {list(maneuvers.keys())[:5]}")
        
        print(f"\nFull Battle Master keys: {list(battle_master.keys())}")

if __name__ == "__main__":
    test_choice_resolution()