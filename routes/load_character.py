"""Character loading and rebuild API routes."""

from flask import Blueprint, render_template, request, session, jsonify, send_file
import json
import io
import logging
from modules.character_builder import CharacterBuilder
from utils.route_helpers import get_builder_from_session, save_builder_to_session

load_character_bp = Blueprint("load_character", __name__)
logger = logging.getLogger(__name__)


@load_character_bp.route("/load-character")
def load_character():
    """
    Load a character from JSON file or paste.
    Allows users to upload a character JSON file or paste JSON content
    to rebuild and view their character.
    """
    return render_template("load_character.html")


@load_character_bp.route("/api/rebuild-character", methods=["POST"])
def api_rebuild_character():
    """
    API endpoint to rebuild a character from a choices_made dictionary.
    Uses CharacterBuilder to create character from choices.

    POST body can be either:
    1. JSON with {"choices_made": {...}}
    2. Form data with 'json_content' field
    3. File upload with 'json_file' field

    Returns the rebuilt character and stores it in session.
    """
    choices_made = None

    # Handle different input methods
    if request.is_json:
        # JSON POST body
        data = request.get_json()
        if not data or "choices_made" not in data:
            return jsonify({"error": "Missing choices_made in request body"}), 400
        choices_made = data["choices_made"]
    else:
        # Form data (file upload or textarea)
        if "json_file" in request.files:
            file = request.files["json_file"]
            if file and file.filename:
                try:
                    content = file.read().decode("utf-8")
                    data = json.loads(content)
                    choices_made = data.get("choices_made", data)
                except Exception as e:
                    return jsonify({"error": f"Invalid JSON file: {str(e)}"}), 400
        elif "json_content" in request.form:
            try:
                content = request.form.get("json_content")
                data = json.loads(content)
                choices_made = data.get("choices_made", data)
            except Exception as e:
                return jsonify({"error": f"Invalid JSON content: {str(e)}"}), 400
        else:
            return jsonify({"error": "No JSON data provided"}), 400

    if not choices_made:
        return jsonify({"error": "No choices_made data found"}), 400

    try:
        # Create character using CharacterBuilder
        builder = CharacterBuilder()
        builder.apply_choices(choices_made)

        # Debug: Check ability scores after applying choices
        char_data = builder.to_json()
        logger.debug(
            f"After apply_choices - ability_scores: {char_data.get('ability_scores')}"
        )
        logger.debug(
            f"Background bonuses from choices: {choices_made.get('background_bonuses')}"
        )

        # Mark as complete
        builder.set_step("complete")

        # Store in session
        save_builder_to_session(builder)
        session.permanent = True

        # Get character data with all calculations for response
        character = builder.to_character()

        return jsonify(
            {
                "success": True,
                "message": "Character loaded successfully",
                "character": character,
                "redirect_url": "/character-summary",
            }
        ), 200

    except Exception as e:
        import traceback

        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@load_character_bp.route("/api/choices-to-character", methods=["POST"])
def api_choices_to_character():
    """
    Pure API endpoint to convert choices_made to character_data.
    Does not affect session - purely for testing and debugging.

    POST body: {"choices_made": {...}}
    Returns: {"character_data": {...}}
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if not data or "choices_made" not in data:
        return jsonify({"error": "Missing choices_made in request body"}), 400

    choices_made = data["choices_made"]

    try:
        # Create character using CharacterBuilder
        builder = CharacterBuilder()
        builder.apply_choices(choices_made)

        # Get complete character data with calculations
        character_data = builder.to_character()

        return jsonify({"success": True, "character_data": character_data}), 200

    except Exception as e:
        import traceback

        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@load_character_bp.route("/api/download-character", methods=["GET"])
def api_download_character():
    """
    Download character data as JSON file.
    Requires character in session.
    """
    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400

    try:
        character_data = builder.to_character()

        # Create JSON file
        json_str = json.dumps(character_data, indent=2, ensure_ascii=False)

        # Create file-like object
        json_file = io.BytesIO()
        json_file.write(json_str.encode("utf-8"))
        json_file.seek(0)

        # Generate filename
        char_name = character_data.get("name", "Character").replace(" ", "_")
        filename = f"{char_name}_character_data.json"

        return send_file(
            json_file,
            as_attachment=True,
            download_name=filename,
            mimetype="application/json",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
