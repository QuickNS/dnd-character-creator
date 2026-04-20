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
        "/api/rebuild-character",
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
        "/api/rebuild-character",
        json={"choices_made": choices},
        content_type="application/json",
    )
    assert resp.status_code == 200
    return client


class TestEditRoute:
    """Test the /edit/<section> route."""

    def test_edit_class_redirects(self, completed_character):
        resp = completed_character.get("/edit/class")
        assert resp.status_code == 302
        assert "/choose-class" in resp.headers["Location"]

    def test_edit_background_redirects(self, completed_character):
        resp = completed_character.get("/edit/background")
        assert resp.status_code == 302
        assert "/choose-background" in resp.headers["Location"]

    def test_edit_species_redirects(self, completed_character):
        resp = completed_character.get("/edit/species")
        assert resp.status_code == 302
        assert "/choose-species" in resp.headers["Location"]

    def test_edit_languages_redirects(self, completed_character):
        resp = completed_character.get("/edit/languages")
        assert resp.status_code == 302
        assert "/choose-languages" in resp.headers["Location"]

    def test_edit_abilities_redirects(self, completed_character):
        resp = completed_character.get("/edit/abilities")
        assert resp.status_code == 302
        assert "/assign-ability-scores" in resp.headers["Location"]

    def test_edit_equipment_redirects(self, completed_character):
        resp = completed_character.get("/edit/equipment")
        assert resp.status_code == 302
        assert "/choose-equipment" in resp.headers["Location"]

    def test_edit_invalid_section_redirects_to_summary(self, completed_character):
        resp = completed_character.get("/edit/invalid")
        assert resp.status_code == 302
        assert "/character-summary" in resp.headers["Location"]

    def test_edit_without_session_redirects_to_index(self, client):
        resp = client.get("/edit/class")
        assert resp.status_code == 302
        assert resp.headers["Location"] in ("/", "http://localhost/")


class TestEditFlowReturnsToSummary:
    """Test that completing an edit section returns to the summary page."""

    def test_edit_languages_returns_to_summary(self, completed_character):
        # Enter edit mode for languages
        completed_character.get("/edit/languages")

        # Submit new language selection
        resp = completed_character.post(
            "/select-languages",
            data={"languages": ["Common", "Dwarvish"]},
        )
        assert resp.status_code == 302
        assert "/character-summary" in resp.headers["Location"]

    def test_edit_abilities_returns_to_summary(self, completed_character):
        # Enter edit mode for abilities
        completed_character.get("/edit/abilities")

        # Submit ability scores
        resp = completed_character.post(
            "/submit-ability-scores",
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
        assert "/character-summary" in resp.headers["Location"]


class TestCancelEdit:
    """Test that canceling an edit returns to summary."""

    def test_cancel_edit_returns_to_summary(self, completed_character):
        # Enter edit mode
        completed_character.get("/edit/class")

        # Go directly to summary (cancel)
        resp = completed_character.get("/character-summary")
        assert resp.status_code == 200


class TestSummaryEditButtons:
    """Test that the summary page contains edit buttons."""

    def test_summary_has_edit_links(self, completed_character):
        resp = completed_character.get("/character-summary")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "/edit/class" in html
        assert "/edit/background" in html
        assert "/edit/species" in html
        assert "/edit/languages" in html
        assert "/edit/abilities" in html
        assert "/edit/equipment" in html


class TestLevelChange:
    """Test that changing level properly rebuilds class features."""

    def test_downlevel_removes_higher_level_features(self, completed_wizard):
        """Regression: level 7→3 Wizard should not retain level 7 features."""
        # Verify the wizard starts at level 7 with level-7 features
        resp = completed_wizard.get("/api/character-sheet")
        data = resp.get_json()
        feature_names = {f["name"] for f in data["features"]["class"]}
        assert "Memorize Spell" in feature_names  # level 5 feature

        # Enter edit mode for class
        completed_wizard.get("/edit/class")

        # Submit same class (Wizard) but with level 3
        resp = completed_wizard.post(
            "/select-class",
            data={"class": "Wizard", "level": "3"},
        )
        assert resp.status_code == 302

        # Submit class choices to complete the edit (skip through)
        resp = completed_wizard.post("/submit-class-choices", data={})
        assert resp.status_code == 302

        # Check the character sheet — should only have level 3 features
        resp = completed_wizard.get("/api/character-sheet")
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
        completed_wizard.get("/edit/class")

        # Submit same class (Wizard) but with level 10
        resp = completed_wizard.post(
            "/select-class",
            data={"class": "Wizard", "level": "10"},
        )
        assert resp.status_code == 302

        # Check level updated
        resp = completed_wizard.get("/api/character-sheet")
        data = resp.get_json()
        assert data["level"] == 10
