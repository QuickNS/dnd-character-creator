"""Class and subclass selection routes."""
from flask import Blueprint, render_template, request, session, redirect, url_for, current_app

class_selection_bp = Blueprint('class_selection', __name__)


@class_selection_bp.route('/choose-class')
def choose_class():
    """Class selection step."""
    print(f"Choose class accessed. Session keys: {list(session.keys())}")
    if 'character' not in session:
        print("No character in session, redirecting to index")
        return redirect(url_for('main.index'))
    
    character = session['character']
    print(f"Character found: {character.get('name', 'Unknown')}")
    character_creator = current_app.config['CHARACTER_CREATOR']
    classes = dict(sorted(character_creator.classes.items()))
    return render_template('choose_class.html', classes=classes)


@class_selection_bp.route('/select-class', methods=['POST'])
def select_class():
    """Handle class selection."""
    print(f"Select class accessed. Session keys: {list(session.keys())}")
    character_creator = current_app.config['CHARACTER_CREATOR']
    
    class_name = request.form.get('class')
    if not class_name or class_name not in character_creator.classes:
        print(f"Invalid class selection: {class_name}")
        return redirect(url_for('class_selection.choose_class'))
    
    if 'character' not in session:
        print("No character in session during class selection")
        character = {
            "name": "Character",
            "level": 1,
            "class": "",
            "background": "",
            "species": "",
            "lineage": "",
            "alignment": "",
            "ability_scores": {
                "Strength": 10, "Dexterity": 10, "Constitution": 10,
                "Intelligence": 10, "Wisdom": 10, "Charisma": 10
            },
            "skill_proficiencies": [],
            "languages": ["Common"],
            "equipment": [],
            "features": {
                "class": [],
                "species": [],
                "lineage": [],
                "background": [],
                "feats": []
            },
            "physical_attributes": {
                "creature_type": "Humanoid",
                "size": "Medium",
                "speed": 30,
                "darkvision": 0
            },
            "choices_made": {},
            "step": "class"
        }
    else:
        character = session['character']
    
    character['class'] = class_name
    character['step'] = 'class_choices'
    
    character_level = character.get('level', 1)
    
    if character_level >= 3:
        class_data = character_creator.classes[class_name]
        subclass_level = class_data.get('subclass_selection_level', 3)
        
        if character_level >= subclass_level:
            character['step'] = 'subclass'
            session['character'] = character
            session.modified = True
            print(f"Class selected: {class_name}, redirecting to subclass selection")
            return redirect(url_for('class_selection.choose_subclass'))
    
    session['character'] = character
    session.modified = True
    print(f"Class selected: {class_name}, redirecting to class choices")
    return redirect(url_for('class_features.class_choices'))


@class_selection_bp.route('/choose-subclass')
def choose_subclass():
    """Dedicated subclass selection step."""
    if 'character' not in session or session['character']['step'] != 'subclass':
        return redirect(url_for('main.index'))
    
    character = session['character']
    class_name = character.get('class', '')
    character_creator = current_app.config['CHARACTER_CREATOR']
    
    if not class_name or class_name not in character_creator.classes:
        return redirect(url_for('class_selection.choose_class'))
    
    subclasses = character_creator.get_subclasses_for_class(class_name)
    
    if not subclasses:
        character['step'] = 'class_choices'
        session['character'] = character
        return redirect(url_for('class_features.class_choices'))
    
    return render_template('choose_subclass.html', 
                         subclasses=subclasses, 
                         class_name=class_name,
                         character_level=character.get('level', 1))


@class_selection_bp.route('/select-subclass', methods=['POST'])
def select_subclass():
    """Handle subclass selection and redirect to class choices."""
    if 'character' not in session:
        return redirect(url_for('main.index'))
        
    subclass_name = request.form.get('subclass')
    if not subclass_name:
        return redirect(url_for('class_selection.choose_subclass'))
    
    character = session['character']
    character['subclass'] = subclass_name
    character['step'] = 'class_choices'
    session['character'] = character
    
    print(f"Subclass selected: {subclass_name}, redirecting to class choices")
    return redirect(url_for('class_features.class_choices'))
