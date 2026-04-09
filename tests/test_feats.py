"""Tests for D&D 2024 origin and general feats — data completeness, builder integration, effects, and choices."""

import json
import pytest
from pathlib import Path

from modules.character_builder import CharacterBuilder


DATA_DIR = Path(__file__).parent.parent / "data"

# ==================== Expected feat lists ====================

ALL_ORIGIN_FEATS = [
    "Alert", "Crafter", "Healer", "Lucky",
    "Magic Initiate (Cleric)", "Magic Initiate (Druid)", "Magic Initiate (Wizard)",
    "Musician", "Savage Attacker", "Skilled", "Tavern Brawler", "Tough",
]

ALL_GENERAL_FEATS = [
    "Ability Score Improvement", "Actor", "Athlete", "Charger", "Chef",
    "Crossbow Expert", "Crusher", "Defensive Duelist", "Dual Wielder", "Durable",
    "Elemental Adept", "Fey Touched", "Grappler", "Great Weapon Master",
    "Heavily Armored", "Heavy Armor Master", "Inspiring Leader", "Keen Mind",
    "Lightly Armored", "Lucky", "Mage Slayer", "Martial Weapon Training",
    "Medium Armor Master", "Moderately Armored", "Mounted Combatant", "Observant",
    "Piercer", "Poisoner", "Polearm Master", "Resilient", "Ritual Caster",
    "Sentinel", "Shadow Touched", "Sharpshooter", "Shield Master", "Skill Expert",
    "Skulker", "Slasher", "Speedy", "Spell Sniper", "Telekinetic", "Telepathic",
    "War Caster", "Weapon Master",
]

REQUIRED_FEAT_FIELDS = ["description", "benefits", "category", "prerequisite", "source"]


# ==================== Fixtures ====================


@pytest.fixture(scope="module")
def origin_feats():
    with open(DATA_DIR / "origin_feats.json") as f:
        return json.load(f)["origin_feats"]


@pytest.fixture(scope="module")
def general_feats():
    with open(DATA_DIR / "general_feats.json") as f:
        return json.load(f)["general_feats"]


# ==================== 1. Data Completeness Tests ====================


class TestOriginFeatsData:
    """Verify origin_feats.json has all expected feats with required structure."""

    def test_origin_feats_all_present(self, origin_feats):
        """All 12 origin feats must exist."""
        for feat_name in ALL_ORIGIN_FEATS:
            assert feat_name in origin_feats, f"Missing origin feat: {feat_name}"
        assert len(origin_feats) == len(ALL_ORIGIN_FEATS)

    @pytest.mark.parametrize("feat_name", ALL_ORIGIN_FEATS)
    def test_origin_feats_required_fields(self, origin_feats, feat_name):
        """Each origin feat must have description, benefits, category, prerequisite, source."""
        feat = origin_feats[feat_name]
        for field in REQUIRED_FEAT_FIELDS:
            assert field in feat, f"{feat_name} missing field: {field}"

    @pytest.mark.parametrize("feat_name", ALL_ORIGIN_FEATS)
    def test_origin_feats_category(self, origin_feats, feat_name):
        """All origin feats must have category 'Origin'."""
        assert origin_feats[feat_name]["category"] == "Origin"

    @pytest.mark.parametrize("feat_name", ALL_ORIGIN_FEATS)
    def test_origin_feats_source(self, origin_feats, feat_name):
        """All origin feats must have source 'Player's Handbook 2024'."""
        assert origin_feats[feat_name]["source"] == "Player's Handbook 2024"

    @pytest.mark.parametrize("feat_name", ALL_ORIGIN_FEATS)
    def test_origin_feats_no_prerequisite(self, origin_feats, feat_name):
        """Origin feats have no level prerequisite."""
        assert origin_feats[feat_name]["prerequisite"] == "None"


class TestGeneralFeatsData:
    """Verify general_feats.json has all expected feats with required structure."""

    def test_general_feats_all_present(self, general_feats):
        """All 44 general feats must exist."""
        for feat_name in ALL_GENERAL_FEATS:
            assert feat_name in general_feats, f"Missing general feat: {feat_name}"
        assert len(general_feats) == len(ALL_GENERAL_FEATS)

    @pytest.mark.parametrize("feat_name", ALL_GENERAL_FEATS)
    def test_general_feats_required_fields(self, general_feats, feat_name):
        """Each general feat must have description, benefits, category, prerequisite, source."""
        feat = general_feats[feat_name]
        for field in REQUIRED_FEAT_FIELDS:
            assert field in feat, f"{feat_name} missing field: {field}"

    @pytest.mark.parametrize("feat_name", ALL_GENERAL_FEATS)
    def test_general_feats_category(self, general_feats, feat_name):
        """All general feats must have category 'General'."""
        assert general_feats[feat_name]["category"] == "General"

    @pytest.mark.parametrize("feat_name", ALL_GENERAL_FEATS)
    def test_general_feats_source(self, general_feats, feat_name):
        """All general feats must have source 'Player's Handbook 2024'."""
        assert general_feats[feat_name]["source"] == "Player's Handbook 2024"


