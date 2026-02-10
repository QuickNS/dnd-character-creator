# Equipment System Implementation Plan

**Status**: Planning Phase  
**Priority**: Medium  
**Estimated Effort**: 3-4 development sessions

## Current State

### What Exists
- ✅ Weapon/armor proficiencies tracked in CharacterBuilder
- ✅ Proficiencies displayed on character summary
- ✅ Placeholder equipment structure in character data
- ✅ Basic AC calculation function (not integrated)
- ✅ Equipment section in character_sheet_converter (placeholder)

### What's Missing
- ❌ Equipment database (weapons, armor, adventuring gear)
- ❌ Starting equipment selection UI
- ❌ Equipment choices from class/background
- ❌ Equipment storage in character data
- ❌ AC Options Calculator (all possible combinations)
- ❌ AC Options Card display
- ❌ Weapon attack stats calculation
- ❌ Equipment display on character sheet

## 🎯 Key Design Decision: AC Options System

**IMPORTANT**: This implementation uses a **simplified, transparent approach** instead of traditional "equipped" item management.

### Design Philosophy
Rather than tracking which armor is "equipped," we:
1. **Store all equipment in inventory** (no equipped flags)
2. **Calculate ALL possible AC combinations** from available armor/shields
3. **Display them ranked** in an "AC Options Card" on character summary
4. **Show full formulas** so players understand the math
5. **Include warnings** about stealth disadvantage, STR requirements, etc.

### Benefits
- ✅ **Simpler implementation** - No equip/unequip UI complexity
- ✅ **More transparent** - Players see all their defensive options at once
- ✅ **Educational** - Formulas help players understand D&D mechanics
- ✅ **Better decision-making** - Trade-offs are clear (AC vs stealth, etc.)
- ✅ **Future-proof** - Easy to add magic items, temporary effects, etc.

### Example Display
```
┌─ Armor Class Options ───────────────┐
│ 🛡️ BEST: AC 18                      │
│ Chain Mail + Shield                  │
│ 16 (armor) + 2 (shield) = 18        │
│ ⚠️ Disadvantage on Stealth           │
├──────────────────────────────────────┤
│ AC 16 - Chain Mail                   │
│ AC 14 - Leather Armor + Shield       │
│ AC 14 - Leather Armor                │
│ AC 13 - Unarmored                    │
└──────────────────────────────────────┘
```

This approach focuses on **information over automation**, empowering players to understand their choices.

## Implementation Phases

### Phase 1: Equipment Database (Foundation)

**Goal**: Create comprehensive equipment data files

#### 1.1 Weapon Database (`data/equipment/weapons.json`)
```json
{
  "Longsword": {
    "category": "Martial Melee",
    "cost": "15 gp",
    "damage": "1d8",
    "damage_type": "Slashing",
    "weight": 3,
    "properties": ["Versatile (1d10)"],
    "proficiency_required": "Martial weapons"
  },
  "Shortbow": {
    "category": "Simple Ranged",
    "cost": "25 gp",
    "damage": "1d6",
    "damage_type": "Piercing",
    "weight": 2,
    "properties": ["Ammunition (range 80/320)", "Two-Handed"],
    "proficiency_required": "Simple weapons"
  }
}
```

**Weapon Categories**:
- Simple Melee Weapons (15-20 items)
- Simple Ranged Weapons (5-10 items)
- Martial Melee Weapons (15-20 items)
- Martial Ranged Weapons (5-10 items)

**Properties to Include**:
- Ammunition (range)
- Finesse
- Heavy
- Light
- Loading
- Range (thrown)
- Reach
- Two-Handed
- Versatile

#### 1.2 Armor Database (`data/equipment/armor.json`)
```json
{
  "Leather Armor": {
    "category": "Light Armor",
    "cost": "10 gp",
    "ac_base": 11,
    "ac_formula": "11 + DEX",
    "weight": 10,
    "stealth_disadvantage": false,
    "strength_requirement": null,
    "proficiency_required": "Light armor"
  },
  "Chain Mail": {
    "category": "Heavy Armor",
    "cost": "75 gp",
    "ac_base": 16,
    "ac_formula": "16",
    "weight": 55,
    "stealth_disadvantage": true,
    "strength_requirement": 13,
    "proficiency_required": "Heavy armor"
  },
  "Shield": {
    "category": "Shield",
    "cost": "10 gp",
    "ac_bonus": 2,
    "weight": 6,
    "proficiency_required": "Shields"
  }
}
```

