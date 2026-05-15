"""Routes package for the D&D Character Creator."""

from flask import Flask
from routes.index import index_bp
from routes.load_character import load_character_bp
from routes.starter_characters import starter_characters_bp
from routes.character_creation import character_creation_bp
from routes.background import background_bp
from routes.species import species_bp
from routes.languages import languages_bp
from routes.ability_scores import ability_scores_bp
from routes.equipment import equipment_bp
from routes.character_summary import character_summary_bp


def register_blueprints(app: Flask):
    """
    Register all blueprint modules with the Flask app.

    Phase 7: legacy Jinja UI is quarantined under `/legacy/*` so the
    React SPA can own root paths (`/`, `/wizard*`, `/sheet*`) while
    the legacy site remains available as a side-by-side comparison
    tool. Both UIs share the same `CharacterBuilder` + Flask session.

    Args:
        app: The Flask application instance
    """
    LEGACY_PREFIX = "/legacy"

    # Legacy Jinja UI — all under /legacy/*
    app.register_blueprint(index_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(load_character_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(starter_characters_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(character_creation_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(background_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(species_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(languages_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(ability_scores_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(equipment_bp, url_prefix=LEGACY_PREFIX)
    app.register_blueprint(character_summary_bp, url_prefix=LEGACY_PREFIX)

    # Register test API endpoints (dev/testing helpers — always available)
    from routes.test_api import test_api_bp
    app.register_blueprint(test_api_bp)

    # Register the v1 REST API used by the React SPA frontend
    from routes.api import api_v1_bp
    app.register_blueprint(api_v1_bp)
