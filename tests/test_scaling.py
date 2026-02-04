#!/usr/bin/env python3
"""Test script to verify feature scaling works correctly."""

import json
from pathlib import Path
from utils.feature_scaling import resolve_scaling_feature

def test_cleric_scaling():
    """Test Channel Divinity scaling at different levels."""
    # Load cleric data
    cleric_path = Path(__file__).parent / 'data' / 'classes' / 'cleric.json'
    with open(cleric_path, 'r') as f:
        cleric_data = json.load(f)
    
    # Get Channel Divinity feature
    channel_divinity = cleric_data['features_by_level']['2']['Channel Divinity']
    
    print("Testing Channel Divinity Scaling")
    print("=" * 60)
    print(f"\nOriginal description:")
    print(channel_divinity['description'][:200] + "...")
    print(f"\nScaling metadata:")
    print(json.dumps(channel_divinity.get('scaling', {}), indent=2))
    
    # Test at different levels
    test_levels = [2, 7, 13, 18]
    for level in test_levels:
        resolved = resolve_scaling_feature(channel_divinity, level)
        print(f"\n--- Level {level} ---")
        # Show just the relevant parts
        lines = resolved.split('\n')
        for line in lines:
            if 'heal' in line.lower() or 'damage' in line.lower() or 'use' in line.lower():
                print(line)
    
    # Test Blessed Strikes
    print("\n\nTesting Blessed Strikes Scaling")
    print("=" * 60)
    blessed_strikes = cleric_data['features_by_level']['8']['Blessed Strikes']
    
    print(f"\nOriginal description:")
    print(blessed_strikes['description'])
    print(f"\nScaling metadata:")
    print(json.dumps(blessed_strikes.get('scaling', {}), indent=2))
    
    test_levels = [8, 14]
    for level in test_levels:
        resolved = resolve_scaling_feature(blessed_strikes, level)
        print(f"\n--- Level {level} ---")
        print(resolved)

if __name__ == '__main__':
    test_cleric_scaling()