**Armor Categories**:
- Light Armor (3-4 types)
- Medium Armor (5-6 types)
- Heavy Armor (4-5 types)
- Shields (1-2 types)

#### 1.3 Adventuring Gear Database (`data/equipment/adventuring_gear.json`)
```json
{
  "Backpack": {
    "cost": "2 gp",
    "weight": 5,
    "category": "Container"
  },
  "Rope, Hempen (50 feet)": {
    "cost": "1 gp",
    "weight": 10,
    "category": "Utility"
  },
  "Thieves' Tools": {
    "cost": "25 gp",
    "weight": 1,
    "category": "Tool"
  }
}
```

**Categories**:
- Containers
- Utility
- Tools
- Consumables
- Miscellaneous

### Phase 2: Starting Equipment System

**Goal**: Allow players to select starting equipment from class/background

#### 2.1 Class Starting Equipment Data
Add to each class JSON:
```json
{
  "starting_equipment": {
    "choices": [
      {
        "description": "Choose one:",
        "options": [
          {
            "items": ["Chain Mail"],
            "condition": "if proficient"
          },
          {
            "items": ["Leather Armor", "Longbow", "20 Arrows"]
          }
        ]
      },
      {
        "description": "Choose one:",
        "options": [
          {"items": ["Martial weapon", "Shield"]},
          {"items": ["Two Martial weapons"]}
        ]
      },
      {
        "description": "Choose one:",
        "options": [
          {"items": ["Light Crossbow", "20 Bolts"]},
          {"items": ["Two Handaxes"]}
        ]
      }
    ],
    "fixed_items": [
      "Explorer's Pack"
    ]
  }
}
```

#### 2.2 Background Starting Equipment
Add to background JSON:
```json
{
  "starting_equipment": {
    "items": [
      "Traveler's Clothes",
      "Belt Pouch",
      "15 gp"
    ]
  }
}
```

#### 2.3 Equipment Selection Route
Create `/choose-equipment` route:
- Display equipment choices from class
- Display equipment from background
- Allow weapon/armor selection from categories
- Store selections in character data
- Validate proficiency requirements

### Phase 3: Equipment Storage & Inventory (SIMPLIFIED)

**Goal**: Store equipment inventory (no "equipped" system needed)

**Design Philosophy**: Rather than tracking what's "equipped", we calculate ALL possible AC combinations from inventory and present them to the player. This is simpler, more transparent, and more useful.

#### 3.1 Character Data Structure (Simplified)
```json
{
  "equipment": {
    "weapons": [
      {
        "name": "Longsword",
        "quantity": 1,
        "properties": {...}
      }
    ],
    "armor": [
      {
        "name": "Chain Mail",
        "properties": {...}
      },
      {
        "name": "Leather Armor",
        "properties": {...}
      }
    ],
    "shields": [
      {
        "name": "Shield",
        "properties": {...}
      }
    ],
    "other": [
      {
        "name": "Rope, Hempen (50 feet)",
        "quantity": 1,
        "properties": {...}
      }
    ],
    "currency": {
      "copper": 0,
      "silver": 0,
      "electrum": 0,
      "gold": 15,
      "platinum": 0
    }
  }
}
```

**Note**: No `equipped` flags. All armor/shields in inventory are potential options.

#### 3.2 Equipment Manager Module
Create `modules/equipment_manager.py`:
```python
class EquipmentManager:
    def add_item(self, item_name, category, quantity=1)
    def remove_item(self, item_name, category, quantity=1)
    def get_all_armor(self)
    def get_all_shields(self)
    def get_all_weapons(self)
    def can_use_armor(self, armor_name, character_proficiencies)
    def can_use_weapon(self, weapon_name, character_proficiencies)
    def calculate_total_weight(self)
```

### Phase 4: AC Options Calculator

**Goal**: Calculate ALL possible AC combinations and present them as options

