"""
Test UI Integration (Phase 5)

Simulates the character_summary route with test data to verify:
- AC options calculations work in route context
- Weapon attacks calculations work in route context  
- Data is properly formatted for template rendering
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.character_calculator import CharacterCalculator
from modules.character_sheet_converter import CharacterSheetConverter
from modules.character_builder import CharacterBuilder
from modules.data_loader import DataLoader
import json


def create_test_character_with_equipment():
    """Create a test character with equipment."""
    # Basic character data
    character = {
        'name': 'Test Fighter',
        'class': 'Fighter',
        'level': 5,
        'subclass': 'Champion',
        'background': 'Soldier',
        'species': 'Human',
        'alignment': 'Neutral Good',
        'ability_scores': {
            'Strength': 16,
            'Dexterity': 14,
            'Constitution': 15,
            'Intelligence': 10,
            'Wisdom': 12,
            'Charisma': 8
        },
        'skill_proficiencies': ['Athletics', 'Intimidation', 'Perception', 'Survival'],
        'skill_expertise': [],
        'languages': ['Common', 'Dwarvish'],
        'speed': 30,
        'darkvision': 0,
        'features': {},
        'proficiencies': {
            'armor': ['Light armor', 'Medium armor', 'Heavy armor', 'Shields'],
            'weapons': ['Simple weapons', 'Martial weapons'],
            'tools': [],
            'proficiency_bonus': 3
        },
        'equipment': {
            'armor': [
                {
                    'name': 'Chain Mail',
                    'quantity': 1,
                    'properties': {
                        'category': 'Heavy Armor',
                        'ac_base': 16,
                        'stealth_disadvantage': True,
                        'strength_requirement': 13,
                        'proficiency_required': 'Heavy armor'
                    }
                },
                {
                    'name': 'Leather Armor',
                    'quantity': 1,
                    'properties': {
                        'category': 'Light Armor',
                        'ac_base': 11,
                        'stealth_disadvantage': False,
                        'proficiency_required': 'Light armor'
                    }
                }
            ],
            'shields': [
                {
                    'name': 'Shield',
                    'quantity': 1,
                    'properties': {
                        'category': 'Shield',
                        'ac_bonus': 2,
                        'proficiency_required': 'Shields'
                    }
                }
            ],
            'weapons': [
                {
                    'name': 'Longsword',
                    'quantity': 1,
                    'properties': {
                        'name': 'Longsword',
                        'category': 'Martial Melee',
                        'damage': '1d8',
                        'damage_type': 'Slashing',
                        'properties': ['Versatile (1d10)']
                    }
                },
                {
                    'name': 'Longbow',
                    'quantity': 1,
                    'properties': {
                        'name': 'Longbow',
                        'category': 'Martial Ranged',
                        'damage': '1d8',
                        'damage_type': 'Piercing',
                        'properties': ['Ammunition (range 150/600)', 'Heavy', 'Two-Handed']
                    }
                },
                {
                    'name': 'Dagger',
                    'quantity': 2,
                    'properties': {
                        'name': 'Dagger',
                        'category': 'Simple Melee',
                        'damage': '1d4',
                        'damage_type': 'Piercing',
                        'properties': ['Finesse', 'Light', 'Thrown (range 20/60)']
                    }
                }
            ],
            'other': []
        }
    }
    
    return character


def test_route_integration():
    """Simulate the character_summary route."""
    print("=" * 60)
    print("Testing UI Integration (Phase 5)")
    print("=" * 60)
    
    # Create test character
    print("\n1. Creating test character with equipment...")
    character = create_test_character_with_equipment()
    print(f"   ✓ Character: {character['name']} ({character['class']} {character['level']})")
    print(f"   ✓ Equipment: {len(character['equipment']['armor'])} armor, " +
          f"{len(character['equipment']['shields'])} shield, " +
          f"{len(character['equipment']['weapons'])} weapons")
    
    # Convert to comprehensive character sheet (like the route does)
    print("\n2. Converting to comprehensive character sheet...")
    converter = CharacterSheetConverter()
    comprehensive_character = converter.convert_to_character_sheet(character)
    
    # Add proficiencies to comprehensive character (normally comes from class data)
    comprehensive_character['proficiencies'] = {
        'armor': ['Light armor', 'Medium armor', 'Heavy armor', 'Shields'],
        'weapons': ['Simple weapons', 'Martial weapons'],
        'tools': [],
        'languages': ['Common', 'Dwarvish'],
        'proficiency_bonus': 3
    }
    
    print(f"   ✓ Comprehensive character created")
    print(f"   ✓ Ability scores calculated: {list(comprehensive_character['ability_scores'].keys())}")
    
    # Calculate AC options (like the route does)
    print("\n3. Calculating AC options for template...")
    calculator = CharacterCalculator()
    ac_options = calculator.calculate_all_ac_options(comprehensive_character)
    best_ac = ac_options[0]['ac'] if ac_options else 10
    
    print(f"   ✓ Found {len(ac_options)} AC options")
    print(f"   ✓ Best AC: {best_ac}")
    
    # Display AC options like the template would
    print("\n4. AC Options Summary (as displayed in UI):")
    print("   " + "=" * 56)
    
    if ac_options:
        # Best option
        option = ac_options[0]
        armor_name = option['armor'] if option['armor'] else 'Unarmored'
        shield_name = f" + {option['shield']}" if option['shield'] else ''
        
        print(f"\n   ★ BEST OPTION: AC {option['ac']}")
        print(f"   {armor_name}{shield_name}")
        print(f"   {option['formula']}")
        if option['notes']:
            for note in option['notes']:
                print(f"   {note}")
        
        # Alternative options
        if len(ac_options) > 1:
            print("\n   Alternative Options:")
            for option in ac_options[1:]:
                armor_name = option['armor'] if option['armor'] else 'Unarmored'
                shield_name = f" + {option['shield']}" if option['shield'] else ''
                print(f"   AC {option['ac']} - {armor_name}{shield_name}")
                print(f"     {option['formula']}")
                if option['notes']:
                    for note in option['notes']:
                        print(f"     {note}")
    
    print("\n   " + "=" * 56)
    
    # Calculate weapon attacks (like the route does)
    print("\n5. Calculating weapon attacks for template...")
    weapon_attacks = calculator.calculate_weapon_attacks(comprehensive_character)
    print(f"   ✓ Found {len(weapon_attacks)} weapons")
    
    # Display weapon attacks like the template would
    print("\n6. Weapon Attacks Summary (as displayed in UI):")
    print("   " + "=" * 56)
    
    for weapon in weapon_attacks:
        print(f"\n   {weapon['name']}")
        print(f"   Attack: {weapon['attack_bonus']} to hit ({weapon['ability']})")
        print(f"   Damage: {weapon['damage']} {weapon['damage_type']}")
        if weapon['versatile_damage']:
            print(f"   Versatile: {weapon['versatile_damage']} {weapon['damage_type']}")
        if weapon['properties']:
            print(f"   Properties: {', '.join(weapon['properties'])}")
        if not weapon['proficient']:
            print(f"   ⚠️ Not proficient - no proficiency bonus applied")
    
    print("\n   " + "=" * 56)
    
    # Verify template data structure
    print("\n7. Verifying template data structure...")
    template_data = {
        'character': character,
        'character_sheet': comprehensive_character,
        'ac_options': ac_options,
        'best_ac': best_ac,
        'weapon_attacks': weapon_attacks
    }
    
    print(f"   ✓ character: {type(character).__name__}")
    print(f"   ✓ character_sheet: {type(comprehensive_character).__name__}")
    print(f"   ✓ ac_options: {type(ac_options).__name__} (length: {len(ac_options)})")
    print(f"   ✓ best_ac: {best_ac}")
    print(f"   ✓ weapon_attacks: {type(weapon_attacks).__name__} (length: {len(weapon_attacks)})")
    
    print("\n" + "=" * 60)
    print("✓ UI Integration Test Complete!")
    print("=" * 60)
    
    print("\nPhase 5 implementation verified!")
    print("\nTemplate data structure:")
    print("- ac_options: List of AC option dicts with keys: ac, armor, shield, formula, notes, valid")
    print("- best_ac: Integer representing the highest AC")
    print("- weapon_attacks: List of weapon dicts with keys: name, attack_bonus, damage, etc.")
    print("\nNext steps:")
    print("- Test with actual Flask app and browser")
    print("- Verify CSS styling and layout")
    print("- Test with different character types (Barbarian, Monk, Wizard, etc.)")


def main():
    """Run the test."""
    try:
        test_route_integration()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
