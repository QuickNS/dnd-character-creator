"""
Spell Loading Utility

This utility provides functions to load spells from the new spell structure:
- Individual spell definitions in data/spells/definitions/
- Class-specific spell lists in data/spells/class_lists/

Usage:
    from utils.spell_loader import SpellLoader
    
    loader = SpellLoader()
    
    # Get spell definition
    longstrider = loader.get_spell("Longstrider")
    
    # Get class spell list
    druid_spells = loader.get_class_spells("Druid")
    
    # Get spells of a specific level for a class
    druid_cantrips = loader.get_class_spells("Druid", level=0)
    druid_1st = loader.get_class_spells("Druid", level=1)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class SpellLoader:
    def __init__(self, data_dir: str = None):
        """Initialize spell loader with data directory."""
        if data_dir is None:
            # Default to the project's data directory
            current_dir = Path(__file__).parent
            self.data_dir = current_dir.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
        self.definitions_dir = self.data_dir / "spells" / "definitions"
        self.class_lists_dir = self.data_dir / "spells" / "class_lists"
        
        # Cache for loaded data
        self._spell_cache = {}
        self._class_list_cache = {}
    
    def get_spell(self, spell_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a spell definition by name.
        
        Args:
            spell_name: Name of the spell (e.g., "Longstrider")
        
        Returns:
            Dictionary with spell data or None if not found
        """
        # Check cache first
        if spell_name in self._spell_cache:
            return self._spell_cache[spell_name]
        
        # Convert spell name to filename
        filename = self._spell_name_to_filename(spell_name)
        file_path = self.definitions_dir / f"{filename}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                spell_data = json.load(f)
                self._spell_cache[spell_name] = spell_data
                return spell_data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading spell {spell_name}: {e}")
            return None
    
    def get_class_spells(self, class_name: str, level: Optional[int] = None) -> Dict[str, Any]:
        """
        Load spell list for a class.
        
        Args:
            class_name: Name of the class (e.g., "Druid")
            level: Optional spell level (0 for cantrips, 1-9 for spells)
        
        Returns:
            Dictionary with class spell data or filtered by level
        """
        # Check cache first
        cache_key = f"{class_name}_{level}" if level is not None else class_name
        if cache_key in self._class_list_cache:
            return self._class_list_cache[cache_key]
        
        filename = class_name.lower()
        file_path = self.class_lists_dir / f"{filename}.json"
        
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                class_data = json.load(f)
                
                if level is not None:
                    # Filter by specific level
                    if level == 0:
                        result = {"cantrips": class_data.get("cantrips", [])}
                    else:
                        spells_by_level = class_data.get("spells_by_level", {})
                        result = {str(level): spells_by_level.get(str(level), [])}
                else:
                    result = class_data
                
                self._class_list_cache[cache_key] = result
                return result
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading class spells for {class_name}: {e}")
            return {}
    
    def get_spell_details_for_class(self, class_name: str, level: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get full spell details for all spells available to a class.
        
        Args:
            class_name: Name of the class
            level: Optional spell level filter
        
        Returns:
            List of spell dictionaries with full details
        """
        class_spells = self.get_class_spells(class_name, level)
        spell_details = []
        
        # Get cantrips if requested or if no level specified
        if level is None or level == 0:
            cantrips = class_spells.get("cantrips", [])
            for cantrip_name in cantrips:
                spell_data = self.get_spell(cantrip_name)
                if spell_data:
                    spell_details.append(spell_data)
        
        # Get leveled spells
        if level is None:
            # Get all levels
            spells_by_level = class_spells.get("spells_by_level", {})
            for spell_level, spell_names in spells_by_level.items():
                for spell_name in spell_names:
                    spell_data = self.get_spell(spell_name)
                    if spell_data:
                        spell_details.append(spell_data)
        elif level > 0:
            # Get specific level
            spells_by_level = class_spells.get("spells_by_level", {})
            spell_names = spells_by_level.get(str(level), [])
            for spell_name in spell_names:
                spell_data = self.get_spell(spell_name)
                if spell_data:
                    spell_details.append(spell_data)
        
        return spell_details
    
    def _spell_name_to_filename(self, spell_name: str) -> str:
        """Convert spell name to filename format."""
        # Convert spaces to underscores and lowercase
        # "Pass without Trace" -> "pass_without_trace"
        return spell_name.lower().replace(" ", "_").replace("'", "")
    
    def list_available_spells(self) -> List[str]:
        """Get list of all available spell names."""
        if not self.definitions_dir.exists():
            return []
        
        spell_names = []
        for file_path in self.definitions_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    spell_data = json.load(f)
                    name = spell_data.get("name")
                    if name:
                        spell_names.append(name)
            except (json.JSONDecodeError, IOError):
                continue
        
        return sorted(spell_names)
    
    def list_available_classes(self) -> List[str]:
        """Get list of all classes with spell lists."""
        if not self.class_lists_dir.exists():
            return []
        
        class_names = []
        for file_path in self.class_lists_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    class_data = json.load(f)
                    name = class_data.get("class")
                    if name:
                        class_names.append(name)
            except (json.JSONDecodeError, IOError):
                continue
        
        return sorted(class_names)


# Convenience functions for backward compatibility
def load_spell(spell_name: str) -> Optional[Dict[str, Any]]:
    """Load a single spell definition."""
    loader = SpellLoader()
    return loader.get_spell(spell_name)


def load_class_spells(class_name: str, level: Optional[int] = None) -> Dict[str, Any]:
    """Load spells for a class, optionally filtered by level."""
    loader = SpellLoader()
    return loader.get_class_spells(class_name, level)


# Example usage
if __name__ == "__main__":
    loader = SpellLoader()
    
    # Test spell loading
    print("Available spells:", loader.list_available_spells())
    print("Available classes:", loader.list_available_classes())
    
    # Test specific spell
    longstrider = loader.get_spell("Longstrider")
    print(f"Longstrider details: {longstrider}")
    
    # Test class spells
    druid_cantrips = loader.get_class_spells("Druid", level=0)
    print(f"Druid cantrips: {druid_cantrips}")
    
    # Test full spell details for class
    druid_1st_details = loader.get_spell_details_for_class("Druid", level=1)
    print(f"Druid 1st level spell details: {druid_1st_details}")