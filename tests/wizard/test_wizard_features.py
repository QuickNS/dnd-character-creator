#!/usr/bin/env python3
"""
Pytest tests for Wizard class and subclass features.

Tests cover:
- Base Wizard class proficiencies, features, spellcasting, spell slots, and HP
- Abjurer (Abjuration) subclass features and effects
- Diviner (Divination) subclass features
- Evoker (Evocation) subclass features and progression
- Illusionist subclass features and spell grants
"""

import pytest
from modules.character_builder import CharacterBuilder


def build_wizard(level, subclass=None):
    """Helper to build a Wizard character at a given level.

    Uses Human species, Sage background, and a standard ability array that
    produces Int 17 (+3) after background bonuses (+2 Int, +1 Con).

    Subclass names must match the JSON filenames under data/subclasses/wizard/:
        Abjuration, Divination, Evocation, Illusionist
    """
    builder = CharacterBuilder()
    builder.set_species("Human")
    builder.set_class("Wizard", level)
    builder.set_background("Sage")
    builder.set_abilities(
        {
            "Strength": 8,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 15,
            "Wisdom": 12,
            "Charisma": 10,
        },
        background_bonuses={"Intelligence": 2, "Constitution": 1},
    )
    if subclass and level >= 3:
        builder.set_subclass(subclass)
    return builder.to_character()


# ---------------------------------------------------------------------------
# 1. Base Wizard Class
# ---------------------------------------------------------------------------


class TestWizardBaseClass:
    """Test Wizard base class proficiencies, features, and core mechanics."""

    # -- Proficiencies --

    def test_saving_throw_proficiencies(self):
        character = build_wizard(1)
        saves = character["proficiencies"]["saving_throws"]
        assert "Intelligence" in saves
        assert "Wisdom" in saves

    def test_weapon_proficiencies(self):
        character = build_wizard(1)
        weapons = character["proficiencies"]["weapons"]
        assert "Simple weapons" in weapons

    def test_no_armor_proficiencies(self):
        character = build_wizard(1)
        armor = character["proficiencies"]["armor"]
        assert armor == []

    # -- Hit Die / HP --

    def test_hit_die(self):
        character = build_wizard(1)
        assert character["class_data"]["hit_die"] == 6

    def test_hit_points_level_1(self):
        """Level 1 HP = 6 (max d6) + 2 (Con mod from 14 Con) = 8."""
        character = build_wizard(1)
        hp = character["combat"]["hit_points"]
        assert hp["maximum"] == 8

    def test_hit_points_level_5(self):
        """Level 5 HP: 6 + 4*4(avg d6) + 5*2(Con) = 6+16+10 = 32."""
        character = build_wizard(5, "Evocation")
        hp = character["combat"]["hit_points"]
        assert hp["maximum"] == 32

    # -- Spellcasting basics --

    def test_has_spellcasting(self):
        character = build_wizard(1)
        stats = character["spellcasting_stats"]
        assert stats["has_spellcasting"] is True

    def test_spellcasting_ability_is_intelligence(self):
        character = build_wizard(1)
        stats = character["spellcasting_stats"]
        assert stats["spellcasting_ability"] == "Intelligence"

    def test_spell_save_dc_level_1(self):
        """DC = 8 + prof(2) + Int mod(3) = 13."""
        character = build_wizard(1)
        stats = character["spellcasting_stats"]
        assert stats["spell_save_dc"] == 13

    def test_spell_attack_bonus_level_1(self):
        """Attack = prof(2) + Int mod(3) = 5."""
        character = build_wizard(1)
        stats = character["spellcasting_stats"]
        assert stats["spell_attack_bonus"] == 5

    def test_max_prepared_spells_level_1(self):
        """Wizard prepared spells at level 1 = 4 (from prepared_spells_by_level)."""
        character = build_wizard(1)
        stats = character["spellcasting_stats"]
        assert stats["max_spells_prepared"] == 4

    # -- Spell slot progression --

    def test_spell_slots_level_1(self):
        character = build_wizard(1)
        slots = character["spell_slots"]
        assert slots["1st"] == 2
        assert "2nd" not in slots

    def test_spell_slots_level_5(self):
        character = build_wizard(5, "Evocation")
        slots = character["spell_slots"]
        assert slots["1st"] == 4
        assert slots["2nd"] == 3
        assert slots["3rd"] == 2

    def test_spell_slots_level_9(self):
        character = build_wizard(9, "Evocation")
        slots = character["spell_slots"]
        assert slots["1st"] == 4
        assert slots["2nd"] == 3
        assert slots["3rd"] == 3
        assert slots["4th"] == 3
        assert slots["5th"] == 1

    # -- Class feature progression --

    def test_level_1_features(self):
        """Level 1: Spellcasting, Ritual Adept, Arcane Recovery."""
        character = build_wizard(1)
        names = [f["name"] for f in character["features"]["class"]]
        assert "Spellcasting" in names
        assert "Ritual Adept" in names
        assert "Arcane Recovery" in names

    def test_level_3_wizard_subclass_feature(self):
        """Level 3 class feature list should include 'Wizard Subclass'."""
        character = build_wizard(3, "Evocation")
        names = [f["name"] for f in character["features"]["class"]]
        assert "Wizard Subclass" in names

    def test_level_5_memorize_spell(self):
        """Level 5 should grant Memorize Spell class feature."""
        character = build_wizard(5, "Evocation")
        names = [f["name"] for f in character["features"]["class"]]
        assert "Memorize Spell" in names

    @pytest.mark.parametrize(
        "level,expected_features",
        [
            (1, ["Spellcasting", "Ritual Adept", "Arcane Recovery"]),
            (3, ["Wizard Subclass"]),
            (4, ["Ability Score Improvement"]),
            (5, ["Memorize Spell"]),
        ],
    )
    def test_class_feature_progression(self, level, expected_features):
        character = build_wizard(level, "Evocation" if level >= 3 else None)
        names = [f["name"] for f in character["features"]["class"]]
        for feature_name in expected_features:
            assert feature_name in names, (
                f"Expected '{feature_name}' at level {level}, got {names}"
            )


