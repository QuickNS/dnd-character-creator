# D&D 2024 Character Creator - TODO List

**Last Updated**: 2026-02-06

## 📋 Recent Completed Work

### Architectural Refactors (2026-02-06) ✅
- CharacterBuilder established as single source of truth for ALL calculations
- Routes refactored as pure consumers of `builder.to_character()`
- Data-driven design implemented (no hardcoded lists)
- Equipment categorization uses data files instead of keyword lists
- Documentation updated to reflect new architecture
- See: [docs/REFACTOR_2026_02_06.md](docs/REFACTOR_2026_02_06.md)

### Code Cleanup (2026-02-06) ✅
- Removed unused `utils/spell_loader.py`
- Removed duplicate `utils/feature_scaling.py` (functionality in CharacterBuilder)
- Archived historical PHASE documents to `docs/archive/`
- Updated documentation examples to use current patterns
- Verified all 175 tests passing with clean architecture

---

## 🚀 Missing Core Features

### Character Sheet Generation
- [ ] **PDF Character Sheet Export** - Generate official D&D 2024 character sheets
- [ ] **Modular Card System** - Individual cards for different character aspects
  - [ ] Character Info Card (stats, abilities, proficiencies)
  - [ ] Weapon Cards (individual weapon stats and properties)
  - [ ] Armor Cards (AC, properties, special effects)
  - [ ] Spell Cards (spell details, components, effects)
  - [ ] Feature Cards (class features, traits, abilities)
  - [ ] Equipment Cards (non-combat items and tools)

### Equipment System  
- [x] **Weapon Database** - Complete D&D 2024 weapon list with properties ✅
- [x] **Armor Database** - All armor types with AC calculations ✅
- [x] **Equipment Database** - Adventuring gear, tools, and miscellaneous items ✅
- [x] **Equipment Selection Interface** - Starting equipment from class/background ✅
- [ ] **Equipment Management** - Add/remove/manage equipment during play
- [x] **Encumbrance Calculation** - Weight and carrying capacity tracking (basic) ✅

### Combat Calculations
- [x] **Attack Roll Calculations** - Weapon attacks with all bonuses ✅
- [x] **Damage Roll Calculations** - Weapon damage with ability modifiers ✅
- [x] **Armor Class Calculation** - Base AC + armor + shield + bonuses ✅
- [x] **Initiative Calculation** - Dexterity + bonuses ✅
- [x] **Combat Actions** - Available actions, bonus actions, reactions (partial) ✅

### Spell System Enhancement
- [ ] **Complete Spell Database** - All D&D 2024 spells with full details
- [ ] **Spell Slot Management** - Track used/available spell slots
- [ ] **Spell Preparation** - Manage prepared vs known spells
- [ ] **Ritual Spells** - Special handling for ritual casting
- [ ] **Spell Attack/Save DC Calculation** - Automatic calculation based on class

### Character Progression
- [ ] **Level Up System** - Guided level progression
- [ ] **Multiclassing Support** - Prerequisites and progression rules
- [ ] **Experience Point Tracking** - XP calculation and level thresholds
- [ ] **Milestone Leveling** - Alternative progression system

---

## 📊 Data Validation Matrix

### Species & Subspecies Data Validation

| Species | Variants | Traits Validated | Effects Implemented | Status |
|---------|----------|------------------|-------------------|---------|
| **Aasimar** | - | ❌ | ❌ | Missing |
| **Dragonborn** | Black, Blue, Brass, Bronze, Copper, Gold, Green, Red, Silver, White | ❌ | ❌ | Missing |
| **Dwarf** | - | ✅ Complete | ✅ Complete | Complete |
| **Elf** | High, Wood, Drow | ✅ Complete | ✅ Complete | Complete |
| **Gnome** | Forest, Rock | ❌ | ❌ | Missing |
| **Goliath** | - | ❌ | ❌ | Missing |
| **Halfling** | - | ❌ | ❌ | Missing |
| **Human** | - | ❌ | ❌ | Missing |
| **Orc** | - | ❌ | ❌ | Missing |
| **Tiefling** | Abyssal, Chthonic, Infernal | ✅ Complete | ✅ Complete | Complete |

**Priority Actions:**
- [ ] Complete all missing species data files
- [ ] Validate all species traits follow D&D 2024 rules
- [ ] Implement effects system for all species features
- [ ] Add darkvision, resistances, and special abilities
- [ ] Verify speed modifications and size categories

### Class & Subclass Data Validation

