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

    Args:
        app: The Flask application instance
    """
    # Register blueprints
    app.register_blueprint(index_bp)
    app.register_blueprint(load_character_bp)
    app.register_blueprint(starter_characters_bp)
    app.register_blueprint(character_creation_bp)
    app.register_blueprint(background_bp)
    app.register_blueprint(species_bp)
    app.register_blueprint(languages_bp)
    app.register_blueprint(ability_scores_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(character_summary_bp)
