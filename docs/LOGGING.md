# Character Creator Logging System

## Overview

The application now includes comprehensive logging that tracks all choices made and builder state changes throughout the character creation process.

## Configuration

Logging is configured in `app.py` with:
- **Log Level**: INFO
- **Output**: Both console (stdout) and file (`character_creator.log`)
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## What Gets Logged

### For Each Route Processing:

1. **Route Name** - Which endpoint was called
2. **Choices Made** - All form inputs and selections
3. **Builder State Changes**:
   - Field changes (class, subclass, species, lineage, background, level, step)
   - Ability score assignments
   - Skill proficiency additions
   - Effect additions (with type and source)
   - Spell additions (prepared/known)
   - Language additions
   - Choices tracked in `choices_made` dict

## Logged Routes

The following routes include detailed logging:

- `create_character` - Initial character setup
- `select_class` - Class selection
- `select_subclass` - Subclass selection
- `submit_class_choices` - Class feature choices and skills
- `select_background` - Background selection
- `select_species` - Species selection
- `select_species_traits` - Species trait choices
- `select_lineage` - Lineage/variant selection
- `select_languages` - Language selections
- `submit_ability_scores` - Ability score assignments
- `submit_background_bonuses` - Background ASI bonuses

## Example Log Output

```
================================================================================
Route: select_class
================================================================================
Choices made:
  class: Wizard

Builder changes:
  class: None → Wizard
  step: class → class_choices
  effects: 0 → 5 (+5)
    - grant_save_proficiency from Wizard
    - grant_weapon_proficiency from Wizard
  choices_made.class: Wizard
================================================================================
```

## Log File Location

Logs are written to: `character_creator.log` in the project root directory.

## Helper Functions

### `log_route_processing(route_name, choices_made, builder_before, builder_after)`
Main logging function that coordinates logging for a route.

### `log_builder_changes(before, after)`
Compares two builder states and logs differences.

### `log_builder_state(builder)`
Logs a summary of current builder state.

## Usage in Routes

```python
@app.route('/select-class', methods=['POST'])
def select_class():
    # Get builder before changes
    builder_before = get_builder_from_session()
    
    # Collect choices from form
    choices = {'class': request.form.get('class')}
    
    # Apply changes
    builder = get_builder_from_session()
    builder.apply_choice('class', choices['class'])
    
    # Save
    save_builder_to_session(builder)
    
    # Log everything
    log_route_processing('select_class', choices, builder_before, builder)
    
    return redirect(url_for('next_step'))
```

## Benefits

1. **Debugging** - Track exactly what choices were made and when
2. **Audit Trail** - Complete history of character creation decisions
3. **Effect Tracking** - See when effects are applied and from what source
4. **State Changes** - Monitor builder state transitions
5. **Testing** - Verify correct behavior during development

## Performance

Logging uses Python's built-in `logging` module which is optimized for performance. The log file is written asynchronously and does not block route processing.

## Future Enhancements

Potential improvements:
- Log rotation (to prevent log file from growing too large)
- Different log levels per environment (DEBUG in dev, INFO in prod)
- Structured logging (JSON format) for easier parsing
- Integration with monitoring tools
- User-specific log files
