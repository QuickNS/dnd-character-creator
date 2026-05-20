"""Pure derived-stat / view-model functions.

Phase 2 extraction: these were previously private helpers inside
`routes/character_summary.py`, mixing session state and file I/O with
pure calculation. They are now pure functions over a `CharacterBuilder`
or its `to_character()` output, exposed through the `/api/v1/character/derived`
endpoint.

NEVER import Flask or session state here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Constants (mirror routes/character_summary.py for backward compatibility)
# ---------------------------------------------------------------------------

ORDINAL_TO_INT: Dict[str, int] = {
    "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5,
    "6th": 6, "7th": 7, "8th": 8, "9th": 9,
}

_DAMAGE_DICE_RE = re.compile(r'(\d+d\d+)\s+(\w+)\s+damage', re.IGNORECASE)
_SPELL_ATTACK_RE = re.compile(r'make\s+a\s+(melee|ranged)\s+spell\s+attack', re.IGNORECASE)
_SAVING_THROW_RE = re.compile(r'succeed\s+on\s+an?\s+(\w+)\s+saving\s+throw', re.IGNORECASE)
_SAVE_FAIL_RE = re.compile(r'saving throw or ([^.;]+)', re.IGNORECASE)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SPELL_CLASS_LISTS = _DATA_DIR / "spells" / "class_lists"
_WEAPONS_FILE = _DATA_DIR / "equipment" / "weapons.json"


# ---------------------------------------------------------------------------
# Cantrip damage scaling
# ---------------------------------------------------------------------------

def scale_cantrip_damage(base_dice: str, level: int) -> str:
    """Scale cantrip damage dice by character level (D&D 5e/2024 tiers: 5/11/17)."""
    match = re.match(r'(\d+)d(\d+)', base_dice)
    if not match:
        return base_dice
    base_count = int(match.group(1))
    die = match.group(2)

    if level >= 17:
        multiplier = 4
    elif level >= 11:
        multiplier = 3
    elif level >= 5:
        multiplier = 2
    else:
        multiplier = 1

    return f"{base_count * multiplier}d{die}"


def build_damage_cantrip_rows(character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build damage-cantrip display rows from a `to_character()` output."""
    cantrips = character_data.get("spells_by_level", {}).get(0, []) or []
    spell_stats = character_data.get("spellcasting_stats", {}) or {}
    level = character_data.get("level", 1)
    rows: List[Dict[str, Any]] = []

    for cantrip in cantrips:
        desc = cantrip.get("description", "")
        dmg_match = _DAMAGE_DICE_RE.search(desc)
        if not dmg_match:
            continue

        base_dice = dmg_match.group(1)
        damage_type = dmg_match.group(2).capitalize()
        damage = scale_cantrip_damage(base_dice, level)

        atk_match = _SPELL_ATTACK_RE.search(desc)
        save_match = _SAVING_THROW_RE.search(desc)
        if atk_match:
            bonus = spell_stats.get("spell_attack_bonus", 0)
            atk_display = f"+{bonus}" if bonus >= 0 else str(bonus)
        elif save_match:
            dc = spell_stats.get("spell_save_dc", 0)
            ability = save_match.group(1)[:3].upper()  # "Wisdom" → "WIS"
            atk_display = f"{ability} {dc}"
        else:
            atk_display = ""

        range_text = cantrip.get("range", "").replace(" feet", "ft").replace(" foot", "ft")
        raw_components = cantrip.get("components", [])
        if isinstance(raw_components, str):
            comp_text = raw_components
        else:
            comp_text = ", ".join(c for c in raw_components if c) if raw_components else ""
        notes = f"{range_text} | {comp_text}" if (range_text and comp_text) else (range_text or comp_text)

        rows.append({
            "name": cantrip.get("name", ""),
            "atk_display": atk_display,
            "damage": damage,
            "damage_type": damage_type,
            "notes": notes,
        })

    return rows


# ---------------------------------------------------------------------------
# Spell management view-model
# ---------------------------------------------------------------------------

def _load_class_spell_list(class_name: str) -> Dict[str, Any]:
    if not class_name:
        return {}
    f = _SPELL_CLASS_LISTS / f"{class_name.lower()}.json"
    if not f.exists():
        return {}
    try:
        with open(f, "r") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        return {}


