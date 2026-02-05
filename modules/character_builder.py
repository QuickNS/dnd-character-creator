#!/usr/bin/env python3
"""
Character Builder Module

Stateful character builder that manages the step-by-step character creation process.
This class is independent of Flask/web framework and can be used in:
- Unit tests
- CLI tools
- API endpoints
- Scripts

Usage:
    builder = CharacterBuilder()
    builder.set_species("Elf")
    builder.set_lineage("Wood Elf", spellcasting_ability="Wisdom")
    builder.set_class("Ranger", level=1)
    builder.set_background("Sage")
    builder.set_abilities({"STR": 10, "DEX": 16, "CON": 14, "INT": 12, "WIS": 15, "CHA": 8})
    
    # Export to various formats
    character_json = builder.to_json()
    character_obj = builder.to_character()
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from copy import deepcopy

from .character import Character
from .ability_scores import AbilityScores
from .feature_manager import FeatureManager
from .hp_calculator import HPCalculator
from .variant_manager import VariantManager


class CharacterBuilder:
    """
    Stateful builder for D&D 2024 character creation.
    
    This class manages the step-by-step process of creating a character,
    loading data from JSON files, applying effects, and tracking choices.
    """
    
    # Character creation steps in order
    CREATION_STEPS = [
        'species',
        'lineage',  # Optional - only for species with variants
        'class',
        'subclass',  # Only at appropriate level
        'background',
        'abilities',
        'features',  # Any additional choices (feats, skills, etc.)
        'complete'
    ]
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the character builder.
        
        Args:
            data_dir: Path to data directory. If None, uses default location.
        """
        # Set up data directory
        if data_dir is None:
            current_dir = Path(__file__).parent
            self.data_dir = current_dir.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        # Initialize modular components
        self.ability_scores = AbilityScores()
        self.feature_manager = FeatureManager()
        self.hp_calculator = HPCalculator()
        self.variant_manager = VariantManager()
        
        # Character data storage
        self.character_data = {
            'name': '',
            'alignment': '',
            'species': None,
            'species_data': None,
            'lineage': None,
            'lineage_data': None,
            'class': None,
            'class_data': None,
            'subclass': None,
            'subclass_data': None,
            'background': None,
            'background_data': None,
            'level': 1,
            'abilities': {},
            'features': {
                'class': [],
                'subclass': [],
                'species': [],
                'lineage': [],
                'background': [],
                'feats': []
            },
            'choices_made': {},
            'spells': {
                'cantrips': [],
                'known': [],
                'prepared': [],
                'slots': {}
            },
            'spell_metadata': {},  # Track spell sources and special properties
            'proficiencies': {
                'armor': [],
                'weapons': [],
                'tools': [],
                'skills': [],
                'languages': [],
                'saving_throws': []
            },
            'proficiency_sources': {
                'armor': {},
                'weapons': {},
                'tools': {},
                'skills': {},
                'languages': {},
                'saving_throws': {}
            },
            'speed': 30,
            'darkvision': 0,
            'resistances': [],
            'immunities': [],
            'step': 'species'  # Track current step
        }
        
        # Track applied effects
        self.applied_effects = []
    
    # ==================== Data Loading Methods ====================
    
    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a JSON file and return its contents."""
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {file_path}: {e}")
            return None
    
    def _load_species_data(self, species_name: str) -> Optional[Dict[str, Any]]:
        """Load species data from JSON file."""
        filename = species_name.lower().replace(" ", "_")
        file_path = self.data_dir / "species" / f"{filename}.json"
        return self._load_json_file(file_path)
    
    def _load_lineage_data(self, species_name: str, lineage_name: str) -> Optional[Dict[str, Any]]:
        """Load lineage/variant data from JSON file."""
        filename = lineage_name.lower().replace(" ", "_")
        file_path = self.data_dir / "species_variants" / f"{filename}.json"
        return self._load_json_file(file_path)
    
    def _load_class_data(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Load class data from JSON file."""
        filename = class_name.lower().replace(" ", "_")
        file_path = self.data_dir / "classes" / f"{filename}.json"
        return self._load_json_file(file_path)
    
    def _load_subclass_data(self, class_name: str, subclass_name: str) -> Optional[Dict[str, Any]]:
        """Load subclass data from JSON file."""
        class_folder = class_name.lower().replace(" ", "_")
        filename = subclass_name.lower().replace(" ", "_").replace(":", "-")
        file_path = self.data_dir / "subclasses" / class_folder / f"{filename}.json"
        return self._load_json_file(file_path)
    
    def _load_background_data(self, background_name: str) -> Optional[Dict[str, Any]]:
        """Load background data from JSON file."""
        filename = background_name.lower().replace(" ", "_")
        file_path = self.data_dir / "backgrounds" / f"{filename}.json"
        return self._load_json_file(file_path)
    
    # ==================== Species/Lineage Methods ====================
    
    def set_species(self, species_name: str) -> bool:
        """
        Set the character's species.
        
        Args:
            species_name: Name of the species (e.g., "Elf", "Dwarf")
        
        Returns:
            True if successful, False otherwise
        """
        species_data = self._load_species_data(species_name)
        if not species_data:
            return False
        
        self.character_data['species'] = species_name
        self.character_data['species_data'] = species_data
        
        # Apply species base traits
        self._apply_species_traits(species_data)
        
        # Check if species has variants
        has_variants = species_name in self.variant_manager.species_variants
        if has_variants:
            self.character_data['step'] = 'lineage'
        else:
            self.character_data['step'] = 'class'
        
        return True
    
    def set_lineage(self, lineage_name: str, spellcasting_ability: Optional[str] = None) -> bool:
        """
        Set the character's lineage/variant.
        
        Args:
            lineage_name: Name of the lineage (e.g., "Wood Elf", "High Elf")
            spellcasting_ability: For lineages with spell choices (e.g., "Wisdom")
        
        Returns:
            True if successful, False otherwise
        """
        if not self.character_data['species']:
            return False
        
        lineage_data = self._load_lineage_data(
            self.character_data['species'],
            lineage_name
        )
        if not lineage_data:
            return False
        
        self.character_data['lineage'] = lineage_name
        self.character_data['lineage_data'] = lineage_data
        
        # Store spellcasting ability if provided
        if spellcasting_ability:
            self.character_data['spellcasting_ability'] = spellcasting_ability
        
        # Apply lineage traits and effects
        self._apply_lineage_traits(lineage_data)
        
        self.character_data['step'] = 'class'
        return True
    
    def _apply_species_traits(self, species_data: Dict[str, Any]):
        """Apply base species traits."""
        # Speed
        if 'speed' in species_data:
            self.character_data['speed'] = species_data['speed']
        
        # Darkvision
        if 'darkvision' in species_data:
            self.character_data['darkvision'] = species_data['darkvision']
        
        # Languages
        if 'languages' in species_data:
            self.character_data['proficiencies']['languages'].extend(
                species_data['languages']
            )
        
        # Traits with effects
        traits = species_data.get('traits', {})
        for trait_name, trait_data in traits.items():
            self._apply_trait_effects(trait_name, trait_data, 'species')
    
    def _apply_lineage_traits(self, lineage_data: Dict[str, Any]):
        """Apply lineage/variant traits."""
        # Override speed if lineage specifies it
        if 'speed' in lineage_data:
            self.character_data['speed'] = lineage_data['speed']
            
        # Override darkvision if lineage specifies it
        if 'darkvision' in lineage_data:
            self.character_data['darkvision'] = lineage_data['darkvision']
        
        # Store lineage data for later re-application when level changes
        self.character_data['_lineage_traits'] = lineage_data.get('traits', {})
        
        # Traits with effects
        traits = lineage_data.get('traits', {})
        for trait_name, trait_data in traits.items():
            self._apply_trait_effects(trait_name, trait_data, 'lineage')
    
    def _apply_trait_effects(self, trait_name: str, trait_data: Any, source: str):
        """
        Apply effects from a trait.
        
        Args:
            trait_name: Name of the trait
            trait_data: Trait data (string or dict with effects)
            source: Source of the trait ('species', 'lineage', 'class', etc.)
        """
        # Get description and apply any template substitutions
        description = trait_data if isinstance(trait_data, str) else trait_data.get('description', '') if isinstance(trait_data, dict) else ''
        
        # Apply scaling/template substitutions for class features
        if source == 'class' and isinstance(trait_data, dict) and 'scaling' in trait_data:
            description = self._apply_feature_scaling(description, trait_data['scaling'])
        
        # Skip features that are just choice placeholders
        # 1. Features with choices dict but minimal description
        if isinstance(trait_data, dict) and 'choices' in trait_data:
            if not description or len(description) < 20 or description.lower().startswith('choose'):
                # Still apply effects if present
                effects = trait_data.get('effects', [])
                for effect in effects:
                    self._apply_effect(effect, trait_name, source)
                return
        
        # 2. Simple string features that start with "Choose"
        if isinstance(description, str) and description.lower().startswith('choose'):
            return
        
        # Map source to feature category and get descriptive source name
        category_map = {
            'species': 'species',
            'lineage': 'lineage',
            'class': 'class',
            'subclass': 'subclass',
            'class_choice': 'class'
        }
        category = category_map.get(source, 'class')
        
        # Get descriptive source name
        if source == 'class':
            source_display = self.character_data.get('class', 'Class')
        elif source == 'subclass':
            source_display = f"{self.character_data.get('subclass', 'Subclass')}"
        elif source == 'species':
            source_display = self.character_data.get('species', 'Species')
        elif source == 'lineage':
            source_display = self.character_data.get('lineage', 'Lineage')
        else:
            source_display = source
        
        # Check if this feature has a choice and if a choice was made
        display_name = trait_name
        if isinstance(trait_data, dict) and 'choices' in trait_data:
            # Look up the choice from choices_made
            choice_config = trait_data['choices']
            choice_key = choice_config.get('name', trait_name.lower().replace(' ', '_'))
            
            # Check various possible choice keys (including species_trait_ prefix)
            choice_value = None
            for possible_key in [
                choice_key,
                trait_name,
                trait_name.lower().replace(' ', '_'),
                f'species_trait_{trait_name}',
                f'species_trait_{trait_name.replace(" ", "_")}'
            ]:
                if possible_key in self.character_data['choices_made']:
                    choice_value = self.character_data['choices_made'][possible_key]
                    break
            
            # Append choice to display name
            if choice_value:
                if isinstance(choice_value, list):
                    display_name = f"{trait_name}: {', '.join(choice_value)}"
                else:
                    display_name = f"{trait_name}: {choice_value}"
        
        # For Spellcasting feature, we'll append cantrips later when choices are made
        # Check if cantrips have already been chosen
        if trait_name == 'Spellcasting':
            spellcasting_choices = self.character_data['choices_made'].get('Spellcasting', [])
            if isinstance(spellcasting_choices, list) and spellcasting_choices:
                description += f"\n\nCantrips Known: {', '.join(spellcasting_choices)}"
        
        # Check for grant_spell effects and append spell list to description
        if isinstance(trait_data, dict) and 'effects' in trait_data:
            spells_by_level = {}  # Group spells by their min_level
            current_level = self.character_data.get('level', 1)
            
            for effect in trait_data.get('effects', []):
                if effect.get('type') == 'grant_spell':
                    spell_name = effect.get('spell')
                    min_level = effect.get('min_level', 1)
                    if spell_name:
                        if min_level not in spells_by_level:
                            spells_by_level[min_level] = []
                        spells_by_level[min_level].append(spell_name)
            
            if spells_by_level:
                # Check if spells are granted at multiple levels
                if len(spells_by_level) > 1:
                    # Create an HTML table format for multiple levels
                    description += "\n\n"
                    description += '<table class="table table-sm table-bordered mt-2">\n'
                    description += '<thead><tr><th>Character Level</th><th>Spells</th></tr></thead>\n'
                    description += '<tbody>\n'
                    for level in sorted(spells_by_level.keys()):
                        spells = ', '.join(spells_by_level[level])
                        if current_level >= level:
                            row_class = 'table-success'
                            marker = '✓ '
                        else:
                            row_class = 'table-secondary'
                            marker = '🔒 '
                        description += f'<tr class="{row_class}"><td>{level}</td><td>{marker}{spells}</td></tr>\n'
                    description += '</tbody>\n</table>'
                else:
                    # Single level, use simple format
                    all_spells = []
                    for spells in spells_by_level.values():
                        all_spells.extend(spells)
                    description += f"\n\nSpells Always Prepared: {', '.join(all_spells)}"
        
        # Add to features dict
        feature_entry = {
            'name': display_name,
            'description': description,
            'source': source_display
        }
        
        # Check if feature already exists (avoid duplicates)
        if not any(f['name'].startswith(trait_name) for f in self.character_data['features'][category]):
            self.character_data['features'][category].append(feature_entry)
        
        # If trait_data is just a string, no effects to apply
        if isinstance(trait_data, str):
            return
        
        # If trait_data is a dict, check for effects
        if isinstance(trait_data, dict):
            effects = trait_data.get('effects', [])
            for effect in effects:
                self._apply_effect(effect, trait_name, source)
    
    def _apply_feature_scaling(self, description: str, scaling: Dict[str, Any]) -> str:
        """
        Apply scaling substitutions to feature description.
        
        Args:
            description: Feature description with template variables
            scaling: Scaling configuration
        
        Returns:
            Description with substituted values
        """
        level = self.character_data.get('level', 1)
        
        for var_name, scale_list in scaling.items():
            # Find the appropriate value for current level
            value = None
            for scale_entry in scale_list:
                min_level = scale_entry.get('min_level', 1)
                if level >= min_level:
                    value = scale_entry.get('value')
            
            # Replace template variable
            if value is not None:
                description = description.replace(f'{{{var_name}}}', str(value))
        
        return description
    
    def _apply_effect(self, effect: Dict[str, Any], source_name: str, source_type: str):
        """
        Apply a single effect from the effects system.
        
        Args:
            effect: Effect dictionary with 'type' and other parameters
            source_name: Name of the feature/trait providing the effect
            source_type: Type of source ('species', 'lineage', 'class', etc.)
        """
        effect_type = effect.get('type')
        
        if effect_type == 'grant_cantrip':
            spell_name = effect.get('spell')
            if spell_name and spell_name not in self.character_data['spells']['cantrips']:
                self.character_data['spells']['cantrips'].append(spell_name)
        
        elif effect_type == 'grant_cantrip_choice':
            # This effect requires a choice to be made - store for later processing
            # The choice handling will add the cantrip when the choice is made
            pass  # Handled by choice resolution system
        
        elif effect_type == 'grant_spell':
            spell_name = effect.get('spell')
            min_level = effect.get('min_level', 1)
            if spell_name and self.character_data['level'] >= min_level:
                # Species/lineage spells are always prepared and castable once per day without slots
                if spell_name not in self.character_data['spells']['prepared']:
                    self.character_data['spells']['prepared'].append(spell_name)
                
                # Track spell metadata for display (source type for once-per-day indicator)
                if 'spell_metadata' not in self.character_data:
                    self.character_data['spell_metadata'] = {}
                self.character_data['spell_metadata'][spell_name] = {
                    'source': source_type,
                    'once_per_day': source_type in ['species', 'lineage']
                }
        
        elif effect_type == 'grant_weapon_proficiency':
            proficiencies = effect.get('proficiencies', [])
            for prof in proficiencies:
                if prof not in self.character_data['proficiencies']['weapons']:
                    self.character_data['proficiencies']['weapons'].append(prof)
                    # Track the source of this weapon proficiency
                    if source_type == 'species_choice':
                        source_display = self.character_data.get('species', source_name)
                    elif source_type in ['species', 'lineage']:
                        source_display = self.character_data.get('species', source_name)
                    else:
                        source_display = source_name
                    self.character_data['proficiency_sources']['weapons'][prof] = source_display
        
        elif effect_type == 'grant_armor_proficiency':
            proficiencies = effect.get('proficiencies', [])
            for prof in proficiencies:
                if prof not in self.character_data['proficiencies']['armor']:
                    self.character_data['proficiencies']['armor'].append(prof)
                    # Track the source of this armor proficiency
                    if source_type == 'species_choice':
                        source_display = self.character_data.get('species', source_name)
                    elif source_type in ['species', 'lineage']:
                        source_display = self.character_data.get('species', source_name)
                    else:
                        source_display = source_name
                    self.character_data['proficiency_sources']['armor'][prof] = source_display
        
        elif effect_type == 'grant_skill_proficiency':
            skills = effect.get('skills', [])
            for skill in skills:
                if skill not in self.character_data['proficiencies']['skills']:
                    self.character_data['proficiencies']['skills'].append(skill)
                    # Track the source of this skill proficiency
                    if source_type == 'species_choice':
                        # For species choices, use just the species name
                        source_display = self.character_data.get('species', source_name)
                    elif source_type in ['species', 'lineage']:
                        source_display = self.character_data.get('species', source_name)
                    else:
                        source_display = source_name
                    self.character_data['proficiency_sources']['skills'][skill] = source_display
        
        elif effect_type == 'grant_damage_resistance':
            damage_type = effect.get('damage_type')
            if damage_type and damage_type not in self.character_data['resistances']:
                self.character_data['resistances'].append(damage_type)
        
        elif effect_type == 'grant_darkvision':
            darkvision_range = effect.get('range', 60)
            if darkvision_range > self.character_data['darkvision']:
                self.character_data['darkvision'] = darkvision_range
        
        elif effect_type == 'increase_speed':
            speed_increase = effect.get('value', 0)
            self.character_data['speed'] += speed_increase
        
        elif effect_type == 'ability_bonus':
            # Store ability bonuses for later calculation (like Thaumaturge)
            if 'ability_bonuses' not in self.character_data:
                self.character_data['ability_bonuses'] = []
            
            bonus_info = {
                'ability': effect.get('ability'),
                'skills': effect.get('skills', []),
                'value': effect.get('value'),
                'minimum': effect.get('minimum', 0),
                'source': source_name
            }
            self.character_data['ability_bonuses'].append(bonus_info)
        
        # Track applied effect
        self.applied_effects.append({
            'type': effect_type,
            'source': source_name,
            'source_type': source_type,
            'effect': effect
        })
    
    # ==================== Class/Subclass Methods ====================
    
    def set_class(self, class_name: str, level: int = 1) -> bool:
        """
        Set the character's class and level.
        
        Args:
            class_name: Name of the class (e.g., "Wizard", "Fighter")
            level: Character level (default: 1)
        
        Returns:
            True if successful, False otherwise
        """
        class_data = self._load_class_data(class_name)
        if not class_data:
            return False

        # If class is changing or level is changing, clear existing class features
        if (self.character_data.get('class') != class_name or 
            self.character_data.get('level') != level):
            self._clear_class_features()
        
        self.character_data['class'] = class_name
        self.character_data['class_data'] = class_data
        self.character_data['level'] = level
        
        # Re-apply lineage traits if they exist (for level-based spells)
        if '_lineage_traits' in self.character_data:
            # Clear existing level-based spells first
            self.character_data['spells']['known'] = []
            # Re-apply with new level
            for trait_name, trait_data in self.character_data['_lineage_traits'].items():
                self._apply_trait_effects(trait_name, trait_data, 'lineage')
        
        # Apply class features
        self._apply_class_features(class_data, level)
        
        # Re-apply subclass features if subclass exists
        if self.character_data.get('subclass'):
            subclass_data = self.character_data.get('subclass_data')
            if subclass_data:
                self._clear_subclass_features()
                self._apply_subclass_features(subclass_data, level)
        
        # Determine next step
        subclass_level = class_data.get('subclass_selection_level', 3)
        if level >= subclass_level:
            self.character_data['step'] = 'subclass'
        else:
            self.character_data['step'] = 'background'
        
        return True
    
    def _clear_class_features(self):
        """Clear all class-related features and effects before re-applying."""
        # Clear class features
        self.character_data['features']['class'] = []
        
        # Reset proficiencies to base level (before class was added)
        self.character_data['proficiencies']['saving_throws'] = []
        self.character_data['proficiencies']['weapons'] = []
        self.character_data['proficiencies']['armor'] = []
        
        # Clear applied effects from class source
        if hasattr(self, 'applied_effects'):
            self.applied_effects = [e for e in self.applied_effects 
                                  if e.get('source_type') not in ['class', 'class_choice']]
    
    def _clear_subclass_features(self):
        """Clear all subclass-related features and effects before re-applying."""
        # Clear subclass features
        self.character_data['features']['subclass'] = []
        
        # Clear applied effects from subclass source
        if hasattr(self, 'applied_effects'):
            self.applied_effects = [e for e in self.applied_effects 
                                  if e.get('source_type') != 'subclass']
        
        # Clear subclass spells from prepared list
        spell_metadata = self.character_data.get('spell_metadata', {})
        prepared_spells = self.character_data['spells']['prepared']
        
        # Remove spells that were from subclass
        for spell_name in list(prepared_spells):
            if spell_name in spell_metadata and spell_metadata[spell_name].get('source') == 'subclass':
                prepared_spells.remove(spell_name)
                del spell_metadata[spell_name]
    
    def set_subclass(self, subclass_name: str) -> bool:
        """
        Set the character's subclass.
        
        Args:
            subclass_name: Name of the subclass
        
        Returns:
            True if successful, False otherwise
        """
        if not self.character_data['class']:
            return False
        
        subclass_data = self._load_subclass_data(
            self.character_data['class'],
            subclass_name
        )
        if not subclass_data:
            return False
        
        self.character_data['subclass'] = subclass_name
        self.character_data['subclass_data'] = subclass_data
        
        # Apply subclass features for current level
        self._apply_subclass_features(subclass_data, self.character_data['level'])
        
        self.character_data['step'] = 'background'
        return True
    
    def _apply_class_features(self, class_data: Dict[str, Any], level: int):
        """Apply class features up to the specified level."""
        # Saving throw proficiencies
        saving_throws = class_data.get('saving_throw_proficiencies', [])
        self.character_data['proficiencies']['saving_throws'].extend(saving_throws)
        
        # Armor proficiencies
        armor_profs = class_data.get('armor_proficiencies', [])
        for prof in armor_profs:
            if prof not in self.character_data['proficiencies']['armor']:
                self.character_data['proficiencies']['armor'].append(prof)
        
        # Weapon proficiencies
        weapon_profs = class_data.get('weapon_proficiencies', [])
        for prof in weapon_profs:
            if prof not in self.character_data['proficiencies']['weapons']:
                self.character_data['proficiencies']['weapons'].append(prof)
        
        # Features by level
        features_by_level = class_data.get('features_by_level', {})
        for feat_level in range(1, level + 1):
            level_features = features_by_level.get(str(feat_level), {})
            for feature_name, feature_data in level_features.items():
                self._apply_trait_effects(feature_name, feature_data, 'class')
    
    def _apply_subclass_features(self, subclass_data: Dict[str, Any], level: int):
        """Apply subclass features up to the specified level."""
        features_by_level = subclass_data.get('features_by_level', {})
        for feat_level_str, level_features in features_by_level.items():
            feat_level = int(feat_level_str)
            if feat_level <= level:
                for feature_name, feature_data in level_features.items():
                    self._apply_trait_effects(feature_name, feature_data, 'subclass')
    
    # ==================== Background Methods ====================
    
    def set_background(self, background_name: str) -> bool:
        """
        Set the character's background.
        
        Args:
            background_name: Name of the background (e.g., "Sage", "Soldier")
        
        Returns:
            True if successful, False otherwise
        """
        background_data = self._load_background_data(background_name)
        if not background_data:
            return False
        
        self.character_data['background'] = background_name
        self.character_data['background_data'] = background_data
        
        # Apply background features
        self._apply_background_features(background_data)
        
        self.character_data['step'] = 'abilities'
        return True
    
    def _apply_background_features(self, background_data: Dict[str, Any]):
        """Apply background features including skill proficiencies."""
        background_name = background_data.get('name', self.character_data.get('background', 'Unknown'))
        
        # Skill proficiencies
        skill_profs = background_data.get('skill_proficiencies', [])
        for skill in skill_profs:
            if skill not in self.character_data['proficiencies']['skills']:
                self.character_data['proficiencies']['skills'].append(skill)
        
        # Tool proficiencies
        tool_profs = background_data.get('tool_proficiencies', [])
        for tool in tool_profs:
            if tool not in self.character_data['proficiencies']['tools']:
                self.character_data['proficiencies']['tools'].append(tool)
        
        # Languages - can be either a list or a number
        languages = background_data.get('languages', [])
        if isinstance(languages, list):
            for lang in languages:
                if lang not in self.character_data['proficiencies']['languages']:
                    self.character_data['proficiencies']['languages'].append(lang)
        elif isinstance(languages, int):
            # Store that they need to choose N languages
            self.character_data['choices_made']['language_choices_needed'] = languages
        
        # Background features
        features = background_data.get('features', {})
        for feature_name, feature_data in features.items():
            description = feature_data if isinstance(feature_data, str) else feature_data.get('description', '')
            feature_entry = {
                'name': feature_name,
                'description': description,
                'source': background_name
            }
            if not any(f['name'] == feature_name for f in self.character_data['features']['background']):
                self.character_data['features']['background'].append(feature_entry)
        
        # Background feat
        feat = background_data.get('feat')
        if feat:
            feat_entry = {
                'name': feat,
                'description': f"Feat granted by {background_name} background.",
                'source': background_name
            }
            if not any(f['name'] == feat for f in self.character_data['features']['feats']):
                self.character_data['features']['feats'].append(feat_entry)
    
    # ==================== Ability Score Methods ====================
    
    def set_abilities(self, scores: Dict[str, int], 
                      species_bonuses: Optional[Dict[str, int]] = None,
                      background_bonuses: Optional[Dict[str, int]] = None) -> bool:
        """
        Set ability scores with optional bonuses.
        
        Args:
            scores: Base ability scores {"STR": 10, "DEX": 14, ...}
            species_bonuses: Species ability bonuses (usually empty in 2024)
            background_bonuses: Background ability bonuses
        
        Returns:
            True if successful, False otherwise
        """
        self.ability_scores.set_base_scores(scores)
        
        if species_bonuses:
            self.ability_scores.apply_species_bonuses(species_bonuses)
        
        if background_bonuses:
            self.ability_scores.apply_background_bonuses(background_bonuses)
        
        # Store in character data
        self.character_data['abilities'] = {
            'base': scores,
            'species_bonuses': species_bonuses or {},
            'background_bonuses': background_bonuses or {},
            'final': self.ability_scores.final_scores
        }
        
        self.character_data['step'] = 'complete'
        return True
    
    # ==================== Choice Application Methods ====================
    
    def apply_choice(self, choice_key: str, choice_value: Any) -> bool:
        """
        Apply a single choice and its effects to the character.
        
        Args:
            choice_key: The choice identifier (e.g., 'species', 'class', 'Divine Order')
            choice_value: The choice value (can be string, int, list, dict)
        
        Returns:
            True if choice was applied successfully
        """
        # Store the choice
        self.character_data['choices_made'][choice_key] = choice_value
        
        # Apply based on choice type
        choice_key_lower = choice_key.lower()
        
        # Core character selections
        if choice_key_lower == 'species':
            return self.set_species(choice_value)
        elif choice_key_lower == 'lineage':
            return self.set_lineage(choice_value)
        elif choice_key_lower == 'class':
            return self.set_class(choice_value, self.character_data.get('level', 1))
        elif choice_key_lower == 'subclass':
            return self.set_subclass(choice_value)
        elif choice_key_lower == 'background':
            return self.set_background(choice_value)
        elif choice_key_lower == 'level':
            current_class = self.character_data.get('class')
            if current_class:
                return self.set_class(current_class, int(choice_value))
            self.character_data['level'] = int(choice_value)
            return True
        
        # Ability scores
        elif choice_key_lower in ['ability_scores', 'abilities']:
            if isinstance(choice_value, dict):
                return self.set_abilities(choice_value)
            elif choice_value == 'standard_array_recommended':
                # Get the recommended ability scores from class data
                class_data = self.character_data.get('class_data', {})
                standard_array = class_data.get('standard_array_assignment')
                if standard_array:
                    return self.set_abilities(standard_array)
            return True
        elif choice_key_lower == 'ability_scores_method':
            # Handle "recommended" or "manual" ability score method
            if choice_value == 'recommended':
                # Get the recommended ability scores from class data
                class_data = self.character_data.get('class_data', {})
                if class_data:
                    # Calculate standard array assignment
                    standard_array = [15, 14, 13, 12, 10, 8]
                    abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
                    primary_ability_data = class_data.get('primary_ability', '')
                    
                    # Parse primary abilities
                    if isinstance(primary_ability_data, list):
                        primary_abilities = primary_ability_data
                    elif isinstance(primary_ability_data, str):
                        primary_abilities = primary_ability_data.split(', ') if primary_ability_data else []
                    else:
                        primary_abilities = []
                    
                    ability_mapping = {}
                    remaining_values = standard_array.copy()
                    remaining_abilities = abilities.copy()
                    
                    # Assign primary abilities first
                    for primary_ability in primary_abilities:
                        if primary_ability in remaining_abilities and remaining_values:
                            ability_mapping[primary_ability] = remaining_values.pop(0)
                            remaining_abilities.remove(primary_ability)
                    
                    # Assign Constitution next (if not already assigned)
                    if "Constitution" in remaining_abilities and remaining_values:
                        ability_mapping["Constitution"] = remaining_values.pop(0)
                        remaining_abilities.remove("Constitution")
                    
                    # Assign remaining values
                    for ability in remaining_abilities:
                        if remaining_values:
                            ability_mapping[ability] = remaining_values.pop(0)
                    
                    return self.set_abilities(ability_mapping)
            return True
        elif choice_key_lower == 'background_ability_score_assignment':
            # Apply background ability bonuses
            if isinstance(choice_value, dict):
                self.ability_scores.apply_background_bonuses(choice_value)
            return True
        elif choice_key_lower == 'background_bonuses_method':
            # Handle "suggested" background bonuses
            if choice_value == 'suggested':
                background_data = self.character_data.get('background_data', {})
                if background_data:
                    asi_data = background_data.get('ability_score_increase', {})
                    suggested = asi_data.get('suggested', {})
                    if suggested:
                        self.ability_scores.apply_background_bonuses(suggested)
            return True
        
        # Languages
        elif choice_key_lower == 'languages':
            if isinstance(choice_value, list):
                # Add languages that aren't already known
                for lang in choice_value:
                    if lang not in self.character_data['proficiencies']['languages']:
                        self.character_data['proficiencies']['languages'].append(lang)
            return True
        
        # Skills
        elif choice_key_lower in ['skill_choices', 'skills']:
            if isinstance(choice_value, list):
                for skill in choice_value:
                    if skill not in self.character_data['proficiencies']['skills']:
                        self.character_data['proficiencies']['skills'].append(skill)
            return True
        
        # Spells
        elif choice_key_lower == 'spellcasting':
            if isinstance(choice_value, list):
                for spell in choice_value:
                    if spell not in self.character_data['spells']['cantrips']:
                        self.character_data['spells']['cantrips'].append(spell)
                
                # Update Spellcasting feature to include chosen cantrips
                for feature in self.character_data['features']['class']:
                    if feature['name'] == 'Spellcasting':
                        # Append cantrips to description
                        cantrip_text = f"\n\nCantrips Known: {', '.join(choice_value)}"
                        if cantrip_text not in feature['description']:
                            feature['description'] += cantrip_text
                        break
            return True
        
        # Nested bonus choices (e.g., Thaumaturge_bonus_cantrip)
        elif '_bonus_cantrip' in choice_key_lower:
            # Extract parent feature name (e.g., "Thaumaturge" from "Thaumaturge_bonus_cantrip")
            parent_name = choice_key.replace('_bonus_cantrip', '').replace('_', ' ').title()
            
            # Add cantrip(s) to character's spell list
            cantrips_to_add = choice_value if isinstance(choice_value, list) else [choice_value]
            for cantrip in cantrips_to_add:
                if cantrip not in self.character_data['spells']['cantrips']:
                    self.character_data['spells']['cantrips'].append(cantrip)
            
            # Find the parent feature and append the choice
            cantrip_display = ', '.join(cantrips_to_add) if isinstance(choice_value, list) else choice_value
            for category in ['class', 'subclass', 'species', 'lineage']:
                for feature in self.character_data['features'][category]:
                    # Look for features that start with "Divine Order: Thaumaturge" or just "Thaumaturge"
                    if parent_name in feature['name']:
                        # Append the bonus cantrip info
                        bonus_text = f"\n\nBonus Cantrip: {cantrip_display}"
                        if bonus_text not in feature['description']:
                            feature['description'] += bonus_text
                        return True
            return True
        
        # Character metadata
        elif choice_key_lower in ['character_name', 'name']:
            self.character_data['name'] = choice_value
            return True
        elif choice_key_lower == 'alignment':
            self.character_data['alignment'] = choice_value
            return True
        
        # Generic choice - might be class feature choice
        # Try to find and apply effects from class/subclass data
        else:
            # Update feature display name if this is a choice for an existing feature
            self._update_feature_choice_display(choice_key, choice_value)
            
            # Check if this is a feature choice with effects
            if self.character_data.get('class_data'):
                self._apply_choice_effects(choice_key, choice_value, self.character_data['class_data'])
            if self.character_data.get('subclass_data'):
                self._apply_choice_effects(choice_key, choice_value, self.character_data['subclass_data'])
            if self.character_data.get('species_data'):
                self._apply_species_choice_effects(choice_key, choice_value, self.character_data['species_data'])
            if self.character_data.get('lineage_data'):
                self._apply_species_choice_effects(choice_key, choice_value, self.character_data['lineage_data'])
            # Just store it
            return True
    
    def _update_feature_choice_display(self, choice_key: str, choice_value: Any):
        """
        Update feature display name and description to include the choice made.
        
        Args:
            choice_key: The choice identifier (e.g., 'Divine Order', 'divine_order', 'species_trait_Elven Lineage')
            choice_value: The chosen value (e.g., 'Thaumaturge', 'Wisdom')
        """
        if not isinstance(choice_value, str):
            return
        
        # Handle species_trait_ prefix
        feature_base = choice_key
        if choice_key.startswith('species_trait_'):
            feature_base = choice_key.replace('species_trait_', '')
        
        # Normalize choice key to match feature names
        feature_name_variants = [
            feature_base,
            feature_base.replace('_', ' ').title(),
            feature_base.replace('_', ' '),
            choice_key,  # Also try original
            choice_key.replace('_', ' ').title(),
            choice_key.replace('_', ' '),
        ]
        
        # Try to find the choice-specific description from class/subclass data
        choice_description = None
        choice_scaling = None
        for data_source_key in ['class_data', 'subclass_data']:
            source_data = self.character_data.get(data_source_key, {})
            if source_data:
                # Look for internal list (e.g., 'divine_orders', 'fighting_styles')
                for data_key, data_value in source_data.items():
                    if isinstance(data_value, dict) and choice_value in data_value:
                        option_data = data_value[choice_value]
                        if isinstance(option_data, dict):
                            if 'description' in option_data:
                                choice_description = option_data['description']
                                choice_scaling = option_data.get('scaling')
                                break
                        elif isinstance(option_data, str):
                            choice_description = option_data
                            break
                if choice_description:
                    break
        
        # Search all feature categories for a matching feature
        for category in ['class', 'subclass', 'species', 'lineage', 'background', 'feats']:
            for feature in self.character_data['features'][category]:
                # Check if this feature matches the choice
                for variant in feature_name_variants:
                    if feature['name'] == variant or feature['name'].startswith(variant + ':'):
                        # Update the name to include the choice
                        base_name = variant if feature['name'] == variant else feature['name'].split(':')[0]
                        if isinstance(choice_value, list):
                            feature['name'] = f"{base_name}: {', '.join(choice_value)}"
                        else:
                            feature['name'] = f"{base_name}: {choice_value}"
                        
                        # Update description if we found a choice-specific one
                        if choice_description:
                            # Apply scaling if present
                            if choice_scaling:
                                choice_description = self._apply_feature_scaling(choice_description, choice_scaling)
                            feature['description'] = choice_description
                        return
    
    def _apply_choice_effects(self, choice_key: str, choice_value: Any, source_data: Dict[str, Any]):
        """
        Look up and apply effects from a choice made in class/subclass features.
        
        Args:
            choice_key: The choice identifier (e.g., 'Divine Order', 'divine_order')
            choice_value: The chosen value (e.g., 'Thaumaturge')
            source_data: Class or subclass data to search for effects
        """
        # Normalize choice key for lookup
        choice_key_lower = choice_key.lower().replace(' ', '_')
        
        # Search for the choice in class data structures
        # Common patterns: 'divine_orders', 'fighting_styles', etc.
        for data_key, data_value in source_data.items():
            if not isinstance(data_value, dict):
                continue
            
            # Check if this dict contains the chosen value
            if isinstance(choice_value, str) and choice_value in data_value:
                option_data = data_value[choice_value]
                if isinstance(option_data, dict) and 'effects' in option_data:
                    # Apply each effect
                    for effect in option_data['effects']:
                        self._apply_effect(effect, choice_value, 'class_choice')
                    return
    
    def _apply_species_choice_effects(self, choice_key: str, choice_value: Any, source_data: Dict[str, Any]):
        """
        Look up and apply effects from a choice made in species/lineage traits.
        
        Args:
            choice_key: The choice identifier (e.g., 'Keen Senses', 'Elven Lineage')
            choice_value: The chosen value (e.g., 'Insight', 'Intelligence')
            source_data: Species or lineage data to search for effects
        """
        # Look for traits with choice_effects
        traits = source_data.get('traits', {})
        for trait_name, trait_data in traits.items():
            # Check if this trait matches the choice key and has choice_effects
            if (trait_name == choice_key and 
                isinstance(trait_data, dict) and 
                'choice_effects' in trait_data):
                
                choice_effects = trait_data['choice_effects']
                if choice_value in choice_effects:
                    effects = choice_effects[choice_value]
                    # Apply each effect
                    for effect in effects:
                        self._apply_effect(effect, f"{trait_name}: {choice_value}", 'species_choice')
                    return
    
    def apply_choices(self, choices: Dict[str, Any]) -> bool:
        """
        Apply multiple choices at once from a choices dictionary.
        This is useful for batch operations like rebuilding from saved choices.
        
        Args:
            choices: Dictionary of choice_key -> choice_value pairs
        
        Returns:
            True if all choices were applied successfully
        """
        # Apply choices in a specific order for dependencies
        order = [
            'character_name', 'name',
            'level',
            'species',
            'lineage',
            'class',
            'subclass',
            'background',
            'ability_scores', 'abilities',
            'background_ability_score_assignment',
            'skill_choices', 'skills',
            'spellcasting',
            'alignment'
        ]
        
        # First pass: apply ordered choices
        for key in order:
            if key in choices:
                self.apply_choice(key, choices[key])
        
        # Second pass: apply remaining choices (class-specific features, etc.)
        for key, value in choices.items():
            if key not in order:
                self.apply_choice(key, value)
        
        return True
    
    # ==================== Export Methods ====================
    
    def to_json(self) -> dict:
        """
        Export character as JSON dictionary.
        
        Returns:
            Complete character data as dictionary
        """
        data = deepcopy(self.character_data)
        # Add ability scores from the AbilityScores module
        data['ability_scores'] = self.ability_scores.final_scores
        
        # Add applied effects to character JSON so web app can use them
        if hasattr(self, 'applied_effects') and self.applied_effects:
            # Include both the effect and source information for web app
            effects_for_export = []
            for applied_effect in self.applied_effects:
                effect = applied_effect['effect'].copy()
                effect['source'] = applied_effect.get('source', 'Unknown')
                effect['source_type'] = applied_effect.get('source_type', 'Unknown')
                effects_for_export.append(effect)
            data['effects'] = effects_for_export
        else:
            data['effects'] = []
        
        # Flatten proficiencies for easier template access
        data['languages'] = data['proficiencies']['languages']
        data['skill_proficiencies'] = data['proficiencies']['skills']
        data['weapon_proficiencies'] = data['proficiencies']['weapons']
        data['armor_proficiencies'] = data['proficiencies']['armor']
        
        # Include choices_made for web app compatibility
        data['choices_made'] = self.character_data.get('choices_made', {})
        
        return data
    
    def to_character(self) -> Character:
        """
        Convert to Character object.
        
        Returns:
            Character object with all data populated
        """
        char = Character()
        char.name = self.character_data.get('name', '')
        char.species = self.character_data.get('species', '')
        char.species_variant = self.character_data.get('lineage', '')
        char.class_name = self.character_data.get('class', '')
        char.subclass = self.character_data.get('subclass', '')
        char.background = self.character_data.get('background', '')
        char.level = self.character_data.get('level', 1)
        
        # Ability scores
        abilities = self.character_data.get('abilities', {})
        if abilities:
            char.ability_scores = self.ability_scores
        
        # Proficiencies
        profs = self.character_data.get('proficiencies', {})
        char.weapon_proficiencies = profs.get('weapons', [])
        char.armor_proficiencies = profs.get('armor', [])
        char.tool_proficiencies = profs.get('tools', [])
        char.skill_proficiencies = profs.get('skills', [])
        char.languages = profs.get('languages', [])
        
        # Other attributes
        char.speed = self.character_data.get('speed', 30)
        char.darkvision_range = self.character_data.get('darkvision', 0)
        
        # Store data references
        char.species_data = self.character_data.get('species_data')
        char.class_data = self.character_data.get('class_data')
        char.background_data = self.character_data.get('background_data')
        
        return char
    
    def from_json(self, data: dict):
        """
        Import character from JSON dictionary.
        
        Args:
            data: Character data dictionary
        """
        self.character_data = deepcopy(data)
        
        # Reconstruct ability scores
        abilities = data.get('abilities', {})
        if abilities:
            if 'base' in abilities:
                self.ability_scores.set_base_scores(abilities['base'])
            if 'species_bonuses' in abilities:
                self.ability_scores.apply_species_bonuses(abilities['species_bonuses'])
            if 'background_bonuses' in abilities:
                self.ability_scores.apply_background_bonuses(abilities['background_bonuses'])
    
    @classmethod
    def quick_create(cls, species: str, char_class: str, background: str,
                     abilities: Dict[str, int], lineage: Optional[str] = None,
                     subclass: Optional[str] = None, level: int = 1,
                     spellcasting_ability: Optional[str] = None) -> 'CharacterBuilder':
        """
        Factory method for quick character creation (useful for testing).
        
        Args:
            species: Species name
            char_class: Class name
            background: Background name
            abilities: Ability scores
            lineage: Optional lineage/variant name
            subclass: Optional subclass name
            level: Character level
            spellcasting_ability: Optional spellcasting ability for lineages
        
        Returns:
            Fully configured CharacterBuilder
        """
        builder = cls()
        builder.set_species(species)
        
        if lineage:
            builder.set_lineage(lineage, spellcasting_ability)
        
        builder.set_class(char_class, level)
        
        if subclass:
            builder.set_subclass(subclass)
        
        builder.set_background(background)
        builder.set_abilities(abilities)
        
        return builder
    
    # ==================== Validation & Query Methods ====================
    
    def is_complete(self) -> bool:
        """Check if character creation is complete."""
        return self.character_data['step'] == 'complete'
    
    def get_current_step(self) -> str:
        """Get the current creation step."""
        return self.character_data['step']
    
    def get_cantrips(self) -> List[str]:
        """Get list of known cantrips."""
        return self.character_data['spells']['cantrips']
    
    def get_spells(self) -> List[str]:
        """Get list of known spells."""
        return self.character_data['spells']['known']
    
    def get_proficiencies(self, prof_type: str) -> List[str]:
        """
        Get proficiencies of a specific type.
        
        Args:
            prof_type: Type of proficiency ('armor', 'weapons', 'skills', etc.)
        
        Returns:
            List of proficiencies
        """
        return self.character_data['proficiencies'].get(prof_type, [])
    
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate character data.
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []
        
        # Check required fields
        if not self.character_data.get('species'):
            errors.append("Species is required")
        
        if not self.character_data.get('class'):
            errors.append("Class is required")
        
        if not self.character_data.get('background'):
            errors.append("Background is required")
        
        if not self.character_data.get('abilities'):
            errors.append("Ability scores are required")
        
        # Check ability score validity
        abilities = self.character_data.get('abilities', {}).get('base', {})
        for ability, score in abilities.items():
            if score < 1 or score > 20:
                errors.append(f"{ability} score {score} is out of valid range (1-20)")
        
        return {'errors': errors, 'warnings': warnings}
