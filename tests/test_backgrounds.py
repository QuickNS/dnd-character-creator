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


class TestBackgroundReselection:
    """Regression tests for GitHub Issue: origin feats accumulate when changing background."""

    def _base_choices(self, background):
        return {
            "character_name": "Test Hero",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": background,
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        }

    def test_changing_background_replaces_feat(self):
        """Switching background replaces the origin feat, not accumulates it."""
        builder = CharacterBuilder()
        # First pick Soldier (Savage Attacker)
        builder.apply_choices(self._base_choices("Soldier"))
        # Then switch to Guard (Alert)
        builder.set_background("Guard")
        character = builder.to_character()

        feat_names = [f["name"] for f in character["features"]["feats"]]
        assert "Alert" in feat_names, "New background feat should be present"
        assert "Savage Attacker" not in feat_names, "Old background feat should be removed"
        assert feat_names.count("Alert") == 1, "Feat should appear exactly once"

    def test_changing_background_removes_old_skills(self):
        """Switching background removes the old background's skill proficiencies."""
        builder = CharacterBuilder()
        builder.apply_choices(self._base_choices("Soldier"))  # Athletics, Intimidation
        builder.set_background("Guard")   # Athletics, Perception
        character = builder.to_character()

        # Guard skills present
        assert "Athletics" in character.get("skill_proficiencies", [])
        assert "Perception" in character.get("skill_proficiencies", [])
        # Soldier-only skill gone
        assert "Intimidation" not in character.get("skill_proficiencies", [])

    def test_tough_hp_bonus_not_multiplied(self):
        """Switching to a background with Tough does not multiply the bonus_hp effect."""
        builder = CharacterBuilder()
        # Start with Sage (Magic Initiate Wizard)
        builder.apply_choices(self._base_choices("Sage"))
        # Switch to Folk Hero (Tough)
        builder.set_background("Folk Hero")

        # Count bonus_hp effects from Tough to confirm it's applied exactly once
        tough_hp_effects = [
            e for e in builder.applied_effects
            if e.get("source") == "Tough" and e["effect"].get("type") == "bonus_hp"
        ]
        assert len(tough_hp_effects) == 1, (
            f"Tough's bonus_hp should appear exactly once, got {len(tough_hp_effects)}"
        )

    def test_multiple_background_changes_no_accumulation(self):
        """Multiple background changes result in exactly one feat from the final background."""
        builder = CharacterBuilder()
        builder.apply_choices(self._base_choices("Sage"))
        builder.set_background("Soldier")
        builder.set_background("Guard")
        builder.set_background("Folk Hero")
        character = builder.to_character()

        feat_names = [f["name"] for f in character["features"]["feats"]]
        # Only Tough (from Folk Hero) should remain
        assert "Tough" in feat_names
        assert "Alert" not in feat_names
        assert "Savage Attacker" not in feat_names
        assert feat_names.count("Tough") == 1


