"""Tests for all D&D 2024 backgrounds - data loading and character building."""

import json
import pytest
from pathlib import Path

from modules.data_loader import DataLoader
from modules.character_builder import CharacterBuilder


DATA_DIR = Path(__file__).parent.parent / "data" / "backgrounds"

# Every D&D 2024 background that should exist
ALL_BACKGROUNDS = [
    "Acolyte", "Artisan", "Charlatan", "Criminal", "Entertainer",
    "Farmer", "Folk Hero", "Guard", "Guide", "Guild Artisan",
    "Hermit", "Merchant", "Noble", "Sage", "Sailor", "Scribe",
    "Soldier", "Wayfarer",
]


@pytest.fixture(scope="module")
def data_loader():
    return DataLoader()


class TestBackgroundDataFiles:
    """Verify every background JSON file loads and has required fields."""

    @pytest.mark.parametrize("bg_name", ALL_BACKGROUNDS)
    def test_background_exists(self, data_loader, bg_name):
        """Each background should be loadable from data files."""
        assert bg_name in data_loader.backgrounds, f"Missing background: {bg_name}"

    @pytest.mark.parametrize("bg_name", ALL_BACKGROUNDS)
    def test_background_required_fields(self, data_loader, bg_name):
        """Each background must have the required schema fields."""
        bg = data_loader.backgrounds.get(bg_name)
        if bg is None:
            pytest.skip(f"{bg_name} not loaded")

        assert bg.get("name") == bg_name
        assert isinstance(bg.get("description"), str)
        assert isinstance(bg.get("feat"), str)
        assert isinstance(bg.get("skill_proficiencies"), list)
        assert len(bg["skill_proficiencies"]) == 2
        assert isinstance(bg.get("tool_proficiencies"), list)
        assert len(bg["tool_proficiencies"]) >= 1

    @pytest.mark.parametrize("bg_name", ALL_BACKGROUNDS)
    def test_background_ability_scores(self, data_loader, bg_name):
        """Ability score increase must have total=3, 3 options, and valid suggested split."""
        bg = data_loader.backgrounds.get(bg_name)
        if bg is None:
            pytest.skip(f"{bg_name} not loaded")

        asi = bg["ability_score_increase"]
        assert asi["total"] == 3
        assert len(asi["options"]) == 3
        suggested = asi["suggested"]
        assert sum(suggested.values()) == 3
        # All suggested abilities must be in options
        for ability in suggested:
            assert ability in asi["options"]

    @pytest.mark.parametrize("bg_name", ALL_BACKGROUNDS)
    def test_background_equipment(self, data_loader, bg_name):
        """Starting equipment must have option_a (with items + gold) and option_b (gold only)."""
        bg = data_loader.backgrounds.get(bg_name)
        if bg is None:
            pytest.skip(f"{bg_name} not loaded")

        equip = bg["starting_equipment"]
        assert "option_a" in equip
        assert "option_b" in equip
        assert "items" in equip["option_a"]
        assert "gold" in equip["option_b"]
        assert equip["option_b"]["gold"] == 50


class TestNewBackgroundsIntegration:
    """Integration tests building characters with newly added backgrounds."""

    def test_artisan_character(self, built_character):
        """Build a character with Artisan background."""
        character = built_character({
            "character_name": "Artisan Test",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": "Artisan",
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 1, "Intelligence": 2},
        })
        assert character["background"] == "Artisan"
        assert "Investigation" in character.get("skill_proficiencies", [])
        assert "Persuasion" in character.get("skill_proficiencies", [])

    def test_farmer_character(self, built_character):
        """Build a character with Farmer background."""
        character = built_character({
            "character_name": "Farmer Test",
            "level": 1,
            "species": "Human",
            "class": "Barbarian",
            "background": "Farmer",
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 8, "Wisdom": 12, "Charisma": 10
            },
            "background_bonuses": {"Strength": 1, "Constitution": 2},
        })
        assert character["background"] == "Farmer"
        assert "Animal Handling" in character.get("skill_proficiencies", [])
        assert "Nature" in character.get("skill_proficiencies", [])

    def test_guard_character(self, built_character):
        """Build a character with Guard background."""
        character = built_character({
            "character_name": "Guard Test",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": "Guard",
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 2, "Wisdom": 1},
        })
        assert character["background"] == "Guard"
        assert "Athletics" in character.get("skill_proficiencies", [])
        assert "Perception" in character.get("skill_proficiencies", [])

    def test_guide_character(self, built_character):
        """Build a character with Guide background."""
        character = built_character({
            "character_name": "Guide Test",
            "level": 1,
            "species": "Human",
            "class": "Ranger",
            "background": "Guide",
            "ability_scores": {
                "Strength": 10, "Dexterity": 15, "Constitution": 14,
                "Intelligence": 8, "Wisdom": 13, "Charisma": 12
            },
            "background_bonuses": {"Dexterity": 1, "Wisdom": 2},
        })
        assert character["background"] == "Guide"
        assert "Stealth" in character.get("skill_proficiencies", [])
        assert "Survival" in character.get("skill_proficiencies", [])

    def test_merchant_character(self, built_character):
        """Build a character with Merchant background."""
        character = built_character({
            "character_name": "Merchant Test",
            "level": 1,
            "species": "Human",
            "class": "Rogue",
            "background": "Merchant",
            "ability_scores": {
                "Strength": 8, "Dexterity": 15, "Constitution": 14,
                "Intelligence": 13, "Wisdom": 10, "Charisma": 12
            },
            "background_bonuses": {"Intelligence": 1, "Charisma": 2},
        })
        assert character["background"] == "Merchant"
        assert "Animal Handling" in character.get("skill_proficiencies", [])
        assert "Persuasion" in character.get("skill_proficiencies", [])

    def test_sailor_character(self, built_character):
        """Build a character with Sailor background."""
        character = built_character({
            "character_name": "Sailor Test",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": "Sailor",
            "ability_scores": {
                "Strength": 14, "Dexterity": 15, "Constitution": 13,
                "Intelligence": 8, "Wisdom": 12, "Charisma": 10
            },
            "background_bonuses": {"Strength": 1, "Dexterity": 2},
        })
        assert character["background"] == "Sailor"
        assert "Acrobatics" in character.get("skill_proficiencies", [])
        assert "Perception" in character.get("skill_proficiencies", [])

    def test_scribe_character(self, built_character):
        """Build a character with Scribe background."""
        character = built_character({
            "character_name": "Scribe Test",
            "level": 1,
            "species": "Human",
            "class": "Wizard",
            "background": "Scribe",
            "ability_scores": {
                "Strength": 8, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 15, "Wisdom": 12, "Charisma": 10
            },
            "background_bonuses": {"Dexterity": 1, "Intelligence": 2},
        })
        assert character["background"] == "Scribe"
        assert "Investigation" in character.get("skill_proficiencies", [])
        assert "Perception" in character.get("skill_proficiencies", [])

    def test_wayfarer_character(self, built_character):
        """Build a character with Wayfarer background."""
        character = built_character({
            "character_name": "Wayfarer Test",
            "level": 1,
            "species": "Human",
            "class": "Rogue",
            "background": "Wayfarer",
            "ability_scores": {
                "Strength": 8, "Dexterity": 15, "Constitution": 14,
                "Intelligence": 12, "Wisdom": 13, "Charisma": 10
            },
            "background_bonuses": {"Dexterity": 2, "Wisdom": 1},
        })
        assert character["background"] == "Wayfarer"
        assert "Insight" in character.get("skill_proficiencies", [])
        assert "Stealth" in character.get("skill_proficiencies", [])
