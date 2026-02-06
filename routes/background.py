"""Background selection routes."""
from flask import Blueprint, render_template, request, redirect, url_for
import logging
from modules.data_loader import DataLoader
from utils.route_helpers import get_builder_from_session, save_builder_to_session, log_route_processing

background_bp = Blueprint('background', __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


@background_bp.route('/choose-background')
def choose_background():
    """Background selection step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    character = builder.to_json()
    # Ensure class is selected before accessing backgrounds
    if not character.get('class'):
        return redirect(url_for('character_creation.choose_class'))
    
    # Update step to background when accessing this page
    builder.set_step('background')
    save_builder_to_session(builder)
    
    backgrounds = dict(sorted(data_loader.backgrounds.items()))
    return render_template('choose_background.html', backgrounds=backgrounds, character=character)


@background_bp.route('/select-background', methods=['POST'])
def select_background():
    """Handle background selection."""
    background_name = request.form.get('background')
    if not background_name or background_name not in data_loader.backgrounds:
        return redirect(url_for('background.choose_background'))
    
    builder_before = get_builder_from_session()
    choices = {'background': background_name}
    
    builder = get_builder_from_session()
    builder.apply_choice('background', background_name)
    builder.set_step('species')
    save_builder_to_session(builder)
    
    # Log route processing
    log_route_processing('select_background', choices, builder_before, builder)
    
    return redirect(url_for('species.choose_species'))
