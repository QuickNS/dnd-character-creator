"""Shared helper functions for route modules.

This module provides common functionality used across all route blueprints,
including session management and logging utilities.
"""

import logging
from typing import Optional, Dict, Any
from flask import session
from modules.character_builder import CharacterBuilder

logger = logging.getLogger(__name__)


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


def log_route_processing(
    route_name: str,
    choices_made: Dict[str, Any],
    builder_before: Optional[CharacterBuilder],
    builder_after: Optional[CharacterBuilder],
):
    """
    Log route processing with choices made and builder changes.

    Args:
        route_name: Name of the route being processed
        choices_made: Dictionary of choices made in this route
        builder_before: Builder state before processing (unused but kept for compatibility)
        builder_after: Builder state after processing (unused but kept for compatibility)
    """
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

    logger.info(f"{'=' * 80}\n")
