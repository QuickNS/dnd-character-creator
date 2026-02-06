# PDF Character Sheet Generation - Quick Start Guide

## For Users

### Download Your Character Sheet

1. **Complete character creation** through the wizard (all steps)
2. **Review your character** on the summary page
3. **Click "Download PDF"** button (green button with PDF icon)
4. **Save the PDF** to your computer
5. **Open with PDF viewer** (Adobe Reader, Preview, Chrome, etc.)

The PDF will be named: `{YourCharacterName}_character_sheet.pdf`

### What's Included

Your PDF character sheet contains:

✅ **Basic Information**
- Character name
- Class and level
- Background
- Species and lineage
- Alignment

✅ **Abilities**
- All six ability scores (raw values)
- Calculated modifiers (+2, -1, etc.)

✅ **Combat Stats**
- Armor Class (AC)
- Initiative
- Speed
- Hit Points (current and maximum)
- Hit Dice

✅ **Saving Throws**
- All six saving throws with bonuses
- Proficiency indicators

✅ **Skills**
- All 18 skills with modifiers
- Proficiency and expertise indicators

✅ **Proficiencies**
- Weapon proficiencies
- Armor proficiencies
- Tool proficiencies
- Languages

✅ **Spells** (for spellcasters)
- Spell slots by level
- Spellcasting ability
- Prepared spells
- Cantrips

✅ **Features & Traits**
- Class features with usage trackers
- Subclass features
- Species traits
- Background features
- Feat benefits

### Special Features

Some features have **checkbox trackers** for easy tracking:
- ☐ Second Wind (1 per short rest)
- ☐ Action Surge (1 per short rest)
- ☐☐☐ Rage (3 per long rest)
- Channel Divinity (uses per long rest)

## For Developers

### Generate PDF from Python

```python
from utils.pdf_writer import generate_character_sheet_pdf
from modules.character_builder import CharacterBuilder

# Create character
builder = CharacterBuilder()
builder.apply_choices({
    'name': 'Thorin Ironforge',
    'species': 'Dwarf',
    'class': 'Fighter',
    'level': 5,
    # ... other choices
})

# Get character data
character = builder.to_json()

# Add calculated values (required)
character['combat_stats'] = {...}
character['saving_throws'] = {...}
character['skill_modifiers'] = {...}
character['spell_slots'] = {...}

# Generate PDF
pdf_bytes = generate_character_sheet_pdf(character)

# Save to file
with open('character.pdf', 'wb') as f:
    f.write(pdf_bytes)
```

### Generate PDF from Flask Route

The route is already implemented at `/download-character-pdf`:

```python
@app.route('/download-character-pdf')
def download_character_pdf():
    """Download character as PDF."""
    # Get builder from session
    builder = get_builder_from_session()
    if not builder:
        return redirect(url_for('index.index'))
    
    # Get complete character data with ALL calculations
    # CharacterBuilder handles all calculations internally
    character_data = builder.to_character()
    
    # Generate and return PDF using pre-calculated data
    pdf_bytes = generate_character_sheet_pdf(character_data)
    return send_file(io.BytesIO(pdf_bytes), ...)
```

### Custom Formatting

Add custom formatting for specific features in `pdf_template/field_mapping_config.json`:

```json
{
  "custom_formatting": {
    "Second Wind": "Second Wind (uses: ☐ / 1 per short rest)",
    "Your Feature": "Custom text with {placeholders}"
  }
}
```

**Template Variables**:
- `{uses}` - Uses per rest
- `{dc}` - Save DC
- `{damage}` - Damage amount
- `{range}` - Range

### Modify Field Mappings

Edit `pdf_template/field_mapping_config.json` to change which character attributes map to which PDF fields:

```json
{
  "basic_info": {
    "CharacterName": "name",
    "ClassLevel": "class_level"
  }
}
```

### Inspect PDF Fields

Use the inspection tool to discover field names in a PDF:

```bash
python utils/inspect_pdf.py
```

This creates `pdf_template/field_mapping.json` with all field information.

### Test PDF Generation

Run the test script:

```bash
python test_pdf_generation.py
```

This generates `test_character_sheet.pdf` from the example character.

## Troubleshooting

### PDF has no data
**Issue**: PDF downloads but is blank

**Solution**: 
1. Ensure PDF template has fillable form fields
2. Check field mappings in `field_mapping_config.json`
3. Verify character has all required data

### Download fails with error
**Issue**: Route returns 500 error

**Check**:
1. Character is complete (`step == 'complete'`)
2. Session contains valid character data
3. Check Flask logs for error details

### Fields in wrong places
**Issue**: Data appears in wrong PDF fields

**Solution**:
1. Run `utils/inspect_pdf.py` to see actual field names
2. Update field mappings in config file
3. Test with simple character first

### Custom formatting not applied
**Issue**: Features show default text

**Solution**:
1. Check feature name matches exactly (case-sensitive)
2. Verify custom_formatting is in correct section
3. Reload Flask app to pick up config changes

## Best Practices

### For Users
1. **Create character first** - Complete all wizard steps before downloading
2. **Check summary** - Review character on summary page before PDF
3. **Save multiple versions** - Download PDF at different levels as character progresses

### For Developers
1. **Calculate server-side** - Always compute values before PDF generation
2. **Test incrementally** - Add fields one section at a time
3. **Use custom formatting sparingly** - Only for features needing special display
4. **Document changes** - Update field mapping comments when modifying

## Examples

### Simple Character PDF
```python
character = {
    'name': 'Bob',
    'class': 'Fighter',
    'level': 1,
    'abilities': {'Strength': 16, 'Dexterity': 14, ...}
}
pdf = generate_character_sheet_pdf(character)
```

### With Custom Formatting
```python
# Add to field_mapping_config.json
{
  "custom_formatting": {
    "Second Wind": "Second Wind (uses: ☐ / 1 per short rest)"
  }
}

# Feature will display with checkbox tracker in PDF
```

### Multiple Characters
```python
for name in ['Alice', 'Bob', 'Charlie']:
    builder.apply_choice('name', name)
    character = builder.to_json()
    pdf_bytes = generate_character_sheet_pdf(character)
    with open(f'{name}_sheet.pdf', 'wb') as f:
        f.write(pdf_bytes)
```

## Resources

- **Full Documentation**: `pdf_template/README.md`
- **Architecture**: `docs/ARCHITECTURE.md` (PDF Generation section)
- **Implementation Details**: `docs/PDF_GENERATION_COMPLETE.md`
- **Source Code**: `utils/pdf_writer.py`
- **Field Mappings**: `pdf_template/field_mapping_config.json`

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Flask logs for error messages
3. Verify PDF template has form fields
4. Test with the example character first
5. Check field mapping configuration

For custom templates or advanced usage, see `pdf_template/README.md`.
