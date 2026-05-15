"""Stateless character build endpoints.

These endpoints take a `choices_made` dict in the request body and return
the calculated character. They never touch the Flask session — the React
frontend is the source of truth for in-progress choices, the Python
`CharacterBuilder` is the source of truth for calculated stats.
"""

from __future__ import annotations

import traceback
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

from modules.character_builder import CharacterBuilder
from modules.derived_stats import (
    build_damage_cantrip_rows,
    build_invocation_management_view,
    build_mastery_management_view,
    build_spell_management_view,
)

character_bp = Blueprint("character", __name__, url_prefix="/character")

_DERIVED_VIEWS = {
    "damage_cantrips",
    "spell_management",
    "mastery_management",
    "invocation_management",
}


def _require_json() -> Dict[str, Any] | None:
    if not request.is_json:
        return None
    return request.get_json(silent=True)


def _build(choices_made: Dict[str, Any]) -> CharacterBuilder:
    builder = CharacterBuilder()
    builder.apply_choices(choices_made)
    return builder


def _enrich_lineages(raw, variant_manager) -> List[Dict[str, Any]]:
    """Normalize lineage data into a uniform list for the SPA.

    Species JSON files store `lineages` either as a list of names
    (`["Drow", "High Elf", ...]`) or as a dict map. Variant detail
    (description, traits) lives in `data/species_variants/`. This
    helper returns a single list of `{id, name, description, traits}`
    so the frontend can render rich lineage cards consistently.
    """
    names: List[str]
    extra: Dict[str, Dict[str, Any]] = {}
    if isinstance(raw, list):
        names = [str(n) for n in raw]
    elif isinstance(raw, dict):
        names = list(raw.keys())
        for n, v in raw.items():
            if isinstance(v, dict):
                extra[n] = v
    else:
        return []

    out: List[Dict[str, Any]] = []
    for name in names:
        variant = variant_manager.get_variant_data(name) or {}
        merged = {
            "id": name,
            "name": variant.get("name", name),
            "description": variant.get("description", ""),
            "traits": variant.get("traits", {}),
        }
        # Per-species inline overrides take precedence over variant file.
        if name in extra:
            merged.update({k: v for k, v in extra[name].items() if v})
        out.append(merged)
    return out


def _subclass_level_feature_names(
    subclass_data: Dict[str, Any],
    level: int = 3,
    limit: int = 3,
) -> List[str]:
    """Return up to `limit` feature names from subclass level data."""
    features_by_level = subclass_data.get("features_by_level")
    if not isinstance(features_by_level, dict):
        return []
    level_data = features_by_level.get(str(level), {})
    if not isinstance(level_data, dict):
        return []
    return [str(name) for name in list(level_data.keys())[:limit]]


# ==================== Build ====================


@character_bp.post("/build")
def build_character():
    """Build a complete character from `choices_made`.

    Request: `{ "choices_made": { ... } }`
    Response: `{ "character": <to_character() output> }`
    """
    body = _require_json()
    if body is None or "choices_made" not in body:
        return jsonify({"error": "Body must be JSON with 'choices_made'"}), 400
    try:
        builder = _build(body["choices_made"])
        return jsonify({"character": builder.to_character()})
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500


# ==================== Validate ====================


# Required choice keys for each logical wizard step. Used by /validate to
# report per-step completion. Optional/conditional keys (subclass, lineage,
# trait choices) are evaluated dynamically against the current build.
_STEP_REQUIRED_KEYS: Dict[str, List[str]] = {
    "basics": ["character_name", "level"],
    "class": ["class"],
    "background": ["background"],
    "species": ["species"],
    "languages": [],  # languages chosen list may be empty if none granted
    "abilities": ["ability_scores"],
    "equipment": [],  # equipment_selections optional
}


def _step_status(builder: CharacterBuilder, step: str) -> Dict[str, Any]:
    character = builder.to_character()
    choices = character.get("choices_made", {}) or {}
    missing: List[str] = []

    for key in _STEP_REQUIRED_KEYS.get(step, []):
        if key not in choices or choices[key] in (None, "", [], {}):
            missing.append(key)

    # Conditional / dynamic checks per step
    if step == "class":
        class_name = choices.get("class")
        level = choices.get("level", 1)
        if class_name:
            class_data = builder.feature_manager.character_data.get("class_data") if hasattr(builder.feature_manager, "character_data") else None
            # Use data_loader directly: subclass required if level >= subclass_selection_level
            from modules.data_loader import DataLoader
            from pathlib import Path
            dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
            cdata = dl.classes.get(class_name, {})
            sub_level = cdata.get("subclass_selection_level", 3)
            if level >= sub_level and not choices.get("subclass"):
                missing.append("subclass")
        # Class feature choices
        try:
            choice_data = builder.get_class_features_and_choices()
            for choice in choice_data.get("choices", []) or []:
                key = choice.get("choice_key") or choice.get("name")
                if key and key not in choices:
                    missing.append(key)
        except Exception:
            pass

    elif step == "species":
        species = choices.get("species")
        if species:
            try:
                trait_choices = builder.get_species_trait_choices()
                for trait_name in trait_choices.keys():
                    if trait_name not in choices:
                        missing.append(trait_name)
            except Exception:
                pass
            # lineage required if species has lineages
            from modules.data_loader import DataLoader
            from pathlib import Path
            dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
            sdata = dl.species.get(species, {})
            if sdata.get("lineages") and not choices.get("lineage"):
                missing.append("lineage")
            # Skill replacement
            try:
                info = builder.get_species_skill_replacement_info()
                if info.get("needed") and not info.get("already_chosen"):
                    missing.append("species_skill_replacement")
            except Exception:
                pass

    elif step == "background":
        if choices.get("background"):
            try:
                info = builder.get_background_skill_replacement_info()
                if info.get("needed", 0) > 0 and not choices.get("background_skill_replacement"):
                    missing.append("background_skill_replacement")
            except Exception:
                pass

    elif step == "abilities":
        # Background ASI bonuses required if applicable
        try:
            asi = builder.get_background_asi_options()
            if asi.get("total_points", 0) > 0 and not choices.get("background_bonuses"):
                missing.append("background_bonuses")
        except Exception:
            pass

    return {"step": step, "complete": len(missing) == 0, "missing": missing}


