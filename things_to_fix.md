# List of Identified Cases we are not handling

## ✅ COMPLETED

### Character Summary - Spellcasting Display
- ✅ Spellcasting section added with spell slot information at the top
- ✅ All spells displayed by level with proper details (school, casting time, range, components, duration, description)
- ✅ Domain/subclass spells show "Always Prepared" badge
- ✅ Species/lineage spells show both "Always Prepared" and "1/Day (No Slot)" badges
- ✅ School of magic shown as property (not badge)
- ✅ Spell slots display with Long Rest recovery note

### Feature Scaling System
- ✅ Created utility for resolving level-based feature scaling
- ✅ Updated class data files with scaling metadata (Channel Divinity, Blessed Strikes)
- ✅ Integrated scaling resolution into CharacterBuilder
- ✅ Documented system in docs/FEATURE_SCALING.md
- ✅ Verified scaling works correctly for level-dependent features

### Spell System Unification
- ✅ Unified domain and species spell granting through effects system
- ✅ All spell granting uses `grant_spell` effect type
- ✅ Domain spells stored in `character['spells']['prepared']`
- ✅ Species spells tracked with metadata for once-per-day indicator
- ✅ Spell tables show availability by character level with ✓/🔒 indicators
- ✅ Consolidated elf lineage spells into single traits (High Elf, Drow, Wood Elf)

### Cleric Class
- ✅ Divine Order → Protector: grants Martial weapons and Heavy Armor proficiencies
- ✅ Divine Order → Thaumaturge: grants one extra Cleric cantrip
- ✅ Divine Order choices display with specific descriptions (not generic prompt)
- ✅ Thaumaturge bonus cantrip displayed in feature description
- ✅ Light Domain: grants Light cantrip
- ✅ Light Domain Spells: table display with level-based availability
- ✅ Thaumaturge: WIS bonus to Intelligence checks (Arcana/Religion), minimum +1
- ✅ Channel Divinity scales with level (damage and uses)
- ✅ Blessed Strikes scales with level (damage dice)

### Proficiency Display
- ✅ Weapon proficiencies from choices display correctly
- ✅ Armor proficiencies from choices display correctly  
- ✅ Shields always displayed last in armor proficiency list
- ✅ Proficiencies sorted: Light/Medium/Heavy armor, other items, then Shields

### Feature Display System
- ✅ Choice-specific descriptions replace generic prompts
- ✅ Nested choices append to parent feature (bonus cantrips)
- ✅ Source names display correctly (class/subclass/species/lineage)
- ✅ Scaling values properly substituted in descriptions
- ✅ Features with choices show chosen value in name
- ✅ HTML rendering supported for feature descriptions (tables, etc.)

### HTML Character Sheet Generation
- ✅ Created HTML character sheet with background images (templates/character_sheet_pdf.html)
- ✅ Background images extracted from PDF at high quality (300 DPI)
- ✅ Positioned input fields overlay character sheet background
- ✅ Flask route (/character-sheet) displays fillable sheet
- ✅ Print to PDF functionality with browser print dialog
- ✅ All calculated values included (combat stats, saves, skills, spell slots)
- ✅ Basic field positioning (name, class, level, abilities, modifiers, AC, initiative, HP, size, passive perception)

## 🔄 IN PROGRESS / TODO

### High-Elf
- Prestidigitation can be substituded by any Wizard Cantrip after a Long Rest - need to model this to offer options to choose from in character creator or later

### Champion: Remarkable Athlete
Needs to choose

### Character Summary
- Feat description is just where it comes from. We should list description and benefits.
- Spellcasting feature should have a better output. It should be caracterized with properties to enable better output than a simple string.

### HTML Character Sheet Refinement
- Position remaining fields (saving throws, skills, proficiencies, features, spells)
- Fine-tune field positions to align with background image
- Add equipment section positioning
- Test print output quality across browsers
- Add helper tool for positioning fields visually
- Consider responsive design for mobile viewing
- Consider spell slot tracker formatting
- Consider exhaustion tracker
- Format equipment and inventory sections

### Species Innate Spellcasting Abilities
- Some species (Tiefling, Elf lineages) offer spellcasting with ability choice (Intelligence, Wisdom, or Charisma)
- Need to implement choice system for spellcasting ability selection
- Currently data files have `spellcasting_ability_choices` but not implemented in wizard

### Repetitions & Conflicts
- **Repeated Skill Proficiency**: Users may select skills that are later granted by Background/Feat
- **Repeated Cantrips**: Users may select cantrips that are later granted by subclass/species
- **Solution**: Add a pre-finalization step to detect and resolve conflicts
- Allow users to swap duplicate proficiencies/cantrips before completing character

### Tiefling Variants
- Tiefling sub-species variants (Abyssal, Chthonic, Infernal) need testing
- Verify Fiendish Legacy choices work correctly
- May need spell data files for Tiefling-specific spells

### Other Classes
- Need to apply scaling system to other classes:
  - Rogue: Sneak Attack damage scaling
  - Barbarian: Rage Damage scaling
  - Monk: Martial Arts Die scaling
  - Warlock: Invocations and Pact Magic scaling
- Verify all class features use effects system where applicable

### Druid
- Druid class and subclass files mention non-existent abilities (e.g., Primal Strike)
- Need to regenerate data files from D&D 2024 sources
- Verify Wild Shape mechanics

### Data Validation
- Add automated validation for all data files against schemas
- Check for missing spell definitions
- Verify all effect types are documented

### Missing Spell Definitions
- Need to create definition files for any spells referenced but not yet defined
- Check Light Domain spells: Arcane Eye, Wall of Fire, Flame Strike, Scrying
- Check elf lineage spells: all definitions needed

## 📋 FUTURE ENHANCEMENTS

### Equipment System
- See EQUIPMENT_PLAN.md for detailed implementation plan
- Equipment database (weapons, armor, adventuring gear)
- Starting equipment selection from class/background
- AC calculation from equipped armor
- Attack/damage calculation from equipped weapons
- Equipment display on character sheet

### Character Sheet Export Formats
- Spell cards generation
- Modular cards (weapon cards, armor cards, feature cards)
- Alternative character sheet templates
- Multiple page support for complex characters

### Spell Preparation
- Interface for selecting prepared spells from class list
- Track which spells are prepared vs. available
- Enforce preparation limits

### Long Rest / Short Rest Tracking
- Track resource usage (spell slots, abilities, HP)
- Implement rest mechanics for recovery
- Session-based character state management

### Multiclassing
- Support for multiclass characters
- Proper spell slot calculation for multiclass casters
- Prerequisite validation
