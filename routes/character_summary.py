"""Character summary and download routes."""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    jsonify,
    current_app,
)
import json
import logging
from modules.data_loader import DataLoader
from utils.route_helpers import get_builder_from_session

character_summary_bp = Blueprint("character_summary", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


# ==================== Route Handlers ====================


@character_summary_bp.route("/character-summary")
def character_summary():
    """Display final character summary."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != "complete":
        return redirect(url_for("index.index"))

    # Get complete character data with all calculations
    # (ac_options, spells_by_level, and spell_slots are now part of character_data)
    character_data = builder.to_character()

    logger.debug(
        f"Character summary - ability_scores: {character_data.get('ability_scores')}"
    )
    logger.debug(
        f"Character summary - attacks count: {len(character_data.get('attacks', []))}"
    )
    logger.debug(
        f"Character summary - skills: {list(character_data.get('skills', {}).keys())}"
    )
    logger.debug(
        f"Character summary - AC options count: {len(character_data.get('ac_options', []))}"
    )
    logger.debug(
        f"Character summary - spell levels: {list(character_data.get('spells_by_level', {}).keys())}"
    )

    return render_template("character_summary.html", character=character_data)


@character_summary_bp.route("/download-character")
def download_character():
    """Download character data as JSON file."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    # Get complete character data with all calculations
    character_data = builder.to_character()

    char_name = character_data.get("name", "character").lower().replace(" ", "_")
    filename = f"{char_name}_character_data.json"

    response = current_app.response_class(
        response=json.dumps(character_data, indent=2),
        status=200,
        mimetype="application/json",
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@character_summary_bp.route("/api/character-sheet")
def api_character_sheet():
    """Return character data as JSON API response."""
    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400

    # Get complete character data with all calculations
    character_data = builder.to_character()

    return jsonify(character_data)


@character_summary_bp.route("/download-character-v2")
def download_character_v2():
    """Download character data (same as /download-character for consistency)."""
    # Redirect to main download endpoint for consistency
    return redirect(url_for("character_summary.download_character"))


@character_summary_bp.route("/api/character-sheet-v2")
def api_character_sheet_v2():
    """Return character data (same as /api/character-sheet for consistency)."""
    # Redirect to main API endpoint for consistency
    return redirect(url_for("character_summary.api_character_sheet"))


@character_summary_bp.route("/character-sheet")
def character_sheet():
    """Display fillable HTML character sheet."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != "complete":
        return redirect(url_for("index.index"))

    # Get complete character data with ALL calculations from CharacterBuilder
    # No transformations needed - template uses data as-is
    character_data = builder.to_character()

    return render_template("character_sheet_pdf.html", character=character_data)
