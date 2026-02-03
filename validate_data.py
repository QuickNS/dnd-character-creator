#!/usr/bin/env python3
"""
Validate D&D 2024 data files against their schemas.
Run this to ensure all data files follow the correct format.
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("❌ jsonschema not installed. Install with: pip install jsonschema")
    sys.exit(1)


def load_json(filepath):
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_file(data_file, schema_file):
    """Validate a data file against a schema."""
    try:
        data = load_json(data_file)
        schema = load_json(schema_file)
        jsonschema.validate(data, schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error loading files: {e}"


def validate_classes():
    """Validate all class files."""
    print("=" * 70)
    print("VALIDATING CLASS FILES")
    print("=" * 70)
    
    schema_file = Path("models/class_schema.json")
    if not schema_file.exists():
        print("❌ Schema file not found:", schema_file)
        return False
    
    classes_dir = Path("data/classes")
    if not classes_dir.exists():
        print("⚠️  No classes directory found")
        return True
    
    all_valid = True
    for class_file in sorted(classes_dir.glob("*.json")):
        valid, error = validate_file(class_file, schema_file)
        if valid:
            print(f"✅ {class_file.name}")
        else:
            print(f"❌ {class_file.name}")
            print(f"   Error: {error}")
            all_valid = False
    
    return all_valid


def validate_subclasses():
    """Validate all subclass files."""
    print("\n" + "=" * 70)
    print("VALIDATING SUBCLASS FILES")
    print("=" * 70)
    
    schema_file = Path("models/subclass_schema.json")
    if not schema_file.exists():
        print("❌ Schema file not found:", schema_file)
        return False
    
    subclasses_dir = Path("data/subclasses")
    if not subclasses_dir.exists():
        print("⚠️  No subclasses directory found")
        return True
    
    all_valid = True
    for class_dir in sorted(subclasses_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        
        print(f"\n{class_dir.name.upper()}:")
        for subclass_file in sorted(class_dir.glob("*.json")):
            valid, error = validate_file(subclass_file, schema_file)
            if valid:
                print(f"  ✅ {subclass_file.name}")
            else:
                print(f"  ❌ {subclass_file.name}")
                print(f"     Error: {error}")
                all_valid = False
    
    return all_valid


def main():
    """Main validation function."""
    print("D&D 2024 Data Validator")
    print("Validating data files against schemas in models/")
    print()
    
    classes_valid = validate_classes()
    subclasses_valid = validate_subclasses()
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    if classes_valid and subclasses_valid:
        print("✅ All data files are valid!")
        return 0
    else:
        print("❌ Some data files failed validation")
        print("\nTo fix validation errors:")
        print("  1. Review the schema in models/ directory")
        print("  2. Check examples in models/README.md")
        print("  3. Update data files to match the schema")
        return 1


if __name__ == "__main__":
    sys.exit(main())
