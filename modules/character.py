#!/usr/bin/env python3
"""
Character Module
Simplified Character class that uses composition with other modules.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from .ability_scores import AbilityScores
from .feature_manager import FeatureManager
from .hp_calculator import HPCalculator


@dataclass
class Character:
    """Represents a D&D character using modular components"""

    def __init__(self):
        # Basic character info
        self.name: str = ""
        self.species: str = ""
        self.species_variant: str = ""
        self.class_name: str = ""
        self.subclass: str = ""
        self.background: str = ""
        self.level: int = 1

        # Modular components
        self.ability_scores = AbilityScores()
        self.feature_manager = FeatureManager()
        self.hp_calculator = HPCalculator()

        # Feature tracking
        self.active_features: List[Dict[str, Any]] = []
        self.feature_bonuses = self.feature_manager.create_empty_feature_bonuses()

        # Spell-related attributes
        self.spell_slots: Dict[str, int] = {}
        self.spells_known: Dict[str, int] = {}
        self.spells_prepared: List[str] = []

        # Additional character attributes that may be modified by variants
        self.speed: int = 30
        self.darkvision_range: int = 0
        self.weapon_proficiencies: List[str] = []
        self.armor_proficiencies: List[str] = []
        self.tool_proficiencies: List[str] = []
        self.skill_proficiencies: List[str] = []
        self.languages: List[str] = []
        self.spellcasting_ability: Optional[str] = None
        self.cantrips_known: int = 0

        # Legacy/compatibility fields
        self.feats: List[str] = []
        self.class_data: Optional[Dict[str, Any]] = None
        self.species_data: Optional[Dict[str, Any]] = None
        self.background_data: Optional[Dict[str, Any]] = None
        self.feat_data: Optional[List[Dict[str, Any]]] = []

    @property
    def hit_points(self) -> int:
        """Calculate current hit points"""
        constitution_score = self.ability_scores.final_scores.get("Constitution", 10)
        hp_bonuses = self.feature_bonuses.get("hit_points", [])
        return self.hp_calculator.calculate_total_hp(
            self.class_name, constitution_score, hp_bonuses, self.level
        )

    # Compatibility properties for legacy code
    @property
    def base_ability_scores(self) -> Dict[str, int]:
        return self.ability_scores.base_scores

    @base_ability_scores.setter
    def base_ability_scores(self, scores: Dict[str, int]):
        self.ability_scores.set_base_scores(scores)

    @property
    def species_ability_bonuses(self) -> Dict[str, int]:
        return self.ability_scores.species_bonuses

    @property
    def background_ability_bonuses(self) -> Dict[str, int]:
        return self.ability_scores.background_bonuses

    @property
    def final_ability_scores(self) -> Dict[str, int]:
        return self.ability_scores.final_scores

    @property
    def ability_scores_legacy(self) -> Dict[str, int]:
        """Legacy ability_scores field for backwards compatibility"""
        return self.ability_scores.legacy_scores

    def compute_final_ability_scores(self):
        """Compute final ability scores (for compatibility)"""
        self.ability_scores._compute_final_scores()

    def add_feature(self, feature: Dict[str, Any]):
        """Add a feature that provides bonuses or effects"""
        self.active_features.append(feature)
        self.feature_manager.apply_feature(feature, self.feature_bonuses)

    def calculate_hp_bonus(self) -> int:
        """Calculate total HP bonus from all sources (for compatibility)"""
        constitution_score = self.ability_scores.final_scores.get("Constitution", 10)
        constitution_bonus = self.hp_calculator.calculate_constitution_bonus(
            constitution_score, self.level
        )
        hp_bonuses = self.feature_bonuses.get("hit_points", [])
        feature_bonus = self.hp_calculator.calculate_feature_bonuses(
            hp_bonuses, self.level
        )
        return constitution_bonus + feature_bonus

    def calculate_final_hp(self) -> int:
        """Calculate final HP including all bonuses (for compatibility)"""
        return self.hit_points

    def get_feature_summary(self) -> Dict[str, List[str]]:
        """Get a summary of all active features and their effects"""
        return self.feature_manager.get_feature_summary(self.active_features)

    def get_hp_breakdown(self) -> Dict[str, Any]:
        """Get detailed HP calculation breakdown"""
        constitution_score = self.ability_scores.final_scores.get("Constitution", 10)
        hp_bonuses = self.feature_bonuses.get("hit_points", [])
        return self.hp_calculator.get_hp_breakdown(
            self.class_name, constitution_score, hp_bonuses, self.level
        )

    def print_character_sheet(self):
        """Print a complete character sheet"""
        print(f"\\n{'=' * 50}")
        print(f"CHARACTER SHEET: {self.name or 'Unnamed Character'}")
        print(f"{'=' * 50}")
        print(f"Species: {self.species}")
        print(f"Class: {self.class_name}")
        print(f"Background: {self.background}")
        print(f"Level: {self.level}")

        # Ability scores
        self.ability_scores.print_ability_breakdown(self.name or "Character")

        # HP breakdown
        hp_breakdown = self.get_hp_breakdown()
        self.hp_calculator.print_hp_breakdown(hp_breakdown)

        # Features
        feature_summary = self.get_feature_summary()
        has_features = any(features for features in feature_summary.values())

        if has_features:
            print("\\nActive Features:")
            for category, features in feature_summary.items():
                if features:
                    print(f"  {category}:")
                    for feature in features:
                        print(f"    • {feature}")

        # Feats
        if self.feats:
            print(f"\\nFeats: {', '.join(self.feats)}")

    def to_json(self) -> str:
        """Convert character to JSON string (basic version)"""
        data = self._to_dict_basic()
        return json.dumps(data, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary (basic version)"""
        return self._to_dict_basic()

    def to_full_json(self) -> str:
        """Convert character to JSON string including full details"""
        data = self._to_dict_full()
        return json.dumps(data, indent=2)

    def to_full_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary including full details"""
        return self._to_dict_full()

    def _to_dict_basic(self) -> Dict[str, Any]:
        """Create basic dictionary representation"""
        ability_data = self.ability_scores.to_dict()

        return {
            "name": self.name,
            "species": self.species,
            "character_class": self.class_name,
            "background": self.background,
            "level": self.level,
            "hit_points": self.hit_points,
            "ability_scores": ability_data["final_ability_scores"],
            "feats": self.feats.copy(),
            "active_features": [f.copy() for f in self.active_features],
            "feature_bonuses": {
                k: [b.copy() for b in v] for k, v in self.feature_bonuses.items()
            },
        }

    def _to_dict_full(self) -> Dict[str, Any]:
        """Create full dictionary representation"""
        basic_data = self._to_dict_basic()
        ability_data = self.ability_scores.to_dict()

        # Add detailed ability score breakdown
        basic_data.update(ability_data)

        # Add full data objects
        if self.class_data:
            basic_data["class_data"] = self.class_data.copy()
        if self.species_data:
            basic_data["species_data"] = self.species_data.copy()
        if self.background_data:
            basic_data["background_data"] = self.background_data.copy()
        if self.feat_data:
            basic_data["feat_data"] = [f.copy() for f in self.feat_data]

        return basic_data

    def from_dict(self, data: Dict[str, Any]):
        """Load character from dictionary"""
        # Basic fields
        self.name = data.get("name", "")
        self.species = data.get("species", "")
        self.class_name = data.get("character_class", data.get("class_name", ""))
        self.background = data.get("background", "")
        self.level = data.get("level", 1)

        # Load ability scores
        self.ability_scores.from_dict(data)

        # Load features
        if "active_features" in data:
            self.active_features = data["active_features"].copy()
        if "feature_bonuses" in data:
            self.feature_bonuses.update(data["feature_bonuses"])

        # Legacy fields
        if "feats" in data:
            self.feats = data["feats"].copy()
        if "class_data" in data:
            self.class_data = data["class_data"].copy()
        if "species_data" in data:
            self.species_data = data["species_data"].copy()
        if "background_data" in data:
            self.background_data = data["background_data"].copy()
        if "feat_data" in data:
            self.feat_data = data["feat_data"].copy()
