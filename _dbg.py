from app import app
from routes.api.character import (
    _filter_nested_choices_for_secondary_class,
    _classify_choice_for_multiclass,
    _resolve_class_row_context,
)
import json

client = app.test_client()
choices = {
    "classes": [
        {"class_name": "wizard", "level": 3},
        {"class_name": "bard", "level": 1},
    ],
    "class": "bard",
    "level": 1,
}
resp = client.post("/api/v1/character/preview-step", json={"choices_made": choices, "step": "class"})
data = resp.get_json()
print("keys:", list(data.keys()))
print("row_context:", data.get("row_context"))
print("nested_choices:", json.dumps(data.get("nested_choices"), indent=2)[:500])
print("features_by_level keys:", list((data.get("features_by_level") or {}).keys()))
# Inspect builder directly via the same path
from modules.character_builder import CharacterBuilder
from routes.api.character import _normalize_choices_for_builder
n = _normalize_choices_for_builder(choices, preserve_explicit_class_context=True)
print("\nnormalized:", json.dumps(n, indent=2))
b = CharacterBuilder()
b.apply_choices(n)
fd = b.get_class_features_and_choices()
print("\nraw choices from builder:", len(fd.get("choices", [])))
for c in fd.get("choices", []):
    print(" -", c.get("type"), c.get("choice_key") or c.get("feature_name"))
