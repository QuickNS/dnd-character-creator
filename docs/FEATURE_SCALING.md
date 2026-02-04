# Feature Scaling System

## Overview
The scaling system allows features to dynamically adjust their values based on character level without creating redundant entries for level upgrades.

## Architecture

### Components
1. **Scaling Metadata** - JSON configuration in class/subclass data files
2. **Scaling Resolution** - `utils/feature_scaling.py` utility module
3. **Integration Points** - Feature display in `app.py` and `class_choices` route

### How It Works
1. Features include `{placeholder}` syntax in their descriptions
2. A `scaling` object defines how each placeholder changes by level
3. `resolve_scaling_feature()` replaces placeholders with level-appropriate values
4. The system works transparently with existing code

## Data Format

### Feature with Scaling
```json
{
  "Channel Divinity": {
    "description": "Use Divine Spark (heal 2d8 + Cleric level HP or deal {damage_dice} Radiant/Necrotic damage) or Turn Undead (Wisdom save or turn for 1 minute). {uses} uses per Short/Long Rest.",
    "scaling": {
      "damage_dice": [
        {"min_level": 2, "value": "1d8"},
        {"min_level": 7, "value": "2d8"},
        {"min_level": 13, "value": "3d8"},
        {"min_level": 18, "value": "4d8"}
      ],
      "uses": [
        {"min_level": 2, "value": "2"},
        {"min_level": 7, "value": "3"},
        {"min_level": 17, "value": "4"}
      ]
    }
  }
}
```

### Scaling Metadata Schema
- **Top-level key**: `scaling` (optional object in feature data)
- **Placeholder keys**: Names matching `{placeholders}` in description
- **Breakpoints**: Array of objects with:
  - `min_level` (int): Character level when this value takes effect
  - `value` (string): The replacement value

### Resolution Logic
For each `{placeholder}`:
1. Find all breakpoints where `min_level <= character_level`
2. Select the one with the highest `min_level`
3. Replace `{placeholder}` with that breakpoint's `value`

## Examples

### Channel Divinity (Multiple Placeholders)
**Levels 2-6**: "deal 1d8 Radiant damage. 2 uses per Short/Long Rest"
**Levels 7-12**: "deal 2d8 Radiant damage. 3 uses per Short/Long Rest"
**Levels 13-16**: "deal 3d8 Radiant damage. 3 uses per Short/Long Rest"
**Levels 17-19**: "deal 3d8 Radiant damage. 4 uses per Short/Long Rest"
**Level 20**: "deal 4d8 Radiant damage. 4 uses per Short/Long Rest"

### Blessed Strikes (Single Placeholder)
**Levels 7-13**: "Divine Strike (+1d8 Necrotic/Radiant)"
**Levels 14-20**: "Divine Strike (+2d8 Necrotic/Radiant)"

## Code Integration

### Feature Display (app.py)
```python
from utils.feature_scaling import resolve_scaling_feature

# When building feature list for display:
description = resolve_scaling_feature(feature_data, character_level)
feature_entry = {
    "name": feature_name,
    "description": description,  # Already resolved
    "source": f"{class_name} Level {level}"
}
```

### Class Choices Route (app.py)
```python
# When adding features without choices to all_features_by_level:
description = resolve_scaling_feature(feature_data, character_level)
all_features_by_level[level].append({
    'name': feature_name,
    'type': 'info',
    'description': description,  # Already resolved
    'level': level,
    'source': 'Class'
})
```

## Benefits

### 1. Data Deduplication
**Before**:
```json
"2": {"Channel Divinity": "...1d8 damage. 2 uses..."},
"7": {"Improved Channel Divinity": "...2d8 damage. 3 uses..."},
"13": {"Greater Channel Divinity": "...3d8 damage. 3 uses..."},
"18": {"Superior Channel Divinity": "...4d8 damage. 4 uses..."}
```

**After**:
```json
"2": {
  "Channel Divinity": {
    "description": "...{damage_dice} damage. {uses} uses...",
    "scaling": { /* ... */ }
  }
}
```

### 2. Easy Maintenance
- Change scaling progression in one place
- No need to update multiple level entries
- Reduces risk of inconsistencies

### 3. Transparent Integration
- Existing code continues to work unchanged
- Resolution happens automatically during display
- No template or frontend changes needed

### 4. Flexible Design
- Multiple placeholders per feature
- Different scaling patterns for each placeholder
- Any number of level breakpoints

## Adding New Scaled Features

### Step 1: Identify Scaling Points
Determine which parts of the feature change with level:
- Damage dice (e.g., 1d6 → 2d6 → 3d6)
- Uses per rest (e.g., 1 → 2 → 3)
- Range or duration (e.g., 30 ft → 60 ft)
- Target count (e.g., 1 creature → 2 creatures)

### Step 2: Create Placeholders
Replace changing values with descriptive `{placeholders}`:
- `{damage_dice}` for damage values
- `{uses}` for usage counts
- `{range}` for distance values
- `{targets}` for creature counts

### Step 3: Define Breakpoints
Create scaling metadata with level breakpoints:
```json
"scaling": {
  "placeholder_name": [
    {"min_level": 1, "value": "initial_value"},
    {"min_level": 5, "value": "upgraded_value"},
    {"min_level": 10, "value": "final_value"}
  ]
}
```

### Step 4: Test Resolution
Use the test script to verify scaling at different levels:
```python
from utils.feature_scaling import resolve_scaling_feature
resolved = resolve_scaling_feature(feature_data, character_level)
print(resolved)
```

## Testing

### Unit Test
```bash
python test_scaling.py
```

### Integration Test
1. Create character at level 2 with the feature
2. View character summary - verify level 2 values
3. Level up character to level 7
4. View character summary - verify level 7 values

### Validation Checklist
- [ ] All `{placeholders}` are replaced (no `{` or `}` in output)
- [ ] Values match expected progression
- [ ] Minimum level breakpoint covers the feature's introduction level
- [ ] No gaps in level coverage (each level gets a value)

## Limitations & Future Work

### Current Limitations
1. **Static Text Only**: Can't calculate values (e.g., "Wisdom modifier + level")
2. **No Conditionals**: Can't express "if X then Y else Z" logic
3. **Single Resolution**: Happens once when feature is displayed

### Potential Enhancements
1. **Expression Support**: Allow `{level * 2}` or `{wisdom_modifier + proficiency}`
2. **Conditional Scaling**: Different progressions based on choices
3. **Live Resolution**: Update in real-time as character levels up
4. **API Endpoint**: `/api/resolve-feature?level=X` for external tools

## Comparison: Approach 1 vs Approach 2

### Approach 1: Upgrade Entries
**Pros**: Simple, explicit level entries
**Cons**: Data duplication, maintenance burden, inconsistency risk

### Approach 2: Scaling Metadata (CHOSEN)
**Pros**: DRY principle, easy maintenance, clear intent
**Cons**: Slightly more complex initial setup

**Winner**: Approach 2 provides better long-term maintainability and extensibility.

## Related Files
- `utils/feature_scaling.py` - Scaling resolution utility
- `data/classes/cleric.json` - Example implementation (Channel Divinity, Blessed Strikes)
- `app.py` - Integration points (lines ~465, ~840, ~900)
- `test_scaling.py` - Test script for validation
