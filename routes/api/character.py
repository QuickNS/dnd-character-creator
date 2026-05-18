"""Stateless character build endpoints.

These endpoints take a `choices_made` dict in the request body and return
the calculated character. They never touch the Flask session — the React
frontend is the source of truth for in-progress choices, the Python
`CharacterBuilder` is the source of truth for calculated stats.
"""

from __future__ import annotations

import re
import traceback
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

from modules.ability_scores import validate_point_buy
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


class ChoicesValidationError(ValueError):
    """Raised when API request choices are structurally invalid."""


# ==================== Multiclass nested-choice filtering ====================
#
# Per D&D 2024 multiclassing rules, a secondary class entry grants ONLY the
# proficiencies listed in that class's `multiclassing` block — it does NOT
# grant the class's level-1 features (no fighting style, no expertise, no
# divine/primal order, no level-1 spells/cantrips, no weapon mastery picks,
# no invocations, etc.). The wizard's level-up step pipeline naively produces
# every nested choice the class would offer at level 1, so for secondary
# rows we filter that list down to only:
#   - skill picks (if `multiclassing.skill_proficiencies` is a non-null dict)
#   - tool picks  (if any `multiclassing.tool_training` entry is a wildcard
#                  like "Musical Instrument (1 of your choice)")
# Subclass selection is handled by `available_subclasses` / `needs_subclass`
# on the response and is always allowed for any class row.


def _classify_choice_for_multiclass(choice: Dict[str, Any]) -> str:
    """Classify a nested_choice as 'skill', 'tool', or 'other'.

    Inspects the structured `type` field first (set by CharacterBuilder for
    level-1 proficiency pickers), then falls back to keywords in
    `choice_key` / `feature_name` / `title`. Branching is intentionally
    generic — never on specific class or feature names.
    """
    ctype = (choice.get("type") or "").lower()
    if ctype == "skills":
        return "skill"
    if ctype == "tools":
        return "tool"
    key = " ".join(
        str(choice.get(k) or "")
        for k in ("choice_key", "feature_name", "title")
    ).lower()
    if "skill" in key:
        return "skill"
    if "tool" in key or "instrument" in key:
        return "tool"
    return "other"


def _parse_tool_wildcard(tool_training: List[Any]) -> Dict[str, Any] | None:
    """Return {count, label} for the first wildcard entry, or None.

    Wildcard form: "<Category> (<N> of your choice)" or any entry containing
    "of your choice" (case-insensitive). Concrete grants like "Thieves' Tools"
    are NOT wildcards and produce no picker.
    """
    for entry in tool_training or []:
        if not isinstance(entry, str) or "of your choice" not in entry.lower():
            continue
        count = 1
        m = re.search(r"\((\d+)\s+of your choice\)", entry, re.IGNORECASE)
        if m:
            count = int(m.group(1))
        label = re.sub(r"\s*\(.*?\)\s*$", "", entry).strip() or entry
        return {"count": count, "label": label}
    return None


