"""Regression coverage for bounded character request validation."""

import pytest

from modules.character_builder import CharacterBuilder


def _choices(**overrides):
    choices = {
        "class": "Fighter",
        "level": 1,
        "species": "Human",
        "background": "Soldier",
        "ability_scores": {
            "Strength": 15,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 12,
            "Wisdom": 10,
            "Charisma": 8,
        },
    }
    choices.update(overrides)
    return choices


@pytest.mark.parametrize(
    ("endpoint", "extra"),
    [
        ("/api/v1/character/build", {}),
        ("/api/v1/character/validate", {}),
        ("/api/v1/character/preview-step", {"step": "class"}),
        ("/api/v1/character/random-languages", {}),
        ("/api/v1/character/derived", {"view": "spell_management"}),
    ],
)
def test_api_character_endpoints_reject_invalid_level_consistently(client, endpoint, extra):
    response = client.post(endpoint, json={
        "choices_made": _choices(level=21),
        **extra,
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == {
        "code": "out_of_bounds",
        "field": "choices_made.level",
        "message": "Must be between 1 and 20",
    }


@pytest.mark.parametrize("level", ["1", 1.0, True, 0])
def test_api_build_rejects_non_integer_or_out_of_range_level(client, level):
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(level=level)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["field"] == "choices_made.level"


def test_api_build_rejects_total_multiclass_level_above_twenty(client):
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(classes=[
            {"class_name": "Fighter", "level": 20},
            {"class_name": "Wizard", "level": 1},
        ])},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["field"] == "choices_made.classes"


def test_api_build_rejects_invalid_ability_score_shape_and_type(client):
    scores = _choices()["ability_scores"]
    scores["Strength"] = True
    scores["Luck"] = 10
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(ability_scores=scores)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["field"] == "choices_made.ability_scores"


def test_api_build_rejects_invalid_ability_bonus_map(client):
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(background_bonuses={"Strength": True})},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["field"] == "choices_made.background_bonuses"


def test_api_build_rejects_unknown_choice(client):
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(unexpected_choice="nope")},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "unknown_field"


def test_api_build_rejects_oversized_collection(client):
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(languages=["Common"] * 101)},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["field"] == "choices_made.languages"


def test_api_build_canonicalizes_identifiers(client):
    response = client.post(
        "/api/v1/character/build",
        json={"choices_made": _choices(
            **{"class": "fighter", "species": "human", "background": "soldier"}
        )},
    )

    assert response.status_code == 200
    character = response.get_json()["character"]
    assert character["class"] == "Fighter"
    assert character["species"] == "Human"
    assert character["background"] == "Soldier"


def test_apply_choices_propagates_failed_setter():
    builder = CharacterBuilder()

    assert builder.apply_choices({"species": "Not A Species"}) is False


def test_apply_choices_propagates_nested_choice_failure(monkeypatch):
    builder = CharacterBuilder()
    apply_choice = builder.apply_choice

    def fail_nested_choice(key, value):
        if key == "Trait":
            return False
        return apply_choice(key, value)

    monkeypatch.setattr(builder, "apply_choice", fail_nested_choice)

    assert builder.apply_choices({"species_trait_choices": {"Trait": "value"}}) is False
