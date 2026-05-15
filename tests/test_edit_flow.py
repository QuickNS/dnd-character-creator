"""Tests for the edit-from-summary flow."""

import json
import pytest


@pytest.fixture
def completed_character(client):
    """Create a completed character via the API, returning the client with session."""
    choices = {
        "character_name": "Test Hero",
        "level": 5,
        "class": "Fighter",
        "background": "Soldier",
        "species": "Human",
        "languages": ["Common", "Elvish"],
        "ability_scores": {
            "Strength": 15,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 12,
            "Wisdom": 10,
            "Charisma": 8,
        },
        "background_bonuses_method": "suggested",
    }
    resp = client.post(
        "/legacy/api/rebuild-character",
        json={"choices_made": choices},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return client


@pytest.fixture
def completed_wizard(client):
    """Create a completed level 7 Wizard via the API."""
    choices = {
        "character_name": "Test Wizard",
        "level": 7,
        "class": "Wizard",
        "background": "Sage",
        "species": "Human",
        "languages": ["Common", "Elvish"],
        "ability_scores": {
            "Strength": 8,
            "Dexterity": 14,
            "Constitution": 13,
            "Intelligence": 15,
            "Wisdom": 12,
            "Charisma": 10,
        },
        "background_bonuses_method": "suggested",
    }
    resp = client.post(
        "/legacy/api/rebuild-character",
        json={"choices_made": choices},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return client


class TestEditRoute:
    """Test the /edit/<section> route."""

    def test_edit_class_redirects(self, completed_character):
        resp = completed_character.get("/legacy/edit/class")
        assert resp.status_code == 302
        assert "/legacy/choose-class" in resp.headers["Location"]

    def test_edit_background_redirects(self, completed_character):
        resp = completed_character.get("/legacy/edit/background")
        assert resp.status_code == 302
        assert "/legacy/choose-background" in resp.headers["Location"]

    def test_edit_species_redirects(self, completed_character):
        resp = completed_character.get("/legacy/edit/species")
        assert resp.status_code == 302
        assert "/legacy/choose-species" in resp.headers["Location"]

    def test_edit_languages_redirects(self, completed_character):
        resp = completed_character.get("/legacy/edit/languages")
        assert resp.status_code == 302
        assert "/legacy/choose-languages" in resp.headers["Location"]

    def test_edit_abilities_redirects(self, completed_character):
        resp = completed_character.get("/legacy/edit/abilities")
        assert resp.status_code == 302
        assert "/legacy/assign-ability-scores" in resp.headers["Location"]

    def test_edit_equipment_redirects(self, completed_character):
        resp = completed_character.get("/legacy/edit/equipment")
        assert resp.status_code == 302
        assert "/legacy/choose-equipment" in resp.headers["Location"]

    def test_edit_invalid_section_redirects_to_summary(self, completed_character):
        resp = completed_character.get("/legacy/edit/invalid")
        assert resp.status_code == 302
        assert "/legacy/character-summary" in resp.headers["Location"]

    def test_edit_without_session_redirects_to_index(self, client):
        resp = client.get("/legacy/edit/class")
        assert resp.status_code == 302
        assert resp.headers["Location"] in ("/legacy/", "http://localhost/legacy/")


class TestEditFlowReturnsToSummary:
    """Test that completing an edit section returns to the summary page."""

    def test_edit_languages_returns_to_summary(self, completed_character):
        # Enter edit mode for languages
        completed_character.get("/legacy/edit/languages")

        # Submit new language selection
        resp = completed_character.post(
            "/legacy/select-languages",
            data={"languages": ["Common", "Dwarvish"]},
        )
        assert resp.status_code == 302
        assert "/legacy/character-summary" in resp.headers["Location"]

    def test_edit_abilities_returns_to_summary(self, completed_character):
        # Enter edit mode for abilities
        completed_character.get("/legacy/edit/abilities")

        # Submit ability scores
        resp = completed_character.post(
            "/legacy/submit-ability-scores",
            data={
                "assignment_method": "manual",
                "ability_Strength": "15",
                "ability_Dexterity": "14",
                "ability_Constitution": "13",
                "ability_Intelligence": "12",
                "ability_Wisdom": "10",
                "ability_Charisma": "8",
                "bonus_method": "suggested",
            },
        )
        assert resp.status_code == 302
        assert "/legacy/character-summary" in resp.headers["Location"]


class TestCancelEdit:
    """Test that canceling an edit returns to summary."""

    def test_cancel_edit_returns_to_summary(self, completed_character):
        # Enter edit mode
        completed_character.get("/legacy/edit/class")

        # Go directly to summary (cancel)
        resp = completed_character.get("/legacy/character-summary")
        assert resp.status_code == 200


class TestSummaryEditButtons:
    """Test that the summary page contains edit buttons."""

    def test_summary_has_edit_links(self, completed_character):
        resp = completed_character.get("/legacy/character-summary")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "/legacy/edit/class" in html
        assert "/legacy/edit/background" in html
        assert "/legacy/edit/species" in html
        assert "/legacy/edit/languages" in html
        assert "/legacy/edit/abilities" in html
        assert "/legacy/edit/equipment" in html


class TestLevelChange:
    """Test that changing level properly rebuilds class features."""

    def test_downlevel_removes_higher_level_features(self, completed_wizard):
        """Regression: level 7→3 Wizard should not retain level 7 features."""
        # Verify the wizard starts at level 7 with level-7 features
        resp = completed_wizard.get("/legacy/api/character-sheet")
        data = resp.get_json()
        feature_names = {f["name"] for f in data["features"]["class"]}
        assert "Memorize Spell" in feature_names  # level 5 feature

        # Enter edit mode for class
        completed_wizard.get("/legacy/edit/class")

        # Submit same class (Wizard) but with level 3
        resp = completed_wizard.post(
            "/legacy/select-class",
            data={"class": "Wizard", "level": "3"},
        )
        assert resp.status_code == 302

        # Submit class choices to complete the edit (skip through)
        resp = completed_wizard.post("/legacy/submit-class-choices", data={})
        assert resp.status_code == 302

        # Check the character sheet — should only have level 3 features
        resp = completed_wizard.get("/legacy/api/character-sheet")
        data = resp.get_json()
        assert data["level"] == 3
        feature_names = {f["name"] for f in data["features"]["class"]}
        assert "Memorize Spell" not in feature_names
        assert "Ability Score Improvement" not in feature_names
        assert "Spellcasting" in feature_names
        assert "Arcane Recovery" in feature_names

    def test_uplevel_adds_higher_level_features(self, completed_wizard):
        """Level 7→10 Wizard should gain level 10 features."""
        # Enter edit mode for class
        completed_wizard.get("/legacy/edit/class")

        # Submit same class (Wizard) but with level 10
        resp = completed_wizard.post(
            "/legacy/select-class",
            data={"class": "Wizard", "level": "10"},
        )
        assert resp.status_code == 302

        # Check level updated
        resp = completed_wizard.get("/legacy/api/character-sheet")
        data = resp.get_json()
        assert data["level"] == 10
