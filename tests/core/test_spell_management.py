#!/usr/bin/env python3
"""
Unit tests for spell management system.

Tests spell selection, preparation, spell level organization,
and the effects-based spell granting system (grant_spell, grant_cantrip).
"""

import pytest
from modules.character_builder import CharacterBuilder


class TestSpellManagement:
    """Test spell selection, preparation, and organization."""

    @pytest.fixture
    def cleric_builder(self):
        """Create a Cleric for testing spell management."""
        builder = CharacterBuilder()
        choices = {
            "character_name": "Test Cleric",
            "species": "Human",
            "class": "Cleric",
            "level": 3,
            "subclass": "Light Domain",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 12,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 16,
                "Charisma": 12,
            },
            "skill_choices": ["Insight", "Religion"],
            "Divine Order": "Thaumaturge",
            "Thaumaturge_bonus_cantrip": "Guidance",
        }
        builder.apply_choices(choices)
        return builder

    @pytest.fixture
    def wizard_builder(self):
        """Create a Wizard for testing spell preparation."""
        builder = CharacterBuilder()
        choices = {
            "character_name": "Test Wizard",
            "species": "Human",
            "class": "Wizard",
            "level": 3,
            "background": "Sage",
            "ability_scores": {
                "Strength": 8,
                "Dexterity": 14,
                "Constitution": 14,
                "Intelligence": 16,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Arcana", "History"],
        }
        builder.apply_choices(choices)
        return builder

    def test_domain_spells_always_prepared(self, cleric_builder):
        """Test Light Domain spells are always prepared."""
        char_data = cleric_builder.to_character()
        spells_by_level = char_data.get("spells_by_level", {})

        # Check for Light Domain level 1 spells
        level_1_spells = spells_by_level.get(1, [])
        level_1_names = [spell["name"] for spell in level_1_spells]

        assert "Burning Hands" in level_1_names
        assert "Faerie Fire" in level_1_names

        # Verify they're marked as always prepared
        for spell in level_1_spells:
            if spell["name"] in ["Burning Hands", "Faerie Fire"]:
                assert spell.get("always_prepared") is True
                assert spell.get("source") == "Light Domain"

    def test_spell_level_organization(self, cleric_builder):
        """Test spells are organized by their correct spell level."""
        # Advance to level 7 to get higher level spells
        builder = CharacterBuilder()
        choices = {
            "character_name": "Test Cleric",
            "species": "Human",
            "class": "Cleric",
            "level": 7,
            "subclass": "Light Domain",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 12,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 16,
                "Charisma": 12,
            },
            "skill_choices": ["Insight", "Religion"],
            "Divine Order": "Thaumaturge",
            "Thaumaturge_bonus_cantrip": "Guidance",
        }
        builder.apply_choices(choices)

        char_data = builder.to_character()
        spells_by_level = char_data.get("spells_by_level", {})

        # Check cantrips (level 0)
        cantrips = spells_by_level.get(0, [])
        assert len(cantrips) > 0
        for spell in cantrips:
            assert spell.get("level") == 0

        # Check level 1 spells
        level_1 = spells_by_level.get(1, [])
        level_1_names = [s["name"] for s in level_1]
        assert "Burning Hands" in level_1_names
        assert "Faerie Fire" in level_1_names
        for spell in level_1:
            assert spell.get("level") == 1

        # Check level 2 spells (should include Scorching Ray, See Invisibility)
        level_2 = spells_by_level.get(2, [])
        level_2_names = [s["name"] for s in level_2]
        assert "Scorching Ray" in level_2_names
        assert "See Invisibility" in level_2_names
        for spell in level_2:
            assert spell.get("level") == 2

        # Check level 3 spells (should include Daylight, Fireball at level 5+)
        level_3 = spells_by_level.get(3, [])
        level_3_names = [s["name"] for s in level_3]
        assert "Daylight" in level_3_names
        assert "Fireball" in level_3_names
        for spell in level_3:
            assert spell.get("level") == 3

        # Check level 4 spells (should include Arcane Eye, Wall of Fire at level 7+)
        level_4 = spells_by_level.get(4, [])
        level_4_names = [s["name"] for s in level_4]
        assert "Arcane Eye" in level_4_names
        assert "Wall of Fire" in level_4_names
        for spell in level_4:
            assert spell.get("level") == 4

    def test_grant_spell_effect_with_min_level(self):
        """Test grant_spell effects only apply at min_level."""
        # Level 2 Cleric shouldn't have Light Domain spells yet (requires level 3)
        builder = CharacterBuilder()
        choices = {
            "character_name": "Low Level Cleric",
            "species": "Human",
            "class": "Cleric",
            "level": 2,
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 12,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 16,
                "Charisma": 12,
            },
            "skill_choices": ["Insight", "Religion"],
            "Divine Order": "Thaumaturge",
            "Thaumaturge_bonus_cantrip": "Guidance",
        }
        builder.apply_choices(choices)

        char_data = builder.to_character()
        spells = char_data.get("spells", {})

        # Shouldn't have Light Domain spells yet (requires subclass at level 3)
        always_prepared = spells.get("always_prepared", {})
        assert "Burning Hands" not in always_prepared

    def test_spell_selection_storage(self, wizard_builder):
        """Test spell selections are stored correctly."""
        # Add prepared spells
        wizard_builder.character_data["spells"]["prepared"]["spells"][
            "Detect Magic"
        ] = {}
        wizard_builder.character_data["spells"]["prepared"]["spells"][
            "Magic Missile"
        ] = {}

        char_data = wizard_builder.to_character()
        spells_by_level = char_data.get("spells_by_level", {})

        level_1_spells = spells_by_level.get(1, [])
        level_1_names = [s["name"] for s in level_1_spells]

        assert "Detect Magic" in level_1_names
        assert "Magic Missile" in level_1_names

    def test_spell_export_import(self):
        """Test spell selections survive export/import."""
        # Create character with spell selections
        builder = CharacterBuilder()
        choices = {
            "character_name": "Test Wizard",
            "species": "Human",
            "class": "Wizard",
            "level": 3,
            "background": "Sage",
            "ability_scores": {
                "Strength": 8,
                "Dexterity": 14,
                "Constitution": 14,
                "Intelligence": 16,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Arcana", "History"],
            "spell_selections": {
                "cantrips": [],
                "spells": ["Detect Magic", "Magic Missile"],
                "background_cantrips": [],
                "background_spells": [],
            },
        }
        builder.apply_choices(choices)

        # Export
        exported = builder.to_json()
        assert "spell_selections" in exported["choices_made"]

        # Reimport
        builder2 = CharacterBuilder()
        builder2.apply_choices(exported["choices_made"])

        char_data = builder2.to_character()
        spells_by_level = char_data.get("spells_by_level", {})
        level_1_spells = spells_by_level.get(1, [])
        level_1_names = [s["name"] for s in level_1_spells]

        assert "Detect Magic" in level_1_names
        assert "Magic Missile" in level_1_names

    def test_spellcasting_stats_calculation(self, cleric_builder):
        """Test spellcasting statistics are calculated correctly."""
        stats = cleric_builder.calculate_spellcasting_stats()

        assert stats["has_spellcasting"] is True
        assert stats["spellcasting_ability"] == "Wisdom"
        assert stats["spellcasting_modifier"] == 3  # +3 from WIS 16
        assert stats["spell_save_dc"] == 13  # 8 + prof(2) + mod(3)
        assert stats["spell_attack_bonus"] == 5  # prof(2) + mod(3)

    def test_cantrip_count_progression(self):
        """Test cantrip slots increase with level."""
        test_levels = [
            (1, 3),  # Level 1 Cleric: 3 cantrips
            (4, 4),  # Level 4 Cleric: 4 cantrips
            (10, 5),  # Level 10 Cleric: 5 cantrips
        ]

        for level, expected_cantrips in test_levels:
            builder = CharacterBuilder()
            choices = {
                "character_name": "Test Cleric",
                "species": "Human",
                "class": "Cleric",
                "level": level,
                "background": "Acolyte",
                "ability_scores": {
                    "Strength": 10,
                    "Dexterity": 12,
                    "Constitution": 14,
                    "Intelligence": 10,
                    "Wisdom": 16,
                    "Charisma": 12,
                },
                "skill_choices": ["Insight", "Religion"],
                "Divine Order": "Thaumaturge",
                "Thaumaturge_bonus_cantrip": "Guidance",
            }
            builder.apply_choices(choices)

            stats = builder.calculate_spellcasting_stats()
            assert stats["max_cantrips"] >= expected_cantrips, (
                f"Level {level} should have at least {expected_cantrips} cantrips"
            )

    def test_prepared_spell_limit(self, cleric_builder):
        """Test prepared spell limit calculation."""
        stats = cleric_builder.calculate_spellcasting_stats()

        # Cleric: Level + WIS modifier (includes always_prepared spells)
        # At level 3 with Light Domain, has several always prepared spells
        assert stats["max_prepared_spells"] > 0
        assert isinstance(stats["max_prepared_spells"], int)

    def test_spell_slots_by_level(self, cleric_builder):
        """Test spell slots is defined in class data."""
        # Check that class data has spell slots defined
        class_data = cleric_builder.character_data.get("class_data", {})
        spell_slots_by_level = class_data.get("spell_slots_by_level", {})

        # Level 3 Cleric should have spell slot definition
        level_3_slots = spell_slots_by_level.get("3")
        assert level_3_slots is not None, "Level 3 should have spell slots defined"
        assert isinstance(level_3_slots, list), "Spell slots should be a list"
        assert len(level_3_slots) == 9, "Should have 9 spell levels (1-9)"

    def test_non_caster_no_spellcasting(self):
        """Test non-caster classes don't have spellcasting stats."""
        builder = CharacterBuilder()
        choices = {
            "character_name": "Test Fighter",
            "species": "Human",
            "class": "Fighter",
            "level": 3,
            "background": "Soldier",
            "ability_scores": {
                "Strength": 16,
                "Dexterity": 14,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Athletics", "Intimidation"],
            "Fighting Style": "Dueling",
        }
        builder.apply_choices(choices)

        stats = builder.calculate_spellcasting_stats()
        assert stats["has_spellcasting"] is False

    def test_grant_cantrip_effect(self, cleric_builder):
        """Test grant_cantrip effects add cantrips to character."""
        char_data = cleric_builder.to_character()
        spells_by_level = char_data.get("spells_by_level", {})

        cantrips = spells_by_level.get(0, [])
        cantrip_names = [s["name"] for s in cantrips]

        # Should have Light from Light Domain and Guidance from Thaumaturge
        assert "Light" in cantrip_names
        assert "Guidance" in cantrip_names
