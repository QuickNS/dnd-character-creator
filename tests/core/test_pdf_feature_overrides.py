#!/usr/bin/env python3

from modules.character_builder import CharacterBuilder


def _class_feature_names(builder: CharacterBuilder) -> list[str]:
    return [f.get("name") for f in builder.character_data["features"]["class"]]


def _class_feature(builder: CharacterBuilder, name: str):
    for feature in builder.character_data["features"]["class"]:
        if feature.get("name") == name:
            return feature
    return None


def test_wizard_subclass_placeholder_not_in_class_features():
    builder = CharacterBuilder()
    assert builder.set_class("Wizard", 3) is True

    assert "Wizard Subclass" not in _class_feature_names(builder)


def test_ability_score_improvement_not_in_class_features():
    builder = CharacterBuilder()
    assert builder.set_class("Fighter", 4) is True

    assert "Ability Score Improvement" not in _class_feature_names(builder)


def test_feature_override_pdf_summary_replaces_description():
    builder = CharacterBuilder()
    assert builder.set_class("Fighter", 1) is True

    second_wind = _class_feature(builder, "Second Wind")
    assert second_wind is not None
    expected_summary = (
        builder._load_feature_overrides()
        .get("Fighter", {})
        .get("Second Wind", {})
        .get("pdf_summary")
    )
    assert second_wind["description"] == expected_summary


def test_feature_override_hidden_suppresses_class_feature(monkeypatch):
    builder = CharacterBuilder()
    monkeypatch.setattr(
        builder,
        "_load_feature_overrides",
        lambda: {"Fighter": {"Weapon Mastery": {"hidden": True}}},
    )
    assert builder.set_class("Fighter", 1) is True

    assert "Weapon Mastery" not in _class_feature_names(builder)
