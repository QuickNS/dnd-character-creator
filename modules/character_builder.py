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

# Import choice resolver for feature processing
import sys
import math

if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.choice_resolver import resolve_choice_options, get_option_descriptions


class CharacterBuilder:
    """
    Stateful builder for D&D 2024 character creation.

    This class manages the step-by-step process of creating a character,
    loading data from JSON files, applying effects, and tracking choices.
    """

    # Character creation steps in order
    CREATION_STEPS = [
        "species",
        "lineage",  # Optional - only for species with variants
        "class",
        "subclass",  # Only at appropriate level
        "background",
        "abilities",
        "features",  # Any additional choices (feats, skills, etc.)
        "complete",
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

        # Load weapon and armor data for equipment processing
        self._weapon_data = self._load_weapon_data()
        self._armor_data = self._load_armor_data()

        # Spell definitions cache
        self._spell_definitions_cache = {}

        # D&D 2024 skill to ability mappings for calculations
        self.skill_abilities = {
            "acrobatics": "dexterity",
            "animal_handling": "wisdom",
            "arcana": "intelligence",
            "athletics": "strength",
            "deception": "charisma",
            "history": "intelligence",
            "insight": "wisdom",
            "intimidation": "charisma",
            "investigation": "intelligence",
            "medicine": "wisdom",
            "nature": "intelligence",
            "perception": "wisdom",
            "performance": "charisma",
            "persuasion": "charisma",
            "religion": "intelligence",
            "sleight_of_hand": "dexterity",
            "stealth": "dexterity",
            "survival": "wisdom",
        }

        # Character data storage
        self.character_data = {
            "name": "",
            "alignment": "",
            "species": None,
            "species_data": None,
            "lineage": None,
            "lineage_data": None,
            "class": None,
            "class_data": None,
            "subclass": None,
            "subclass_data": None,
            "background": None,
            "background_data": None,
            "level": 1,
            "abilities": {},
            "features": {
                "class": [],
                "subclass": [],
                "species": [],
                "lineage": [],
                "background": [],
                "feats": [],
            },
            "choices_made": {},
            "spells": {
                "always_prepared": {},  # Fixed spells (subclass, lineage, features) - dict of spell_name -> metadata
                "prepared": {
                    "cantrips": {},
                    "spells": {},
                },  # User-selected prepared spells (can change on long rest)
                "known": {},  # Permanently known spells (for known casters)
                "background_spells": {},  # Special background spells (Magic Initiate, etc.)
                "slots": {},
            },
            "spell_metadata": {},  # Track spell sources and special properties
            "spell_selections_needed": {  # Track what spells need to be selected
                "cantrips": 0,
                "prepared_spells": 0,
                "background_cantrips": {"count": 0, "spell_list": None},
                "background_spells": {"count": 0, "spell_list": None, "level": 1},
            },
            "weapon_masteries": {
                "selected": [],  # User-selected weapon masteries
                "available": [],  # Weapons available for mastery
                "max_count": 0,  # Maximum masteries allowed
            },
            "proficiencies": {
                "armor": [],
                "weapons": [],
                "tools": [],
                "skills": [],
                "languages": [],
                "saving_throws": [],
            },
            "proficiency_sources": {
                "armor": {},
                "weapons": {},
                "tools": {},
                "skills": {},
                "languages": {},
                "saving_throws": {},
            },
            "speed": 30,
            "darkvision": 0,
            "resistances": [],
            "immunities": [],
            "equipment": None,  # Will be initialized when equipment_selections are processed
            "step": "species",  # Track current step
        }

        # Track applied effects
        self.applied_effects = []

    # ==================== Data Loading Methods ====================

    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load a JSON file and return its contents."""
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def _load_species_data(self, species_name: str) -> Optional[Dict[str, Any]]:
        """Load species data from JSON file."""
        filename = species_name.lower().replace(" ", "_")
        file_path = self.data_dir / "species" / f"{filename}.json"
        return self._load_json_file(file_path)

    def _load_lineage_data(
        self, species_name: str, lineage_name: str
    ) -> Optional[Dict[str, Any]]:
        """Load lineage/variant data from JSON file."""
        filename = lineage_name.lower().replace(" ", "_")
        file_path = self.data_dir / "species_variants" / f"{filename}.json"
        return self._load_json_file(file_path)

    def _load_class_data(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Load class data from JSON file."""
        filename = class_name.lower().replace(" ", "_")
        file_path = self.data_dir / "classes" / f"{filename}.json"
        return self._load_json_file(file_path)

    def _load_subclass_data(
        self, class_name: str, subclass_name: str
    ) -> Optional[Dict[str, Any]]:
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

        self.character_data["species"] = species_name
        self.character_data["species_data"] = species_data

        # Apply species base traits
        self._apply_species_traits(species_data)

        # Check if species has variants
        has_variants = species_name in self.variant_manager.species_variants
        if has_variants:
            self.character_data["step"] = "lineage"
        else:
            self.character_data["step"] = "class"

        return True

    def set_lineage(
        self, lineage_name: str, spellcasting_ability: Optional[str] = None
    ) -> bool:
        """
        Set the character's lineage/variant.

        Args:
            lineage_name: Name of the lineage (e.g., "Wood Elf", "High Elf")
            spellcasting_ability: For lineages with spell choices (e.g., "Wisdom")

        Returns:
            True if successful, False otherwise
        """
        if not self.character_data["species"]:
            return False

        lineage_data = self._load_lineage_data(
            self.character_data["species"], lineage_name
        )
        if not lineage_data:
            return False

        self.character_data["lineage"] = lineage_name
        self.character_data["lineage_data"] = lineage_data

        # Store spellcasting ability if provided
        if spellcasting_ability:
            self.character_data["spellcasting_ability"] = spellcasting_ability

        # Apply lineage traits and effects
        self._apply_lineage_traits(lineage_data)

        self.character_data["step"] = "class"
        return True

    def _apply_species_traits(self, species_data: Dict[str, Any]):
        """Apply base species traits."""
        # Speed
        if "speed" in species_data:
            self.character_data["speed"] = species_data["speed"]

        # Darkvision
        if "darkvision" in species_data:
            self.character_data["darkvision"] = species_data["darkvision"]

        # Languages
        if "languages" in species_data:
            self.character_data["proficiencies"]["languages"].extend(
                species_data["languages"]
            )

        # Traits with effects
        traits = species_data.get("traits", {})
        for trait_name, trait_data in traits.items():
            self._apply_trait_effects(trait_name, trait_data, "species")

    def _apply_lineage_traits(self, lineage_data: Dict[str, Any]):
        """Apply lineage/variant traits."""
        # Override speed if lineage specifies it
        if "speed" in lineage_data:
            self.character_data["speed"] = lineage_data["speed"]

        # Override darkvision if lineage specifies it
        if "darkvision" in lineage_data:
            self.character_data["darkvision"] = lineage_data["darkvision"]

        # Store lineage data for later re-application when level changes
        self.character_data["_lineage_traits"] = lineage_data.get("traits", {})

        # Traits with effects
        traits = lineage_data.get("traits", {})
        for trait_name, trait_data in traits.items():
            self._apply_trait_effects(trait_name, trait_data, "lineage")

    def _apply_trait_effects(
        self, trait_name: str, trait_data: Any, source: str, level: int = None
    ):
        """
        Apply effects from a trait.

        Args:
            trait_name: Name of the trait
            trait_data: Trait data (string or dict with effects)
            source: Source of the trait ('species', 'lineage', 'class', etc.)
        """
        # Get description and apply any template substitutions
        description = (
            trait_data
            if isinstance(trait_data, str)
            else trait_data.get("description", "")
            if isinstance(trait_data, dict)
            else ""
        )

        # Apply scaling/template substitutions for class features
        if (
            source == "class"
            and isinstance(trait_data, dict)
            and "scaling" in trait_data
        ):
            description = self._apply_feature_scaling(
                description, trait_data["scaling"]
            )

        # Skip features that are just choice placeholders
        # 1. Features with choices dict but minimal description
        if isinstance(trait_data, dict) and "choices" in trait_data:
            if (
                not description
                or len(description) < 20
                or description.lower().startswith("choose")
            ):
                # Still apply effects if present
                effects = trait_data.get("effects", [])
                for effect in effects:
                    self._apply_effect(effect, trait_name, source)
                return

        # 2. Simple string features that start with "Choose"
        if isinstance(description, str) and description.lower().startswith("choose"):
            return

        # Map source to feature category and get descriptive source name
        category_map = {
            "species": "species",
            "lineage": "lineage",
            "class": "class",
            "subclass": "subclass",
            "class_choice": "class",
        }
        category = category_map.get(source, "class")

        # Get descriptive source name
        if source == "class":
            source_display = self.character_data.get("class", "Class")
        elif source == "subclass":
            source_display = f"{self.character_data.get('subclass', 'Subclass')}"
        elif source == "species":
            source_display = self.character_data.get("species", "Species")
        elif source == "lineage":
            source_display = self.character_data.get("lineage", "Lineage")
        else:
            source_display = source

        # Check if this feature has a choice and if a choice was made
        display_name = trait_name
        if isinstance(trait_data, dict) and "choices" in trait_data:
            # Look up the choice from choices_made
            choice_config = trait_data["choices"]
            choice_key = choice_config.get("name", trait_name.lower().replace(" ", "_"))

            # Check various possible choice keys (including species_trait_ prefix)
            choice_value = None
            for possible_key in [
                choice_key,
                trait_name,
                trait_name.lower().replace(" ", "_"),
                f"species_trait_{trait_name}",
                f"species_trait_{trait_name.replace(' ', '_')}",
            ]:
                if possible_key in self.character_data["choices_made"]:
                    choice_value = self.character_data["choices_made"][possible_key]
                    break

            # Append choice to display name
            if choice_value:
                if isinstance(choice_value, list):
                    display_name = f"{trait_name}: {', '.join(choice_value)}"
                else:
                    display_name = f"{trait_name}: {choice_value}"

                # Replace base description with specific choice description
                choice_source = choice_config.get("source", {})
                source_type_str = choice_source.get("type", "")

                if source_type_str == "external":
                    # Load description from external file
                    external_file = choice_source.get("file", "")
                    choice_list_name = choice_source.get("list", "")

                    if external_file and choice_list_name:
                        try:
                            external_path = self.data_dir / external_file
                            if external_path.exists():
                                with open(external_path, "r") as f:
                                    external_data = json.load(f)
                                    choice_list = external_data.get(
                                        choice_list_name, {}
                                    )

                                    # Handle both single choice and list of choices
                                    if isinstance(choice_value, list):
                                        # For multiple choices, combine descriptions
                                        descriptions = []
                                        for cv in choice_value:
                                            if isinstance(choice_list.get(cv), dict):
                                                descriptions.append(
                                                    choice_list[cv].get(
                                                        "description", ""
                                                    )
                                                )
                                            elif isinstance(choice_list.get(cv), str):
                                                descriptions.append(choice_list[cv])
                                        if descriptions:
                                            description = "\n\n".join(descriptions)
                                    else:
                                        # Single choice
                                        if isinstance(
                                            choice_list.get(choice_value), dict
                                        ):
                                            choice_desc = choice_list[choice_value].get(
                                                "description", ""
                                            )
                                            if choice_desc:
                                                description = choice_desc
                                        elif isinstance(
                                            choice_list.get(choice_value), str
                                        ):
                                            description = choice_list[choice_value]
                        except (json.JSONDecodeError, IOError) as e:
                            print(
                                f"Warning: Could not load choice description from {external_file}: {e}"
                            )

                elif source_type_str == "internal":
                    # Load description from internal list
                    internal_list_name = choice_source.get("list", "")

                    if internal_list_name and isinstance(trait_data, dict):
                        internal_list = trait_data.get(internal_list_name, {})

                        # Handle both single choice and list of choices
                        if isinstance(choice_value, list):
                            descriptions = []
                            for cv in choice_value:
                                if isinstance(internal_list.get(cv), dict):
                                    descriptions.append(
                                        internal_list[cv].get("description", "")
                                    )
                                elif isinstance(internal_list.get(cv), str):
                                    descriptions.append(internal_list[cv])
                            if descriptions:
                                description = "\n\n".join(descriptions)
                        else:
                            # Single choice
                            if isinstance(internal_list.get(choice_value), dict):
                                choice_desc = internal_list[choice_value].get(
                                    "description", ""
                                )
                                if choice_desc:
                                    description = choice_desc
                            elif isinstance(internal_list.get(choice_value), str):
                                description = internal_list[choice_value]

        # For Spellcasting feature, we'll append cantrips later when choices are made
        # Check if cantrips have already been chosen
        if trait_name == "Spellcasting":
            spellcasting_choices = self.character_data["choices_made"].get(
                "Spellcasting", []
            )
            if isinstance(spellcasting_choices, list) and spellcasting_choices:
                description += f"\n\nCantrips Known: {', '.join(spellcasting_choices)}"

        # Check for grant_spell effects and append spell list to description
        if isinstance(trait_data, dict) and "effects" in trait_data:
            spells_by_level = {}  # Group spells by their min_level
            current_level = self.character_data.get("level", 1)

            for effect in trait_data.get("effects", []):
                if effect.get("type") == "grant_spell":
                    spell_name = effect.get("spell")
                    min_level = effect.get("min_level", 1)
                    if spell_name:
                        if min_level not in spells_by_level:
                            spells_by_level[min_level] = []
                        spells_by_level[min_level].append(spell_name)

            if spells_by_level:
                # Check if spells are granted at multiple levels
                if len(spells_by_level) > 1:
                    # Create an HTML table format for multiple levels
                    description += "\n\n"
                    description += (
                        '<table class="table table-sm table-bordered mt-2">\n'
                    )
                    description += "<thead><tr><th>Character Level</th><th>Spells</th></tr></thead>\n"
                    description += "<tbody>\n"
                    for level in sorted(spells_by_level.keys()):
                        spells = ", ".join(spells_by_level[level])
                        if current_level >= level:
                            row_class = "table-success"
                            marker = "✓ "
                        else:
                            row_class = "table-secondary"
                            marker = "🔒 "
                        description += f'<tr class="{row_class}"><td>{level}</td><td>{marker}{spells}</td></tr>\n'
                    description += "</tbody>\n</table>"
                else:
                    # Single level, use simple format
                    all_spells = []
                    for spells in spells_by_level.values():
                        all_spells.extend(spells)
                    description += (
                        f"\n\nSpells Always Prepared: {', '.join(all_spells)}"
                    )

        # Add to features dict
        feature_entry = {
            "name": display_name,
            "description": description,
            "source": source_display,
        }

        # Add level information if provided (for class/subclass features)
        if level is not None:
            feature_entry["level"] = level

        # Check if feature already exists (avoid duplicates)
        if not any(
            f["name"].startswith(trait_name)
            for f in self.character_data["features"][category]
        ):
            self.character_data["features"][category].append(feature_entry)

        # If trait_data is just a string, no effects to apply
        if isinstance(trait_data, str):
            return

        # If trait_data is a dict, check for effects
        if isinstance(trait_data, dict):
            effects = trait_data.get("effects", [])
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
        level = self.character_data.get("level", 1)

        for var_name, scale_list in scaling.items():
            # Find the appropriate value for current level
            value = None
            for scale_entry in scale_list:
                min_level = scale_entry.get("min_level", 1)
                if level >= min_level:
                    value = scale_entry.get("value")

            # Replace template variable
            if value is not None:
                description = description.replace(f"{{{var_name}}}", str(value))

        return description

    def _apply_effect(self, effect: Dict[str, Any], source_name: str, source_type: str):
        """
        Apply a single effect from the effects system.

        Args:
            effect: Effect dictionary with 'type' and other parameters
            source_name: Name of the feature/trait providing the effect
            source_type: Type of source ('species', 'lineage', 'class', etc.)
        """
        effect_type = effect.get("type")

        if effect_type == "grant_cantrip":
            spell_name = effect.get("spell")
            counts_against_limit = effect.get("counts_against_limit", False)

            if spell_name:
                # Map source_type to actual display name
                if source_type == "species":
                    display_source = self.character_data.get("species", source_name)
                elif source_type == "lineage":
                    display_source = self.character_data.get("lineage", source_name)
                elif source_type == "class":
                    display_source = self.character_data.get("class", source_name)
                elif source_type == "subclass":
                    display_source = self.character_data.get("subclass", source_name)
                else:
                    display_source = source_name

                # Add to always_prepared dict with metadata
                self.character_data["spells"]["always_prepared"][spell_name] = {
                    "level": 0,
                    "source": display_source,
                    "always_prepared": True,
                    "counts_against_limit": counts_against_limit,
                }

                # Also track in spell_metadata for compatibility
                self.character_data["spell_metadata"][spell_name] = {
                    "source": display_source,
                    "always_prepared": True,
                    "once_per_day": False,
                    "counts_against_limit": counts_against_limit,
                }

        elif effect_type == "grant_cantrip_choice":
            # This effect requires a choice to be made - store for later processing
            # The choice handling will add the cantrip when the choice is made
            pass  # Handled by choice resolution system

        elif effect_type == "grant_spell":
            spell_name = effect.get("spell")
            min_level = effect.get("min_level", 1)
            counts_against_limit = effect.get("counts_against_limit", False)

            if spell_name and self.character_data["level"] >= min_level:
                # Load spell definition to get actual spell level
                spell_def = self._load_spell_definition(spell_name)
                spell_level = spell_def.get("level", 1)

                # Map source_type to actual name for display
                if source_type == "species":
                    display_source = self.character_data.get("species", source_name)
                elif source_type == "lineage":
                    display_source = self.character_data.get("lineage", source_name)
                elif source_type == "class":
                    display_source = self.character_data.get("class", source_name)
                elif source_type == "subclass":
                    display_source = self.character_data.get("subclass", source_name)
                elif source_type == "background":
                    display_source = self.character_data.get("background", source_name)
                else:
                    display_source = source_name

                # Determine if spell is 1/day (for species/lineage spells)
                once_per_day = source_type in ["species", "lineage"]

                # Add to always_prepared dict with metadata
                self.character_data["spells"]["always_prepared"][spell_name] = {
                    "level": spell_level,
                    "source": display_source,
                    "always_prepared": True,
                    "once_per_day": once_per_day,
                    "counts_against_limit": counts_against_limit,
                }

                # Also track in spell_metadata for compatibility
                self.character_data["spell_metadata"][spell_name] = {
                    "source": display_source,
                    "source_type": source_type,
                    "once_per_day": once_per_day,
                    "always_prepared": True,
                    "counts_against_limit": counts_against_limit,
                }

        elif effect_type == "grant_weapon_proficiency":
            proficiencies = effect.get("proficiencies", [])
            for prof in proficiencies:
                if prof not in self.character_data["proficiencies"]["weapons"]:
                    self.character_data["proficiencies"]["weapons"].append(prof)
                    # Track the source of this weapon proficiency
                    if source_type == "species_choice":
                        source_display = self.character_data.get("species", source_name)
                    elif source_type in ["species", "lineage"]:
                        source_display = self.character_data.get("species", source_name)
                    else:
                        source_display = source_name
                    self.character_data["proficiency_sources"]["weapons"][prof] = (
                        source_display
                    )

        elif effect_type == "grant_armor_proficiency":
            proficiencies = effect.get("proficiencies", [])
            for prof in proficiencies:
                if prof not in self.character_data["proficiencies"]["armor"]:
                    self.character_data["proficiencies"]["armor"].append(prof)
                    # Track the source of this armor proficiency
                    if source_type == "species_choice":
                        source_display = self.character_data.get("species", source_name)
                    elif source_type in ["species", "lineage"]:
                        source_display = self.character_data.get("species", source_name)
                    else:
                        source_display = source_name
                    self.character_data["proficiency_sources"]["armor"][prof] = (
                        source_display
                    )

        elif effect_type == "grant_skill_proficiency":
            skills = effect.get("skills", [])
            for skill in skills:
                if skill not in self.character_data["proficiencies"]["skills"]:
                    self.character_data["proficiencies"]["skills"].append(skill)
                    # Track the source of this skill proficiency
                    if source_type == "species_choice":
                        # For species choices, use just the species name
                        source_display = self.character_data.get("species", source_name)
                    elif source_type in ["species", "lineage"]:
                        source_display = self.character_data.get("species", source_name)
                    else:
                        source_display = source_name
                    self.character_data["proficiency_sources"]["skills"][skill] = (
                        source_display
                    )

        elif effect_type == "grant_damage_resistance":
            damage_type = effect.get("damage_type")
            if damage_type and damage_type not in self.character_data["resistances"]:
                self.character_data["resistances"].append(damage_type)

        elif effect_type == "grant_darkvision":
            darkvision_range = effect.get("range", 60)
            if darkvision_range > self.character_data["darkvision"]:
                self.character_data["darkvision"] = darkvision_range

        elif effect_type == "increase_speed":
            speed_increase = effect.get("value", 0)
            self.character_data["speed"] += speed_increase

        elif effect_type == "ability_bonus":
            # Store ability bonuses for later calculation (like Thaumaturge)
            if "ability_bonuses" not in self.character_data:
                self.character_data["ability_bonuses"] = []

            bonus_info = {
                "ability": effect.get("ability"),
                "skills": effect.get("skills", []),
                "value": effect.get("value"),
                "minimum": effect.get("minimum", 0),
                "source": source_name,
            }
            self.character_data["ability_bonuses"].append(bonus_info)

        # Track applied effect
        self.applied_effects.append(
            {
                "type": effect_type,
                "source": source_name,
                "source_type": source_type,
                "effect": effect,
            }
        )

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
        if (
            self.character_data.get("class") != class_name
            or self.character_data.get("level") != level
        ):
            self._clear_class_features()

        self.character_data["class"] = class_name
        self.character_data["class_data"] = class_data
        self.character_data["level"] = level

        # Re-apply lineage traits if they exist (for level-based spells)
        if "_lineage_traits" in self.character_data:
            # Clear existing level-based spells first
            self.character_data["spells"]["known"] = {}
            # Re-apply with new level
            for trait_name, trait_data in self.character_data[
                "_lineage_traits"
            ].items():
                self._apply_trait_effects(trait_name, trait_data, "lineage")

        # Apply class features
        self._apply_class_features(class_data, level)

        # Re-apply subclass features if subclass exists
        if self.character_data.get("subclass"):
            subclass_data = self.character_data.get("subclass_data")
            if subclass_data:
                self._clear_subclass_features()
                self._apply_subclass_features(subclass_data, level)

        # Determine next step
        subclass_level = class_data.get("subclass_selection_level", 3)
        if level >= subclass_level:
            self.character_data["step"] = "subclass"
        else:
            self.character_data["step"] = "background"

        return True

    def _clear_class_features(self):
        """Clear all class-related features and effects before re-applying."""
        # Clear class features
        self.character_data["features"]["class"] = []

        # Reset proficiencies to base level (before class was added)
        self.character_data["proficiencies"]["saving_throws"] = []
        self.character_data["proficiencies"]["weapons"] = []
        self.character_data["proficiencies"]["armor"] = []

        # Clear applied effects from class source
        if hasattr(self, "applied_effects"):
            self.applied_effects = [
                e
                for e in self.applied_effects
                if e.get("source_type") not in ["class", "class_choice"]
            ]

    def _clear_subclass_features(self):
        """Clear all subclass-related features and effects before re-applying."""
        # Clear subclass features
        self.character_data["features"]["subclass"] = []

        # Clear applied effects from subclass source
        if hasattr(self, "applied_effects"):
            self.applied_effects = [
                e for e in self.applied_effects if e.get("source_type") != "subclass"
            ]

        # Clear subclass spells from prepared list
        spell_metadata = self.character_data.get("spell_metadata", {})
        prepared_spells = self.character_data["spells"]["prepared"]

        # Remove spells that were from subclass (using source_type)
        for spell_name in list(prepared_spells):
            if (
                spell_name in spell_metadata
                and spell_metadata[spell_name].get("source_type") == "subclass"
            ):
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
        if not self.character_data["class"]:
            return False

        subclass_data = self._load_subclass_data(
            self.character_data["class"], subclass_name
        )
        if not subclass_data:
            return False

        # If subclass is changing, clear existing subclass features first
        if (
            self.character_data.get("subclass")
            and self.character_data.get("subclass") != subclass_name
        ):
            self._clear_subclass_features()

        self.character_data["subclass"] = subclass_name
        self.character_data["subclass_data"] = subclass_data

        # Apply subclass features for current level
        self._apply_subclass_features(subclass_data, self.character_data["level"])

        self.character_data["step"] = "background"
        return True

    def _apply_class_features(self, class_data: Dict[str, Any], level: int):
        """Apply class features up to the specified level."""
        # Saving throw proficiencies
        saving_throws = class_data.get("saving_throw_proficiencies", [])
        self.character_data["proficiencies"]["saving_throws"].extend(saving_throws)

        # Armor proficiencies
        armor_profs = class_data.get("armor_proficiencies", [])
        for prof in armor_profs:
            if prof not in self.character_data["proficiencies"]["armor"]:
                self.character_data["proficiencies"]["armor"].append(prof)

        # Weapon proficiencies
        weapon_profs = class_data.get("weapon_proficiencies", [])
        for prof in weapon_profs:
            if prof not in self.character_data["proficiencies"]["weapons"]:
                self.character_data["proficiencies"]["weapons"].append(prof)

        # Features by level
        features_by_level = class_data.get("features_by_level", {})

        # Ensure features_by_level is a dict
        if not isinstance(features_by_level, dict):
            print(
                f"Warning: features_by_level is not a dict for class {class_data.get('name')}: {type(features_by_level)}"
            )
            return

        for feat_level in range(1, level + 1):
            level_features = features_by_level.get(str(feat_level), {})

            # Ensure level_features is a dict
            if not isinstance(level_features, dict):
                print(
                    f"Warning: level_features at level {feat_level} is not a dict: {type(level_features)}"
                )
                continue

            for feature_name, feature_data in level_features.items():
                self._apply_trait_effects(
                    feature_name, feature_data, "class", feat_level
                )

    def _apply_subclass_features(self, subclass_data: Dict[str, Any], level: int):
        """Apply subclass features up to the specified level."""
        features_by_level = subclass_data.get("features_by_level", {})

        # Ensure features_by_level is a dict
        if not isinstance(features_by_level, dict):
            print(
                f"Warning: features_by_level is not a dict for subclass {subclass_data.get('name')}: {type(features_by_level)}"
            )
            return

        for feat_level_str, level_features in features_by_level.items():
            feat_level = int(feat_level_str)
            if feat_level <= level:
                # Ensure level_features is a dict
                if not isinstance(level_features, dict):
                    print(
                        f"Warning: level_features at level {feat_level_str} is not a dict: {type(level_features)}"
                    )
                    continue

                for feature_name, feature_data in level_features.items():
                    self._apply_trait_effects(
                        feature_name, feature_data, "subclass", feat_level
                    )

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

        self.character_data["background"] = background_name
        self.character_data["background_data"] = background_data

        # Apply background features
        self._apply_background_features(background_data)

        self.character_data["step"] = "abilities"
        return True

    def _apply_background_features(self, background_data: Dict[str, Any]):
        """Apply background features including skill proficiencies."""
        background_name = background_data.get(
            "name", self.character_data.get("background", "Unknown")
        )

        # Skill proficiencies
        skill_profs = background_data.get("skill_proficiencies", [])
        for skill in skill_profs:
            if skill not in self.character_data["proficiencies"]["skills"]:
                self.character_data["proficiencies"]["skills"].append(skill)
                # Track source
                self.character_data["proficiency_sources"]["skills"][skill] = (
                    background_name
                )

        # Tool proficiencies
        tool_profs = background_data.get("tool_proficiencies", [])
        for tool in tool_profs:
            if tool not in self.character_data["proficiencies"]["tools"]:
                self.character_data["proficiencies"]["tools"].append(tool)

        # Languages - can be either a list or a number
        languages = background_data.get("languages", [])
        if isinstance(languages, list):
            for lang in languages:
                if lang not in self.character_data["proficiencies"]["languages"]:
                    self.character_data["proficiencies"]["languages"].append(lang)
        elif isinstance(languages, int):
            # Store that they need to choose N languages
            self.character_data["choices_made"]["language_choices_needed"] = languages

        # Background features
        features = background_data.get("features", {})

        # Ensure features is a dict
        if not isinstance(features, dict):
            print(
                f"Warning: background features is not a dict for {background_name}: {type(features)}"
            )
            features = {}

        for feature_name, feature_data in features.items():
            description = (
                feature_data
                if isinstance(feature_data, str)
                else feature_data.get("description", "")
            )
            feature_entry = {
                "name": feature_name,
                "description": description,
                "source": background_name,
            }
            if not any(
                f["name"] == feature_name
                for f in self.character_data["features"]["background"]
            ):
                self.character_data["features"]["background"].append(feature_entry)

        # Background feat
        feat = background_data.get("feat")
        if feat:
            feat_entry = {
                "name": feat,
                "description": f"Feat granted by {background_name} background.",
                "source": background_name,
            }
            if not any(
                f["name"] == feat for f in self.character_data["features"]["feats"]
            ):
                self.character_data["features"]["feats"].append(feat_entry)

    def _process_equipment_selections(
        self, equipment_selections: Dict[str, str]
    ) -> bool:
        """
        Process equipment selections to generate actual equipment items.

        Args:
            equipment_selections: Dict with 'class_equipment' and 'background_equipment' choices

        Returns:
            True if equipment was processed successfully
        """
        if not isinstance(equipment_selections, dict):
            return False

        # Initialize equipment if not already present
        if (
            "equipment" not in self.character_data
            or self.character_data["equipment"] is None
        ):
            self.character_data["equipment"] = {
                "weapons": [],
                "armor": [],
                "items": [],
                "gold": 0,
            }

        # Check if equipment has already been processed to avoid duplicates
        equipment = self.character_data["equipment"]
        has_class_equipment = any(
            item.get("source") == "Class"
            for item in equipment["weapons"] + equipment["armor"] + equipment["items"]
        )
        has_background_equipment = any(
            item.get("source") == "Background"
            for item in equipment["weapons"] + equipment["armor"] + equipment["items"]
        )

        # Process class equipment selection
        class_choice = equipment_selections.get("class_equipment")
        if (
            class_choice
            and self.character_data.get("class_data")
            and not has_class_equipment
        ):
            class_equipment = self.character_data["class_data"].get(
                "starting_equipment", {}
            )
            if class_choice in class_equipment:
                option_data = class_equipment[class_choice]
                self._add_equipment_from_option(option_data, "Class")

        # Process background equipment selection
        background_choice = equipment_selections.get("background_equipment")
        if (
            background_choice
            and self.character_data.get("background_data")
            and not has_background_equipment
        ):
            background_equipment = self.character_data["background_data"].get(
                "starting_equipment", {}
            )
            if background_choice in background_equipment:
                option_data = background_equipment[background_choice]
                self._add_equipment_from_option(option_data, "Background")

        return True

    def _add_equipment_from_option(self, option_data: Dict[str, Any], source: str):
        """Add equipment items from a starting equipment option."""
        # Add gold
        gold = option_data.get("gold", 0)
        if gold > 0:
            self.character_data["equipment"]["gold"] += gold

        # Add items with categorization
        items = option_data.get("items", [])
        for item in items:
            item_name_lower = item.lower()

            # Check if item is a weapon by looking it up in weapon data
            weapon_props = self._get_weapon_properties(item)
            if weapon_props:
                # Item exists in weapons.json, so it's a weapon
                self.character_data["equipment"]["weapons"].append(
                    {"name": item, "source": source, "properties": weapon_props}
                )
            elif any(
                armor_type in item_name_lower
                for armor_type in [
                    "armor",
                    "mail",
                    "leather",
                    "chain",
                    "scale",
                    "plate",
                    "shield",
                ]
            ):
                self.character_data["equipment"]["armor"].append(
                    {"name": item, "source": source}
                )
            else:
                self.character_data["equipment"]["items"].append(
                    {"name": item, "source": source}
                )

    def _load_weapon_data(self) -> Dict[str, Any]:
        """Load weapon data from weapons.json."""
        weapons_file = self.data_dir / "equipment" / "weapons.json"
        try:
            with open(weapons_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Warning: Could not load weapons data from {weapons_file}")
            return {}

    def _load_armor_data(self) -> Dict[str, Any]:
        """Load armor data from armor.json."""
        armor_file = self.data_dir / "equipment" / "armor.json"
        try:
            with open(armor_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Warning: Could not load armor data from {armor_file}")
            return {}

    def _spell_list_contains(self, spell_list: list, spell_name: str) -> bool:
        """
        Check if a spell list contains a spell by name.
        Handles both string and dict spell formats.
        """
        for spell in spell_list:
            if isinstance(spell, dict) and spell.get("name") == spell_name:
                return True
            elif isinstance(spell, str) and spell == spell_name:
                return True
        return False

    def _load_spell_definition(self, spell_name: str) -> Dict[str, Any]:
        """Load spell definition from spell definitions directory."""
        # Check cache first
        if spell_name in self._spell_definitions_cache:
            return self._spell_definitions_cache[spell_name]

        # Convert spell name to filename format (lowercase with underscores)
        filename = spell_name.lower().replace(" ", "_").replace("'", "")
        spell_file = self.data_dir / "spells" / "definitions" / f"{filename}.json"

        try:
            with open(spell_file, "r") as f:
                spell_data = json.load(f)
                # Convert components list to string for template display
                if "components" in spell_data and isinstance(
                    spell_data["components"], list
                ):
                    spell_data["components"] = ", ".join(spell_data["components"])
                # Cache it
                self._spell_definitions_cache[spell_name] = spell_data
                return spell_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Return minimal spell object if file not found
            print(
                f"Warning: Could not load spell definition for '{spell_name}' from {spell_file}: {e}"
            )
            return {
                "name": spell_name,
                "level": 0,
                "description": "Spell definition not available.",
                "source": "Unknown",
            }

    def _get_weapon_properties(self, weapon_name: str) -> Dict[str, Any]:
        """Get weapon properties from loaded weapon data."""
        if weapon_name in self._weapon_data:
            return self._weapon_data[weapon_name].copy()
        else:
            print(f"Warning: Weapon '{weapon_name}' not found in weapon data")
            return {}

    def calculate_ac_options(self) -> List[Dict[str, Any]]:
        """
        Calculate all possible AC combinations based on available equipment.
        Returns AC options sorted from highest to lowest AC.
        """
        ac_options = []

        # Get character data
        abilities = self.calculate_processed_ability_scores()
        dex_mod = abilities.get("dexterity", {}).get("modifier", 0)
        equipment = self.character_data.get("equipment")
        proficiencies = self.character_data.get("proficiencies", {}).get("armor", [])

        # Check for bonus_ac effects (e.g., Defense fighting style)
        ac_bonus = 0
        ac_bonus_sources = []
        if hasattr(self, "applied_effects"):
            for effect_wrapper in self.applied_effects:
                if effect_wrapper.get("type") == "bonus_ac":
                    effect = effect_wrapper.get("effect", {})
                    effect.get("condition", "")
                    # Check if condition is met (we'll verify wearing armor per option)
                    # For now, just track the bonus
                    ac_bonus += effect.get("value", 0)
                    source_name = effect_wrapper.get("source", "Unknown")
                    ac_bonus_sources.append(source_name)

        # Handle case where equipment is None (like in tests)
        if equipment is None:
            # Just return unarmored AC
            unarmored_ac = 10 + dex_mod
            return [
                {
                    "ac": unarmored_ac,
                    "armor": None,
                    "shield": False,
                    "formula": f"10 + Dex modifier ({dex_mod})",
                    "notes": [],
                    "equipped_armor": None,
                }
            ]

        # Available armor pieces
        armor_items = equipment.get("armor", [])
        has_shield = any(item.get("name") == "Shield" for item in armor_items)

        # Get all armor (non-shield) pieces
        armor_pieces = [item for item in armor_items if item.get("name") != "Shield"]

        # Calculate AC for each armor combination
        for armor in armor_pieces:
            armor_name = armor.get("name")
            if armor_name and armor_name in self._armor_data:
                armor_data = self._armor_data[armor_name]
                ac_option = self._calculate_armor_ac(
                    armor_data, dex_mod, has_shield, proficiencies, armor_name
                )
                ac_option["equipped_armor"] = armor_name

                # Apply bonus_ac if wearing armor
                if ac_bonus > 0:
                    ac_option["ac"] += ac_bonus
                    for source in ac_bonus_sources:
                        ac_option["notes"].append(f"+{ac_bonus} from {source}")

                ac_options.append(ac_option)

        # Add unarmored AC option
        unarmored_ac = 10 + dex_mod
        shield_bonus = 2 if has_shield and "Shields" in proficiencies else 0
        total_unarmored = unarmored_ac + shield_bonus

        formula_parts = [f"10 + Dex modifier ({dex_mod})"]
        if shield_bonus:
            formula_parts.append(f"Shield ({shield_bonus})")

        unarmored_option = {
            "ac": total_unarmored,
            "armor": None,
            "shield": has_shield,
            "formula": " + ".join(formula_parts),
            "notes": [],
            "equipped_armor": None,
        }
        ac_options.append(unarmored_option)

        # Add notes for unproficient equipment
        for option in ac_options:
            if option["equipped_armor"]:
                armor_data = self._armor_data.get(option["equipped_armor"], {})
                required_prof = armor_data.get("proficiency_required")
                if required_prof and required_prof not in proficiencies:
                    option["notes"].append(f"Not proficient with {required_prof}")

            if has_shield and "Shields" not in proficiencies:
                option["notes"].append("Not proficient with Shields")

        # Sort by AC (highest first)
        ac_options.sort(key=lambda x: x["ac"], reverse=True)

        return ac_options

    def _calculate_armor_ac(
        self,
        armor_data: Dict[str, Any],
        dex_mod: int,
        has_shield: bool,
        proficiencies: List[str],
        armor_name: str = None,
    ) -> Dict[str, Any]:
        """Calculate AC for a specific armor."""
        ac_base = armor_data.get("ac_base", 10)
        category = armor_data.get("category", "")

        # Calculate DEX modifier contribution based on armor type
        if "Light" in category:
            # Light armor: full DEX modifier
            dex_bonus = dex_mod
        elif "Medium" in category:
            # Medium armor: DEX modifier max 2
            dex_bonus = min(dex_mod, 2)
        else:
            # Heavy armor: no DEX modifier
            dex_bonus = 0

        # Base AC calculation
        total_ac = ac_base + dex_bonus

        # Shield bonus
        shield_bonus = 0
        if has_shield and "Shields" in proficiencies:
            shield_bonus = 2
            total_ac += shield_bonus

        # Build formula string
        formula_parts = []
        if ac_base != 10:
            formula_parts.append(f"Armor base ({ac_base})")
        if dex_bonus > 0:
            formula_parts.append(f"Dex modifier ({dex_bonus})")
        if shield_bonus > 0:
            formula_parts.append(f"Shield ({shield_bonus})")

        formula = " + ".join(formula_parts) if formula_parts else str(total_ac)

        return {
            "ac": total_ac,
            "armor": armor_name,
            "shield": has_shield,
            "formula": formula,
            "notes": [],
        }

    # ==================== Ability Score Methods ====================

    def set_abilities(
        self,
        scores: Dict[str, int],
        species_bonuses: Optional[Dict[str, int]] = None,
        background_bonuses: Optional[Dict[str, int]] = None,
    ) -> bool:
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
        self.character_data["abilities"] = {
            "base": scores,
            "species_bonuses": species_bonuses or {},
            "background_bonuses": background_bonuses or {},
            "final": self.ability_scores.final_scores,
        }

        self.character_data["step"] = "complete"
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
        self.character_data["choices_made"][choice_key] = choice_value

        # Apply based on choice type
        choice_key_lower = choice_key.lower()

        # Core character selections
        if choice_key_lower == "species":
            return self.set_species(choice_value)
        elif choice_key_lower == "lineage":
            return self.set_lineage(choice_value)
        elif choice_key_lower == "class":
            return self.set_class(choice_value, self.character_data.get("level", 1))
        elif choice_key_lower == "subclass":
            return self.set_subclass(choice_value)
        elif choice_key_lower == "background":
            return self.set_background(choice_value)
        elif choice_key_lower == "level":
            current_class = self.character_data.get("class")
            if current_class:
                return self.set_class(current_class, int(choice_value))
            self.character_data["level"] = int(choice_value)
            return True

        # Ability scores
        elif choice_key_lower in ["ability_scores", "abilities"]:
            if isinstance(choice_value, dict):
                return self.set_abilities(choice_value)
            elif choice_value == "standard_array_recommended":
                # Get the recommended ability scores from class data
                class_data = self.character_data.get("class_data", {})
                standard_array = class_data.get("standard_array_assignment")
                if standard_array:
                    return self.set_abilities(standard_array)
            return True
        elif choice_key_lower == "ability_scores_method":
            # Handle "recommended" or "manual" ability score method
            if choice_value == "recommended":
                # Use the predefined standard_array_assignment from class data
                class_data = self.character_data.get("class_data", {})

                if "standard_array_assignment" in class_data:
                    return self.set_abilities(class_data["standard_array_assignment"])
                else:
                    print(
                        f"Warning: Class {class_data.get('name', 'Unknown')} missing standard_array_assignment"
                    )
                    return False
            return True
        elif choice_key_lower == "background_ability_score_assignment":
            # Apply background ability bonuses
            if isinstance(choice_value, dict):
                self.ability_scores.apply_background_bonuses(choice_value)
                # Update character_data so it persists across session save/restore
                if "abilities" not in self.character_data:
                    self.character_data["abilities"] = {}
                self.character_data["abilities"]["background_bonuses"] = choice_value
            return True
        elif choice_key_lower == "background_bonuses":
            # Apply background ability bonuses (alternate key name)
            if isinstance(choice_value, dict):
                self.ability_scores.apply_background_bonuses(choice_value)
                # Update character_data so it persists across session save/restore
                if "abilities" not in self.character_data:
                    self.character_data["abilities"] = {}
                self.character_data["abilities"]["background_bonuses"] = choice_value
            return True
        elif choice_key_lower == "background_bonuses_method":
            # Handle "suggested" background bonuses
            if choice_value == "suggested":
                background_data = self.character_data.get("background_data", {})
                if background_data:
                    asi_data = background_data.get("ability_score_increase", {})
                    suggested = asi_data.get("suggested", {})
                    if suggested:
                        self.ability_scores.apply_background_bonuses(suggested)
            return True

        # Languages
        elif choice_key_lower == "languages":
            if isinstance(choice_value, list):
                # Add languages that aren't already known
                for lang in choice_value:
                    if lang not in self.character_data["proficiencies"]["languages"]:
                        self.character_data["proficiencies"]["languages"].append(lang)
            return True

        # Skills
        elif choice_key_lower in ["skill_choices", "skills"]:
            if isinstance(choice_value, list):
                for skill in choice_value:
                    if skill not in self.character_data["proficiencies"]["skills"]:
                        self.character_data["proficiencies"]["skills"].append(skill)
                        # Track that this came from class selection
                        class_name = self.character_data.get("class", "Class")
                        self.character_data["proficiency_sources"]["skills"][skill] = (
                            class_name
                        )
            return True

        # Spells - Legacy handler (cantrip selection removed from creation wizard)
        elif choice_key_lower == "spellcasting":
            # Old system: cantrips were selected during character creation
            # New system: cantrips are managed post-creation via "Manage Spells"
            # This handler is kept for backwards compatibility with old saved characters
            # but does nothing for new characters
            return True

        # Spell selections - restore user-selected prepared spells
        elif choice_key_lower == "spell_selections":
            if isinstance(choice_value, dict):
                # Restore prepared cantrips
                cantrips = choice_value.get("cantrips", [])
                if isinstance(cantrips, list):
                    for cantrip in cantrips:
                        self.character_data["spells"]["prepared"]["cantrips"][
                            cantrip
                        ] = {}

                # Restore prepared spells
                spells = choice_value.get("spells", [])
                if isinstance(spells, list):
                    for spell in spells:
                        self.character_data["spells"]["prepared"]["spells"][spell] = {}

                # Restore background spells if any
                bg_cantrips = choice_value.get("background_cantrips", [])
                if isinstance(bg_cantrips, list):
                    for cantrip in bg_cantrips:
                        self.character_data["spells"]["background_spells"][cantrip] = {
                            "level": 0
                        }

                bg_spells = choice_value.get("background_spells", [])
                if isinstance(bg_spells, list):
                    for spell in bg_spells:
                        self.character_data["spells"]["background_spells"][spell] = {
                            "level": 1
                        }
            return True

        # Weapon Mastery - removed from creation wizard, managed post-creation
        elif choice_key_lower == "weapon mastery":
            # Weapon masteries are managed post-creation via "Manage Masteries"
            # This handler is kept for backwards compatibility with old saved characters
            # but does nothing for new characters
            return True

        # Weapon mastery selections - restore user-selected masteries
        elif choice_key_lower == "weapon_mastery_selections":
            if isinstance(choice_value, list):
                self.character_data["weapon_masteries"]["selected"] = choice_value
            return True

        # Nested bonus choices (e.g., Thaumaturge_bonus_cantrip)
        elif "_bonus_cantrip" in choice_key_lower:
            # Extract parent feature name (e.g., "Thaumaturge" from "Thaumaturge_bonus_cantrip")
            parent_name = (
                choice_key.replace("_bonus_cantrip", "").replace("_", " ").title()
            )
            class_name = self.character_data.get("class", "Class")

            # Add cantrip(s) to always_prepared dict (doesn't count against limit)
            cantrips_to_add = (
                choice_value if isinstance(choice_value, list) else [choice_value]
            )
            for cantrip in cantrips_to_add:
                # Add to always_prepared dict
                self.character_data["spells"]["always_prepared"][cantrip] = {
                    "level": 0,
                    "source": f"{parent_name} ({class_name})",
                    "always_prepared": True,
                    "counts_against_limit": False,
                }

                # Also track in spell_metadata for compatibility
                self.character_data["spell_metadata"][cantrip] = {
                    "source": f"{parent_name} ({class_name})",
                    "always_prepared": True,
                    "once_per_day": False,
                    "counts_against_limit": False,
                }

            # Find the parent feature and append the choice
            cantrip_display = (
                ", ".join(cantrips_to_add)
                if isinstance(choice_value, list)
                else choice_value
            )
            for category in ["class", "subclass", "species", "lineage"]:
                for feature in self.character_data["features"][category]:
                    # Look for features that start with "Divine Order: Thaumaturge" or just "Thaumaturge"
                    if parent_name in feature["name"]:
                        # Append the bonus cantrip info
                        bonus_text = f"\n\nBonus Cantrip: {cantrip_display}"
                        if bonus_text not in feature["description"]:
                            feature["description"] += bonus_text
                        return True
            return True

        # Character metadata
        elif choice_key_lower in ["character_name", "name"]:
            self.character_data["name"] = choice_value
            return True
        elif choice_key_lower == "alignment":
            self.character_data["alignment"] = choice_value
            return True

        # Equipment selections
        elif choice_key_lower == "equipment_selections":
            return self._process_equipment_selections(choice_value)

        # Generic choice - might be class feature choice
        # Try to find and apply effects from class/subclass data
        else:
            # Update feature display name if this is a choice for an existing feature
            self._update_feature_choice_display(choice_key, choice_value)

            # Check if this is a feature choice with effects
            if self.character_data.get("class_data"):
                self._apply_choice_effects(
                    choice_key, choice_value, self.character_data["class_data"]
                )
            if self.character_data.get("subclass_data"):
                self._apply_choice_effects(
                    choice_key, choice_value, self.character_data["subclass_data"]
                )
            if self.character_data.get("species_data"):
                self._apply_species_choice_effects(
                    choice_key, choice_value, self.character_data["species_data"]
                )
            if self.character_data.get("lineage_data"):
                self._apply_species_choice_effects(
                    choice_key, choice_value, self.character_data["lineage_data"]
                )
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
        if choice_key.startswith("species_trait_"):
            feature_base = choice_key.replace("species_trait_", "")

        # Normalize choice key to match feature names
        feature_name_variants = [
            feature_base,
            feature_base.replace("_", " ").title(),
            feature_base.replace("_", " "),
            choice_key,  # Also try original
            choice_key.replace("_", " ").title(),
            choice_key.replace("_", " "),
        ]

        # Try to find the choice-specific description from class/subclass data
        choice_description = None
        choice_scaling = None

        # First check for external sources
        for data_source_key in ["class_data", "subclass_data"]:
            source_data = self.character_data.get(data_source_key, {})
            if source_data and isinstance(source_data, dict):
                # Check features_by_level for external source references
                features_by_level = source_data.get("features_by_level", {})
                for level_features in features_by_level.values():
                    if not isinstance(level_features, dict):
                        continue

                    for feature_name, feature_data in level_features.items():
                        # Check if this feature name matches our choice_key
                        if feature_name in feature_name_variants and isinstance(
                            feature_data, dict
                        ):
                            choices_config = feature_data.get("choices", {})
                            if choices_config:
                                source_config = choices_config.get("source", {})

                                # Handle external source
                                if source_config.get("type") == "external":
                                    external_file = source_config.get("file")
                                    external_list = source_config.get("list")

                                    if external_file and external_list:
                                        try:
                                            external_path = (
                                                self.data_dir / external_file
                                            )
                                            if external_path.exists():
                                                import json

                                                with open(external_path, "r") as f:
                                                    external_data = json.load(f)
                                                choice_list = external_data.get(
                                                    external_list, {}
                                                )

                                                if choice_value in choice_list:
                                                    option_data = choice_list[
                                                        choice_value
                                                    ]
                                                    if isinstance(option_data, dict):
                                                        choice_description = (
                                                            option_data.get(
                                                                "description", ""
                                                            )
                                                        )
                                                        choice_scaling = (
                                                            option_data.get("scaling")
                                                        )
                                                    elif isinstance(option_data, str):
                                                        choice_description = option_data
                                                    break
                                        except (json.JSONDecodeError, IOError) as e:
                                            print(
                                                f"Warning: Could not load choice description from {external_file}: {e}"
                                            )

                        if choice_description:
                            break
                    if choice_description:
                        break
                if choice_description:
                    break

        # If not found in external sources, check internal lists
        if not choice_description:
            for data_source_key in ["class_data", "subclass_data"]:
                source_data = self.character_data.get(data_source_key, {})
                if source_data and isinstance(source_data, dict):
                    # Look for internal list (e.g., 'divine_orders', 'fighting_styles')
                    for data_key, data_value in source_data.items():
                        if isinstance(data_value, dict) and choice_value in data_value:
                            option_data = data_value[choice_value]
                            if isinstance(option_data, dict):
                                if "description" in option_data:
                                    choice_description = option_data["description"]
                                    choice_scaling = option_data.get("scaling")
                                    break
                            elif isinstance(option_data, str):
                                choice_description = option_data
                                break
                    if choice_description:
                        break

        # Search all feature categories for a matching feature
        for category in [
            "class",
            "subclass",
            "species",
            "lineage",
            "background",
            "feats",
        ]:
            for feature in self.character_data["features"][category]:
                # Check if this feature matches the choice
                for variant in feature_name_variants:
                    if feature["name"] == variant or feature["name"].startswith(
                        variant + ":"
                    ):
                        # Update the name to include the choice
                        base_name = (
                            variant
                            if feature["name"] == variant
                            else feature["name"].split(":")[0]
                        )
                        if isinstance(choice_value, list):
                            feature["name"] = f"{base_name}: {', '.join(choice_value)}"
                        else:
                            feature["name"] = f"{base_name}: {choice_value}"

                        # Update description if we found a choice-specific one
                        if choice_description:
                            # Apply scaling if present
                            if choice_scaling:
                                choice_description = self._apply_feature_scaling(
                                    choice_description, choice_scaling
                                )
                            feature["description"] = choice_description
                        return

    def _apply_choice_effects(
        self, choice_key: str, choice_value: Any, source_data: Dict[str, Any]
    ):
        """
        Look up and apply effects from a choice made in class/subclass features.

        Args:
            choice_key: The choice identifier (e.g., 'Divine Order', 'divine_order')
            choice_value: The chosen value (e.g., 'Thaumaturge')
            source_data: Class or subclass data to search for effects
        """
        if not isinstance(source_data, dict):
            print(
                f"WARNING: _apply_choice_effects received non-dict source_data: {type(source_data)}"
            )
            return

        # Normalize choice key for lookup
        choice_key.lower().replace(" ", "_")

        # First, check if there's a feature with choices that references an external file
        features_by_level = source_data.get("features_by_level", {})
        for level_features in features_by_level.values():
            if not isinstance(level_features, dict):
                continue

            for feature_name, feature_data in level_features.items():
                # Check if this feature matches our choice key
                if feature_name == choice_key and isinstance(feature_data, dict):
                    choices_config = feature_data.get("choices", {})
                    source_config = choices_config.get("source", {})

                    # Handle external source
                    if source_config.get("type") == "external":
                        external_file = source_config.get("file")
                        external_list = source_config.get("list")

                        if external_file and external_list:
                            # Load external data file
                            import json

                            external_path = self.data_dir / external_file
                            if external_path.exists():
                                try:
                                    with open(external_path, "r") as f:
                                        external_data = json.load(f)

                                    # Look for the choice value in the external list
                                    options_list = external_data.get(external_list, {})
                                    if choice_value in options_list:
                                        option_data = options_list[choice_value]
                                        if (
                                            isinstance(option_data, dict)
                                            and "effects" in option_data
                                        ):
                                            # Apply each effect
                                            for effect in option_data["effects"]:
                                                self._apply_effect(
                                                    effect, choice_value, "class_choice"
                                                )
                                            return
                                except (json.JSONDecodeError, IOError) as e:
                                    print(
                                        f"WARNING: Failed to load external file {external_file}: {e}"
                                    )

        # Fallback: Search for the choice in class data structures (internal references)
        # Common patterns: 'divine_orders', 'fighting_styles', etc.
        for data_key, data_value in source_data.items():
            if not isinstance(data_value, dict):
                continue

            # Check if this dict contains the chosen value
            if isinstance(choice_value, str) and choice_value in data_value:
                option_data = data_value[choice_value]
                if isinstance(option_data, dict) and "effects" in option_data:
                    # Apply each effect
                    for effect in option_data["effects"]:
                        self._apply_effect(effect, choice_value, "class_choice")
                    return

    def _apply_species_choice_effects(
        self, choice_key: str, choice_value: Any, source_data: Dict[str, Any]
    ):
        """
        Look up and apply effects from a choice made in species/lineage traits.

        Args:
            choice_key: The choice identifier (e.g., 'Keen Senses', 'Elven Lineage')
            choice_value: The chosen value (e.g., 'Insight', 'Intelligence')
            source_data: Species or lineage data to search for effects
        """
        if not isinstance(source_data, dict):
            print(
                f"WARNING: _apply_species_choice_effects received non-dict source_data: {type(source_data)}"
            )
            return

        # Look for traits with choice_effects
        traits = source_data.get("traits", {})
        if not isinstance(traits, dict):
            print(f"WARNING: traits is not a dict: {type(traits)}")
            return

        for trait_name, trait_data in traits.items():
            # Check if this trait matches the choice key and has choice_effects
            if (
                trait_name == choice_key
                and isinstance(trait_data, dict)
                and "choice_effects" in trait_data
            ):
                choice_effects = trait_data["choice_effects"]
                if choice_value in choice_effects:
                    effects = choice_effects[choice_value]
                    # Apply each effect
                    for effect in effects:
                        self._apply_effect(
                            effect, f"{trait_name}: {choice_value}", "species_choice"
                        )
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
        # Ensure choices is a dict
        if not isinstance(choices, dict):
            print(f"Error: apply_choices received non-dict type: {type(choices)}")
            print(f"Choices value: {choices}")
            return False

        # Apply choices in a specific order for dependencies
        order = [
            "character_name",
            "name",
            "level",
            "species",
            "lineage",
            "class",
            "subclass",
            "background",
            # Ability scores: only apply method if no explicit scores provided
            "ability_scores_method",  # This might apply standard array
            "ability_scores",
            "abilities",  # This overrides if present
            # Background bonuses must come after base ability scores
            "background_ability_score_assignment",
            "background_bonuses_method",
            "background_bonuses",
            "skill_choices",
            "skills",
            "spellcasting",
            "spell_selections",  # Restore spell selections after class/subclass applied
            "weapon mastery",
            "weapon_mastery_selections",  # Restore mastery selections after class applied
            "alignment",
        ]

        # Special handling: if both ability_scores and ability_scores_method exist,
        # skip ability_scores_method since ability_scores is the final value
        apply_method = (
            "ability_scores_method" in choices
            and "ability_scores" not in choices
            and "abilities" not in choices
        )

        # First pass: apply ordered choices
        for key in order:
            if key in choices:
                # Skip ability_scores_method if we have explicit ability_scores
                if key == "ability_scores_method" and not apply_method:
                    continue
                self.apply_choice(key, choices[key])

        # Second pass: apply remaining choices (class-specific features, etc.)
        for key, value in choices.items():
            if key not in order:
                self.apply_choice(key, value)

        return True

    # ==================== Calculation Methods ====================

    def calculate_ability_modifier(self, score: int) -> int:
        """Calculate ability modifier from score."""
        return math.floor((score - 10) / 2)

    def calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        if level >= 17:
            return 6
        elif level >= 13:
            return 5
        elif level >= 9:
            return 4
        elif level >= 5:
            return 3
        else:
            return 2

    def calculate_spellcasting_stats(self) -> Dict[str, Any]:
        """
        Calculate spellcasting statistics for spellcasting classes.

        Returns:
            Dictionary with spellcasting ability, save DC, attack bonus, and spell counts
        """
        stats = {
            "has_spellcasting": False,
            "spellcasting_ability": None,
            "spellcasting_modifier": 0,
            "spell_save_dc": 0,
            "spell_attack_bonus": 0,
            "spellcasting_type": None,
            "preparation_formula": None,
            "ritual_casting": False,
            # Cantrip tracking
            "cantrips_always_prepared": 0,
            "cantrips_to_prepare": 0,
            "max_cantrips_prepared": 0,
            # Spell tracking
            "spells_always_prepared": 0,
            "spells_prepared": 0,
            "max_spells_prepared": 0,
            # Background spells
            "background_cantrips_needed": 0,
            "background_cantrips_list": None,
            "background_spells_needed": 0,
            "background_spells_list": None,
            "background_spell_level": 1,
            # Available spells
            "available_cantrips": [],
            "available_spells": {},
        }

        # Get class data from character_data (already loaded)
        class_name = self.character_data.get("class")
        if not class_name:
            return stats

        class_data = self.character_data.get("class_data")
        if not class_data:
            # Try to load it if not available
            class_data = self._load_class_data(class_name)
            if not class_data:
                return stats

        # Check if class has spellcasting
        spellcasting_ability = class_data.get("spellcasting_ability")
        if not spellcasting_ability:
            return stats

        stats["has_spellcasting"] = True
        stats["spellcasting_ability"] = spellcasting_ability
        stats["spellcasting_type"] = class_data.get("spellcasting_type", "prepared")
        stats["preparation_formula"] = class_data.get("spell_preparation_formula")
        stats["ritual_casting"] = class_data.get("ritual_casting", False)

        # Get spellcasting modifier from abilities
        ability_key = spellcasting_ability.lower()
        abilities = self.calculate_processed_ability_scores()
        ability_data = abilities.get(ability_key, {})
        spellcasting_modifier = ability_data.get("modifier", 0)
        stats["spellcasting_modifier"] = spellcasting_modifier

        # Calculate spell save DC and attack bonus
        level = self.character_data.get("level", 1)
        proficiency_bonus = self.calculate_proficiency_bonus(level)
        stats["spell_save_dc"] = 8 + proficiency_bonus + spellcasting_modifier
        stats["spell_attack_bonus"] = proficiency_bonus + spellcasting_modifier

        # Count always prepared cantrips (from features, lineage, etc)
        always_prepared = self.character_data.get("spells", {}).get(
            "always_prepared", {}
        )
        if isinstance(always_prepared, dict):
            always_prepared_cantrips = [
                spell_name
                for spell_name, spell_data in always_prepared.items()
                if isinstance(spell_data, dict) and spell_data.get("level", 0) == 0
            ]
        else:
            always_prepared_cantrips = []
        stats["cantrips_always_prepared"] = len(always_prepared_cantrips)

        # Get max cantrips from class table
        cantrip_progression = class_data.get("cantrip_progression", {})
        if isinstance(cantrip_progression, dict):
            # Direct lookup in cantrip_progression dict
            max_cantrips_total = cantrip_progression.get(str(level), 0)
        else:
            # cantrip_progression is a string like "class_table" - use cantrips_by_level
            cantrips_by_level = class_data.get("cantrips_by_level", {})
            max_cantrips_total = cantrips_by_level.get(str(level), 0)

        # Calculate how many cantrips can be prepared (not counting always_prepared that don't count)
        always_prepared_that_count = sum(
            1
            for spell_data in always_prepared.values()
            if isinstance(spell_data, dict)
            and spell_data.get("level", 0) == 0
            and spell_data.get("counts_against_limit", True)
        )
        stats["max_cantrips_to_prepare"] = max(
            0, max_cantrips_total - always_prepared_that_count
        )
        stats["max_cantrips_prepared"] = max_cantrips_total

        # Count currently prepared cantrips
        prepared = self.character_data.get("spells", {}).get("prepared", {})
        if isinstance(prepared, dict):
            current_prepared_cantrips = list(prepared.get("cantrips", {}).keys())
        else:
            current_prepared_cantrips = []
        stats["cantrips_to_prepare"] = len(current_prepared_cantrips)

        # Count always prepared spells (from subclass, features)
        if isinstance(always_prepared, dict):
            always_prepared_spells = [
                spell_name
                for spell_name, spell_data in always_prepared.items()
                if isinstance(spell_data, dict) and spell_data.get("level", 0) > 0
            ]
        else:
            always_prepared_spells = []
        stats["spells_always_prepared"] = len(always_prepared_spells)

        # Calculate max prepared spells based on formula
        prepared_by_level = class_data.get("prepared_spells_by_level", {})
        if prepared_by_level:
            # Use class table
            max_spells_total = prepared_by_level.get(str(level), 0)
        elif stats["preparation_formula"]:
            # Use formula (e.g., "level + wisdom_modifier")
            formula = stats["preparation_formula"]
            if "level" in formula and "modifier" in formula:
                max_spells_total = max(1, level + spellcasting_modifier)
        else:
            max_spells_total = 0

        # Calculate how many spells can be prepared (not counting always_prepared that don't count)
        always_prepared_spells_that_count = sum(
            1
            for spell_data in always_prepared.values()
            if isinstance(spell_data, dict)
            and spell_data.get("level", 0) > 0
            and spell_data.get("counts_against_limit", True)
        )
        stats["max_spells_to_prepare"] = max(
            0, max_spells_total - always_prepared_spells_that_count
        )
        stats["max_spells_prepared"] = max_spells_total

        # Count currently prepared spells
        if isinstance(prepared, dict):
            current_prepared_spells = list(prepared.get("spells", {}).keys())
        else:
            current_prepared_spells = []
        stats["spells_prepared"] = len(current_prepared_spells)

        # Add template-friendly field names for display
        # Total cantrips known = always prepared + user selected
        stats["cantrips_known"] = (
            stats["cantrips_always_prepared"] + stats["cantrips_to_prepare"]
        )
        # Max cantrips = base slots + bonus cantrips that don't count against limit
        bonus_cantrips = stats["cantrips_always_prepared"] - always_prepared_that_count
        stats["max_cantrips"] = stats["max_cantrips_prepared"] + bonus_cantrips
        # Total spells prepared = always prepared + user selected
        total_spells_prepared = (
            stats["spells_always_prepared"] + stats["spells_prepared"]
        )
        stats["spells_prepared"] = total_spells_prepared  # Override with total
        # Max spells = base slots + bonus spells that don't count against limit
        bonus_spells = (
            stats["spells_always_prepared"] - always_prepared_spells_that_count
        )
        stats["max_prepared_spells"] = stats["max_spells_prepared"] + bonus_spells

        # Check for background spell requirements (e.g., Magic Initiate)
        background_data = self.character_data.get("background_data") or {}
        feat = background_data.get("feat") if background_data else None
        if feat and "Magic Initiate" in feat:
            # Extract spell list from feat name
            import re

            match = re.search(r"Magic Initiate \((\w+)\)", feat)
            if match:
                spell_list_class = match.group(1)
                stats["background_cantrips_needed"] = 2
                stats["background_cantrips_list"] = spell_list_class
                stats["background_spells_needed"] = 1
                stats["background_spells_list"] = spell_list_class
                stats["background_spell_level"] = 1

        # Load available spell lists for this class
        spell_list_path = (
            self.data_dir / "spells" / "class_lists" / f"{class_name.lower()}.json"
        )
        if spell_list_path.exists():
            try:
                import json

                with open(spell_list_path, "r") as f:
                    spell_list_data = json.load(f)

                # Get available cantrips
                available_cantrips = spell_list_data.get("cantrips", [])
                stats["available_cantrips"] = sorted(available_cantrips)

                # Get available spells by level
                spells_by_level = spell_list_data.get("spells_by_level", {})
                stats["available_spells"] = {
                    int(k): sorted(v) for k, v in spells_by_level.items()
                }

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load spell list for {class_name}: {e}")

        return stats

    def calculate_weapon_mastery_stats(self) -> Dict[str, Any]:
        """
        Calculate weapon mastery statistics for classes with weapon mastery.

        Returns:
            Dictionary with available weapons, max masteries, and current selections
        """
        stats = {
            "has_mastery": False,
            "available_weapons": [],
            "max_masteries": 0,
            "current_masteries": [],
        }

        # Get class data
        class_name = self.character_data.get("class")
        if not class_name:
            return stats

        class_data = self.character_data.get("class_data")
        if not class_data:
            class_data = self._load_class_data(class_name)
            if not class_data:
                return stats

        # Check if class has masterable_weapons
        masterable_weapons = class_data.get("masterable_weapons", [])
        if not masterable_weapons:
            return stats

        stats["has_mastery"] = True
        stats["available_weapons"] = sorted(masterable_weapons)

        # Get max masteries from masteries_by_level (like cantrips_by_level)
        masteries_by_level = class_data.get("masteries_by_level", {})
        level = self.character_data.get("level", 1)
        max_masteries = masteries_by_level.get(str(level), 0)

        stats["max_masteries"] = max_masteries

        # Get current selections
        current_masteries = self.character_data.get("weapon_masteries", {}).get(
            "selected", []
        )
        stats["current_masteries"] = current_masteries

        # Update character data for easy access
        self.character_data["weapon_masteries"]["available"] = stats[
            "available_weapons"
        ]
        self.character_data["weapon_masteries"]["max_count"] = stats["max_masteries"]

        return stats

    def calculate_processed_ability_scores(self) -> Dict[str, Dict[str, Any]]:
        """Calculate ability scores with modifiers and saving throws."""
        raw_scores = self.ability_scores.final_scores
        level = self.character_data.get("level", 1)
        proficiency_bonus = self.calculate_proficiency_bonus(level)

        # Get saving throw proficiencies
        class_data = self.character_data.get("class_data")
        if class_data is None:
            class_data = {}
        saving_throw_profs = class_data.get("saving_throw_proficiencies", [])

        processed_scores = {}
        for ability_name, score in raw_scores.items():
            ability_lower = ability_name.lower()
            modifier = self.calculate_ability_modifier(score)
            is_proficient = ability_name in saving_throw_profs
            saving_throw_bonus = modifier + (proficiency_bonus if is_proficient else 0)

            processed_scores[ability_lower] = {
                "score": score,
                "modifier": modifier,
                "saving_throw": saving_throw_bonus,
                "saving_throw_proficient": is_proficient,
            }

        return processed_scores

    def calculate_skills(self) -> Dict[str, Dict[str, Any]]:
        """Calculate skill bonuses with proficiency and expertise."""
        ability_scores = self.calculate_processed_ability_scores()
        # Get skill proficiencies from the correct location
        proficiencies = self.character_data.get("proficiencies", {})
        skill_proficiencies = proficiencies.get("skills", [])
        skill_expertise = self.character_data.get("skill_expertise", [])
        proficiency_sources = self.character_data.get("proficiency_sources", {})
        skill_sources = proficiency_sources.get("skills", {})
        proficiency_bonus = self.calculate_proficiency_bonus(
            self.character_data.get("level", 1)
        )

        skills = {}
        for skill, ability in self.skill_abilities.items():
            # Handle different skill name variants
            skill_name_variants = [
                skill,
                skill.replace("_", " ").title(),
                skill.title(),
                skill.replace("_", ""),
            ]

            # Check proficiency
            proficient = any(
                variant in skill_proficiencies for variant in skill_name_variants
            )
            expertise = any(
                variant in skill_expertise for variant in skill_name_variants
            )

            # Determine source of proficiency
            source = "None"
            if proficient:
                for variant in skill_name_variants:
                    if variant in skill_sources:
                        source = skill_sources[variant]
                        break
                else:
                    source = "Class"  # Default assumption

            # Calculate bonus
            ability_modifier = ability_scores[ability]["modifier"]
            prof_bonus = 0
            if expertise:
                prof_bonus = proficiency_bonus * 2
            elif proficient:
                prof_bonus = proficiency_bonus

            bonus = ability_modifier + prof_bonus

            skills[skill] = {
                "proficient": proficient,
                "expertise": expertise,
                "bonus": bonus,
                "modifier": bonus,
                "ability": ability,
                "source": source,
            }

        return skills

    def calculate_weapon_attacks(self) -> List[Dict[str, Any]]:
        """Calculate attack stats for all weapons in inventory."""
        attacks = []
        equipment = self.character_data.get("equipment") or {
            "weapons": [],
            "armor": [],
            "items": [],
            "gold": 0,
        }
        all_weapons = equipment.get("weapons", [])

        ability_scores = self.calculate_processed_ability_scores()
        proficiencies = self.character_data.get("proficiencies") or {
            "weapons": [],
            "armor": [],
            "skills": [],
        }
        weapon_profs = proficiencies.get("weapons", [])
        level = self.character_data.get("level", 1)
        proficiency_bonus = self.calculate_proficiency_bonus(level)

        for weapon in all_weapons:
            weapon_name = weapon.get("name")
            weapon_props = weapon.get("properties", {})

            # Determine ability modifier
            category = weapon_props.get("category", "")
            properties = weapon_props.get("properties", [])

            if "Finesse" in properties:
                str_mod = ability_scores.get("strength", {}).get("modifier", 0)
                dex_mod = ability_scores.get("dexterity", {}).get("modifier", 0)
                ability_mod = max(str_mod, dex_mod)
                ability_name = f"STR/DEX ({'STR' if str_mod >= dex_mod else 'DEX'})"
            elif "Ranged" in category:
                ability_mod = ability_scores.get("dexterity", {}).get("modifier", 0)
                ability_name = "DEX"
            else:
                ability_mod = ability_scores.get("strength", {}).get("modifier", 0)
                ability_name = "STR"

            # Check proficiency
            is_proficient = self._has_weapon_proficiency(weapon_props, weapon_profs)
            prof_bonus = proficiency_bonus if is_proficient else 0

            # Calculate attack bonus
            attack_bonus = ability_mod + prof_bonus

            # Apply bonus_attack effects from features (e.g., Archery fighting style)
            if hasattr(self, "applied_effects"):
                for effect_wrapper in self.applied_effects:
                    if effect_wrapper.get("type") == "bonus_attack":
                        # Get the actual effect data (nested inside 'effect' key)
                        effect = effect_wrapper.get("effect", {})

                        # Check if this effect applies to this weapon
                        weapon_property = effect.get("weapon_property")
                        if weapon_property:
                            # Check if weapon matches the property requirement
                            if weapon_property == "Ranged" and "Ranged" in category:
                                bonus = effect.get("value", 0)
                                attack_bonus += bonus
                            elif weapon_property in properties:
                                bonus = effect.get("value", 0)
                                attack_bonus += bonus
                        else:
                            # No condition, applies to all weapons
                            attack_bonus += effect.get("value", 0)

            # Calculate damage
            damage_dice = weapon_props.get("damage", "1d4")
            damage_bonus = ability_mod
            damage_type = weapon_props.get("damage_type", "Bludgeoning")

            # Apply bonus_damage effects from features (e.g., Dueling fighting style)
            # Track which bonuses apply (for excluding from dual-wield offhand)
            damage_notes = []
            dueling_bonus = 0  # Track Dueling separately for dual-wield exclusion

            if hasattr(self, "applied_effects"):
                for effect_wrapper in self.applied_effects:
                    if effect_wrapper.get("type") == "bonus_damage":
                        effect = effect_wrapper.get("effect", {})
                        condition = effect.get("condition", "")

                        # Check if condition is met for this weapon
                        applies = False
                        if condition == "one handed melee weapon":
                            # Dueling: Check weapon qualifies (one-handed melee)
                            # Display as if used alone (dual-wielding shown separately)
                            is_melee = "Ranged" not in category
                            is_one_handed = "Two-Handed" not in properties

                            if is_melee and is_one_handed:
                                applies = True
                                # Track Dueling bonus to exclude from dual-wield damage
                                dueling_bonus = effect.get("value", 0)
                        elif condition == "thrown weapon ranged attack":
                            # Thrown Weapon Fighting: Check if weapon has Thrown property
                            # The "Thrown" property means it can be used for ranged attacks
                            # (even if weapon category is "Melee")
                            # Property appears as "Thrown (range X/Y)" in the list
                            #
                            # IMPORTANT: Only apply to pure thrown weapons OR the separate
                            # throw damage calculation. For melee weapons with Thrown property,
                            # we'll show separate "throw_damage" field with this bonus.
                            is_melee = "Melee" in category
                            has_thrown = any("Thrown" in prop for prop in properties)

                            # Only apply to main damage if it's NOT a melee weapon
                            # (pure thrown weapons without melee option get the bonus on main damage)
                            if has_thrown and not is_melee:
                                applies = True
                        elif not condition:
                            # No condition, applies to all
                            applies = True

                        if applies:
                            bonus_value = effect.get("value", 0)
                            damage_bonus += bonus_value
                            source_name = effect_wrapper.get("source", "Unknown")
                            damage_notes.append(f"+{bonus_value} from {source_name}")

            # Format damage string with bonus if non-zero
            if damage_bonus > 0:
                damage_str = f"{damage_dice} + {damage_bonus}"
            elif damage_bonus < 0:
                damage_str = f"{damage_dice} - {abs(damage_bonus)}"
            else:
                damage_str = damage_dice

            # Check for Great Weapon Fighting (affects average damage for Two-Handed/Versatile weapons)
            has_gwf = False
            if hasattr(self, "applied_effects"):
                for effect_wrapper in self.applied_effects:
                    if effect_wrapper.get("type") == "great_weapon_fighting":
                        # Check if weapon qualifies (melee with Two-Handed or Versatile)
                        is_melee = "Ranged" not in category
                        is_two_handed = "Two-Handed" in properties
                        is_versatile = any("Versatile" in prop for prop in properties)

                        if is_melee and (is_two_handed or is_versatile):
                            has_gwf = True
                            damage_notes.append("Can reroll 1s and 2s (GWF)")
                            break

            # Calculate average damage (adjusted for GWF if applicable)
            avg_damage = self._calculate_average_damage(
                damage_dice, damage_bonus, has_gwf=has_gwf
            )
            avg_crit = self._calculate_average_damage(
                damage_dice, damage_bonus, is_crit=True, has_gwf=has_gwf
            )

            # Check for Thrown weapons that can also be used in melee
            # Show separate "Throw Damage" calculation
            throw_damage_str = None
            avg_throw_damage = None
            has_thrown = any("Thrown" in prop for prop in properties)
            is_melee = "Melee" in category

            if has_thrown and is_melee:
                # Calculate throw damage (without Dueling, with Thrown Weapon Fighting if active)
                throw_bonus = ability_mod
                throw_notes = []

                # Check for Thrown Weapon Fighting bonus
                if hasattr(self, "applied_effects"):
                    for effect_wrapper in self.applied_effects:
                        if effect_wrapper.get("type") == "bonus_damage":
                            effect = effect_wrapper.get("effect", {})
                            condition = effect.get("condition", "")

                            if condition == "thrown weapon ranged attack":
                                bonus_value = effect.get("value", 0)
                                throw_bonus += bonus_value
                                source_name = effect_wrapper.get("source", "Unknown")
                                throw_notes.append(f"+{bonus_value} from {source_name}")

                # Format throw damage string
                if throw_bonus > 0:
                    throw_damage_str = f"{damage_dice} + {throw_bonus}"
                elif throw_bonus < 0:
                    throw_damage_str = f"{damage_dice} - {abs(throw_bonus)}"
                else:
                    throw_damage_str = damage_dice

                avg_throw_damage = self._calculate_average_damage(
                    damage_dice, throw_bonus
                )

            # Check for Versatile weapons - show one-handed and two-handed damage
            versatile_die = None
            damage_one_handed_str = None
            damage_two_handed_str = None
            avg_one_handed = None
            avg_two_handed = None

            for prop in properties:
                if "Versatile" in prop:
                    # Parse versatile die (e.g., "Versatile (1d8)")
                    import re

                    match = re.search(r"\((\d+d\d+)\)", prop)
                    if match:
                        versatile_die = match.group(1)

                        # One-handed damage (use current damage calculation)
                        damage_one_handed_str = damage_str
                        avg_one_handed = avg_damage

                        # Two-handed damage (use versatile die with GWF if active)
                        two_handed_bonus = ability_mod

                        # Dueling doesn't apply when using two hands
                        # But other bonuses might apply
                        # For now, just use ability mod (no Dueling for two-handed)
                        if two_handed_bonus > 0:
                            damage_two_handed_str = (
                                f"{versatile_die} + {two_handed_bonus}"
                            )
                        elif two_handed_bonus < 0:
                            damage_two_handed_str = (
                                f"{versatile_die} - {abs(two_handed_bonus)}"
                            )
                        else:
                            damage_two_handed_str = versatile_die

                        # Apply GWF to two-handed versatile use
                        avg_two_handed = self._calculate_average_damage(
                            versatile_die, two_handed_bonus, has_gwf=has_gwf
                        )
                    break

            # Get weapon mastery if available
            mastery = weapon_props.get("mastery")

            attack_info = {
                "name": weapon_name,
                "attack_bonus": attack_bonus,
                "attack_bonus_display": f"+{attack_bonus}"
                if attack_bonus >= 0
                else str(attack_bonus),
                "damage": damage_str,
                "damage_type": damage_type,
                "avg_damage": avg_damage,
                "avg_crit": avg_crit,
                "properties": properties,
                "ability": ability_name,
                "proficient": is_proficient,
                "mastery": mastery,
                "icon": self._get_weapon_icon(weapon_name),
                "damage_notes": damage_notes,
                "_damage_dice": damage_dice,  # Store for offhand calculation
                "_ability_mod": ability_mod,  # Store for offhand calculation
                "_dueling_bonus": dueling_bonus,  # Store to exclude from dual-wield
            }

            # Add thrown damage if applicable
            if throw_damage_str:
                attack_info["throw_damage"] = throw_damage_str
                attack_info["avg_throw_damage"] = avg_throw_damage

            # Add versatile damage options if applicable
            if versatile_die:
                attack_info["damage_one_handed"] = damage_one_handed_str
                attack_info["damage_two_handed"] = damage_two_handed_str
                attack_info["avg_one_handed"] = avg_one_handed
                attack_info["avg_two_handed"] = avg_two_handed

            attacks.append(attack_info)

        # Add Unarmed Strike
        # Base unarmed strike: 1 + STR modifier
        # With Unarmed Fighting: 1d6 + STR (or 1d8 + STR if no weapons/shield)
        str_mod = ability_scores.get("strength", {}).get("modifier", 0)
        has_unarmed_fighting = False

        if hasattr(self, "applied_effects"):
            for effect_wrapper in self.applied_effects:
                if effect_wrapper.get("type") == "unarmed_fighting":
                    has_unarmed_fighting = True
                    break

        if has_unarmed_fighting:
            # Check if character has weapons or shield equipped
            has_weapons_or_shield = len(all_weapons) > 0

            # Check for shield in armor
            armor_list = equipment.get("armor", [])
            has_shield = any("Shield" in armor.get("name", "") for armor in armor_list)

            # Determine damage die
            if has_weapons_or_shield or has_shield:
                unarmed_damage_dice = "1d6"
            else:
                unarmed_damage_dice = "1d8"

            # Format damage string
            if str_mod > 0:
                unarmed_damage_str = f"{unarmed_damage_dice} + {str_mod}"
            elif str_mod < 0:
                unarmed_damage_str = f"{unarmed_damage_dice} - {abs(str_mod)}"
            else:
                unarmed_damage_str = unarmed_damage_dice

            unarmed_avg = self._calculate_average_damage(unarmed_damage_dice, str_mod)
            unarmed_crit_avg = self._calculate_average_damage(
                unarmed_damage_dice, str_mod, is_crit=True
            )
        else:
            # Base unarmed strike: 1 + STR modifier
            unarmed_damage_base = 1 + str_mod
            if unarmed_damage_base > 0:
                unarmed_damage_str = str(unarmed_damage_base)
            else:
                unarmed_damage_str = "1"  # Minimum 1 damage

            unarmed_avg = float(max(1, 1 + str_mod))
            unarmed_crit_avg = float(
                max(1, 1 + str_mod)
            )  # Unarmed crits don't double the base 1

        unarmed_attack_bonus = str_mod + proficiency_bonus

        unarmed_notes = []
        if has_unarmed_fighting:
            if has_weapons_or_shield or has_shield:
                unarmed_notes.append("1d8 if no weapons or shield equipped")
            else:
                unarmed_notes.append("1d6 if wielding weapons or shield")
            unarmed_notes.append("1d4 damage to grappled creature (start of turn)")

        unarmed_attack = {
            "name": "Unarmed Strike",
            "attack_bonus": unarmed_attack_bonus,
            "attack_bonus_display": f"+{unarmed_attack_bonus}"
            if unarmed_attack_bonus >= 0
            else str(unarmed_attack_bonus),
            "damage": unarmed_damage_str,
            "damage_type": "Bludgeoning",
            "avg_damage": unarmed_avg,
            "avg_crit": unarmed_crit_avg,
            "properties": [],
            "ability": "STR",
            "proficient": True,  # Everyone is proficient with unarmed strikes
            "mastery": None,
            "icon": "/static/images/weapons/strike.svg",
            "damage_notes": unarmed_notes,
        }

        attacks.append(unarmed_attack)

        # Check if character has 2+ light weapons for dual wielding
        # Create combination cards for each pair
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]

        combinations = []
        if len(light_weapons) >= 2:
            # Create all possible combinations of light weapons
            for i, weapon1 in enumerate(light_weapons):
                for weapon2 in light_weapons[i + 1 :]:
                    # Create combination card
                    combo = self._create_dual_wield_combo(
                        weapon1, weapon2, proficiency_bonus
                    )
                    combinations.append(combo)

        # Clean up temporary fields for all attacks
        for attack in attacks:
            attack.pop("_damage_dice", None)
            attack.pop("_ability_mod", None)
            attack.pop("_dueling_bonus", None)

        return {"attacks": attacks, "combinations": combinations}

    def _create_dual_wield_combo(
        self, weapon1: Dict[str, Any], weapon2: Dict[str, Any], proficiency_bonus: int
    ) -> Dict[str, Any]:
        """Create a dual-wield combination card for two light weapons."""
        # Calculate mainhand attack (weapon1)
        mh_damage_dice = weapon1.get("_damage_dice", "1d4")
        mh_ability_mod = weapon1.get("_ability_mod", 0)
        mh_attack_bonus = weapon1.get("attack_bonus")

        # Mainhand damage: ability mod but NO Dueling
        if mh_ability_mod > 0:
            mh_damage = f"{mh_damage_dice} + {mh_ability_mod}"
        elif mh_ability_mod < 0:
            mh_damage = f"{mh_damage_dice} - {abs(mh_ability_mod)}"
        else:
            mh_damage = mh_damage_dice

        # Mainhand average (no GWF adjustment needed here - applied to individual weapons)
        mh_avg_damage = self._calculate_average_damage(mh_damage_dice, mh_ability_mod)

        # Calculate offhand attack (weapon2)
        oh_damage_dice = weapon2.get("_damage_dice", "1d4")
        oh_ability_mod = weapon2.get("_ability_mod", 0)
        oh_attack_bonus = weapon2.get("attack_bonus")

        # Check for Two-Weapon Fighting style (adds ability mod to offhand)
        has_two_weapon_fighting = False
        if hasattr(self, "applied_effects"):
            for effect_wrapper in self.applied_effects:
                if effect_wrapper.get("type") == "two_weapon_fighting_modifier":
                    has_two_weapon_fighting = True
                    break

        # Offhand damage:
        # - With Two-Weapon Fighting: add full ability mod
        # - Without: dice only (but include negative modifier)
        if has_two_weapon_fighting:
            # Add full ability modifier
            if oh_ability_mod > 0:
                oh_damage = f"{oh_damage_dice} + {oh_ability_mod}"
            elif oh_ability_mod < 0:
                oh_damage = f"{oh_damage_dice} - {abs(oh_ability_mod)}"
            else:
                oh_damage = oh_damage_dice
            oh_damage_bonus = oh_ability_mod
        else:
            # Dice only (unless negative)
            if oh_ability_mod < 0:
                oh_damage = f"{oh_damage_dice} - {abs(oh_ability_mod)}"
                oh_damage_bonus = oh_ability_mod
            else:
                oh_damage = oh_damage_dice
                oh_damage_bonus = 0

        # Offhand average (no GWF adjustment needed here - applied to individual weapons)
        oh_avg_damage = self._calculate_average_damage(oh_damage_dice, oh_damage_bonus)

        # Check if Dueling was applied to either weapon
        has_dueling = (
            weapon1.get("_dueling_bonus", 0) > 0 or weapon2.get("_dueling_bonus", 0) > 0
        )

        return {
            "type": "combination",
            "name": f"{weapon1['name']} & {weapon2['name']}",
            "mainhand": {
                "name": weapon1["name"],
                "attack_bonus": mh_attack_bonus,
                "attack_bonus_display": f"+{mh_attack_bonus}"
                if mh_attack_bonus >= 0
                else str(mh_attack_bonus),
                "damage": mh_damage,
                "damage_type": weapon1["damage_type"],
                "avg_damage": mh_avg_damage,
                "icon": weapon1["icon"],
            },
            "offhand": {
                "name": weapon2["name"],
                "attack_bonus": oh_attack_bonus,
                "attack_bonus_display": f"+{oh_attack_bonus}"
                if oh_attack_bonus >= 0
                else str(oh_attack_bonus),
                "damage": oh_damage,
                "damage_type": weapon2["damage_type"],
                "avg_damage": oh_avg_damage,
                "icon": weapon2["icon"],
            },
            "notes": ["Dueling bonus does not apply when dual-wielding"]
            if has_dueling
            else [],
        }

    def _has_weapon_proficiency(
        self, weapon_props: Dict[str, Any], weapon_proficiencies: List[str]
    ) -> bool:
        """Check if character has proficiency for weapon."""
        prof_required = weapon_props.get("proficiency_required", "")
        weapon_name = weapon_props.get("name", "")

        # Check specific weapon proficiency first
        if weapon_name in weapon_proficiencies:
            return True

        # Check category proficiency
        if prof_required in weapon_proficiencies:
            return True

        return False

    def _calculate_average_damage(
        self, dice_expr: str, bonus: int, is_crit: bool = False, has_gwf: bool = False
    ) -> float:
        """Calculate average damage from a dice expression.

        Args:
            dice_expr: Dice expression (e.g., "1d6", "2d8")
            bonus: Flat bonus damage
            is_crit: Whether this is a critical hit (doubles dice)
            has_gwf: Whether Great Weapon Fighting applies (reroll 1s and 2s)
        """
        try:
            if "d" not in dice_expr:
                return float(bonus)

            parts = dice_expr.lower().split("d")
            num_dice = int(parts[0]) if parts[0] else 1
            die_size = int(parts[1])

            # For crits, double the number of dice
            if is_crit:
                num_dice *= 2

            # Average of a die
            if has_gwf:
                # Great Weapon Fighting: reroll 1s and 2s
                # Expected value = (2/N)*avg_reroll + sum(3 to N)/N
                # Where avg_reroll is the normal die average
                avg_all = (1 + die_size) / 2.0
                sum_3_to_n = sum(range(3, die_size + 1))
                avg_per_die = (2 * avg_all + sum_3_to_n) / die_size
            else:
                avg_per_die = (1 + die_size) / 2.0

            total_avg = (num_dice * avg_per_die) + bonus

            return round(total_avg, 1)
        except (ValueError, IndexError):
            return float(bonus)

    def _get_weapon_icon(self, weapon_name: str) -> str:
        """Get the appropriate weapon icon path for a weapon name."""
        if not weapon_name:
            return "/static/images/weapons/sword.svg"

        weapon_lower = weapon_name.lower()

        # Weapon icon mappings
        icon_mappings = {
            "club": "club.svg",
            "dagger": "dagger.svg",
            "dart": "dart.svg",
            "greatclub": "club.svg",
            "handaxe": "axe.svg",
            "javelin": "spear.svg",
            "light_hammer": "hammer.svg",
            "mace": "mace.svg",
            "quarterstaff": "staff.svg",
            "sickle": "sickle.svg",
            "spear": "spear.svg",
            "crossbow_light": "crossbow.svg",
            "shortbow": "bow.svg",
            "battleaxe": "axe.svg",
            "flail": "flail.svg",
            "glaive": "polearm.svg",
            "greataxe": "axe.svg",
            "greatsword": "sword.svg",
            "halberd": "polearm.svg",
            "lance": "lance.svg",
            "longsword": "sword.svg",
            "maul": "hammer.svg",
            "morningstar": "mace.svg",
            "pike": "spear.svg",
            "rapier": "rapier.svg",
            "scimitar": "scimitar.svg",
            "shortsword": "sword.svg",
            "trident": "trident.svg",
            "war_pick": "pick.svg",
            "warhammer": "hammer.svg",
            "whip": "whip.svg",
            "crossbow_hand": "crossbow.svg",
            "crossbow_heavy": "crossbow.svg",
            "longbow": "bow.svg",
            "unarmed_strike": "strike.svg",
        }

        # Try exact match first
        normalized_name = weapon_lower.replace(" ", "_").replace("-", "_")
        if normalized_name in icon_mappings:
            return f"/static/images/weapons/{icon_mappings[normalized_name]}"

        # Try partial matches
        for key, icon in icon_mappings.items():
            if key in normalized_name or normalized_name in key:
                return f"/static/images/weapons/{icon}"

        # Default icon
        return "/static/images/weapons/sword.svg"

    def calculate_combat_stats(self) -> Dict[str, Any]:
        """Calculate combat statistics."""
        ability_scores = self.calculate_processed_ability_scores()
        equipment = self.character_data.get("equipment") or {
            "weapons": [],
            "armor": [],
            "items": [],
            "gold": 0,
        }
        level = self.character_data.get("level", 1)

        # Basic combat stats
        dex_modifier = ability_scores["dexterity"]["modifier"]
        wis_modifier = ability_scores["wisdom"]["modifier"]
        constitution_score = self.ability_scores.final_scores.get("Constitution", 10)

        # Calculate HP with bonuses
        class_name = self.character_data.get("class", "")
        class_data = self.character_data.get("class_data", {})
        hp_bonuses = self._extract_hp_bonuses()
        max_hp = self.hp_calculator.calculate_total_hp(
            class_name, constitution_score, hp_bonuses, level
        )

        # Calculate AC (basic calculation - can be enhanced)
        base_ac = 10 + dex_modifier

        # Apply armor if any
        equipment.get("armor", [])
        armor_ac = base_ac  # Start with unarmored AC

        # Speed (default 30, can be modified by species/features)
        speed = self.character_data.get("speed", 30)

        # Hit dice
        hit_die = class_data.get("hit_die", 8) if class_data else 8
        hit_dice_total = f"{level}d{hit_die}"

        # Proficiency bonus
        proficiency_bonus = self.calculate_proficiency_bonus(level)

        # Check if proficient in Perception
        skill_proficiencies = self.character_data.get("proficiencies", {}).get(
            "skills", []
        )
        perception_proficient = "Perception" in skill_proficiencies

        return {
            "armor_class": armor_ac,
            "initiative": dex_modifier,  # For backward compatibility
            "initiative_bonus": dex_modifier,
            "speed": speed,
            "hit_point_maximum": max_hp,  # For backward compatibility
            "hit_points": {"current": max_hp, "maximum": max_hp, "temporary": 0},
            "hit_dice": {"total": hit_dice_total, "spent": 0},
            "passive_perception": 10
            + wis_modifier
            + (proficiency_bonus if perception_proficient else 0),
        }

    def _extract_hp_bonuses(self) -> List[Dict[str, Any]]:
        """Extract HP bonuses from effects and features."""
        hp_bonuses = []

        # Check effects for HP bonuses
        if hasattr(self, "applied_effects"):
            for applied_effect in self.applied_effects:
                effect = applied_effect["effect"]
                if effect.get("type") == "bonus_hp":
                    # Check if it's per-level scaling
                    scaling = effect.get("scaling")
                    value = effect.get("value", 0)

                    hp_bonuses.append(
                        {
                            "source": applied_effect.get("source", "Unknown"),
                            "value": value,
                            "scaling": scaling,
                        }
                    )

        return hp_bonuses

    # ==================== Export Methods ====================

    def to_character(self) -> Dict[str, Any]:
        """
        Export character as complete calculated data dictionary.
        This is the main method that returns character_data with all calculations.

        Returns:
            Complete character data with all calculated values
        """
        # Start with base character data
        character_data = deepcopy(self.character_data)

        # Add calculated ability scores
        character_data["ability_scores"] = self.ability_scores.final_scores
        character_data["abilities"] = self.calculate_processed_ability_scores()

        # Add calculated skills
        character_data["skills"] = self.calculate_skills()

        # Add calculated combat stats
        character_data["combat"] = self.calculate_combat_stats()

        # Add calculated weapon attacks and combinations
        weapon_data = self.calculate_weapon_attacks()
        character_data["attacks"] = weapon_data.get("attacks", [])
        character_data["attack_combinations"] = weapon_data.get("combinations", [])

        # Add calculated AC options
        character_data["ac_options"] = self.calculate_ac_options()

        # Process spell data for template display
        spells = character_data.get("spells", {})
        spell_slots = spells.get("slots", {})
        character_data.get("spell_metadata", {})

        # Organize spells by level for display
        spells_by_level = {}

        # Process always_prepared spells (dict of spell_name -> metadata)
        for spell_name, spell_info in spells.get("always_prepared", {}).items():
            spell_data = self._load_spell_definition(spell_name)
            if spell_data:
                # Merge with stored metadata
                spell_data.update(
                    {
                        "source": spell_info.get("source", "Unknown"),
                        "always_prepared": True,
                        "once_per_day": spell_info.get("once_per_day", False),
                    }
                )
                level = spell_info.get("level", spell_data.get("level", 0))
                if level not in spells_by_level:
                    spells_by_level[level] = []
                spells_by_level[level].append(spell_data)

        # Process prepared spells (dict with cantrips and spells subdicts)
        prepared = spells.get("prepared", {})
        if isinstance(prepared, dict):
            # Process prepared cantrips
            for spell_name, spell_info in prepared.get("cantrips", {}).items():
                spell_data = self._load_spell_definition(spell_name)
                if spell_data:
                    spell_data.update(
                        {
                            "source": spell_info.get("source", "Selected"),
                            "always_prepared": False,
                        }
                    )
                    if 0 not in spells_by_level:
                        spells_by_level[0] = []
                    spells_by_level[0].append(spell_data)

            # Process prepared spells
            for spell_name, spell_info in prepared.get("spells", {}).items():
                spell_data = self._load_spell_definition(spell_name)
                if spell_data:
                    spell_data.update(
                        {
                            "source": spell_info.get("source", "Selected"),
                            "always_prepared": False,
                        }
                    )
                    level = spell_data.get("level", 1)
                    if level not in spells_by_level:
                        spells_by_level[level] = []
                    spells_by_level[level].append(spell_data)

        # Process known spells (dict of spell_name -> metadata)
        for spell_name, spell_info in spells.get("known", {}).items():
            spell_data = self._load_spell_definition(spell_name)
            if spell_data:
                spell_data.update(spell_info)
                level = spell_info.get("level", spell_data.get("level", 1))
                if level not in spells_by_level:
                    spells_by_level[level] = []
                spells_by_level[level].append(spell_data)

        # Process background spells (dict of spell_name -> metadata)
        for spell_name, spell_info in spells.get("background_spells", {}).items():
            spell_data = self._load_spell_definition(spell_name)
            if spell_data:
                spell_data.update(
                    {
                        "source": spell_info.get("source", "Background"),
                        "once_per_day": True,
                    }
                )
                level = spell_info.get("level", spell_data.get("level", 0))
                if level not in spells_by_level:
                    spells_by_level[level] = []
                spells_by_level[level].append(spell_data)

        character_data["spells_by_level"] = spells_by_level
        character_data["spell_slots"] = spell_slots

        # Add proficiency bonus
        character_data["proficiency_bonus"] = self.calculate_proficiency_bonus(
            character_data.get("level", 1)
        )

        # Add spellcasting stats
        character_data["spellcasting_stats"] = self.calculate_spellcasting_stats()

        # Add weapon mastery stats
        character_data["weapon_mastery_stats"] = self.calculate_weapon_mastery_stats()

        # Add applied effects for export
        if hasattr(self, "applied_effects") and self.applied_effects:
            effects_for_export = []
            for applied_effect in self.applied_effects:
                effect = applied_effect["effect"].copy()
                effect["source"] = applied_effect.get("source", "Unknown")
                effect["source_type"] = applied_effect.get("source_type", "Unknown")
                effects_for_export.append(effect)
            character_data["effects"] = effects_for_export
        else:
            character_data["effects"] = []

        # Flatten proficiencies for easier template access
        proficiencies = character_data.get("proficiencies", {})
        character_data["languages"] = proficiencies.get("languages", [])
        character_data["skill_proficiencies"] = proficiencies.get("skills", [])
        character_data["weapon_proficiencies"] = proficiencies.get("weapons", [])
        character_data["armor_proficiencies"] = proficiencies.get("armor", [])

        # Include choices_made for web app compatibility
        character_data["choices_made"] = character_data.get("choices_made", {})

        # Include spell selections in choices_made for export/import
        spells = character_data.get("spells", {})
        prepared = spells.get("prepared", {})
        background_spells = spells.get("background_spells", {})

        spell_selections = {
            "cantrips": list(prepared.get("cantrips", {}).keys()),
            "spells": list(prepared.get("spells", {}).keys()),
            "background_cantrips": [
                name
                for name, data in background_spells.items()
                if data.get("level") == 0
            ],
            "background_spells": [
                name
                for name, data in background_spells.items()
                if data.get("level", 1) > 0
            ],
        }

        # Only include if there are any spell selections
        if any(spell_selections.values()):
            character_data["choices_made"]["spell_selections"] = spell_selections

        # Include weapon mastery selections in choices_made for export/import
        weapon_masteries = character_data.get("weapon_masteries", {})
        selected_masteries = weapon_masteries.get("selected", [])

        if selected_masteries:
            character_data["choices_made"]["weapon_mastery_selections"] = (
                selected_masteries
            )

        return character_data

    def to_json(self) -> Dict[str, Any]:
        """
        Legacy method - now calls to_character() for consistency.

        Returns:
            Complete character data as dictionary
        """
        return self.to_character()

    def to_character_object(self) -> Character:
        """
        Convert to Character object (renamed from old to_character method).

        Returns:
            Character object with all data populated
        """
        char = Character()
        character_data = self.to_character()

        char.name = character_data.get("name", "")
        char.species = character_data.get("species", "")
        char.species_variant = character_data.get("lineage", "")
        char.class_name = character_data.get("class", "")
        char.subclass = character_data.get("subclass", "")
        char.background = character_data.get("background", "")
        char.level = character_data.get("level", 1)

        # Ability scores from calculated data
        abilities = character_data.get("abilities", {})
        for ability_name, ability_data in abilities.items():
            char.abilities[ability_name.title()] = ability_data.get("score", 10)

        return char
        if abilities:
            char.ability_scores = self.ability_scores

        # Proficiencies
        profs = self.character_data.get("proficiencies", {})
        char.weapon_proficiencies = profs.get("weapons", [])
        char.armor_proficiencies = profs.get("armor", [])
        char.tool_proficiencies = profs.get("tools", [])
        char.skill_proficiencies = profs.get("skills", [])
        char.languages = profs.get("languages", [])

        # Other attributes
        char.speed = self.character_data.get("speed", 30)
        char.darkvision_range = self.character_data.get("darkvision", 0)

        # Store data references
        char.species_data = self.character_data.get("species_data")
        char.class_data = self.character_data.get("class_data")
        char.background_data = self.character_data.get("background_data")

        return char

    def from_json(self, data: dict):
        """
        Import character from JSON dictionary.

        Args:
            data: Character data dictionary
        """
        self.character_data = deepcopy(data)

        # Ensure weapon_masteries structure exists (for backwards compatibility)
        if "weapon_masteries" not in self.character_data:
            self.character_data["weapon_masteries"] = {
                "selected": [],
                "available": [],
                "max_count": 0,
            }

        # Ensure choices_made exists (for backwards compatibility)
        if "choices_made" not in self.character_data:
            self.character_data["choices_made"] = {}

        # Reconstruct ability scores
        # First check for ability_scores (raw scores exported by to_character)
        if "ability_scores" in data:
            self.ability_scores.set_base_scores(data["ability_scores"])

        # Also check for detailed abilities structure
        abilities = data.get("abilities", {})
        if abilities:
            if "base" in abilities:
                self.ability_scores.set_base_scores(abilities["base"])
            if "species_bonuses" in abilities:
                self.ability_scores.apply_species_bonuses(abilities["species_bonuses"])
            if "background_bonuses" in abilities:
                self.ability_scores.apply_background_bonuses(
                    abilities["background_bonuses"]
                )

        # Restore applied_effects from exported effects array
        # This is critical for preserving effects across session save/restore cycles
        self.applied_effects = []
        if "effects" in data and isinstance(data["effects"], list):
            for effect in data["effects"]:
                if isinstance(effect, dict):
                    # Reconstruct the applied_effect structure
                    applied_effect = {
                        "type": effect.get("type"),  # Preserve top-level type
                        "effect": {
                            k: v
                            for k, v in effect.items()
                            if k not in ["source", "source_type"]
                        },
                        "source": effect.get("source", "Unknown"),
                        "source_type": effect.get("source_type", "Unknown"),
                    }
                    self.applied_effects.append(applied_effect)

    @classmethod
    def quick_create(
        cls,
        species: str,
        char_class: str,
        background: str,
        abilities: Dict[str, int],
        lineage: Optional[str] = None,
        subclass: Optional[str] = None,
        level: int = 1,
        spellcasting_ability: Optional[str] = None,
    ) -> "CharacterBuilder":
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
        return self.character_data["step"] == "complete"

    def get_current_step(self) -> str:
        """Get the current creation step."""
        return self.character_data["step"]

    def set_step(self, step: str) -> None:
        """
        Set the current creation step.

        Args:
            step: The step name ('class', 'species', 'lineage', etc.)
        """
        self.character_data["step"] = step

    def get_cantrips(self) -> List[str]:
        """Get list of known cantrips."""
        return self.character_data["spells"]["cantrips"]

    def get_spells(self) -> List[str]:
        """Get list of known spells."""
        return self.character_data["spells"]["known"]

    def get_proficiencies(self, prof_type: str) -> List[str]:
        """
        Get proficiencies of a specific type.

        Args:
            prof_type: Type of proficiency ('armor', 'weapons', 'skills', etc.)

        Returns:
            List of proficiencies
        """
        return self.character_data["proficiencies"].get(prof_type, [])

    def get_all_spells(self) -> Dict[int, List[Dict[str, Any]]]:
        """
        Gather all spells known by the character from various sources.

        Returns a dictionary mapping spell level (0 for cantrips, 1-9 for leveled spells)
        to a list of spell dictionaries containing name, school, components, description,
        source, and other metadata.

        Sources include:
        - Effects (grant_cantrip, grant_spell)
        - Prepared spells (domain/species spells)
        - Known spells
        - Class cantrips from choices
        - Bonus cantrips from grant_cantrip_choice effects
        - Subclass spells from effects

        Returns:
            Dictionary mapping spell level to list of spell dicts
        """
        spells_by_level = {}
        character = self.to_json()
        choices_made = character.get("choices_made", {})
        class_name = character.get("class", "")
        subclass_name = character.get("subclass")
        character_level = character.get("level", 1)

        # Helper to load spell definition
        def load_spell_definition(spell_name: str) -> Dict[str, Any]:
            """Load spell details from definitions folder."""
            spell_file = (
                self.data_dir
                / "spells"
                / "definitions"
                / f"{spell_name.lower().replace(' ', '_')}.json"
            )
            if spell_file.exists():
                spell_info = self._load_json_file(spell_file)
                return spell_info or {}
            return {}

        # 1) Add spells granted directly via character effects
        effects = character.get("effects", [])
        if isinstance(effects, list):
            for effect in effects:
                if not isinstance(effect, dict):
                    continue

                # Check min_level requirement
                min_level = effect.get("min_level")
                if isinstance(min_level, int) and character_level < min_level:
                    continue

                effect_type = effect.get("type")

                if effect_type == "grant_cantrip":
                    cantrip_name = effect.get("spell")
                    if not cantrip_name:
                        continue

                    # Avoid duplicates
                    if 0 in spells_by_level and any(
                        s.get("name") == cantrip_name for s in spells_by_level[0]
                    ):
                        continue

                    cantrip_info = load_spell_definition(cantrip_name)

                    if 0 not in spells_by_level:
                        spells_by_level[0] = []

                    spells_by_level[0].append(
                        {
                            "name": cantrip_name,
                            "school": cantrip_info.get("school", ""),
                            "casting_time": cantrip_info.get("casting_time", ""),
                            "range": cantrip_info.get("range", ""),
                            "components": cantrip_info.get("components", ""),
                            "duration": cantrip_info.get("duration", ""),
                            "description": cantrip_info.get("description", ""),
                            "source": effect.get("source", "Effects"),
                        }
                    )

                elif effect_type == "grant_spell":
                    spell_name = effect.get("spell")
                    spell_level = effect.get("level")
                    if not spell_name or not isinstance(spell_level, int):
                        continue

                    # Avoid duplicates
                    if spell_level in spells_by_level and any(
                        s.get("name") == spell_name
                        for s in spells_by_level[spell_level]
                    ):
                        continue

                    spell_info = load_spell_definition(spell_name)

                    if spell_level not in spells_by_level:
                        spells_by_level[spell_level] = []

                    spells_by_level[spell_level].append(
                        {
                            "name": spell_name,
                            "school": spell_info.get("school", ""),
                            "casting_time": spell_info.get("casting_time", ""),
                            "range": spell_info.get("range", ""),
                            "components": spell_info.get("components", ""),
                            "duration": spell_info.get("duration", ""),
                            "description": spell_info.get("description", ""),
                            "source": effect.get("source", "Effects"),
                        }
                    )

        # 2) Add spells from character['spells']['prepared'] (domain/species spells - always prepared)
        prepared_spells = character.get("spells", {}).get("prepared", [])
        spell_metadata = character.get("spell_metadata", {})

        if isinstance(prepared_spells, list):
            for spell_name in prepared_spells:
                if not spell_name or not isinstance(spell_name, str):
                    continue

                spell_info = load_spell_definition(spell_name)
                spell_level = spell_info.get("level", 1)

                if spell_level not in spells_by_level:
                    spells_by_level[spell_level] = []

                if not any(
                    s.get("name") == spell_name for s in spells_by_level[spell_level]
                ):
                    # Get metadata for this spell
                    metadata = spell_metadata.get(spell_name, {})
                    once_per_day = metadata.get("once_per_day", False)

                    # Determine the source from metadata
                    spell_source = metadata.get("source", "always_prepared")
                    if spell_source == "lineage":
                        lineage = character.get("lineage", "")
                        display_source = (
                            f"{lineage} Spells" if lineage else "Lineage Spells"
                        )
                    elif spell_source == "subclass":
                        display_source = (
                            f"{subclass_name} Spells"
                            if subclass_name
                            else "Subclass Spells"
                        )
                    else:
                        display_source = "Always Prepared"

                    spells_by_level[spell_level].append(
                        {
                            "name": spell_name,
                            "school": spell_info.get("school", ""),
                            "casting_time": spell_info.get("casting_time", ""),
                            "range": spell_info.get("range", ""),
                            "components": spell_info.get("components", ""),
                            "duration": spell_info.get("duration", ""),
                            "description": spell_info.get("description", ""),
                            "source": display_source,
                            "always_prepared": True,
                            "once_per_day": once_per_day,
                        }
                    )

        # 3) Add spells from character['spells']['known']
        known_spells = character.get("spells", {}).get("known", [])
        if isinstance(known_spells, list):
            for spell_name in known_spells:
                if not spell_name or not isinstance(spell_name, str):
                    continue

                spell_info = load_spell_definition(spell_name)
                spell_level = spell_info.get("level", 1)

                if spell_level not in spells_by_level:
                    spells_by_level[spell_level] = []

                if not any(
                    s.get("name") == spell_name for s in spells_by_level[spell_level]
                ):
                    spells_by_level[spell_level].append(
                        {
                            "name": spell_name,
                            "school": spell_info.get("school", ""),
                            "casting_time": spell_info.get("casting_time", ""),
                            "range": spell_info.get("range", ""),
                            "components": spell_info.get("components", ""),
                            "duration": spell_info.get("duration", ""),
                            "description": spell_info.get("description", ""),
                            "source": "Known Spells",
                        }
                    )

        # 4) Get class cantrips from choices
        cantrips = choices_made.get("cantrips", [])
        if not cantrips:
            # Try common feature names
            for key in ["Spellcasting", "spellcasting", "Cantrips"]:
                if key in choices_made:
                    potential_cantrips = choices_made[key]
                    if isinstance(potential_cantrips, list):
                        cantrips = potential_cantrips
                        break

        if cantrips and class_name:
            if 0 not in spells_by_level:
                spells_by_level[0] = []

            # Load class cantrip list
            class_lower = class_name.lower()
            spell_file = (
                self.data_dir / "spells" / "class_lists" / f"{class_lower}.json"
            )

            if spell_file.exists():
                spell_data = self._load_json_file(spell_file)
                if spell_data:
                    available_cantrips = spell_data.get("cantrips", [])

                    for cantrip_name in cantrips:
                        if cantrip_name in available_cantrips:
                            existing_names = [s["name"] for s in spells_by_level[0]]
                            if cantrip_name not in existing_names:
                                cantrip_info = load_spell_definition(cantrip_name)

                                spells_by_level[0].append(
                                    {
                                        "name": cantrip_name,
                                        "school": cantrip_info.get("school", ""),
                                        "casting_time": cantrip_info.get(
                                            "casting_time", ""
                                        ),
                                        "range": cantrip_info.get("range", ""),
                                        "components": cantrip_info.get(
                                            "components", ""
                                        ),
                                        "duration": cantrip_info.get("duration", ""),
                                        "description": cantrip_info.get(
                                            "description", ""
                                        ),
                                        "source": f"{class_name} Class",
                                    }
                                )

        # 5) Add bonus cantrips from grant_cantrip_choice effects
        if class_name:
            class_data = self._load_class_data(class_name)
            if class_data:
                # Scan for options with grant_cantrip_choice effects
                for data_key, data_value in class_data.items():
                    if isinstance(data_value, dict):
                        for option_name, option_data in data_value.items():
                            if (
                                isinstance(option_data, dict)
                                and "effects" in option_data
                            ):
                                # Check if this option was selected
                                for choice_key, choice_value in choices_made.items():
                                    if choice_value == option_name:
                                        # Check for grant_cantrip_choice effects
                                        for effect in option_data.get("effects", []):
                                            if (
                                                effect.get("type")
                                                == "grant_cantrip_choice"
                                            ):
                                                bonus_cantrip_key = (
                                                    f"{option_name}_bonus_cantrip"
                                                )
                                                bonus_cantrips = choices_made.get(
                                                    bonus_cantrip_key
                                                )

                                                if bonus_cantrips:
                                                    spell_list = effect.get(
                                                        "spell_list", class_name
                                                    )
                                                    class_lower = spell_list.lower()
                                                    spell_file = (
                                                        self.data_dir
                                                        / "spells"
                                                        / "class_lists"
                                                        / f"{class_lower}.json"
                                                    )

                                                    if spell_file.exists():
                                                        spell_data = (
                                                            self._load_json_file(
                                                                spell_file
                                                            )
                                                        )
                                                        if spell_data:
                                                            available_cantrips = (
                                                                spell_data.get(
                                                                    "cantrips", []
                                                                )
                                                            )

                                                            if 0 not in spells_by_level:
                                                                spells_by_level[0] = []

                                                            cantrip_list = (
                                                                bonus_cantrips
                                                                if isinstance(
                                                                    bonus_cantrips, list
                                                                )
                                                                else [bonus_cantrips]
                                                            )

                                                            for (
                                                                cantrip_name
                                                            ) in cantrip_list:
                                                                if (
                                                                    cantrip_name
                                                                    in available_cantrips
                                                                ):
                                                                    existing_names = [
                                                                        s["name"]
                                                                        for s in spells_by_level[
                                                                            0
                                                                        ]
                                                                    ]
                                                                    if (
                                                                        cantrip_name
                                                                        not in existing_names
                                                                    ):
                                                                        cantrip_info = load_spell_definition(
                                                                            cantrip_name
                                                                        )

                                                                        spells_by_level[
                                                                            0
                                                                        ].append(
                                                                            {
                                                                                "name": cantrip_name,
                                                                                "school": cantrip_info.get(
                                                                                    "school",
                                                                                    "",
                                                                                ),
                                                                                "casting_time": cantrip_info.get(
                                                                                    "casting_time",
                                                                                    "",
                                                                                ),
                                                                                "range": cantrip_info.get(
                                                                                    "range",
                                                                                    "",
                                                                                ),
                                                                                "components": cantrip_info.get(
                                                                                    "components",
                                                                                    "",
                                                                                ),
                                                                                "duration": cantrip_info.get(
                                                                                    "duration",
                                                                                    "",
                                                                                ),
                                                                                "description": cantrip_info.get(
                                                                                    "description",
                                                                                    "",
                                                                                ),
                                                                                "source": f"{option_name} ({data_key})",
                                                                            }
                                                                        )

        # 6) Add cantrips from subclass features with grant_cantrip effects
        if subclass_name and class_name:
            subclass_data = self._load_subclass_data(class_name, subclass_name)
            if subclass_data:
                features_by_level = subclass_data.get("features_by_level", {})

                # Load class cantrip list once for efficiency
                class_lower = class_name.lower()
                spell_file = (
                    self.data_dir / "spells" / "class_lists" / f"{class_lower}.json"
                )
                available_cantrips = []

                if spell_file.exists():
                    spell_data = self._load_json_file(spell_file)
                    if spell_data:
                        available_cantrips = spell_data.get("cantrips", [])

                # Check each level up to character level for effects
                for level in range(1, character_level + 1):
                    level_str = str(level)
                    if level_str in features_by_level:
                        level_features = features_by_level[level_str]
                        for feature_name, feature_data in level_features.items():
                            if (
                                isinstance(feature_data, dict)
                                and "effects" in feature_data
                            ):
                                for effect in feature_data.get("effects", []):
                                    if effect.get("type") == "grant_cantrip":
                                        cantrip_name = effect.get("spell")
                                        if (
                                            cantrip_name
                                            and cantrip_name in available_cantrips
                                        ):
                                            if 0 not in spells_by_level:
                                                spells_by_level[0] = []

                                            existing_names = [
                                                s["name"] for s in spells_by_level[0]
                                            ]
                                            if cantrip_name not in existing_names:
                                                cantrip_info = load_spell_definition(
                                                    cantrip_name
                                                )

                                                spells_by_level[0].append(
                                                    {
                                                        "name": cantrip_name,
                                                        "school": cantrip_info.get(
                                                            "school", ""
                                                        ),
                                                        "casting_time": cantrip_info.get(
                                                            "casting_time", ""
                                                        ),
                                                        "range": cantrip_info.get(
                                                            "range", ""
                                                        ),
                                                        "components": cantrip_info.get(
                                                            "components", ""
                                                        ),
                                                        "duration": cantrip_info.get(
                                                            "duration", ""
                                                        ),
                                                        "description": cantrip_info.get(
                                                            "description", ""
                                                        ),
                                                        "source": f"{subclass_name} (Level {level})",
                                                    }
                                                )

        return spells_by_level

    def get_language_options(self) -> Dict[str, Any]:
        """
        Get language choices: base languages (already known) and available languages for selection.

        Returns:
            dict with keys:
                - base_languages: set of languages already known from species/class
                - available_languages: list of languages available to choose from
        """
        species_name = self.character_data.get("species")
        class_name = self.character_data.get("class")

        # Start with Common
        base_languages = set(["Common"])

        # Add species languages
        if species_name:
            species_data = self._load_species_data(species_name)
            if species_data and "languages" in species_data:
                base_languages.update(species_data["languages"])

        # Add class languages (if any)
        if class_name:
            class_data = self._load_class_data(class_name)
            if class_data and "languages" in class_data:
                base_languages.update(class_data["languages"])

        # All available languages in D&D 2024
        all_languages = [
            "Abyssal",
            "Celestial",
            "Common",
            "Deep Speech",
            "Draconic",
            "Dwarvish",
            "Elvish",
            "Giant",
            "Gnomish",
            "Goblin",
            "Halfling",
            "Infernal",
            "Orc",
            "Primordial",
            "Sylvan",
            "Undercommon",
        ]

        # Languages available for selection (not already known)
        available_languages = [
            lang for lang in all_languages if lang not in base_languages
        ]

        return {
            "base_languages": sorted(base_languages),
            "available_languages": available_languages,
        }

    def get_background_asi_options(self) -> Dict[str, Any]:
        """
        Get background ability score increase options and suggested allocation.

        Returns:
            dict with keys:
                - total_points: Total ASI points to allocate (typically 3)
                - suggested: Suggested allocation from background data
                - ability_options: List of abilities available for allocation
        """
        background_name = self.character_data.get("background")
        if not background_name:
            return {
                "total_points": 3,
                "suggested": {},
                "ability_options": [
                    "Strength",
                    "Dexterity",
                    "Constitution",
                    "Intelligence",
                    "Wisdom",
                    "Charisma",
                ],
            }

        background_data = self._load_background_data(background_name)
        if not background_data:
            return {
                "total_points": 3,
                "suggested": {},
                "ability_options": [
                    "Strength",
                    "Dexterity",
                    "Constitution",
                    "Intelligence",
                    "Wisdom",
                    "Charisma",
                ],
            }

        # D&D 2024 standard
        total_points = 3
        suggested = {}
        ability_options = [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]

        if "ability_score_increase" in background_data:
            asi_data = background_data["ability_score_increase"]
            if "suggested" in asi_data:
                suggested = asi_data["suggested"]
            if "options" in asi_data:
                # Keep background-specific abilities in standard D&D order
                bg_options = asi_data["options"]
                ability_options = [
                    ability for ability in ability_options if ability in bg_options
                ]

        return {
            "total_points": total_points,
            "suggested": suggested,
            "ability_options": ability_options,
        }

    def get_species_trait_choices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get trait choices for the character's species (e.g., Keen Senses for Elf).

        Returns:
            dict mapping trait_name -> {description, options, count}
        """
        species_name = self.character_data.get("species")
        if not species_name:
            return {}

        species_data = self._load_species_data(species_name)
        if not species_data or "traits" not in species_data:
            return {}

        # Find trait choices and extract options
        trait_choices = {}
        for trait_name, trait_data in species_data["traits"].items():
            if isinstance(trait_data, dict) and trait_data.get("type") == "choice":
                # Extract options from the nested structure
                choices_data = trait_data.get("choices", {})
                source_data = choices_data.get("source", {})
                options = source_data.get("options", [])

                # Create simplified structure
                trait_choices[trait_name] = {
                    "description": trait_data.get("description", ""),
                    "options": options,
                    "count": choices_data.get("count", 1),
                }

        return trait_choices

    def get_class_features_and_choices(self) -> Dict[str, Any]:
        """
        Get all class and subclass features with their choices for character's level.

        This method processes:
        - Skill proficiency selections
        - Class features by level (informational and choice-based)
        - Subclass features by level (informational and choice-based)
        - Nested choices from effects (e.g., bonus cantrips from grant_cantrip_choice)

        Returns a dictionary with:
        - 'features_by_level': Dict mapping level (int) to list of feature dicts
        - 'choices': List of choice dicts for form processing
        - 'skill_choice': Dict with skill selection info (or None)

        Returns:
            Dictionary with features_by_level, choices, and skill_choice
        """
        character = self.to_json()
        class_name = character.get("class")
        subclass_name = character.get("subclass")
        character_level = character.get("level", 1)
        choices_made = character.get("choices_made", {})

        if not class_name:
            return {"features_by_level": {}, "choices": [], "skill_choice": None}

        # Load class and subclass data
        class_data = self._load_class_data(class_name)
        if not class_data:
            return {"features_by_level": {}, "choices": [], "skill_choice": None}

        subclass_data = None
        if subclass_name:
            subclass_data = self._load_subclass_data(class_name, subclass_name)

        all_features_by_level = {}
        choices = []
        skill_choice = None

        # All D&D skills - constant list
        ALL_SKILLS = [
            "Acrobatics",
            "Animal Handling",
            "Arcana",
            "Athletics",
            "Deception",
            "History",
            "Insight",
            "Intimidation",
            "Investigation",
            "Medicine",
            "Nature",
            "Perception",
            "Performance",
            "Persuasion",
            "Religion",
            "Sleight of Hand",
            "Stealth",
            "Survival",
        ]

        # 1) Add skill selection (level 1)
        if "skill_options" in class_data and "skill_proficiencies_count" in class_data:
            skill_options = class_data["skill_options"]

            # Expand "Any" to all available skills
            if skill_options == ["Any"] or (
                len(skill_options) == 1 and skill_options[0] == "Any"
            ):
                skill_options = ALL_SKILLS

            if 1 not in all_features_by_level:
                all_features_by_level[1] = []

            all_features_by_level[1].append(
                {
                    "name": "Skill Proficiencies",
                    "type": "choice",
                    "description": f"Choose {class_data['skill_proficiencies_count']} skill proficiencies from the available options.",
                    "level": 1,
                    "source": "Class",
                }
            )

            skill_choice = {
                "title": "Skill Proficiencies",
                "type": "skills",
                "description": f"Choose {class_data['skill_proficiencies_count']} skill proficiencies from the available options.",
                "options": skill_options,
                "count": class_data["skill_proficiencies_count"],
                "required": True,
                "level": 1,
            }
            choices.append(skill_choice)

        # Get class and subclass features
        class_features_by_level = class_data.get("features_by_level", {})
        subclass_features_by_level = {}
        if subclass_data:
            subclass_features_by_level = subclass_data.get("features_by_level", {})

        # 2) Process all levels up to character level
        for level in range(1, character_level + 1):
            level_str = str(level)

            if level not in all_features_by_level:
                all_features_by_level[level] = []

            # Process class features for this level
            self._process_level_features(
                level,
                level_str,
                class_features_by_level.get(level_str, {}),
                all_features_by_level,
                choices,
                character,
                class_data,
                None,
                source_name="Class",
            )

            # Process subclass features for this level
            if subclass_name and level_str in subclass_features_by_level:
                self._process_level_features(
                    level,
                    level_str,
                    subclass_features_by_level[level_str],
                    all_features_by_level,
                    choices,
                    character,
                    class_data,
                    subclass_data,
                    source_name=subclass_name,
                )

        # 3) Add nested choices from effects (e.g., bonus cantrips from grant_cantrip_choice)
        self._add_nested_choices_from_effects(
            choices, choices_made, class_data, character, class_name
        )

        return {
            "features_by_level": all_features_by_level,
            "choices": choices,
            "skill_choice": skill_choice,
        }

    def _process_level_features(
        self,
        level: int,
        level_str: str,
        level_features: Dict[str, Any],
        all_features_by_level: Dict[int, List[Dict]],
        choices: List[Dict],
        character: Dict,
        class_data: Dict,
        subclass_data: Optional[Dict],
        source_name: str,
    ):
        """
        Process features for a specific level (class or subclass).

        Adds features to all_features_by_level and choices lists.
        """
        for feature_name, feature_data in level_features.items():
            if isinstance(feature_data, dict) and "choices" in feature_data:
                # Choice-based feature
                all_features_by_level[level].append(
                    {
                        "name": feature_name,
                        "type": "choice",
                        "description": feature_data.get("description", ""),
                        "level": level,
                        "source": source_name,
                    }
                )

                # Add to choices for form processing
                choices_data = feature_data["choices"]
                if isinstance(choices_data, list):
                    # Multiple choices
                    for idx, choice_item in enumerate(choices_data):
                        choice_name_suffix = choice_item.get(
                            "name", f"Choice {idx + 1}"
                        )
                        feature_key = (
                            f"{feature_name}_{choice_item.get('name', f'choice_{idx}')}"
                        )

                        # For subclass features, prefix with 'subclass_'
                        if subclass_data:
                            feature_key = f"subclass_{feature_key}"

                        choice = {
                            "title": f"{feature_name} - {choice_name_suffix} ({source_name}, Level {level})",
                            "type": "feature",
                            "description": feature_data.get("description", ""),
                            "options": resolve_choice_options(
                                choice_item, character, class_data, subclass_data
                            ),
                            "count": choice_item.get("count", 1),
                            "required": not choice_item.get("optional", False),
                            "level": level,
                            "feature_name": feature_key,
                            "option_descriptions": get_option_descriptions(
                                feature_data, choice_item, class_data, subclass_data
                            ),
                        }

                        # Skip subclass-related features in class-only context
                        if (
                            source_name == "Class"
                            and "subclass" not in feature_name.lower()
                        ):
                            choices.append(choice)
                        elif source_name != "Class":
                            choices.append(choice)
                else:
                    # Single choice
                    feature_key = feature_name
                    if subclass_data:
                        feature_key = f"subclass_{feature_name}"

                    choice = {
                        "title": f"{feature_name} ({source_name}, Level {level})",
                        "type": "feature",
                        "description": feature_data.get("description", ""),
                        "options": resolve_choice_options(
                            choices_data, character, class_data, subclass_data
                        ),
                        "count": choices_data.get("count", 1),
                        "required": not choices_data.get("optional", False),
                        "level": level,
                        "feature_name": feature_key,
                        "option_descriptions": get_option_descriptions(
                            feature_data, choices_data, class_data, subclass_data
                        ),
                    }

                    # Skip subclass-related features in class-only context
                    if (
                        source_name == "Class"
                        and "subclass" not in feature_name.lower()
                    ):
                        choices.append(choice)
                    elif source_name != "Class":
                        choices.append(choice)
            else:
                # Feature without choices (simple informational)
                description = (
                    feature_data
                    if isinstance(feature_data, str)
                    else feature_data.get("description", "")
                )
                all_features_by_level[level].append(
                    {
                        "name": feature_name,
                        "type": "info",
                        "description": description,
                        "level": level,
                        "source": source_name,
                    }
                )

    def _add_nested_choices_from_effects(
        self,
        choices: List[Dict],
        choices_made: Dict[str, Any],
        class_data: Dict,
        character: Dict,
        class_name: str,
    ):
        """
        Add nested choices triggered by grant_cantrip_choice effects.

        Scans class_data for ALL options with grant_cantrip_choice effects and adds
        the corresponding bonus cantrip choices to the choices list (hidden by default,
        shown by JavaScript when parent option is selected).
        """
        # First, find the parent choice key from existing choices
        parent_choice_key = None
        for choice in choices:
            feature_name = choice.get("feature_name")
            # Check if any options in class_data match this choice and have grant_cantrip_choice effects
            for data_key, data_value in class_data.items():
                if isinstance(data_value, dict):
                    for option_name, option_data in data_value.items():
                        if isinstance(option_data, dict) and "effects" in option_data:
                            for effect in option_data.get("effects", []):
                                if effect.get("type") == "grant_cantrip_choice":
                                    # Found a parent choice that triggers nested choices
                                    # Use the choice's feature_name or a normalized key
                                    if not parent_choice_key:
                                        # Try to derive the choice key from the feature name or data_key
                                        parent_choice_key = (
                                            feature_name.lower().replace(" ", "_")
                                            if feature_name
                                            else data_key.rstrip("s")
                                        )

        # Scan all keys in class_data for option lists that might have effects
        for data_key, data_value in class_data.items():
            if isinstance(data_value, dict):
                # This could be a choice list (e.g., divine_orders, fighting_styles, etc.)
                for option_name, option_data in data_value.items():
                    if isinstance(option_data, dict) and "effects" in option_data:
                        # Check for grant_cantrip_choice effects (add ALL, not just selected ones)
                        for effect in option_data.get("effects", []):
                            if effect.get("type") == "grant_cantrip_choice":
                                cantrip_count = effect.get("count", 1)
                                spell_list = effect.get("spell_list", class_name)

                                # Load cantrip options
                                class_lower = spell_list.lower()
                                spell_file_path = (
                                    f"spells/class_lists/{class_lower}.json"
                                )
                                cantrip_options = resolve_choice_options(
                                    {
                                        "source": {
                                            "type": "external",
                                            "file": spell_file_path,
                                            "list": "cantrips",
                                        }
                                    },
                                    character,
                                    class_data,
                                    None,
                                )

                                # Create unique feature name based on the option that grants it
                                bonus_feature_name = f"{option_name}_bonus_cantrip"

                                # Derive parent choice key (e.g., "divine_order" from "Divine Order" or "divine_orders")
                                choice_key = data_key.rstrip(
                                    "s"
                                )  # Remove trailing 's' (e.g., divine_orders -> divine_order)

                                # Only add if not already in choices
                                if not any(
                                    c.get("feature_name") == bonus_feature_name
                                    for c in choices
                                ):
                                    choice = {
                                        "title": f"{option_name} - Bonus Cantrip (Level 1)",
                                        "type": "feature",
                                        "description": f"Choose {cantrip_count} additional cantrip from the {spell_list} spell list.",
                                        "options": cantrip_options,
                                        "count": cantrip_count,
                                        "required": True,
                                        "level": 1,
                                        "feature_name": bonus_feature_name,
                                        "depends_on": choice_key,
                                        "depends_on_value": option_name,
                                        "is_nested": True,
                                        "option_descriptions": get_option_descriptions(
                                            {
                                                "choices": {
                                                    "source": {
                                                        "type": "external",
                                                        "file": spell_file_path,
                                                        "list": "cantrips",
                                                    }
                                                }
                                            },
                                            {
                                                "source": {
                                                    "type": "external",
                                                    "file": spell_file_path,
                                                    "list": "cantrips",
                                                }
                                            },
                                            class_data,
                                            None,
                                        ),
                                    }
                                    choices.append(choice)

    def validate(self) -> Dict[str, List[str]]:
        """
        Validate character data.

        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []

        # Check required fields
        if not self.character_data.get("species"):
            errors.append("Species is required")

        if not self.character_data.get("class"):
            errors.append("Class is required")

        if not self.character_data.get("background"):
            errors.append("Background is required")

        if not self.character_data.get("abilities"):
            errors.append("Ability scores are required")

        # Check ability score validity
        abilities = self.character_data.get("abilities", {}).get("base", {})
        for ability, score in abilities.items():
            if score < 1 or score > 20:
                errors.append(f"{ability} score {score} is out of valid range (1-20)")

        return {"errors": errors, "warnings": warnings}
