"""Starter characters display route."""

from flask import Blueprint, render_template

starter_characters_bp = Blueprint("starter_characters", __name__)


@starter_characters_bp.route("/starter-characters")
def starter_characters():
    """
    Display pre-made starter characters for quick play.
    Shows a gallery of iconic characters, one for each class.
    """
    # Define starter characters with names and descriptions
    starters = [
        {
            "class": "Barbarian",
            "name": "Krag Ironhide",
            "description": "A fierce warrior from the northern wastes who channels primal fury in battle.",
            "image": "barbarian.png",
        },
        {
            "class": "Bard",
            "name": "Lyra Songweaver",
            "description": "A charismatic performer whose music inspires allies and confounds enemies.",
            "image": "bard.png",
        },
        {
            "class": "Cleric",
            "name": "Brother Aldric",
            "description": "A devoted priest of light who heals the wounded and smites the wicked.",
            "image": "cleric.png",
        },
        {
            "class": "Druid",
            "name": "Liara Swiftgazer",
            "description": "A guardian of nature who communes with beasts and wields primal magic.",
            "image": "druid.png",
        },
        {
            "class": "Fighter",
            "name": "Captain Valen Steel",
            "description": "A master of arms and tactics, equally deadly with sword or bow.",
            "image": "fighter.png",
        },
        {
            "class": "Monk",
            "name": "Zen Master Kuai",
            "description": "A martial artist who has achieved perfect harmony of body and mind.",
            "image": "monk.png",
        },
        {
            "class": "Paladin",
            "name": "Lady Brianna Darflame",
            "description": "A holy knight sworn to protect the innocent and vanquish evil.",
            "image": "paladin.png",
        },
        {
            "class": "Ranger",
            "name": "Elara Swiftarrow",
            "description": "A skilled tracker and hunter who protects the borderlands from threats.",
            "image": "ranger.png",
        },
        {
            "class": "Rogue",
            "name": "Shadow",
            "description": "A cunning operative who strikes from the shadows with deadly precision.",
            "image": "rogue.png",
        },
        {
            "class": "Sorcerer",
            "name": "Zephyr Stormborn",
            "description": "Born with innate magic flowing through their veins, raw power incarnate.",
            "image": "sorcerer.png",
        },
        {
            "class": "Warlock",
            "name": "Malakai Hexblade",
            "description": "Bound by a dark pact, wielding eldritch powers from beyond the veil.",
            "image": "warlock.png",
        },
        {
            "class": "Wizard",
            "name": "Archmage Thalion",
            "description": "A scholarly spellcaster who has mastered the arcane arts through study.",
            "image": "wizard.png",
        },
    ]

    return render_template("starter_characters.html", starters=starters)
