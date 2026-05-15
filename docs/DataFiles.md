# Data Files

All game content lives as **plain JSON** under `data/`. Schemas are in `models/`. There is no code generation: adding a class, subclass, species, background, feat or spell means editing JSON.

## Top-Level Layout

```
data/
├── classes/                   # 12 class files
├── subclasses/                # one folder per class
│   └── <class>/
├── species/                   # 10 species files
├── species_variants/          # 8 lineage / variant files
├── backgrounds/               # 18 background files
├── equipment/                 # weapons, armor, gear, masteries
├── spells/
│   ├── class_lists/           # 8 spellcasting-class lists
│   └── definitions/           # ~383 individual spell definitions
├── completeness/
│   └── backlog.json           # tracked content gaps
├── fighting_styles.json       # reference: all fighting styles
├── eldritch_invocations.json  # reference: all warlock invocations
├── origin_feats.json          # reference: origin feats catalogue
├── general_feats.json         # reference: general feats catalogue
├── trait_patterns.json        # reference: shared trait shapes
├── character_sheet_model.json # reference: character export model
└── example_complete_character.json
```

## Categories

### Classes (`data/classes/`)

12 files, one per class:

```
barbarian.json   bard.json     cleric.json     druid.json
fighter.json     monk.json     paladin.json    ranger.json
rogue.json       sorcerer.json warlock.json    wizard.json
```

Validated against [models/class_schema.json](../models/class_schema.json). Required fields include `name`, `hit_die`, `primary_ability`, `saving_throw_proficiencies`, `armor_proficiencies`, `weapon_proficiencies`, `subclass_selection_level`, `features_by_level`, and (where applicable) `spell_slots_by_level`.

`features_by_level` is **always an object of `{ feature_name: description }`**, never an array. See [.github/instructions/data-schemas.instructions.md](../.github/instructions/data-schemas.instructions.md).

### Subclasses (`data/subclasses/<class>/`)

One folder per class, one file per subclass within. Validated against [models/subclass_schema.json](../models/subclass_schema.json). Same `features_by_level` rule applies.

### Species (`data/species/`)

10 files:

```
aasimar.json   dragonborn.json  dwarf.json   elf.json    gnome.json
goliath.json   halfling.json    human.json   orc.json    tiefling.json
```

Each species defines `traits`, `creature_type`, `size`, `speed`, optional `darkvision`, and either a list or map of `lineages`.

### Species variants / lineages (`data/species_variants/`)

8 files for lineage detail (description, traits, etc.) referenced by parent species:

```
abyssal_tiefling.json   chthonic_tiefling.json   drow.json
forest_gnome.json       high_elf.json            infernal_tiefling.json
rock_gnome.json         wood_elf.json
```

The catalog endpoint normalises these into a uniform `{ id, name, description, traits }` shape via `_enrich_lineages` in [routes/api/character.py](../routes/api/character.py).

### Backgrounds (`data/backgrounds/`)

18 files. In D&D 2024 every background grants an origin feat and ASI options — both are encoded here.

### Equipment (`data/equipment/`)

| File                    | Contents                                       |
|-------------------------|------------------------------------------------|
| `weapons.json`          | All weapons. Authoritative source for "is X a weapon?" — never hardcode lists in Python. |
| `armor.json`            | All armor (light, medium, heavy, shields).     |
| `adventuring_gear.json` | Gear, packs, tools, kits.                      |
| `weapon_masteries.json` | Mastery property definitions.                  |

### Spells (`data/spells/`)

```
data/spells/
├── class_lists/   # 8 files: bard, cleric, druid, paladin, ranger, sorcerer, warlock, wizard
└── definitions/   # ~383 individual spell JSON files (slug-named)
```

Class lists hold `{ class, cantrips: [...], spells_by_level: { "1": [...], "2": [...] } }`. Definitions hold the full mechanical text for each spell.

### Reference files (top level)

| File                          | Contents                                                              |
|-------------------------------|-----------------------------------------------------------------------|
| `fighting_styles.json`        | All fighting styles, their effects.                                   |
| `eldritch_invocations.json`   | All warlock invocations, prerequisites, effects.                      |
| `origin_feats.json`           | Origin feats granted by 2024 backgrounds.                             |
| `general_feats.json`          | General feats available at level 4+.                                  |
| `trait_patterns.json`         | Shared trait shape templates referenced by species traits.            |
| `character_sheet_model.json`  | Reference model used when exporting a complete character.             |
| `example_complete_character.json` | A worked example — handy for tests and inspection.                |

