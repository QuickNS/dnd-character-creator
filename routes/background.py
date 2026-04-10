"""Background selection routes."""

from flask import Blueprint, render_template, request, redirect, url_for
import logging
from modules.data_loader import DataLoader
from utils.route_helpers import (
    get_builder_from_session,
    save_builder_to_session,
    log_route_processing,
    get_nav_context,
)


background_bp = Blueprint("background", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


@background_bp.route("/choose-background")
def choose_background():
    """Background selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()
    # Ensure class is selected before accessing backgrounds
    if not character.get("class"):
        return redirect(url_for("character_creation.choose_class"))

    # Update step to background when accessing this page
    builder.set_step("background")
    save_builder_to_session(builder)

    backgrounds = dict(sorted(data_loader.backgrounds.items()))
    nav = get_nav_context(builder, "background")
    return render_template(
        "choose_background.html", backgrounds=backgrounds, character=character, **nav
    )


@background_bp.route("/select-background", methods=["POST"])
def select_background():
    """Handle background selection."""
    background_name = request.form.get("background")
    if not background_name or background_name not in data_loader.backgrounds:
        return redirect(url_for("background.choose_background"))

    builder_before = get_builder_from_session()
    choices = {"background": background_name}

    builder = get_builder_from_session()
    builder.apply_choice("background", background_name)
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_background", choices, builder_before, builder)

    # If the background overlaps with existing class skill proficiencies,
    # redirect to the replacement skill selection step first.
    replacement_info = builder.get_background_skill_replacement_info()
    if replacement_info["needed"] > 0:
        builder.set_step("background_skill_replacement")
        save_builder_to_session(builder)
        return redirect(url_for("background.choose_replacement_skills"))

    builder.set_step("feat_choices")
    save_builder_to_session(builder)
    return redirect(url_for("background.feat_choices"))


@background_bp.route("/choose-replacement-skills")
def choose_replacement_skills():
    """Choose replacement skill proficiencies when background overlaps with class skills."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    replacement_info = builder.get_background_skill_replacement_info()
    if not replacement_info["needed"]:
        return redirect(url_for("background.feat_choices"))

    character = builder.to_json()
    background_data = character.get("background_data") or {}
    background_skills = background_data.get("skill_proficiencies", [])

    nav = get_nav_context(builder, "background_skill_replacement")
    return render_template(
        "choose_replacement_skills.html",
        character=character,
        replacement_info=replacement_info,
        background_skills=background_skills,
        **nav,
    )


@background_bp.route("/submit-replacement-skills", methods=["POST"])
def submit_replacement_skills():
    """Process replacement skill selection submissions."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    replacement_info = builder.get_background_skill_replacement_info()
    needed = replacement_info["needed"]

    skills = request.form.getlist("replacement_skills")[:needed]

    if len(skills) < needed:
        # Not enough skills selected — return to the replacement page
        save_builder_to_session(builder)
        return redirect(url_for("background.choose_replacement_skills"))

    builder.apply_background_skill_replacement(skills)
    log_route_processing(
        "submit_replacement_skills",
        {"replacement_skills": skills},
        builder_before,
        builder,
    )

    builder.set_step("feat_choices")
    save_builder_to_session(builder)
    return redirect(url_for("background.feat_choices"))


@background_bp.route("/feat-choices")
def feat_choices():
    """Display origin feat choices granted by the selected background (if any)."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    feat_choice_data = builder.get_feat_choices()

    # Nothing to choose — skip straight to species
    if not feat_choice_data["choices"]:
        builder.set_step("species")
        save_builder_to_session(builder)
        return redirect(url_for("species.choose_species"))

    character = builder.to_json()
    choices_made = character.get("choices_made", {})

    nav = get_nav_context(builder, "feat_choices")
    return render_template(
        "feat_choices.html",
        character=character,
        feat_name=feat_choice_data["feat_name"],
        feat_description=feat_choice_data["feat_description"],
        feat_benefits=feat_choice_data["feat_benefits"],
        choices=feat_choice_data["choices"],
        choices_made=choices_made,
        **nav,
    )


@background_bp.route("/submit-feat-choices", methods=["POST"])
def submit_feat_choices():
    """Process origin feat choice submissions."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    # Collect feat choices from the form (field names: feat_choice_<choice_name>)
    # Always keep values as a list so apply_feat_choices handles them uniformly.
    choices: dict = {}
    for key, values in request.form.lists():
        if key.startswith("feat_choice_"):
            choice_name = key[len("feat_choice_"):]
            choices[choice_name] = values

    if choices:
        builder.apply_feat_choices(choices)

    builder.set_step("species")
    save_builder_to_session(builder)

    log_route_processing("submit_feat_choices", choices, builder_before, builder)

    return redirect(url_for("species.choose_species"))
