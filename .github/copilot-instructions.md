# Copilot Instructions for D&D 2024 Character Creator

## Core Principles

### 1. Effects System — NEVER Hardcode
**NEVER hardcode specific feature names or species names in application logic.**
All mechanical benefits are defined as structured `effects` arrays in JSON data files and applied generically through `CharacterBuilder._apply_effect()`. Check `effect['type']`, never `feature_name == '...'`.
See `.github/instructions/effects-system.instructions.md` and `docs/FEATURE_EFFECTS.md` for the full catalog.

### 2. Single Source of Truth — CharacterBuilder
`CharacterBuilder` is the ONLY place where character calculations happen.
- The REST API (`/api/v1/character/build`) calls `builder.to_character()` and returns the result as JSON
- The React SPA (`frontend/`) is a pure consumer of that calculated dict — no calculations in TypeScript components
- The legacy Jinja UI (under `/legacy/*`) also only displays — no calculations in templates or legacy routes
- JSON export, HTML/PDF sheets, SPA views, and API responses all use the same calculated dict

### 3. D&D 2024 Edition Compliance
- **ALWAYS** verify rules come from D&D 2024 (One D&D), not 2014
- Species no longer have ability score increases (moved to backgrounds)
- Dwarf variants (Hill/Mountain) don't exist in 2024
- When in doubt, check `wiki_data/` cache or fetch from http://dnd2024.wikidot.com/

### 4. Data-Driven Design
**NEVER hardcode lists of game content.** Check against data files instead.
- Weapon detection checks `weapons.json`, not keyword lists
- All game data (classes, species, spells, feats) lives in `data/` as JSON
- Adding content means updating data files, not code

### 5. Schema Compliance
All data files MUST comply with schemas in `models/` directory.
- `features_by_level` maps level (string) → **OBJECT** of feature_name → description
- ❌ NEVER arrays: `"1": ["Feature1"]` — ✅ ALWAYS objects: `"1": {"Feature1": "Description"}`
See `.github/instructions/data-schemas.instructions.md` for full schemas.

## Data Sources Priority

1. `data/` — Application-ready structured JSON (primary)
2. `wiki_data/` — Cached wiki content with `content.text` and `content.html` fields
3. http://dnd2024.wikidot.com/ — Live wiki (only when cache is missing)

Use `update_classes.py --class <name>` or `update_species.py --species <name>` to fetch/cache wiki data.
Use `update_spells.py --class <name>` to fetch spell lists (cantrips + leveled spells) for a class.

## Architecture Overview

```
modules/character_builder.py  # ALL calculations — single source of truth
modules/ability_scores.py     # Ability score management
modules/feature_manager.py    # Feature tracking and effects application
modules/hp_calculator.py      # Hit point calculations
modules/variant_manager.py    # Species variant (lineage) system
modules/data_loader.py        # JSON data file loading
modules/equipment_manager.py  # Equipment tracking
modules/derived_stats.py      # Stateless view helpers reused by REST + legacy

routes/api/                   # REST API v1 (/api/v1/*) — stateless, JSON, primary surface
routes/                       # Legacy Jinja routes — mounted under /legacy/* for comparison
templates/                    # Legacy Jinja templates — display only, no calculations
frontend/                     # React + Vite + TypeScript SPA (the new UI)
  src/lib/api.ts              # Typed client for /api/v1
  src/store/                  # Zustand stores (character + roster)
  src/features/               # Wizard step components, sheet, PDF view
data/                         # Game content JSON files
models/                       # JSON Schema definitions
```

In production Flask serves the built SPA from `frontend/dist/` at `/`,
the REST API at `/api/v1/*`, and the legacy UI at `/legacy/*`. The
legacy UI is kept as a side-by-side comparison surface and will be
removed in a future phase.

## Scoped Instructions

Domain-specific guidance has been moved to focused instruction files that load only when relevant:
- `.github/instructions/effects-system.instructions.md` — Effect types, JSON shapes, rules
- `.github/instructions/data-schemas.instructions.md` — Class, subclass, species, background schemas
- `.github/instructions/choice-reference.instructions.md` — Choice Reference System
- `.github/instructions/testing.instructions.md` — Pytest conventions and patterns
- `.github/instructions/flask-routes.instructions.md` — Route patterns and session management

## Development Checklist

When implementing any feature:
1. Verify it exists in D&D 2024 (not 2014)
2. Define effects in JSON data files (never hardcode)
3. Implement generic handler if new effect type needed
4. Validate data against schema (`python validate_data.py`)
5. Write tests (`pytest tests/`)

## Issue Tracking

Known bugs and missing features are tracked as GitHub Issues on `QuickNS/dnd-character-creator`.
Issue titles follow the format `[Category] Short description` (e.g., `[Monk]`, `[Elf]`, `[Monk/Warrior of Shadow]`) with `bug` or `enhancement` labels.
Use GitHub MCP tools (`mcp_github_list_issues`, `mcp_github_search_issues`) to find open issues.
When the user reports a bug or missing feature conversationally, use the `file-issue` skill to create a structured GitHub Issue.
When fixing issues, use the `fix-issue` skill for the full workflow (covers classes, species, feats, backgrounds, spells, and application issues).