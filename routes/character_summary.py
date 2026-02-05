"""Character summary and download routes."""
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, send_file, current_app
import json
import io
import logging
from pathlib import Path
from typing import Dict, Any
from modules.character_builder import CharacterBuilder
from modules.data_loader import DataLoader
from modules.character_sheet_converter import CharacterSheetConverter
from utils.pdf_writer import generate_character_sheet_pdf
from utils.route_helpers import get_builder_from_session

character_summary_bp = Blueprint('character_summary', __name__)
data_loader = DataLoader()
character_sheet_converter = CharacterSheetConverter()
logger = logging.getLogger(__name__)


# ==================== Route Handlers ====================

@character_summary_bp.route('/character-summary')
def character_summary():
    """Display final character summary."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != 'complete':
        return redirect(url_for('index.index'))
    
    character = builder.to_json()
    
    # Convert to comprehensive character sheet format
    comprehensive_character = character_sheet_converter.convert_to_character_sheet(character)
    
    # Add max_hp to character object for template compatibility
    character['max_hp'] = comprehensive_character['combat_stats']['hit_point_maximum']
    
    # Gather all spells from various sources using CharacterBuilder
    spells_by_level = builder.get_all_spells()
    
    # Get class name for later use
    class_name = character.get('class')
    
    # Calculate spell slots for spellcasters
    spell_slots = {}
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        if 'spell_slots_by_level' in class_data:
            character_level = character.get('level', 1)
            level_str = str(character_level)
            slots_array = class_data['spell_slots_by_level'].get(level_str, [0]*9)
            
            # Create a dict of spell level -> slot count (only non-zero)
            for spell_level in range(1, 10):
                if spell_level - 1 < len(slots_array) and slots_array[spell_level - 1] > 0:
                    spell_slots[spell_level] = slots_array[spell_level - 1]
    
    # Gather weapon and armor proficiencies
    weapon_proficiencies = []
    armor_proficiencies = []
    
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        weapon_proficiencies = list(class_data.get('weapon_proficiencies', []))
        armor_proficiencies = list(class_data.get('armor_proficiencies', []))
    
    # Add proficiencies from effects
    if 'weapon_proficiencies' in character:
        for prof in character['weapon_proficiencies']:
            if prof not in weapon_proficiencies:
                weapon_proficiencies.append(prof)
    
    if 'armor_proficiencies' in character:
        for prof in character['armor_proficiencies']:
            if prof not in armor_proficiencies:
                armor_proficiencies.append(prof)
    
    # Sort armor proficiencies: Light, Medium, Heavy armor types first, then other items, Shields last
    def sort_armor_proficiencies(profs):
        armor_order = ["Light armor", "Medium armor", "Heavy armor"]
        shields = [p for p in profs if p == "Shields"]
        ordered = [p for p in armor_order if p in profs]
        other = [p for p in profs if p not in armor_order and p != "Shields"]
        return ordered + other + shields
    
    armor_proficiencies = sort_armor_proficiencies(armor_proficiencies)
    
    # Extract calculated data from comprehensive character sheet (avoid recalculation)
    ability_scores_data = comprehensive_character['ability_scores']
    skills_data = comprehensive_character['skills']
    combat_stats = comprehensive_character['combat_stats']
    proficiency_bonus = comprehensive_character['proficiencies']['proficiency_bonus']
    
    # Calculate special ability bonuses (like Thaumaturge's WIS bonus to INT checks)
    # This is data-driven from effects and can't be pre-calculated without character state
    calculated_bonuses = []
    if 'ability_bonuses' in character:
        for bonus_info in character['ability_bonuses']:
            # Calculate the bonus value
            if bonus_info.get('value') == 'wisdom_modifier':
                wis_score = character.get('ability_scores', {}).get('Wisdom', 10)
                wis_modifier = (wis_score - 10) // 2
                bonus_value = max(wis_modifier, bonus_info.get('minimum', 0))
            else:
                bonus_value = bonus_info.get('value', 0)
            
            calculated_bonuses.append({
                'ability': bonus_info.get('ability'),
                'skills': bonus_info.get('skills', []),
                'value': bonus_value,
                'source': bonus_info.get('source')
            })
    
    # Build skill sources map to show where proficiencies come from
    skill_sources = {}
    
    # Get species skill proficiencies from proficiency_sources
    species_skill_sources = character.get('proficiency_sources', {}).get('skills', {})
    for skill, source in species_skill_sources.items():
        skill_sources[skill] = source
    
    # Get class skill choices
    class_skills = character.get('choices_made', {}).get('skill_choices', [])
    for skill in class_skills:
        if isinstance(skill, str):
            skill_sources[skill] = f"{class_name}"
    
    # Get background skills
    background_name = character.get('background')
    if background_name and background_name in data_loader.backgrounds:
        bg_data = data_loader.backgrounds[background_name]
        bg_skills = bg_data.get('skill_proficiencies', [])
        for skill in bg_skills:
            if isinstance(skill, str):
                skill_sources[skill] = f"{background_name}"
    
    # Build skill modifiers from comprehensive_character (avoids recalculation)
    # Format: comprehensive skills data enriched with special bonuses and sources for template
    skill_ability_map = {
        'acrobatics': ('Acrobatics', 'Dexterity'), 'animal_handling': ('Animal Handling', 'Wisdom'),
        'arcana': ('Arcana', 'Intelligence'), 'athletics': ('Athletics', 'Strength'),
        'deception': ('Deception', 'Charisma'), 'history': ('History', 'Intelligence'),
        'insight': ('Insight', 'Wisdom'), 'intimidation': ('Intimidation', 'Charisma'),
        'investigation': ('Investigation', 'Intelligence'), 'medicine': ('Medicine', 'Wisdom'),
        'nature': ('Nature', 'Intelligence'), 'perception': ('Perception', 'Wisdom'),
        'performance': ('Performance', 'Charisma'), 'persuasion': ('Persuasion', 'Charisma'),
        'religion': ('Religion', 'Intelligence'), 'sleight_of_hand': ('Sleight of Hand', 'Dexterity'),
        'stealth': ('Stealth', 'Dexterity'), 'survival': ('Survival', 'Wisdom')
    }
    
    skill_modifiers = []
    for skill_key, (skill_name, ability_name) in skill_ability_map.items():
        skill_info = skills_data.get(skill_key, {})
        ability_info = ability_scores_data.get(ability_name.lower(), {})
        
        ability_score = ability_info.get('score', 10)
        ability_modifier = ability_info.get('modifier', 0)
        is_proficient = skill_info.get('proficient', False)
        is_expertise = skill_info.get('expertise', False)
        
        # Calculate proficiency bonus
        prof_bonus = 0
        if is_expertise:
            prof_bonus = proficiency_bonus * 2
        elif is_proficient:
            prof_bonus = proficiency_bonus
        
        # Check for special bonuses (e.g., Thaumaturge's WIS to INT skills)
        special_bonus = 0
        bonus_source = ''
        for bonus in calculated_bonuses:
            if skill_name in bonus['skills']:
                special_bonus = bonus['value']
                bonus_source = bonus['source']
                break
        
        total_modifier = ability_modifier + prof_bonus + special_bonus
        
        skill_modifiers.append({
            'name': skill_name,
            'ability': ability_name,
            'ability_score': ability_score,
            'ability_modifier': ability_modifier,
            'proficiency_bonus': prof_bonus,
            'is_proficient': is_proficient,
            'proficiency_source': skill_sources.get(skill_name, ''),
            'special_bonus': special_bonus,
            'bonus_source': bonus_source,
            'total_modifier': total_modifier
        })
    
    # Combat stats already calculated in comprehensive_character (no need to recalculate)
    # combat_stats extracted above from comprehensive_character['combat_stats']
    
    # Build saving throw modifiers from comprehensive_character (avoids recalculation)
    # Format: ability_scores data with special effect notes for template
    saving_throws = []
    abilities_order = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
    
    for ability_name in abilities_order:
        ability_info = ability_scores_data.get(ability_name.lower(), {})
        ability_score = ability_info.get('score', 10)
        ability_modifier = ability_info.get('modifier', 0)
        saving_throw = ability_info.get('saving_throw', ability_modifier)
        is_proficient = ability_info.get('saving_throw_proficient', False)
        prof_bonus = (saving_throw - ability_modifier) if is_proficient else 0
        
        # Check for special conditions using effects system (data-driven)
        special_notes = []
        
        # Check effects for grant_save_advantage
        if 'effects' in character:
            for effect in character['effects']:
                if effect.get('type') == 'grant_save_advantage':
                    # Check if this effect applies to current ability
                    affected_abilities = effect.get('abilities', [])
                    if ability_name in affected_abilities:
                        display_text = effect.get('display', 'Advantage')
                        source = effect.get('source', '')
                        if source:
                            special_notes.append(f"{display_text} (from {source})")
                        else:
                            special_notes.append(display_text)
        
        saving_throws.append({
            'ability': ability_name,
            'ability_score': ability_score,
            'ability_modifier': ability_modifier,
            'proficiency_bonus': prof_bonus,
            'is_proficient': is_proficient,
            'total_modifier': saving_throw,
            'special_notes': special_notes
        })
    
    # Store character sheet in session for templates
    session['character_sheet'] = comprehensive_character
    session.modified = True
    
    # Build inventory from equipment selections
    inventory = []
    total_gold = 0
    equipment_selections = character.get('choices_made', {}).get('equipment_selections', {})
    
    # Load equipment databases to identify equippable items
    equipment_dir = Path(__file__).parent.parent / "data" / "equipment"
    weapons = {}
    armor = {}
    gear = {}
    
    try:
        with open(equipment_dir / "weapons.json", 'r') as f:
            weapons = json.load(f)
        with open(equipment_dir / "armor.json", 'r') as f:
            armor = json.load(f)
        with open(equipment_dir / "adventuring_gear.json", 'r') as f:
            gear = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading equipment data: {e}")
    
    if equipment_selections:
        class_choice = equipment_selections.get('class_equipment')
        background_choice = equipment_selections.get('background_equipment')
        
        # Get class equipment
        if class_name and class_name in data_loader.classes:
            class_data = data_loader.classes[class_name]
            class_equipment = class_data.get('starting_equipment', {})
            
            if class_choice == 'option_a' and 'option_a' in class_equipment:
                # Add items from class option A
                for item in class_equipment['option_a'].get('items', []):
                    # Determine item type
                    is_weapon = item in weapons
                    is_armor = item in armor or 'Shield' in item
                    is_gear = item in gear
                    is_equippable = is_weapon or is_armor
                    
                    if is_weapon:
                        item_type = 'weapon'
                    elif is_armor:
                        item_type = 'armor'
                    elif is_gear:
                        item_type = 'gear'
                    else:
                        item_type = 'other'
                    
                    inventory.append({
                        'name': item,
                        'equippable': is_equippable,
                        'type': item_type
                    })
                # Add gold from class option A
                total_gold += class_equipment['option_a'].get('gold', 0)
            elif class_choice == 'option_b' and 'option_b' in class_equipment:
                # Add gold from class option B
                total_gold += class_equipment['option_b'].get('gold', 0)
        
        # Get background equipment
        if background_name and background_name in data_loader.backgrounds:
            bg_data = data_loader.backgrounds[background_name]
            bg_equipment = bg_data.get('starting_equipment', {})
            
            if background_choice == 'option_a' and 'option_a' in bg_equipment:
                # Add items from background option A
                for item in bg_equipment['option_a'].get('items', []):
                    # Determine item type
                    is_weapon = item in weapons
                    is_armor = item in armor or 'Shield' in item
                    is_gear = item in gear
                    is_equippable = is_weapon or is_armor
                    
                    if is_weapon:
                        item_type = 'weapon'
                    elif is_armor:
                        item_type = 'armor'
                    elif is_gear:
                        item_type = 'gear'
                    else:
                        item_type = 'other'
                    
                    inventory.append({
                        'name': item,
                        'equippable': is_equippable,
                        'type': item_type
                    })
                # Add gold from background option A
                total_gold += bg_equipment['option_a'].get('gold', 0)
            elif background_choice == 'option_b' and 'option_b' in bg_equipment:
                # Add gold from background option B
                total_gold += bg_equipment['option_b'].get('gold', 0)
    
    # Sort inventory by type: weapons -> armor -> gear -> other -> currency
    type_order = {'weapon': 1, 'armor': 2, 'gear': 3, 'other': 4, 'currency': 5}
    inventory.sort(key=lambda x: type_order.get(x['type'], 99))
    
    # Add accumulated gold at the end if any
    if total_gold > 0:
        inventory.append({
            'name': f'{total_gold} GP',
            'equippable': False,
            'type': 'currency'
        })
    
    return render_template('character_summary.html', 
                         character=character,
                         character_sheet=comprehensive_character,
                         spells_by_level=spells_by_level,
                         spell_slots=spell_slots,
                         weapon_proficiencies=weapon_proficiencies,
                         armor_proficiencies=armor_proficiencies,
                         ability_bonuses=calculated_bonuses,
                         skill_modifiers=skill_modifiers,
                         saving_throws=saving_throws,
                         combat_stats=combat_stats,
                         inventory=inventory)


@character_summary_bp.route('/download-character')
def download_character():
    """Download character as comprehensive JSON file."""
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    character = builder.to_json()
    
    # Convert to comprehensive character sheet format
    comprehensive_character = character_sheet_converter.convert_to_character_sheet(character)
    
    filename = f"{comprehensive_character['character_info']['character_name'].lower().replace(' ', '_')}_character.json"
    
    response = current_app.response_class(
        response=json.dumps(comprehensive_character, indent=2),
        status=200,
        mimetype='application/json'
    )
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response


@character_summary_bp.route('/api/character-sheet')
def api_character_sheet():
    """Return comprehensive character sheet as JSON API response."""
    builder = get_builder_from_session()
    if not builder:
        return jsonify({"error": "No character in session"}), 400
    
    character = builder.to_json()
    comprehensive_character = character_sheet_converter.convert_to_character_sheet(character)
    
    return jsonify(comprehensive_character)


@character_summary_bp.route('/download-character-pdf')
def download_character_pdf():
    """Download character as filled PDF character sheet."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != 'complete':
        return redirect(url_for('index.index'))
    
    # Get character data
    character = builder.to_json()
    
    # Add calculated values from character_summary
    character_sheet = character_sheet_converter.convert_to_character_sheet(character)
    
    # Extract combat stats
    character['combat_stats'] = character_sheet['combat_stats']
    character['max_hp'] = character_sheet['combat_stats']['hit_point_maximum']
    
    # Extract saving throws from ability_scores
    ability_scores = character_sheet.get('ability_scores', {})
    saving_throws = {}
    for ability, data in ability_scores.items():
        saving_throws[ability.title()] = {
            'modifier': data.get('modifier', 0),
            'proficient': data.get('saving_throw_proficient', False),
            'total': data.get('saving_throw', 0)
        }
    character['saving_throws'] = saving_throws
    
    # Extract skill modifiers from skills
    skills = character_sheet.get('skills', {})
    skill_modifiers = {}
    for skill, data in skills.items():
        skill_name = skill.replace('_', ' ').title()
        skill_modifiers[skill_name] = {
            'modifier': data.get('bonus', 0),
            'proficient': data.get('proficient', False),
            'expertise': data.get('expertise', False),
            'total': data.get('bonus', 0)
        }
    character['skill_modifiers'] = skill_modifiers
    
    # Calculate spell slots
    class_name = character.get('class')
    if class_name and class_name in data_loader.classes:
        class_data = data_loader.classes[class_name]
        if 'spell_slots_by_level' in class_data:
            character_level = character.get('level', 1)
            level_str = str(character_level)
            slots_array = class_data['spell_slots_by_level'].get(level_str, [0]*9)
            
            spell_slots = {}
            for spell_level in range(1, 10):
                if spell_level - 1 < len(slots_array) and slots_array[spell_level - 1] > 0:
                    spell_slots[spell_level] = slots_array[spell_level - 1]
            character['spell_slots'] = spell_slots
    
    # Generate PDF
    pdf_bytes = generate_character_sheet_pdf(character)
    
    # Create filename
    char_name = character.get('name', 'character').replace(' ', '_')
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
    
    # Get character data
    character = builder.to_json()
    
    # Get comprehensive character sheet data (all calculations already done)
    character_sheet_data = character_sheet_converter.convert_to_character_sheet(character)
    
    # Extract ability modifiers (already calculated)
    ability_modifiers = {}
    for ability, data in character_sheet_data.get('ability_scores', {}).items():
        modifier = data.get('modifier', 0)
        # Capitalize ability name to match template expectations (Strength, Dexterity, etc.)
        ability_modifiers[ability.capitalize()] = f"{'+' if modifier >= 0 else ''}{modifier}"
    
    # Extract combat stats (already calculated)
    combat_stats = character_sheet_data['combat_stats']
    
    # Extract saving throws (already calculated)
    ability_scores_data = character_sheet_data.get('ability_scores', {})
    saving_throws = {}
    for ability, data in ability_scores_data.items():
        saving_throws[ability.title()] = {
            'modifier': data.get('modifier', 0),
            'proficient': data.get('saving_throw_proficient', False),
            'total': data.get('saving_throw', 0)
        }
    
    # Extract skill modifiers (already calculated)
    skills_data = character_sheet_data.get('skills', {})
    skill_modifiers = {}
    for skill, data in skills_data.items():
        skill_name = skill.replace('_', ' ').title()
        skill_modifiers[skill_name] = {
            'modifier': data.get('bonus', 0),
            'proficient': data.get('proficient', False),
            'expertise': data.get('expertise', False),
            'total': data.get('bonus', 0)
        }
    
    # Get size from character data (already determined by builder)
    size = character.get('size', 'Medium')
    
    # Get passive perception (already calculated - 10 + perception bonus)
    perception_data = skills_data.get('perception', {})
    passive_perception = 10 + perception_data.get('bonus', 0)
    
    # Get proficiency bonus (already calculated in combat_stats)
    proficiency_bonus = combat_stats.get('proficiency_bonus', 2)
    
    # Extract features (already organized by category)
    features = character_sheet_data.get('features_and_traits', {})
    
    return render_template('character_sheet_pdf.html',
                         character=character,
                         ability_modifiers=ability_modifiers,
                         combat_stats=combat_stats,
                         saving_throws=saving_throws,
                         skill_modifiers=skill_modifiers,
                         size=size,
                         passive_perception=passive_perception,
                         proficiency_bonus=proficiency_bonus,
                         features=features)