# ---------------------------------------------------------------------------
# 2. Abjurer (Abjuration) Subclass
# ---------------------------------------------------------------------------


class TestAbjurerSubclass:
    """Test Abjuration subclass features and effects."""

    def test_level_3_arcane_ward(self):
        character = build_wizard(3, "Abjuration")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Arcane Ward" in names

    def test_level_6_projected_ward(self):
        character = build_wizard(6, "Abjuration")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Projected Ward" in names

    def test_level_10_spell_breaker(self):
        character = build_wizard(10, "Abjuration")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Spell Breaker" in names

    def test_spell_breaker_grants_counterspell(self):
        """Spell Breaker at L10 should grant Counterspell as always prepared."""
        character = build_wizard(10, "Abjuration")
        always_prepared = character["spells"]["always_prepared"]
        assert "Counterspell" in always_prepared

    def test_spell_breaker_grants_dispel_magic(self):
        """Spell Breaker at L10 should grant Dispel Magic as always prepared."""
        character = build_wizard(10, "Abjuration")
        always_prepared = character["spells"]["always_prepared"]
        assert "Dispel Magic" in always_prepared

    def test_spell_breaker_effects(self):
        """Spell Breaker effects should include grant_spell for both spells."""
        character = build_wizard(10, "Abjuration")
        effects = character.get("effects", [])
        spell_grants = [e for e in effects if e.get("type") == "grant_spell"]
        granted_spells = [e.get("spell") for e in spell_grants]
        assert "Counterspell" in granted_spells
        assert "Dispel Magic" in granted_spells

    def test_level_14_spell_resistance(self):
        character = build_wizard(14, "Abjuration")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Spell Resistance" in names

    def test_spell_resistance_save_advantage(self):
        """Spell Resistance should grant save advantage against spells."""
        character = build_wizard(14, "Abjuration")
        save_advs = character.get("save_advantages", [])
        assert len(save_advs) > 0
        spell_adv = [a for a in save_advs if a.get("condition") == "against spells"]
        assert len(spell_adv) == 1
        assert "Strength" in spell_adv[0]["abilities"]
        assert "Wisdom" in spell_adv[0]["abilities"]

    def test_spell_resistance_effect_in_effects_list(self):
        """Spell Resistance effect should appear in the effects export."""
        character = build_wizard(14, "Abjuration")
        effects = character.get("effects", [])
        save_adv_effects = [
            e for e in effects if e.get("type") == "grant_save_advantage"
        ]
        assert len(save_adv_effects) >= 1
        assert save_adv_effects[0]["condition"] == "against spells"

    def test_spell_resistance_not_before_level_14(self):
        """At level 13, Spell Resistance should not yet be present."""
        character = build_wizard(13, "Abjuration")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Spell Resistance" not in names
        save_advs = character.get("save_advantages", [])
        spell_adv = [a for a in save_advs if a.get("condition") == "against spells"]
        assert len(spell_adv) == 0

    @pytest.mark.parametrize(
        "level,expected_features",
        [
            (3, ["Arcane Ward"]),
            (6, ["Projected Ward"]),
            (10, ["Spell Breaker"]),
            (14, ["Spell Resistance"]),
        ],
    )
    def test_abjurer_feature_progression(self, level, expected_features):
        character = build_wizard(level, "Abjuration")
        names = [f["name"] for f in character["features"]["subclass"]]
        for feature_name in expected_features:
            assert feature_name in names, (
                f"Expected '{feature_name}' at level {level}"
            )


