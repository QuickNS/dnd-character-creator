---
name: update-backlog
description: "Scan the data/ directory and update data/completeness/backlog.json with current implementation status. Use when checking project completeness or after adding new content."
---

# Update Backlog

Scans the `data/` directory and updates the machine-readable backlog to reflect current implementation status.

## When to Use

- After adding new data files to track their status
- Before planning the next batch of work
- When asked "what's missing?" or "what should I work on next?"

## Procedure

### 1. Scan Data Directory

Check what files exist:

```bash
# Classes
ls data/classes/

# Subclasses per class
for class in data/subclasses/*/; do echo "$(basename $class): $(ls $class | wc -l) subclasses"; done

# Species
ls data/species/

# Backgrounds
ls data/backgrounds/

# Spell definitions
ls data/spells/definitions/ | wc -l

# Spell class lists
ls data/spells/class_lists/
```

### 2. Check Expected Content

D&D 2024 expected content:
- **12 classes**: Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard
- **4 subclasses each** (48 total)
- **10 species**: Aasimar, Dragonborn, Dwarf, Elf, Gnome, Goliath, Halfling, Human, Orc, Tiefling
- **16 backgrounds**: Acolyte, Artisan, Charlatan, Criminal, Entertainer, Farmer, Folk Hero, Guard, Guide, Guild Artisan, Hermit, Merchant, Noble, Sage, Sailor, Scribe, Soldier, Wayfarer
- **10 origin feats, 44 general feats**

### 3. Check Feature Completeness

For each data file that exists, check:
- Does it have `features_by_level` with content? → `features_validated`
- Do features with mechanical benefits have `effects` arrays? → `effects_implemented`
- Are there tests covering this content? → `tests_written`

### 4. Update backlog.json

Update `data/completeness/backlog.json` with findings. Set boolean flags:
- `data_file`: Does the JSON file exist?
- `features_validated`: Are all features present and described?
- `effects_implemented`: Do mechanical features have `effects` arrays?
- `tests_written`: Are there tests for this content?

**Preserve existing fields** — do NOT overwrite or remove any extra keys in class entries. Only set `features_validated` / `effects_implemented` to `true` if the data has been fully verified.

### 5. Generate Summary

Print a human-readable summary:

```
=== Content Completeness ===
Classes:     12/12 files (3/12 fully validated)
Subclasses:  46/48 files (4/48 fully validated)
Species:     10/10 files (10/10 fully validated)
Backgrounds: 10/16 files (0/16 fully validated)
Feats:       8/54 files
Spells:      35/??? definitions
```

For open issues, check GitHub:
```
mcp_github_list_issues(owner="QuickNS", repo="dnd-character-creator", state="OPEN")
```
