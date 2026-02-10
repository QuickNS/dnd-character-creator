"""
Choice resolution utilities for the Choice Reference System.
Handles resolving choice options from various source types.
"""

import json
from pathlib import Path


def resolve_choice_options(
    choices_data: dict,
    character: dict,
    class_data: dict | None = None,
    subclass_data: dict | None = None,
) -> list:
    """Resolve choice options from various source types in the Choice Reference System."""
    source = choices_data.get("source", {})
    source_type = source.get("type")

    if source_type == "internal":
        # Reference list within same JSON file (e.g., fighting_styles in Fighter, maneuvers in Battle Master)
        list_name = source.get("list", "")
        # Try subclass_data first (for subclass features), then class_data (for class features)
        data_source = (
            subclass_data
            if subclass_data and list_name in subclass_data
            else class_data
        )
        if data_source and list_name in data_source:
            choice_list = data_source[list_name]
            if isinstance(choice_list, dict):
                return list(choice_list.keys())
            elif isinstance(choice_list, list):
                return choice_list
        return []
    elif source_type == "external":
        # Reference specific external file
        file_path = source.get("file", "")
        list_name = source.get("list", "")
        return load_external_choice_list(file_path, list_name)
    elif source_type == "external_dynamic":
        # Dynamic file based on previous choice
        file_pattern = source.get("file_pattern", "")
        depends_on = source.get("depends_on", "")
        list_name = source.get("list", "")

        # Get the dependency value from character's choices
        choices_made = character.get("choices_made", {})
        dependency_value = choices_made.get(depends_on)

        if dependency_value:
            file_path = file_pattern.format(**{depends_on: dependency_value})
            return load_external_choice_list(file_path, list_name)
        return []
    elif source_type == "fixed_list":
        # Direct option list
        return source.get("options", [])

    return []


def get_option_descriptions(
    feature_data: dict,
    choices_data: dict,
    class_data: dict | None = None,
    subclass_data: dict | None = None,
) -> dict:
    """Get option descriptions from various sources."""
    # First check if feature_data has option_descriptions field
    if "option_descriptions" in feature_data:
        return feature_data["option_descriptions"]

    # For external sources, load the file and extract descriptions
    source = choices_data.get("source", {})
    if source.get("type") == "external":
        file_path = source.get("file", "")
        list_name = source.get("list", "")
        if file_path and list_name:
            try:
                # Get the project root directory (parent of utils/)
                project_root = Path(__file__).parent.parent
                full_path = project_root / "data" / file_path
                if full_path.exists():
                    with open(full_path, "r") as f:
                        data = json.load(f)
                        choice_list = data.get(list_name, {})
                        if isinstance(choice_list, dict):
                            # Extract descriptions from structured objects
                            descriptions = {}
                            for key, value in choice_list.items():
                                if isinstance(value, dict) and "description" in value:
                                    descriptions[key] = value["description"]
                                elif isinstance(value, str):
                                    descriptions[key] = value
                                else:
                                    descriptions[key] = str(value)
                            return descriptions
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load descriptions from {file_path}: {e}")
    
    # For internal sources, look for the list in the data
    if source.get("type") == "internal":
        list_name = source.get("list", "")
        # Try subclass_data first, then class_data
        data_source = (
            subclass_data
            if subclass_data and list_name in subclass_data
            else class_data
        )
        if data_source and list_name in data_source:
            choice_list = data_source[list_name]
            if isinstance(choice_list, dict):
                # Extract descriptions from structured objects (e.g., divine_orders with effects)
                descriptions = {}
                for key, value in choice_list.items():
                    if isinstance(value, dict) and "description" in value:
                        descriptions[key] = value["description"]
                    elif isinstance(value, str):
                        descriptions[key] = value
                    else:
                        descriptions[key] = str(value)
                return descriptions

    return {}


def load_external_choice_list(file_path: str, list_name: str) -> list:
    """Load choice options from external JSON file."""
    try:
        # Get the project root directory (parent of utils/)
        project_root = Path(__file__).parent.parent
        full_path = project_root / "data" / file_path
        if full_path.exists():
            with open(full_path, "r") as f:
                data = json.load(f)
                choice_list = data.get(list_name, {})
                if isinstance(choice_list, dict):
                    return list(choice_list.keys())
                elif isinstance(choice_list, list):
                    return choice_list
        return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load choice list from {file_path}: {e}")
        return []
