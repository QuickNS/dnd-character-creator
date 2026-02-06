#!/usr/bin/env python3
"""Test script to verify feature scaling works correctly."""

import json
from pathlib import Path
from utils.feature_scaling import resolve_scaling_feature


def test_cleric_scaling():
    """Test Channel Divinity scaling at different levels."""
    # Load cleric data
    cleric_path = Path(__file__).parent.parent.parent / 'data' / 'classes' / 'cleric.json'
    with open(cleric_path, 'r') as f:
        cleric_data = json.load(f)
    
    # Get Channel Divinity feature
    channel_divinity = cleric_data['features_by_level']['2']['Channel Divinity']
    
    print("Testing Channel Divinity Scaling")
    print("=" * 60)
    print("\nOriginal description:")
    print(channel_divinity['description'][:200] + "...")
    print("\nScaling metadata:")
    print(json.dumps(channel_divinity.get('scaling', {}), indent=2))
    
    # Test Channel Divinity scaling
    test_levels = [2, 7, 13, 18]
    expected_dice = ['1d8', '2d8', '3d8', '4d8']
    expected_uses = ['2', '3', '3', '4']
    
    for i, level in enumerate(test_levels):
        resolved = resolve_scaling_feature(channel_divinity, level)
        
        # Basic test: ensure the feature description was resolved
        assert resolved is not None
        assert len(resolved) > 0
        
        # Test that scaling values are being substituted correctly
        expected_damage = expected_dice[i]
        expected_use_count = expected_uses[i]
        
        assert expected_damage in resolved, f"Expected '{expected_damage}' not found in level {level}: {resolved}"
        assert f"Channel Divinity {expected_use_count} per Short/Long Rest" in resolved, f"Expected '{expected_use_count}' uses not found in level {level}: {resolved}"


if __name__ == '__main__':
    test_cleric_scaling()
