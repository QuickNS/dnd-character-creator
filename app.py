"""
D&D 2024 Character Creator - Main Application
Flask web application for creating D&D 2024 characters.

All routes are organized into blueprint modules in the routes/ directory.
"""

from flask import Flask, session
from flask_session import Session
import logging
from datetime import timedelta
from typing import Dict, Any, Optional
from routes import register_blueprints

from modules.data_loader import DataLoader
from modules.character_builder import CharacterBuilder

# ==================== Logging Configuration ====================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("character_creator.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ==================== Flask App Initialization ====================

app = Flask(__name__)
app.secret_key = "dnd-character-creator-secret-key-2024"  # Change this in production

# Configure server-side sessions (filesystem)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize Flask-Session
Session(app)

# Initialize data loaders (available to all blueprints)
app.data_loader = DataLoader()

# ==================== Logging Helper Functions ====================


def log_route_processing(
    route_name: str,
    choices_made: Dict[str, Any],
    builder_before: Optional[CharacterBuilder],
    builder_after: Optional[CharacterBuilder],
):
    """Log route processing with choices made and builder changes."""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Route: {route_name}")
    logger.info(f"{'=' * 80}")

    # Log choices made in this route
    if choices_made:
        logger.info("Choices made:")
        for key, value in choices_made.items():
            if isinstance(value, list):
                logger.info(f"  {key}: [{', '.join(str(v) for v in value)}]")
            else:
                logger.info(f"  {key}: {value}")
    else:
        logger.info("No choices made in this route")

    # Log builder state changes
    if builder_before and builder_after:
        log_builder_changes(builder_before, builder_after)
    elif builder_after:
        logger.info("\nBuilder created (new session)")
        log_builder_state(builder_after)

    logger.info(f"{'=' * 80}\n")


def log_builder_changes(before: CharacterBuilder, after: CharacterBuilder):
    """Log changes between two builder states."""
    before_data = before.to_json()
    after_data = after.to_json()

    changes = []

    # Check for changes in main fields
    for key in [
        "name",
        "class",
        "subclass",
        "species",
        "lineage",
        "background",
        "level",
        "step",
    ]:
        before_val = before_data.get(key)
        after_val = after_data.get(key)
        if before_val != after_val:
            changes.append(f"  {key}: {before_val} → {after_val}")

    # Check ability scores
    before_abilities = before_data.get("ability_scores", {})
    after_abilities = after_data.get("ability_scores", {})
    if before_abilities != after_abilities:
        changes.append(f"  ability_scores: {before_abilities} → {after_abilities}")

    # Check proficiencies
    before_skills = set(before_data.get("skill_proficiencies", []))
    after_skills = set(after_data.get("skill_proficiencies", []))
    new_skills = after_skills - before_skills
    if new_skills:
        changes.append(f"  +skill_proficiencies: {list(new_skills)}")

    # Check effects
    before_effects_count = len(before_data.get("effects", []))
    after_effects_count = len(after_data.get("effects", []))
    if before_effects_count != after_effects_count:
        new_effects = after_effects_count - before_effects_count
        changes.append(
            f"  effects: {before_effects_count} → {after_effects_count} (+{new_effects})"
        )
        # Log new effects
        if new_effects > 0:
            recent_effects = after_data.get("effects", [])[-new_effects:]
            for effect in recent_effects:
                effect_type = effect.get("type", "unknown")
                effect_source = effect.get("source", "unknown")
                changes.append(f"    - {effect_type} from {effect_source}")

    # Check spells
    before_prepared = set(before_data.get("spells", {}).get("prepared", []))
    after_prepared = set(after_data.get("spells", {}).get("prepared", []))
    new_prepared = after_prepared - before_prepared
    if new_prepared:
        changes.append(f"  +spells.prepared: {list(new_prepared)}")

    # Check languages
    before_langs = set(before_data.get("languages", []))
    after_langs = set(after_data.get("languages", []))
    new_langs = after_langs - before_langs
    if new_langs:
        changes.append(f"  +languages: {list(new_langs)}")

    # Check choices_made
    before_choices = before_data.get("choices_made", {})
    after_choices = after_data.get("choices_made", {})
    for key in after_choices:
        if key not in before_choices or before_choices[key] != after_choices[key]:
            changes.append(f"  choices_made.{key}: {after_choices[key]}")

    if changes:
        logger.info("\nBuilder changes:")
        for change in changes:
            logger.info(change)
    else:
        logger.info("\nNo builder changes detected")


def log_builder_state(builder: CharacterBuilder):
    """Log current builder state summary."""
    data = builder.to_json()
    logger.info("Current builder state:")
    logger.info(f"  Name: {data.get('name', 'N/A')}")
    logger.info(f"  Class: {data.get('class', 'N/A')} (Level {data.get('level', 1)})")
    logger.info(f"  Subclass: {data.get('subclass', 'N/A')}")
    logger.info(f"  Species: {data.get('species', 'N/A')}")
    logger.info(f"  Lineage: {data.get('lineage', 'N/A')}")
    logger.info(f"  Background: {data.get('background', 'N/A')}")
    logger.info(f"  Step: {data.get('step', 'N/A')}")
    logger.info(f"  Effects: {len(data.get('effects', []))}")
    logger.info(f"  Skill Proficiencies: {len(data.get('skill_proficiencies', []))}")
    logger.info(f"  Languages: {len(data.get('languages', []))}")


# Make logging helpers available to blueprints
app.log_route_processing = log_route_processing
app.log_builder_changes = log_builder_changes
app.log_builder_state = log_builder_state

# ==================== Session Helper Functions ====================


def get_builder_from_session() -> Optional[CharacterBuilder]:
    """
    Get CharacterBuilder from session.

    Returns:
        CharacterBuilder if found in session, None otherwise
    """
    if "builder_state" not in session:
        return None

    builder = CharacterBuilder()
    builder.from_json(session["builder_state"])
    return builder


def save_builder_to_session(builder: CharacterBuilder):
    """
    Save CharacterBuilder state to session.

    Args:
        builder: The CharacterBuilder instance to save
    """
    session["builder_state"] = builder.to_json()
    session.modified = True


# Make session helpers available to blueprints
app.get_builder_from_session = get_builder_from_session
app.save_builder_to_session = save_builder_to_session

# ==================== Legacy Helper Functions ====================


def _extract_hp_bonuses_from_character(character):
    """Extract HP bonuses from character effects using the effects system."""
    hp_bonuses = []

    # Check effects array for bonus_hp effects
    effects = character.get("effects", [])
    for effect in effects:
        if isinstance(effect, dict) and effect.get("type") == "bonus_hp":
            hp_bonuses.append(
                {
                    "source": effect.get("source", "Unknown"),
                    "value": effect.get("value", 0),
                    "scaling": effect.get("scaling", "flat"),
                }
            )

    return hp_bonuses


# Make helper functions available to blueprints
app._extract_hp_bonuses_from_character = _extract_hp_bonuses_from_character

# ==================== Blueprint Registration ====================

try:
    register_blueprints(app)
    logger.info("All blueprints registered successfully")
except Exception as e:
    logger.error(f"Error registering blueprints: {e}")
    raise

# ==================== Application Entry Point ====================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
