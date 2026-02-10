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


@character_summary_bp.route("/api/spell-details/<spell_name>")
def api_spell_details(spell_name):
    """Return spell details for a given spell name."""
    from pathlib import Path
    import json

    # Load spell definition from data files
    data_dir = Path(__file__).parent.parent / "data" / "spells" / "definitions"

    # Convert spell name to filename format (lowercase, underscores)
    filename = (
        spell_name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
        + ".json"
    )
    spell_file = data_dir / filename

    if not spell_file.exists():
        return jsonify({"error": f"Spell '{spell_name}' not found"}), 404

    try:
        with open(spell_file, "r") as f:
            spell_data = json.load(f)
        return jsonify(spell_data)
    except (json.JSONDecodeError, IOError) as e:
        return jsonify({"error": f"Failed to load spell data: {str(e)}"}), 500


@character_summary_bp.route("/api/spell-management-data")
def api_spell_management_data():
    """Return spell management data for the modal."""
    from pathlib import Path

    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400

    try:
        # Get spellcasting stats
        stats = builder.calculate_spellcasting_stats()

        if not stats or not stats.get("has_spellcasting"):
            return jsonify({"error": "Character is not a spellcaster"}), 400

        # Get always-prepared spells
        always_prepared = []
        if (
            "spells" in builder.character_data
            and "always_prepared" in builder.character_data["spells"]
        ):
            for spell_name, spell_data in builder.character_data["spells"][
                "always_prepared"
            ].items():
                always_prepared.append(
                    {
                        "name": spell_name,
                        "level": spell_data.get("level", 0),
                        "source": spell_data.get("source", "Unknown"),
                        "counts_against_limit": spell_data.get(
                            "counts_against_limit", True
                        ),
                    }
                )

        # Get available cantrips from class spell list
        available_cantrips = []
        class_name = builder.character_data.get("class")
        if class_name:
            spell_list_file = (
                Path(__file__).parent.parent
                / "data"
                / "spells"
                / "class_lists"
                / f"{class_name.lower()}.json"
            )
            if spell_list_file.exists():
                with open(spell_list_file, "r") as f:
                    spell_list_data = json.load(f)
                    cantrip_names = spell_list_data.get("cantrips", [])
                    for spell_name in cantrip_names:
                        available_cantrips.append(
                            {
                                "name": spell_name,
                                "school": "Unknown",  # Will be filled by spell details modal
                            }
                        )

        # Get available spells from class spell list (organized by level)
        available_spells = {}
        if class_name:
            spell_list_file = (
                Path(__file__).parent.parent
                / "data"
                / "spells"
                / "class_lists"
                / f"{class_name.lower()}.json"
            )
            if spell_list_file.exists():
                with open(spell_list_file, "r") as f:
                    spell_list_data = json.load(f)
                    for level_str, spell_names in spell_list_data.get(
                        "spells_by_level", {}
                    ).items():
                        int(level_str)
                        # Show all spell levels (user can prepare only what they can cast)
                        available_spells[level_str] = []
                        for spell_name in spell_names:
                            available_spells[level_str].append(
                                {
                                    "name": spell_name,
                                    "school": "Unknown",  # Will be filled by spell details modal
                                }
                            )

        # Get current selections from character
        # Handle both old (list) and new (dict) spell storage formats
        spells_data = builder.character_data.get("spells", {})
        prepared = spells_data.get("prepared", {})

        # Convert old list format to dict format if needed
        if isinstance(prepared, list):
            prepared = {"cantrips": {}, "spells": {}}

        current_selections = {
            "cantrips": list(prepared.get("cantrips", {}).keys())
            if isinstance(prepared.get("cantrips", {}), dict)
            else [],
            "spells": list(prepared.get("spells", {}).keys())
            if isinstance(prepared.get("spells", {}), dict)
            else [],
            "background_cantrips": [],
            "background_spells": [],
        }

        # Handle background spell requirements
        background_requirements = None
        if stats.get("background_spell_requirements"):
            bg_req = stats["background_spell_requirements"]
            background_requirements = {}

            # Background cantrips
            if bg_req.get("cantrips_needed", 0) > 0:
                bg_cantrips = []
                bg_class = bg_req.get("cantrip_class", "")
                if bg_class:
                    bg_spell_list_file = (
                        Path(__file__).parent.parent
                        / "data"
                        / "spells"
                        / "class_lists"
                        / f"{bg_class.lower()}.json"
                    )
                    if bg_spell_list_file.exists():
                        with open(bg_spell_list_file, "r") as f:
                            bg_spell_list_data = json.load(f)
                            cantrip_names = bg_spell_list_data.get("cantrips", [])
                            for spell_name in cantrip_names:
                                bg_cantrips.append(
                                    {"name": spell_name, "school": "Unknown"}
                                )

                background_requirements["cantrips"] = {
                    "count": bg_req["cantrips_needed"],
                    "class_name": bg_class,
                    "available": bg_cantrips,
                }

                # Get current background cantrip selections
                background_spells = spells_data.get("background_spells", {})
                if isinstance(background_spells, dict):
                    current_selections["background_cantrips"] = [
                        name
                        for name, data in background_spells.items()
                        if isinstance(data, dict) and data.get("level") == 0
                    ]

            # Background spells
            if bg_req.get("spells_needed", 0) > 0:
                bg_spells = []
                bg_class = bg_req.get("spell_class", "")
                if bg_class:
                    bg_spell_list_file = (
                        Path(__file__).parent.parent
                        / "data"
                        / "spells"
                        / "class_lists"
                        / f"{bg_class.lower()}.json"
                    )
                    if bg_spell_list_file.exists():
                        with open(bg_spell_list_file, "r") as f:
                            bg_spell_list_data = json.load(f)
                            # Get level 1 spells only (typical for background features)
                            spell_names = bg_spell_list_data.get(
                                "spells_by_level", {}
                            ).get("1", [])
                            for spell_name in spell_names:
                                bg_spells.append(
                                    {"name": spell_name, "school": "Unknown"}
                                )

                background_requirements["spells"] = {
                    "count": bg_req["spells_needed"],
                    "class_name": bg_class,
                    "available": bg_spells,
                }

                # Get current background spell selections
                background_spells = spells_data.get("background_spells", {})
                if isinstance(background_spells, dict):
                    current_selections["background_spells"] = [
                        name
                        for name, data in background_spells.items()
                        if isinstance(data, dict) and data.get("level", 0) > 0
                    ]

        return jsonify(
            {
                "always_prepared": always_prepared,
                "available_cantrips": available_cantrips,
                "available_spells": available_spells,
                "current_selections": current_selections,
                "limits": {
                    "cantrips": stats.get("max_cantrips_to_prepare", 0),
                    "spells": stats.get("max_spells_to_prepare", 0),
                },
                "background_requirements": background_requirements,
            }
        )

    except Exception as e:
        logger.error(f"Error loading spell management data: {e}")
        return jsonify({"error": str(e)}), 500