Served by `GET /api/v1/catalog/reference/<name>` (allowed names: `fighting_styles`, `eldritch_invocations`, `origin_feats`, `general_feats`, `trait_patterns`).

### Completeness tracking (`data/completeness/`)

| File             | Contents                                         |
|------------------|--------------------------------------------------|
| `backlog.json`   | Known content gaps tracked outside GitHub Issues |

## Schemas (`models/`)

| File                              | Status        | Used by                               |
|-----------------------------------|---------------|---------------------------------------|
| `class_schema.json`               | Active        | `validate_data.py`, content reviewers |
| `subclass_schema.json`            | Active        | `validate_data.py`, content reviewers |
| `character_sheet_v2_schema.json`  | **Aspirational** — no producer or consumer was found in the codebase. Document the intended shape but do not assume any code reads or emits it today. |
| `example_character_v2.json`       | Reference     | Companion example for the v2 schema   |
| `README.md`                       | Schema notes  | Reference                             |

Run `python validate_data.py` to validate `data/` against the active schemas.

## Wiki Generation Pipeline

Three updater scripts pull from `http://dnd2024.wikidot.com/` and cache results locally. **They are not symmetrical.**

| Script              | Reads                                  | Writes to                                                | Notes |
|---------------------|----------------------------------------|----------------------------------------------------------|-------|
| `update_classes.py` | Wiki class + subclass pages            | **`wiki_data/classes/`** and **`wiki_data/subclasses/<class>/`** | Cache only. Prints: *"Create a separate script to transform `wiki_data → data/`"*. The application-ready `data/classes/<n>.json` and `data/subclasses/<class>/<sub>.json` are **hand-authored** from the cache. |
| `update_species.py` | Wiki species pages                     | **`wiki_data/species/`**                                  | Cache only. Same pattern as classes. Application-ready `data/species/<n>.json` and `data/species_variants/<v>.json` are hand-authored. |
| `update_spells.py`  | Wiki class spell-list pages            | **`data/spells/class_lists/<class>.json` directly**       | **Asymmetry — writes straight into `data/`.** Three `write_text` calls in the script bypass `wiki_data/` entirely. There is no transform step for spell lists. |

### The spell-fetcher asymmetry — what it means in practice

- Re-running `update_spells.py --class wizard` will **overwrite `data/spells/class_lists/wizard.json` in place** (only with `--overwrite`, but still in the production data tree). Diff before committing.
- There is no parallel cache, so any manual edits to a class spell list are lost on re-fetch.
- `data/spells/definitions/*.json` (~383 files) has **no fetcher at all** — every individual spell is hand-authored.
- A future cleanup should either (a) align `update_spells.py` with the `update_classes.py` / `update_species.py` pattern (write to `wiki_data/spells/` and add a transform), or (b) decide explicitly that spell lists are wiki-mirrored and document that the application-ready file *is* the cache.

## Loading Data at Runtime

`modules/data_loader.py` provides `DataLoader(data_dir=...)` which lazily loads:

- `classes`, `subclasses` (per class), `species`, `backgrounds`, `feats`
- Equipment files via direct path access (`data/equipment/<kind>.json`)
- Spell lists / definitions via direct path access

The catalog and character endpoints share a single `DataLoader` instance; previewers re-instantiate it with the absolute `data/` path because they need to read fresh data without polluting the app-level cache.

## Adding Content

Generic procedure:

1. Verify the rule against D&D 2024 (use `wiki_data/` cache or fetch from `http://dnd2024.wikidot.com/`).
2. Add or update the JSON file in the relevant `data/` subfolder.
3. Encode mechanical benefits as `effects` arrays — never hardcode in Python. See [docs/FEATURE_EFFECTS.md](FEATURE_EFFECTS.md) and [.github/instructions/effects-system.instructions.md](../.github/instructions/effects-system.instructions.md).
4. Run `python validate_data.py`.
5. Add or update tests under `tests/`.

For batch additions, the `add-game-content` and `implement-class-feature` skills automate steps 1–5.

## See Also

- [docs/Architecture.md](Architecture.md)
- [docs/APIContract.md](APIContract.md)
- [docs/FEATURE_EFFECTS.md](FEATURE_EFFECTS.md)
- [.github/instructions/data-schemas.instructions.md](../.github/instructions/data-schemas.instructions.md)
- [.github/instructions/effects-system.instructions.md](../.github/instructions/effects-system.instructions.md)
