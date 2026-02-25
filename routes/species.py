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
)

species_bp = Blueprint("species", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


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
    return render_template("choose_species.html", species=species, character=character)


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
        builder.set_step("languages")
        save_builder_to_session(builder)

        # Log route processing
        log_route_processing("select_species", choices, builder_before, builder)

        return redirect(url_for("languages.choose_languages"))


@species_bp.route("/choose-species-traits")
def choose_species_traits():
    """Species trait choice step (e.g., Keen Senses)."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != "species_traits":
        return redirect(url_for("index.index"))

    character = builder.to_json()

    # Get species trait choices from builder (business logic moved to CharacterBuilder)
    trait_choices = builder.get_species_trait_choices()

    return render_template(
        "choose_species_traits.html", character=character, trait_choices=trait_choices
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

    # Check if species has lineages
    if species_data.get("lineages"):
        builder.set_step("lineage")
        save_builder_to_session(builder)
        return redirect(url_for("species.choose_lineage"))
    else:
        builder.set_step("languages")
        save_builder_to_session(builder)
        return redirect(url_for("languages.choose_languages"))


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

    return render_template(
        "choose_lineage.html", character=character, lineages=lineages
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

    # Update session step
    builder.set_step("languages")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_lineage", choices, builder_before, builder)

    return redirect(url_for("languages.choose_languages"))