**Design Philosophy**: Instead of calculating a single AC, we generate all valid AC combinations from inventory and show them ranked by AC value. This gives players complete transparency about their defensive options.

#### 4.1 AC Options Calculation
Update `modules/character_calculator.py`:
```python
def calculate_all_ac_options(self, character):
    """
    Calculate all possible AC combinations from inventory.
    Returns a list of AC options sorted by AC value (highest first).
    """
    options = []
    dex_modifier = character['ability_modifiers']['Dexterity']
    proficiencies = character['proficiencies']
    
    # Get all armor and shields from inventory
    all_armor = character['equipment'].get('armor', [])
    all_shields = character['equipment'].get('shields', [])
    
    # Calculate armor options (with and without shield)
    for armor in all_armor:
        armor_data = self.load_armor_data(armor['name'])
        
        # Check proficiency
        if not self.has_proficiency(armor_data, proficiencies):
            continue
        
        # Calculate AC for this armor
        ac_without_shield = self._calculate_armor_ac(armor_data, dex_modifier, character)
        
        # Option 1: Armor without shield
        options.append({
            'ac': ac_without_shield,
            'armor': armor['name'],
            'shield': None,
            'formula': self._get_ac_formula(armor_data, dex_modifier, None, character),
            'notes': self._get_armor_notes(armor_data, character),
            'valid': True
        })
        
        # Option 2: Armor with each shield
        for shield in all_shields:
            if not self.has_proficiency(shield, proficiencies):
                continue
            
            shield_data = self.load_armor_data(shield['name'])
            ac_with_shield = ac_without_shield + shield_data.get('ac_bonus', 0)
            
            options.append({
                'ac': ac_with_shield,
                'armor': armor['name'],
                'shield': shield['name'],
                'formula': self._get_ac_formula(armor_data, dex_modifier, shield_data, character),
                'notes': self._get_armor_notes(armor_data, character),
                'valid': True
            })
    
    # Unarmored options (with and without shield)
    unarmored_ac = self._calculate_unarmored_ac(character)
    
    # Unarmored without shield
    options.append({
        'ac': unarmored_ac,
        'armor': None,
        'shield': None,
        'formula': self._get_unarmored_formula(character),
        'notes': [],
        'valid': True,
        'is_unarmored': True
    })
    
    # Unarmored with shields
    for shield in all_shields:
        if not self.has_proficiency(shield, proficiencies):
            continue
        
        shield_data = self.load_armor_data(shield['name'])
        options.append({
            'ac': unarmored_ac + shield_data.get('ac_bonus', 0),
            'armor': None,
            'shield': shield['name'],
            'formula': f"{self._get_unarmored_formula(character)} + Shield ({shield_data.get('ac_bonus', 0)})",
            'notes': [],
            'valid': True,
            'is_unarmored': True
        })
    
    # Sort by AC (highest first), then by complexity (simpler first)
    options.sort(key=lambda x: (-x['ac'], x['armor'] is None))
    
    return options

def _calculate_armor_ac(self, armor_data, dex_modifier, character):
    """Calculate AC for a specific armor"""
    category = armor_data.get('category')
    base_ac = armor_data.get('ac_base', 0)
    
    if category == 'Light Armor':
        return base_ac + dex_modifier
    elif category == 'Medium Armor':
        return base_ac + min(dex_modifier, 2)
    else:  # Heavy Armor
        return base_ac

def _calculate_unarmored_ac(self, character):
    """Calculate unarmored AC (may be overridden by class features)"""
    dex_modifier = character['ability_modifiers']['Dexterity']
    
    # Check for special unarmored defense
    # Barbarian: 10 + DEX + CON
    if 'Unarmored Defense' in character.get('features', {}):
        feature_desc = character['features']['Unarmored Defense']
        if 'Constitution' in feature_desc:
            con_modifier = character['ability_modifiers']['Constitution']
            return 10 + dex_modifier + con_modifier
        # Monk: 10 + DEX + WIS
        elif 'Wisdom' in feature_desc:
            wis_modifier = character['ability_modifiers']['Wisdom']
            return 10 + dex_modifier + wis_modifier
    
    # Default: 10 + DEX
    return 10 + dex_modifier

def _get_ac_formula(self, armor_data, dex_modifier, shield_data, character):
    """Generate human-readable AC formula"""
    category = armor_data.get('category')
    base_ac = armor_data.get('ac_base', 0)
    
    if category == 'Light Armor':
        formula = f"{base_ac} (armor) + {dex_modifier} (DEX)"
    elif category == 'Medium Armor':
        dex_bonus = min(dex_modifier, 2)
        formula = f"{base_ac} (armor) + {dex_bonus} (DEX, max +2)"
    else:  # Heavy Armor
        formula = f"{base_ac} (armor)"
    
    if shield_data:
        shield_bonus = shield_data.get('ac_bonus', 0)
        formula += f" + {shield_bonus} (shield)"
    
    return formula

def _get_unarmored_formula(self, character):
    """Get formula for unarmored AC"""
    dex_modifier = character['ability_modifiers']['Dexterity']
    
    if 'Unarmored Defense' in character.get('features', {}):
        feature_desc = character['features']['Unarmored Defense']
        if 'Constitution' in feature_desc:
            con_modifier = character['ability_modifiers']['Constitution']
            return f"10 + {dex_modifier} (DEX) + {con_modifier} (CON)"
        elif 'Wisdom' in feature_desc:
            wis_modifier = character['ability_modifiers']['Wisdom']
            return f"10 + {dex_modifier} (DEX) + {wis_modifier} (WIS)"
    
    return f"10 + {dex_modifier} (DEX)"

def _get_armor_notes(self, armor_data, character):
    """Get warnings/notes about armor"""
    notes = []
    
    if armor_data.get('stealth_disadvantage'):
        notes.append('⚠️ Disadvantage on Stealth checks')
    
    str_req = armor_data.get('strength_requirement')
    if str_req:
        str_score = character['ability_scores']['Strength']
        if str_score < str_req:
            notes.append(f'⚠️ Requires STR {str_req} (you have {str_score})')
    
    return notes
```

