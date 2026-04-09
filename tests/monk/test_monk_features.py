"""Tests for Monk class features and effects (D&D 2024)."""

import pytest
from modules.character_builder import CharacterBuilder


# ==================== Helpers & Fixtures ====================


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


def _build_full_monk(level=6, subclass=None, ability_scores=None,
                     background_bonuses=None):
    """Helper to build a full Monk character via apply_choices + to_character."""
    builder = CharacterBuilder()
    choices = {
        "character_name": "Test Monk",
        "level": level,
        "species": "Human",
        "class": "Monk",
        "background": "Acolyte",
        "ability_scores": ability_scores or {
            "Strength": 10, "Dexterity": 16, "Constitution": 14,
            "Intelligence": 8, "Wisdom": 15, "Charisma": 10
        },
        "background_bonuses": background_bonuses or {
            "Dexterity": 2, "Wisdom": 1
        },
    }
    if subclass and level >= 3:
        choices["subclass"] = subclass
    builder.apply_choices(choices)
    return builder


# ==================== Base Class Tests ====================


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
        """Unarmored Defense: AC = 10 + DEX + WIS.

        DEX 16 + 2 background = 18 → +4, WIS 15 + 1 background = 16 → +3.
        Expected: 10 + 4 + 3 = 17.
        """
        builder = _build_full_monk(level=1)
        character = builder.to_character()
        ac_options = character.get("ac_options", [])

        unarmored_defense = [
            opt for opt in ac_options
            if any("Unarmored Defense" in note for note in opt.get("notes", []))
        ]
        assert len(unarmored_defense) >= 1, (
            f"Expected Unarmored Defense AC option, got: {ac_options}"
        )
        assert unarmored_defense[0]["ac"] == 17, (
            f"Expected AC 17, got {unarmored_defense[0]['ac']}"
        )

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

    def test_superior_defense_feature_exists_at_level_18(self):
        """Superior Defense should exist as a class feature at level 18."""
        builder = _build_monk(level=18)
        features = builder.character_data["features"]["class"]
        names = [f["name"] for f in features]
        assert "Superior Defense" in names

    def test_no_passive_resistances_at_level_18(self):
        """Superior Defense is an activated ability (3 FP, 1 minute), NOT passive.

        It should NOT grant permanent resistances.
        """
        builder = _build_monk(level=18)
        resistances = builder.character_data["resistances"]
        assert len(resistances) == 0, (
            f"Human Monk should have no passive resistances, got: {resistances}"
        )

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


# ==================== Subclass Tests ====================


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


# ==================== Full Character Build Tests ====================


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


class TestWarriorOfMercyFullBuild:
    """Full character build tests for Warrior of Mercy at level 6."""

    @pytest.fixture
    def mercy_character(self):
        builder = _build_full_monk(level=6, subclass="Warrior of Mercy")
        return builder.to_character()

    def test_class_and_level(self, mercy_character):
        assert mercy_character["class"] == "Monk"
        assert mercy_character["level"] == 6
        assert mercy_character["subclass"] == "Warrior of Mercy"

    def test_skill_proficiencies(self, mercy_character):
        skills = mercy_character["proficiencies"]["skills"]
        assert "Insight" in skills, "Implements of Mercy should grant Insight"
        assert "Medicine" in skills, "Implements of Mercy should grant Medicine"

    def test_all_features_present(self, mercy_character):
        class_features = [f["name"] for f in mercy_character["features"]["class"]]
        subclass_features = [f["name"] for f in mercy_character["features"]["subclass"]]

        # Core class features through level 6
        assert "Martial Arts" in class_features
        assert "Unarmored Defense" in class_features
        assert "Extra Attack" in class_features

        # Subclass features
        assert "Hand of Healing" in subclass_features
        assert "Hand of Harm" in subclass_features
        assert "Physician's Touch" in subclass_features

    def test_hp_calculation(self, mercy_character):
        """L6 Monk, CON 14 → +2 modifier.

        HP = 8 (L1 max d8) + 5*5 (avg d8=5, levels 2-6) + 6*2 (CON) = 45.
        """
        hp = mercy_character["combat"]["hit_points"]["maximum"]
        assert hp == 45, f"Expected 45 HP at L6, got {hp}"

    def test_speed(self, mercy_character):
        """L6 Monk: 30 base + 10 (L2) + 5 (L6) = 45."""
        assert mercy_character["speed"] == 45

    def test_ac_includes_unarmored_defense(self, mercy_character):
        """Unarmored Defense: 10 + DEX(18→+4) + WIS(16→+3) = 17."""
        ac_options = mercy_character.get("ac_options", [])
        unarmored_defense = [
            opt for opt in ac_options
            if any("Unarmored Defense" in note for note in opt.get("notes", []))
        ]
        assert len(unarmored_defense) >= 1
        assert unarmored_defense[0]["ac"] == 17