| Class | Subclasses Available | Features Validated | Effects Implemented | Spell Lists Complete |
|-------|---------------------|-------------------|-------------------|-------------------|
| **Barbarian** | Path of the Berserker, Path of the Wild Heart, Path of the World Tree, Path of the Zealot | ❌ | ❌ | N/A |
| **Bard** | College of Dance, College of Glamour, College of Lore, College of Valor | ❌ | ❌ | ⚠️ Partial |
| **Cleric** | Life, Light, Trickery, War Domain | ❌ | ❌ | ⚠️ Partial |
| **Druid** | Circle of the Land, Circle of the Moon, Circle of the Sea, Circle of the Stars | ❌ | ❌ | ⚠️ Partial |
| **Fighter** | Battle Master, Champion, Eldritch Knight, Psi Warrior | ❌ | ❌ | ❌ |
| **Monk** | Way of the Four Elements, Way of Mercy, Way of the Open Hand, Way of Shadow | ❌ | ❌ | ❌ |
| **Paladin** | Oath of Devotion, Oath of the Ancients, Oath of Vengeance, Oath of Glory | ❌ | ❌ | ⚠️ Partial |
| **Ranger** | Beast Master, Fey Wanderer, Gloom Stalker, Hunter | ❌ | ❌ | ⚠️ Partial |
| **Rogue** | Arcane Trickster, Assassin, Soulknife, Thief | ❌ | ❌ | ❌ |
| **Sorcerer** | Aberrant Mind, Clockwork Soul, Draconic Bloodline, Storm Sorcery | ❌ | ❌ | ⚠️ Partial |
| **Warlock** | Archfey, Celestial, Fiend, Great Old One | ❌ | ❌ | ⚠️ Partial |
| **Wizard** | Abjurer, Diviner, Evoker, Illusionist | ❌ | ❌ | ⚠️ Partial |

**Priority Actions:**
- [ ] Complete all missing subclass data files
- [ ] Validate all class features follow D&D 2024 progression
- [ ] Implement Choice Reference System for all class choices
- [ ] Complete spell lists for all spellcasting classes
- [ ] Add hit point calculation and proficiency bonuses

### Background Data Validation

| Background | Ability Score Increases | Skill Proficiencies | Features | Feat Options | Status |
|------------|------------------------|-------------------|----------|-------------|---------|
| **Acolyte** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Artisan** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Charlatan** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Criminal** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Entertainer** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Farmer** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Guard** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Guide** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Hermit** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Merchant** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Noble** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Sage** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Sailor** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Scribe** | ❌ | ❌ | ❌ | ❌ | Missing |
| **Soldier** | ✅ | ✅ | ✅ | ❌ | Partial |
| **Wayfarer** | ❌ | ❌ | ❌ | ❌ | Missing |

**Priority Actions:**
- [ ] Add all missing background data files
- [ ] Implement feat options for all backgrounds
- [ ] Validate background features follow D&D 2024 rules
- [ ] Add tool proficiencies and languages
- [ ] Implement background-specific equipment

### Feat Data Validation

| Feat Category | Total Count | Data Available | Effects Implemented | Choice System | Status |
|---------------|-------------|----------------|-------------------|---------------|---------|
| **Origin Feats** | 10 | ⚠️ Partial (8/10) | ❌ | ❌ | Partial |
| **General Feats** | 44 | ❌ (0/44) | ❌ | ❌ | Missing |
| **Fighting Style Feats** | 10 | ⚠️ Partial (4/10) | ❌ | ❌ | Partial |

**Origin Feats (Available at Character Creation)**
- ✅ Alert, ✅ Crafter, ✅ Healer, ❌ Lucky, ✅ Magic Initiate, ✅ Musician, ✅ Savage Attacker, ✅ Skilled, ❌ Tavern Brawler, ❌ Tough

**General Feats (Available from Level 4+)**
- ❌ All 44 feats missing: Ability Score Improvement, Actor, Athlete, Charger, Chef, Crossbow Expert, Crusher, Defensive Duelist, Dual Wielder, Durable, Elemental Adept, Fey Touched, Grappler, Great Weapon Master, Harper Teamwork, Heavily Armored, Heavy Armor Master, Inspiring Leader, Keen Mind, Lightly Armored, Mage Slayer, Martial Weapon Training, Medium Armor Master, Moderately Armored, Mounted Combatant, Observant, Piercer, Poisoner, Polearm Master, Resilient, Ritual Caster, Sentinel, Shadow Touched, Sharpshooter, Shield Master, Skill Expert, Skulker, Slasher, Speedy, Spell Sniper, Telekinetic, Telepathic, War Caster, Weapon Master

**Fighting Style Feats (Class Features & Feat Options)**
- ✅ Archery, ❌ Blind Fighting, ✅ Defense, ✅ Dueling, ❌ Great Weapon Fighting, ❌ Interception, ❌ Protection, ❌ Thrown Weapon Fighting, ❌ Two Weapon Fighting, ❌ Unarmed Fighting

**Priority Actions:**
- [ ] Complete all missing Origin feat data files (Lucky, Tavern Brawler, Tough)
- [ ] Add all 44 General feat data files
- [ ] Complete missing Fighting Style feats (6 remaining)
- [ ] Implement effects system for all feat benefits
- [ ] Add prerequisite validation for General feats
- [ ] Implement feat choices using Choice Reference System
- [ ] Add level restrictions and scaling effects

---

## 🔧 System Architecture Improvements

