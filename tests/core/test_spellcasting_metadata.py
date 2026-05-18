import json
from pathlib import Path

import pytest


CLASSES_DIR = Path(__file__).resolve().parents[2] / "data" / "classes"


def _load_class_data(class_name: str) -> dict:
    with (CLASSES_DIR / f"{class_name}.json").open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    "class_name,spellcasting_type,formula,ritual_casting,feature_name",
    [
        ("bard", "prepared", "level + charisma_modifier", True, "Spellcasting"),
        ("druid", "prepared", "level + wisdom_modifier", True, "Spellcasting"),
        ("paladin", "prepared", "level + charisma_modifier", False, "Spellcasting"),
        ("ranger", "prepared", "level + wisdom_modifier", False, "Spellcasting"),
        ("sorcerer", "known", "class_table", False, "Spellcasting"),
        ("warlock", "pact_magic", "class_table", False, "Pact Magic"),
    ],
)
def test_spellcasting_metadata_is_complete(
    class_name: str,
    spellcasting_type: str,
    formula: str,
    ritual_casting: bool,
    feature_name: str,
):
    class_data = _load_class_data(class_name)

    assert class_data["spellcasting_type"] == spellcasting_type
    assert class_data["spell_preparation_formula"] == formula
    assert class_data["cantrip_progression"] == "class_table"
    assert class_data["spell_list_restrictions"] is None
    assert class_data["ritual_casting"] is ritual_casting
    assert "cantrips_by_level" in class_data

    level_1_features = class_data["features_by_level"]["1"]
    assert isinstance(level_1_features[feature_name], dict)
    assert isinstance(level_1_features[feature_name]["description"], str)


@pytest.mark.parametrize("class_name", ["paladin", "ranger"])
def test_half_casters_have_zero_cantrip_progression(class_name: str):
    class_data = _load_class_data(class_name)
    cantrip_progression = class_data["cantrips_by_level"]

    assert all(count == 0 for count in cantrip_progression.values())


def test_warlock_uses_pact_magic_slots_metadata():
    class_data = _load_class_data("warlock")

    assert class_data["spellcasting_type"] == "pact_magic"
    assert isinstance(class_data["pact_magic_slots_by_level"], dict)
    assert "spell_slots_by_level" not in class_data