@character_summary_bp.route("/api/save-spell-selections", methods=["POST"])
def api_save_spell_selections():
    """Save spell selections from the modal."""
    from flask import request
    from utils.route_helpers import save_builder_to_session

    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400

    try:
        selections = request.get_json()

        # Validate selections
        if not selections:
            return jsonify({"error": "No selections provided"}), 400

        # Initialize spell storage if it doesn't exist
        if "spells" not in builder.character_data:
            builder.character_data["spells"] = {
                "always_prepared": {},
                "prepared": {"cantrips": {}, "spells": {}},
                "background_spells": {},
            }

        # Save cantrips to prepared
        builder.character_data["spells"]["prepared"]["cantrips"] = {}
        for cantrip_name in selections.get("cantrips", []):
            builder.character_data["spells"]["prepared"]["cantrips"][cantrip_name] = {
                "source": "Selected",
                "level": 0,
            }

        # Save spells to prepared
        builder.character_data["spells"]["prepared"]["spells"] = {}
        for spell_name in selections.get("spells", []):
            # Determine spell level from spell data
            builder.character_data["spells"]["prepared"]["spells"][spell_name] = {
                "source": "Selected"
            }

        # Save background cantrips
        for cantrip_name in selections.get("background_cantrips", []):
            builder.character_data["spells"]["background_spells"][cantrip_name] = {
                "source": "Background",
                "level": 0,
            }

        # Save background spells
        for spell_name in selections.get("background_spells", []):
            builder.character_data["spells"]["background_spells"][spell_name] = {
                "source": "Background",
                "level": 1,  # Assuming level 1 for background spells
            }

        # CRITICAL: Save the builder back to the session
        save_builder_to_session(builder)

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error saving spell selections: {e}")
        return jsonify({"error": str(e)}), 500


