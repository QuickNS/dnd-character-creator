"""
Equipment Manager Module

Handles equipment inventory management for D&D 2024 characters.
This module provides inventory management WITHOUT equipped flags - 
all items in inventory are potential options.
"""
from typing import Dict, Any, List
from pathlib import Path
import json


class EquipmentManager:
    """
    Manages character equipment inventory.
    
    Design Philosophy:
    - No "equipped" flags - all inventory items are potential options
    - AC calculation shows ALL possible combinations
    - Weapon stats calculated for all weapons in inventory
    """
    
    def __init__(self, data_dir: str = "data/equipment"):
        """
        Initialize the equipment manager.
        
        Args:
            data_dir: Path to equipment data directory
        """
        self.data_dir = Path(data_dir)
        self._weapon_data = None
        self._armor_data = None
        self._gear_data = None
    
    @property
    def weapon_data(self) -> Dict[str, Dict[str, Any]]:
        """Lazy load weapon data."""
        if self._weapon_data is None:
            self._weapon_data = self._load_equipment_data('weapons.json')
        return self._weapon_data
    
    @property
    def armor_data(self) -> Dict[str, Dict[str, Any]]:
        """Lazy load armor data."""
        if self._armor_data is None:
            self._armor_data = self._load_equipment_data('armor.json')
        return self._armor_data
    
    @property
    def gear_data(self) -> Dict[str, Dict[str, Any]]:
        """Lazy load adventuring gear data."""
        if self._gear_data is None:
            self._gear_data = self._load_equipment_data('adventuring_gear.json')
        return self._gear_data
    
    def _load_equipment_data(self, filename: str) -> Dict[str, Dict[str, Any]]:
        """Load equipment data from JSON file."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {filename}: {e}")
            return {}
    
    def add_item(self, character_equipment: Dict[str, Any], item_name: str, 
                 category: str, quantity: int = 1) -> None:
        """
        Add item to character's inventory.
        
        Args:
            character_equipment: Character's equipment dict
            item_name: Name of the item to add
            category: 'weapons', 'armor', 'shields', or 'other'
            quantity: Number of items to add
        """
        if category not in character_equipment:
            character_equipment[category] = []
        
        # Check if item already exists
        for item in character_equipment[category]:
            if item['name'] == item_name:
                item['quantity'] = item.get('quantity', 1) + quantity
                return
        
        # Add new item
        item_data = self._get_item_properties(item_name, category)
        character_equipment[category].append({
            'name': item_name,
            'quantity': quantity,
            'properties': item_data
        })
    
    def remove_item(self, character_equipment: Dict[str, Any], item_name: str, 
                   category: str, quantity: int = 1) -> bool:
        """
        Remove item from character's inventory.
        
        Args:
            character_equipment: Character's equipment dict
            item_name: Name of the item to remove
            category: 'weapons', 'armor', 'shields', or 'other'
            quantity: Number of items to remove
            
        Returns:
            True if item was removed, False if not found
        """
        if category not in character_equipment:
            return False
        
        for i, item in enumerate(character_equipment[category]):
            if item['name'] == item_name:
                current_qty = item.get('quantity', 1)
                if current_qty <= quantity:
                    # Remove entirely
                    character_equipment[category].pop(i)
                else:
                    # Reduce quantity
                    item['quantity'] = current_qty - quantity
                return True
        
        return False
    
    def _get_item_properties(self, item_name: str, category: str) -> Dict[str, Any]:
        """Get item properties from data files."""
        if category == 'weapons':
            return self.weapon_data.get(item_name, {})
        elif category in ('armor', 'shields'):
            return self.armor_data.get(item_name, {})
        else:
            return self.gear_data.get(item_name, {})
    
    def get_all_armor(self, character_equipment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all armor pieces from inventory."""
        return character_equipment.get('armor', [])
    
    def get_all_shields(self, character_equipment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all shields from inventory."""
        return character_equipment.get('shields', [])
    
    def get_all_weapons(self, character_equipment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get all weapons from inventory."""
        return character_equipment.get('weapons', [])
    
    def can_use_armor(self, armor_name: str, proficiencies: List[str]) -> bool:
        """
        Check if character has proficiency to use armor.
        
        Args:
            armor_name: Name of the armor
            proficiencies: List of armor proficiencies
            
        Returns:
            True if character is proficient
        """
        armor_props = self.armor_data.get(armor_name, {})
        prof_required = armor_props.get('proficiency_required', '')
        
        # Check proficiency
        return any(prof.lower() in prof_required.lower() for prof in proficiencies)
    
    def can_use_weapon(self, weapon_name: str, proficiencies: List[str]) -> bool:
        """
        Check if character has proficiency to use weapon.
        
        Args:
            weapon_name: Name of the weapon
            proficiencies: List of weapon proficiencies
            
        Returns:
            True if character is proficient
        """
        weapon_props = self.weapon_data.get(weapon_name, {})
        prof_required = weapon_props.get('proficiency_required', '')
        
        # Check proficiency (e.g., "Simple weapons", "Martial weapons", or specific weapon)
        for prof in proficiencies:
            prof_lower = prof.lower()
            if (prof_lower == prof_required.lower() or 
                prof_lower == weapon_name.lower() or
                prof_lower == 'all weapons'):
                return True
        
        return False
    
    def calculate_total_weight(self, character_equipment: Dict[str, Any]) -> float:
        """
        Calculate total weight of equipment in pounds.
        
        Args:
            character_equipment: Character's equipment dict
            
        Returns:
            Total weight in pounds
        """
        total_weight = 0.0
        
        for category in ['weapons', 'armor', 'shields', 'other']:
            for item in character_equipment.get(category, []):
                weight = item.get('properties', {}).get('weight', 0)
                quantity = item.get('quantity', 1)
                total_weight += weight * quantity
        
        return total_weight
