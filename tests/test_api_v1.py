"""Tests for the v1 REST API used by the React SPA frontend."""

import pytest


# ==================== Health ====================


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": "v1"}


# ==================== Catalog: classes ====================


class TestCatalogClasses:
    def test_list_classes(self, client):
        r = client.get("/api/v1/catalog/classes")
        assert r.status_code == 200
        data = r.get_json()
        assert "classes" in data
        names = {c["name"] for c in data["classes"]}
        # Should include all 12 standard classes
        for expected in ("Fighter", "Wizard", "Cleric", "Rogue"):
            assert expected in names
        # Each summary has the required shape
        for c in data["classes"]:
            assert "id" in c and "name" in c

    def test_get_class(self, client):
        r = client.get("/api/v1/catalog/classes/Fighter")
        assert r.status_code == 200
        data = r.get_json()
        assert data["name"] == "Fighter"
        assert "hit_die" in data
        assert "features_by_level" in data

    def test_get_class_unknown_404(self, client):
        r = client.get("/api/v1/catalog/classes/NotARealClass")
        assert r.status_code == 404

    def test_list_subclasses(self, client):
        r = client.get("/api/v1/catalog/classes/Fighter/subclasses")
        assert r.status_code == 200
        data = r.get_json()
        assert data["class"] == "Fighter"
        assert isinstance(data["subclasses"], list)
        assert len(data["subclasses"]) > 0


# ==================== Catalog: species ====================


class TestCatalogSpecies:
    def test_list_species(self, client):
        r = client.get("/api/v1/catalog/species")
        assert r.status_code == 200
        species = r.get_json()["species"]
        names = {s["name"] for s in species}
        assert "Elf" in names and "Dwarf" in names and "Human" in names
        # Elf has lineages and trait choices (per data files)
        elf = next(s for s in species if s["name"] == "Elf")
        assert elf["has_lineages"] is True
        assert elf["has_trait_choices"] is True

    def test_get_species(self, client):
        r = client.get("/api/v1/catalog/species/Elf")
        assert r.status_code == 200
        data = r.get_json()
        assert data["name"] == "Elf"
        assert "traits" in data


# ==================== Catalog: backgrounds, feats, spells, equipment ====================


class TestCatalogMisc:
    def test_list_backgrounds(self, client):
        r = client.get("/api/v1/catalog/backgrounds")
        assert r.status_code == 200
        names = {b["name"] for b in r.get_json()["backgrounds"]}
        assert "Acolyte" in names

    def test_list_feats(self, client):
        r = client.get("/api/v1/catalog/feats")
        assert r.status_code == 200
        assert isinstance(r.get_json()["feats"], list)

    def test_class_spells_all(self, client):
        r = client.get("/api/v1/catalog/spells/wizard")
        assert r.status_code == 200
        data = r.get_json()
        assert data["class"] == "Wizard"
        assert "cantrips" in data and "spells_by_level" in data

    def test_class_spells_by_level(self, client):
        r = client.get("/api/v1/catalog/spells/wizard?level=0")
        assert r.status_code == 200
        data = r.get_json()
        assert data["level"] == 0
        assert "Fire Bolt" in data["spells"]

    def test_equipment_weapons(self, client):
        r = client.get("/api/v1/catalog/equipment/weapons")
        assert r.status_code == 200

    def test_equipment_unknown_404(self, client):
        r = client.get("/api/v1/catalog/equipment/spaceships")
        assert r.status_code == 404


# ==================== Wizard metadata ====================


class TestWizard:
    def test_steps(self, client):
        r = client.get("/api/v1/wizard/steps")
        assert r.status_code == 200
        steps = r.get_json()["steps"]
        ids = [s["id"] for s in steps]
        assert ids[0] == "basics"
        assert "class" in ids and "species" in ids and "complete" in ids

    def test_dependencies(self, client):
        r = client.get("/api/v1/wizard/dependencies")
        assert r.status_code == 200
        deps = r.get_json()["dependencies"]
        # Class change must invalidate subclass + spells
        assert "subclass" in deps["class"]
        assert "spells" in deps["class"]
        # Species change must invalidate lineage
        assert "lineage" in deps["species"]


# ==================== Character build/validate/preview ====================


