"""
Level Manager Module for D&D 2024 Character Creator

Handles character level progression, including:
- Class feature unlocking by level
- Subclass selection and features
- Spell slot progression for casters
- Ability score improvements
- Proficiency bonus tracking
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class LevelManager:
    """Manages character level progression and feature unlocking"""

    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.class_data = self._load_class_data()
        self.subclass_data = self._load_subclass_data()

    def _load_class_data(self) -> Dict[str, Dict[str, Any]]:
        """Load all class data from JSON files"""
        class_dir = self.data_dir / "classes"
        classes = {}

        if class_dir.exists():
            for json_file in class_dir.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        class_data = json.load(f)
                        name = class_data.get("name")
                        if name:
                            classes[name] = class_data
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load {json_file}: {e}")

        return classes

    def _load_subclass_data(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Load all subclass data organized by class name"""
        subclass_dir = self.data_dir / "subclasses"
        subclasses = {}

        if subclass_dir.exists():
            # Each subdirectory represents a class
            for class_dir in subclass_dir.iterdir():
                if class_dir.is_dir():
                    class_name = class_dir.name.title()
                    subclasses[class_name] = {}

                    # Load all subclass files in this class directory
                    for json_file in class_dir.glob("*.json"):
                        try:
                            with open(json_file, "r") as f:
                                subclass_data = json.load(f)
                                subclass_name = subclass_data.get("name")
                                if subclass_name:
                                    subclasses[class_name][subclass_name] = (
                                        subclass_data
                                    )
                        except (json.JSONDecodeError, IOError) as e:
                            print(f"Warning: Could not load {json_file}: {e}")

        return subclasses

    def get_class_data(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific class"""
        return self.class_data.get(class_name)

    def get_proficiency_bonus(self, level: int) -> int:
        """Get proficiency bonus for a given level"""
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

    def get_class_features_at_level(
        self, class_name: str, level: int
    ) -> Dict[str, str]:
        """Get class features gained at a specific level"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            return {}

        features_by_level = class_data.get("features_by_level", {})
        return features_by_level.get(str(level), {})

    def get_all_features_up_to_level(
        self, class_name: str, level: int
    ) -> Dict[int, Dict[str, str]]:
        """Get all class features from level 1 to the specified level"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            return {}

        features_by_level = class_data.get("features_by_level", {})
        all_features = {}

        for feat_level in range(1, level + 1):
            if str(feat_level) in features_by_level:
                all_features[feat_level] = features_by_level[str(feat_level)]

        return all_features

    def get_subclass_level(self, class_name: str) -> int:
        """Get the level at which subclasses are chosen for a class"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            return 3  # Default for most classes

        return class_data.get("subclass_level", 3)

    def get_available_subclasses(self, class_name: str) -> List[str]:
        """Get list of available subclasses for a class"""
        return list(self.subclass_data.get(class_name, {}).keys())

    def get_subclass_data(
        self, class_name: str, subclass_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get data for a specific subclass"""
        class_subclasses = self.subclass_data.get(class_name, {})
        return class_subclasses.get(subclass_name)

    def get_subclass_features_at_level(
        self, class_name: str, subclass_name: str, level: int
    ) -> Dict[str, str]:
        """Get subclass features gained at a specific level"""
        subclass_data = self.get_subclass_data(class_name, subclass_name)
        if not subclass_data:
            return {}

        features = subclass_data.get("features", {})
        return features.get(str(level), {})

    def get_spell_slots_at_level(
        self, class_name: str, level: int, subclass_name: str = None
    ) -> Dict[str, int]:
        """Get spell slots available at a specific level"""
        # Check subclass first (for partial casters like Eldritch Knight)
        if subclass_name:
            subclass_data = self.get_subclass_data(class_name, subclass_name)
            if subclass_data and "spell_slots_by_level" in subclass_data:
                spell_slots = subclass_data["spell_slots_by_level"]
                level_slots = spell_slots.get(str(level), {})
                return self._normalize_spell_slots(level_slots)

        # Check class spell slots (for full casters)
        class_data = self.get_class_data(class_name)
        if not class_data:
            return {}

        spell_slots_by_level = class_data.get("spell_slots_by_level", {})
        level_slots = spell_slots_by_level.get(str(level), {})
        return self._normalize_spell_slots(level_slots)

    def _normalize_spell_slots(self, slots_data):
        """Convert spell slot data to consistent dictionary format"""
        if isinstance(slots_data, dict):
            # Already in dictionary format
            return slots_data
        elif isinstance(slots_data, list):
            # Convert array format to dictionary
            spell_levels = [
                "1st",
                "2nd",
                "3rd",
                "4th",
                "5th",
                "6th",
                "7th",
                "8th",
                "9th",
            ]
            result = {}
            for i, count in enumerate(slots_data):
                if i < len(spell_levels) and count > 0:
                    result[spell_levels[i]] = count
            return result
        else:
            return {}

    def get_spells_known_at_level(self, class_name: str, level: int) -> Dict[str, int]:
        """Get number of spells known at a specific level"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            return {}

        spells_known_by_level = class_data.get("spells_known_by_level", {})
        level_data = spells_known_by_level.get(str(level), {})

        # Handle both dictionary and object formats
        if isinstance(level_data, dict):
            return level_data
        else:
            return {}

    def is_caster_class(self, class_name: str) -> bool:
        """Check if a class has spellcasting capability"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            return False

        return "spellcasting" in class_data or "spell_slots_by_level" in class_data

    def is_subclass_caster(self, class_name: str, subclass_name: str) -> bool:
        """Check if a subclass has spellcasting capability"""
        subclass_data = self.get_subclass_data(class_name, subclass_name)
        if not subclass_data:
            return False

        return "spellcasting" in subclass_data or "spell_slots" in subclass_data

    def get_ability_score_improvements(self, class_name: str, level: int) -> int:
        """Get number of ability score improvements available up to a level"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            return 0

        features_by_level = class_data.get("features_by_level", {})
        asi_count = 0

        for feat_level in range(1, level + 1):
            level_features = features_by_level.get(str(feat_level), {})
            if "Ability Score Improvement" in level_features:
                asi_count += 1

        return asi_count

    def apply_level_progression(self, character, new_level: int) -> None:
        """Apply level progression to a character"""
        if new_level <= character.level:
            print(f"Character is already level {character.level}")
            return

        old_level = character.level
        character.level = new_level

        # Apply new class features
        for level in range(old_level + 1, new_level + 1):
            class_features = self.get_class_features_at_level(
                character.class_name, level
            )
            for feature_name, feature_description in class_features.items():
                character.feature_manager.add_feature(
                    feature_name, feature_description, f"Class (Level {level})"
                )

            # Apply subclass features if character has a subclass
            if hasattr(character, "subclass") and character.subclass:
                subclass_features = self.get_subclass_features_at_level(
                    character.class_name, character.subclass, level
                )
                for feature_name, feature_description in subclass_features.items():
                    character.feature_manager.add_feature(
                        feature_name, feature_description, f"Subclass (Level {level})"
                    )

        # Update HP
        if hasattr(character, "hp_calculator"):
            # HP calculation will be automatically updated by the hp_calculator
            pass

        # Update spell slots if applicable
        if hasattr(character, "spell_slots"):
            if hasattr(character, "subclass") and self.is_subclass_caster(
                character.class_name, character.subclass
            ):
                character.spell_slots = self.get_spell_slots_at_level(
                    character.class_name, new_level, character.subclass
                )
            elif self.is_caster_class(character.class_name):
                character.spell_slots = self.get_spell_slots_at_level(
                    character.class_name, new_level
                )

        print(f"Character leveled up from {old_level} to {new_level}!")

    def display_level_progression(
        self, class_name: str, start_level: int = 1, end_level: int = 20
    ) -> None:
        """Display level progression for a class"""
        class_data = self.get_class_data(class_name)
        if not class_data:
            print(f"Class {class_name} not found")
            return

        print(f"\\n{class_name} Level Progression:")
        print("=" * 50)

        features_by_level = class_data.get("features_by_level", {})

        for level in range(start_level, end_level + 1):
            level_features = features_by_level.get(str(level), {})
            if level_features:
                prof_bonus = self.get_proficiency_bonus(level)
                print(f"\\nLevel {level} (Proficiency Bonus: +{prof_bonus}):")

                for feature_name, feature_desc in level_features.items():
                    # Truncate long descriptions
                    short_desc = (
                        feature_desc[:60] + "..."
                        if len(feature_desc) > 60
                        else feature_desc
                    )
                    print(f"  • {feature_name}: {short_desc}")

                # Show spell slots if available
                spell_slots = self.get_spell_slots_at_level(class_name, level)
                if spell_slots:
                    slots_str = ", ".join(
                        [
                            f"{slot_level}: {count}"
                            for slot_level, count in spell_slots.items()
                        ]
                    )
                    print(f"  • Spell Slots: {slots_str}")

        # Show subclass information
        subclass_level = self.get_subclass_level(class_name)
        subclasses = self.get_available_subclasses(class_name)
        if subclasses:
            print(f"\\nSubclasses (chosen at level {subclass_level}):")
            for subclass in subclasses:
                subclass_data = self.get_subclass_data(class_name, subclass)
                if subclass_data:
                    description = subclass_data.get("description", "No description")
                    print(f"  • {subclass}: {description}")

    def can_choose_subclass(self, class_name: str, level: int) -> bool:
        """Check if a character can choose a subclass at this level"""
        subclass_level = self.get_subclass_level(class_name)
        return level >= subclass_level

    def get_level_summary(
        self, class_name: str, level: int, subclass_name: str = None
    ) -> Dict[str, Any]:
        """Get a comprehensive summary of what a character has at a specific level"""
        summary = {
            "level": level,
            "class_name": class_name,
            "subclass": subclass_name,
            "proficiency_bonus": self.get_proficiency_bonus(level),
            "class_features": {},
            "subclass_features": {},
            "spell_slots": {},
            "spells_known": {},
            "ability_score_improvements": self.get_ability_score_improvements(
                class_name, level
            ),
        }

        # Get all class features up to this level
        all_class_features = self.get_all_features_up_to_level(class_name, level)
        summary["class_features"] = all_class_features

        # Get subclass features if applicable
        if subclass_name and self.can_choose_subclass(class_name, level):
            subclass_features = {}
            for feat_level in range(self.get_subclass_level(class_name), level + 1):
                level_features = self.get_subclass_features_at_level(
                    class_name, subclass_name, feat_level
                )
                if level_features:
                    subclass_features[feat_level] = level_features
            summary["subclass_features"] = subclass_features

        # Get spell information
        summary["spell_slots"] = self.get_spell_slots_at_level(
            class_name, level, subclass_name
        )
        summary["spells_known"] = self.get_spells_known_at_level(class_name, level)

        return summary
