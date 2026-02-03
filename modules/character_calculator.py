"""
Character sheet calculation module for D&D 2024.
Handles all derived value calculations for the character sheet.
"""
from typing import Dict, Any, List
import math


class CharacterCalculator:
    """Main calculator for all character sheet values."""
    
    def __init__(self):
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
            }
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