# HTML Character Sheet Generation - Quick Start Guide

## For Users

### Print Your Character Sheet to PDF

1. **Complete character creation** through the wizard (all steps)
2. **Review your character** on the summary page
3. **Click "View Character Sheet"** button 
4. **Use browser's Print function** (Ctrl+P / Cmd+P or click the Print button on the page)
5. **Select "Save as PDF"** as the printer destination
6. **Save the PDF** to your computer

The character sheet is displayed as an HTML page with background images of the official D&D 2024 character sheet, with your character's information overlaid in the correct positions.

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

### Rendering Character Sheet HTML

The character sheet is rendered as HTML with CSS positioning overlay on background images:

```python
from modules.character_builder import CharacterBuilder
from flask import render_template

# Create character
builder = CharacterBuilder()
builder.apply_choices({
    'name': 'Thorin Ironforge',
    'species': 'Dwarf',
    'class': 'Fighter',
    'level': 5,
    # ... other choices
})

# Get complete character data with ALL calculations
character = builder.to_character()

# Render HTML character sheet (all calculations pre-done by CharacterBuilder)
return render_template('character_sheet_pdf.html', character=character)
```

### Flask Route Implementation

The route is already implemented at `/character-sheet`:

```python
@character_summary_bp.route("/character-sheet")
def character_sheet():
    """Display fillable HTML character sheet."""
    builder = get_builder_from_session()
    if not builder or builder.get_current_step() != "complete":
        return redirect(url_for("index.index"))

    # Get complete character data with ALL calculations from CharacterBuilder
    # No transformations needed - template uses data as-is
    character_data = builder.to_character()

    return render_template("character_sheet_pdf.html", character=character_data)
```

### HTML Template Structure

The template (`templates/character_sheet_pdf.html`) uses:
- **Background images**: Official D&D 2024 character sheet layout (`/static/pdf_template/sheet1.png`, `sheet2.png`)
- **Absolute positioning**: CSS positions text fields exactly where they should appear
- **Print styles**: `@media print` rules for clean PDF export
- **No-print controls**: On-screen buttons (Print, Back) that don't appear in PDF output

```css
.sheet-background {
    background-image: url('/static/pdf_template/sheet1.png');
    background-size: cover;
}

.char-field {
    position: absolute;
    top: 1.2in;    /* Exact position on sheet */
    left: 0.5in;
    /* ... */
}
```

### Customizing Field Positions

Edit `templates/character_sheet_pdf.html` to adjust field positions:

```html
<input type="text" 
       class="char-field" 
       value="{{ character.name }}"
       style="top: 1.2in; left: 0.5in; width: 3in;"
       readonly>
```

**Positioning Tips**:
- Use inches (`in`) for precise print positioning
- Measure from top-left of the page
- Use `readonly` attribute so fields can't be edited in browser
- Test by printing to PDF and checking alignment

### Adding New Fields

1. Determine the position on the background image
2. Add HTML input/textarea with absolute positioning
3. Use character data from `{{ character.property_name }}`
4. Style with appropriate font size and alignment

Example:
```html
<textarea class="char-field" 
          style="top: 5in; left: 1in; width: 6in; height: 2in;"
          readonly>{{ character.features.class['Feature Name'].description }}</textarea>
```

### Modifying Background Images

Replace images in `/static/pdf_template/`:
- `sheet1.png` - Character sheet page 1 (abilities, skills, combat)
- `sheet2.png` - Character sheet page 2 (features, spells, equipment)

**Image Requirements**:
- Size: 8.5" x 11" at 300 DPI (2550 x 3300 pixels)
- Format: PNG with transparent or white background
- Quality: High-resolution scan or vector export

## Troubleshooting

### Fields not aligning with background
**Issue**: Text appears in wrong locations

**Solution**: 
1. Check background image dimensions (should be 8.5" x 11")
2. Adjust CSS positioning in template
3. Test print preview frequently
4. Use browser developer tools to inspect positioning

### Print button not visible
**Issue**: Can't find the print button

**Solution**:
1. Look in top-right corner of page (floating "no-print" div)
2. Or use browser's Print function (Ctrl+P / Cmd+P)
3. Make sure JavaScript is enabled

### PDF exports blank
**Issue**: Browser prints empty pages

**Solution**:
1. Check "Print background graphics" is enabled in print dialog
2. Ensure background images are loading (check browser console)
3. Verify images exist in `/static/pdf_template/`
3. Verify character has all required data

### Download fails with error
**Issue**: Route returns 500 error

**Check**:
1. Character is complete (`step == 'complete'`)
2. Session contains valid character data
3. Check Flask logs for error details


## Best Practices

### For Users
1. **Complete character creation** - Finish all wizard steps before viewing sheet
2. **Check summary** - Review character on summary page 
3. **Use browser Print to PDF** - Select "Save as PDF" as printer destination
4. **Enable background graphics** - Ensure this option is checked in print dialog

### For Developers
1. **Calculate in CharacterBuilder** - ALL calculations happen in `builder.to_character()`
2. **Use absolute positioning** - Position fields precisely with CSS top/left in inches
3. **Test print preview frequently** - Check alignment after each change
4. **Keep template clean** - Separate CSS styles from positioning logic
5. **Use readonly inputs** - Prevent browser editing with `readonly` attribute

## Template Structure

### Page Layout
```html
<div class="sheet-container">
    <!-- Background image layer -->
    <div class="sheet-background sheet-page1"></div>
    
    <!-- Positioned fields layer -->
    <div class="field-layer">
        <input type="text" class="char-field" 
               style="top: 0.5in; left: 1in;" 
               value="{{ character.name }}" readonly>
        <!-- More fields... -->
    </div>
</div>
```

### Print Styles
```css
@media print {
    .no-print { display: none; }
    .sheet-container { margin: 0; box-shadow: none; }
    body { background: white; }
}
```

## Resources

- **Template**: `templates/character_sheet_pdf.html`
- **Background Images**: `static/pdf_template/sheet1.png`, `sheet2.png`  
- **Route**: `routes/character_summary.py` (contains `/character-sheet` route)
- **Architecture Documentation**: `docs/ARCHITECTURE.md` (HTML Character Sheet section)
- **Flask App**: `app.py`

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Ensure background images are present in `/static/pdf_template/`
3. Enable "Print background graphics" in browser print dialog
4. Test with the browser's Print Preview
5. Check Flask logs for any template rendering errors
For customization and advanced usage, see `templates/character_sheet_pdf.html`.