# ---------------------------------------------------------------------------
# 3. Diviner (Divination) Subclass
# ---------------------------------------------------------------------------


class TestDivinerSubclass:
    """Test Divination subclass features."""

    def test_level_3_portent(self):
        character = build_wizard(3, "Divination")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Portent" in names

    def test_level_6_expert_divination(self):
        character = build_wizard(6, "Divination")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Expert Divination" in names

    def test_level_10_the_third_eye(self):
        character = build_wizard(10, "Divination")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "The Third Eye" in names

    def test_level_14_greater_portent(self):
        character = build_wizard(14, "Divination")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Greater Portent" in names

    def test_greater_portent_not_before_level_14(self):
        character = build_wizard(13, "Divination")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Greater Portent" not in names

    @pytest.mark.parametrize(
        "level,expected_features",
        [
            (3, ["Portent"]),
            (6, ["Expert Divination"]),
            (10, ["The Third Eye"]),
            (14, ["Greater Portent"]),
        ],
    )
    def test_diviner_feature_progression(self, level, expected_features):
        character = build_wizard(level, "Divination")
        names = [f["name"] for f in character["features"]["subclass"]]
        for feature_name in expected_features:
            assert feature_name in names, (
                f"Expected '{feature_name}' at level {level}"
            )


# ---------------------------------------------------------------------------
# 4. Evoker (Evocation) Subclass
# ---------------------------------------------------------------------------


