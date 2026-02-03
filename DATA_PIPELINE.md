# Data Pipeline: Wiki → Cache → Data Files

This document describes the two-stage data pipeline for D&D 2024 content.

## Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  D&D 2024   │────▶│  wiki_data/ │────▶│   data/     │
│    Wiki     │     │   (cache)   │     │  (app data) │
└─────────────┘     └─────────────┘     └─────────────┘
   dnd2024.          Raw HTML/text      Structured JSON
   wikidot.com       from wiki pages     for application
```

## Stage 1: Fetch & Cache

**Script**: [update_classes.py](update_classes.py)  
**Purpose**: Fetch D&D 2024 wiki pages and store them locally

### What It Does

1. Fetches all class pages (e.g., `wizard:main`, `fighter:main`)
2. Fetches all subclass pages (e.g., `wizard:evoker`, `fighter:battle-master`)
3. Extracts both plain text and HTML from each page
4. Saves to `wiki_data/` with metadata (URL, timestamp)
5. Respects rate limits (1 second delay between requests)

### Running Stage 1

```bash
python update_classes.py
```

**Output**: `wiki_data/` directory populated with JSON files containing raw wiki content

**When to Run**:
- Initial setup (first time)
- After D&D 2024 errata/updates
- When adding new classes/subclasses
- Periodically to stay current

## Stage 2: Transform & Structure

**Script**: To be created (e.g., `transform_wiki_data.py`)  
**Purpose**: Convert cached wiki data into application-ready JSON files

### What It Should Do

1. Read from `wiki_data/` cache files
2. Parse text/HTML to extract:
   - Features by level
   - Spell slots progression
   - Proficiencies and bonuses
   - Subclass-specific abilities
3. Structure into application JSON schema
4. Write to `data/classes/` and `data/subclasses/`

### Example Transformation

```python
# Read cached wiki data
wiki_data = load_json('wiki_data/classes/wizard.json')

# Parse features from text
features = parse_features(wiki_data['content']['text'])

# Structure for application
class_data = {
    "name": "Wizard",
    "hit_die": "d6",
    "spellcasting_ability": "Intelligence",
    "features_by_level": {
        "1": ["Spellcasting", "Ritual Adept", "Arcane Recovery"],
        "2": ["Scholar"],
        # ... etc
    },
    "spell_slots_by_level": {
        "1": [2, 0, 0, 0, 0, 0, 0, 0, 0],
        "2": [3, 0, 0, 0, 0, 0, 0, 0, 0],
        # ... etc
    }
}

# Write to application data directory
save_json('data/classes/wizard.json', class_data)
```

## Benefits of Two-Stage Approach

### 1. **Separation of Concerns**
- **Stage 1**: Web scraping and caching (external dependency)
- **Stage 2**: Data transformation (internal logic)

### 2. **Format Flexibility**
- Change application data format without re-scraping wiki
- Experiment with different data structures
- Support multiple output formats (JSON, XML, etc.)

### 3. **Reliability**
- Wiki scraping can fail (network issues, site changes)
- Transformation logic can be tested/refined independently
- Cached data acts as a stable intermediate layer

### 4. **Development Speed**
- Test transformation logic on cached data instantly
- No need to wait for network requests during development
- Run transformations multiple times without hitting the wiki

### 5. **Version Control**
- Track when wiki content changes (via `fetched_at` timestamps)
- Review diffs in cached data to see rule changes
- Regenerate application data from any historical cache

## Workflow Examples

### Initial Project Setup

```bash
# 1. Fetch all wiki data
python update_classes.py

# 2. Transform to application format
python transform_wiki_data.py

# 3. Application ready to use
python app.py
```

### After D&D 2024 Errata

```bash
# 1. Re-fetch affected pages
python update_classes.py  # Updates all pages with new timestamps

# 2. Review changes
git diff wiki_data/

# 3. Re-transform to application format
python transform_wiki_data.py

# 4. Review application data changes
git diff data/
```

### Changing Data Format

```bash
# No need to re-fetch! Just modify transformation logic

# 1. Update transformation script
vim transform_wiki_data.py

# 2. Re-run transformation
python transform_wiki_data.py

# 3. Test new format
python app.py
```

## File Organization

```
dnd-character-creator/
├── update_classes.py           # Stage 1: Fetch & cache wiki data
├── transform_wiki_data.py      # Stage 2: Transform cache → app data
│
├── wiki_data/                  # Stage 1 output (git tracked)
│   ├── README.md
│   ├── classes/
│   │   ├── wizard.json         # Raw wiki content
│   │   └── ...
│   └── subclasses/
│       ├── wizard/
│       │   ├── evoker.json
│       │   └── ...
│       └── ...
│
├── data/                       # Stage 2 output (git tracked)
│   ├── classes/
│   │   ├── wizard.json         # Structured app data
│   │   └── ...
│   └── subclasses/
│       ├── wizard/
│       │   ├── evoker.json
│       │   └── ...
│       └── ...
│
└── app.py                      # Application (reads from data/)
```

## Next Steps

1. ✅ **Stage 1 Complete**: `update_classes.py` fetches and caches wiki data
2. ⏳ **Stage 2 TODO**: Create `transform_wiki_data.py` to parse and structure data
3. ⏳ **Automation**: Consider CI/CD to auto-update when wiki changes

## Implementation Notes

### Stage 1 (update_classes.py)
- ✅ Fetches from dnd2024.wikidot.com
- ✅ Saves to `wiki_data/` with timestamps
- ✅ Handles both classes and subclasses
- ✅ Rate limiting (1 sec between requests)
- ✅ Error handling and reporting

### Stage 2 (transform_wiki_data.py) - TODO
- Parse text content to extract features
- Identify level progression patterns
- Extract spell slot tables
- Handle class-specific mechanics
- Generate clean, structured JSON
- Validate against application schema

## Maintenance

- **Weekly**: Quick check for D&D 2024 updates
- **Monthly**: Full re-fetch to catch any changes
- **On Errata**: Immediate re-fetch and review diffs
- **On Format Change**: Re-run transformations with new logic