def _filter_nested_choices_for_secondary_class(
    nested_choices: List[Dict[str, Any]],
    class_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Drop everything except the proficiency picks the multiclass block allows.

    For surviving skill/tool pickers, narrow count and options to match the
    multiclass entry (e.g. Rogue multiclass = 1 skill from a constrained list).
    """
    multiclass = class_data.get("multiclassing") or {}

    skill_block = multiclass.get("skill_proficiencies")
    allow_skill = isinstance(skill_block, dict)

    tool_wildcard = _parse_tool_wildcard(multiclass.get("tool_training") or [])
    allow_tool = tool_wildcard is not None

    filtered: List[Dict[str, Any]] = []
    for choice in nested_choices:
        kind = _classify_choice_for_multiclass(choice)

        if kind == "skill" and allow_skill:
            narrowed = dict(choice)
            mc_options = skill_block.get("options")
            # "any" (Bard) → keep the existing full-skill list the builder
            # already expanded. A constrained list (Rogue, Ranger) → use the
            # multiclass list directly as the authoritative set; do NOT
            # intersect with the primary class's skill_options, which may be
            # narrower than the multiclass-entry list per RAW.
            if isinstance(mc_options, list) and mc_options:
                narrowed["options"] = list(mc_options)
            mc_count = skill_block.get("count")
            if isinstance(mc_count, int) and mc_count > 0:
                narrowed["count"] = mc_count
                noun = "proficiency" if mc_count == 1 else "proficiencies"
                narrowed["description"] = (
                    f"Choose {mc_count} skill {noun} (multiclass)."
                )
            filtered.append(narrowed)

        elif kind == "tool" and allow_tool:
            narrowed = dict(choice)
            narrowed["count"] = tool_wildcard["count"]
            # The primary class's tool_options usually already enumerates the
            # category (e.g. Bard's instrument list). If empty, fall back to
            # the label as a single non-selectable entry.
            if not narrowed.get("options"):
                narrowed["options"] = [tool_wildcard["label"]]
                # TODO: enumerate the category from a shared data source once
                # one exists for tool categories beyond Musical Instrument.
                narrowed["_todo"] = (
                    "Multiclass tool picker has no options list; using label fallback."
                )
            filtered.append(narrowed)

        # All other categories (fighting style, expertise, spells, cantrips,
        # divine/primal order, weapon mastery, invocations, etc.) are dropped.

    return filtered


def _resolve_class_row_context(
    request_choices: Dict[str, Any],
    previewed_class: str | None,
) -> Dict[str, Any]:
    """Determine which row of choices_made.classes is being previewed.

    Resolution rules:
      - No `classes` array (legacy single-class) → row_index 0, primary.
      - Otherwise: find the first row whose class_name matches the previewed
        class. If multiple rows share the class name (rare; e.g. someone
        previewing a duplicate), the first match wins. The request currently
        has no row-index hint — Phase 2 will likely add one; until then,
        first-match is the documented resolution.
    """
    classes = request_choices.get("classes")
    if not isinstance(classes, list) or not classes:
        return {"row_index": 0, "is_primary": True, "total_class_rows": 1}

    total = len(classes)
    row_index = 0
    if previewed_class:
        target = previewed_class.strip().lower()
        for idx, row in enumerate(classes):
            if not isinstance(row, dict):
                continue
            name = row.get("class_name")
            if isinstance(name, str) and name.strip().lower() == target:
                row_index = idx
                break
    return {
        "row_index": row_index,
        "is_primary": row_index == 0,
        "total_class_rows": total,
    }


def _require_json() -> Dict[str, Any] | None:
    if not request.is_json:
        return None
    return request.get_json(silent=True)


def _coerce_level(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ChoicesValidationError(f"'{field_name}' must be an integer")
    try:
        level = int(value)
    except (TypeError, ValueError) as exc:
        raise ChoicesValidationError(f"'{field_name}' must be an integer") from exc
    if level < 1:
        raise ChoicesValidationError(f"'{field_name}' must be at least 1")
    return level


def _normalize_class_entries(classes: Any, field_name: str = "choices_made.classes") -> List[Dict[str, Any]]:
    """Validate and normalize classes payload entries."""
    if not isinstance(classes, list):
        raise ChoicesValidationError(f"'{field_name}' must be an array")
    if len(classes) == 0:
        raise ChoicesValidationError(f"'{field_name}' must contain at least one class entry")

    normalized_entries: List[Dict[str, Any]] = []
    for idx, class_entry in enumerate(classes):
        entry_path = f"{field_name}[{idx}]"
        if not isinstance(class_entry, dict):
            raise ChoicesValidationError(f"'{entry_path}' must be an object")

        class_name = class_entry.get("class_name")
        if not isinstance(class_name, str) or not class_name.strip():
            raise ChoicesValidationError(f"'{entry_path}.class_name' must be a non-empty string")

        level = _coerce_level(class_entry.get("level"), f"{entry_path}.level")
        normalized_entry: Dict[str, Any] = {
            "class_name": class_name.strip(),
            "level": level,
        }

        subclass = class_entry.get("subclass")
        if subclass is not None:
            if not isinstance(subclass, str):
                raise ChoicesValidationError(f"'{entry_path}.subclass' must be a string when provided")
            if subclass.strip():
                normalized_entry["subclass"] = subclass.strip()

        normalized_entries.append(normalized_entry)

    return normalized_entries


def _normalize_choices_for_builder(
    choices_made: Dict[str, Any],
    *,
    preserve_explicit_class_context: bool = False,
) -> Dict[str, Any]:
    """Normalize legacy/new class payload shapes into canonical class structures."""
    if not isinstance(choices_made, dict):
        raise ChoicesValidationError("'choices_made' must be a JSON object")

    normalized = dict(choices_made)

    # Normalise singular API key → plural internal key expected by CharacterBuilder.
    if "background_skill_replacement" in normalized and "background_skill_replacements" not in normalized:
        normalized["background_skill_replacements"] = normalized.pop("background_skill_replacement")

    classes = normalized.get("classes")
    if classes is None:
        # Legacy compatibility: class/level(/subclass) remains supported.
        class_name = normalized.get("class")
        if isinstance(class_name, str) and class_name.strip():
            level = _coerce_level(normalized.get("level", 1), "choices_made.level")
            class_entry: Dict[str, Any] = {
                "class_name": class_name.strip(),
                "level": level,
            }
            subclass = normalized.get("subclass")
            if isinstance(subclass, str) and subclass.strip():
                class_entry["subclass"] = subclass.strip()
            normalized["classes"] = [class_entry]
            normalized["class"] = class_entry["class_name"]
            normalized["level"] = level
        return normalized

    class_entries = _normalize_class_entries(classes)
    normalized["classes"] = class_entries

    explicit_class = normalized.get("class")
    if (
        preserve_explicit_class_context
        and isinstance(explicit_class, str)
        and explicit_class.strip()
    ):
        normalized["class"] = explicit_class.strip()
        normalized["level"] = _coerce_level(
            normalized.get("level", 1), "choices_made.level"
        )
        class_entry: Dict[str, Any] = {
            "class_name": normalized["class"],
            "level": normalized["level"],
        }
        explicit_subclass = normalized.get("subclass")
        if isinstance(explicit_subclass, str) and explicit_subclass.strip():
            normalized["subclass"] = explicit_subclass.strip()
            class_entry["subclass"] = normalized["subclass"]
        else:
            normalized.pop("subclass", None)
        normalized["classes"] = [class_entry]
        return normalized

    primary = class_entries[0]
    normalized["class"] = primary["class_name"]
    normalized["level"] = sum(entry["level"] for entry in class_entries)
    if primary.get("subclass"):
        normalized["subclass"] = primary["subclass"]
    else:
        normalized.pop("subclass", None)

    return normalized


def _build(
    choices_made: Dict[str, Any],
    *,
    preserve_explicit_class_context: bool = False,
) -> CharacterBuilder:
    builder = CharacterBuilder()
    normalized_choices = _normalize_choices_for_builder(
        choices_made,
        preserve_explicit_class_context=preserve_explicit_class_context,
    )
    builder.apply_choices(normalized_choices)
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
        builder = _build(body["choices_made"], preserve_explicit_class_context=True)
        return jsonify({"character": builder.to_character()})
    except ChoicesValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500


# ==================== Validate ====================


# Required choice keys for each logical wizard step. Used by /validate to
# report per-step completion. Optional/conditional keys (subclass, lineage,
# trait choices) are evaluated dynamically against the current build.
_STEP_REQUIRED_KEYS: Dict[str, List[str]] = {
    "class": ["class"],
    "background": ["background"],
    "species": ["species"],
    "languages": [],
    "abilities": ["ability_scores"],
    "equipment": [],  # equipment_selections optional
    "complete": [],
}


def _step_status(builder: CharacterBuilder, step: str) -> Dict[str, Any]:
    character = builder.to_character()
    choices = character.get("choices_made", {}) or {}
    missing: List[str] = []

    for key in _STEP_REQUIRED_KEYS.get(step, []):
        if key == "class":
            has_legacy_class = bool(choices.get("class"))
            classes = choices.get("classes")
            has_classes = isinstance(classes, list) and len(classes) > 0
            if not has_legacy_class and not has_classes:
                missing.append("class")
            continue

        if key not in choices or choices[key] in (None, "", [], {}):
            missing.append(key)

    # Conditional / dynamic checks per step
    if step == "class":
        from modules.data_loader import DataLoader
        from pathlib import Path

        dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))

        class_rows = choices.get("classes")
        if isinstance(class_rows, list) and class_rows:
            for idx, row in enumerate(class_rows):
                if not isinstance(row, dict):
                    continue
                class_name = row.get("class_name")
                if not class_name:
                    continue
                try:
                    class_level = int(row.get("level", 1))
                except (TypeError, ValueError):
                    class_level = 1
                cdata = dl.classes.get(class_name, {})
                sub_level = cdata.get("subclass_selection_level", 3)
                if class_level >= sub_level and not row.get("subclass"):
                    missing.append(f"classes[{idx}].subclass")
        else:
            class_name = choices.get("class")
            level = choices.get("level", 1)
            if class_name:
                cdata = dl.classes.get(class_name, {})
                sub_level = cdata.get("subclass_selection_level", 3)
                if level >= sub_level and not choices.get("subclass"):
                    missing.append("subclass")
        # Class feature choices
        try:
            choice_data = builder.get_class_features_and_choices()
            for choice in choice_data.get("choices", []) or []:
                # Mirror the key resolution the frontend uses:
                # choice.choice_key ?? choice.feature_name ?? choice.name
                key = choice.get("choice_key") or choice.get("feature_name") or choice.get("name")
                if not key:
                    continue
                # Skip conditional choices whose parent condition isn't met yet.
                # Try multiple key variants (snake_case, Title Case) to match how
                # the frontend stores parent choices, mirroring parentKeyVariants().
                depends_on = choice.get("depends_on")
                if depends_on:
                    snake = depends_on.lower().replace(" ", "_").replace("-", "_")
                    title = " ".join(w.capitalize() for w in snake.split("_"))
                    parent_val = next(
                        (choices[k] for k in (depends_on, snake, title) if k in choices),
                        None,
                    )
                    depends_on_value = choice.get("depends_on_value")
                    if depends_on_value is not None:
                        matches = (
                            depends_on_value in parent_val
                            if isinstance(parent_val, list)
                            else parent_val == depends_on_value
                        )
                    else:
                        matches = bool(parent_val)
                    if not matches:
                        continue
                val = choices.get(key)
                required_count = choice.get("count", 1)
                if val is None:
                    missing.append(key)
                elif isinstance(val, list) and len(val) < required_count:
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
        method = choices.get("ability_scores_method")
        scores = choices.get("ability_scores")
        abilities = [
            "Strength",
            "Dexterity",
            "Constitution",
            "Intelligence",
            "Wisdom",
            "Charisma",
        ]

        if method == "standard_array":
            standard_array = [15, 14, 13, 12, 10, 8]
            valid_standard_array = False
            if isinstance(scores, dict) and all(a in scores for a in abilities):
                try:
                    selected = [int(scores.get(a, 0)) for a in abilities]
                    valid_standard_array = sorted(selected) == sorted(standard_array)
                except (TypeError, ValueError):
                    valid_standard_array = False
            if not valid_standard_array:
                missing.append("ability_scores")
        elif method == "point_buy":
            if not isinstance(scores, dict):
                missing.append("ability_scores")
            else:
                is_valid, _ = validate_point_buy(scores)
                if not is_valid:
                    missing.append("ability_scores")

        # Background ASI bonuses required if applicable
        try:
            asi = builder.get_background_asi_options()
            if asi.get("total_points", 0) > 0 and not choices.get("background_bonuses"):
                missing.append("background_bonuses")
        except Exception:
            pass
    elif step == "languages":
        try:
            language_options = builder.get_language_options()
            required_count = language_options.get("selection_count", 2)
            available_languages = set(language_options.get("available_languages", []))
            selected = choices.get("languages", [])
            if not isinstance(selected, list):
                selected = []

            normalized = []
            for lang in selected:
                if (
                    isinstance(lang, str)
                    and lang in available_languages
                    and lang not in normalized
                ):
                    normalized.append(lang)
            if len(normalized) != required_count:
                missing.append("languages")
        except Exception:
            missing.append("languages")

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
    except ChoicesValidationError as exc:
        return jsonify({"error": str(exc)}), 400
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
        # preserve_explicit_class_context ensures that when the frontend sends
        # `class: "druid"` for the active multiclass row, the builder uses only
        # that class — not the first entry in the `classes` array (which would
        # surface the wrong class's features, e.g. Cleric's Divine Order for Druid).
        builder = _build(body["choices_made"], preserve_explicit_class_context=True)
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500

    try:
        result: Dict[str, Any] = {"step": step, "choices_made": body["choices_made"]}
        # Only call to_character() for steps that actually use its result.
        # The "languages" step only needs builder.get_language_options() and must
        # not fail when choices_made is empty (no class/species set yet).
        _STEPS_NEEDING_CHARACTER = {"class", "species", "background", "abilities", "equipment"}
        character = builder.to_character() if step in _STEPS_NEEDING_CHARACTER else {}

        if step == "class":
            request_choices = body.get("choices_made") or {}
            explicit_class = request_choices.get("class")
            class_name = (
                explicit_class.strip()
                if isinstance(explicit_class, str) and explicit_class.strip()
                else character.get("class")
            )
            level = (
                _coerce_level(request_choices.get("level", 1), "choices_made.level")
                if isinstance(explicit_class, str) and explicit_class.strip()
                else character.get("level", 1)
            )
            class_rows = (character.get("choices_made") or {}).get("classes")
            if (
                not isinstance(explicit_class, str)
                or not explicit_class.strip()
            ) and isinstance(class_rows, list) and class_rows and isinstance(class_rows[0], dict):
                class_name = class_rows[0].get("class_name", class_name)
                level = class_rows[0].get("level", level)
            if class_name:
                from modules.data_loader import DataLoader
                from pathlib import Path
                dl = DataLoader(data_dir=str(Path(__file__).resolve().parent.parent.parent / "data"))
                # DataLoader keys classes by their canonical-cased name (e.g.
                # "Bard"), but request payloads carry lowercase ("bard"). Do a
                # case-insensitive resolution so the multiclassing block and
                # subclass lookups work regardless of incoming case.
                canonical_class = next(
                    (k for k in dl.classes if k.lower() == class_name.lower()),
                    class_name,
                )
                cdata = dl.classes.get(canonical_class, {})
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
                        for n, d in sorted(dl.get_subclasses_for_class(canonical_class).items())
                    ]
                feature_data = builder.get_class_features_and_choices()
                result["features_by_level"] = feature_data.get("features_by_level", {})
                result["nested_choices"] = feature_data.get("choices", [])

                # Resolve which class row this preview corresponds to and, if it
                # is a secondary multiclass row, filter nested_choices down to
                # only the proficiency picks RAW grants on multiclass entry.
                row_context = _resolve_class_row_context(request_choices, class_name)
                if not row_context["is_primary"]:
                    result["nested_choices"] = _filter_nested_choices_for_secondary_class(
                        result["nested_choices"], cdata
                    )
                result["row_context"] = row_context
            else:
                # No class resolved — still surface a legacy single-class context.
                result["row_context"] = {
                    "row_index": 0,
                    "is_primary": True,
                    "total_class_rows": 1,
                }

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
                # Surface the background's granted feat so the UI can grey it
                # out in the species feat picker (e.g. Human "Versatile").
                try:
                    bg_feat_info = builder.get_feat_choices()
                    if bg_feat_info.get("feat_name"):
                        result["background_feat"] = bg_feat_info["feat_name"]
                except Exception:
                    pass
                # Include currently-granted proficiencies so feat skill pickers
                # can grey out already-covered options.
                result["granted_proficiencies"] = {
                    "skills": character.get("proficiencies", {}).get("skills", []),
                    "tools": character.get("proficiencies", {}).get("tools", []),
                }

        elif step == "background":
            background = character.get("background")
            if background:
                result["skill_replacement"] = builder.get_background_skill_replacement_info()
                result["origin_feat_choices"] = builder.get_feat_choices()
            # Include currently-granted skill and tool proficiencies so the UI
            # can grey out already-covered options in feat skill pickers (e.g.
            # the Skilled origin feat).
            result["granted_proficiencies"] = {
                "skills": character.get("proficiencies", {}).get("skills", []),
                "tools": character.get("proficiencies", {}).get("tools", []),
            }

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


@character_bp.post("/random-languages")
def random_languages():
    """Return a random valid language selection for the language step."""
    body = _require_json()
    if body is None or "choices_made" not in body:
        return jsonify({"error": "Body must be JSON with 'choices_made'"}), 400
    try:
        builder = _build(body["choices_made"])
        return jsonify({"languages": builder.roll_languages()})
    except Exception:
        return jsonify({"error": "Failed to generate random languages"}), 500


# ==================== Derived views ====================


@character_bp.post("/derived")
def derived_view():
    """Return a derived view-model from `choices_made` for the React SPA.

    Request: `{ "choices_made": {...}, "view": "damage_cantrips" | "spell_management" |
                "mastery_management" | "invocation_management" }`
    Response: `{ "view": "<name>", "applicable": true|false, "data": {...}|null }`

    Returns 400 on missing/invalid body or unknown view. If a view is valid but
    not applicable to the current character (e.g. invocations on a non-Warlock),
    returns 200 with `applicable: false` and a human-readable `reason`.
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
        builder = _build(body["choices_made"], preserve_explicit_class_context=True)
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
        return jsonify({
            "view": view,
            "applicable": True,
            "choices_made": body["choices_made"],
            "data": data,
        })
    except ValueError as exc:
        return jsonify({
            "view": view,
            "applicable": False,
            "choices_made": body["choices_made"],
            "reason": str(exc),
            "data": None,
        })
    except Exception as exc:
        return jsonify({"error": str(exc), "traceback": traceback.format_exc()}), 500
