"""Species, traits, and lineage selection routes."""

from flask import Blueprint, render_template, request, redirect, url_for
import json
import logging
from pathlib import Path
from modules.data_loader import DataLoader
from utils.route_helpers import (
    get_builder_from_session,
    save_builder_to_session,
    log_route_processing,
    get_nav_context,
    redirect_after_edit_or,
    is_editing,
)

species_bp = Blueprint("species", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


def _redirect_to_languages_or_replacement(builder):
    """Check for species skill overlaps before moving to languages.

    If the species/lineage tried to grant a skill the character already has,
    redirect to the replacement-skills page.  Otherwise go straight to
    language selection.
    """
    info = builder.get_species_skill_replacement_info()
    if info["needed"] and not info["already_chosen"]:
        builder.set_step("species_skill_replacement")
        save_builder_to_session(builder)
        return redirect(url_for("species.choose_species_replacement_skills"))
    builder.set_step("languages")
    save_builder_to_session(builder)
    return redirect_after_edit_or("languages.choose_languages")


@species_bp.route("/choose-species")
def choose_species():
    """Species selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()
    if not character.get("background"):
        return redirect(url_for("background.choose_background"))

    builder.set_step("species")
    save_builder_to_session(builder)

    species = dict(sorted(data_loader.species.items()))
    nav = get_nav_context(builder, "species")

    # Build a per-species next-label map so the template can update the button
    # dynamically via JavaScript when the user selects a species card.
    species_next_labels = {}
    for name, data in species.items():
        has_trait_choices = any(
            isinstance(t, dict) and t.get("type") == "choice"
            for t in data.get("traits", {}).values()
        )
        if has_trait_choices:
            species_next_labels[name] = "Continue to Species Traits"
        elif data.get("lineages"):
            species_next_labels[name] = "Continue to Lineage"
        else:
            species_next_labels[name] = "Continue to Languages"

    return render_template(
        "choose_species.html",
        species=species,
        character=character,
        species_next_labels=species_next_labels,
        **nav,
    )


@species_bp.route("/select-species", methods=["POST"])
def select_species():
    """Handle species selection using CharacterBuilder."""
    species_name = request.form.get("species")
    if not species_name or species_name not in data_loader.species:
        return redirect(url_for("species.choose_species"))

    builder_before = get_builder_from_session()
    choices = {"species": species_name}

    builder = get_builder_from_session()
    builder.apply_choice("species", species_name)

    save_builder_to_session(builder)

    # Check if species has trait choices that need to be made
    species_data = data_loader.species[species_name]
    has_trait_choices = False
    if "traits" in species_data:
        for trait_name, trait_data in species_data["traits"].items():
            if isinstance(trait_data, dict) and trait_data.get("type") == "choice":
                has_trait_choices = True
                break

    # Update session step based on what comes next
    if has_trait_choices:
        builder.set_step("species_traits")
        save_builder_to_session(builder)
        # Log route processing
        log_route_processing("select_species", choices, builder_before, builder)
        return redirect(url_for("species.choose_species_traits"))
    elif species_data.get("lineages"):
        builder.set_step("lineage")
        save_builder_to_session(builder)
        # Log route processing
        log_route_processing("select_species", choices, builder_before, builder)
        return redirect(url_for("species.choose_lineage"))
    else:
        # Log route processing
        log_route_processing("select_species", choices, builder_before, builder)

        return _redirect_to_languages_or_replacement(builder)


@species_bp.route("/choose-species-traits")
def choose_species_traits():
    """Species trait choice step (e.g., Keen Senses)."""
    builder = get_builder_from_session()
    if not builder or (builder.get_current_step() != "species_traits" and not is_editing()):
        return redirect(url_for("index.index"))

    character = builder.to_json()

    # Get species trait choices from builder (business logic moved to CharacterBuilder)
    trait_choices = builder.get_species_trait_choices()

    nav = get_nav_context(builder, "species_traits")
    return render_template(
        "choose_species_traits.html", character=character, trait_choices=trait_choices, **nav
    )


@species_bp.route("/select-species-traits", methods=["POST"])
def select_species_traits():
    """Handle species trait choices using CharacterBuilder."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    character = builder.to_json()
    species_name = character.get("species")

    if not species_name:
        return redirect(url_for("species.choose_species"))

    species_data = data_loader.species.get(species_name, {})

    # Collect trait choices
    choices = {}

    # Process trait choices
    if "traits" in species_data:
        for trait_name, trait_data in species_data["traits"].items():
            if isinstance(trait_data, dict) and trait_data.get("type") == "choice":
                choice_key = f"trait_{trait_name.lower().replace(' ', '_')}"
                selected_option = request.form.get(choice_key)

                if selected_option:
                    # Apply the choice using just the trait name
                    builder.apply_choice(trait_name, selected_option)
                    choices[trait_name] = selected_option

    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_species_traits", choices, builder_before, builder)

    # If any species trait granted an origin feat that requires choices,
    # redirect to the species feat choices step before proceeding.
    species_feat_data = builder.get_species_feat_choices()
    if species_feat_data["choices"]:
        builder.set_step("species_feat_choices")
        save_builder_to_session(builder)
        return redirect(url_for("species.species_feat_choices"))

    # Check if species has lineages
    if species_data.get("lineages"):
        builder.set_step("lineage")
        save_builder_to_session(builder)
        return redirect(url_for("species.choose_lineage"))
    else:
        return _redirect_to_languages_or_replacement(builder)


@species_bp.route("/species-feat-choices")
def species_feat_choices():
    """Display origin feat choices granted by a species trait (e.g. Human Versatile)."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    feat_choice_data = builder.get_species_feat_choices()

    # Nothing to choose — skip to next step
    if not feat_choice_data["choices"]:
        species_name = builder.to_json().get("species", "")
        species_data = data_loader.species.get(species_name, {})
        if species_data.get("lineages"):
            builder.set_step("lineage")
            save_builder_to_session(builder)
            return redirect(url_for("species.choose_lineage"))
        return _redirect_to_languages_or_replacement(builder)

    character = builder.to_json()
    choices_made = character.get("choices_made", {})

    nav = get_nav_context(builder, "species_feat_choices")
    return render_template(
        "feat_choices.html",
        character=character,
        feat_name=feat_choice_data["feat_name"],
        feat_description=feat_choice_data["feat_description"],
        feat_benefits=feat_choice_data["feat_benefits"],
        choices=feat_choice_data["choices"],
        choices_made=choices_made,
        action_url=url_for("species.submit_species_feat_choices"),
        source_label="Your species grants you",
        **nav,
    )


@species_bp.route("/submit-species-feat-choices", methods=["POST"])
def submit_species_feat_choices():
    """Process origin feat choice submissions from a species trait."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    # Collect feat choices from the form (field names: feat_choice_<choice_name>)
    choices: dict = {}
    for key, values in request.form.lists():
        if key.startswith("feat_choice_"):
            choice_name = key[len("feat_choice_"):]
            choices[choice_name] = values

    if choices:
        feat_name = builder.character_data.get("pending_species_feat")
        builder.apply_feat_choices(choices, feat_name=feat_name)

    # Clear the pending flag now that choices have been applied
    builder.clear_pending_species_feat()

    character = builder.to_json()
    species_name = character.get("species", "")
    species_data = data_loader.species.get(species_name, {})

    log_route_processing("submit_species_feat_choices", choices, builder_before, builder)

    if species_data.get("lineages"):
        builder.set_step("lineage")
        save_builder_to_session(builder)
        return redirect(url_for("species.choose_lineage"))

    return _redirect_to_languages_or_replacement(builder)


@species_bp.route("/choose-lineage")
def choose_lineage():
    """Lineage selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()

    if character.get("step") != "lineage" and not character.get("species"):
        return redirect(url_for("index.index"))

    species_name = character["species"]

    # Get available lineages directly from species data
    species_data = data_loader.species.get(species_name, {})
    lineage_names = species_data.get("lineages", [])

    lineages = {}
    lineage_dir = Path(data_loader.data_dir) / "species_variants"

    for lineage_name in lineage_names:
        # Convert lineage name to filename (replace spaces with underscores, lowercase)
        filename = lineage_name.lower().replace(" ", "_") + ".json"
        lineage_file = lineage_dir / filename

        try:
            if lineage_file.exists():
                with open(lineage_file, "r") as f:
                    lineage_data = json.load(f)
                    lineages[lineage_name] = lineage_data
            else:
                logger.warning(f"Lineage file not found: {filename}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading lineage {lineage_name}: {e}")

    nav = get_nav_context(builder, "lineage")
    return render_template(
        "choose_lineage.html", character=character, lineages=lineages, **nav
    )


@species_bp.route("/select-lineage", methods=["POST"])
def select_lineage():
    """Handle lineage selection."""
    lineage_name = request.form.get("lineage")

    builder_before = get_builder_from_session()
    builder = get_builder_from_session()

    # Collect choices
    choices = {}

    # Apply lineage choice
    if lineage_name:
        builder.apply_choice("lineage", lineage_name)
        choices["lineage"] = lineage_name

    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_lineage", choices, builder_before, builder)

    return _redirect_to_languages_or_replacement(builder)


@species_bp.route("/choose-species-replacement-skills")
def choose_species_replacement_skills():
    """Choose replacement skill profs when species/lineage overlaps with existing skills."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    replacement_info = builder.get_species_skill_replacement_info()
    if not replacement_info["needed"]:
        builder.set_step("languages")
        save_builder_to_session(builder)
        return redirect(url_for("languages.choose_languages"))

    character = builder.to_json()
    nav = get_nav_context(builder, "species_skill_replacement")
    return render_template(
        "choose_species_replacement_skills.html",
        character=character,
        replacement_info=replacement_info,
        **nav,
    )


@species_bp.route("/submit-species-replacement-skills", methods=["POST"])
def submit_species_replacement_skills():
    """Process species replacement skill selection submissions."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    replacement_info = builder.get_species_skill_replacement_info()
    needed = replacement_info["needed"]

    skills = request.form.getlist("replacement_skills")[:needed]

    if len(skills) < needed:
        save_builder_to_session(builder)
        return redirect(url_for("species.choose_species_replacement_skills"))

    builder.apply_species_skill_replacement(skills)
    log_route_processing(
        "submit_species_replacement_skills",
        {"replacement_skills": skills},
        builder_before,
        builder,
    )

    builder.set_step("languages")
    save_builder_to_session(builder)
    return redirect_after_edit_or("languages.choose_languages")