@character_bp.post("/validate")
def validate_character():
    """Return per-step completion status for a `choices_made` payload."""
    body = _require_json()
    if body is None or "choices_made" not in body:
        return jsonify({"error": "Body must be JSON with 'choices_made'"}), 400
    try:
        builder = _build(body["choices_made"])
        steps = list(_STEP_REQUIRED_KEYS.keys())
        statuses = [_step_status(builder, s) for s in steps]
        return jsonify({
            "complete": all(s["complete"] for s in statuses),
            "steps": statuses,
        })
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500


# ==================== Preview step ====================


@character_bp.post("/preview-step")
def preview_step():
    """Return the dynamic, data-driven options for a given wizard step.

    The React frontend posts the current `choices_made` plus the step it
    is rendering; this endpoint returns the structured nested-choice
    schema that should drive the UI for that step. This is what makes the
    wizard data-driven — adding a new species/class/feature in JSON
    automatically surfaces here without any frontend code change.

    Request: `{ "choices_made": {...}, "step": "class" }`
    Response: `{ "step": "class", "nested_choices": [...], "features": ... }`
    """
    body = _require_json()
    if body is None or "choices_made" not in body or "step" not in body:
        return jsonify({"error": "Body must be JSON with 'choices_made' and 'step'"}), 400

    step = body["step"]
    try:
        builder = _build(body["choices_made"])
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500

    try:
        result: Dict[str, Any] = {"step": step}
        character = builder.to_character()

        if step == "class":
            class_name = character.get("class")
            level = character.get("level", 1)
            if class_name:
                from modules.data_loader import DataLoader
                from pathlib import Path
                dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
                cdata = dl.classes.get(class_name, {})
                sub_level = cdata.get("subclass_selection_level", 3)
                result["needs_subclass"] = level >= sub_level
                if result["needs_subclass"]:
                    result["available_subclasses"] = [
                        {
                            "id": n,
                            "name": d.get("name", n),
                            "description": d.get("description", ""),
                            "level_3_feature_names": _subclass_level_feature_names(d),
                        }
                        for n, d in sorted(dl.get_subclasses_for_class(class_name).items())
                    ]
                feature_data = builder.get_class_features_and_choices()
                result["features_by_level"] = feature_data.get("features_by_level", {})
                result["nested_choices"] = feature_data.get("choices", [])

        elif step == "species":
            species = character.get("species")
            if species:
                from modules.data_loader import DataLoader
                from modules.variant_manager import VariantManager
                from pathlib import Path
                dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
                sdata = dl.species.get(species, {})
                result["traits"] = sdata.get("traits", {})
                result["lineages"] = _enrich_lineages(sdata.get("lineages", {}), VariantManager())
                result["trait_choices"] = builder.get_species_trait_choices()
                result["species_feat_choices"] = builder.get_species_feat_choices()
                result["skill_replacement"] = builder.get_species_skill_replacement_info()

        elif step == "background":
            background = character.get("background")
            if background:
                result["skill_replacement"] = builder.get_background_skill_replacement_info()
                result["origin_feat_choices"] = builder.get_feat_choices()

        elif step == "languages":
            result["language_options"] = builder.get_language_options()

        elif step == "abilities":
            result["background_asi"] = builder.get_background_asi_options()
            class_name = character.get("class", "")
            if class_name:
                from modules.data_loader import DataLoader
                from pathlib import Path
                dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
                cdata = dl.classes.get(class_name, {})
                recommended = cdata.get("standard_array_assignment")
                if isinstance(recommended, dict):
                    result["recommended_array"] = recommended

        elif step == "equipment":
            class_name = character.get("class", "")
            background_name = character.get("background", "")
            from modules.data_loader import DataLoader
            from pathlib import Path
            dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
            result["class_equipment"] = dl.classes.get(class_name, {}).get("starting_equipment", {})
            result["background_equipment"] = dl.backgrounds.get(background_name, {}).get("starting_equipment", {})

        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500


# ==================== Derived views ====================


@character_bp.post("/derived")
def derived_view():
    """Return a derived view-model from `choices_made` for the React SPA.

    Request: `{ "choices_made": {...}, "view": "damage_cantrips" | "spell_management" |
                "mastery_management" | "invocation_management" }`
    Response: `{ "view": "<name>", "data": {...} }`

    Returns 400 on missing/invalid body, unknown view, or when the character
    does not satisfy the view's prerequisite (e.g. invocations on a non-Warlock).
    """
    body = _require_json()
    if body is None or "choices_made" not in body or "view" not in body:
        return jsonify({"error": "Body must be JSON with 'choices_made' and 'view'"}), 400
    view = body["view"]
    if view not in _DERIVED_VIEWS:
        return jsonify({
            "error": f"Unknown view '{view}'",
            "allowed": sorted(_DERIVED_VIEWS),
        }), 400

    try:
        builder = _build(body["choices_made"])
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500

    try:
        if view == "damage_cantrips":
            data = build_damage_cantrip_rows(builder.to_character())
        elif view == "spell_management":
            data = build_spell_management_view(builder)
        elif view == "mastery_management":
            data = build_mastery_management_view(builder)
        else:  # invocation_management
            data = build_invocation_management_view(builder)
        return jsonify({"view": view, "data": data})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500
