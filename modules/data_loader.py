"""
Data Loader Module

Handles loading all game data from JSON files in the data/ directory.
This module provides a clean interface for accessing D&D 2024 game data.
"""

import json
from pathlib import Path
from typing import Dict, Any


class DataLoader:
    """
    Loads and provides access to D&D 2024 game data from JSON files.

    Attributes:
        data_dir: Path to the data directory
        classes: Dictionary of class data keyed by class name
        backgrounds: Dictionary of background data keyed by background name
        species: Dictionary of species data keyed by species name
        species_variants: Dictionary of species variant data
        feats: Dictionary of feat data keyed by feat name
        subclasses: Dictionary of subclass data organized by class name
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the data loader.

        Args:
            data_dir: Path to the directory containing game data JSON files
        """
        self.data_dir = Path(data_dir)
        self.classes = self._load_data("classes")
        self.backgrounds = self._load_data("backgrounds")
        self.species = self._load_data("species")
        self.species_variants = self._load_data("species_variants")
        self.feats = self._load_data("feats")
        self.subclasses = self._load_subclasses()

    def _load_data(self, data_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Load JSON data files from a directory.

        Args:
            data_type: Name of the subdirectory to load from (e.g., 'classes', 'species')

        Returns:
            Dictionary of loaded data keyed by the 'name' field in each JSON file
        """
        data_dir = self.data_dir / data_type
        data = {}

        if data_dir.exists():
            for json_file in data_dir.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        file_data = json.load(f)
                        name = file_data.get("name")
                        if name:
                            data[name] = file_data
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load {json_file}: {e}")

        return data

    def _load_subclasses(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Load subclass data organized by class name.

        Returns:
            Dictionary with structure: {class_name: {subclass_name: subclass_data}}
        """
        subclass_dir = self.data_dir / "subclasses"
        subclasses = {}

        if subclass_dir.exists():
            # Each subdirectory represents a class
            for class_dir in subclass_dir.iterdir():
                if class_dir.is_dir():
                    class_name = class_dir.name.title()
                    subclasses[class_name] = {}

                    # Load all subclass files in this class directory
                    for json_file in class_dir.glob("*.json"):
                        try:
                            with open(json_file, "r") as f:
                                subclass_data = json.load(f)
                                subclass_name = subclass_data.get("name")
                                if subclass_name:
                                    subclasses[class_name][subclass_name] = (
                                        subclass_data
                                    )
                        except (json.JSONDecodeError, IOError) as e:
                            print(f"Warning: Could not load {json_file}: {e}")

        return subclasses

    def get_subclasses_for_class(self, class_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get available subclasses for a specific class.

        Args:
            class_name: Name of the class (e.g., 'Fighter', 'Wizard')

        Returns:
            Dictionary of subclass data for the specified class
        """
        return self.subclasses.get(class_name, {})
