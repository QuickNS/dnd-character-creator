"""Main routes for the D&D Character Creator."""
from flask import Blueprint, render_template, request, session, redirect, url_for

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Main landing page for character creation."""
    return render_template('index.html')


@main_bp.route('/create', methods=['GET', 'POST'])
def create_character():
    """Start character creation process."""
    from modules.character_creator import CharacterCreator
    character_creator = CharacterCreator()
    
    if request.method == 'POST':
        # Initialize character data
        character_data = {
            "name": request.form.get('name', 'Unnamed Character'),
            "level": int(request.form.get('level', 1)),
            "class": "",
            "background": "",
            "species": "",
            "lineage": "",
            "alignment": "",
            "ability_scores": {
                "Strength": 10,
                "Dexterity": 10, 
                "Constitution": 10,
                "Intelligence": 10,
                "Wisdom": 10,
                "Charisma": 10
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
        
        session.clear()  # Clear any existing session data
        session['character'] = character_data
        session.permanent = True
        session.modified = True
        
        print(f"Session created with character: {character_data['name']}")
        print(f"Session after save: {dict(session)}")
        
        # Instead of redirect, render the class selection page directly
        classes = dict(sorted(character_creator.classes.items()))
        return render_template('choose_class.html', classes=classes, character_created=True)
    
    return render_template('create_character.html')


@main_bp.route('/reset')
def reset():
    """Reset session data."""
    session.clear()
    return redirect(url_for('main.index'))


@main_bp.route('/test-session')
def test_session():
    """Debug route to check session data."""
    return {"session_keys": list(session.keys()), "character": session.get('character')}