@character_summary_bp.route("/api/mastery-management-data")
def api_mastery_management_data():
    """Return weapon mastery management data for the modal."""
    from pathlib import Path
    import json

    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400

    try:
        # Get weapon mastery stats
        stats = builder.calculate_weapon_mastery_stats()

        if not stats or not stats.get("has_mastery"):
            return jsonify({"error": "Character does not have weapon mastery"}), 400

        # Get current masteries
        current_masteries = stats.get("current_masteries", [])

        # Load weapon data to get mastery properties
        weapons_file = (
            Path(__file__).parent.parent / "data" / "equipment" / "weapons.json"
        )
        weapon_masteries = {}

        if weapons_file.exists():
            with open(weapons_file, "r") as f:
                weapons_data = json.load(f)
                for weapon_name in stats.get("available_weapons", []):
                    if weapon_name in weapons_data:
                        weapon_masteries[weapon_name] = weapons_data[weapon_name].get(
                            "mastery", "Unknown"
                        )

        return jsonify(
            {
                "available_weapons": stats.get("available_weapons", []),
                "max_masteries": stats.get("max_masteries", 0),
                "current_masteries": current_masteries,
                "weapon_masteries": weapon_masteries,
            }
        )

    except Exception as e:
        logger.error(f"Error loading mastery management data: {e}")
        return jsonify({"error": str(e)}), 500


@character_summary_bp.route("/api/save-mastery-selections", methods=["POST"])
def api_save_mastery_selections():
    """Save weapon mastery selections from the modal."""
    from flask import request
    from utils.route_helpers import save_builder_to_session

    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400

    try:
        data = request.get_json()

        # Validate selections
        if not data or "masteries" not in data:
            return jsonify({"error": "No masteries provided"}), 400

        masteries = data["masteries"]

        # Validate mastery count
        stats = builder.calculate_weapon_mastery_stats()
        max_masteries = stats.get("max_masteries", 0)

        if len(masteries) > max_masteries:
            return jsonify(
                {"error": f"Too many masteries selected. Maximum is {max_masteries}"}
            ), 400

        # Save masteries to character data
        if "weapon_masteries" not in builder.character_data:
            builder.character_data["weapon_masteries"] = {
                "selected": [],
                "available": [],
                "max_count": 0,
            }

        builder.character_data["weapon_masteries"]["selected"] = masteries

        # CRITICAL: Save the builder back to the session
        save_builder_to_session(builder)

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error saving mastery selections: {e}")
        return jsonify({"error": str(e)}), 500


@character_summary_bp.route("/api/mastery-details/<mastery_name>")
def api_mastery_details(mastery_name):
    """Return weapon mastery details for a given mastery name."""
    from pathlib import Path
    import json

    # Load mastery definitions
    data_dir = Path(__file__).parent.parent / "data" / "equipment"
    mastery_file = data_dir / "weapon_masteries.json"

    if not mastery_file.exists():
        return jsonify({"error": "Mastery definitions not found"}), 404

    try:
        with open(mastery_file, "r") as f:
            masteries_data = json.load(f)

        if mastery_name not in masteries_data:
            return jsonify({"error": f"Mastery '{mastery_name}' not found"}), 404

        return jsonify(masteries_data[mastery_name])
    except (json.JSONDecodeError, IOError) as e:
        return jsonify({"error": f"Failed to load mastery data: {str(e)}"}), 500
