#!/usr/bin/env python3
"""
Create a Wood Elf Fighter character with default choices.
This demonstrates programmatic character creation using the D&D 2024 data.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

class ProgrammaticCharacterCreator:
    """Creates D&D 2024 characters programmatically with default choices."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize with data directory path."""
        self.data_dir = Path(data_dir)
        self.classes = self._load_data("classes")
        self.species = self._load_data("species")
        self.species_variants = self._load_data("species_variants")
        self.backgrounds = self._load_data("backgrounds")
    
    def _load_data(self, data_type: str) -> Dict[str, Dict[str, Any]]:
        """Load data from JSON files in the specified directory."""
        data_dir = self.data_dir / data_type
        data = {}
        
        if data_dir.exists():
            for json_file in data_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        file_data = json.load(f)
                        name = file_data.get("name")
                        if name:
                            data[name] = file_data
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Could not load {json_file}: {e}")
        
        return data
    
    def create_wood_elf_fighter(self, name: str = "Arandel") -> Dict[str, Any]:
        """Create a Wood Elf Fighter with default choices."""
        character = {
            "name": name,
            "level": 1,
            "class": "Fighter",
            "background": "Soldier",  # Default background
            "species": "Elf",
            "lineage": "Wood Elf",
            "ability_scores": {
                "Strength": 15,
                "Dexterity": 13, 
                "Constitution": 14,
                "Intelligence": 10,
                "Wisdom": 12,
                "Charisma": 8
            },
            "skills": [],
            "features": {
                "class": [],
                "species": [],
                "lineage": [],
                "background": [],
                "feats": []
            },
            "equipment": [],
            "choices_made": {}
        }
        
        print(f"Creating {name}, Level 1 Wood Elf Fighter...")
        
        # Apply class features and make default choices
        self._apply_class_features(character)
        
        # Apply background features and default ability scores
        self._apply_background_features(character)
        
        # Apply species and lineage traits
        self._apply_species_features(character)
        self._apply_lineage_features(character)
        
        return character
    
    def _apply_class_features(self, character: Dict[str, Any]) -> None:
        """Apply Fighter class features with default choices."""
        fighter_data = self.classes["Fighter"]
        
        # Add default Fighter skills (Acrobatics, Perception for Wood Elf)
        default_skills = ["Acrobatics", "Perception"]
        character["skills"].extend(default_skills)
        character["choices_made"]["class_skills"] = default_skills
        
        # Apply level 1 features
        level_1_features = fighter_data["features_by_level"]["1"]
        
        for feature_name, feature_data in level_1_features.items():
            if feature_name == "Fighting Style":
                # Choose Archery fighting style
                fighting_style = "Archery"
                character["choices_made"]["fighting_style"] = fighting_style
                
                feature_entry = {
                    "name": "Fighting Style",
                    "description": f"Fighting Style: {fighting_style} - You gain a +2 bonus to attack rolls you make with ranged weapons.",
                    "source": "Level 1"
                }
                character["features"]["class"].append(feature_entry)
            
            elif isinstance(feature_data, str):
                # Simple text feature
                feature_entry = {
                    "name": feature_name,
                    "description": feature_data,
                    "source": "Level 1"
                }
                character["features"]["class"].append(feature_entry)
    
    def _apply_background_features(self, character: Dict[str, Any]) -> None:
        """Apply Soldier background features and ability score increases."""
        soldier_data = self.backgrounds["Soldier"]
        
        # Apply suggested ability score increases (Strength +2, Constitution +1)
        character["ability_scores"]["Dexterity"] += 2
        character["ability_scores"]["Strength"] += 1
        character["choices_made"]["ability_score_assignment"] = {
            "Dexterity": 2,
            "Strength": 1
        }
        
        # Add background skills (Athletics, Intimidation)
        bg_skills = ["Athletics", "Intimidation"]
        character["skills"].extend(bg_skills)
        
        # Add background feat
        if "feat" in soldier_data:
            feature_entry = {
                "name": "Background Feat",
                "description": f"Background Feat: {soldier_data['feat']}",
                "source": "Soldier Background"
            }
            character["features"]["background"].append(feature_entry)
    
    def _apply_species_features(self, character: Dict[str, Any]) -> None:
        """Apply Elf species traits with default choices."""
        elf_data = self.species["Elf"]
        
        # Apply all Elf traits
        for trait_name, trait_data in elf_data["traits"].items():
            if trait_name == "Keen Senses":
                # Choose Perception as default
                chosen_skill = "Perception"
                character["skills"].append(chosen_skill)
                character["choices_made"]["keen_senses"] = chosen_skill
                
                feature_entry = {
                    "name": "Keen Senses",
                    "description": f"Keen Senses: {chosen_skill}",
                    "source": "Elf Species"
                }
                character["features"]["species"].append(feature_entry)
            
            elif isinstance(trait_data, str):
                feature_entry = {
                    "name": trait_name,
                    "description": trait_data,
                    "source": "Elf Species"
                }
                character["features"]["species"].append(feature_entry)
    
    def _apply_lineage_features(self, character: Dict[str, Any]) -> None:
        """Apply Wood Elf lineage traits."""
        wood_elf_data = self.species_variants["Wood Elf"]
        
        # Update speed to 35 feet
        character["speed"] = wood_elf_data["speed"] if
        
        # Apply Wood Elf traits
        for trait_name, trait_data in wood_elf_data["traits"].items():
            if isinstance(trait_data, str):
                feature_entry = {
                    "name": trait_name,
                    "description": trait_data,
                    "source": "Wood Elf Lineage"
                }
                character["features"]["lineage"].append(feature_entry)
        
        # Note spellcasting ability choice (default to Wisdom for Wood Elf)
        character["choices_made"]["lineage_spellcasting_ability"] = "Wisdom"
    
    def display_character(self, character: Dict[str, Any]) -> None:
        """Display the created character."""
        print("\n" + "="*60)
        print("WOOD ELF FIGHTER CHARACTER")
        print("="*60)
        
        print(f"Name: {character['name']}")
        print(f"Level: {character['level']}")
        print(f"Class: {character['class']}")
        print(f"Background: {character['background']}")
        print(f"Species: {character['species']}")
        print(f"Lineage: {character['lineage']}")
        print(f"Speed: {character.get('speed', 30)} feet")
        
        print(f"\nAbility Scores:")
        for ability, score in character['ability_scores'].items():
            modifier = (score - 10) // 2
            sign = "+" if modifier >= 0 else ""
            print(f"  {ability}: {score} ({sign}{modifier})")
        
        print(f"\nSkill Proficiencies: {', '.join(character['skills'])}")
        
        print(f"\nFeatures:")
        
        # Display features by category
        category_headers = {
            "class": "Class Features",
            "species": "Species Features", 
            "lineage": "Lineage Features",
            "background": "Background Features"
        }
        
        for category, header in category_headers.items():
            if character['features'][category]:
                print(f"\n  {header}:")
                for feature in character['features'][category]:
                    print(f"    • {feature['description']}")
        
        print(f"\nChoices Made:")
        for choice_type, choice_value in character['choices_made'].items():
            print(f"  {choice_type}: {choice_value}")

def main():
    """Main function to create and display the Wood Elf Fighter."""
    try:
        creator = ProgrammaticCharacterCreator()
        
        # Create the character
        character = creator.create_wood_elf_fighter("Arandel Swiftarrow")
        
        # Display the character
        creator.display_character(character)
        
        # Save to file
        filename = f"{character['name'].replace(' ', '_').lower()}_fighter.json"
        with open(filename, 'w') as f:
            json.dump(character, f, indent=2)
        
        print(f"\nCharacter saved to {filename}")
        
    except Exception as e:
        print(f"Error creating character: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