class TestBackgroundSkillReplacement:
    """Regression tests for GitHub Issue: overlapping class/background skill proficiencies
    should offer a replacement choice instead of silently dropping the duplicate."""

    def _monk_choices(self, background: str):
        """Monk choosing Acrobatics as their class skill, then a given background."""
        return {
            "character_name": "Test Monk",
            "level": 1,
            "species": "Human",
            "class": "Monk",
            "background": background,
            "skill_choices": ["Acrobatics", "History"],
            "ability_scores": {
                "Strength": 12, "Dexterity": 16, "Constitution": 13,
                "Intelligence": 10, "Wisdom": 14, "Charisma": 8,
            },
            "background_bonuses": {"Dexterity": 2, "Wisdom": 1},
        }

    # ---- overlap detection --------------------------------------------------

    def test_overlap_detection_sets_replacements_needed(self):
        """When background skill overlaps with class skill, replacements_needed is stored."""
        builder = CharacterBuilder()
        # Monk picks Acrobatics; Sailor also grants Acrobatics
        builder.apply_choices(self._monk_choices("Sailor"))
        needed = builder.character_data["choices_made"].get(
            "background_skill_replacements_needed", 0
        )
        assert needed == 1, (
            f"Expected 1 replacement needed, got {needed}"
        )

    def test_no_overlap_no_replacements_needed(self):
        """When there is no overlap, replacements_needed is not set."""
        builder = CharacterBuilder()
        # Monk picks History and Insight; Sailor grants Acrobatics + Perception — no overlap
        builder.apply_choices({
            **self._monk_choices("Sailor"),
            "skill_choices": ["History", "Insight"],
        })
        needed = builder.character_data["choices_made"].get(
            "background_skill_replacements_needed", 0
        )
        assert needed == 0, (
            f"Expected 0 replacements needed, got {needed}"
        )

    # ---- replacement info ---------------------------------------------------

    def test_get_replacement_info_returns_options(self):
        """get_background_skill_replacement_info() lists valid replacement options."""
        builder = CharacterBuilder()
        builder.apply_choices(self._monk_choices("Sailor"))

        info = builder.get_background_skill_replacement_info()
        assert info["needed"] == 1
        assert len(info["options"]) > 0
        # Options should not include already-proficient skills
        current_profs = set(builder.character_data["proficiencies"]["skills"])
        for skill in info["options"]:
            assert skill not in current_profs, (
                f"Option '{skill}' is already proficient — should be excluded"
            )

    def test_get_replacement_info_returns_zero_when_no_overlap(self):
        """get_background_skill_replacement_info() returns needed=0 when no overlap."""
        builder = CharacterBuilder()
        builder.apply_choices({
            **self._monk_choices("Sailor"),
            "skill_choices": ["History", "Insight"],
        })
        info = builder.get_background_skill_replacement_info()
        assert info["needed"] == 0

    # ---- applying replacements ----------------------------------------------

    def test_apply_replacement_adds_skill(self):
        """apply_background_skill_replacement() grants the chosen skill proficiency."""
        builder = CharacterBuilder()
        builder.apply_choices(self._monk_choices("Sailor"))

        info = builder.get_background_skill_replacement_info()
        replacement_skill = info["options"][0]

        builder.apply_background_skill_replacement([replacement_skill])

        skills = builder.character_data["proficiencies"]["skills"]
        assert replacement_skill in skills, (
            f"Replacement skill '{replacement_skill}' should now be proficient"
        )

    def test_apply_replacement_correct_total_proficiencies(self):
        """After replacement, character should have the expected total skill count."""
        builder = CharacterBuilder()
        # Monk picks 2 class skills; Sailor grants 2 background skills with 1 overlap
        # → should end up with 2 + 2 = 4 distinct skill proficiencies (1 bg replaced)
        builder.apply_choices(self._monk_choices("Sailor"))

        info = builder.get_background_skill_replacement_info()
        builder.apply_background_skill_replacement([info["options"][0]])

        skills = builder.character_data["proficiencies"]["skills"]
        assert len(skills) == 4, (
            f"Expected 4 distinct skill proficiencies, got {len(skills)}: {skills}"
        )

    def test_apply_replacement_idempotent(self):
        """Calling apply_background_skill_replacement twice replaces the first choice."""
        builder = CharacterBuilder()
        builder.apply_choices(self._monk_choices("Sailor"))

        info = builder.get_background_skill_replacement_info()
        skill_a = info["options"][0]
        skill_b = info["options"][1] if len(info["options"]) > 1 else info["options"][0]

        builder.apply_background_skill_replacement([skill_a])
        builder.apply_background_skill_replacement([skill_b])

        skills = builder.character_data["proficiencies"]["skills"]
        # Only one replacement should survive
        assert skills.count(skill_a) <= 1
        assert skills.count(skill_b) == 1

    # ---- clearing on background change --------------------------------------

    def test_changing_background_clears_replacement_data(self):
        """Switching background removes replacement tracking and replacement skills."""
        builder = CharacterBuilder()
        builder.apply_choices(self._monk_choices("Sailor"))

        info = builder.get_background_skill_replacement_info()
        replacement_skill = info["options"][0]
        builder.apply_background_skill_replacement([replacement_skill])

        # Switch to a background that does NOT overlap with remaining class skills
        builder.set_background("Hermit")  # Grants Medicine + Religion

        choices_made = builder.character_data["choices_made"]
        assert "background_skill_replacements_needed" not in choices_made
        assert "background_skill_replacements" not in choices_made
        # Replacement skill from old background should be removed
        assert replacement_skill not in builder.character_data["proficiencies"]["skills"]

    # ---- restore from choices_made ------------------------------------------

    def test_apply_choices_restores_replacement_skills(self):
        """apply_choices() with background_skill_replacements restores proficiencies."""
        builder = CharacterBuilder()
        builder.apply_choices({
            **self._monk_choices("Sailor"),
            "background_skill_replacements": ["Athletics"],
        })
        skills = builder.character_data["proficiencies"]["skills"]
        assert "Athletics" in skills, (
            "Replacement skill should be restored from choices_made"
        )
        assert len(set(skills)) == len(skills), "No duplicate proficiencies"

