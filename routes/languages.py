"""Language selection routes."""

from flask import Blueprint, render_template, request, redirect, url_for
import logging
from modules.data_loader import DataLoader
from utils.route_helpers import (
    get_builder_from_session,
    save_builder_to_session,
    log_route_processing,
)

languages_bp = Blueprint("languages", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


@languages_bp.route("/choose-languages")
def choose_languages():
    """Language selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    # Allow access if step is 'languages' or we're navigating back from later steps
    current_step = builder.get_current_step()
    if current_step not in [
        "languages",
        "ability_scores",
        "background_bonuses",
        "complete",
    ]:
        return redirect(url_for("index.index"))

    # Update step to languages when accessing this page
    builder.set_step("languages")
    save_builder_to_session(builder)

    character = builder.to_json()

    # Get language options from builder (business logic moved to CharacterBuilder)
    language_options = builder.get_language_options()
    base_languages = language_options["base_languages"]
    available_languages = language_options["available_languages"]

    return render_template(
        "choose_languages.html",
        character=character,
        base_languages=sorted(base_languages),
        available_languages=available_languages,
    )


@languages_bp.route("/select-languages", methods=["POST"])
def select_languages():
    """Handle language selection."""
    selected_languages = request.form.getlist("languages")

    builder_before = get_builder_from_session()
    choices = {"languages": selected_languages}

    builder = get_builder_from_session()
    builder.apply_choice("languages", selected_languages)
    builder.set_step("ability_scores")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_languages", choices, builder_before, builder)

    return redirect(url_for("ability_scores.assign_ability_scores"))
