---
description: 'Implements species features end-to-end'
---

Implement all features for species **{{ species_name }}** end-to-end.

Use the `implement-class-feature` skill (adapted for species) to implement all traits:
- Species data: `data/species/{{ species_name }}.json`
- Variant data (if applicable): `data/species_variants/{{ species_name }}/`
- Wiki data: `wiki_data/species/{{ species_name }}.json`
- Tests: `tests/species/test_{{ species_name }}_traits.py`

Remember: species do NOT have ability score increases in D&D 2024.

Update `data/completeness/backlog.json` to mark {{ species_name }} as validated.