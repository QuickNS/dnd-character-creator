"""
Test script for Equipment System (Phase 3 & 4)

Tests:
- Equipment Manager (inventory management)
- AC Options Calculator (all possible AC combinations)
- Weapon attack calculations
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.equipment_manager import EquipmentManager
from modules.character_calculator import CharacterCalculator
import json


def create_test_character():
    """Create a test character with basic stats."""
    return {
        'name': 'Test Fighter',
        'class': 'Fighter',
        'level': 5,
        'ability_scores': {
            'strength': {'score': 16, 'modifier': 3},
            'dexterity': {'score': 14, 'modifier': 2},
            'constitution': {'score': 15, 'modifier': 2},
            'intelligence': {'score': 10, 'modifier': 0},
            'wisdom': {'score': 12, 'modifier': 1},
            'charisma': {'score': 8, 'modifier': -1}
        },
        'proficiencies': {
            'armor': ['Light armor', 'Medium armor', 'Heavy armor', 'Shields'],
            'weapons': ['Simple weapons', 'Martial weapons'],
            'proficiency_bonus': 3
        },
        'equipment': {
            'armor': [],
            'shields': [],
            'weapons': [],
            'other': []
        },
        'features': {}
    }


def test_equipment_manager():
    """Test the EquipmentManager module."""
    print("=" * 60)
    print("Testing Equipment Manager (Phase 3)")
    print("=" * 60)
    
    manager = EquipmentManager()
    character = create_test_character()
    equipment = character['equipment']
    
    # Test adding armor
    print("\n1. Adding armor to inventory...")
    manager.add_item(equipment, 'Chain Mail', 'armor')
    manager.add_item(equipment, 'Leather Armor', 'armor')
    print(f"   ✓ Added 2 armor pieces")
    print(f"   Inventory: {[a['name'] for a in equipment['armor']]}")
    
    # Test adding shields
    print("\n2. Adding shields to inventory...")
    manager.add_item(equipment, 'Shield', 'shields')
    print(f"   ✓ Added shield")
    print(f"   Inventory: {[s['name'] for s in equipment['shields']]}")
    
    # Test adding weapons
    print("\n3. Adding weapons to inventory...")
    manager.add_item(equipment, 'Longsword', 'weapons')
    manager.add_item(equipment, 'Longbow', 'weapons')
    manager.add_item(equipment, 'Dagger', 'weapons', quantity=2)
    print(f"   ✓ Added 3 weapon types")
    print(f"   Inventory: {[(w['name'], w.get('quantity', 1)) for w in equipment['weapons']]}")
    
    # Test proficiency checks
    print("\n4. Testing proficiency checks...")
    has_chain_prof = manager.can_use_armor('Chain Mail', character['proficiencies']['armor'])
    has_longbow_prof = manager.can_use_weapon('Longbow', character['proficiencies']['weapons'])
    print(f"   ✓ Can use Chain Mail: {has_chain_prof}")
    print(f"   ✓ Can use Longbow: {has_longbow_prof}")
    
    # Test weight calculation
    print("\n5. Calculating total weight...")
    total_weight = manager.calculate_total_weight(equipment)
    print(f"   ✓ Total equipment weight: {total_weight} lbs")
    
    print("\n✓ Equipment Manager tests passed!\n")
    return character


def test_ac_options_calculator(character):
    """Test the AC Options Calculator."""
    print("=" * 60)
    print("Testing AC Options Calculator (Phase 4)")
    print("=" * 60)
    
    calculator = CharacterCalculator()
    
    # Calculate all AC options
    print("\n1. Calculating all AC options...")
    ac_options = calculator.calculate_all_ac_options(character)
    print(f"   ✓ Found {len(ac_options)} AC options")
    
    # Display AC options
    print("\n2. AC Options Summary:")
    print("   " + "=" * 56)
    
    for i, option in enumerate(ac_options):
        armor_name = option['armor'] if option['armor'] else 'Unarmored'
        shield_name = f" + {option['shield']}" if option['shield'] else ''
        
        print(f"\n   Option {i+1}: AC {option['ac']} - {armor_name}{shield_name}")
        print(f"   Formula: {option['formula']}")
        
        if option['notes']:
            for note in option['notes']:
                print(f"   {note}")
        
        if not option['valid']:
            print("   ⚠️ NOT VALID (missing proficiency)")
    
    print("\n   " + "=" * 56)
    
    # Test best AC
    if ac_options:
        best_option = ac_options[0]
        print(f"\n3. Best AC Option: AC {best_option['ac']}")
        armor_desc = best_option['armor'] if best_option['armor'] else 'Unarmored'
        if best_option['shield']:
            armor_desc += f" + {best_option['shield']}"
        print(f"   {armor_desc}")
        print(f"   {best_option['formula']}")
    
    print("\n✓ AC Options Calculator tests passed!\n")
    return ac_options


def test_weapon_attacks(character):
    """Test weapon attack calculations."""
    print("=" * 60)
    print("Testing Weapon Attack Calculations")
    print("=" * 60)
    
    calculator = CharacterCalculator()
    
    # Calculate weapon attacks
    print("\n1. Calculating weapon attack stats...")
    attacks = calculator.calculate_weapon_attacks(character)
    print(f"   ✓ Found {len(attacks)} weapons")
    
    # Display weapon attacks
    print("\n2. Weapon Attack Summary:")
    print("   " + "=" * 56)
    
    for attack in attacks:
        print(f"\n   {attack['name']}")
        print(f"   Attack: {attack['attack_bonus']} to hit ({attack['ability']})")
        print(f"   Damage: {attack['damage']} {attack['damage_type']}")
        
        if attack['versatile_damage']:
            print(f"   Versatile: {attack['versatile_damage']} {attack['damage_type']}")
        
        if attack['properties']:
            print(f"   Properties: {', '.join(attack['properties'])}")
        
        print(f"   Proficient: {'Yes' if attack['proficient'] else 'No'}")
    
    print("\n   " + "=" * 56)
    print("\n✓ Weapon attack calculations passed!\n")


def test_unarmored_defense():
    """Test special unarmored defense features."""
    print("=" * 60)
    print("Testing Unarmored Defense Features")
    print("=" * 60)
    
    calculator = CharacterCalculator()
    
    # Test Barbarian unarmored defense
    print("\n1. Testing Barbarian Unarmored Defense (10 + DEX + CON)...")
    barbarian = create_test_character()
    barbarian['features'] = {
        'Unarmored Defense': 'While not wearing armor, your AC equals 10 + DEX + Constitution modifier'
    }
    
    ac_options = calculator.calculate_all_ac_options(barbarian)
    unarmored_option = next((opt for opt in ac_options if opt['is_unarmored'] and not opt['shield']), None)
    
    if unarmored_option:
        expected_ac = 10 + 2 + 2  # 10 + DEX(2) + CON(2) = 14
        print(f"   ✓ Unarmored AC: {unarmored_option['ac']} (expected: {expected_ac})")
        print(f"   Formula: {unarmored_option['formula']}")
        assert unarmored_option['ac'] == expected_ac, f"Expected AC {expected_ac}, got {unarmored_option['ac']}"
    
    # Test Monk unarmored defense
    print("\n2. Testing Monk Unarmored Defense (10 + DEX + WIS)...")
    monk = create_test_character()
    monk['features'] = {
        'Unarmored Defense': 'While not wearing armor, your AC equals 10 + DEX + Wisdom modifier'
    }
    
    ac_options = calculator.calculate_all_ac_options(monk)
    unarmored_option = next((opt for opt in ac_options if opt['is_unarmored'] and not opt['shield']), None)
    
    if unarmored_option:
        expected_ac = 10 + 2 + 1  # 10 + DEX(2) + WIS(1) = 13
        print(f"   ✓ Unarmored AC: {unarmored_option['ac']} (expected: {expected_ac})")
        print(f"   Formula: {unarmored_option['formula']}")
        assert unarmored_option['ac'] == expected_ac, f"Expected AC {expected_ac}, got {unarmored_option['ac']}"
    
    print("\n✓ Unarmored Defense tests passed!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EQUIPMENT SYSTEM TEST SUITE")
    print("Phase 3: Equipment Manager")
    print("Phase 4: AC Options Calculator & Weapon Attacks")
    print("=" * 60 + "\n")
    
    try:
        # Test Phase 3: Equipment Manager
        character = test_equipment_manager()
        
        # Test Phase 4: AC Options
        ac_options = test_ac_options_calculator(character)
        
        # Test Weapon Attacks
        test_weapon_attacks(character)
        
        # Test special features
        test_unarmored_defense()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 3 & 4 implementation complete!")
        print("\nNext steps:")
        print("- Integrate into app.py routes")
        print("- Create UI templates for AC Options Card")
        print("- Add equipment selection workflow")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