#### 4.2 AC Options Display Component
The character summary will include a prominent "**Armor Class Options**" card showing all combinations.

**Display Structure**:
```
┌─ Armor Class Options ─────────────────────┐
│                                             │
│ 🛡️ BEST OPTION: AC 18                      │
│ Chain Mail + Shield                         │
│ 16 (armor) + 2 (shield) = 18               │
│ ⚠️ Disadvantage on Stealth checks          │
│                                             │
│ ── Alternative Options ───────────────────  │
│                                             │
│ AC 16 - Chain Mail                          │
│ 16 (armor) = 16                            │
│ ⚠️ Disadvantage on Stealth checks          │
│                                             │
│ AC 14 - Leather Armor + Shield              │
│ 11 (armor) + 3 (DEX) + 2 (shield) = 16     │
│                                             │
│ AC 14 - Leather Armor                       │
│ 11 (armor) + 3 (DEX) = 14                  │
│                                             │
│ AC 13 - Unarmored                           │
│ 10 + 3 (DEX) = 13                          │
│                                             │
└────────────────────────────────────────────┘
```

#### 4.3 Server-Side Integration
In `app.py`, add AC options to character summary:
```python
@app.route('/character-summary')
def character_summary():
    from utils.route_helpers import get_builder_from_session
    builder = get_builder_from_session()
    character = builder.to_character()  # Get complete calculated character
    
    # Calculate all AC options (already done in to_character)
    ac_options = character.get('ac_options', [])
    
    # Get the best AC
    best_ac = ac_options[0]['ac'] if ac_options else 10
    
    return render_template(
        'character_summary.html',
        character=character,
        ac_options=ac_options,
        best_ac=best_ac
    )
```

