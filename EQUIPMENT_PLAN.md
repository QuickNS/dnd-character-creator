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
- ❌ AC calculation from equipped armor
- ❌ Attack/damage calculation from equipped weapons
- ❌ Equipment display on character sheet

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

### Phase 3: Equipment Storage & Management

**Goal**: Store and manage equipment in character data

#### 3.1 Character Data Structure
```json
{
  "equipment": {
    "weapons": [
      {
        "name": "Longsword",
        "equipped": true,
        "quantity": 1,
        "properties": {...}
      }
    ],
    "armor": [
      {
        "name": "Chain Mail",
        "equipped": true,
        "properties": {...}
      }
    ],
    "shield": {
      "name": "Shield",
      "equipped": true,
      "properties": {...}
    },
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

#### 3.2 Equipment Manager Module
Create `modules/equipment_manager.py`:
```python
class EquipmentManager:
    def add_item(self, item_name, category, quantity=1)
    def equip_item(self, item_name, category)
    def unequip_item(self, item_name, category)
    def get_equipped_armor(self)
    def get_equipped_weapons(self)
    def can_equip(self, item_name, character_proficiencies)
    def calculate_total_weight(self)
    def calculate_armor_class(self, dex_modifier, equipped_armor, equipped_shield)
```

### Phase 4: Combat Statistics Integration

**Goal**: Calculate AC, attacks, and damage from equipment

#### 4.1 Armor Class Calculation
Update `modules/character_calculator.py`:
```python
def calculate_armor_class(self, character):
    equipped_armor = character['equipment']['armor']
    equipped_shield = character['equipment']['shield']
    dex_modifier = character['ability_modifiers']['Dexterity']
    
    if not equipped_armor:
        # Unarmored: 10 + DEX
        return 10 + dex_modifier
    
    armor_data = self.load_armor_data(equipped_armor['name'])
    
    if armor_data['category'] == 'Light Armor':
        # Light: AC + DEX
        ac = armor_data['ac_base'] + dex_modifier
    elif armor_data['category'] == 'Medium Armor':
        # Medium: AC + DEX (max 2)
        ac = armor_data['ac_base'] + min(dex_modifier, 2)
    else:  # Heavy Armor
        # Heavy: AC only
        ac = armor_data['ac_base']
    
    # Add shield
    if equipped_shield and equipped_shield.get('equipped'):
        shield_data = self.load_armor_data('Shield')
        ac += shield_data['ac_bonus']
    
    return ac
```

#### 4.2 Attack Calculations
```python
def calculate_weapon_attacks(self, character):
    attacks = []
    equipped_weapons = character['equipment']['weapons']
    
    for weapon in equipped_weapons:
        if not weapon.get('equipped'):
            continue
            
        weapon_data = self.load_weapon_data(weapon['name'])
        
        # Determine ability modifier
        if 'Finesse' in weapon_data['properties']:
            ability_mod = max(
                character['ability_modifiers']['Strength'],
                character['ability_modifiers']['Dexterity']
            )
            ability_name = 'STR/DEX'
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
        
        attacks.append({
            'name': weapon['name'],
            'attack_bonus': f"+{attack_bonus}",
            'damage': f"{damage_dice} + {damage_bonus}",
            'damage_type': weapon_data['damage_type'],
            'properties': weapon_data['properties']
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
```html
<!-- Equipment Section -->
<div class="card mb-4">
    <div class="sub-card-header bg-secondary">
        <h5 class="mb-0">Equipment</h5>
    </div>
    <div class="card-body">
        <h6>Armor & Shield</h6>
        <ul>
            {% for armor in character.equipment.armor %}
            <li>{{ armor.name }} (AC: {{ armor.properties.ac_base }})</li>
            {% endfor %}
            {% if character.equipment.shield %}
            <li>{{ character.equipment.shield.name }} (+{{ character.equipment.shield.properties.ac_bonus }} AC)</li>
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

### Phase 3: Calculations
- [ ] AC calculates correctly for Light armor
- [ ] AC calculates correctly for Medium armor (DEX max +2)
- [ ] AC calculates correctly for Heavy armor (no DEX)
- [ ] Shield bonus applies correctly
- [ ] Attack bonuses correct for STR weapons
- [ ] Attack bonuses correct for DEX weapons
- [ ] Attack bonuses correct for Finesse weapons
- [ ] Proficiency bonus applies when proficient
- [ ] No proficiency bonus when not proficient

### Phase 4: UI Integration
- [ ] Equipment displays on character summary
- [ ] AC shown with breakdown
- [ ] Attacks shown with bonuses
- [ ] Equipment selection UI intuitive
- [ ] Character sheet PDF includes equipment

## Technical Considerations

### Performance
- Cache equipment data in data_loader
- Don't recalculate AC/attacks on every page load
- Store calculated values in session

### Validation
- Check proficiency before allowing equipment
- Validate STR requirement for heavy armor
- Prevent equipping multiple armor pieces
- Allow multiple weapons (main hand + off hand)

### Edge Cases
- Unarmored AC (10 + DEX)
- Versatile weapons (1d8 or 1d10)
- Two-weapon fighting
- Monk unarmored defense (10 + DEX + WIS)
- Barbarian unarmored defense (10 + DEX + CON)
- Magic armor/weapons (future)

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
1. Weapon database
2. Armor database
3. Starting equipment selection
4. Equipment storage
5. AC calculation from armor
6. Basic attack display

**Should Have (v1.1)**:
7. Adventuring gear database
8. Equipment weight tracking
9. Full attack/damage calculation
10. Equipment on character sheet PDF

**Could Have (v2.0)**:
11. Magic items
12. Buy/sell interface
13. Encumbrance rules
14. Equipment cards generation

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

- [ ] Phase 1: Equipment Database
- [ ] Phase 2: Starting Equipment
- [ ] Phase 3: Storage & Management
- [ ] Phase 4: Combat Integration
- [ ] Phase 5: UI Integration
- [ ] Phase 6: Wizard Flow
- [ ] Testing Complete
- [ ] Documentation Updated

---

**Next Steps When Resuming**:
1. Start with Phase 1.1 - Create weapons.json with 10-15 common weapons
2. Test loading weapons in data_loader
3. Create Phase 1.2 - armor.json with all armor types
4. Implement basic equipment selection UI
5. Integrate AC calculation
