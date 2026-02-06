"""
Character sheet calculation module for D&D 2024.
Handles all derived value calculations for the character sheet.
"""
from typing import Dict, Any, List, Optional, Tuple
import math
from pathlib import Path
import json


class CharacterCalculator:
    """Main calculator for all character sheet values."""
    
    def __init__(self, data_dir: str = "data/equipment"):
        """
        Initialize the calculator.
        
        Args:
            data_dir: Path to equipment data directory
        """
        self.data_dir = Path(data_dir)
        self._armor_data = None
        
        # D&D 2024 skill to ability mappings
        self.skill_abilities = {
            'acrobatics': 'dexterity',
            'animal_handling': 'wisdom',
            'arcana': 'intelligence',
            'athletics': 'strength',
            'deception': 'charisma',
            'history': 'intelligence',
            'insight': 'wisdom',
            'intimidation': 'charisma',
            'investigation': 'intelligence',
            'medicine': 'wisdom',
            'nature': 'intelligence',
            'perception': 'wisdom',
            'performance': 'charisma',
            'persuasion': 'charisma',
            'religion': 'intelligence',
            'sleight_of_hand': 'dexterity',
            'stealth': 'dexterity',
            'survival': 'wisdom'
        }
    
    def calculate_ability_modifier(self, score: int) -> int:
        """Calculate ability modifier from score."""
        return math.floor((score - 10) / 2)
    
    def calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        if level <= 4:
            return 2
        elif level <= 8:
            return 3
        elif level <= 12:
            return 4
        elif level <= 16:
            return 5
        else:
            return 6
    
    def calculate_ability_scores(self, raw_scores: Dict[str, int], level: int, 
                               saving_throw_proficiencies: List[str]) -> Dict[str, Dict[str, Any]]:
        """Calculate complete ability score data including modifiers and saves."""
        proficiency_bonus = self.calculate_proficiency_bonus(level)
        ability_scores = {}
        
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in abilities:
            # Convert from title case to lowercase for consistency
            raw_ability = ability.title()
            score = raw_scores.get(raw_ability, 10)
            modifier = self.calculate_ability_modifier(score)
            
            # Calculate saving throw
            save_proficient = ability in saving_throw_proficiencies
            saving_throw = modifier + (proficiency_bonus if save_proficient else 0)
            
            ability_scores[ability] = {
                'score': score,
                'modifier': modifier,
                'saving_throw': saving_throw,
                'saving_throw_proficient': save_proficient
            }
        
        return ability_scores
    
    def calculate_skills(self, ability_scores: Dict[str, Dict[str, Any]], 
                        skill_proficiencies: List[str], skill_expertise: List[str],
                        proficiency_bonus: int) -> Dict[str, Dict[str, Any]]:
        """Calculate complete skill data with bonuses."""
        skills = {}
        
        for skill, ability in self.skill_abilities.items():
            # Convert skill names from various formats
            skill_name_variants = [
                skill.replace('_', ' ').title(),  # "animal_handling" -> "Animal Handling"
                skill.replace('_', '').lower(),   # "animal_handling" -> "animalhandling" 
                skill.title().replace('_', ''),   # "animal_handling" -> "AnimalHandling"
                skill.lower()                     # "animal_handling" -> "animal_handling"
            ]
            
            # Check if character has proficiency in this skill
            proficient = any(variant in skill_proficiencies for variant in skill_name_variants)
            expertise = any(variant in skill_expertise for variant in skill_name_variants)
            
            # Calculate bonus
            ability_modifier = ability_scores[ability]['modifier']
            prof_bonus = 0
            if expertise:
                prof_bonus = proficiency_bonus * 2
            elif proficient:
                prof_bonus = proficiency_bonus
            
            bonus = ability_modifier + prof_bonus
            
            skills[skill] = {
                'proficient': proficient,
                'expertise': expertise,
                'bonus': bonus
            }
        
        return skills
    
    def calculate_combat_stats(self, ability_scores: Dict[str, Dict[str, Any]], 
                             equipment: Dict[str, Any], level: int, 
                             hit_points_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate combat statistics."""
        # Basic combat stats
        dex_modifier = ability_scores['dexterity']['modifier']
        wis_modifier = ability_scores['wisdom']['modifier']
        
        # Calculate proficiency bonus for level
        proficiency_bonus = self.calculate_proficiency_bonus(level)
        
        # Calculate AC (basic 10 + dex, will be enhanced with armor)
        base_ac = 10 + dex_modifier
        armor_ac = self._calculate_armor_class(base_ac, equipment, ability_scores)
        
        # Calculate initiative
        initiative = dex_modifier
        
        # Speed (default 30, may be modified by species/equipment)
        speed = 30  # Will be updated from species data
        
        # Hit points
        max_hp = hit_points_data.get('max_hp', level * 6)  # Fallback calculation
        
        # Hit dice based on class
        class_name = hit_points_data.get('class', 'Fighter')
        hit_dice_type = self._get_class_hit_dice(class_name)
        
        # Calculate passive perception (10 + WIS modifier, will add proficiency if they have it below)
        # For now, simplified - pass skill proficiencies in from character data if we want accurate calculation
        passive_perception = 10 + wis_modifier
        
        return {
            'armor_class': armor_ac,
            'initiative': initiative,
            'speed': speed,
            'hit_point_maximum': max_hp,
            'current_hit_points': max_hp,
            'temporary_hit_points': 0,
            'hit_dice': {
                'total': f"{level}d{hit_dice_type}",
                'current': level
            },
            'death_saves': {
                'successes': 0,
                'failures': 0
            },
            'passive_perception': passive_perception
        }
    
    def _calculate_armor_class(self, base_ac: int, equipment: Dict[str, Any], 
                              ability_scores: Dict[str, Dict[str, Any]]) -> int:
        """Calculate AC including armor and shields."""
        # For now, return base AC
        # Will be enhanced when equipment system is fully implemented
        armor_list = equipment.get('armor', [])
        
        # Find equipped armor
        equipped_armor = None
        for armor in armor_list:
            if armor.get('equipped', False):
                equipped_armor = armor
                break
        
        if equipped_armor:
            return equipped_armor.get('ac', base_ac)
        
        return base_ac
    
    def _get_class_hit_dice(self, class_name: str) -> int:
        """Get hit dice type for class."""
        class_hit_dice = {
            'Barbarian': 12,
            'Fighter': 10, 'Paladin': 10, 'Ranger': 10,
            'Bard': 8, 'Cleric': 8, 'Druid': 8, 'Monk': 8, 'Rogue': 8, 'Warlock': 8,
            'Sorcerer': 6, 'Wizard': 6
        }
        return class_hit_dice.get(class_name, 8)
    
    def calculate_proficiencies(self, class_data: Dict[str, Any], 
                               species_data: Dict[str, Any], 
                               background_data: Dict[str, Any],
                               level: int) -> Dict[str, Any]:
        """Calculate and organize all proficiencies."""
        languages = set(['Common'])  # Everyone gets Common
        armor_profs = set()
        weapon_profs = set()
        tool_profs = set()
        
        # Add from species
        languages.update(species_data.get('languages', []))
        weapon_profs.update(species_data.get('weapon_proficiencies', []))
        tool_profs.update(species_data.get('tool_proficiencies', []))
        
        # Add from class
        armor_profs.update(class_data.get('armor_proficiencies', []))
        weapon_profs.update(class_data.get('weapon_proficiencies', []))
        tool_profs.update(class_data.get('tool_proficiencies', []))
        
        # Add from background
        tool_profs.update(background_data.get('tool_proficiencies', []))
        
        return {
            'languages': sorted(list(languages)),
            'armor': sorted(list(armor_profs)),
            'weapons': sorted(list(weapon_profs)),
            'tools': sorted(list(tool_profs)),
            'proficiency_bonus': self.calculate_proficiency_bonus(level)
        }
    
    # ========== AC OPTIONS SYSTEM (Phase 4) ==========
    
    @property
    def armor_data(self) -> Dict[str, Dict[str, Any]]:
        """Lazy load armor data."""
        if self._armor_data is None:
            armor_file = self.data_dir / 'armor.json'
            if armor_file.exists():
                try:
                    with open(armor_file, 'r') as f:
                        self._armor_data = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load armor.json: {e}")
                    self._armor_data = {}
            else:
                self._armor_data = {}
        return self._armor_data
    
    def calculate_all_ac_options(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate ALL possible AC combinations from inventory.
        
        This is the core of the AC Options System - instead of tracking a single
        "equipped" armor, we calculate all valid combinations and let the player
        see all their options.
        
        Args:
            character: Complete character data dict
            
        Returns:
            List of AC options sorted by AC value (highest first), each containing:
            - ac: Total AC value
            - armor: Armor name (or None for unarmored)
            - shield: Shield name (or None)
            - formula: Human-readable calculation
            - notes: List of warnings/notes
            - valid: Whether this option is valid (proficient)
            - is_unarmored: Whether this is an unarmored option
        """
        options = []
        
        # Get character data with safe defaults
        ability_scores = character.get('ability_scores', {})
        
        # Safely get DEX modifier
        dex_data = ability_scores.get('dexterity', {})
        if isinstance(dex_data, dict):
            dex_modifier = dex_data.get('modifier', 0)
        elif isinstance(dex_data, int):
            # Sometimes it's stored as a direct score
            dex_modifier = (dex_data - 10) // 2
        else:
            # Absolute fallback
            dex_modifier = 0
        
        # Get proficiencies with safe defaults
        proficiencies = character.get('proficiencies', {})
        armor_profs = proficiencies.get('armor', [])
        
        # Get all armor and shields from inventory
        equipment = character.get('equipment', {})
        all_armor = equipment.get('armor', [])
        all_shields = equipment.get('shields', [])
        
        # Debug: Log what we found
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"AC Options Calculator - Equipment structure: {list(equipment.keys())}")
        logger.debug(f"AC Options Calculator - Found {len(all_armor)} armor pieces: {[a.get('name') for a in all_armor]}")
        logger.debug(f"AC Options Calculator - Found {len(all_shields)} shields: {[s.get('name') for s in all_shields]}")
        logger.debug(f"AC Options Calculator - Armor proficiencies: {armor_profs}")
        
        # Calculate armor options (with and without shield)
        for armor in all_armor:
            armor_name = armor.get('name')
            armor_props = armor.get('properties', {})
            
            # Skip armor without a name
            if not armor_name:
                logger.debug(f"AC Options Calculator - Skipping armor without name: {armor}")
                continue
            
            # Load full armor data if properties are missing
            if not armor_props and armor_name:
                armor_props = self.armor_data.get(armor_name, {})
                logger.debug(f"AC Options Calculator - Loaded {armor_name} properties from armor.json: {armor_props}")
            
            # Skip if we still don't have armor properties
            if not armor_props or not armor_props.get('category'):
                logger.warning(f"AC Options Calculator - No properties found for armor: {armor_name}")
                continue
            
            # Check proficiency
            is_proficient = self._has_armor_proficiency(armor_props, armor_profs)
            logger.debug(f"AC Options Calculator - {armor_name} proficiency: {is_proficient}")
            
            # Calculate AC for this armor
            ac_without_shield = self._calculate_armor_ac(armor_props, dex_modifier, character)
            
            # Option 1: Armor without shield
            options.append({
                'ac': ac_without_shield,
                'armor': armor_name,
                'shield': None,
                'formula': self._get_ac_formula(armor_props, dex_modifier, None, character),
                'notes': self._get_armor_notes(armor_props, character, is_proficient),
                'valid': is_proficient,
                'is_unarmored': False
            })
            
            # Option 2: Armor with each shield
            for shield in all_shields:
                shield_name = shield.get('name')
                shield_props = shield.get('properties', {})
                
                # Load full shield data if properties are missing
                if not shield_props and shield_name:
                    shield_props = self.armor_data.get(shield_name, {})
                
                # Check shield proficiency
                shield_proficient = self._has_armor_proficiency(shield_props, armor_profs)
                
                if shield_proficient:
                    shield_bonus = shield_props.get('ac_bonus', 0)
                    ac_with_shield = ac_without_shield + shield_bonus
                    
                    options.append({
                        'ac': ac_with_shield,
                        'armor': armor_name,
                        'shield': shield_name,
                        'formula': self._get_ac_formula(armor_props, dex_modifier, shield_props, character),
                        'notes': self._get_armor_notes(armor_props, character, is_proficient),
                        'valid': is_proficient and shield_proficient,
                        'is_unarmored': False
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
            shield_name = shield.get('name')
            shield_props = shield.get('properties', {})
            
            # Load full shield data if properties are missing
            if not shield_props and shield_name:
                shield_props = self.armor_data.get(shield_name, {})
            
            # Check shield proficiency
            shield_proficient = self._has_armor_proficiency(shield_props, armor_profs)
            
            if shield_proficient:
                shield_bonus = shield_props.get('ac_bonus', 0)
                options.append({
                    'ac': unarmored_ac + shield_bonus,
                    'armor': None,
                    'shield': shield_name,
                    'formula': f"{self._get_unarmored_formula(character)} + {shield_bonus} (shield)",
                    'notes': [],
                    'valid': True,
                    'is_unarmored': True
                })
        
        # Sort by AC (highest first), then by validity, then by simplicity
        options.sort(key=lambda x: (-x['ac'], not x['valid'], x['armor'] is None))
        
        # Safety check: ensure we always have at least one valid option
        if not options:
            # No options found - create a default unarmored option
            unarmored_ac = max(10 + dex_modifier, 5)
            options.append({
                'ac': unarmored_ac,
                'armor': None,
                'shield': None,
                'formula': f"10 + {dex_modifier} (DEX)",
                'notes': [],
                'valid': True,
                'is_unarmored': True
            })
        
        # Verify no AC is impossibly low (below 5)
        for option in options:
            if option['ac'] < 5:
                option['ac'] = 5
                option['notes'].append('⚠️ AC adjusted to minimum value (5)')
        
        return options
    
    def _calculate_armor_ac(self, armor_props: Dict[str, Any], dex_modifier: int, 
                           character: Dict[str, Any]) -> int:
        """Calculate AC for a specific armor."""
        category = armor_props.get('category', '')
        base_ac = armor_props.get('ac_base', 10)
        
        if 'Light' in category:
            return max(base_ac + dex_modifier, 5)  # Minimum 5 AC
        elif 'Medium' in category:
            return max(base_ac + min(dex_modifier, 2), 5)  # Minimum 5 AC
        else:  # Heavy Armor
            return max(base_ac, 5)  # Minimum 5 AC
    
    def _calculate_unarmored_ac(self, character: Dict[str, Any]) -> int:
        """
        Calculate unarmored AC (may be overridden by class features).
        
        Handles:
        - Default: 10 + DEX
        - Barbarian Unarmored Defense: 10 + DEX + CON
        - Monk Unarmored Defense: 10 + DEX + WIS
        """
        ability_scores = character.get('ability_scores', {})
        
        # Safely get DEX modifier with multiple fallback attempts
        dex_data = ability_scores.get('dexterity', {})
        if isinstance(dex_data, dict):
            dex_modifier = dex_data.get('modifier', 0)
        else:
            # Fallback: calculate from score if we got a score instead
            dex_score = dex_data if isinstance(dex_data, int) else 10
            dex_modifier = (dex_score - 10) // 2
        
        # Check for special unarmored defense features
        features = character.get('features', {})
        
        # Barbarian: 10 + DEX + CON
        if 'Unarmored Defense' in features:
            feature_desc = features['Unarmored Defense']
            if 'Constitution' in feature_desc:
                con_data = ability_scores.get('constitution', {})
                con_modifier = con_data.get('modifier', 0) if isinstance(con_data, dict) else 0
                return max(10 + dex_modifier + con_modifier, 5)  # Never less than 5
            # Monk: 10 + DEX + WIS
            elif 'Wisdom' in feature_desc:
                wis_data = ability_scores.get('wisdom', {})
                wis_modifier = wis_data.get('modifier', 0) if isinstance(wis_data, dict) else 0
                return max(10 + dex_modifier + wis_modifier, 5)  # Never less than 5
        
        # Default: 10 + DEX (minimum 5 AC, even with very low DEX)
        return max(10 + dex_modifier, 5)
    
    def _get_ac_formula(self, armor_props: Dict[str, Any], dex_modifier: int, 
                       shield_props: Optional[Dict[str, Any]], character: Dict[str, Any]) -> str:
        """Generate human-readable AC formula."""
        category = armor_props.get('category', '')
        base_ac = armor_props.get('ac_base', 10)
        
        if 'Light' in category:
            formula = f"{base_ac} (armor) + {dex_modifier} (DEX)"
        elif 'Medium' in category:
            dex_bonus = min(dex_modifier, 2)
            formula = f"{base_ac} (armor) + {dex_bonus} (DEX, max +2)"
        else:  # Heavy Armor
            formula = f"{base_ac} (armor)"
        
        if shield_props:
            shield_bonus = shield_props.get('ac_bonus', 0)
            formula += f" + {shield_bonus} (shield)"
        
        return formula
    
    def _get_unarmored_formula(self, character: Dict[str, Any]) -> str:
        """Get formula for unarmored AC."""
        ability_scores = character.get('ability_scores', {})
        dex_modifier = ability_scores.get('dexterity', {}).get('modifier', 0)
        
        # Check for special unarmored defense
        features = character.get('features', {})
        if 'Unarmored Defense' in features:
            feature_desc = features['Unarmored Defense']
            if 'Constitution' in feature_desc:
                con_modifier = ability_scores.get('constitution', {}).get('modifier', 0)
                return f"10 + {dex_modifier} (DEX) + {con_modifier} (CON)"
            elif 'Wisdom' in feature_desc:
                wis_modifier = ability_scores.get('wisdom', {}).get('modifier', 0)
                return f"10 + {dex_modifier} (DEX) + {wis_modifier} (WIS)"
        
        return f"10 + {dex_modifier} (DEX)"
    
    def _get_armor_notes(self, armor_props: Dict[str, Any], character: Dict[str, Any], 
                        is_proficient: bool) -> List[str]:
        """Get warnings/notes about armor."""
        notes = []
        
        # Proficiency warning
        if not is_proficient:
            notes.append('⚠️ Not proficient - disadvantage on attack rolls and ability checks')
        
        # Stealth disadvantage
        if armor_props.get('stealth_disadvantage', False):
            notes.append('⚠️ Disadvantage on Stealth checks')
        
        # Strength requirement
        str_req = armor_props.get('strength_requirement')
        if str_req:
            ability_scores = character.get('ability_scores', {})
            str_score = ability_scores.get('strength', {}).get('score', 10)
            if str_score < str_req:
                notes.append(f'⚠️ Requires STR {str_req} (you have {str_score}) - speed reduced by 10 ft')
        
        return notes
    
    def _has_armor_proficiency(self, armor_props: Dict[str, Any], 
                              armor_proficiencies: List[str]) -> bool:
        """Check if character has proficiency for armor."""
        prof_required = armor_props.get('proficiency_required', '')
        
        # Check if any of the character's proficiencies match
        for prof in armor_proficiencies:
            if prof.lower() in prof_required.lower():
                return True
        
        return False
    
    # ========== WEAPON ATTACK CALCULATIONS ==========
    
    def calculate_weapon_attacks(self, character: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate attack stats for all weapons in inventory.
        
        Args:
            character: Complete character data dict
            
        Returns:
            List of weapon attack data with bonuses, damage, etc.
        """
        attacks = []
        equipment = character.get('equipment', {})
        all_weapons = equipment.get('weapons', [])
        
        ability_scores = character.get('ability_scores', {})
        proficiencies = character.get('proficiencies', {})
        weapon_profs = proficiencies.get('weapons', [])
        proficiency_bonus = proficiencies.get('proficiency_bonus', 2)
        
        for weapon in all_weapons:
            weapon_name = weapon.get('name')
            weapon_props = weapon.get('properties', {})
            
            # Determine ability modifier
            category = weapon_props.get('category', '')
            properties = weapon_props.get('properties', [])
            
            if 'Finesse' in properties:
                str_mod = ability_scores.get('strength', {}).get('modifier', 0)
                dex_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
                ability_mod = max(str_mod, dex_mod)
                ability_name = f'STR/DEX ({"STR" if str_mod >= dex_mod else "DEX"})'
            elif 'Ranged' in category:
                ability_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
                ability_name = 'DEX'
            else:
                ability_mod = ability_scores.get('strength', {}).get('modifier', 0)
                ability_name = 'STR'
            
            # Check proficiency
            is_proficient = self._has_weapon_proficiency(weapon_props, weapon_profs)
            prof_bonus = proficiency_bonus if is_proficient else 0
            
            # Calculate attack bonus
            attack_bonus = ability_mod + prof_bonus
            
            # Calculate damage
            damage_dice = weapon_props.get('damage', '1d4')
            damage_bonus = ability_mod
            damage_type = weapon_props.get('damage_type', 'Bludgeoning')
            
            # Handle versatile weapons
            versatile_damage = None
            for prop in properties:
                if isinstance(prop, str) and prop.startswith('Versatile'):
                    # Extract damage from "Versatile (1d10)"
                    try:
                        versatile_damage = prop.split('(')[1].split(')')[0]
                    except IndexError:
                        pass
            
            # Calculate average damage and crit damage
            avg_damage = self._calculate_average_damage(damage_dice, damage_bonus)
            avg_crit = self._calculate_average_damage(damage_dice, damage_bonus, is_crit=True)
            
            # Calculate versatile average damage if applicable
            versatile_avg_damage = None
            versatile_avg_crit = None
            if versatile_damage:
                versatile_avg_damage = self._calculate_average_damage(versatile_damage, damage_bonus)
                versatile_avg_crit = self._calculate_average_damage(versatile_damage, damage_bonus, is_crit=True)
            
            # Get weapon mastery if available
            mastery = weapon_props.get('mastery')
            
            attacks.append({
                'name': weapon_name,
                'attack_bonus': f"+{attack_bonus}" if attack_bonus >= 0 else str(attack_bonus),
                'damage': f"{damage_dice} + {damage_bonus}",
                'avg_damage': avg_damage,
                'avg_crit': avg_crit,
                'versatile_damage': f"{versatile_damage} + {damage_bonus}" if versatile_damage else None,
                'versatile_avg_damage': versatile_avg_damage,
                'versatile_avg_crit': versatile_avg_crit,
                'damage_type': damage_type,
                'properties': properties,
                'ability': ability_name,
                'proficient': is_proficient,
                'mastery': mastery,
                'is_light': 'Light' in properties
            })
        
        # Check if character has 2+ light weapons for two-weapon fighting
        light_weapons = [w for w in attacks if w.get('is_light')]
        has_two_weapon_fighting = len(light_weapons) >= 2
        
        # Add offhand attack info to light weapons if two-weapon fighting is possible
        if has_two_weapon_fighting:
            for attack in attacks:
                if attack.get('is_light'):
                    # Offhand attack: same attack bonus, but damage is dice only (no ability mod unless negative)
                    damage_dice = weapon_props.get('damage', '1d4')
                    
                    # Find the weapon props again (we need to access the original weapon data)
                    weapon_name = attack['name']
                    weapon_data = next((w for w in all_weapons if w.get('name') == weapon_name), None)
                    if weapon_data:
                        weapon_props_offhand = weapon_data.get('properties', {})
                        damage_dice_offhand = weapon_props_offhand.get('damage', '1d4')
                        
                        # Get ability modifier for this weapon
                        properties_offhand = weapon_props_offhand.get('properties', [])
                        category_offhand = weapon_props_offhand.get('category', '')
                        
                        if 'Finesse' in properties_offhand:
                            str_mod = ability_scores.get('strength', {}).get('modifier', 0)
                            dex_mod = ability_scores.get('dexterity', {}).get('modifier', 0)
                            ability_mod_offhand = max(str_mod, dex_mod)
                        elif 'Ranged' in category_offhand:
                            ability_mod_offhand = ability_scores.get('dexterity', {}).get('modifier', 0)
                        else:
                            ability_mod_offhand = ability_scores.get('strength', {}).get('modifier', 0)
                        
                        # Offhand damage: dice only, or dice + mod if mod is negative
                        offhand_damage_bonus = ability_mod_offhand if ability_mod_offhand < 0 else 0
                        offhand_avg_damage = self._calculate_average_damage(damage_dice_offhand, offhand_damage_bonus)
                        offhand_avg_crit = self._calculate_average_damage(damage_dice_offhand, offhand_damage_bonus, is_crit=True)
                        
                        attack['offhand_damage'] = f"{damage_dice_offhand}" + (f" + {offhand_damage_bonus}" if offhand_damage_bonus != 0 else "")
                        attack['offhand_avg_damage'] = offhand_avg_damage
                        attack['offhand_avg_crit'] = offhand_avg_crit
        
        return attacks
    
    def _has_weapon_proficiency(self, weapon_props: Dict[str, Any], 
                               weapon_proficiencies: List[str]) -> bool:
        """Check if character has proficiency for weapon."""
        # Check the proficiency_required field (e.g., "Simple weapons", "Martial weapons")
        prof_required = weapon_props.get('proficiency_required', '')
        weapon_name = weapon_props.get('name', '')
        
        for prof in weapon_proficiencies:
            prof_lower = prof.lower()
            # Check if proficiency matches the required proficiency
            if (prof_lower == prof_required.lower() or
                prof_lower == weapon_name.lower() or
                prof_lower == 'all weapons'):
                return True
        
        return False
    
    def _calculate_average_damage(self, dice_expr: str, bonus: int, is_crit: bool = False) -> float:
        """Calculate average damage from a dice expression.
        
        Args:
            dice_expr: Dice expression like "1d6", "2d8", etc.
            bonus: Damage bonus to add
            is_crit: If True, roll dice twice (critical hit)
            
        Returns:
            Average damage as a float
        """
        try:
            # Parse dice expression (e.g., "1d6" or "2d8")
            if 'd' not in dice_expr:
                return float(bonus)  # No dice, just flat damage
            
            parts = dice_expr.lower().split('d')
            num_dice = int(parts[0]) if parts[0] else 1
            die_size = int(parts[1])
            
            # For crits, double the number of dice (not the modifier)
            if is_crit:
                num_dice *= 2
            
            # Average of a die is (1 + die_size) / 2
            avg_per_die = (1 + die_size) / 2.0
            total_avg = (num_dice * avg_per_die) + bonus
            
            return round(total_avg, 1)
        except (ValueError, IndexError):
            # If parsing fails, return bonus only
            return float(bonus)