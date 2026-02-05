---
agent: 'agent'
description: 'Implements class features'
---

This details the execution plan for implementing the species features for species {{ species_name }} in accordance with:

- The data models defined in the models/ folder
- The data files under the data/ folder
- The effects system detailed in FEATURE_EFFECTS.md
- All relevant instructions in copilot-instructions.md

## Sequence Plan:

1. Check the data files located at data/species/{{ species_name }}.yaml for any inconsistencies or missing information related to the wiki page for {{ species_name }}.
  - The wiki information is stored in wiki_data/species/{{ species_name }}.json. If needed, update the data files to ensure they accurately reflect the wiki content.
  - We are only focusing on features from basic rules and/or official Player's Handbook 2024.
2. Take special note of any features that have complex effects or interactions as detailed in FEATURE_EFFECTS.md.
3. Make sure all class features are accurately represented according in the data files, including the level where they become available.
4. Review the class data file located at data/classes/{{ class_name }}.yaml to understand the core features and attributes of the class.
5. Implement the class features in the codebase, ensuring that:
   - Each feature is implemented according to its description in the data files.
   - Any special effects or interactions are handled as per FEATURE_EFFECTS.md.
   - The implementation adheres to coding standards and best practices.
6. Write unit tests for each class feature to ensure they function as intended.
7. Conduct integration testing to verify that the class features work correctly within the overall system.
8. Document the implementation details and any important notes regarding the class features.