class TestFeatSourceConsistency:
    """All feats (origin + general) must share PLayers Handbook 2024 source."""

    def test_all_feats_source(self, origin_feats, general_feats):
        """Every single feat should have source 'Player's Handbook 2024'."""
        all_feats = {**origin_feats, **general_feats}
        for name, feat in all_feats.items():
            assert feat["source"] == "Player's Handbook 2024", (
                f"{name} has unexpected source: {feat['source']}"
            )


# ==================== 2. Builder Integration Tests ====================


class TestFeatDataLoading:
    """Verify CharacterBuilder._load_feat_data returns data for all feats."""

    @pytest.mark.parametrize("feat_name", ALL_ORIGIN_FEATS)
    def test_load_origin_feat(self, feat_name):
        """Builder can load each origin feat by name."""
        builder = CharacterBuilder()
        data = builder._load_feat_data(feat_name)
        assert data is not None, f"_load_feat_data returned None for '{feat_name}'"
        assert data["category"] == "Origin"

    @pytest.mark.parametrize("feat_name", ALL_GENERAL_FEATS)
    def test_load_general_feat(self, feat_name):
        """Builder can load each general feat by name."""
        builder = CharacterBuilder()
        data = builder._load_feat_data(feat_name)
        assert data is not None, f"_load_feat_data returned None for '{feat_name}'"
        # "Lucky" exists in both origin and general; _load_feat_data returns origin first
        if feat_name in ALL_ORIGIN_FEATS:
            assert data["category"] in ("Origin", "General")
        else:
            assert data["category"] == "General"

    def test_load_nonexistent_feat(self):
        """Unknown feat name returns None."""
        builder = CharacterBuilder()
        assert builder._load_feat_data("Nonexistent Feat") is None


# Background → feat mappings for parametrize
BACKGROUND_FEAT_PAIRS = [
    ("Acolyte", "Magic Initiate (Cleric)"),
    ("Artisan", "Crafter"),
    ("Charlatan", "Skilled"),
    ("Criminal", "Alert"),
    ("Entertainer", "Musician"),
    ("Farmer", "Tough"),
    ("Folk Hero", "Tough"),
    ("Guard", "Alert"),
    ("Guide", "Magic Initiate (Druid)"),
    ("Guild Artisan", "Crafter"),
    ("Hermit", "Healer"),
    ("Merchant", "Lucky"),
    ("Noble", "Skilled"),
    ("Sage", "Magic Initiate (Wizard)"),
    ("Sailor", "Tavern Brawler"),
    ("Scribe", "Skilled"),
    ("Soldier", "Savage Attacker"),
    ("Wayfarer", "Lucky"),
]


class TestOriginFeatFromBackground:
    """Origin feats are granted via backgrounds; verify they appear in character feats."""

    @pytest.mark.parametrize("background,expected_feat", BACKGROUND_FEAT_PAIRS)
    def test_origin_feat_from_background(self, built_character, background, expected_feat):
        """Setting a background adds the correct origin feat to character feats."""
        character = built_character({
            "character_name": "Feat Test",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": background,
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        })
        feat_names = [f["name"] for f in character["features"]["feats"]]
        assert expected_feat in feat_names, (
            f"Background '{background}' should grant feat '{expected_feat}', "
            f"but feats are: {feat_names}"
        )

    @pytest.mark.parametrize("background,expected_feat", BACKGROUND_FEAT_PAIRS)
    def test_feat_has_source(self, built_character, background, expected_feat):
        """Feat entry should record the background as its source."""
        character = built_character({
            "character_name": "Source Test",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": background,
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        })
        feat_entry = next(
            (f for f in character["features"]["feats"] if f["name"] == expected_feat),
            None,
        )
        assert feat_entry is not None
        assert feat_entry["source"] == background

    @pytest.mark.parametrize("background,expected_feat", BACKGROUND_FEAT_PAIRS)
    def test_feat_has_description(self, built_character, background, expected_feat):
        """Feat entry should have a non-empty description."""
        character = built_character({
            "character_name": "Desc Test",
            "level": 1,
            "species": "Human",
            "class": "Fighter",
            "background": background,
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        })
        feat_entry = next(
            (f for f in character["features"]["feats"] if f["name"] == expected_feat),
            None,
        )
        assert feat_entry is not None
        assert len(feat_entry["description"]) > 0


