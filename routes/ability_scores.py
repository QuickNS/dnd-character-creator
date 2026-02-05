"""Ability score assignment routes."""
from flask import Blueprint, render_template, request, session, redirect, url_for
import logging
from typing import Dict, Any
from modules.character_builder import CharacterBuilder
from modules.data_loader import DataLoader
from utils.route_helpers import get_builder_from_session, save_builder_to_session, log_route_processing

ability_scores_bp = Blueprint('ability_scores', __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


@ability_scores_bp.route('/assign-ability-scores')
def assign_ability_scores():
    """Ability score assignment step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    character = builder.to_json()
    
    # Allow access if we're at ability_scores step or later
    if character.get('step') not in ['ability_scores', 'background_bonuses', 'complete']:
        return redirect(url_for('index.index'))
    
    class_name = character['class']
    
    # Get class data
    class_data = data_loader.classes.get(class_name, {})
    
    # Use predefined standard_array_assignment from class JSON
    recommended_allocation = class_data.get('standard_array_assignment', {})
    
    standard_array = [15, 14, 13, 12, 10, 8]
    
    # Get primary abilities for display purposes
    primary_ability_data = class_data.get('primary_ability', '')
    if isinstance(primary_ability_data, list):
        primary_abilities = primary_ability_data
    elif isinstance(primary_ability_data, str):
        primary_abilities = primary_ability_data.split(', ') if primary_ability_data else []
    else:
        primary_abilities = []
    
    return render_template('assign_ability_scores.html', 
                         character=character, 
                         primary_abilities=primary_abilities,
                         standard_array=standard_array,
                         recommended_allocation=recommended_allocation)


@ability_scores_bp.route('/submit-ability-scores', methods=['POST'])
def submit_ability_scores():
    """Process ability score assignment."""
    assignment_method = request.form.get('assignment_method')
    
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    
    choices = {'assignment_method': assignment_method}
    
    if assignment_method == 'recommended':
        # Use recommended ability scores for the class
        builder.apply_choice('ability_scores_method', 'recommended')
    else:  # manual
        # Get manual assignments from form
        manual_scores = {}
        for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            score = request.form.get(f'ability_{ability}')
            if score:
                manual_scores[ability] = int(score)
        
        # Apply manual scores
        builder.apply_choice('ability_scores', manual_scores)
        choices['ability_scores'] = manual_scores
        
        # IMPORTANT: Mark that manual method was used to override any previous "recommended" choice
        builder.apply_choice('ability_scores_method', 'manual')
    
    save_builder_to_session(builder)
    
    # Update step to background_bonuses
    builder.set_step('background_bonuses')
    save_builder_to_session(builder)
    
    # Log route processing
    log_route_processing('submit_ability_scores', choices, builder_before, builder)
    
    return redirect(url_for('ability_scores.background_bonuses'))


@ability_scores_bp.route('/background-bonuses')
def background_bonuses():
    """Background ability score bonuses step."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    character = builder.to_json()
    
    # Allow access if we're at background_bonuses step or later
    if character.get('step') not in ['background_bonuses', 'complete']:
        return redirect(url_for('index.index'))
    
    # Get background ASI options from builder (business logic moved to CharacterBuilder)
    asi_options = builder.get_background_asi_options()
    total_points = asi_options['total_points']
    suggested = asi_options['suggested']
    ability_options = asi_options['ability_options']
    
    return render_template('background_bonuses.html', 
                         character=character,
                         total_points=total_points,
                         suggested=suggested,
                         ability_options=ability_options)


@ability_scores_bp.route('/submit-background-bonuses', methods=['POST'])
def submit_background_bonuses():
    """Process background ability score bonuses."""
    assignment_method = request.form.get('assignment_method')
    
    builder_before = get_builder_from_session()
    builder = get_builder_from_session()
    
    choices = {'assignment_method': assignment_method}
    
    if assignment_method == 'suggested':
        # Use suggested background bonuses
        builder.apply_choice('background_bonuses_method', 'suggested')
    else:  # manual
        # Get manual background bonus assignments from form
        manual_bonuses = {}
        for ability in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            bonus = request.form.get(f'bonus_{ability}')
            if bonus and int(bonus) > 0:
                manual_bonuses[ability] = int(bonus)
        
        builder.apply_choice('background_bonuses', manual_bonuses)
        choices['background_bonuses'] = manual_bonuses
    
    save_builder_to_session(builder)
    
    # Next step: equipment selection
    builder.set_step('equipment')
    save_builder_to_session(builder)
    
    # Log route processing
    log_route_processing('submit_background_bonuses', choices, builder_before, builder)
    
    return redirect(url_for('equipment.choose_equipment'))
