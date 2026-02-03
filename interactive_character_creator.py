#!/usr/bin/env python3
"""
Interactive D&D 2024 Character Creator
Handles step-by-step character creation with all choices and validations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class CharacterCreator:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.classes = self._load_data("classes")
        self.backgrounds = self._load_data("backgrounds")
        self.species = self._load_data("species")
        self.species_variants = self._load_data("species_variants")
        self.feats = self._load_data("feats")
        self.subclasses = self._load_subclasses()
        
    def _load_data(self, data_type: str) -> Dict[str, Dict[str, Any]]:
        """Load JSON data files from a directory."""
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
    
    def _load_subclasses(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Load subclass data organized by class name."""
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
                            with open(json_file, 'r') as f:
                                subclass_data = json.load(f)
                                subclass_name = subclass_data.get("name")
                                if subclass_name:
                                    subclasses[class_name][subclass_name] = subclass_data
                        except (json.JSONDecodeError, IOError) as e:
                            print(f"Warning: Could not load {json_file}: {e}")
        
        return subclasses
    
    def get_subclasses_for_class(self, class_name: str) -> Dict[str, Dict[str, Any]]:
        """Get available subclasses for a specific class."""
        return self.subclasses.get(class_name, {})
    
    def display_options(self, options: List[str], title: str = "Choose from:") -> None:
        """Display numbered options to the user."""
        print(f"\n{title}")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
    
    def get_user_choice(self, options: List[str], prompt: str = "Enter your choice: ") -> str:
        """Get a valid choice from the user."""
        while True:
            try:
                self.display_options(options)
                choice = input(f"\n{prompt}").strip()
                
                # Handle empty input
                if not choice:
                    print("Please enter a choice.")
                    continue
                
                # Try to parse as number
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(options):
                        return options[choice_num - 1]
                    else:
                        print(f"Please enter a number between 1 and {len(options)}")
                        continue
                except ValueError:
                    # Try to match by name (exact match first)
                    choice_clean = choice.strip().lower()
                    exact_matches = [opt for opt in options if opt.lower() == choice_clean]
                    if exact_matches:
                        return exact_matches[0]
                    
                    # Try partial match
                    partial_matches = [opt for opt in options if choice_clean in opt.lower()]
                    if len(partial_matches) == 1:
                        return partial_matches[0]
                    elif len(partial_matches) > 1:
                        print(f"Ambiguous choice. Did you mean: {', '.join(partial_matches)}?")
                        continue
                    else:
                        print(f"'{choice}' is not a valid option.")
                        continue
                        
            except KeyboardInterrupt:
                print("\nCharacter creation cancelled.")
                sys.exit(0)
            except EOFError:
                print("\nCharacter creation cancelled.")
                sys.exit(0)
    
    def get_multiple_choices(self, options: List[str], count: int, prompt: str = "Enter your choices: ") -> List[str]:
        """Get multiple choices from the user."""
        chosen = []
        available = options.copy()
        
        for i in range(count):
            if i == 0:
                selection_prompt = f"{prompt} ({i+1} of {count})"
            else:
                selection_prompt = f"Choose another ({i+1} of {count}): "
                
            choice = self.get_user_choice(available, selection_prompt)
            chosen.append(choice)
            available.remove(choice)
            
            if i < count - 1:
                print(f"Selected: {', '.join(chosen)}")
        
        return chosen
    
    def create_character(self) -> Dict[str, Any]:
        """Main character creation workflow."""
        character = {
            "name": "",
            "level": 1,
            "class": "",
            "background": "",
            "species": "",
            "lineage": None,
            "creature_type": "Humanoid",
            "size": "Medium",
            "speed": 30,
            "darkvision": 0,
            "alignment": "",
            "ability_scores": {"Strength": 10, "Dexterity": 10, "Constitution": 10, 
                             "Intelligence": 10, "Wisdom": 10, "Charisma": 10},
            "skills": [],
            "languages": [],
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
        
        print("=== D&D 2024 Character Creator ===")
        character["name"] = input("\nCharacter name: ")
        
        # Get level
        while True:
            try:
                level = int(input("Character level (1-20): "))
                if 1 <= level <= 20:
                    character["level"] = level
                    break
                else:
                    print("Level must be between 1 and 20.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Step 1: Choose Class
        character = self._choose_class(character)
        
        # Step 2: Choose Background  
        character = self._choose_background(character)
        
        # Step 3: Choose Starting Equipment
        character = self._choose_starting_equipment(character)
        
        # Step 4: Choose Species
        character = self._choose_species(character)
        
        # Step 5: Determine Languages
        character = self._choose_languages(character)
        
        # Step 6: Assign Ability Scores (Standard Array)
        character = self._assign_standard_array_ability_scores(character)
        
        # Step 6b: Apply Background Ability Score Increases
        character = self._apply_background_ability_score_increases(character)
        
        # Step 7: Choose Alignment
        character = self._choose_alignment(character)
        
        return character
    
    def _choose_class(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Handle class selection and class-specific choices."""
        print("\n=== Class Selection ===")
        
        # Choose class
        available_classes = list(self.classes.keys())
        chosen_class = self.get_user_choice(available_classes, "Choose a class: ")
        character["class"] = chosen_class
        
        class_data = self.classes[chosen_class]
        print(f"\nYou chose {chosen_class}!")
        print(f"Primary Ability: {', '.join(class_data['primary_ability'])}")
        print(f"Hit Die: d{class_data['hit_die']}")
        
        # Choose skills
        skill_count = class_data["skill_proficiencies_count"]
        skill_options = class_data["skill_options"]
        
        chosen_skills = self.get_multiple_choices(
            skill_options, 
            skill_count, 
            f"Choose {skill_count} skill proficiencies:"
        )
        character["skills"].extend(chosen_skills)
        character["choices_made"]["class_skills"] = chosen_skills
        
        # Process level-based features with choices
        for level in range(1, character["level"] + 1):
            level_str = str(level)
            if level_str in class_data.get("features_by_level", {}):
                features = class_data["features_by_level"][level_str]
                character = self._process_features(character, features, f"Level {level}")
        
        return character
    
    def _process_features(self, character: Dict[str, Any], features: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Process features, handling both simple text and choice-based features."""
        # Determine feature category based on source
        if "Level" in source:
            category = "class"
        elif "Lineage" in source:
            category = "lineage"
        elif "Species" in source:
            category = "species"
        elif "Background" in source or "Feat" in source:
            category = "background"
        else:
            category = "class"  # Default
        
        for feature_name, feature_data in features.items():
            if isinstance(feature_data, dict) and feature_data.get("type") == "choice":
                # Handle choice-based feature
                character = self._handle_choice_feature(character, feature_name, feature_data, source, category)
            elif isinstance(feature_data, str):
                # Handle simple text feature
                feature_entry = {
                    "name": feature_name,
                    "description": feature_data,
                    "source": source
                }
                character["features"][category].append(feature_entry)
            elif isinstance(feature_data, dict):
                # Handle complex feature (non-choice)
                description = feature_data.get("description", str(feature_data))
                feature_entry = {
                    "name": feature_name,
                    "description": description,
                    "source": source
                }
                character["features"][category].append(feature_entry)
        
        return character
    
    def _handle_choice_feature(self, character: Dict[str, Any], feature_name: str, choice_data: Dict[str, Any], source: str, category: str) -> Dict[str, Any]:
        """Handle a feature that requires user choice."""
        print(f"\n🎯 {feature_name} Choice")
        print(f"   {choice_data.get('description', '')}")
        
        options = choice_data["options"]
        count = choice_data["count"]
        
        # Check if count varies by level
        if "count_by_level" in choice_data:
            level_counts = choice_data["count_by_level"]
            for level in sorted(level_counts.keys(), key=int, reverse=True):
                if character["level"] >= int(level):
                    count = level_counts[level]
                    break
        
        # Display option descriptions if available
        option_descriptions = choice_data.get("option_descriptions", {})
        if option_descriptions:
            print("   Options:")
            for option in options:
                desc = option_descriptions.get(option, "")
                print(f"     • {option}: {desc}")
        
        # Handle single vs multiple choices
        if count == 1:
            chosen = self.get_user_choice(options, f"Choose {feature_name}: ")
            choices = [chosen]
        else:
            choices = self.get_multiple_choices(options, count, f"Choose {count} for {feature_name}: ")
        
        # Store the choice
        choice_key = f"{source.lower().replace(' ', '_')}_{feature_name.lower().replace(' ', '_')}"
        character["choices_made"][choice_key] = choices
        
        # Add to features with proper categorization
        if count == 1:
            feature_text = f"{feature_name}: {choices[0]}"
        else:
            feature_text = f"{feature_name}: {', '.join(choices)}"
        
        feature_entry = {
            "name": feature_name,
            "description": feature_text,
            "source": source
        }
        character["features"][category].append(feature_entry)
        
        # Handle special feature types
        if feature_name == "Keen Senses":
            # Add skill proficiency for Keen Senses choice
            character["skills"].extend(choices)
        
        return character
    
    def _choose_background(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Handle background selection and background choices."""
        print("\n=== Background Selection ===")
        
        available_backgrounds = list(self.backgrounds.keys())
        chosen_background = self.get_user_choice(available_backgrounds, "Choose a background: ")
        character["background"] = chosen_background
        
        background_data = self.backgrounds[chosen_background]
        print(f"\nYou chose {chosen_background}!")
        
        # Handle skill conflicts
        background_skills = background_data.get("skill_proficiencies", [])
        character = self._resolve_skill_conflicts(character, background_skills)
        
        # Add feat if provided
        if "feat" in background_data:
            feature_entry = {
                "name": "Background Feat",
                "description": f"Background Feat: {background_data['feat']}",
                "source": f"{chosen_background} Background"
            }
            character["features"]["background"].append(feature_entry)
        
        return character
    
    
    def _resolve_skill_conflicts(self, character: Dict[str, Any], background_skills: List[str]) -> Dict[str, Any]:
        """Handle skill proficiency conflicts between class and background."""
        class_skills = character["choices_made"]["class_skills"]
        conflicts = [skill for skill in background_skills if skill in class_skills]
        
        if conflicts:
            print(f"\nSkill Conflict! You already have {', '.join(conflicts)} from your class.")
            print("You can choose replacement skills instead:")
            
            # For each conflict, choose a replacement
            all_skills = [
                "Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception", 
                "History", "Insight", "Intimidation", "Investigation", "Medicine", 
                "Nature", "Perception", "Performance", "Persuasion", "Religion", 
                "Sleight of Hand", "Stealth", "Survival"
            ]
            
            replacement_skills = []
            for conflict_skill in conflicts:
                available_skills = [skill for skill in all_skills 
                                 if skill not in character["skills"] + replacement_skills]
                
                replacement = self.get_user_choice(
                    available_skills, 
                    f"Choose replacement for {conflict_skill}: "
                )
                replacement_skills.append(replacement)
            
            # Add non-conflicting background skills and replacements
            for skill in background_skills:
                if skill not in conflicts:
                    character["skills"].append(skill)
            
            character["skills"].extend(replacement_skills)
            character["choices_made"]["background_skill_replacements"] = dict(zip(conflicts, replacement_skills))
        else:
            character["skills"].extend(background_skills)
        
        return character
    
    def _choose_species(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Handle species selection and lineage choices."""
        print("\n=== Species Selection ===")
        
        available_species = list(self.species.keys())
        chosen_species = self.get_user_choice(available_species, "Choose a species: ")
        character["species"] = chosen_species
        
        species_data = self.species[chosen_species]
        print(f"\nYou chose {chosen_species}!")
        
        # Apply base species attributes
        character = self._apply_species_attributes(character, species_data)
        
        # Check for lineage options
        lineage_variants = [variant for variant in self.species_variants.values() 
                          if variant.get("parent_species") == chosen_species]
        
        if lineage_variants:
            print(f"\n{chosen_species} has the following lineages:")
            lineage_names = [variant["name"] for variant in lineage_variants]
            
            chosen_lineage = self.get_user_choice(lineage_names, "Choose a lineage: ")
            character["lineage"] = chosen_lineage
            
            # Apply lineage traits
            lineage_data = next(variant for variant in lineage_variants if variant["name"] == chosen_lineage)
            
            # Apply lineage attributes (may override species attributes)
            character = self._apply_lineage_attributes(character, lineage_data)
            
            # Handle spellcasting ability choice for lineage spells
            if "spellcasting_ability_choices" in lineage_data:
                spellcasting_choices = lineage_data["spellcasting_ability_choices"]
                print(f"\n🎯 {chosen_lineage} Spellcasting Ability")
                print("   Choose your spellcasting ability for lineage spells:")
                
                chosen_ability = self.get_user_choice(spellcasting_choices, "Choose spellcasting ability: ")
                character["lineage_spellcasting_ability"] = chosen_ability
                character["choices_made"]["lineage_spellcasting_ability"] = chosen_ability
                
                print(f"   Selected: {chosen_ability}")
            
            print(f"\nApplying {chosen_lineage} traits:")
            if "traits" in lineage_data:
                character = self._process_features(character, lineage_data["traits"], f"{chosen_lineage} Lineage")
        
        # Apply base species traits
        print(f"\nApplying base {chosen_species} traits:")
        if "traits" in species_data:
            character = self._process_features(character, species_data["traits"], f"{chosen_species} Species")
        
        # Handle base species skill proficiencies (non-choice)
        species_skills = species_data.get("skill_proficiencies", [])
        if species_skills:
            character["skills"].extend(species_skills)
            print(f"   Added skill proficiencies: {', '.join(species_skills)}")
        
        return character
    
    def _apply_species_attributes(self, character: Dict[str, Any], species_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply physical attributes from species data."""
        # Apply creature type
        if "creature_type" in species_data:
            character["creature_type"] = species_data["creature_type"]
        
        # Apply size
        if "size" in species_data:
            character["size"] = species_data["size"]
        
        # Apply speed
        if "speed" in species_data:
            character["speed"] = species_data["speed"]
        
        # Apply darkvision (extract from traits or use default)
        if "darkvision_range" in species_data:
            character["darkvision"] = species_data["darkvision_range"]
        elif "Darkvision" in species_data.get("traits", {}):
            # Extract darkvision range from trait description
            darkvision_trait = species_data["traits"]["Darkvision"]
            if "60 feet" in darkvision_trait:
                character["darkvision"] = 60
            elif "120 feet" in darkvision_trait:
                character["darkvision"] = 120
            else:
                character["darkvision"] = 60  # Default for species with darkvision
        else:
            character["darkvision"] = 0  # No darkvision
        
        return character
    
    def _apply_lineage_attributes(self, character: Dict[str, Any], lineage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply lineage attributes that may override species attributes."""
        # Override speed if lineage specifies it
        if "speed" in lineage_data:
            character["speed"] = lineage_data["speed"]
        
        # Override darkvision if lineage specifies it
        if "darkvision_range" in lineage_data:
            character["darkvision"] = lineage_data["darkvision_range"]
        
        # Override size if lineage specifies it (rare but possible)
        if "size" in lineage_data:
            character["size"] = lineage_data["size"]
        
        # Override creature type if lineage specifies it (very rare but possible)
        if "creature_type" in lineage_data:
            character["creature_type"] = lineage_data["creature_type"]
        
        return character
    
    def _choose_starting_equipment(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Handle starting equipment selection from class and background."""
        print("\n=== Starting Equipment ===")
        
        # For now, add basic equipment - this could be expanded to handle choices
        class_name = character["class"]
        background_name = character["background"]
        
        equipment = []
        equipment.append(f"{class_name} starting equipment")
        equipment.append(f"{background_name} background equipment")
        
        character["equipment"] = equipment
        print(f"Added starting equipment from {class_name} and {background_name}")
        
        return character
    
    def _choose_languages(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Handle language selection: Common + 2 choices, plus any from class/species."""
        print("\n=== Language Selection ===")
        
        languages = ["Common"]  # Everyone gets Common
        
        # Add species languages
        species_data = self.species.get(character["species"], {})
        species_languages = species_data.get("languages", [])
        for lang in species_languages:
            if lang != "Common" and lang not in languages:
                if "choice" not in lang.lower():
                    languages.append(lang)
        
        # Standard language choices (Common + 2 additional)
        available_languages = [
            "Draconic", "Dwarvish", "Elvish", "Giant", "Gnomish", "Goblin", 
            "Halfling", "Orc", "Abyssal", "Celestial", "Deep Speech", 
            "Infernal", "Primordial", "Sylvan", "Undercommon"
        ]
        
        # Remove already known languages from choices
        available_choices = [lang for lang in available_languages if lang not in languages]
        
        if available_choices and len(languages) < 3:  # Common + 2 more
            needed = 3 - len(languages)
            print(f"Choose {needed} additional language(s):")
            
            chosen_languages = self.get_multiple_choices(
                available_choices, 
                needed, 
                f"Select {needed} language(s):"
            )
            languages.extend(chosen_languages)
            character["choices_made"]["languages"] = chosen_languages
        
        character["languages"] = languages
        print(f"Languages: {', '.join(languages)}")
        
        return character
    
    def _assign_standard_array_ability_scores(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Assign ability scores using standard array with class-recommended allocation."""
        print("\n=== Ability Score Assignment ===")
        print("Using Standard Array: 15, 14, 13, 12, 10, 8")
        
        # Get class recommendations
        class_data = self.classes.get(character["class"], {})
        primary_abilities = class_data.get("primary_ability", [])
        
        # Standard array values
        standard_array = [15, 14, 13, 12, 10, 8]
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        
        # Ask user for allocation preference
        if primary_abilities:
            print(f"\nRecommended high scores for {character['class']}: {', '.join(primary_abilities)}")
            print("1. Use recommended allocation")
            print("2. Assign values manually")
            
            choice = self.get_user_choice(["Use recommended allocation", "Assign values manually"], 
                                        "Choose allocation method: ")
            
            if choice == "Use recommended allocation":
                # Auto-assign with recommended allocation
                ability_mapping = {}
                remaining_values = standard_array.copy()
                remaining_abilities = abilities.copy()
                
                # Assign highest values to primary abilities
                for i, primary in enumerate(primary_abilities[:2]):  # Top 2 primaries get highest scores
                    if i < len(remaining_values) and primary in remaining_abilities:
                        ability_mapping[primary] = remaining_values.pop(0)
                        remaining_abilities.remove(primary)
                
                # Constitution gets next highest (important for all classes)
                if "Constitution" in remaining_abilities and remaining_values:
                    ability_mapping["Constitution"] = remaining_values.pop(0)
                    remaining_abilities.remove("Constitution")
                
                # Assign remaining values to remaining abilities
                for ability in remaining_abilities:
                    if remaining_values:
                        ability_mapping[ability] = remaining_values.pop(0)
                
                # Apply the assignments
                for ability, score in ability_mapping.items():
                    character["ability_scores"][ability] = score
                
                print("\nApplied recommended ability score allocation:")
                for ability, score in character["ability_scores"].items():
                    modifier = (score - 10) // 2
                    sign = "+" if modifier >= 0 else ""
                    print(f"  {ability}: {score} ({sign}{modifier})")
                
                character["choices_made"]["ability_scores"] = "standard_array_recommended"
                
            else:
                # Manual assignment
                print("\nManual Assignment:")
                print("Assign the standard array values (15, 14, 13, 12, 10, 8) to your abilities.")
                
                remaining_values = standard_array.copy()
                ability_mapping = {}
                
                # Let user assign each value
                for i, value in enumerate(standard_array):
                    print(f"\nAssigning value: {value}")
                    print(f"Remaining values after this: {remaining_values[i+1:] if i+1 < len(remaining_values) else 'None'}")
                    
                    # Show current assignments
                    if ability_mapping:
                        current_assignments = [f"{ability}: {score}" for ability, score in ability_mapping.items()]
                        print(f"Current assignments: {', '.join(current_assignments)}")
                    
                    # Get available abilities (not yet assigned)
                    available_abilities = [ability for ability in abilities if ability not in ability_mapping]
                    
                    chosen_ability = self.get_user_choice(available_abilities, f"Assign {value} to which ability: ")
                    ability_mapping[chosen_ability] = value
                
                # Apply the assignments
                for ability, score in ability_mapping.items():
                    character["ability_scores"][ability] = score
                
                print("\nApplied manual ability score allocation:")
                for ability, score in character["ability_scores"].items():
                    modifier = (score - 10) // 2
                    sign = "+" if modifier >= 0 else ""
                    print(f"  {ability}: {score} ({sign}{modifier})")
                
                character["choices_made"]["ability_scores"] = "standard_array_manual"
        
        return character
    
    def _apply_background_ability_score_increases(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Apply ability score increases from background."""
        print("\n=== Background Ability Score Increases ===")
        
        background_name = character["background"]
        background_data = self.backgrounds.get(background_name, {})
        asi_data = background_data.get("ability_score_increase", {})
        
        if not asi_data:
            print(f"No ability score increases from {background_name} background.")
            return character
        
        total_points = asi_data.get("total", 3)
        options = asi_data.get("options", ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"])
        suggested = asi_data.get("suggested", {})
        
        print(f"Background provides {total_points} ability score increase points.")
        
        if suggested:
            suggestion_text = ", ".join([f"{ability} +{bonus}" for ability, bonus in suggested.items()])
            print(f"Suggested allocation: {suggestion_text}")
            
            use_suggested = input("Use suggested allocation? (y/n): ").lower().startswith('y')
            if use_suggested:
                for ability, bonus in suggested.items():
                    character["ability_scores"][ability] += bonus
                character["choices_made"]["background_ability_score_assignment"] = suggested
                
                print("Applied background ability score increases:")
                for ability, bonus in suggested.items():
                    total_score = character["ability_scores"][ability]
                    modifier = (total_score - 10) // 2
                    sign = "+" if modifier >= 0 else ""
                    print(f"  {ability}: {total_score} ({sign}{modifier}) [+{bonus} from background]")
                
                return character
        
        # Manual assignment
        print("Manual assignment:")
        remaining_points = total_points
        assignment = {}
        
        while remaining_points > 0:
            available_abilities = [ability for ability in options if assignment.get(ability, 0) < 2]  # Max +2 per ability
            
            print(f"\nRemaining points: {remaining_points}")
            print("Current assignment:", {k: f"+{v}" for k, v in assignment.items()} if assignment else "None")
            
            ability = self.get_user_choice(available_abilities, "Choose ability to increase: ")
            
            max_increase = min(2 - assignment.get(ability, 0), remaining_points)
            if max_increase == 1:
                increase = 1
            else:
                while True:
                    try:
                        increase = int(input(f"Increase {ability} by how much? (1-{max_increase}): "))
                        if 1 <= increase <= max_increase:
                            break
                        else:
                            print(f"Must be between 1 and {max_increase}")
                    except ValueError:
                        print("Please enter a valid number")
            
            assignment[ability] = assignment.get(ability, 0) + increase
            remaining_points -= increase
            character["ability_scores"][ability] += increase
        
        character["choices_made"]["background_ability_score_assignment"] = assignment
        
        print("Applied background ability score increases:")
        for ability, bonus in assignment.items():
            total_score = character["ability_scores"][ability]
            modifier = (total_score - 10) // 2
            sign = "+" if modifier >= 0 else ""
            print(f"  {ability}: {total_score} ({sign}{modifier}) [+{bonus} from background]")
        
        return character
    
    def _choose_alignment(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alignment selection."""
        print("\n=== Alignment Selection ===")
        
        alignments = [
            "Lawful Good", "Neutral Good", "Chaotic Good",
            "Lawful Neutral", "True Neutral", "Chaotic Neutral", 
            "Lawful Evil", "Neutral Evil", "Chaotic Evil"
        ]
        
        chosen_alignment = self.get_user_choice(alignments, "Choose your character's alignment: ")
        character["alignment"] = chosen_alignment
        character["choices_made"]["alignment"] = chosen_alignment
        
        print(f"Selected alignment: {chosen_alignment}")
        
        return character
    
    def display_character_summary(self, character: Dict[str, Any]) -> None:
        """Display a summary of the created character."""
        print("\n" + "="*50)
        print("CHARACTER SUMMARY")
        print("="*50)
        
        print(f"Name: {character['name']}")
        print(f"Level: {character['level']}")
        print(f"Class: {character['class']}")
        print(f"Background: {character['background']}")
        print(f"Species: {character['species']}")
        if character['lineage']:
            print(f"Lineage: {character['lineage']}")
        print(f"Alignment: {character.get('alignment', 'Not set')}")
        
        print(f"\nPhysical Attributes:")
        print(f"  Creature Type: {character.get('creature_type', 'Humanoid')}")
        print(f"  Size: {character.get('size', 'Medium')}")
        print(f"  Speed: {character.get('speed', 30)} feet")
        darkvision = character.get('darkvision', 0)
        if darkvision > 0:
            print(f"  Darkvision: {darkvision} feet")
        else:
            print(f"  Darkvision: None")
        
        # Display lineage spellcasting ability if chosen
        if character.get('lineage_spellcasting_ability'):
            print(f"\nSpellcasting:")
            print(f"  Lineage Spellcasting Ability: {character['lineage_spellcasting_ability']}")
        
        print(f"\nAbility Scores:")
        for ability, score in character['ability_scores'].items():
            modifier = (score - 10) // 2
            sign = "+" if modifier >= 0 else ""
            print(f"  {ability}: {score} ({sign}{modifier})")
        
        print(f"\nSkill Proficiencies: {', '.join(character['skills'])}")
        
        if character.get('languages'):
            print(f"Languages: {', '.join(character['languages'])}")
        
        if character.get('equipment'):
            print(f"\nEquipment:")
            for item in character['equipment']:
                print(f"  • {item}")
        
        print(f"\nFeatures:")
        
        # Display features by category
        category_headers = {
            "class": "Class Features",
            "species": "Species Features",
            "lineage": "Lineage Features",
            "background": "Background Features",
            "feats": "Feats"
        }
        
        for category, header in category_headers.items():
            if character['features'][category]:
                print(f"\n  {header}:")
                for feature in character['features'][category]:
                    if isinstance(feature, dict):
                        print(f"    • {feature['description']} (from {feature['source']})")
                    else:
                        print(f"    • {feature}")  # Fallback for string features
        
        # Display choices made
        if character['choices_made']:
            print(f"\nChoices Made:")
            for choice_type, choice_value in character['choices_made'].items():
                print(f"  {choice_type}: {choice_value}")

def main():
    """Main entry point for the character creator."""
    try:
        creator = CharacterCreator()
        character = creator.create_character()
        creator.display_character_summary(character)
        
        # Ask if they want to save the character
        save = input("\nSave character to file? (y/n): ").lower().startswith('y')
        if save:
            filename = f"{character['name'].replace(' ', '_').lower()}_character.json"
            with open(filename, 'w') as f:
                json.dump(character, f, indent=2)
            print(f"Character saved to {filename}")
        
    except KeyboardInterrupt:
        print("\nCharacter creation cancelled.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()