class TestToughFeatHP:
    """Tough feat should add 2 * level to HP."""

    def _build_fighter(self, background, level):
        """Helper: build a level N Human Fighter with given background."""
        builder = CharacterBuilder()
        builder.apply_choices({
            "character_name": "HP Test",
            "level": level,
            "species": "Human",
            "class": "Fighter",
            "background": background,
            "ability_scores": {
                "Strength": 15, "Dexterity": 13, "Constitution": 14,
                "Intelligence": 10, "Wisdom": 12, "Charisma": 8
            },
            "background_bonuses": {"Strength": 2, "Constitution": 1},
        })
        return builder.to_character()

    def test_tough_feat_present(self):
        """Farmer background grants Tough feat."""
        char = self._build_fighter("Farmer", 1)
        feat_names = [f["name"] for f in char["features"]["feats"]]
        assert "Tough" in feat_names

    @pytest.mark.xfail(reason="Tough feat bonus_hp effect not yet applied by builder")
    def test_tough_feat_hp_bonus_level_1(self):
        """At level 1, Tough should add 2 HP (2 * 1 = 2)."""
        tough_char = self._build_fighter("Farmer", 1)
        no_tough_char = self._build_fighter("Criminal", 1)
        tough_hp = tough_char["combat"]["hit_points"]["maximum"]
        normal_hp = no_tough_char["combat"]["hit_points"]["maximum"]
        # Tough should add 2 HP at level 1
        assert tough_hp == normal_hp + 2, (
            f"Tough HP {tough_hp} should be {normal_hp} + 2 = {normal_hp + 2}"
        )

    @pytest.mark.xfail(reason="Tough feat bonus_hp effect not yet applied by builder")
    def test_tough_feat_hp_bonus_level_5(self):
        """At level 5, Tough should add 10 HP (2 * 5 = 10)."""
        tough_char = self._build_fighter("Farmer", 5)
        no_tough_char = self._build_fighter("Criminal", 5)
        tough_hp = tough_char["combat"]["hit_points"]["maximum"]
        normal_hp = no_tough_char["combat"]["hit_points"]["maximum"]
        assert tough_hp == normal_hp + 10, (
            f"Tough HP {tough_hp} should be {normal_hp} + 10 = {normal_hp + 10}"
        )


# ==================== 3. Effects Tests ====================


class TestGeneralFeatEffects:
    """Feats with effects arrays should contain the correct effect definitions."""

    def test_lightly_armored_effects(self, general_feats):
        """Lightly Armored grants Light armor and Shields proficiency."""
        effects = general_feats["Lightly Armored"]["effects"]
        armor_effects = [e for e in effects if e["type"] == "grant_armor_proficiency"]
        assert len(armor_effects) == 1
        assert "Light armor" in armor_effects[0]["proficiencies"]
        assert "Shields" in armor_effects[0]["proficiencies"]

    def test_heavily_armored_effects(self, general_feats):
        """Heavily Armored grants Heavy armor proficiency."""
        effects = general_feats["Heavily Armored"]["effects"]
        armor_effects = [e for e in effects if e["type"] == "grant_armor_proficiency"]
        assert len(armor_effects) == 1
        assert "Heavy armor" in armor_effects[0]["proficiencies"]

    def test_moderately_armored_effects(self, general_feats):
        """Moderately Armored grants Medium armor proficiency."""
        effects = general_feats["Moderately Armored"]["effects"]
        armor_effects = [e for e in effects if e["type"] == "grant_armor_proficiency"]
        assert len(armor_effects) == 1
        assert "Medium armor" in armor_effects[0]["proficiencies"]

    def test_martial_weapon_training_effects(self, general_feats):
        """Martial Weapon Training grants Martial weapons proficiency."""
        effects = general_feats["Martial Weapon Training"]["effects"]
        weapon_effects = [e for e in effects if e["type"] == "grant_weapon_proficiency"]
        assert len(weapon_effects) == 1
        assert "Martial weapons" in weapon_effects[0]["proficiencies"]

    def test_speedy_effects(self, general_feats):
        """Speedy increases speed by 10."""
        effects = general_feats["Speedy"]["effects"]
        speed_effects = [e for e in effects if e["type"] == "increase_speed"]
        assert len(speed_effects) == 1
        assert speed_effects[0]["value"] == 10

    def test_telekinetic_effects(self, general_feats):
        """Telekinetic grants Mage Hand cantrip."""
        effects = general_feats["Telekinetic"]["effects"]
        cantrip_effects = [e for e in effects if e["type"] == "grant_cantrip"]
        assert len(cantrip_effects) == 1
        assert cantrip_effects[0]["spell"] == "Mage Hand"

    def test_fey_touched_effects(self, general_feats):
        """Fey Touched grants Misty Step spell."""
        effects = general_feats["Fey Touched"]["effects"]
        spell_effects = [e for e in effects if e["type"] == "grant_spell"]
        assert len(spell_effects) == 1
        assert spell_effects[0]["spell"] == "Misty Step"

    def test_shadow_touched_effects(self, general_feats):
        """Shadow Touched grants Invisibility spell."""
        effects = general_feats["Shadow Touched"]["effects"]
        spell_effects = [e for e in effects if e["type"] == "grant_spell"]
        assert len(spell_effects) == 1
        assert spell_effects[0]["spell"] == "Invisibility"

    def test_telepathic_effects(self, general_feats):
        """Telepathic grants Detect Thoughts spell."""
        effects = general_feats["Telepathic"]["effects"]
        spell_effects = [e for e in effects if e["type"] == "grant_spell"]
        assert len(spell_effects) == 1
        assert spell_effects[0]["spell"] == "Detect Thoughts"


