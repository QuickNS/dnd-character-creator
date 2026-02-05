---
agent: 'agent'
description: 'Removes old code and documentation files related to the previous character state management approach, ensuring a clean architecture with CharacterBuilder as the single source of truth.'
---

Check all files for any remaining references to the old character state management approach, including:
- Direct access to `session['character']`
- Manual character dictionaries
- Any dual-save compatibility code

Remove any such references and ensure that all routes and templates are updated to use `CharacterBuilder` and the new session management approach. This includes:
- Updating route handlers to use `get_builder_from_session()` and `save_builder_to_session()`
- Updating templates to use the character data passed from routes instead of accessing session data directly

Remove unused files that are no longer relevant to the new architecture, such as:
- Any old Python files that were specific to the previous character state management approach
- Any old template files that were specific to the previous approach
- Any old documentation files that were specific to the previous approach
- Any old utility functions that were specific to the previous approach
- Any old test cases that were specific to the previous approach

Identify unused code or documentation that may have been missed in the initial refactoring and remove it to ensure a clean codebase. This includes:
- Old helper functions that are no longer used
- Old documentation that references the previous architecture
- Leftover test scripts that are no longer relevant
- Any other code or documentation that is not aligned with the new architecture and coding standards
- Refactoring plans or summaries that are no longer relevant to the current state of the codebase

Refactor any remaining code or documentation that may still reference the old architecture to ensure consistency with the new architecture and coding standards. This includes:
- Ensure that all routes are properly using `CharacterBuilder` and the new session management approach
- Ensure there is no duplication of logic that should now be centralized in `CharacterBuilder`. Apply DRY principles to eliminate any such duplication.
- Ensure that all templates are properly using the character data passed from routes
- Ensure that all documentation is updated to reflect the new architecture and coding standards
- Update any remaining documentation to reflect the new architecture and coding standards
- Ensure that all test cases are updated to reflect the new architecture and coding standards, and that all tests are passing with the new implementation



