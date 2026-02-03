"""
Character sheet data converter for D&D 2024.
Converts internal character data to comprehensive character sheet format.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from .character_calculator import CharacterCalculator
from .hp_calculator import HPCalculator


class CharacterSheetConverter:
    """Converts character data to comprehensive character sheet format."""
    
    def __init__(self):
        self.calculator = CharacterCalculator()
        self.hp_calculator = HPCalculator()
    
    def convert_to_character_sheet(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert internal character format to comprehensive character sheet format."""
        
        # Extract basic info
        level = character_data.get('level', 1)
        class_name = character_data.get('class', 'Fighter')
        subclass = character_data.get('subclass')
        
        # Build class_level string
        if subclass:
            class_level = f"{class_name} ({subclass}) {level}"
        else:
            class_level = f"{class_name} {level}"
        
        # Calculate proficiency bonus
        proficiency_bonus = self.calculator.calculate_proficiency_bonus(level)
        
        # Convert ability scores
        raw_ability_scores = character_data.get('ability_scores', {})
        saving_throw_profs = self._extract_saving_throw_proficiencies(character_data)
        ability_scores = self.calculator.calculate_ability_scores(
            raw_ability_scores, level, saving_throw_profs
        )
        
        # Convert skills
        skill_proficiencies = character_data.get('skill_proficiencies', [])
        skill_expertise = character_data.get('skill_expertise', [])  # Add if exists
        skills = self.calculator.calculate_skills(
            ability_scores, skill_proficiencies, skill_expertise, proficiency_bonus
        )
        
        # Calculate HP with bonuses
        constitution_score = raw_ability_scores.get('Constitution', 10)
        hp_bonuses = self._extract_hp_bonuses(character_data)
        max_hp = self.hp_calculator.calculate_total_hp(
            class_name, constitution_score, hp_bonuses, level
        )
        
        # Calculate combat stats
        equipment = self._convert_equipment(character_data)
        combat_stats = self.calculator.calculate_combat_stats(
            ability_scores, equipment, level, 
            {'max_hp': max_hp, 'class': class_name}
        )
        
        # Apply species physical attributes
        physical_attrs = character_data.get('physical_attributes', {})
        if 'speed' in physical_attrs:
            combat_stats['speed'] = physical_attrs['speed']
        
        # Convert proficiencies
        class_data = character_data.get('class_data', {})
        species_data = character_data.get('species_data', {})
        background_data = self._get_background_data(character_data)
        
        proficiencies = self.calculator.calculate_proficiencies(
            class_data, species_data, background_data, level
        )
        
        # Use character's actual languages if available
        if 'languages' in character_data:
            proficiencies['languages'] = character_data['languages']
        
        # Build comprehensive character sheet
        character_sheet = {
            "character_info": {
                "character_name": character_data.get('name', 'Unnamed Character'),
                "class_level": class_level,
                "background": character_data.get('background', ''),
                "player_name": character_data.get('player_name', ''),
                "species": character_data.get('species', ''),
                "lineage": character_data.get('lineage'),
                "alignment": character_data.get('alignment', ''),
                "experience_points": self._calculate_xp_for_level(level)
            },
            "ability_scores": ability_scores,
            "skills": skills,
            "combat_stats": combat_stats,
            "proficiencies": proficiencies,
            "attacks_and_spellcasting": self._convert_attacks_spellcasting(character_data),
            "equipment": equipment,
            "features_and_traits": self._convert_features(character_data),
            "spells": self._convert_spells(character_data),
            "physical_characteristics": {
                "age": character_data.get('age'),
                "height": character_data.get('height'),
                "weight": character_data.get('weight'),
                "eyes": character_data.get('eyes'),
                "skin": character_data.get('skin'),
                "hair": character_data.get('hair'),
                "appearance": character_data.get('appearance'),
                "backstory": character_data.get('backstory'),
                "allies_organizations": character_data.get('allies_organizations'),
                "additional_features_traits": character_data.get('additional_features_traits'),
                "treasure": character_data.get('treasure')
            },
            "meta_data": {
                "creation_method": "D&D 2024 Character Creator Web",
                "creation_date": datetime.now().strftime("%Y-%m-%d"),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0",
                "choices_made": character_data.get('choices_made', {})
            }
        }
        
        return character_sheet
    
    def _extract_saving_throw_proficiencies(self, character_data: Dict[str, Any]) -> List[str]:
        """Extract saving throw proficiencies from class data."""
        class_data = character_data.get('class_data', {})
        
        # Try both possible field names for saving throw proficiencies
        saving_throws = (class_data.get('saving_throw_proficiencies', []) or 
                        class_data.get('saving_throws', []))
        
        # Convert to lowercase for consistency with ability score keys
        return [save.lower() for save in saving_throws]
    
    def _extract_hp_bonuses(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract HP bonuses from character features."""
        hp_bonuses = []
        found_dwarven_toughness = False
        
        # Check species traits in species_data (original structure)
        species_data = character_data.get('species_data', {})
        traits = species_data.get('traits', {})
        
        # Look for Dwarven Toughness in original structure
        if 'Dwarven Toughness' in traits:
            hp_bonuses.append({
                "source": "Dwarven Toughness (species_data)",
                "value": 1,
                "scaling": "per_level"
            })
            found_dwarven_toughness = True
        
        # Check features structure for HP bonuses (new structure)
        features = character_data.get('features', {})
        if isinstance(features, dict):
            for category, feature_list in features.items():
                if isinstance(feature_list, list):
                    for feature in feature_list:
                        if isinstance(feature, dict):
                            name = feature.get('name', '')
                            desc = feature.get('description', '').lower()
                            
                            # Check for Dwarven Toughness specifically (avoid duplicates)
                            if (name == 'Dwarven Toughness' or 'dwarven toughness' in desc) and not found_dwarven_toughness:
                                hp_bonuses.append({
                                    "source": f"{name} ({category})",
                                    "value": 1,
                                    "scaling": "per_level"
                                })
                                found_dwarven_toughness = True
                            # Check for other HP bonuses
                            elif ('hit point' in desc or 'hp' in desc) and ('level' in desc or 'per level' in desc):
                                # Try to parse HP bonus amount (basic pattern matching)
                                if '+1' in desc and ('level' in desc or 'per level' in desc):
                                    hp_bonuses.append({
                                        "source": name,
                                        "value": 1,
                                        "scaling": "per_level"
                                    })
        
        return hp_bonuses
    
    def _convert_equipment(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert equipment to detailed format."""
        # For now, return basic structure
        # Will be enhanced when equipment system is implemented
        return {
            "armor": [],
            "weapons": [],
            "other_equipment": [],
            "money": {
                "copper": 0,
                "silver": 0,
                "electrum": 0,
                "gold": character_data.get('gold', 0),
                "platinum": 0
            }
        }
    
    def _get_background_data(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get background data for proficiency calculations."""
        # Return empty dict for now, will be enhanced
        return {}
    
    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate minimum XP for given level."""
        xp_table = {
            1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
            6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
            11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
            16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
        }
        return xp_table.get(level, 0)
    
    def _convert_attacks_spellcasting(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert attacks and spellcasting data."""
        return {
            "attacks": [],  # Will be populated from equipment/features
            "spellcasting": None  # Will be enhanced for spellcasters
        }
    
    def _convert_features(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert features to detailed format."""
        features = character_data.get('features', {})
        
        # Handle both old list format and new dict format
        if isinstance(features, list):
            # Convert old format to new
            return {
                "class": [],
                "species": [],
                "lineage": [],
                "background": [],
                "feats": []
            }
        elif isinstance(features, dict):
            # Ensure all categories exist
            result = {
                "class": features.get('class', []),
                "species": features.get('species', []),
                "lineage": features.get('lineage', []),
                "background": features.get('background', []),
                "feats": features.get('feats', [])
            }
            return result
        
        return {
            "class": [],
            "species": [],
            "lineage": [],
            "background": [],
            "feats": []
        }
    
    def _convert_spells(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert spells data."""
        return {
            "cantrips": [],
            "prepared_spells": []
        }