class TestWarriorOfShadowFullBuild:
    """Full character build tests for Warrior of Shadow at level 6."""

    @pytest.fixture
    def shadow_character(self):
        builder = _build_full_monk(level=6, subclass="Warrior of Shadow")
        return builder.to_character()

    def test_class_and_level(self, shadow_character):
        assert shadow_character["class"] == "Monk"
        assert shadow_character["level"] == 6
        assert shadow_character["subclass"] == "Warrior of Shadow"

    def test_darkvision(self, shadow_character):
        assert shadow_character.get("darkvision", 0) >= 60

    def test_minor_illusion_cantrip(self, shadow_character):
        spells = shadow_character.get("spells", {}).get("always_prepared", {})
        assert "Minor Illusion" in spells

    def test_shadow_step_feature(self, shadow_character):
        subclass_features = [
            f["name"] for f in shadow_character["features"]["subclass"]
        ]
        assert "Shadow Step" in subclass_features

    def test_all_features_present(self, shadow_character):
        class_features = [f["name"] for f in shadow_character["features"]["class"]]
        subclass_features = [
            f["name"] for f in shadow_character["features"]["subclass"]
        ]

        assert "Martial Arts" in class_features
        assert "Unarmored Defense" in class_features
        assert "Extra Attack" in class_features
        assert "Shadow Arts" in subclass_features
        assert "Shadow Step" in subclass_features

    def test_hp_calculation(self, shadow_character):
        """L6, CON 14 → +2. HP = 8 + 5*5 + 6*2 = 45."""
        hp = shadow_character["combat"]["hit_points"]["maximum"]
        assert hp == 45, f"Expected 45 HP at L6, got {hp}"

    def test_speed(self, shadow_character):
        assert shadow_character["speed"] == 45

    def test_ac_includes_unarmored_defense(self, shadow_character):
        ac_options = shadow_character.get("ac_options", [])
        unarmored_defense = [
            opt for opt in ac_options
            if any("Unarmored Defense" in note for note in opt.get("notes", []))
        ]
        assert len(unarmored_defense) >= 1
        assert unarmored_defense[0]["ac"] == 17


class TestWarriorOfTheElementsFullBuild:
    """Full character build tests for Warrior of the Elements at level 6."""

    @pytest.fixture
    def elements_character(self):
        builder = _build_full_monk(level=6, subclass="Warrior of the Elements")
        return builder.to_character()

    def test_class_and_level(self, elements_character):
        assert elements_character["class"] == "Monk"
        assert elements_character["level"] == 6
        assert elements_character["subclass"] == "Warrior of the Elements"

    def test_elementalism_cantrip(self, elements_character):
        spells = elements_character.get("spells", {}).get("always_prepared", {})
        assert "Elementalism" in spells

    def test_all_features_present(self, elements_character):
        class_features = [f["name"] for f in elements_character["features"]["class"]]
        subclass_features = [
            f["name"] for f in elements_character["features"]["subclass"]
        ]

        assert "Martial Arts" in class_features
        assert "Unarmored Defense" in class_features
        assert "Extra Attack" in class_features
        assert "Elemental Attunement" in subclass_features
        assert "Elemental Burst" in subclass_features

    def test_hp_calculation(self, elements_character):
        hp = elements_character["combat"]["hit_points"]["maximum"]
        assert hp == 45, f"Expected 45 HP at L6, got {hp}"

    def test_speed(self, elements_character):
        assert elements_character["speed"] == 45

    def test_ac_includes_unarmored_defense(self, elements_character):
        ac_options = elements_character.get("ac_options", [])
        unarmored_defense = [
            opt for opt in ac_options
            if any("Unarmored Defense" in note for note in opt.get("notes", []))
        ]
        assert len(unarmored_defense) >= 1
        assert unarmored_defense[0]["ac"] == 17


class TestWarriorOfTheOpenHandFullBuild:
    """Full character build tests for Warrior of the Open Hand at level 6."""

    @pytest.fixture
    def open_hand_character(self):
        builder = _build_full_monk(level=6, subclass="Warrior of the Open Hand")
        return builder.to_character()

    def test_class_and_level(self, open_hand_character):
        assert open_hand_character["class"] == "Monk"
        assert open_hand_character["level"] == 6
        assert open_hand_character["subclass"] == "Warrior of the Open Hand"

    def test_all_features_present(self, open_hand_character):
        class_features = [f["name"] for f in open_hand_character["features"]["class"]]
        subclass_features = [
            f["name"] for f in open_hand_character["features"]["subclass"]
        ]

        assert "Martial Arts" in class_features
        assert "Unarmored Defense" in class_features
        assert "Extra Attack" in class_features
        assert "Open Hand Technique" in subclass_features
        assert "Wholeness of Body" in subclass_features

    def test_hp_calculation(self, open_hand_character):
        hp = open_hand_character["combat"]["hit_points"]["maximum"]
        assert hp == 45, f"Expected 45 HP at L6, got {hp}"

    def test_speed(self, open_hand_character):
        assert open_hand_character["speed"] == 45

    def test_ac_includes_unarmored_defense(self, open_hand_character):
        ac_options = open_hand_character.get("ac_options", [])
        unarmored_defense = [
            opt for opt in ac_options
            if any("Unarmored Defense" in note for note in opt.get("notes", []))
        ]
        assert len(unarmored_defense) >= 1
        assert unarmored_defense[0]["ac"] == 17
