#!/usr/bin/env python3
"""Test script to verify the refactored lineage system works correctly."""

import requests
import json

def test_character_creation_with_lineages():
    """Test that the new lineage system works correctly in the web interface."""
    base_url = "http://127.0.0.1:5000"
    
    # Test each species that has lineages
    species_tests = [
        {
            "species": "Elf",
            "lineages": ["High Elf", "Wood Elf", "Drow"]
        },
        {
            "species": "Dragonborn", 
            "lineages": ["Chromatic Dragonborn", "Metallic Dragonborn"]
        },
        {
            "species": "Gnome",
            "lineages": ["Forest Gnome", "Rock Gnome"]
        },
        {
            "species": "Tiefling",
            "lineages": ["Abyssal Tiefling", "Chthonic Tiefling", "Infernal Tiefling"]
        }
    ]
    
    for test in species_tests:
        print(f"\n=== Testing {test['species']} ===")
        
        # Start a session
        session = requests.Session()
        
        # Create character
        response = session.post(f"{base_url}/create", data={"character_name": f"Test {test['species']}"})
        print(f"Create character: {response.status_code}")
        
        # Select Fighter class (simple choice)
        response = session.post(f"{base_url}/select-class", data={"class": "Fighter"})
        print(f"Select class: {response.status_code}")
        
        # Skip class choices for simplicity
        response = session.post(f"{base_url}/submit-class-choices", data={"skills": ["Acrobatics", "Perception"]})
        print(f"Class choices: {response.status_code}")
        
        # Select background
        response = session.post(f"{base_url}/select-background", data={"background": "Acolyte"})
        print(f"Select background: {response.status_code}")
        
        # Select species
        response = session.post(f"{base_url}/select-species", data={"species": test['species']})
        print(f"Select species: {response.status_code}")
        
        # Check if redirected to lineage selection
        if response.status_code == 302:
            print(f"✓ Correctly redirected to lineage selection for {test['species']}")
            
            # Get lineage selection page
            response = session.get(f"{base_url}/choose-lineage")
            if response.status_code == 200:
                print(f"✓ Lineage selection page loaded successfully")
                
                # Check if expected lineages are available (basic check)
                page_content = response.text
                for lineage in test['lineages']:
                    if lineage in page_content:
                        print(f"  ✓ {lineage} found on page")
                    else:
                        print(f"  ✗ {lineage} NOT found on page")
            else:
                print(f"✗ Failed to load lineage selection page: {response.status_code}")
        else:
            print(f"✗ Expected redirect to lineage selection but got: {response.status_code}")

if __name__ == "__main__":
    print("Testing refactored lineage system...")
    try:
        test_character_creation_with_lineages()
        print("\n✅ Lineage system test completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")