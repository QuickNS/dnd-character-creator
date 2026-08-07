"""Regression tests: game-content selections must not escape data/ directories.

Player-supplied class / species / lineage / background / subclass identifiers
address JSON files on disk. They must resolve to a canonical content id inside
the expected content directory, and anything else must be rejected without
touching the filesystem.
"""

import pytest

from modules.character_builder import CharacterBuilder, content_slug


TRAVERSAL_IDENTIFIERS = [
    "../general_feats",              # real JSON one level up from a content dir
    "../../app",                     # outside data/ entirely
    "../../../../etc/passwd",
    "/etc/passwd",                   # absolute path
    "..%2f..%2fgeneral_feats",       # encoded traversal
    "..\\..\\general_feats",         # windows-style traversal
    "fighter/../../general_feats",
    "sub/dir/fighter",               # nested path
    "fighter\x00.json",              # NUL byte
    "",
    "   ",
]


class TestContentSlug:
    def test_canonical_names_slugify(self):
        assert content_slug("Fighter") == "fighter"
        assert content_slug("Wood Elf") == "wood_elf"
        assert content_slug(" Half-Elf ") == "half-elf"

    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS)
    def test_malformed_identifiers_rejected(self, identifier):
        assert content_slug(identifier) is None

    @pytest.mark.parametrize("identifier", [None, 3, ["fighter"], {"name": "fighter"}])
    def test_non_string_identifiers_rejected(self, identifier):
        assert content_slug(identifier) is None


class TestBuilderContentLoading:
    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS)
    def test_species_traversal_loads_nothing(self, identifier):
        builder = CharacterBuilder()
        assert builder._load_species_data(identifier) is None
        assert builder.set_species(identifier) is False
        assert builder.character_data["species"] is None

    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS)
    def test_class_traversal_loads_nothing(self, identifier):
        builder = CharacterBuilder()
        assert builder._load_class_data(identifier) is None
        assert builder.set_class(identifier) is False
        assert builder.character_data["class"] is None

    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS)
    def test_background_traversal_loads_nothing(self, identifier):
        builder = CharacterBuilder()
        assert builder._load_background_data(identifier) is None
        assert builder.set_background(identifier) is False
        assert builder.character_data["background"] is None

    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS)
    def test_lineage_traversal_loads_nothing(self, identifier):
        builder = CharacterBuilder()
        assert builder.set_species("Elf") is True
        assert builder._load_lineage_data("Elf", identifier) is None
        assert builder.set_lineage(identifier) is False
        assert builder.character_data["lineage"] is None

    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS)
    def test_subclass_traversal_loads_nothing(self, identifier):
        builder = CharacterBuilder()
        assert builder._load_subclass_data("Fighter", identifier) is None
        assert builder._load_subclass_data(identifier, "Champion") is None

    def test_spell_definition_traversal_returns_placeholder(self):
        builder = CharacterBuilder()
        definition = builder._load_spell_definition("../../general_feats")
        assert definition["description"] == "Spell definition not available."

    def test_canonical_content_still_loads(self):
        builder = CharacterBuilder()
        assert builder._load_species_data("Elf")["name"] == "Elf"
        assert builder._load_class_data("Fighter")["name"] == "Fighter"
        assert builder._load_background_data("Sage")["name"] == "Sage"
        assert builder._load_lineage_data("Elf", "Wood Elf")["name"] == "Wood Elf"
        assert builder._load_subclass_data("Fighter", "Champion") is not None


class TestContentSelectionExists:
    def test_known_identifiers(self):
        builder = CharacterBuilder()
        assert builder.content_selection_exists("species", "Elf")
        assert builder.content_selection_exists("class", "Fighter")
        assert builder.content_selection_exists("background", "Sage")
        assert builder.content_selection_exists("lineage", "Wood Elf")

    @pytest.mark.parametrize("identifier", TRAVERSAL_IDENTIFIERS + ["NotARealClass"])
    def test_unknown_or_malformed_identifiers(self, identifier):
        builder = CharacterBuilder()
        assert builder.content_selection_exists("class", identifier) is False

    def test_unknown_kind_raises(self):
        builder = CharacterBuilder()
        with pytest.raises(ValueError):
            builder.content_selection_exists("weapons", "Longsword")


class TestBuildApiRejectsTraversal:
    """The API must answer with a sanitized 400 — never a 500 or file content."""

    BASE_CHOICES = {
        "species": "Elf",
        "class": "Fighter",
        "background": "Sage",
        "level": 1,
    }

    def _post(self, client, overrides):
        choices = dict(self.BASE_CHOICES)
        choices.update(overrides)
        return client.post("/api/v1/character/build", json={"choices_made": choices})

    def test_valid_build_still_succeeds(self, client):
        r = self._post(client, {})
        assert r.status_code == 200
        assert r.get_json()["character"]["species"] == "Elf"

    @pytest.mark.parametrize("key", ["species", "class", "background"])
    @pytest.mark.parametrize("identifier", ["../general_feats", "/etc/passwd", "..%2f..%2fapp", "NotRealContent"])
    def test_traversal_and_unknown_identifiers_rejected(self, client, key, identifier):
        r = self._post(client, {key: identifier})
        assert r.status_code == 400
        error = r.get_json()["error"]
        assert "Unknown or invalid" in error
        # The response must not echo the submitted value back to the client.
        assert identifier not in error

    def test_lineage_traversal_rejected(self, client):
        r = self._post(client, {"lineage": "../../general_feats"})
        assert r.status_code == 400
        assert "lineage" in r.get_json()["error"]

    def test_subclass_traversal_rejected(self, client):
        r = self._post(client, {"level": 3, "subclass": "../../general_feats"})
        assert r.status_code == 400
        assert "subclass" in r.get_json()["error"]

    def test_traversal_in_classes_payload_rejected(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={
                "choices_made": {
                    "species": "Elf",
                    "background": "Sage",
                    "classes": [{"class_name": "../../general_feats", "level": 1}],
                }
            },
        )
        assert r.status_code == 400
        assert "class_name" in r.get_json()["error"]

    def test_validate_endpoint_rejects_traversal(self, client):
        r = client.post(
            "/api/v1/character/validate",
            json={"choices_made": {"species": "../../general_feats"}},
        )
        assert r.status_code == 400
        assert "Unknown or invalid" in r.get_json()["error"]

    def test_preview_step_endpoint_rejects_traversal(self, client):
        r = client.post(
            "/api/v1/character/preview-step",
            json={"choices_made": {"species": "../../general_feats"}, "step": "species"},
        )
        assert r.status_code == 400
        assert "Unknown or invalid" in r.get_json()["error"]

    def test_derived_endpoint_rejects_traversal(self, client):
        r = client.post(
            "/api/v1/character/derived",
            json={
                "choices_made": {"class": "../../general_feats"},
                "view": "spell_management",
            },
        )
        assert r.status_code == 400
        assert "Unknown or invalid" in r.get_json()["error"]
