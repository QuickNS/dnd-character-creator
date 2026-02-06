"""Character summary and download routes."""
from flask import Blueprint, render_template, redirect, url_for, jsonify, send_file, current_app
import json
import io
import logging
from modules.data_loader import DataLoader
from utils.route_helpers import get_builder_from_session

character_summary_bp = Blueprint('character_summary', __name__)
data_loader = DataLoader()
logger = logging.getLogger(__name__)


# ==================== Route Handlers ====================

@character_summary_bp.route('/character-summary')
def character_summary():
    """Display final character summary."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != 'complete':
        return redirect(url_for('index.index'))
    
    # Get complete character data with all calculations
    # (ac_options, spells_by_level, and spell_slots are now part of character_data)
    character_data = builder.to_character()
    
    logger.debug(f"Character summary - ability_scores: {character_data.get('ability_scores')}")
    logger.debug(f"Character summary - attacks count: {len(character_data.get('attacks', []))}")
    logger.debug(f"Character summary - skills: {list(character_data.get('skills', {}).keys())}")
    logger.debug(f"Character summary - AC options count: {len(character_data.get('ac_options', []))}")
    logger.debug(f"Character summary - spell levels: {list(character_data.get('spells_by_level', {}).keys())}")
    
    return render_template('character_summary.html', character=character_data)


@character_summary_bp.route('/download-character')
def download_character():
    """Download character data as JSON file."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    # Get complete character data with all calculations
    character_data = builder.to_character()
    
    char_name = character_data.get('name', 'character').lower().replace(' ', '_')
    filename = f"{char_name}_character_data.json"
    
    response = current_app.response_class(
        response=json.dumps(character_data, indent=2),
        status=200,
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@character_summary_bp.route('/api/character-sheet')
def api_character_sheet():
    """Return character data as JSON API response."""
    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400
    
    # Get complete character data with all calculations
    character_data = builder.to_character()
    
    return jsonify(character_data)


@character_summary_bp.route('/download-character-v2')
def download_character_v2():
    """Download character data (same as /download-character for consistency)."""
    # Redirect to main download endpoint for consistency
    return redirect(url_for('character_summary.download_character'))


@character_summary_bp.route('/api/character-sheet-v2')
def api_character_sheet_v2():
    """Return character data (same as /api/character-sheet for consistency)."""
    # Redirect to main API endpoint for consistency
    return redirect(url_for('character_summary.api_character_sheet'))


@character_summary_bp.route('/download-character-pdf')
def download_character_pdf():
    """Download character as filled PDF character sheet."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != 'complete':
        return redirect(url_for('index.index'))
    
    # Get complete character data with all calculations
    character_data = builder.to_character()
    
    # Generate PDF using the complete character data
    pdf_bytes = generate_character_sheet_pdf(character_data)
    
    # Create filename
    char_name = character_data.get('name', 'character').replace(' ', '_')
    filename = f"{char_name}_character_sheet.pdf"
    
    # Return as downloadable file
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@character_summary_bp.route('/character-sheet')
def character_sheet():
    """Display fillable HTML character sheet."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != 'complete':
        return redirect(url_for('index.index'))
    
    # Get complete character data with all calculations
    character_data = builder.to_character()
    
    # Extract ability modifiers from calculated data
    ability_modifiers = {}
    abilities = character_data.get('abilities', {})
    for ability_name, ability_data in abilities.items():
        modifier = ability_data.get('modifier', 0)
        # Capitalize ability name to match template expectations
        ability_modifiers[ability_name.title()] = f"{'+' if modifier >= 0 else ''}{modifier}"
    
    # Extract combat stats
    combat_stats = character_data.get('combat', {})
    
    # Extract saving throws
    saving_throws = {}
    for ability_name, ability_data in abilities.items():
        saving_throws[ability_name.title()] = {
            'modifier': ability_data.get('modifier', 0),
            'proficient': ability_data.get('saving_throw_proficient', False),
            'total': ability_data.get('saving_throw', 0)
        }
    
    # Extract skill modifiers
    skills_data = character_data.get('skills', {})
    skill_modifiers = {}
    for skill, data in skills_data.items():
        skill_name = skill.replace('_', ' ').title()
        skill_modifiers[skill_name] = {
            'modifier': data.get('modifier', 0),
            'proficient': data.get('proficient', False),
            'expertise': data.get('expertise', False),
            'total': data.get('modifier', 0)
        }
    
    # Get size (default to Medium)
    size = character_data.get('size', 'Medium')
    
    # Calculate passive perception
    perception_data = skills_data.get('perception', {})
    passive_perception = 10 + perception_data.get('modifier', 0)
    
    # Get proficiency bonus
    proficiency_bonus = character_data.get('proficiency_bonus', 2)
    
    # Get features
    features = character_data.get('features', {})
    
    return render_template('character_sheet_pdf.html',
                         character=character_data,
                         ability_modifiers=ability_modifiers,
                         combat_stats=combat_stats,
                         saving_throws=saving_throws,
                         skill_modifiers=skill_modifiers,
                         size=size,
                         passive_perception=passive_perception,
                         proficiency_bonus=proficiency_bonus,
                         features=features)
