"""Equipment selection routes."""

from flask import Blueprint, render_template, request, redirect, url_for
import logging
from modules.data_loader import DataLoader
from utils.route_helpers import (
    get_builder_from_session,
    save_builder_to_session,
    log_route_processing,
)

equipment_bp = Blueprint("equipment", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


@equipment_bp.route("/choose-equipment")
def choose_equipment():
    """Equipment selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()

    # Allow access if at equipment step or later
    if character.get("step") not in ["equipment", "complete"]:
        return redirect(url_for("index.index"))

    class_name = character.get("class", "")
    background_name = character.get("background", "")

    # Get starting equipment from class
    class_data = data_loader.classes.get(class_name, {})
    class_equipment = class_data.get("starting_equipment", {})

    # Get starting equipment from background
    background_data = data_loader.backgrounds.get(background_name, {})
    background_equipment = background_data.get("starting_equipment", {})

    return render_template(
        "choose_equipment.html",
        character=character,
        class_equipment=class_equipment,
        background_equipment=background_equipment,
    )


@equipment_bp.route("/select-equipment", methods=["POST"])
def select_equipment():
    """Handle equipment selection."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()

    # Collect equipment choices from form
    equipment_choices = {
        "class_equipment": request.form.get("class_equipment"),
        "background_equipment": request.form.get("background_equipment"),
    }

    # Store equipment selections
    builder.apply_choice("equipment_selections", equipment_choices)

    save_builder_to_session(builder)

    # Mark character creation as complete
    builder.set_step("complete")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_equipment", equipment_choices, builder_before, builder)

    return redirect(url_for("character_summary.character_summary"))
