"""
Route integration tests for species feat choices flow.
Regression tests for GitHub Issue: [Human] Versatile feat choices not presented
when selecting origin feat via species trait.
"""

import json
import pytest
from app import app
from modules.character_builder import CharacterBuilder


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BASE_CHOICES = {
    "character_name": "Varis",
    "level": 1,
    "class": "Fighter",
    "background": "Criminal",
    "species": "Human",
    "ability_scores": {
        "Strength": 15, "Dexterity": 13, "Constitution": 14,
        "Intelligence": 10, "Wisdom": 12, "Charisma": 8,
    },
    "background_bonuses": {"Strength": 2, "Constitution": 1},
}


def _make_human_builder(**extra_choices) -> CharacterBuilder:
    """Return a CharacterBuilder with Human fully set up."""
    builder = CharacterBuilder()
    choices = {**_BASE_CHOICES, **extra_choices}
    builder.apply_choices(choices)
    return builder


def _seed_session(client, builder: CharacterBuilder):
    """Store a builder in the test session."""
    with client.session_transaction() as sess:
        sess["builder_state"] = builder.to_json()


@pytest.fixture
def skilled_builder():
    """Builder representing a Human who chose Skilled via Versatile."""
    builder = _make_human_builder()
    builder.apply_choice("Versatile", "Skilled")
    builder.set_step("species_feat_choices")
    return builder


class TestSpeciesFeatChoicesRoute:
    """Tests for GET /species-feat-choices and POST /submit-species-feat-choices."""

    def test_get_species_feat_choices_renders_200(self, client, skilled_builder):
        """GET /species-feat-choices should return 200 when feat has choices."""
        _seed_session(client, skilled_builder)

        response = client.get("/species-feat-choices")
        assert response.status_code == 200
        assert b"Skilled" in response.data

    def test_get_species_feat_choices_shows_skill_options(self, client, skilled_builder):
        """The feat choices page should list skill/tool options from Skilled."""
        _seed_session(client, skilled_builder)

        response = client.get("/species-feat-choices")
        assert response.status_code == 200
        assert b"Arcana" in response.data

    def test_get_species_feat_choices_shows_species_source_label(self, client, skilled_builder):
        """The page should say the species grants the feat, not the background."""
        _seed_session(client, skilled_builder)

        response = client.get("/species-feat-choices")
        assert response.status_code == 200
        assert b"species" in response.data.lower()

    def test_submit_species_feat_choices_grants_skills(self, client, skilled_builder):
        """POST /submit-species-feat-choices should apply selected skills."""
        _seed_session(client, skilled_builder)

        response = client.post(
            "/submit-species-feat-choices",
            data={
                "feat_choice_skills_or_tools": ["Arcana", "History", "Deception"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

        # Verify skills were applied to builder in session
        with client.session_transaction() as sess:
            state = sess.get("builder_state", {})
        profs = state.get("proficiencies", {}).get("skills", [])
        assert "Arcana" in profs
        assert "History" in profs
        assert "Deception" in profs

    def test_submit_species_feat_choices_clears_pending_feat(self, client, skilled_builder):
        """After submission, pending_species_feat should be cleared."""
        _seed_session(client, skilled_builder)

        client.post(
            "/submit-species-feat-choices",
            data={
                "feat_choice_skills_or_tools": ["Arcana", "History", "Deception"],
            },
        )

        with client.session_transaction() as sess:
            state = sess.get("builder_state", {})
        assert "pending_species_feat" not in state

    def test_submit_species_feat_choices_redirects_to_languages(self, client, skilled_builder):
        """For a species without lineages, should redirect to choose_languages."""
        _seed_session(client, skilled_builder)

        response = client.post(
            "/submit-species-feat-choices",
            data={
                "feat_choice_skills_or_tools": ["Arcana", "History", "Deception"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "language" in response.headers["Location"].lower()

    def test_species_feat_choices_skips_when_no_choices(self, client):
        """GET /species-feat-choices redirects away when feat has no choices."""
        builder = _make_human_builder()
        # Alert has no choices
        builder.apply_choice("Versatile", "Alert")
        builder.set_step("species_feat_choices")
        _seed_session(client, builder)

        response = client.get("/species-feat-choices", follow_redirects=False)
        # Should redirect (no choices to present)
        assert response.status_code == 302


class TestSelectSpeciesTraitsRedirect:
    """Test that select_species_traits redirects to feat choices when needed."""

    def test_select_species_traits_redirects_to_feat_choices_for_skilled(self, client):
        """Selecting Skilled via Versatile should redirect to species_feat_choices."""
        builder = _make_human_builder()
        builder.set_step("species_traits")
        _seed_session(client, builder)

        response = client.post(
            "/select-species-traits",
            data={
                "trait_skillful": "Arcana",
                "trait_versatile": "Skilled",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "species-feat-choices" in response.headers["Location"]

    def test_select_species_traits_no_redirect_for_alert(self, client):
        """Selecting Alert (no choices) should proceed to languages, not feat choices."""
        builder = _make_human_builder()
        builder.set_step("species_traits")
        _seed_session(client, builder)

        response = client.post(
            "/select-species-traits",
            data={
                "trait_skillful": "Arcana",
                "trait_versatile": "Alert",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        location = response.headers["Location"]
        assert "species-feat-choices" not in location
        assert "language" in location.lower()
