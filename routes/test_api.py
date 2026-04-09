"""Test-only API endpoints for agent-driven integration testing.

These endpoints are stateless (no session) and designed for automated validation.
They supplement the existing /api/choices-to-character endpoint.
"""

from flask import Blueprint, request, jsonify
import json
import os
import logging
from modules.character_builder import CharacterBuilder

test_api_bp = Blueprint("test_api", __name__, url_prefix="/api/test")
logger = logging.getLogger(__name__)


@test_api_bp.route("/build-character", methods=["POST"])
def build_character():
    """
    Stateless character build from choices_made.
    Alias for /api/choices-to-character with a cleaner interface.

    POST body: {"choices_made": {...}}
    Returns: {"success": true, "character": {...}}
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if not data or "choices_made" not in data:
        return jsonify({"error": "Missing choices_made in request body"}), 400

    try:
        builder = CharacterBuilder()
        builder.apply_choices(data["choices_made"])
        character = builder.to_character()
        return jsonify({"success": True, "character": character}), 200
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@test_api_bp.route("/validate-effects", methods=["POST"])
def validate_effects():
    """
    Build a minimal character and return only the applied effects.
    Useful for quickly verifying effect application without full character build.

    POST body: {
        "species": "Dwarf",
        "class": "Cleric",
        "subclass": "Light Domain",  (optional)
        "level": 3,                  (optional, default 1)
        "lineage": "High Elf"       (optional)
    }
    Returns: {"success": true, "effects": [...], "features": {...}}
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Empty request body"}), 400

    # Build minimal choices
    choices = {
        "character_name": "EffectTest",
        "level": data.get("level", 1),
        "alignment": "Neutral",
        "background": data.get("background", "Acolyte"),
        "ability_scores": data.get("ability_scores", {
            "Strength": 10, "Dexterity": 10, "Constitution": 10,
            "Intelligence": 10, "Wisdom": 10, "Charisma": 10
        }),
        "background_bonuses": data.get("background_bonuses", {})
    }

    if "species" in data:
        choices["species"] = data["species"]
    if "lineage" in data:
        choices["lineage"] = data["lineage"]
    if "class" in data:
        choices["class"] = data["class"]
    if "subclass" in data:
        choices["subclass"] = data["subclass"]

    try:
        builder = CharacterBuilder()
        builder.apply_choices(choices)
        character = builder.to_character()

        return jsonify({
            "success": True,
            "effects": character.get("effects", []),
            "features": character.get("features", {}),
            "proficiencies": character.get("proficiencies", {}),
            "spells": character.get("spells", {})
        }), 200
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@test_api_bp.route("/schema-validate", methods=["POST"])
def schema_validate():
    """
    Validate a JSON payload against the appropriate schema.

    POST body: {
        "schema_type": "class" | "subclass",
        "data": {...}
    }
    Returns: {"valid": true/false, "errors": [...]}
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    schema_type = data.get("schema_type")
    payload = data.get("data")

    if not schema_type or not payload:
        return jsonify({"error": "Missing schema_type or data"}), 400

    schema_map = {
        "class": "models/class_schema.json",
        "subclass": "models/subclass_schema.json",
    }

    schema_path = schema_map.get(schema_type)
    if not schema_path:
        return jsonify({"error": f"Unknown schema_type: {schema_type}. Valid: {list(schema_map.keys())}"}), 400

    try:
        import jsonschema

        with open(schema_path, "r") as f:
            schema = json.load(f)

        errors = []
        validator = jsonschema.Draft7Validator(schema)
        for error in validator.iter_errors(payload):
            errors.append({
                "path": list(error.absolute_path),
                "message": error.message,
                "schema_path": list(error.absolute_schema_path)
            })

        return jsonify({
            "valid": len(errors) == 0,
            "errors": errors,
            "schema_type": schema_type
        }), 200
    except FileNotFoundError:
        return jsonify({"error": f"Schema file not found: {schema_path}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