class TestOriginFeatEffects:
    """Origin feats with effects should have correct definitions."""

    def test_tough_has_bonus_hp_effect(self, origin_feats):
        """Tough feat must have a bonus_hp effect with formula '2 * level'."""
        effects = origin_feats["Tough"].get("effects", [])
        hp_effects = [e for e in effects if e["type"] == "bonus_hp"]
        assert len(hp_effects) == 1
        assert hp_effects[0]["formula"] == "2 * level"


# Feats that have effects (for parametrize)
FEATS_WITH_EFFECTS = [
    ("Lightly Armored", "grant_armor_proficiency"),
    ("Heavily Armored", "grant_armor_proficiency"),
    ("Moderately Armored", "grant_armor_proficiency"),
    ("Martial Weapon Training", "grant_weapon_proficiency"),
    ("Speedy", "increase_speed"),
    ("Telekinetic", "grant_cantrip"),
    ("Fey Touched", "grant_spell"),
    ("Shadow Touched", "grant_spell"),
    ("Telepathic", "grant_spell"),
]


class TestEffectsStructure:
    """All feats with effects must have well-formed effect entries."""

    @pytest.mark.parametrize("feat_name,expected_type", FEATS_WITH_EFFECTS)
    def test_feat_has_expected_effect_type(self, general_feats, feat_name, expected_type):
        """Each feat's effects array contains the expected effect type."""
        effects = general_feats[feat_name].get("effects", [])
        effect_types = [e["type"] for e in effects]
        assert expected_type in effect_types, (
            f"{feat_name} should have effect type '{expected_type}', "
            f"but has: {effect_types}"
        )

    @pytest.mark.parametrize("feat_name,_", FEATS_WITH_EFFECTS)
    def test_effects_have_type_field(self, general_feats, feat_name, _):
        """Every effect entry must have a 'type' key."""
        effects = general_feats[feat_name].get("effects", [])
        for i, effect in enumerate(effects):
            assert "type" in effect, f"{feat_name} effect[{i}] missing 'type' field"


# ==================== 4. Choices Validation ====================


