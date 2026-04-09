"""Tests for Monk class features and effects (D&D 2024)."""

import pytest
from modules.character_builder import CharacterBuilder


@pytest.fixture
def monk_builder():
    """Fresh CharacterBuilder for Monk tests."""
    return CharacterBuilder()


def _build_monk(level=1, subclass=None):
    """Helper to build a Monk character at a given level."""
    builder = CharacterBuilder()
    builder.set_species("Human")
    builder.set_class("Monk", level)
    if subclass and level >= 3:
        builder.set_subclass(subclass)
    return builder


class TestMonkBasicSetup:

    def test_monk_class_setup(self, monk_builder):
        builder = monk_builder
        builder.set_species("Human")
        builder.set_class("Monk", 1)

        data = builder.character_data
        assert data["class"] == "Monk"
        assert data["level"] == 1

        # Saving throws
        saves = data["proficiencies"]["saving_throws"]
        assert "Strength" in saves
        assert "Dexterity" in saves

        # Weapons — 2024 Monk
        weapons = data["proficiencies"]["weapons"]
        assert "Simple weapons" in weapons
        assert "Martial weapons that have the Light property" in weapons

        # No armor proficiency
        assert data["proficiencies"]["armor"] == []

    def test_monk_features_level_1(self, monk_builder):
        builder = monk_builder
        builder.set_species("Human")
        builder.set_class("Monk", 1)

        features = builder.character_data["features"]["class"]
        names = [f["name"] for f in features]
        assert "Martial Arts" in names
        assert "Unarmored Defense" in names

    def test_monk_features_level_5(self):
        builder = _build_monk(level=5)
        features = builder.character_data["features"]["class"]
        names = [f["name"] for f in features]
        assert "Extra Attack" in names
        assert "Stunning Strike" in names
        assert "Deflect Attacks" in names
        assert "Slow Fall" in names


class TestUnarmoredDefense:

    def test_unarmored_defense_ac_option(self):
        builder = _build_monk(level=1)
        builder.apply_choices({
            "character_name": "Monk Test",
            "level": 1,
            "species": "Human",
            "class": "Monk",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10, "Dexterity": 16, "Constitution": 12,
                "Intelligence": 8, "Wisdom": 16, "Charisma": 10
            },
            "background_bonuses": {"Dexterity": 2, "Wisdom": 1},
        })
        character = builder.to_character()
        ac_options = character.get("ac_options", [])

        # Should have an Unarmored Defense option with 10 + DEX(+3) + WIS(+3) = 16
        # (With +2 DEX from background: DEX=18 → +4, WIS=17 → +3, so 10+4+3=17)
        unarmored_defense = [
            opt for opt in ac_options
            if "Unarmored Defense" in (opt.get("notes", []) or [" "])[0]
            if opt.get("notes")
        ]
        assert len(unarmored_defense) >= 1
        # The alternative AC should be higher than standard unarmored (10 + DEX)
        standard_unarmored = [
            opt for opt in ac_options
            if opt.get("equipped_armor") is None and not opt.get("notes")
        ]
        if standard_unarmored and unarmored_defense:
            assert unarmored_defense[0]["ac"] >= standard_unarmored[0]["ac"]

    def test_alternative_ac_effect_applied(self):
        builder = _build_monk(level=1)
        effects = builder.applied_effects
        alt_ac_effects = [e for e in effects if e["type"] == "alternative_ac"]
        assert len(alt_ac_effects) == 1
        assert alt_ac_effects[0]["effect"]["modifiers"] == ["dexterity", "wisdom"]


class TestUnarmoredMovement:

    def test_speed_increase_level_2(self):
        builder = _build_monk(level=2)
        assert builder.character_data["speed"] == 40  # 30 base + 10

    def test_speed_increase_level_6(self):
        builder = _build_monk(level=6)
        assert builder.character_data["speed"] == 45  # 30 + 10 + 5

    def test_speed_increase_level_10(self):
        builder = _build_monk(level=10)
        assert builder.character_data["speed"] == 50  # 30 + 10 + 5 + 5

    def test_speed_increase_level_14(self):
        builder = _build_monk(level=14)
        assert builder.character_data["speed"] == 55  # 30 + 10 + 5 + 5 + 5

    def test_speed_increase_level_18(self):
        builder = _build_monk(level=18)
        assert builder.character_data["speed"] == 60  # 30 + 10 + 5 + 5 + 5 + 5

    def test_no_speed_increase_level_1(self):
        builder = _build_monk(level=1)
        assert builder.character_data["speed"] == 30


class TestDisciplinedSurvivor:

    def test_all_save_proficiencies_at_level_14(self):
        builder = _build_monk(level=14)
        saves = builder.character_data["proficiencies"]["saving_throws"]
        for ability in ["Strength", "Dexterity", "Constitution",
                        "Intelligence", "Wisdom", "Charisma"]:
            assert ability in saves, f"Missing save proficiency: {ability}"

    def test_no_extra_saves_before_level_14(self):
        builder = _build_monk(level=13)
        saves = builder.character_data["proficiencies"]["saving_throws"]
        # Should only have Strength and Dexterity from base class
        assert "Constitution" not in saves
        assert "Intelligence" not in saves
        assert "Charisma" not in saves


