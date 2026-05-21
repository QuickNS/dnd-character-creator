"""Read-only catalog endpoints — game data exposed as JSON.

The frontend uses these to populate selection lists. All responses come
straight from the data files via `DataLoader`; no character state is
involved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, jsonify, abort

from modules.data_loader import DataLoader

catalog_bp = Blueprint("catalog", __name__, url_prefix="/catalog")

_data_loader: DataLoader | None = None
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _dl() -> DataLoader:
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader(data_dir=str(_DATA_DIR))
    return _data_loader


def _summarize(name: str, data: Dict[str, Any], extra_fields: List[str]) -> Dict[str, Any]:
    summary = {"id": name, "name": data.get("name", name)}
    if "description" in data:
        summary["description"] = data["description"]
    for field in extra_fields:
        if field in data:
            summary[field] = data[field]
    return summary


# ==================== Classes ====================


@catalog_bp.get("/classes")
def list_classes():
    classes = _dl().classes
    return jsonify({
        "classes": [
            _summarize(name, data, ["hit_die", "primary_ability", "subclass_selection_level"])
            for name, data in sorted(classes.items())
        ]
    })


@catalog_bp.get("/classes/<class_name>")
def get_class(class_name: str):
    data = _dl().classes.get(class_name)
    if data is None:
        abort(404, description=f"Unknown class: {class_name}")
    return jsonify(data)


@catalog_bp.get("/classes/<class_name>/subclasses")
def list_subclasses(class_name: str):
    if class_name not in _dl().classes:
        abort(404, description=f"Unknown class: {class_name}")
    subclasses = _dl().get_subclasses_for_class(class_name)
    return jsonify({
        "class": class_name,
        "subclasses": [
            _summarize(name, data, [])
            for name, data in sorted(subclasses.items())
        ],
    })


@catalog_bp.get("/classes/<class_name>/subclasses/<subclass_name>")
def get_subclass(class_name: str, subclass_name: str):
    subclasses = _dl().get_subclasses_for_class(class_name)
    data = subclasses.get(subclass_name)
    if data is None:
        abort(404, description=f"Unknown subclass: {subclass_name}")
    return jsonify(data)


# ==================== Species ====================


@catalog_bp.get("/species")
def list_species():
    species = _dl().species
    out = []
    for name, data in sorted(species.items()):
        summary = _summarize(name, data, ["creature_type", "size", "speed", "darkvision"])
        summary["has_lineages"] = bool(data.get("lineages"))
        summary["has_trait_choices"] = any(
            isinstance(t, dict) and t.get("type") == "choice"
            for t in data.get("traits", {}).values()
        )
        out.append(summary)
    return jsonify({"species": out})


@catalog_bp.get("/species/<species_name>")
def get_species(species_name: str):
    data = _dl().species.get(species_name)
    if data is None:
        abort(404, description=f"Unknown species: {species_name}")
    return jsonify(data)


# ==================== Backgrounds ====================


def _extract_background_feat(data: Dict[str, Any]) -> str | None:
    """Return the feat name from a grant_origin_feat effect, or None."""
    for effect in data.get("effects", []):
        if effect.get("type") == "grant_origin_feat":
            return effect.get("feat")
    return None


@catalog_bp.get("/backgrounds")
def list_backgrounds():
    backgrounds = _dl().backgrounds
    items = []
    for name, data in sorted(backgrounds.items()):
        enriched = dict(data)
        if "feat" not in enriched:
            feat = _extract_background_feat(data)
            if feat is not None:
                enriched["feat"] = feat
        items.append(_summarize(name, enriched, ["skill_proficiencies", "ability_scores", "feat"]))
    return jsonify({"backgrounds": items})


@catalog_bp.get("/backgrounds/<background_name>")
def get_background(background_name: str):
    data = _dl().backgrounds.get(background_name)
    if data is None:
        abort(404, description=f"Unknown background: {background_name}")
    enriched = dict(data)
    skill_proficiencies: List[str] = []
    tool_proficiencies: List[str] = []
    for effect in data.get("effects", []):
        etype = effect.get("type")
        if etype == "grant_skill_proficiency":
            skill_proficiencies.extend(effect.get("skills", []))
        elif etype == "grant_tool_proficiency":
            tool_proficiencies.extend(effect.get("tools", []))
    if skill_proficiencies and "skill_proficiencies" not in enriched:
        enriched["skill_proficiencies"] = skill_proficiencies
    if tool_proficiencies and "tool_proficiencies" not in enriched:
        enriched["tool_proficiencies"] = tool_proficiencies
    if "feat" not in enriched:
        feat = _extract_background_feat(data)
        if feat is not None:
            enriched["feat"] = feat
    return jsonify(enriched)


# ==================== Feats ====================


@catalog_bp.get("/feats")
def list_feats():
    from flask import request
    feat_type = request.args.get("type")  # "origin", "general", or None
    feats = _dl().feats
    items = []
    for name, data in sorted(feats.items()):
        category = data.get("category", "general")
        if feat_type and category != feat_type:
            continue
        items.append(_summarize(name, data, ["category", "prerequisites"]))
    return jsonify({"feats": items})


@catalog_bp.get("/feats/<feat_name>")
def get_feat(feat_name: str):
    data = _dl().feats.get(feat_name)
    if data is None:
        abort(404, description=f"Unknown feat: {feat_name}")
    return jsonify(data)


# ==================== Spells ====================


def _load_class_spell_list(class_name: str) -> Dict[str, Any] | None:
    path = _DATA_DIR / "spells" / "class_lists" / f"{class_name.lower()}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)


@catalog_bp.get("/spells/<class_name>")
def list_class_spells(class_name: str):
    """Return the spell list for a class, optionally filtered by level.

    Query: ?level=N (0 = cantrips). Omit to return all.
    """
    from flask import request
    data = _load_class_spell_list(class_name)
    if data is None:
        abort(404, description=f"No spell list for class: {class_name}")
    level_param = request.args.get("level")
    if level_param is None:
        return jsonify(data)
    try:
        level = int(level_param)
    except ValueError:
        abort(400, description="level must be an integer")
    if level == 0:
        return jsonify({"class": data.get("class"), "level": 0, "spells": data.get("cantrips", [])})
    spells = data.get("spells_by_level", {}).get(str(level), [])
    return jsonify({"class": data.get("class"), "level": level, "spells": spells})


@catalog_bp.get("/spells/definitions/<spell_name>")
def get_spell_definition(spell_name: str):
    """Return the full spell definition for a single spell."""
    import re
    safe = re.sub(r"[^a-z0-9_]", "_", spell_name.lower().replace(" ", "_"))
    path = _DATA_DIR / "spells" / "definitions" / f"{safe}.json"
    if not path.exists():
        abort(404, description=f"Unknown spell: {spell_name}")
    with open(path, "r") as f:
        return jsonify(json.load(f))


# ==================== Equipment ====================


@catalog_bp.get("/equipment/<kind>")
def get_equipment(kind: str):
    allowed = {"weapons", "armor", "adventuring_gear", "weapon_masteries"}
    if kind not in allowed:
        abort(404, description=f"Unknown equipment kind: {kind}. Valid: {sorted(allowed)}")
    path = _DATA_DIR / "equipment" / f"{kind}.json"
    if not path.exists():
        abort(404, description=f"Equipment file missing: {kind}.json")
    with open(path, "r") as f:
        return jsonify(json.load(f))


# ==================== Fighting Styles / Invocations / etc. ====================


@catalog_bp.get("/reference/<name>")
def get_reference(name: str):
    """Top-level reference JSON files (fighting_styles, eldritch_invocations, etc.)."""
    allowed = {
        "fighting_styles",
        "eldritch_invocations",
        "origin_feats",
        "general_feats",
        "trait_patterns",
    }
    if name not in allowed:
        abort(404, description=f"Unknown reference: {name}")
    path = _DATA_DIR / f"{name}.json"
    if not path.exists():
        abort(404, description=f"Reference file missing: {name}.json")
    with open(path, "r") as f:
        return jsonify(json.load(f))