#### 4.4 Weapon Attack Calculations
For weapons, we'll show all available weapons with their stats (no "equipped" flag needed):
```python
def calculate_weapon_attacks(self, character):
    """Calculate attack stats for all weapons in inventory"""
    attacks = []
    all_weapons = character['equipment'].get('weapons', [])
    
    for weapon in all_weapons:
        weapon_data = self.load_weapon_data(weapon['name'])
        
        # Determine ability modifier
        if 'Finesse' in weapon_data['properties']:
            str_mod = character['ability_modifiers']['Strength']
            dex_mod = character['ability_modifiers']['Dexterity']
            ability_mod = max(str_mod, dex_mod)
            ability_name = f'STR/DEX ({"STR" if str_mod >= dex_mod else "DEX"})'
        elif weapon_data['category'].endswith('Ranged'):
            ability_mod = character['ability_modifiers']['Dexterity']
            ability_name = 'DEX'
        else:
            ability_mod = character['ability_modifiers']['Strength']
            ability_name = 'STR'
        
        # Check proficiency
        is_proficient = self.check_weapon_proficiency(
            weapon_data, 
            character['proficiencies']['weapons']
        )
        prof_bonus = character['proficiency_bonus'] if is_proficient else 0
        
        # Calculate attack bonus
        attack_bonus = ability_mod + prof_bonus
        
        # Calculate damage
        damage_dice = weapon_data['damage']
        damage_bonus = ability_mod
        
        # Handle versatile weapons
        versatile_damage = None
        for prop in weapon_data.get('properties', []):
            if prop.startswith('Versatile'):
                # Extract damage from "Versatile (1d10)"
                versatile_damage = prop.split('(')[1].split(')')[0]
        
        attacks.append({
            'name': weapon['name'],
            'attack_bonus': f"+{attack_bonus}" if attack_bonus >= 0 else str(attack_bonus),
            'damage': f"{damage_dice} + {damage_bonus}",
            'versatile_damage': f"{versatile_damage} + {damage_bonus}" if versatile_damage else None,
            'damage_type': weapon_data['damage_type'],
            'properties': weapon_data['properties'],
            'ability': ability_name,
            'proficient': is_proficient
        })
    
    return attacks
```

### Phase 5: UI Integration

**Goal**: Display equipment throughout the application

#### 5.1 Equipment Selection Page
Template: `templates/choose_equipment.html`
- Display class equipment choices
- Display background equipment
- Show proficiency requirements
- Real-time validation
- Equipment preview

#### 5.2 Character Summary Updates
Update `templates/character_summary.html`:

**AC Options Card** (prominent display):
```html
<!-- Armor Class Options Card -->
<div class="card mb-4">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0">🛡️ Armor Class Options</h5>
    </div>
    <div class="card-body">
        {% if ac_options %}
            <!-- Best AC Option -->
            <div class="best-ac-option p-3 mb-3 border border-success rounded bg-light">
                <h6 class="text-success mb-2">
                    <strong>BEST OPTION: AC {{ ac_options[0].ac }}</strong>
                </h6>
                <p class="mb-1">
                    {% if ac_options[0].armor %}
                        {{ ac_options[0].armor }}
                    {% else %}
                        Unarmored
                    {% endif %}
                    {% if ac_options[0].shield %}
                        + {{ ac_options[0].shield }}
                    {% endif %}
                </p>
                <p class="text-muted mb-2">{{ ac_options[0].formula }}</p>
                {% if ac_options[0].notes %}
                    {% for note in ac_options[0].notes %}
                        <div class="text-warning">{{ note }}</div>
                    {% endfor %}
                {% endif %}
            </div>
            
            <!-- Alternative Options -->
            {% if ac_options|length > 1 %}
                <h6 class="border-top pt-3 mb-3">Alternative Options</h6>
                {% for option in ac_options[1:] %}
                    <div class="ac-option p-2 mb-2 border rounded">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>AC {{ option.ac }}</strong> - 
                                {% if option.armor %}
                                    {{ option.armor }}
                                {% else %}
                                    Unarmored
                                {% endif %}
                                {% if option.shield %}
                                    + {{ option.shield }}
                                {% endif %}
                            </div>
                        </div>
                        <small class="text-muted">{{ option.formula }}</small>
                        {% if option.notes %}
                            {% for note in option.notes %}
                                <div class="text-warning small">{{ note }}</div>
                            {% endfor %}
                        {% endif %}
                    </div>
                {% endfor %}
            {% endif %}
        {% else %}
            <p class="text-muted">No armor in inventory. AC = 10 + DEX modifier</p>
        {% endif %}
    </div>
</div>

<!-- Equipment Inventory -->
<div class="card mb-4">
    <div class="sub-card-header bg-secondary">
        <h5 class="mb-0">Equipment Inventory</h5>
    </div>
    <div class="card-body">
        <h6>Armor</h6>
        <ul>
            {% for armor in character.equipment.armor %}
            <li>{{ armor.name }}</li>
            {% endfor %}
            {% if character.equipment.shields %}
                {% for shield in character.equipment.shields %}
                <li>{{ shield.name }}</li>
                {% endfor %}
            {% endif %}
        </ul>
        
        <h6>Weapons</h6>
        <ul>
            {% for weapon in character.equipment.weapons %}
            <li>
                {{ weapon.name }} 
                ({{ weapon.properties.damage }} {{ weapon.properties.damage_type }})
            </li>
            {% endfor %}
        </ul>
        
        <h6>Other Equipment</h6>
        <ul>
            {% for item in character.equipment.other %}
            <li>{{ item.name }} {% if item.quantity > 1 %}(×{{ item.quantity }}){% endif %}</li>
            {% endfor %}
        </ul>
    </div>
</div>
```

