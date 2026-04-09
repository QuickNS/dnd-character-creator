"""
Unit tests for the Human species implementation.
Tests the Versatile trait (origin feat choice) and Skillful trait.
Regression tests for GitHub Issue #8.
"""

import pytest
from modules.character_builder import CharacterBuilder


@pytest.fixture
def human_builder():
    """Fixture providing a fresh CharacterBuilder with Human species setup."""
    builder = CharacterBuilder()
    builder.set_species("Human")
    return builder


class TestHumanVersatileTrait:
    """Regression tests for GitHub Issue #8: Versatile trait grants an Origin Feat."""

    def test_versatile_is_choice_trait(self, human_builder):
        """Versatile trait should be a choice, not plain text."""
        trait_choices = human_builder.get_species_trait_choices()
        assert "Versatile" in trait_choices
        assert len(trait_choices["Versatile"]["options"]) > 0

    def test_versatile_offers_all_origin_feats(self, human_builder):
        """Versatile should offer all origin feats as choices."""
        trait_choices = human_builder.get_species_trait_choices()
        options = trait_choices["Versatile"]["options"]
        expected_feats = [
            "Alert", "Crafter", "Healer", "Lucky",
            "Magic Initiate (Cleric)", "Magic Initiate (Druid)",
            "Magic Initiate (Wizard)", "Musician", "Savage Attacker",
            "Skilled", "Tavern Brawler", "Tough",
        ]
        for feat in expected_feats:
            assert feat in options, f"Versatile should offer '{feat}'"

    def test_versatile_grants_chosen_feat(self, human_builder):
        """Choosing an origin feat via Versatile adds it to character feats."""
        human_builder.apply_choice("Versatile", "Alert")

        char_data = human_builder.character_data
        feat_names = [f["name"] for f in char_data["features"]["feats"]]
        assert "Alert" in feat_names

    def test_versatile_feat_has_description(self, human_builder):
        """Origin feat granted by Versatile should have a description."""
        human_builder.apply_choice("Versatile", "Lucky")

        char_data = human_builder.character_data
        feat_entry = next(
            f for f in char_data["features"]["feats"] if f["name"] == "Lucky"
        )
        assert len(feat_entry["description"]) > 0

    def test_versatile_feat_has_source(self, human_builder):
        """Origin feat granted by Versatile should record the source."""
        human_builder.apply_choice("Versatile", "Healer")

        char_data = human_builder.character_data
        feat_entry = next(
            f for f in char_data["features"]["feats"] if f["name"] == "Healer"
        )
        assert feat_entry["source"] is not None

    def test_versatile_choice_is_stored(self, human_builder):
        """Versatile choice should be stored in choices_made."""
        human_builder.apply_choice("Versatile", "Musician")

        choices_made = human_builder.character_data["choices_made"]
        assert "Versatile" in choices_made
        assert choices_made["Versatile"] == "Musician"

    def test_versatile_tough_applies_hp_effect(self):
        """Choosing Tough via Versatile should apply bonus_hp effect."""
        builder = CharacterBuilder()
        builder.apply_choices({
            "character_name": "Tough Human",
            "level": 3,
            "species": "Human",
            "class": "Fighter",
            "background": "Criminal",
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8,
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        })
        builder.apply_choice("Versatile", "Tough")

        # The bonus_hp effect from Tough should be tracked
        hp_effects = [
            e for e in builder.applied_effects
            if e["effect"].get("type") == "bonus_hp"
        ]
        assert len(hp_effects) > 0, "Tough feat should produce a bonus_hp effect"

    def test_versatile_extra_feat_on_top_of_background(self):
        """Human should have TWO origin feats: one from background, one from Versatile."""
        builder = CharacterBuilder()
        builder.apply_choices({
            "character_name": "Two Feats",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": "Criminal",
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8,
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        })
        # Criminal background grants "Alert" feat
        builder.apply_choice("Versatile", "Skilled")

        character = builder.to_character()
        feat_names = [f["name"] for f in character["features"]["feats"]]
        assert "Alert" in feat_names, "Background feat should be present"
        assert "Skilled" in feat_names, "Versatile feat should be present"
        assert len(feat_names) >= 2, "Human should have at least 2 origin feats"


class TestHumanSkillfulTrait:
    """Test Skillful trait (existing functionality)."""

    def test_skillful_grants_chosen_skill(self, human_builder):
        """Skillful trait should grant proficiency in the chosen skill."""
        human_builder.apply_choice("Skillful", "Athletics")

        skills = human_builder.character_data["proficiencies"]["skills"]
        assert "Athletics" in skills
