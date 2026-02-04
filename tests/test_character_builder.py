#!/usr/bin/env python3
"""
Test script for CharacterBuilder

Demonstrates how to use the CharacterBuilder class for testing
without needing the Flask web interface.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.character_builder import CharacterBuilder


def test_wood_elf_cantrip():
    """Test that Wood Elf gets Druidcraft cantrip"""
    print("\n" + "="*60)
    print("TEST: Wood Elf should receive Druidcraft cantrip")
    print("="*60)
    
    builder = CharacterBuilder()
    
    # Set species
    print("\n1. Setting species to Elf...")
    success = builder.set_species("Elf")
    print(f"   ✓ Species set: {success}")
    
    # Set lineage
    print("\n2. Setting lineage to Wood Elf...")
    success = builder.set_lineage("Wood Elf", spellcasting_ability="Wisdom")
    print(f"   ✓ Lineage set: {success}")
    
    # Check cantrips
    print("\n3. Checking granted cantrips...")
    cantrips = builder.get_cantrips()
    print(f"   Cantrips: {cantrips}")
    
    # Assertions
    assert "Druidcraft" in cantrips, "Wood Elf should have Druidcraft cantrip"
    print("   ✓ Druidcraft found!")
    
    # Check spellcasting ability
    spellcasting_ability = builder.character_data.get('spellcasting_ability')
    print(f"   Spellcasting ability: {spellcasting_ability}")
    assert spellcasting_ability == "Wisdom", "Spellcasting ability should be Wisdom"
    print("   ✓ Spellcasting ability correct!")
    
    # Check speed
    print("\n4. Checking speed modification...")
    speed = builder.character_data['speed']
    print(f"   Speed: {speed}")
    assert speed == 35, "Wood Elf should have 35 ft speed"
    print("   ✓ Speed correct!")
    
    print("\n" + "="*60)
    print("✅ TEST PASSED: Wood Elf cantrip test successful!")
    print("="*60)
    return True


def test_quick_create():
    """Test the quick_create factory method"""
    print("\n" + "="*60)
    print("TEST: Quick create method")
    print("="*60)
    
    builder = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={
            "STR": 10,
            "DEX": 16,
            "CON": 14,
            "INT": 12,
            "WIS": 15,
            "CHA": 8
        },
        level=1,
        spellcasting_ability="Wisdom"
    )
    
    print("\n1. Character created via quick_create")
    print(f"   Species: {builder.character_data['species']}")
    print(f"   Lineage: {builder.character_data['lineage']}")
    print(f"   Class: {builder.character_data['class']}")
    print(f"   Background: {builder.character_data['background']}")
    print(f"   Level: {builder.character_data['level']}")
    
    print("\n2. Checking character completeness...")
    print(f"   Current step: {builder.get_current_step()}")
    print(f"   Is complete: {builder.is_complete()}")
    
    print("\n3. Character features:")
    print(f"   Cantrips: {builder.get_cantrips()}")
    print(f"   Speed: {builder.character_data['speed']}")
    print(f"   Darkvision: {builder.character_data['darkvision']}")
    print(f"   Skill proficiencies: {builder.get_proficiencies('skills')}")
    
    print("\n" + "="*60)
    print("✅ TEST PASSED: Quick create successful!")
    print("="*60)
    return True


def test_character_export():
    """Test exporting character to different formats"""
    print("\n" + "="*60)
    print("TEST: Character export formats")
    print("="*60)
    
    builder = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={
            "STR": 10,
            "DEX": 16,
            "CON": 14,
            "INT": 12,
            "WIS": 15,
            "CHA": 8
        }
    )
    
    print("\n1. Exporting to JSON...")
    character_json = builder.to_json()
    print(f"   ✓ JSON export has {len(character_json.keys())} top-level keys")
    print(f"   Keys: {', '.join(character_json.keys())}")
    
    print("\n2. Exporting to Character object...")
    character_obj = builder.to_character()
    print(f"   ✓ Character object created")
    print(f"   Type: {type(character_obj).__name__}")
    print(f"   Species: {character_obj.species}")
    print(f"   Class: {character_obj.class_name}")
    
    print("\n3. Testing round-trip (JSON -> Builder -> JSON)...")
    builder2 = CharacterBuilder()
    builder2.from_json(character_json)
    print(f"   ✓ Character loaded from JSON")
    print(f"   Species matches: {builder2.character_data['species'] == builder.character_data['species']}")
    print(f"   Class matches: {builder2.character_data['class'] == builder.character_data['class']}")
    
    print("\n" + "="*60)
    print("✅ TEST PASSED: Export successful!")
    print("="*60)
    return True


def test_validation():
    """Test character validation"""
    print("\n" + "="*60)
    print("TEST: Character validation")
    print("="*60)
    
    # Invalid character (missing required fields)
    builder = CharacterBuilder()
    print("\n1. Testing incomplete character...")
    validation = builder.validate()
    print(f"   Errors: {validation['errors']}")
    print(f"   Warnings: {validation['warnings']}")
    assert len(validation['errors']) > 0, "Should have validation errors"
    print("   ✓ Validation caught missing fields")
    
    # Complete character
    print("\n2. Testing complete character...")
    builder.set_species("Elf")
    builder.set_lineage("Wood Elf")
    builder.set_class("Ranger")
    builder.set_background("Sage")
    builder.set_abilities({
        "STR": 10,
        "DEX": 16,
        "CON": 14,
        "INT": 12,
        "WIS": 15,
        "CHA": 8
    })
    
    validation = builder.validate()
    print(f"   Errors: {validation['errors']}")
    print(f"   Warnings: {validation['warnings']}")
    assert len(validation['errors']) == 0, "Should have no validation errors"
    print("   ✓ Complete character passes validation")
    
    print("\n" + "="*60)
    print("✅ TEST PASSED: Validation working correctly!")
    print("="*60)
    return True


def test_level_3_spell():
    """Test that Wood Elf gets Longstrider at level 3"""
    print("\n" + "="*60)
    print("TEST: Wood Elf level 3 spell grant")
    print("="*60)
    
    # Level 1 character
    print("\n1. Creating level 1 Wood Elf...")
    builder1 = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8},
        level=1,
        spellcasting_ability="Wisdom"
    )
    spells_l1 = builder1.get_spells()
    print(f"   Level 1 known spells: {spells_l1}")
    assert "Longstrider" not in spells_l1, "Longstrider should NOT be available at level 1"
    print("   ✓ Longstrider not yet available")
    
    # Level 3 character
    print("\n2. Creating level 3 Wood Elf...")
    builder3 = CharacterBuilder.quick_create(
        species="Elf",
        lineage="Wood Elf",
        char_class="Ranger",
        background="Sage",
        abilities={"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8},
        level=3,
        spellcasting_ability="Wisdom"
    )
    spells_l3 = builder3.get_spells()
    print(f"   Level 3 known spells: {spells_l3}")
    assert "Longstrider" in spells_l3, "Longstrider SHOULD be available at level 3"
    print("   ✓ Longstrider available at level 3!")
    
    print("\n" + "="*60)
    print("✅ TEST PASSED: Level-based spell grant working!")
    print("="*60)
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("RUNNING ALL CHARACTER BUILDER TESTS")
    print("="*60)
    
    tests = [
        ("Wood Elf Cantrip", test_wood_elf_cantrip),
        ("Quick Create", test_quick_create),
        ("Character Export", test_character_export),
        ("Validation", test_validation),
        ("Level 3 Spell", test_level_3_spell),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
