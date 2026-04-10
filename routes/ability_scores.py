"""Ability score assignment routes."""

from flask import Blueprint, render_template, request, redirect, url_for
import logging
from modules.data_loader import DataLoader
from modules.ability_scores import POINT_BUY_COSTS, POINT_BUY_TOTAL, POINT_BUY_MIN, POINT_BUY_MAX, validate_point_buy
from utils.route_helpers import (
    get_builder_from_session,
    save_builder_to_session,
    log_route_processing,
    get_nav_context,
)

ability_scores_bp = Blueprint("ability_scores", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]


def _ability_score_template_context(character):
    """Build the shared template context for the ability score assignment page."""
    class_name = character.get("class", "")
    class_data = data_loader.classes.get(class_name, {})
    recommended_allocation = class_data.get("standard_array_assignment", {})

    primary_ability_data = class_data.get("primary_ability", "")
    if isinstance(primary_ability_data, list):
        primary_abilities = primary_ability_data
    elif isinstance(primary_ability_data, str):
        primary_abilities = primary_ability_data.split(", ") if primary_ability_data else []
    else:
        primary_abilities = []

    return dict(
        primary_abilities=primary_abilities,
        standard_array=STANDARD_ARRAY,
        recommended_allocation=recommended_allocation,
        point_buy_costs=POINT_BUY_COSTS,
        point_buy_total=POINT_BUY_TOTAL,
        point_buy_min=POINT_BUY_MIN,
        point_buy_max=POINT_BUY_MAX,
    )


@ability_scores_bp.route("/assign-ability-scores")
def assign_ability_scores():
    """Ability score assignment step (merged with background bonuses)."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()

    # Allow access if we're at ability_scores step or later
    if character.get("step") not in [
        "ability_scores",
        "equipment",
        "complete",
    ]:
        return redirect(url_for("index.index"))

    # Background ASI options (merged from old background_bonuses page)
    asi_options = builder.get_background_asi_options()

    nav = get_nav_context(builder, "ability_scores")
    return render_template(
        "assign_ability_scores.html",
        character=character,
        **_ability_score_template_context(character),
        asi_total_points=asi_options["total_points"],
        asi_suggested=asi_options["suggested"],
        asi_ability_options=asi_options["ability_options"],
        **nav,
    )


@ability_scores_bp.route("/submit-ability-scores", methods=["POST"])
def submit_ability_scores():
    """Process ability score assignment."""
    assignment_method = request.form.get("assignment_method")

    builder_before = get_builder_from_session()
    builder = get_builder_from_session()

    choices = {"assignment_method": assignment_method}

    if assignment_method == "recommended":
        # Use recommended ability scores for the class
        builder.apply_choice("ability_scores_method", "recommended")
    elif assignment_method == "point_buy":
        # Get point-buy scores from form
        point_buy_scores = {}
        for ability in [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]:
            score = request.form.get(f"pb_ability_{ability}")
            if score:
                point_buy_scores[ability] = int(score)

        is_valid, error_msg = validate_point_buy(point_buy_scores)
        if not is_valid:
            logger.warning("Invalid point buy submission: %s", error_msg)
            character = builder.to_json()
            return render_template(
                "assign_ability_scores.html",
                character=character,
                **_ability_score_template_context(character),
                point_buy_error=error_msg,
            )

        builder.apply_choice("ability_scores", point_buy_scores)
        choices["ability_scores"] = point_buy_scores
        builder.apply_choice("ability_scores_method", "point_buy")
    else:  # manual
        # Get manual assignments from form
        manual_scores = {}
        for ability in [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]:
            score = request.form.get(f"ability_{ability}")
            if score:
                manual_scores[ability] = int(score)

        # Apply manual scores
        builder.apply_choice("ability_scores", manual_scores)
        choices["ability_scores"] = manual_scores

        # IMPORTANT: Mark that manual method was used to override any previous "recommended" choice
        builder.apply_choice("ability_scores_method", "manual")

    # --- Background bonuses (merged from old background_bonuses page) ---
    bonus_method = request.form.get("bonus_method", "suggested")
    if bonus_method == "suggested":
        builder.apply_choice("background_bonuses_method", "suggested")
        choices["bonus_method"] = "suggested"
    else:
        manual_bonuses = {}
        for ability in [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]:
            bonus = request.form.get(f"bonus_{ability}")
            if bonus and int(bonus) > 0:
                manual_bonuses[ability] = int(bonus)
        builder.apply_choice("background_bonuses", manual_bonuses)
        choices["background_bonuses"] = manual_bonuses

    save_builder_to_session(builder)

    # Next step: equipment selection (skip old background_bonuses step)
    builder.set_step("equipment")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("submit_ability_scores", choices, builder_before, builder)

    return redirect(url_for("equipment.choose_equipment"))


@ability_scores_bp.route("/background-bonuses")
def background_bonuses():
    """Redirect to ability scores (bonuses are now merged there)."""
    return redirect(url_for("ability_scores.assign_ability_scores"))


@ability_scores_bp.route("/submit-background-bonuses", methods=["POST"])
def submit_background_bonuses():
    """Redirect to ability scores (bonuses are now merged there)."""
    return redirect(url_for("ability_scores.assign_ability_scores"))
