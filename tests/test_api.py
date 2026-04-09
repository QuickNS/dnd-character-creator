"""Tests for the API endpoints including test-only endpoints."""

import pytest
import json
from modules.character_builder import CharacterBuilder


class TestChoicesToCharacterAPI:
    """Tests for the existing /api/choices-to-character endpoint."""

    def test_valid_character_build(self, client, dwarf_cleric_choices):
        response = client.post(
            "/api/choices-to-character",
            json={"choices_made": dwarf_cleric_choices},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "character_data" in data

    def test_missing_choices_made(self, client):
        response = client.post(
            "/api/choices-to-character",
            json={"invalid": "data"},
            content_type="application/json"
        )
        assert response.status_code == 400

    def test_wrong_content_type(self, client):
        response = client.post(
            "/api/choices-to-character",
            data="not json"
        )
        assert response.status_code == 400


class TestBuildCharacterAPI:
    """Tests for /api/test/build-character."""

    def test_valid_build(self, client, dwarf_cleric_choices):
        response = client.post(
            "/api/test/build-character",
            json={"choices_made": dwarf_cleric_choices},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "character" in data
        character = data["character"]
        assert character.get("name") == "Thorin"

    def test_elf_fighter_build(self, client, elf_fighter_choices):
        response = client.post(
            "/api/test/build-character",
            json={"choices_made": elf_fighter_choices},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_missing_choices(self, client):
        response = client.post(
            "/api/test/build-character",
            json={},
            content_type="application/json"
        )
        assert response.status_code == 400


class TestValidateEffectsAPI:
    """Tests for /api/test/validate-effects."""

    def test_dwarf_effects(self, client):
        response = client.post(
            "/api/test/validate-effects",
            json={"species": "Dwarf", "class": "Cleric", "level": 3},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        effects = data["effects"]
        # Dwarf should have poison resistance
        resistance_types = [e.get("damage_type") for e in effects if e.get("type") == "grant_damage_resistance"]
        assert "Poison" in resistance_types

    def test_minimal_request(self, client):
        response = client.post(
            "/api/test/validate-effects",
            json={"species": "Human", "class": "Fighter"},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True


class TestSchemaValidateAPI:
    """Tests for /api/test/schema-validate."""

    def test_valid_class_data(self, client):
        valid_class = {
            "name": "TestClass",
            "description": "A test class",
            "hit_die": 8,
            "primary_ability": "Strength",
            "saving_throw_proficiencies": ["Strength", "Constitution"],
            "subclass_selection_level": 3,
            "proficiency_bonus_by_level": {str(i): (2 + (i - 1) // 4) for i in range(1, 21)},
            "features_by_level": {
                "1": {"Test Feature": "A test feature description."}
            }
        }
        response = client.post(
            "/api/test/schema-validate",
            json={"schema_type": "class", "data": valid_class},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is True

    def test_invalid_class_missing_fields(self, client):
        invalid_class = {"name": "Bad", "hit_die": 8}
        response = client.post(
            "/api/test/schema-validate",
            json={"schema_type": "class", "data": invalid_class},
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    def test_unknown_schema_type(self, client):
        response = client.post(
            "/api/test/schema-validate",
            json={"schema_type": "unknown", "data": {}},
            content_type="application/json"
        )
        assert response.status_code == 400


class TestDirectBuilder:
    """Tests using CharacterBuilder directly (no HTTP)."""

    def test_dwarf_cleric_build(self, built_character, dwarf_cleric_choices):
        character = built_character(dwarf_cleric_choices)
        assert character.get("name") == "Thorin"
        assert character.get("class") == "Cleric"
        assert character.get("species") == "Dwarf"

    def test_elf_fighter_build(self, built_character, elf_fighter_choices):
        character = built_character(elf_fighter_choices)
        assert character.get("name") == "Elenian"
        assert character.get("class") == "Fighter"