class TestSuperiorDefense:

    def test_damage_resistances_at_level_18(self):
        builder = _build_monk(level=18)
        resistances = builder.character_data["resistances"]
        expected = [
            "Bludgeoning", "Piercing", "Slashing",
            "Acid", "Cold", "Fire", "Lightning",
            "Necrotic", "Poison", "Psychic", "Radiant", "Thunder"
        ]
        for dmg_type in expected:
            assert dmg_type in resistances, f"Missing resistance: {dmg_type}"
        # Force should NOT be resisted
        assert "Force" not in resistances

    def test_no_resistances_before_level_18(self):
        builder = _build_monk(level=17)
        # Human has no innate resistances
        resistances = builder.character_data["resistances"]
        assert len(resistances) == 0


class TestBodyAndMind:

    def test_ability_bonuses_at_level_20(self):
        builder = _build_monk(level=20)
        bonuses = builder.character_data.get("ability_bonuses", [])
        dex_bonus = [b for b in bonuses if b["ability"] == "Dexterity"]
        wis_bonus = [b for b in bonuses if b["ability"] == "Wisdom"]
        assert len(dex_bonus) >= 1
        assert dex_bonus[0]["value"] == 4
        assert len(wis_bonus) >= 1
        assert wis_bonus[0]["value"] == 4


class TestWarriorOfMercy:

    def test_implements_of_mercy_proficiencies(self):
        builder = _build_monk(level=3, subclass="Warrior of Mercy")
        skills = builder.character_data["proficiencies"]["skills"]
        assert "Insight" in skills
        assert "Medicine" in skills

    def test_features_present(self):
        builder = _build_monk(level=3, subclass="Warrior of Mercy")
        features = builder.character_data["features"]["subclass"]
        names = [f["name"] for f in features]
        assert "Hand of Healing" in names
        assert "Hand of Harm" in names


class TestWarriorOfShadow:

    def test_shadow_arts_darkvision(self):
        builder = _build_monk(level=3, subclass="Warrior of Shadow")
        assert builder.character_data["darkvision"] >= 60

    def test_shadow_arts_cantrip(self):
        builder = _build_monk(level=3, subclass="Warrior of Shadow")
        spells = builder.character_data["spells"]["always_prepared"]
        assert "Minor Illusion" in spells

    def test_features_present(self):
        builder = _build_monk(level=6, subclass="Warrior of Shadow")
        features = builder.character_data["features"]["subclass"]
        names = [f["name"] for f in features]
        assert "Shadow Step" in names


class TestWarriorOfTheElements:

    def test_manipulate_elements_cantrip(self):
        builder = _build_monk(level=3, subclass="Warrior of the Elements")
        spells = builder.character_data["spells"]["always_prepared"]
        assert "Elementalism" in spells

    def test_features_present(self):
        builder = _build_monk(level=3, subclass="Warrior of the Elements")
        features = builder.character_data["features"]["subclass"]
        names = [f["name"] for f in features]
        assert "Elemental Attunement" in names


class TestWarriorOfTheOpenHand:

    def test_open_hand_technique(self):
        builder = _build_monk(level=3, subclass="Warrior of the Open Hand")
        features = builder.character_data["features"]["subclass"]
        names = [f["name"] for f in features]
        assert "Open Hand Technique" in names

    def test_high_level_features(self):
        builder = _build_monk(level=17, subclass="Warrior of the Open Hand")
        features = builder.character_data["features"]["subclass"]
        names = [f["name"] for f in features]
        assert "Quivering Palm" in names
        assert "Fleet Step" in names
        assert "Wholeness of Body" in names


class TestMonkFullBuild:

    def test_full_character_build(self):
        builder = CharacterBuilder()
        result = builder.apply_choices({
            "character_name": "Shadow Monk",
            "level": 10,
            "species": "Human",
            "class": "Monk",
            "subclass": "Warrior of Shadow",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10, "Dexterity": 16, "Constitution": 14,
                "Intelligence": 8, "Wisdom": 15, "Charisma": 12
            },
            "background_bonuses": {"Dexterity": 2, "Wisdom": 1},
        })
        assert result is True

        character = builder.to_character()
        assert character["class"] == "Monk"
        assert character["level"] == 10
        assert character["speed"] >= 50  # 30 + 10(L2) + 5(L6) + 5(L10)

        # Should have darkvision from Shadow Arts
        assert character.get("darkvision", 0) >= 60

        # Should have Minor Illusion
        spells = character.get("spells", {}).get("always_prepared", {})
        assert "Minor Illusion" in spells