class TestFeatsWithChoices:
    """Feats containing choices arrays must have valid choice structure."""

    def _all_feats_with_choices(self, origin_feats, general_feats):
        """Return list of (feat_name, choices_array) for all feats that have choices."""
        result = []
        for name, data in origin_feats.items():
            if "choices" in data:
                result.append((name, data["choices"]))
        for name, data in general_feats.items():
            if "choices" in data:
                result.append((name, data["choices"]))
        return result

    def test_choices_is_list(self, origin_feats, general_feats):
        """choices field must be a list."""
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            assert isinstance(choices, list), f"{name}: choices should be a list"

    def test_choices_have_type(self, origin_feats, general_feats):
        """Each choice entry must have a 'type' field."""
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            for i, choice in enumerate(choices):
                assert "type" in choice, f"{name} choice[{i}] missing 'type'"

    def test_choices_have_name(self, origin_feats, general_feats):
        """Each choice entry must have a 'name' field."""
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            for i, choice in enumerate(choices):
                assert "name" in choice, f"{name} choice[{i}] missing 'name'"

    def test_choices_have_source(self, origin_feats, general_feats):
        """Each choice entry must have a 'source' field."""
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            for i, choice in enumerate(choices):
                assert "source" in choice, f"{name} choice[{i}] missing 'source'"

    def test_choice_type_is_valid(self, origin_feats, general_feats):
        """Choice type must be one of the known types."""
        valid_types = {"select_single", "select_multiple"}
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            for i, choice in enumerate(choices):
                assert choice["type"] in valid_types, (
                    f"{name} choice[{i}] has invalid type '{choice['type']}'"
                )

    def test_select_multiple_has_count(self, origin_feats, general_feats):
        """select_multiple choices must have a positive 'count' field."""
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            for i, choice in enumerate(choices):
                if choice["type"] == "select_multiple":
                    assert "count" in choice, (
                        f"{name} choice[{i}] select_multiple missing 'count'"
                    )
                    assert choice["count"] > 0, (
                        f"{name} choice[{i}] count should be > 0"
                    )

    def test_choice_source_has_type(self, origin_feats, general_feats):
        """Choice source must have a 'type' field (fixed_list or external)."""
        for name, choices in self._all_feats_with_choices(origin_feats, general_feats):
            for i, choice in enumerate(choices):
                source = choice["source"]
                assert "type" in source, (
                    f"{name} choice[{i}] source missing 'type'"
                )
                assert source["type"] in {"fixed_list", "external"}, (
                    f"{name} choice[{i}] source has invalid type '{source['type']}'"
                )


# ==================== Specific Origin Feats with Choices ====================


class TestMagicInitiateChoices:
    """Magic Initiate feats should have cantrip and spell choices."""

    @pytest.mark.parametrize("variant", [
        "Magic Initiate (Cleric)",
        "Magic Initiate (Druid)",
        "Magic Initiate (Wizard)",
    ])
    def test_has_cantrip_choice(self, origin_feats, variant):
        """Each Magic Initiate variant must have a cantrip selection (2 cantrips)."""
        choices = origin_feats[variant]["choices"]
        cantrip_choices = [c for c in choices if c["name"] == "cantrips"]
        assert len(cantrip_choices) == 1
        assert cantrip_choices[0]["type"] == "select_multiple"
        assert cantrip_choices[0]["count"] == 2

    @pytest.mark.parametrize("variant", [
        "Magic Initiate (Cleric)",
        "Magic Initiate (Druid)",
        "Magic Initiate (Wizard)",
    ])
    def test_has_spell_choice(self, origin_feats, variant):
        """Each Magic Initiate variant must have a 1st-level spell selection."""
        choices = origin_feats[variant]["choices"]
        spell_choices = [c for c in choices if c["name"] == "1st_level_spell"]
        assert len(spell_choices) == 1
        assert spell_choices[0]["type"] == "select_single"

    @pytest.mark.parametrize("variant,expected_file", [
        ("Magic Initiate (Cleric)", "spells/cleric_cantrips.json"),
        ("Magic Initiate (Druid)", "spells/druid_cantrips.json"),
        ("Magic Initiate (Wizard)", "spells/wizard_cantrips.json"),
    ])
    def test_cantrip_source_file(self, origin_feats, variant, expected_file):
        """Cantrip choices should reference the correct external spell file."""
        choices = origin_feats[variant]["choices"]
        cantrip_choice = next(c for c in choices if c["name"] == "cantrips")
        assert cantrip_choice["source"]["type"] == "external"
        assert cantrip_choice["source"]["file"] == expected_file


class TestSkilledChoices:
    """Skilled feat should allow choosing 3 skills or tools."""

    def test_skilled_choice_count(self, origin_feats):
        """Skilled allows selecting 3 skills or tools."""
        choices = origin_feats["Skilled"]["choices"]
        assert len(choices) == 1
        assert choices[0]["type"] == "select_multiple"
        assert choices[0]["count"] == 3

    def test_skilled_has_skill_options(self, origin_feats):
        """Skilled's options include standard D&D skills."""
        choices = origin_feats["Skilled"]["choices"]
        options = choices[0]["source"]["options"]
        # Spot-check some standard skills
        assert "Perception" in options
        assert "Stealth" in options
        assert "Athletics" in options