class TestCharacterBuild:
    def test_build_dwarf_cleric(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": dwarf_cleric_choices},
        )
        assert r.status_code == 200
        char = r.get_json()["character"]
        assert char["name"] == "Thorin"
        assert char["class"] == "Cleric"

    def test_build_response_structure_wrapped(self, client, dwarf_cleric_choices):
        """
        REGRESSION TEST: Validate that /character/build returns { "character": {...} }
        
        The Flask endpoint must return a wrapped response structure. The frontend
        API client (frontend/src/lib/api.ts) unwraps this to return the character
        object directly to React components.
        
        This test prevents regression of the double-unwrapping bug where components
        were attempting to access response.character.character instead of response.character.
        
        Contract:
        - Flask returns: { "character": {...} }
        - API client unwraps and returns: {...}
        - Components receive: {...}
        """
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": dwarf_cleric_choices},
        )
        assert r.status_code == 200
        
        # Response must be wrapped in { "character": {...} }
        data = r.get_json()
        assert isinstance(data, dict), "Response must be a dict"
        assert "character" in data, "Response must have 'character' key"
        
        # The character value must be a dict, not double-wrapped
        character = data["character"]
        assert isinstance(character, dict), "character must be a dict, not further nested"
        
        # Validate expected top-level keys exist in the character object
        # (proves it's the actual character, not another wrapper)
        expected_keys = [
            "name", "level", "class", "species", "background",
            "proficiencies", "combat", "features", "spellcasting_stats"
        ]
        for key in expected_keys:
            assert key in character, f"character must have '{key}' key"
        
        # Sanity check: verify it's the actual character data
        assert character["name"] == "Thorin"
        assert character["level"] == 7
        assert character["class"] == "Cleric"

    def test_build_missing_body(self, client):
        r = client.post("/api/v1/character/build", json={})
        assert r.status_code == 400

    def test_validate_complete(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/validate",
            json={"choices_made": dwarf_cleric_choices},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert "steps" in data
        # Each step has the expected shape
        for step in data["steps"]:
            assert "step" in step and "complete" in step and "missing" in step

    def test_validate_missing_class_fails(self, client):
        # Just basics — class is missing, should not be complete
        r = client.post(
            "/api/v1/character/validate",
            json={"choices_made": {"character_name": "X", "level": 1}},
        )
        assert r.status_code == 200
        data = r.get_json()
        class_step = next(s for s in data["steps"] if s["step"] == "class")
        assert class_step["complete"] is False
        assert "class" in class_step["missing"]

    def test_preview_class_step(self, client):
        # Fighter at level 3 needs subclass
        r = client.post(
            "/api/v1/character/preview-step",
            json={
                "step": "class",
                "choices_made": {
                    "character_name": "Test",
                    "level": 3,
                    "class": "Fighter",
                },
            },
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["step"] == "class"
        assert data["needs_subclass"] is True
        assert isinstance(data["available_subclasses"], list)
        assert len(data["available_subclasses"]) > 0
        first = data["available_subclasses"][0]
        assert isinstance(first["id"], str)
        assert isinstance(first["name"], str)
        assert isinstance(first["level_3_feature_names"], list)
        champion = next((s for s in data["available_subclasses"] if s["name"] == "Champion"), None)
        assert champion is not None
        assert "Improved Critical" in champion["level_3_feature_names"]

    def test_preview_class_no_subclass_at_low_level(self, client):
        r = client.post(
            "/api/v1/character/preview-step",
            json={
                "step": "class",
                "choices_made": {
                    "character_name": "Test",
                    "level": 1,
                    "class": "Fighter",
                },
            },
        )
        assert r.status_code == 200
        assert r.get_json()["needs_subclass"] is False

    def test_preview_species_step(self, client):
        r = client.post(
            "/api/v1/character/preview-step",
            json={
                "step": "species",
                "choices_made": {
                    "character_name": "Test",
                    "level": 1,
                    "species": "Elf",
                },
            },
        )
        assert r.status_code == 200
        data = r.get_json()
        assert "traits" in data
        assert "trait_choices" in data


# ==================== Character derived views (Phase 2) ====================


class TestCharacterDerived:
    def test_derived_missing_body(self, client):
        r = client.post("/api/v1/character/derived", json={})
        assert r.status_code == 400

    def test_derived_unknown_view(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": dwarf_cleric_choices, "view": "nope"},
        )
        assert r.status_code == 400
        body = r.get_json()
        assert "allowed" in body

    def test_derived_damage_cantrips_cleric(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": dwarf_cleric_choices, "view": "damage_cantrips"},
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body["view"] == "damage_cantrips"
        assert isinstance(body["data"], list)
        # Each row (if any) has the documented shape
        for row in body["data"]:
            assert {"name", "atk_display", "damage", "damage_type", "notes"} <= set(row)

    def test_derived_spell_management_cleric(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": dwarf_cleric_choices, "view": "spell_management"},
        )
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert "available_cantrips" in data
        assert "available_spells" in data
        assert "spell_slots" in data
        assert "limits" in data

    def test_derived_spell_management_non_caster_400(self, client, elf_fighter_choices):
        # Champion Fighter is not a spellcaster
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": elf_fighter_choices, "view": "spell_management"},
        )
        assert r.status_code == 400

    def test_derived_mastery_management_fighter(self, client, elf_fighter_choices):
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": elf_fighter_choices, "view": "mastery_management"},
        )
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert "available_weapons" in data
        assert "max_masteries" in data
        assert "weapon_masteries" in data

    def test_derived_invocation_management_non_warlock_400(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": dwarf_cleric_choices, "view": "invocation_management"},
        )
        assert r.status_code == 400