#### 5.3 Character Sheet (HTML) Updates
Update `templates/character_sheet_pdf.html`:
- Add equipment fields
- Position weapon attack blocks
- Show AC calculation breakdown
- Display carried items

### Phase 6: Wizard Flow Integration

**Goal**: Add equipment selection to character creation wizard

#### 6.1 Wizard Step Order
```
1. Species → 2. Background → 3. Class → 4. Subclass → 
5. Ability Scores → 6. Skills → 7. Equipment → 8. Summary
```

#### 6.2 Equipment Step Implementation
- After ability scores assigned
- Before final summary
- Show calculated AC preview
- Show attack bonuses preview
- Validation before proceeding

## Data Files to Create

### Priority 1 (Essential)
1. `data/equipment/weapons.json` - All D&D 2024 weapons
2. `data/equipment/armor.json` - All armor types + shields
3. `data/equipment/starting_packs.json` - Explorer's Pack, etc.

### Priority 2 (Important)
4. `data/equipment/adventuring_gear.json` - General equipment
5. `data/equipment/tools.json` - Artisan's tools, gaming sets, etc.

### Priority 3 (Nice to Have)
6. `data/equipment/magic_items.json` - Common magic items (future)

## Module Files to Create/Update

### New Files
- `modules/equipment_manager.py` - Equipment storage and management
- `utils/equipment_loader.py` - Load equipment data from JSON
- `templates/choose_equipment.html` - Equipment selection UI

### Files to Update
- `modules/character_builder.py` - Add equipment methods
- `modules/character_calculator.py` - Update AC calculation
- `app.py` - Add equipment selection route
- `templates/character_summary.html` - Display equipment
- `templates/character_sheet_pdf.html` - Add equipment fields

## Testing Checklist

### Phase 1: Data Files
- [ ] All weapon categories represented
- [ ] All armor types with correct AC formulas
- [ ] Properties match D&D 2024 rules
- [ ] Costs and weights accurate

### Phase 2: Selection System
- [ ] Class equipment choices load correctly
- [ ] Background equipment grants properly
- [ ] Proficiency validation works
- [ ] Can select from weapon/armor categories
- [ ] Equipment stored in character data

### Phase 3: Storage & Display (SIMPLIFIED)
- [ ] Equipment stored in inventory (no "equipped" flags)
- [ ] All armor pieces stored in `armor` array
- [ ] All shields stored in `shields` array
- [ ] All weapons stored in `weapons` array

### Phase 4: AC Options Calculator
- [ ] AC calculates correctly for all Light armor options
- [ ] AC calculates correctly for all Medium armor options (DEX max +2)
- [ ] AC calculates correctly for all Heavy armor options (no DEX)
- [ ] Shield bonus applies correctly to all options
- [ ] Unarmored AC calculated correctly
- [ ] Special unarmored defense (Barbarian/Monk) works
- [ ] AC options sorted by value (highest first)
- [ ] Proficiency checks prevent invalid options
- [ ] STR requirement warnings display correctly
- [ ] Stealth disadvantage warnings display correctly
- [ ] Attack bonuses correct for STR weapons
- [ ] Attack bonuses correct for DEX weapons
- [ ] Attack bonuses correct for Finesse weapons
- [ ] Proficiency bonus applies when proficient
- [ ] No proficiency bonus when not proficient

