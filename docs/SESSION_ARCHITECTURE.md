# Session Architecture - Migration Complete ✅

## Current State: Fully Builder-Based Architecture

The application has been **fully migrated** to use `CharacterBuilder` exclusively. The legacy dual-architecture has been removed.

### Architecture (After Migration)

**Single Source of Truth**: `session['builder_state']` contains serialized CharacterBuilder

```python
# All routes now use this pattern
def some_route():
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index'))
    
    # Work with builder
    builder.apply_choice('some_choice', value)
    builder.set_step('next_step')
    
    # Save back to session
    save_builder_to_session(builder)
    
    # Get character data for templates
    character = builder.to_json()
    return render_template('template.html', character=character)
```

## What Was Fixed

### Before (Dual Architecture - PROBLEMATIC ❌)
- **Two parallel systems**: `session['character']` (dict) and `session['builder_state']` (serialized builder)
- **Data inconsistency**: Changes in one didn't always reflect in the other
- **Lost effects**: `from_json()` didn't restore `applied_effects`, causing data loss
- **Maintenance burden**: Developers had to know which system to use where

### After (Single Architecture - CLEAN ✅)
- **Single source**: Only `session['builder_state']` is used
- **Always consistent**: All changes go through CharacterBuilder
- **Effects preserved**: `from_json()` properly restores all state including `applied_effects`
- **Simple mental model**: Always use `get_builder_from_session()` and `save_builder_to_session()`

## Migration Changes

### Helper Functions

**`get_builder_from_session()`** - Simplified
```python
def get_builder_from_session() -> Optional[CharacterBuilder]:
    """Get CharacterBuilder from session."""
    if 'builder_state' not in session:
        return None
    
    builder = CharacterBuilder()
    builder.from_json(session['builder_state'])
    return builder
```

**`save_builder_to_session()`** - No more dual-save
```python
def save_builder_to_session(builder: CharacterBuilder):
    """Save CharacterBuilder state to session."""
    session['builder_state'] = builder.to_json()  # Only saves to builder_state
    session.modified = True
```

### CharacterBuilder Enhancements

Added helper methods for common operations:
```python
class CharacterBuilder:
    def set_step(self, step: str) -> None:
        """Set the current creation step."""
        self.character_data['step'] = step
    
    def get_current_step(self) -> str:
        """Get the current creation step."""
        return self.character_data['step']
```

### Route Pattern

All routes now follow this consistent pattern:
1. Get builder from session
2. Check if builder exists (if not, redirect)
3. Make changes through builder methods
4. Save builder back to session
5. Pass` builder.to_json()` to templates

**Example:**
```python
@app.route('/select-species', methods=['POST'])
def select_species():
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index'))
    
    builder.apply_choice('species', species_name)
    builder.set_step('lineage')
    save_builder_to_session(builder)
    return redirect(url_for('choose_lineage'))
```

## Testing

Comprehensive test suite ensures migration correctness:
- **`tests/core/test_serialization.py`** - 13 tests for `to_json()`/`from_json()` cycle
- **`tests/core/test_character_builder.py`** - 4 tests for basic builder functionality

Key tests:
- `test_effects_survive_multiple_cycles` - Ensures effects persist through save/restore
- `test_full_wizard_flow` - Simulates entire wizard with 5+ steps
- `test_cantrips_preserved_after_restore` - Prevents regression of cantrip bug

✅ **All 17 tests pass**

## Benefits of Migration

1. **Data Integrity**: Effects and all character state are always preserved
2. **Simpler Code**: Single pattern for all routes, easier to understand
3. **Better Testing**: Clear interface makes it easy to test
4. **Future-Proof**: Adding new features only requires updating CharacterBuilder
5. **No More Sync Issues**: Single source of truth eliminates inconsistencies

## Guidelines for New Code

### ✅ DO:
- Always use `get_builder_from_session()` to access character state
- Always use `save_builder_to_session()` to persist changes
- Use `builder.set_step()` to change steps
- Pass `builder.to_json()` to templates for display
- Add new builder methods for common operations

### ❌ DON'T:
- Never access `session['character']` directly (doesn't exist anymore)
- Never create character dictionaries manually
- Never modify character data without going through builder
- Never assume session has character data without checking builder first

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                 Flask Session                    │
│                                                  │
│  ┌───────────────────────────────────────────┐ │
│  │ session['builder_state']                  │ │
│  │ (serialized CharacterBuilder JSON)        │ │
│  └───────────────────────────────────────────┘ │
│         ↑                        ↓              │
│         │                        │              │
│   save_builder_to_session  get_builder_from   │
│         │                   _session            │
└─────────┼────────────────────────┼──────────────┘
          │                        │
          │                        ↓
    ┌─────┴────────────────────────────┐
    │      CharacterBuilder             │
    │                                   │
    │  • character_data (dict)          │
    │  • applied_effects (list)         │
    │  • ability_scores (AbilityScores) │
    │                                   │
    │  Methods:                         │
    │  • apply_choice()                 │
    │  • set_step()                     │
    │  • to_json() / from_json()       │
    └───────────────────────────────────┘
```

## Migration Completed

- ✅ CharacterBuilder `set_step()` method added
- ✅ All routes converted to use builder
- ✅ `/create` route uses builder from the start
- ✅ All `session['character']` references removed
- ✅ Dual-save compatibility code removed
- ✅ Template updated to use route-passed data
- ✅ All tests passing
- ✅ Effects properly preserved through entire wizard flow

The application now has a clean, maintainable architecture with a single source of truth for character state.
