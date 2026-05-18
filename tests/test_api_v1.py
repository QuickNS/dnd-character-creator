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
        assert ids[0] == "class"
        assert "basics" not in ids
        assert "class" in ids and "species" in ids and "complete" in ids

    def test_dependencies(self, client):
        r = client.get("/api/v1/wizard/dependencies")
        assert r.status_code == 200
        deps = r.get_json()["dependencies"]
        # Class change must invalidate subclass + spells
        assert "subclass" in deps["class"]
        assert "spells" in deps["class"]
        # Classes payload change must invalidate class-dependent choices
        assert "classes" in deps
        assert "subclass" in deps["classes"]
        assert "spells" in deps["classes"]
        # Species change must invalidate lineage
        assert "lineage" in deps["species"]

    def test_steps_class_no_longer_requires_level(self, client):
        r = client.get("/api/v1/wizard/steps")
        assert r.status_code == 200
        steps = r.get_json()["steps"]
        class_step = next(s for s in steps if s["id"] == "class")
        assert "character_name" in class_step["required_keys"]
        assert "level" not in class_step["required_keys"]


# ==================== Character build/validate/preview ====================


class TestCharacterBuild:
    @staticmethod
    def _rogue_fighter_multiclass_choices():
        return {
            "character_name": "Dual Track",
            "species": "Human",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 16,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 14,
                "Charisma": 8,
            },
            "background_bonuses": {"Dexterity": 2, "Wisdom": 1},
            "classes": [
                {"class_name": "Rogue", "level": 3, "subclass": "Thief"},
                {"class_name": "Fighter", "level": 2},
            ],
            "Fighting Style": "Dueling",
        }

    @staticmethod
    def _cleric_fighter_multiclass_choices():
        return {
            "character_name": "Spellblade",
            "species": "Human",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 12,
                "Dexterity": 10,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 16,
                "Charisma": 8,
            },
            "background_bonuses": {"Wisdom": 2, "Constitution": 1},
            "classes": [
                {"class_name": "Cleric", "level": 4, "subclass": "Light Domain"},
                {"class_name": "Fighter", "level": 1},
            ],
        }

    @staticmethod
    def _cleric_wizard_multiclass_choices():
        return {
            "character_name": "Twin Study",
            "species": "Human",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 10,
                "Constitution": 14,
                "Intelligence": 16,
                "Wisdom": 16,
                "Charisma": 8,
            },
            "background_bonuses": {"Wisdom": 2, "Intelligence": 1},
            "classes": [
                {"class_name": "Cleric", "level": 3, "subclass": "Light Domain"},
                {"class_name": "Wizard", "level": 2},
            ],
        }

    @staticmethod
    def _cleric_ranger_multiclass_choices():
        return {
            "character_name": "Wild Aegis",
            "species": "Human",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 14,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 16,
                "Charisma": 8,
            },
            "background_bonuses": {"Wisdom": 2, "Dexterity": 1},
            "classes": [
                {"class_name": "Cleric", "level": 4, "subclass": "Light Domain"},
                {"class_name": "Ranger", "level": 2},
            ],
        }

    @staticmethod
    def _cleric_eldritch_knight_multiclass_choices():
        return {
            "character_name": "Tempered Arcana",
            "species": "Human",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 14,
                "Dexterity": 10,
                "Constitution": 14,
                "Intelligence": 14,
                "Wisdom": 16,
                "Charisma": 8,
            },
            "background_bonuses": {"Wisdom": 2, "Constitution": 1},
            "classes": [
                {"class_name": "Cleric", "level": 4, "subclass": "Light Domain"},
                {"class_name": "Fighter", "level": 3, "subclass": "Eldritch Knight"},
            ],
        }

    @staticmethod
    def _cleric_warlock_multiclass_choices():
        return {
            "character_name": "Veilbound",
            "species": "Human",
            "background": "Acolyte",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 10,
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 16,
                "Charisma": 14,
            },
            "background_bonuses": {"Wisdom": 2, "Constitution": 1},
            "classes": [
                {"class_name": "Cleric", "level": 4, "subclass": "Light Domain"},
                {"class_name": "Warlock", "level": 2},
            ],
        }

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

    def test_build_legacy_class_level_payload_still_supported(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": dwarf_cleric_choices},
        )
        assert r.status_code == 200
        char = r.get_json()["character"]
        assert char["class"] == "Cleric"
        assert char["level"] == 7

    def test_build_single_entry_classes_payload_matches_legacy(self, client, dwarf_cleric_choices):
        legacy_payload = dict(dwarf_cleric_choices)

        new_shape_payload = {
            k: v
            for k, v in dwarf_cleric_choices.items()
            if k not in ("class", "level", "subclass")
        }
        new_shape_payload["classes"] = [{
            "class_name": dwarf_cleric_choices["class"],
            "level": dwarf_cleric_choices["level"],
            "subclass": dwarf_cleric_choices["subclass"],
        }]

        legacy_response = client.post(
            "/api/v1/character/build",
            json={"choices_made": legacy_payload},
        )
        new_shape_response = client.post(
            "/api/v1/character/build",
            json={"choices_made": new_shape_payload},
        )

        assert legacy_response.status_code == 200
        assert new_shape_response.status_code == 200

        legacy_character = legacy_response.get_json()["character"]
        new_shape_character = new_shape_response.get_json()["character"]

        assert new_shape_character["class"] == legacy_character["class"]
        assert new_shape_character["level"] == legacy_character["level"]
        assert new_shape_character["subclass"] == legacy_character["subclass"]
        assert (
            new_shape_character["combat"]["hit_points"]["maximum"]
            == legacy_character["combat"]["hit_points"]["maximum"]
        )
        assert (
            new_shape_character["proficiency_bonus"]
            == legacy_character["proficiency_bonus"]
        )

    def test_build_multiclass_rogue3_fighter2_returns_200(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._rogue_fighter_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        assert char["class"] == "Rogue"
        assert char["level"] == 5
        assert char["proficiency_bonus"] == 3

    def test_build_multiclass_features_include_both_class_tracks(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._rogue_fighter_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        class_feature_names = [f["name"] for f in char["features"]["class"]]

        assert any(name.startswith("Sneak Attack") for name in class_feature_names)
        assert any(name.startswith("Action Surge") for name in class_feature_names)

    def test_multiclass_spellcasting_stats_use_total_level_proficiency_bonus(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._cleric_fighter_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        spell_stats = char["spellcasting_stats"]

        # Cleric 4 / Fighter 1 is total level 5 (PB +3), while primary class level 4 would be +2.
        assert char["level"] == 5
        assert char["proficiency_bonus"] == 3
        assert spell_stats["has_spellcasting"] is True
        assert spell_stats["spell_attack_bonus"] == (
            char["proficiency_bonus"] + spell_stats["spellcasting_modifier"]
        )
        assert spell_stats["spell_save_dc"] == (
            8 + char["proficiency_bonus"] + spell_stats["spellcasting_modifier"]
        )

    def test_multiclass_full_plus_full_uses_effective_caster_level_for_slots(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._cleric_wizard_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        stats = char["spellcasting_stats"]

        # Cleric 3 + Wizard 2 => effective caster level 5.
        assert char["spell_slots"].get("1st") == 4
        assert char["spell_slots"].get("2nd") == 3
        assert char["spell_slots"].get("3rd") == 2
        assert stats.get("effective_caster_level") == 5

    def test_multiclass_full_plus_half_uses_floor_rule(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._cleric_ranger_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        stats = char["spellcasting_stats"]

        # Cleric 4 + Ranger 2 => 4 + floor(2/2) = effective caster level 5.
        assert char["spell_slots"].get("1st") == 4
        assert char["spell_slots"].get("2nd") == 3
        assert char["spell_slots"].get("3rd") == 2
        assert stats.get("effective_caster_level") == 5

    def test_multiclass_full_plus_third_uses_floor_rule(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._cleric_eldritch_knight_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        stats = char["spellcasting_stats"]

        # Cleric 4 + Fighter(EK) 3 => 4 + floor(3/3) = effective caster level 5.
        assert char["spell_slots"].get("1st") == 4
        assert char["spell_slots"].get("2nd") == 3
        assert char["spell_slots"].get("3rd") == 2
        assert stats.get("effective_caster_level") == 5

    def test_multiclass_non_caster_rows_do_not_change_effective_caster_level(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._cleric_fighter_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        stats = char["spellcasting_stats"]

        # Cleric 4 + Fighter 1 (non-caster row) => effective caster level remains 4.
        assert char["spell_slots"].get("1st") == 4
        assert char["spell_slots"].get("2nd") == 3
        assert "3rd" not in char["spell_slots"]
        assert stats.get("effective_caster_level") == 4

    def test_multiclass_pact_magic_is_tracked_separately(self, client):
        r = client.post(
            "/api/v1/character/build",
            json={"choices_made": self._cleric_warlock_multiclass_choices()},
        )

        assert r.status_code == 200
        char = r.get_json()["character"]
        stats = char["spellcasting_stats"]

        # Cleric standard slots still use effective standard caster level 4.
        assert char["spell_slots"].get("1st") == 4
        assert char["spell_slots"].get("2nd") == 3
        assert "3rd" not in char["spell_slots"]

        # Pact slots are additive metadata, not merged into standard slots.
        assert "pact_magic_slots" in char
        assert isinstance(char["pact_magic_slots"], list)
        assert char["pact_magic_slots"][0]["class_name"] == "Warlock"
        assert char["pact_magic_slots"][0]["slots"] == 2
        assert char["pact_magic_slots"][0]["slot_level"] == 1
        assert isinstance(char.get("spell_slot_notes"), list)
        assert isinstance(stats.get("multiclass_notes"), list)

    def test_build_single_entry_classes_payload_preserves_single_class_spell_slots(
        self,
        client,
        dwarf_cleric_choices,
    ):
        legacy_payload = dict(dwarf_cleric_choices)
        new_shape_payload = {
            k: v
            for k, v in dwarf_cleric_choices.items()
            if k not in ("class", "level", "subclass")
        }
        new_shape_payload["classes"] = [{
            "class_name": dwarf_cleric_choices["class"],
            "level": dwarf_cleric_choices["level"],
            "subclass": dwarf_cleric_choices["subclass"],
        }]

        legacy_response = client.post(
            "/api/v1/character/build",
            json={"choices_made": legacy_payload},
        )
        new_shape_response = client.post(
            "/api/v1/character/build",
            json={"choices_made": new_shape_payload},
        )

        assert legacy_response.status_code == 200
        assert new_shape_response.status_code == 200

        legacy_character = legacy_response.get_json()["character"]
        new_shape_character = new_shape_response.get_json()["character"]
        assert new_shape_character["spell_slots"] == legacy_character["spell_slots"]

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

    def test_validate_step_list_excludes_basics(self, client):
        choices = {
            "character_name": "Phase3",
            "classes": [{"class_name": "Fighter", "level": 1}],
        }
        r = client.post(
            "/api/v1/character/validate",
            json={"choices_made": choices},
        )

        assert r.status_code == 200
        data = r.get_json()
        step_ids = [s["step"] for s in data["steps"]]
        assert step_ids == [
            "class",
            "background",
            "species",
            "languages",
            "abilities",
            "equipment",
            "complete",
        ]

    def test_validate_missing_character_name_reported_in_class_step(self, client):
        choices = {
            "classes": [{"class_name": "Fighter", "level": 1}],
        }
        r = client.post(
            "/api/v1/character/validate",
            json={"choices_made": choices},
        )

        assert r.status_code == 200
        data = r.get_json()
        class_step = next(s for s in data["steps"] if s["step"] == "class")
        assert class_step["complete"] is False
        assert "character_name" in class_step["missing"]
        assert "class" not in class_step["missing"]

    def test_validate_multiclass_requires_subclass_per_qualifying_class_row(self, client):
        choices = self._rogue_fighter_multiclass_choices()
        choices["classes"] = [
            {"class_name": "Rogue", "level": 3},
            {"class_name": "Fighter", "level": 2},
        ]

        r = client.post(
            "/api/v1/character/validate",
            json={"choices_made": choices},
        )

        assert r.status_code == 200
        data = r.get_json()
        class_step = next(s for s in data["steps"] if s["step"] == "class")
        assert class_step["complete"] is False
        assert "classes[0].subclass" in class_step["missing"]

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

    def test_derived_spell_management_non_caster_not_applicable(self, client, elf_fighter_choices):
        # Champion Fighter is not a spellcaster
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": elf_fighter_choices, "view": "spell_management"},
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body["view"] == "spell_management"
        assert body["applicable"] is False
        assert isinstance(body.get("reason"), str)
        assert body["data"] is None

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

    def test_derived_invocation_management_non_warlock_not_applicable(self, client, dwarf_cleric_choices):
        r = client.post(
            "/api/v1/character/derived",
            json={"choices_made": dwarf_cleric_choices, "view": "invocation_management"},
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body["view"] == "invocation_management"
        assert body["applicable"] is False
        assert isinstance(body.get("reason"), str)
        assert body["data"] is None