### Phase 5: UI Integration
- [ ] AC Options card displays prominently on character summary
- [ ] Best AC option highlighted at top
- [ ] Alternative AC options listed below
- [ ] Formula breakdown shown for each option
- [ ] Warnings/notes display correctly (stealth, STR req)
- [ ] Equipment inventory displays all items
- [ ] Weapon stats shown correctly
- [ ] Equipment selection UI intuitive
- [ ] Character sheet PDF includes AC options

## Technical Considerations

### Performance
- Cache equipment data in data_loader
- Calculate AC options once per page load
- Store AC options in session if needed

### Validation
- Check proficiency before showing AC option
- Validate STR requirement for heavy armor
- Show warnings for invalid options (don't hide them, educate the player)

### Edge Cases
- Unarmored AC (10 + DEX)
- Barbarian unarmored defense (10 + DEX + CON)
- Monk unarmored defense (10 + DEX + WIS)
- Multiple armor pieces in inventory (show all combinations)
- Multiple shields in inventory (show each option)
- No armor in inventory (show only unarmored options)

## Future Enhancements (Post-MVP)

### Phase 7: Advanced Features
- Equipment encumbrance/weight tracking
- Currency conversion
- Buy/sell equipment during play
- Equipment conditions (damaged, broken)
- Attunement for magic items

### Phase 8: Combat Integration
- Ammunition tracking
- Weapon properties (reach, thrown)
- Improvised weapons
- Unarmed strikes
- Natural weapons (claws, bite)

### Phase 9: Character Sheet Export
- Include equipment in JSON export
- Generate equipment cards
- Weapon cards with full stats
- Armor card with AC breakdown

## Implementation Priority

**Must Have (MVP)**:
1. Weapon database (`data/equipment/weapons.json`)
2. Armor database (`data/equipment/armor.json`)
3. Starting equipment selection UI
4. Equipment inventory storage (no "equipped" flags)
5. **AC Options Calculator** - calculate ALL possible AC combinations
6. **AC Options Card** - display all AC options on character summary
7. Weapon attack stats display

**Should Have (v1.1)**:
8. Adventuring gear database
9. Equipment weight tracking
10. Detailed weapon properties display (reach, thrown, etc.)
11. Equipment on character sheet PDF
12. Starting equipment packs (Explorer's Pack, etc.)

**Could Have (v2.0)**:
13. Magic items
14. Buy/sell interface
15. Encumbrance rules
16. Equipment cards generation
17. Versatile weapon two-hand mode toggle

## Resources Needed

### D&D 2024 References
- Player's Handbook 2024 - Equipment chapter
- SRD 2024 - Weapons and armor tables
- Verify all stat blocks and properties

### Development Tools
- JSON schema validator
- Equipment data entry templates
- Test character with various equipment loadouts

## Progress Tracking

- [✅] Phase 1: Equipment Database (weapons, armor, shields)
- [✅] Phase 2: Starting Equipment Selection System  
- [✅] Phase 3: Equipment Inventory Storage (SIMPLIFIED - no equipping)
- [✅] Phase 4: AC Options Calculator & Weapon Stats
- [✅] Phase 5: UI Integration (AC Options Card + Inventory Display)
- [ ] Phase 6: Wizard Flow Integration
- [ ] Testing Complete
- [ ] Documentation Updated

---

**Next Steps When Resuming**:
1. Start with Phase 1.1 - Create weapons.json with 10-15 common weapons
2. Test loading weapons in data_loader  
3. Create Phase 1.2 - armor.json with all armor types + shields
4. Implement basic equipment selection UI (Phase 2)
5. Create AC Options Calculator (Phase 4.1)
6. Design and implement AC Options Card UI (Phase 5.2)

**Key Design Decision**:
✅ **No "equipped" system** - Calculate and display ALL possible AC options from inventory
✅ **Transparency over automation** - Show players all their choices with full calculations
✅ **Educational approach** - Display formulas and warnings to help players understand mechanics
