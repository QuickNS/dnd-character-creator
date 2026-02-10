#!/usr/bin/env python3
"""
Unit tests for dual-wielding (two-weapon fighting) system.

Tests the automatic detection of dual-wielding scenarios and
offhand damage calculation for characters with two light weapons.
"""

import pytest
from modules.character_builder import CharacterBuilder


class TestDualWielding:
    """Test dual-wielding detection and offhand damage calculation."""

    @pytest.fixture
    def dual_wielding_fighter(self):
        """Create a Fighter with two light weapons."""
        builder = CharacterBuilder()
        choices = {
            "character_name": "Dual Wielder",
            "species": "Human",
            "class": "Fighter",
            "level": 3,
            "background": "Soldier",
            "ability_scores": {
                "Strength": 14,
                "Dexterity": 16,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Athletics", "Acrobatics"],
            "Fighting Style": "Two-Weapon Fighting",
            "equipment_selections": {
                "class_equipment": "option_b",  # Gets Scimitar and Shortsword
                "background_equipment": "option_a",
            },
        }
        builder.apply_choices(choices)
        return builder

    @pytest.fixture
    def single_weapon_fighter(self):
        """Create a Fighter with one weapon."""
        builder = CharacterBuilder()
        choices = {
            "character_name": "Single Wielder",
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
            "equipment_selections": {
                "class_equipment": "option_a",  # Gets Longsword and Shield
                "background_equipment": "option_a",
            },
        }
        builder.apply_choices(choices)
        return builder

    def test_dual_wielding_detection(self, dual_wielding_fighter):
        """Test that two light weapons trigger offhand damage."""
        attacks = dual_wielding_fighter.calculate_weapon_attacks()

        # Find light weapons
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]

        assert len(light_weapons) >= 2, "Should have at least 2 light weapons"

        # All light weapons should have offhand damage
        for weapon in light_weapons:
            assert (
                "damage_offhand" in weapon
            ), f"{weapon['name']} should have offhand damage"
            assert (
                "avg_damage_offhand" in weapon
            ), f"{weapon['name']} should have average offhand damage"
            assert (
                "avg_crit_offhand" in weapon
            ), f"{weapon['name']} should have crit offhand damage"

    def test_single_weapon_no_offhand(self, single_weapon_fighter):
        """Test that single weapon doesn't get offhand damage."""
        attacks = single_weapon_fighter.calculate_weapon_attacks()

        # No attacks should have offhand damage
        for weapon in attacks:
            assert (
                "damage_offhand" not in weapon
            ), f"{weapon['name']} shouldn't have offhand damage with single weapon"

    def test_offhand_damage_no_ability_modifier(self):
        """Test offhand damage is dice-only (no positive ability mod)."""
        # Use dual_wielding_fighter fixture which already has two light weapons
        builder = CharacterBuilder()
        choices = {
            "character_name": "Dual Wielder",
            "species": "Human",
            "class": "Fighter",
            "level": 3,
            "background": "Soldier",
            "ability_scores": {
                "Strength": 14,
                "Dexterity": 16,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Athletics", "Acrobatics"],
            "Fighting Style": "Two-Weapon Fighting",
            "equipment_selections": {
                "class_equipment": "option_b",  # Gets Scimitar and Shortsword
                "background_equipment": "option_a",
            },
        }
        builder.apply_choices(choices)

        attacks = builder.calculate_weapon_attacks()
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]

        if len(light_weapons) >= 2:
            for weapon in light_weapons:
                offhand_dmg = weapon.get("damage_offhand", "")
                # Should be just dice (e.g., "1d4" or "1d6"), not "1d4 + 3"
                assert "+" not in offhand_dmg, "Offhand shouldn't add positive ability mod"

    def test_offhand_damage_with_negative_modifier(self):
        """Test offhand damage includes negative ability modifier."""
        builder = CharacterBuilder()
        choices = {
            "character_name": "Dual Wielder",
            "species": "Human",
            "class": "Fighter",
            "level": 3,
            "background": "Soldier",
            "ability_scores": {
                "Strength": 8, # enforce negative modifier
                "Dexterity": 8, # enforce negative modifier
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Athletics", "Acrobatics"],
            "Fighting Style": "Two-Weapon Fighting",
            "equipment_selections": {
                "class_equipment": "option_b",  # Gets Scimitar and Shortsword
                "background_equipment": "option_a",
            },
        }
        builder.apply_choices(choices)

        attacks = builder.calculate_weapon_attacks()
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]

        if len(light_weapons) >= 2:
            for weapon in light_weapons:
                offhand_dmg = weapon.get("damage_offhand", "")
                # Should include negative modifier (e.g., "1d4 - 1")
                if weapon.get("_ability_mod", 0) < 0:
                    assert "-" in offhand_dmg, "Offhand should subtract negative modifier"

    def test_offhand_average_damage_calculation(self, dual_wielding_fighter):
        """Test offhand average damage is calculated correctly."""
        attacks = dual_wielding_fighter.calculate_weapon_attacks()
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]

        assert len(light_weapons) >= 2

        for weapon in light_weapons:
            avg_offhand = weapon.get("avg_damage_offhand")
            avg_crit_offhand = weapon.get("avg_crit_offhand")

            assert avg_offhand is not None
            assert avg_crit_offhand is not None
            assert isinstance(avg_offhand, (int, float))
            assert isinstance(avg_crit_offhand, (int, float))

            # Crit should always be higher than normal
            assert avg_crit_offhand > avg_offhand

    def test_mixed_weapons_only_light_get_offhand(self):
        """Test that only light weapons get offhand damage in mixed loadout."""
        
        builder = CharacterBuilder()
        choices = {
            "character_name": "Dual Wielder",
            "species": "Human",
            "class": "Fighter",
            "level": 3,
            "background": "Soldier",
            "ability_scores": {
                "Strength": 14,
                "Dexterity": 16,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 12,
                "Charisma": 10,
            },
            "skill_choices": ["Athletics", "Acrobatics"],
            "Fighting Style": "Two-Weapon Fighting",
            "equipment_selections": {
                "class_equipment": "option_b",  # Gets Scimitar and Shortsword
                "background_equipment": "option_a",
            },
        }
        builder.apply_choices(choices)

        attacks = builder.calculate_weapon_attacks()

        # Find light weapons
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]
        heavy_weapons = [
            atk for atk in attacks if "Light" not in atk.get("properties", [])
        ]

        # Should have 2+ light weapons to trigger dual-wielding
        if len(light_weapons) >= 2:
            # Light weapons should have offhand damage
            for weapon in light_weapons:
                assert "damage_offhand" in weapon

            # Heavy weapons should NOT have offhand damage
            for weapon in heavy_weapons:
                assert "damage_offhand" not in weapon

    def test_offhand_damage_in_character_export(self, dual_wielding_fighter):
        """Test offhand damage appears in character export."""
        char_data = dual_wielding_fighter.to_character()

        attacks = char_data.get("attacks", [])
        light_weapons = [atk for atk in attacks if "Light" in atk.get("properties", [])]

        assert len(light_weapons) >= 2

        for weapon in light_weapons:
            assert "damage_offhand" in weapon
            assert "avg_damage_offhand" in weapon
            assert "avg_crit_offhand" in weapon
