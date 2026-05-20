#!/usr/bin/env python3
"""
Tests for get_language_options — standard/rare language splitting and
the rare_base_languages key introduced for the language wizard step.
"""

import pytest
from modules.character_builder import CharacterBuilder


class TestGetLanguageOptionsRareBaseLanguages:
    """Tests for rare_base_languages in get_language_options."""

    def test_returns_rare_base_languages_key(self):
        """get_language_options always returns a rare_base_languages key."""
        builder = CharacterBuilder()
        builder.set_species("Human")
        builder.set_background("Acolyte")
        builder.set_class("Fighter", 1)
        opts = builder.get_language_options()
        assert "rare_base_languages" in opts

    def test_no_rare_languages_for_non_rogue(self):
        """A Fighter without rare-language features has no rare_base_languages."""
        builder = CharacterBuilder()
        builder.set_species("Human")
        builder.set_background("Acolyte")
        builder.set_class("Fighter", 1)
        opts = builder.get_language_options()
        assert opts["rare_base_languages"] == []

    def test_rogue_thieves_cant_in_rare_base_languages(self):
        """Thieves' Cant (granted automatically by Rogue level 1) appears in rare_base_languages."""
        builder = CharacterBuilder()
        builder.set_species("Human")
        builder.set_background("Criminal")
        builder.set_class("Rogue", 1)
        opts = builder.get_language_options()
        assert "Thieves' Cant" in opts["rare_base_languages"]
        # Must NOT appear in standard base_languages
        assert "Thieves' Cant" not in opts["base_languages"]

    def test_rogue_thieves_cant_not_in_available_languages(self):
        """Thieves' Cant must not be offered as a standard pick-able language."""
        builder = CharacterBuilder()
        builder.set_species("Human")
        builder.set_background("Criminal")
        builder.set_class("Rogue", 1)
        opts = builder.get_language_options()
        assert "Thieves' Cant" not in opts["available_languages"]

    def test_common_not_in_rare_base_languages(self):
        """Common is always in base_languages, never in rare_base_languages."""
        builder = CharacterBuilder()
        builder.set_species("Human")
        builder.set_background("Criminal")
        builder.set_class("Rogue", 1)
        opts = builder.get_language_options()
        assert "Common" in opts["base_languages"]
        assert "Common" not in opts["rare_base_languages"]

    def test_deft_explorer_chosen_rare_language_in_rare_base_languages(self):
        """A rare language chosen via Deft Explorer appears in rare_base_languages."""
        builder = CharacterBuilder()
        builder.apply_choices({
            "character_name": "Test Ranger",
            "level": 2,
            "class": "Ranger",
            "species": "Human",
            "background": "Soldier",
            "skill_choices": ["Stealth", "Perception", "Survival"],
            "fighting_style": "Archery",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 15,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 14,
                "Charisma": 8,
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
            "deft_explorer_expertise": "Stealth",
            "deft_explorer_languages": ["Sylvan", "Abyssal"],
        })
        opts = builder.get_language_options()
        assert "Sylvan" in opts["rare_base_languages"]
        assert "Abyssal" in opts["rare_base_languages"]
        # They must NOT be offered as additional standard picks
        assert "Sylvan" not in opts["available_languages"]
        assert "Abyssal" not in opts["available_languages"]

    def test_deft_explorer_standard_language_in_base_languages(self):
        """A standard language chosen via Deft Explorer appears in base_languages."""
        builder = CharacterBuilder()
        builder.apply_choices({
            "character_name": "Test Ranger",
            "level": 2,
            "class": "Ranger",
            "species": "Human",
            "background": "Soldier",
            "skill_choices": ["Stealth", "Perception", "Survival"],
            "fighting_style": "Archery",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 15,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 14,
                "Charisma": 8,
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
            "deft_explorer_expertise": "Stealth",
            "deft_explorer_languages": ["Elvish", "Draconic"],
        })
        opts = builder.get_language_options()
        assert "Elvish" in opts["base_languages"]
        assert "Draconic" in opts["base_languages"]
        # Already known → not in available picks
        assert "Elvish" not in opts["available_languages"]
        assert "Draconic" not in opts["available_languages"]

    def test_thieves_cant_additional_language_choice_grants_language(self):
        """The chosen Thieves' Cant additional language is tracked in the character."""
        builder = CharacterBuilder()
        builder.apply_choices({
            "character_name": "Test Rogue",
            "level": 1,
            "class": "Rogue",
            "species": "Human",
            "background": "Criminal",
            "skill_choices": ["Stealth", "Perception", "Deception", "Athletics"],
            "ability_scores": {
                "Strength": 10, "Dexterity": 15, "Constitution": 14,
                "Intelligence": 12, "Wisdom": 10, "Charisma": 8,
            },
            "background_bonuses": {"Dexterity": 2, "Intelligence": 1},
            "thieves_cant_language": "Gnomish",
        })
        opts = builder.get_language_options()
        # Standard language chosen via Thieves' Cant → in base_languages
        assert "Gnomish" in opts["base_languages"]
        # Should not be offered again
        assert "Gnomish" not in opts["available_languages"]