def build_spell_management_view(builder) -> Dict[str, Any]:
    """Return the spell-management modal view as a plain dict.

    Raises `ValueError` if the character is not a spellcaster.
    """
    stats = builder.calculate_spellcasting_stats()
    if not stats or not stats.get("has_spellcasting"):
        raise ValueError("Character is not a spellcaster")

    # Always-prepared
    always_prepared: List[Dict[str, Any]] = []
    spells_block = builder.character_data.get("spells", {}) or {}
    for spell_name, spell_data in (spells_block.get("always_prepared", {}) or {}).items():
        spell_definition = builder._load_spell_definition(spell_name)
        always_prepared.append({
            **spell_definition,
            "name": spell_name,
            "level": spell_data.get("level", spell_definition.get("level", 0)),
            "source": spell_data.get("source", "Unknown"),
            "counts_against_limit": spell_data.get("counts_against_limit", True),
        })

    available_cantrips = [
        builder._load_spell_definition(name)
        for name in stats.get("available_cantrips", []) or []
    ]
    available_spells: Dict[str, List[Dict[str, Any]]] = {}
    for level, spell_names in (stats.get("available_spells", {}) or {}).items():
        available_spells[str(level)] = [
            builder._load_spell_definition(name) for name in spell_names
        ]

    # Filter available spells by levels the character actually has slots for
    character = builder.to_character()
    spell_slots = character.get("spell_slots", {}) or {}
    available_slot_levels = {
        ORDINAL_TO_INT[name]
        for name in spell_slots
        if name in ORDINAL_TO_INT and spell_slots[name] > 0
    }
    if available_slot_levels:
        available_spells = {
            level: spells
            for level, spells in available_spells.items()
            if int(level) in available_slot_levels
        }

    prepared = spells_block.get("prepared", {})
    if isinstance(prepared, list):
        prepared = {"cantrips": {}, "spells": {}}
    current_selections = {
        "cantrips": list(prepared.get("cantrips", {}).keys())
            if isinstance(prepared.get("cantrips", {}), dict) else [],
        "spells": list(prepared.get("spells", {}).keys())
            if isinstance(prepared.get("spells", {}), dict) else [],
        "background_cantrips": [],
        "background_spells": [],
    }

    background_requirements = None
    bg_req = stats.get("background_spell_requirements")
    if bg_req:
        background_requirements = {}
        bg_spells_data = spells_block.get("background_spells", {})

        if bg_req.get("cantrips_needed", 0) > 0:
            bg_class = bg_req.get("cantrip_class", "")
            class_list = _load_class_spell_list(bg_class)
            bg_cantrips = [
                builder._load_spell_definition(name)
                for name in class_list.get("cantrips", []) or []
            ]
            background_requirements["cantrips"] = {
                "count": bg_req["cantrips_needed"],
                "class_name": bg_class,
                "available": bg_cantrips,
            }
            if isinstance(bg_spells_data, dict):
                current_selections["background_cantrips"] = [
                    name for name, data in bg_spells_data.items()
                    if isinstance(data, dict) and data.get("level") == 0
                ]

        if bg_req.get("spells_needed", 0) > 0:
            bg_class = bg_req.get("spell_class", "")
            class_list = _load_class_spell_list(bg_class)
            bg_spell_names = (class_list.get("spells_by_level", {}) or {}).get("1", [])
            bg_spells = [builder._load_spell_definition(name) for name in bg_spell_names]
            background_requirements["spells"] = {
                "count": bg_req["spells_needed"],
                "class_name": bg_class,
                "available": bg_spells,
            }
            if isinstance(bg_spells_data, dict):
                current_selections["background_spells"] = [
                    name for name, data in bg_spells_data.items()
                    if isinstance(data, dict) and data.get("level", 0) > 0
                ]

    return {
        "always_prepared": always_prepared,
        "available_cantrips": available_cantrips,
        "available_spells": available_spells,
        "spell_slots": spell_slots,
        "current_selections": current_selections,
        "limits": {
            "cantrips": stats.get("max_cantrips_to_prepare", 0),
            "spells": stats.get("max_spells_to_prepare", 0),
        },
        "background_requirements": background_requirements,
    }


# ---------------------------------------------------------------------------
# Mastery management view-model
# ---------------------------------------------------------------------------

def build_mastery_management_view(builder) -> Dict[str, Any]:
    """Return the weapon-mastery modal view as a plain dict.

    Raises `ValueError` if the character does not have weapon mastery.
    """
    stats = builder.calculate_weapon_mastery_stats()
    if not stats or not stats.get("has_mastery"):
        raise ValueError("Character does not have weapon mastery")

    weapon_masteries: Dict[str, str] = {}
    if _WEAPONS_FILE.exists():
        try:
            with open(_WEAPONS_FILE, "r") as f:
                weapons_data = json.load(f)
            for weapon_name in stats.get("available_weapons", []) or []:
                if weapon_name in weapons_data:
                    weapon_masteries[weapon_name] = weapons_data[weapon_name].get(
                        "mastery", "Unknown"
                    )
        except (json.JSONDecodeError, IOError):
            pass

    return {
        "available_weapons": stats.get("available_weapons", []),
        "max_masteries": stats.get("max_masteries", 0),
        "current_masteries": stats.get("current_masteries", []),
        "weapon_masteries": weapon_masteries,
    }


# ---------------------------------------------------------------------------
# Eldritch Invocation management view-model
# ---------------------------------------------------------------------------

def build_invocation_management_view(builder) -> Dict[str, Any]:
    """Return the Eldritch Invocation modal view as a plain dict.

    Raises `ValueError` if the character does not have invocations.
    """
    stats = builder.calculate_eldritch_invocation_stats()
    if not stats or not stats.get("has_invocations"):
        raise ValueError("Character does not have Eldritch Invocations")

    return {
        "available_invocations": stats.get("available_invocations", []),
        "max_invocations": stats.get("max_invocations", 0),
        "current_invocations": stats.get("current_invocations", []),
    }