### Code Quality & Maintainability
- [ ] **Unit Testing** - Comprehensive test coverage for all modules
- [x] **Integration Testing** - End-to-end character recreation tests ✅ *COMPLETED*
  - [x] Level 3 Dwarf Cleric (Light Domain) comprehensive verification
  - [x] Level 3 Wood Elf Fighter (Champion) comprehensive verification
  - [x] HP calculation testing using HPCalculator.calculate_total_hp()
  - [x] Ability modifier testing using CharacterCalculator.calculate_ability_scores()
  - [x] Skill modifier testing using CharacterCalculator.calculate_skills()
  - [x] Effects system verification (species, class, subclass features)
  - [x] Spell system verification (domain spells, lineage cantrips)
- [ ] **Error Handling** - Graceful handling of malformed data
- [ ] **Input Validation** - Validate all user inputs and data files
- [ ] **Performance Optimization** - Cache frequently accessed data

### User Experience
- [ ] **Mobile Responsiveness** - Optimize for mobile devices
- [ ] **Accessibility** - Screen reader support and keyboard navigation
- [ ] **Character Import/Export** - Save and load character files
- [ ] **Character Templates** - Pre-built character archetypes
- [ ] **Tutorial Mode** - Guided character creation for new users

### Development Tools
- [ ] **Data Validation Scripts** - Automated checking of data file integrity
- [ ] **Content Migration Tools** - Scripts to convert between data formats
- [ ] **Development Documentation** - API documentation and contribution guides
- [ ] **Automated Testing CI/CD** - Continuous integration and deployment

---

## 📋 Immediate Priorities (Next Sprint)

1. **Complete Species Data** - Focus on Human, Halfling, and Dragonborn (Dwarf and Elf now complete)
2. **Unit Testing Coverage** - Add unit tests for individual modules (CharacterBuilder, HPCalculator, etc.)
3. **Equipment Foundation** - Basic weapon and armor data structures
4. **Data Validation Tools** - Scripts to verify data file compliance
5. **More Integration Tests** - Add tests for different class/species combinations

---

## 🎯 Long-term Goals

1. **Official D&D 2024 Compliance** - 100% accurate implementation of all rules
2. **Complete Content Coverage** - All species, classes, subclasses, backgrounds, and feats
3. **Professional Character Sheets** - High-quality PDF generation
4. **Campaign Integration** - Multi-character party management
5. **Digital Integration** - API compatibility with popular D&D tools

---

## 📈 Recent Accomplishments (February 5, 2026)

### ✅ Integration Testing Framework
- **Character Recreation Tests** - Comprehensive tests that recreate characters from `choices_made` dictionaries
- **Effects System Verification** - Tests validate all species, class, and subclass effects are properly applied
- **Calculator Integration** - Tests use actual calculation modules instead of duplicating logic
- **Realistic Test Cases** - Level 3 Dwarf Cleric (Light Domain) and Wood Elf Fighter (Champion)

### ✅ Spell System Fixes
- **Lineage Cantrip UI Display** - Fixed elf lineage cantrips not appearing in web interface
- **Spell Source Attribution** - Corrected Faerie Fire showing proper "Drow Spells" source instead of "Always Prepared"
- **Effects Export** - CharacterBuilder now exports effects and choices_made for web app integration

### ✅ Species Implementation  
- **Complete Dwarf Species** - Dwarven Resilience, Toughness (+1 HP/level), Poison Resistance, Darkvision
- **Complete Elf Lineage System** - High Elf, Wood Elf, and Drow lineages fully implemented
- **Complete Tiefling Lineage System** - Abyssal, Chthonic, and Infernal lineages with proper D&D 2024 compliance
- **Cantrip Effects** - Prestidigitation (High Elf), Druidcraft (Wood Elf), Dancing Lights (Drow), Thaumaturgy (All Tieflings)
- **Lineage Cantrips** - Poison Spray (Abyssal), Chill Touch (Chthonic), Fire Bolt (Infernal)
- **Damage Resistances** - Poison (Dwarf + Abyssal), Fire (Infernal), Necrotic (Chthonic)
- **Speed Bonuses** - Wood Elf 35ft speed correctly implemented
- **Weapon Proficiencies** - Elf weapon training properly applied
- **Spell Progression** - All Tiefling variants get level-based spells (L3 and L5 always prepared)

### ✅ Calculator Architecture
- **Proper Module Usage** - Tests now use HPCalculator, CharacterCalculator methods correctly
- **DRY Principle** - Eliminated duplicated calculation logic in tests
- **Maintainability** - Changes to calculation logic only need to happen in one place

---

## Bugs / Corrections / Enhancements:

- Features and Traits (class and subclass) should display level at which they became available - Nice to have
- Features like "Subclass Feature: Gain a feature from your Martial Archetype subclass" should be removed from data files, potentially creating a cleanup script for data files
- Spellcasting feature should have a more detailed template (spell slots, number of prepared spells, etc.)
- Subclass spells (like Life Domain) should appear as Always Prepared

## Fighter

- Fighting Style: Archery needs to add bonus to ranged attacks

*Last Updated: February 5, 2026*
*Status Legend: ✅ Complete | ⚠️ Partial | ❌ Missing*