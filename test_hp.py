#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.hp_calculator import HPCalculator

def test_hp_calculation():
    """Test HP calculation with different characters."""
    
    hp_calc = HPCalculator()
    
    print("=== HP Calculator Test ===")
    
    # Test 1: Level 1 Fighter with 15 Constitution
    print("\n1. Level 1 Fighter, Constitution 15:")
    breakdown = hp_calc.get_hp_breakdown("Fighter", 15, [], 1)
    hp_calc.print_hp_breakdown(breakdown)
    
    # Test 2: Level 3 Barbarian with 16 Constitution
    print("\n2. Level 3 Barbarian, Constitution 16:")
    breakdown = hp_calc.get_hp_breakdown("Barbarian", 16, [], 3)
    hp_calc.print_hp_breakdown(breakdown)
    
    # Test 3: Level 1 Wizard with 14 Constitution
    print("\n3. Level 1 Wizard, Constitution 14:")
    breakdown = hp_calc.get_hp_breakdown("Wizard", 14, [], 1)
    hp_calc.print_hp_breakdown(breakdown)
    
    # Test 4: Level 5 character with Dwarven Toughness (+1 HP per level)
    print("\n4. Level 5 Fighter with Dwarven Toughness, Constitution 15:")
    dwarven_toughness = [{
        "source": "Dwarven Toughness",
        "value": 1,
        "scaling": "per_level"
    }]
    breakdown = hp_calc.get_hp_breakdown("Fighter", 15, dwarven_toughness, 5)
    hp_calc.print_hp_breakdown(breakdown)
    
    print("\n=== All Tests Complete ===")

if __name__ == "__main__":
    test_hp_calculation()