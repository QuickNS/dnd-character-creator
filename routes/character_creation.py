"""Character creation routes - class, subclass, and class choices."""

from flask import Blueprint, render_template, request, session, redirect, url_for
import logging
from modules.character_builder import CharacterBuilder
from modules.data_loader import DataLoader
from utils.route_helpers import (
    get_builder_from_session,
    save_builder_to_session,
    log_route_processing,
    get_nav_context,
    redirect_after_edit_or,
    is_editing,
)

character_creation_bp = Blueprint("character_creation", __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================


def _human_join(items: list[str], conjunction: str = "and") -> str:
    """Join list items with proper grammar."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    return ", ".join(items[:-1]) + f", {conjunction} " + items[-1]


# ==================== Route Handlers ====================


@character_creation_bp.route("/create", methods=["GET", "POST"])
def create_character():
    """Start character creation process."""
    alignments = [
        "Unaligned",
        "Lawful Good",
        "Neutral Good",
        "Chaotic Good",
        "Lawful Neutral",
        "True Neutral",
        "Chaotic Neutral",
        "Lawful Evil",
        "Neutral Evil",
        "Chaotic Evil",
    ]

    if request.method == "POST":
        selected_alignment = request.form.get("alignment", "").strip()
        if selected_alignment and selected_alignment not in alignments:
            selected_alignment = ""

        # Capture choices
        choices = {
            "name": request.form.get("name", "Unnamed Character"),
            "level": int(request.form.get("level", 1)),
        }
        if selected_alignment:
            choices["alignment"] = selected_alignment

        # Use CharacterBuilder from the start
        session.clear()  # Clear any existing session data
        builder = CharacterBuilder()

        # Set basic character info
        builder.character_data["name"] = choices["name"]
        builder.character_data["level"] = choices["level"]
        if selected_alignment:
            builder.character_data["alignment"] = selected_alignment

        # Track choices
        builder.character_data["choices_made"]["character_name"] = choices["name"]
        builder.character_data["choices_made"]["level"] = choices["level"]
        if selected_alignment:
            builder.character_data["choices_made"]["alignment"] = selected_alignment

        # Set initial step
        builder.set_step("class")

        # Save to session using builder
        save_builder_to_session(builder)
        session.permanent = True

        # Log route processing
        log_route_processing("create_character", choices, None, builder)

        # Instead of redirect, render the class selection page directly
        classes = dict(sorted(data_loader.classes.items()))
        nav = get_nav_context(builder, "class")
        return render_template(
            "choose_class.html", classes=classes, character_created=True, **nav
        )

    return render_template("create_character.html", alignments=alignments)


@character_creation_bp.route("/choose-class")
def choose_class():
    """Class selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()
    nav = get_nav_context(builder, "class")
    classes = dict(sorted(data_loader.classes.items()))
    return render_template(
        "choose_class.html",
        classes=classes,
        current_level=character.get("level", 1),
        **nav,
    )


@character_creation_bp.route("/select-class", methods=["POST"])
def select_class():
    """Handle class selection."""
    class_name = request.form.get("class")
    if not class_name or class_name not in data_loader.classes:
        return redirect(url_for("character_creation.choose_class"))

    builder_before = get_builder_from_session()
    choices = {"class": class_name}

    builder = get_builder_from_session()

    # Handle level change when editing from summary
    new_level = None
    if is_editing():
        level_str = request.form.get("level")
        if level_str:
            new_level = max(1, min(20, int(level_str)))
            choices["level"] = new_level

    # Apply class (and level if changed) — set_class handles clearing old features
    if new_level is not None:
        builder.set_class(class_name, new_level)
        builder.character_data["choices_made"]["class"] = class_name
        builder.character_data["choices_made"]["level"] = new_level
    else:
        builder.apply_choice("class", class_name)

    builder.set_step("class_choices")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_class", choices, builder_before, builder)

    return redirect(url_for("character_creation.class_choices"))


@character_creation_bp.route("/choose-subclass")
def choose_subclass():
    """Redirect to class-choices (subclass is now embedded there)."""
    return redirect(url_for("character_creation.class_choices"))


@character_creation_bp.route("/select-subclass", methods=["POST"])
def select_subclass():
    """Handle subclass selection and redirect to class choices."""
    subclass_name = request.form.get("subclass")
    if not subclass_name:
        return redirect(url_for("character_creation.class_choices"))

    builder_before = get_builder_from_session()
    choices = {"subclass": subclass_name}

    builder = get_builder_from_session()
    builder.apply_choice("subclass", subclass_name)
    builder.set_step("class_choices")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("select_subclass", choices, builder_before, builder)

    return redirect(url_for("character_creation.class_choices"))


@character_creation_bp.route("/class-choices")
def class_choices():
    """Display all class and subclass features with choices.

    If the character level qualifies for a subclass, the subclass picker
    is embedded at the top of this page (Phase 2 merge).
    """
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for("index.index"))

    character = builder.to_json()
    class_name = character.get("class", "Fighter")
    character_level = character.get("level", 1)
    choices_made = character.get("choices_made", {})

    if class_name not in data_loader.classes:
        return redirect(url_for("character_creation.choose_class"))

    class_data = data_loader.classes[class_name]

    # Subclass selection — embedded in this page (Phase 2)
    subclass_level = class_data.get("subclass_selection_level", 3)
    needs_subclass = character_level >= subclass_level
    subclasses = {}
    current_subclass = character.get("subclass", "")
    if needs_subclass:
        subclasses = data_loader.get_subclasses_for_class(class_name)

    # Use builder to get class features and choices (business logic moved to CharacterBuilder)
    feature_data = builder.get_class_features_and_choices()
    all_features_by_level = feature_data["features_by_level"]
    choices = feature_data["choices"]

    # Build "Core <Class> Traits" table rows
    core_traits: list[dict[str, str]] = []

    primary_ability = class_data.get("primary_ability", "")
    if isinstance(primary_ability, list):
        primary_ability_value = _human_join(primary_ability, conjunction="or")
    else:
        primary_ability_value = str(primary_ability)
    core_traits.append({"label": "Primary Ability", "value": primary_ability_value})

    hit_die = class_data.get("hit_die")
    if hit_die:
        core_traits.append(
            {"label": "Hit Point Die", "value": f"D{hit_die} per {class_name} level"}
        )

    saving_throws = class_data.get("saving_throw_proficiencies", [])
    if saving_throws:
        core_traits.append(
            {
                "label": "Saving Throw Proficiencies",
                "value": _human_join(list(saving_throws), conjunction="and"),
            }
        )

    skill_count = class_data.get("skill_proficiencies_count")
    skill_options = class_data.get("skill_options", [])
    if skill_count and skill_options:
        core_traits.append(
            {
                "label": "Skill Proficiencies",
                "value": f"Choose {skill_count}: {_human_join(list(skill_options), conjunction='or')}",
            }
        )

    tool_count = class_data.get("tool_proficiencies_count")
    tool_options = class_data.get("tool_options", [])
    if tool_count and tool_options:
        core_traits.append(
            {
                "label": "Tool Proficiencies",
                "value": f"Choose {tool_count} from: {_human_join(list(tool_options), conjunction='or')}",
            }
        )

    # Weapon proficiencies: combine base class proficiencies with any from effects
    weapon_proficiencies = list(class_data.get("weapon_proficiencies", []))
    # Add any additional weapon proficiencies from character effects
    if "weapon_proficiencies" in character:
        for prof in character["weapon_proficiencies"]:
            if prof not in weapon_proficiencies:
                weapon_proficiencies.append(prof)

    if weapon_proficiencies:
        weapon_items = list(weapon_proficiencies)
        if all(
            isinstance(w, str) and w.lower().endswith(" weapons") for w in weapon_items
        ):
            categories = [w[:-8] for w in weapon_items]  # strip " weapons"
            core_traits.append(
                {
                    "label": "Weapon Proficiencies",
                    "value": f"{_human_join(categories, conjunction='and')} weapons",
                }
            )
        else:
            core_traits.append(
                {
                    "label": "Weapon Proficiencies",
                    "value": _human_join(weapon_items, conjunction="and"),
                }
            )

    # Armor proficiencies: combine base class proficiencies with any from effects
    armor_proficiencies = list(class_data.get("armor_proficiencies", []))
    # Add any additional armor proficiencies from character effects
    if "armor_proficiencies" in character:
        for prof in character["armor_proficiencies"]:
            if prof not in armor_proficiencies:
                armor_proficiencies.append(prof)

    if armor_proficiencies:
        armor_items = list(armor_proficiencies)
        armor_types = []
        other_armor = []
        for item in armor_items:
            if isinstance(item, str) and item.lower().endswith(" armor"):
                armor_types.append(item[:-6])  # strip " armor"
            else:
                other_armor.append(item)

        armor_order = ["Light", "Medium", "Heavy"]
        ordered_armor_types = [a for a in armor_order if a in armor_types] + [
            a for a in armor_types if a not in armor_order
        ]
        armor_training_parts: list[str] = []
        if ordered_armor_types:
            armor_training_parts.append(
                f"{_human_join(ordered_armor_types, conjunction='and')} armor"
            )
        # Add other armor items (excluding Shields) first
        other_armor_no_shields = [item for item in other_armor if item != "Shields"]
        armor_training_parts.extend(other_armor_no_shields)
        # Always add Shields last if present
        if "Shields" in other_armor:
            armor_training_parts.append("Shields")
        core_traits.append(
            {
                "label": "Armor Training",
                "value": _human_join(armor_training_parts, conjunction="and"),
            }
        )

    nav = get_nav_context(builder, "class_choices")
    return render_template(
        "class_choices.html",
        character=character,
        choices=choices,
        all_features_by_level=all_features_by_level,
        character_level=character_level,
        core_traits=core_traits,
        choices_made=choices_made,
        needs_subclass=needs_subclass,
        subclasses=subclasses,
        current_subclass=current_subclass,
        **nav,
    )


@character_creation_bp.route("/submit-class-choices", methods=["POST"])
def submit_class_choices():
    """Process class choice submissions (including embedded subclass)."""
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()

    # Collect all choices from the form
    choices = {}

    # Process embedded subclass selection (Phase 2)
    subclass = request.form.get("subclass")
    if subclass:
        builder.apply_choice("subclass", subclass)
        choices["subclass"] = subclass

    # Process skill selections
    skills = request.form.getlist("skills")
    if skills:
        choices["skill_choices"] = skills

    # Process tool proficiency selections
    tools = request.form.getlist("tools")
    if tools:
        choices["tool_choices"] = tools

    # Process feature choices
    for key, values in request.form.lists():
        if key.startswith("choice_"):
            choice_name = key.replace("choice_", "")
            choices[choice_name] = values[0] if len(values) == 1 else values

    # Apply all choices at once (subclass already applied above for ordering)
    remaining = {k: v for k, v in choices.items() if k != "subclass"}
    if remaining:
        builder.apply_choices(remaining)

    builder.set_step("background")
    save_builder_to_session(builder)

    # Log route processing
    log_route_processing("submit_class_choices", choices, builder_before, builder)

    return redirect_after_edit_or("background.choose_background")