class TestEvokerSubclass:
    """Test Evocation subclass features and progression."""

    def test_level_3_potent_cantrip(self):
        character = build_wizard(3, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Potent Cantrip" in names

    
    def test_sculpt_spells_not_at_level_3(self):
        """Sculpt Spells is a L6 feature, not L3 (2024 rules)."""
        character = build_wizard(3, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Sculpt Spells" not in names

    def test_level_6_sculpt_spells(self):
        character = build_wizard(6, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Sculpt Spells" in names

    def test_level_10_empowered_evocation(self):
        character = build_wizard(10, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Empowered Evocation" in names

    def test_level_14_overchannel(self):
        character = build_wizard(14, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Overchannel" in names

    def test_overchannel_not_before_level_14(self):
        character = build_wizard(13, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Overchannel" not in names

    @pytest.mark.parametrize(
        "level,expected_features",
        [
            (3, ["Potent Cantrip"]),
            (6, ["Sculpt Spells"]),
            (10, ["Empowered Evocation"]),
            (14, ["Overchannel"]),
        ],
    )
    def test_evoker_feature_progression(self, level, expected_features):
        character = build_wizard(level, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        for feature_name in expected_features:
            assert feature_name in names, (
                f"Expected '{feature_name}' at level {level}"
            )

    def test_evoker_full_progression_at_level_14(self):
        """At L14 all four evoker features should be present."""
        character = build_wizard(14, "Evocation")
        names = [f["name"] for f in character["features"]["subclass"]]
        for feature in ["Potent Cantrip", "Sculpt Spells", "Empowered Evocation", "Overchannel"]:
            assert feature in names


# ---------------------------------------------------------------------------
# 5. Illusionist Subclass
# ---------------------------------------------------------------------------


class TestIllusionistSubclass:
    """Test Illusionist subclass features and spell grants."""

    def test_level_3_improved_illusions(self):
        character = build_wizard(3, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Improved Illusions" in names


    def test_improved_illusions_grants_minor_illusion(self):
        """Improved Illusions should add Minor Illusion as always prepared."""
        character = build_wizard(3, "Illusionist")
        always_prepared = character["spells"]["always_prepared"]
        assert "Minor Illusion" in always_prepared

    def test_improved_illusions_grant_cantrip_effect(self):
        """The grant_cantrip effect should appear in exported effects."""
        character = build_wizard(3, "Illusionist")
        effects = character.get("effects", [])
        cantrip_effects = [e for e in effects if e.get("type") == "grant_cantrip"]
        assert len(cantrip_effects) >= 1
        granted = [e.get("spell") for e in cantrip_effects]
        assert "Minor Illusion" in granted

    def test_level_6_phantasmal_creatures(self):
        character = build_wizard(6, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Phantasmal Creatures" in names

    def test_phantasmal_creatures_grants_summon_beast(self):
        """Phantasmal Creatures at L6 should grant Summon Beast as always prepared."""
        character = build_wizard(6, "Illusionist")
        always_prepared = character["spells"]["always_prepared"]
        assert "Summon Beast" in always_prepared

    def test_phantasmal_creatures_grants_summon_fey(self):
        """Phantasmal Creatures at L6 should grant Summon Fey as always prepared."""
        character = build_wizard(6, "Illusionist")
        always_prepared = character["spells"]["always_prepared"]
        assert "Summon Fey" in always_prepared

    def test_phantasmal_creatures_not_at_level_3(self):
        """At L3, Summon Beast and Summon Fey should not be granted yet."""
        character = build_wizard(3, "Illusionist")
        always_prepared = character["spells"]["always_prepared"]
        assert "Summon Beast" not in always_prepared
        assert "Summon Fey" not in always_prepared

    def test_level_10_illusory_self(self):
        character = build_wizard(10, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Illusory Self" in names

    def test_level_14_illusory_reality(self):
        character = build_wizard(14, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Illusory Reality" in names

    def test_illusory_reality_not_before_level_14(self):
        character = build_wizard(13, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        assert "Illusory Reality" not in names

    @pytest.mark.parametrize(
        "level,expected_features",
        [
            (3, ["Improved Illusions"]),
            (6, ["Phantasmal Creatures"]),
            (10, ["Illusory Self"]),
            (14, ["Illusory Reality"]),
        ],
    )
    def test_illusionist_feature_progression(self, level, expected_features):
        character = build_wizard(level, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        for feature_name in expected_features:
            assert feature_name in names, (
                f"Expected '{feature_name}' at level {level}"
            )

    def test_illusionist_full_progression_at_level_14(self):
        """At L14 all four illusionist features should be present."""
        character = build_wizard(14, "Illusionist")
        names = [f["name"] for f in character["features"]["subclass"]]
        for feature in [
            "Improved Illusions",
            "Phantasmal Creatures",
            "Illusory Self",
            "Illusory Reality",
        ]:
            assert feature in names


# ---------------------------------------------------------------------------
# 6. Cross-cutting / edge-case tests
# ---------------------------------------------------------------------------


class TestWizardEffectsAndEdgeCases:
    """Miscellaneous tests covering effects, spell-slot edge cases, etc."""

    def test_effects_list_present_in_output(self):
        """The to_character() output should always include an 'effects' list."""
        character = build_wizard(1)
        assert "effects" in character
        assert isinstance(character["effects"], list)

    def test_no_subclass_features_before_level_3(self):
        """At level 2, subclass features list should be empty."""
        character = build_wizard(2)
        assert character["features"]["subclass"] == []

    def test_subclass_name_stored(self):
        """The chosen subclass name should be stored on the character."""
        character = build_wizard(3, "Evocation")
        assert character["subclass"] == "Evocation"

    def test_proficiency_bonus_at_level_1(self):
        character = build_wizard(1)
        assert character["proficiency_bonus"] == 2

    def test_proficiency_bonus_at_level_5(self):
        character = build_wizard(5, "Evocation")
        assert character["proficiency_bonus"] == 3

    def test_proficiency_bonus_at_level_9(self):
        character = build_wizard(9, "Evocation")
        assert character["proficiency_bonus"] == 4

    def test_spell_save_dc_scales_with_proficiency(self):
        """At L5 prof=3, Int mod=3 → DC = 8+3+3 = 14."""
        character = build_wizard(5, "Evocation")
        stats = character["spellcasting_stats"]
        assert stats["spell_save_dc"] == 14

    def test_spell_attack_bonus_scales_with_proficiency(self):
        """At L5 prof=3, Int mod=3 → attack = 3+3 = 6."""
        character = build_wizard(5, "Evocation")
        stats = character["spellcasting_stats"]
        assert stats["spell_attack_bonus"] == 6

    def test_combat_stats_structure(self):
        """Verify the shape of the combat stats dictionary."""
        character = build_wizard(1)
        combat = character["combat"]
        assert "hit_points" in combat
        assert "maximum" in combat["hit_points"]
        assert "current" in combat["hit_points"]
        assert "armor_class" in combat
        assert "initiative" in combat
        assert "speed" in combat
        assert "hit_dice" in combat

    def test_hp_breakdown_present(self):
        """HP breakdown should include base, con bonus, and total."""
        character = build_wizard(1)
        breakdown = character["combat"]["hp_breakdown"]
        assert breakdown["base_hp"] == 6
        assert breakdown["constitution_modifier"] == 2
        assert breakdown["total_hp"] == 8
        assert breakdown["hit_die"] == 6

    @pytest.mark.parametrize(
        "level,expected_slots",
        [
            (1, {"1st": 2}),
            (3, {"1st": 4, "2nd": 2}),
            (5, {"1st": 4, "2nd": 3, "3rd": 2}),
            (7, {"1st": 4, "2nd": 3, "3rd": 3, "4th": 1}),
            (9, {"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 1}),
        ],
    )
    def test_full_spell_slot_progression(self, level, expected_slots):
        character = build_wizard(level, "Evocation" if level >= 3 else None)
        slots = character["spell_slots"]
        for slot_level, count in expected_slots.items():
            assert slots.get(slot_level) == count, (
                f"Expected {slot_level}={count} at wizard level {level}, "
                f"got {slots.get(slot_level)}"
            )
