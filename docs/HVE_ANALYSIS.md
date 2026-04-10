# HVE (Highly Valuable Experience) Implementation Analysis

This document analyzes the GitHub Copilot customization infrastructure ("HVE") in the D&D 2024 Character Creator project. It covers every entry point, artifact type, and their interconnections.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Entry Points](#entry-points)
3. [Instructions (`.instructions.md`)](#instructions)
4. [Skills (`SKILL.md`)](#skills)
5. [Agents (`.agent.md`)](#agents)
6. [Prompts (`.prompt.md`)](#prompts)
7. [Hooks (`.json`)](#hooks)
8. [Setup Steps (`copilot-setup-steps.yml`)](#setup-steps)
9. [Reference Files](#reference-files)
10. [Interaction Map](#interaction-map)
11. [Prompts vs Skills — Overlap Analysis](#prompts-vs-skills--overlap-analysis)
12. [Common Tasks](#common-tasks)

---

## Architecture Overview

The project uses a layered Copilot customization system under `.github/` that directs AI assistants to follow domain-specific rules, use data-driven patterns, and maintain quality gates automatically. The system is designed around the principle that **all game content is data, not code**, and AI agents should respect strict separation of concerns.

```
.github/
├── copilot-instructions.md              # Global entry point (always loaded)
├── copilot-setup-steps.yml              # Environment bootstrap for coding agent
├── instructions/                         # Scoped instructions (loaded contextually)
│   ├── choice-reference.instructions.md
│   ├── data-schemas.instructions.md
│   ├── effects-system.instructions.md
│   ├── flask-routes.instructions.md
│   └── testing.instructions.md
├── skills/                               # Complex multi-step workflows
│   ├── add-game-content/SKILL.md
│   ├── file-issue/SKILL.md
│   ├── fix-issue/SKILL.md
│   ├── implement-class-feature/SKILL.md
│   ├── update-backlog/SKILL.md
│   └── validate-character/SKILL.md
├── agents/                               # Specialized agent personas
│   ├── data-author.agent.md
│   ├── data-validator.agent.md
│   ├── feature-implementer.agent.md
│   ├── test-writer.agent.md
│   └── wiki-fetcher.agent.md
├── prompts/                              # Reusable prompt templates
│   ├── add-data-files.prompt.md
│   ├── batch-implement.prompt.md
│   ├── check-data-files.prompt.md
│   ├── cleanup-project.prompt.md
│   ├── implement-class.prompt.md
│   ├── implement-species.prompt.md
│   └── next-task.prompt.md
└── hooks/                                # Automated post-edit quality gates
    ├── post-edit-data.json
    └── post-edit-python.json
```

---

## Entry Points

### 1. `copilot-instructions.md` — Global Instructions (Always Active)

**File:** `.github/copilot-instructions.md`

This is the root customization file, **loaded automatically into every Copilot conversation** within this workspace. It establishes:

- **5 Core Principles:**
  1. **Effects System** — Never hardcode feature/species names; use generic `effects` arrays
  2. **Single Source of Truth** — `CharacterBuilder` is the only place calculations happen
  3. **D&D 2024 Compliance** — Always verify rules are from 2024, not 2014
  4. **Data-Driven Design** — Never hardcode lists of game content
  5. **Schema Compliance** — All data files must pass `validate_data.py`
- **Data Source Priority:** `data/` → `wiki_data/` → live wiki
- **Architecture Overview:** Module responsibilities and separation of concerns
- **Development Checklist:** Steps every feature implementation must follow
- **Issue Tracking:** Convention for GitHub Issues and linking to skills

**Purpose:** Sets the ground rules so that every AI interaction respects the project's architecture, regardless of which specific task is being performed.

### 2. `copilot-setup-steps.yml` — Coding Agent Bootstrap

**File:** `.github/copilot-setup-steps.yml`

Runs automatically when the **GitHub Copilot Coding Agent** (the cloud-based agent that picks up GitHub Issues) starts working on an issue. Installs dependencies and validates the environment is healthy before making changes:

```yaml
steps:
  - pip install -r requirements.txt
  - pip install pytest
  - python validate_data.py
  - pytest tests/ -x -q --tb=short
```

**Purpose:** Ensures the Copilot coding agent (which runs in cloud containers) has a working environment before attempting any fix.

---

## Instructions

Instructions are **contextually-loaded** files that activate based on `applyTo` glob patterns — they only appear in the AI's context when relevant files are being discussed or edited.

### `effects-system.instructions.md`
- **Triggers on:** `data/**/*.json`, `modules/character_builder.py`, `modules/feature_manager.py`, `FEATURE_EFFECTS.md`
- **Purpose:** Documents the complete effects system — the cardinal rule of never hardcoding, the JSON shape for effects, a quick-reference table of all ~25 effect types, spell granting format, condition strings for bonuses, and the procedure for adding new effect types.
- **Key content:** Effect type table (grant_cantrip, grant_spell, bonus_hp, bonus_ac, etc.), spell storage destinations, condition string mappings.

### `data-schemas.instructions.md`
- **Triggers on:** `data/**/*.json`
- **Purpose:** Documents the exact schema for every data file type — classes, subclasses, species, backgrounds, and spells. Especially enforces that `features_by_level` must use **objects** (never arrays), which is a critical and easily violated constraint.
- **Key content:** Required/optional fields per schema, the critical `features_by_level` format, ability_score_increase structure for backgrounds.

### `choice-reference.instructions.md`
- **Triggers on:** `data/**/*.json`, `modules/character_builder.py`
- **Purpose:** Documents the declarative choice system — how player decisions (spell selection, feat picks, fighting styles, maneuver choices) are defined in JSON and resolved at runtime. Covers source types (`internal`, `external`, `external_dynamic`, `fixed_list`), level progression via `additional_choices_by_level`, and restrictions.
- **Key content:** Choice object schema, source type table, worked examples for maneuvers/fighting styles/Magic Initiate.

### `testing.instructions.md`
- **Triggers on:** `tests/**/*.py`
- **Purpose:** Establishes pytest conventions — test directory structure, how to build characters in tests (always via `CharacterBuilder`), the stateless API testing pattern, assertion patterns for effects/proficiencies/spells/combat stats, naming conventions, and common fixtures.
- **Key content:** Character building pattern, assertion idioms, fixture templates, run commands.

### `flask-routes.instructions.md`
- **Triggers on:** `routes/**/*.py`
- **Purpose:** Documents the Flask route pattern — every route follows get-builder → apply-choice → calculate → render. Critical rules: no calculations in routes or templates, always use session helpers, always save after mutation.
- **Key content:** Route handler template, session helper imports, API endpoint pattern, blueprint registration.

---

## Skills

Skills are **complex, multi-step workflows** invoked when the user's request matches the skill description. The AI reads the `SKILL.md` file before executing, getting a detailed procedure to follow.

### `implement-class-feature`
- **When:** Adding a class/subclass feature with mechanical effects, or adding a new effect type.
- **Procedure:** Verify wiki source → identify effect types from catalog → update data JSON → validate schema → implement effect handler if needed → write tests → run full suite.
- **Reference files:** Includes `references/effect-type-catalog.md` (quick-reference for all effect types) for mapping game mechanics to effect JSON.

### `fix-issue`
- **When:** Resolving a GitHub Issue (bug, missing feature, inaccuracy).
- **Procedure:** Find open issues via MCP → read issue → classify category → create feature branch → verify against wiki source of truth → apply fix → validate → write regression test → commit/push → create PR → wait for user confirmation → merge and close.
- **Key feature:** Full git workflow with branch management and PR creation. Includes a category table mapping issue types to data files, wiki sources, and validation steps.

### `file-issue`
- **When:** User casually describes a bug or missing feature.
- **Procedure:** Parse user description → gather codebase context → check for duplicate issues → determine labels → create structured GitHub Issue → assign Copilot coding agent.
- **Key feature:** Converts informal bug reports into structured issues with severity, affected files, reproduction steps, and auto-assigns the Copilot coding agent for autonomous fixing.

### `add-game-content`
- **When:** Populating a batch of game content (e.g., all subclasses for a class, missing backgrounds).
- **Procedure:** Check backlog → fetch wiki data → create data files from templates → add effects → validate → write tests → update backlog → run full suite.
- **Reference files:** Includes `references/data-file-templates.md` with blank JSON templates for classes, subclasses, species, backgrounds, spells, and feats.

### `validate-character`
- **When:** Verifying a character build produces correct calculated values after changes.
- **Procedure:** Choose/create character choices → build via API or CharacterBuilder → verify HP, proficiencies, effects, spells, skills → compare with reference builds → report pass/fail.
- **Reference characters:** `test_characters/test_cleric_dwarf.json`, `test_characters/test_figher_wood_elf.json`.

### `update-backlog`
- **When:** Checking project completeness or after adding new content.
- **Procedure:** Scan `data/` directory → check against expected D&D 2024 content list (12 classes, 48 subclasses, 10 species, 16 backgrounds, 54 feats) → verify feature completeness → update `data/completeness/backlog.json` → generate human-readable summary.

---

## Agents

Agents are **specialized personas** with constrained tool access and strict boundaries on what files they may modify. They are invoked via `runSubagent` and can be chained in pipelines.

### `data-author`
- **Scope:** Create/edit JSON files under `data/` only
- **Cannot touch:** Python code, test files
- **Tools:** read, edit, search, web
- **Purpose:** Writes game data JSON following schemas and effects system. Verifies against wiki sources.
- **Workflow:** Read schema → check wiki cache → create/update JSON → run `validate_data.py`

### `feature-implementer`
- **Scope:** Modify Python files in `modules/`, `utils/`, `routes/` only
- **Cannot touch:** JSON data files, test files
- **Tools:** read, edit, search, execute
- **Purpose:** Implements effect handlers in `CharacterBuilder._apply_effect()`, calculation methods, and application logic. Follows the generic processing rule (never hardcode).

### `test-writer`
- **Scope:** Create/edit files in `tests/` only
- **Cannot touch:** Production code, data files
- **Tools:** read, edit, search, execute
- **Purpose:** Writes pytest tests following project conventions. Uses `CharacterBuilder` directly and the stateless API endpoint.

### `data-validator`
- **Scope:** Read-only — produces reports but does NOT modify files
- **Tools:** read, search, execute
- **Purpose:** Audits data file integrity, schema compliance, D&D 2024 accuracy, and effects coverage. Produces structured pass/fail reports with completeness percentages.

### `wiki-fetcher`
- **Scope:** Only update files in `wiki_data/` or run fetcher scripts
- **Cannot touch:** `data/` files, Python source code
- **Tools:** read, edit, search, web, execute
- **Purpose:** Ensures the wiki data cache is up-to-date. Runs `update_classes.py` / `update_species.py` or fetches directly from `http://dnd2024.wikidot.com/`.

### Agent Chaining

The agents are designed to be composed in pipelines. The standard chain is:

```
wiki-fetcher → data-author → data-validator → feature-implementer → test-writer
```

Each agent handles one concern and passes the baton to the next.

---

## Prompts

Prompts are **reusable prompt templates** (`.prompt.md` files) that can be invoked by name. Some use template variables (e.g., `{{ class_name }}`) that get filled at invocation time.

### `implement-class.prompt.md`
- **Variable:** `{{ class_name }}`
- **Purpose:** Thin launcher for end-to-end class implementation. Delegates the core workflow to the `implement-class-feature` and `add-game-content` skills, and adds git branch management + PR creation/merge on top.

### `implement-species.prompt.md`
- **Variable:** `{{ species_name }}`
- **Purpose:** Thin launcher for species implementation. Delegates to the `implement-class-feature` skill (adapted for species) and reminds about D&D 2024 species rules.

### `add-data-files.prompt.md`
- **Variable:** `{{ class_name }}`
- **Agent:** `agent` (general agent mode)
- **Purpose:** Thin launcher that delegates to the `add-game-content` skill for generating class and subclass data files.

### `batch-implement.prompt.md`
- **Variables:** `{{ content_category }}`, `{{ scope }}`
- **Purpose:** Thin launcher for parallel content implementation. Delegates each item to the `add-game-content` skill after resolving shared dependencies via `implement-class-feature`.

### `next-task.prompt.md`
- **Purpose:** Thin launcher that delegates backlog scanning to the `update-backlog` skill, then applies a priority ordering to select the next task. Outputs a work plan referencing which skills to use.

### `check-data-files.prompt.md`
- **Agent:** `agent` (general agent mode)
- **Purpose:** Audits all data files against their schemas. Fixes simple issues automatically; describes complex ones. Generates a `data-file-report.md` with findings.

### `cleanup-project.prompt.md`
- **Agent:** `agent` (general agent mode)
- **Purpose:** Removes legacy code from the old character state management approach. Finds and removes direct `session['character']` access, manual character dicts, dual-save compatibility code. Ensures clean `CharacterBuilder`-based architecture.

---

## Hooks

Hooks run **automatically after Copilot edits files**, providing continuous quality gates without manual intervention.

### `post-edit-python.json`
- **Trigger:** After any Python file edit (PostToolUse)
- **Action:** `python -m pytest tests/ -x -q --tb=line 2>&1 | tail -5`
- **Timeout:** 60 seconds
- **Purpose:** Catches test regressions immediately after any code change. Shows only the last 5 lines (pass/fail summary).

### `post-edit-data.json`
- **Trigger:** After any data file edit (PostToolUse)
- **Action:** `python validate_data.py 2>&1 | grep -c '❌' | xargs -I{} test {} -eq 0`
- **Timeout:** 15 seconds
- **Purpose:** Validates JSON data files against their schemas immediately after editing. Fails silently (exit code) if any schema violations are detected, signaling the AI to fix them.

---

## Setup Steps

### `copilot-setup-steps.yml`

Runs when the **Copilot Coding Agent** (the autonomous GitHub agent that picks up issues labeled `copilot`) starts a cloud session:

1. Install Python dependencies from `requirements.txt`
2. Install pytest
3. Run `validate_data.py` — confirms all data files are schema-compliant
4. Run `pytest tests/` — confirms the test suite passes

**Purpose:** Ensures the coding agent starts from a known-good state before making changes.

---

## Reference Files

Supporting documents that skills and instructions link to:

| File | Used By | Content |
|---|---|---|
| `skills/add-game-content/references/data-file-templates.md` | add-game-content skill | Blank JSON templates for all data file types |
| `skills/implement-class-feature/references/effect-type-catalog.md` | implement-class-feature skill | Quick-reference table of all effect types grouped by category |
| `FEATURE_EFFECTS.md` (repo root) | effects-system instruction, multiple agents | Canonical documentation of all effect types with examples |
| `data/completeness/backlog.json` | update-backlog skill, next-task prompt | Machine-readable tracking of implementation completeness |
| `models/class_schema.json`, `models/subclass_schema.json` | data-schemas instruction, data-validator agent | JSON Schema definitions for validation |

---

## Interaction Map

How the components connect and when they activate:

```
User Request
    │
    ├──[always]──► copilot-instructions.md (core principles)
    │
    ├──[editing data/*.json]──► data-schemas.instructions.md
    │                          effects-system.instructions.md
    │                          choice-reference.instructions.md
    │
    ├──[editing tests/**]──► testing.instructions.md
    │
    ├──[editing routes/**]──► flask-routes.instructions.md
    │
    ├──[reports a bug]──► file-issue skill
    │                      └── creates GitHub Issue ──► Copilot coding agent
    │                                                    └── copilot-setup-steps.yml
    │
    ├──["fix issue #N"]──► fix-issue skill
    │                       └── agent chain: wiki-fetcher → data-author → feature-implementer → test-writer
    │
    ├──["implement Ranger"]──► implement-class.prompt.md
    │                           └── full agent chain + branch/PR management
    │
    ├──["what's next?"]──► next-task.prompt.md
    │                       └── reads backlog.json → generates work plan
    │
    └──[after any edit]──► hooks
                            ├── Python edit → run pytest
                            └── Data edit → run validate_data.py
```

---

## Prompts vs Skills — Overlap Analysis

Prompts and skills serve different invocation models but in this project have significant content duplication.

### How They Differ

| | **Prompts** (`.prompt.md`) | **Skills** (`SKILL.md`) |
|---|---|---|
| **Invocation** | Explicit — user picks from a menu (slash command / `#` picker in VS Code) | Implicit — AI auto-detects from the user's natural language request matching the skill `description` |
| **Content model** | A text template injected into the conversation as-is | A procedure document the AI reads first, then executes step-by-step |
| **Variables** | Support `{{ template_vars }}` filled at invocation time | No template variables — context comes from the conversation |
| **Typical shape** | "Do X for {{ thing }}" — a directive | "When you encounter Y, follow these steps" — a workflow |

In short: **prompts are buttons you press**, **skills are behaviors the AI learns**.

### Identified Redundancy

| Prompt | Overlapping Skill | Nature of Overlap |
|---|---|---|
| `implement-class.prompt.md` | `implement-class-feature` + `add-game-content` | Both describe the wiki→data→validate→implement→test pipeline. The prompt adds git branching/PR on top. |
| `implement-species.prompt.md` | `implement-class-feature` (adapted) | Same agent chain, just for species instead of classes. |
| `batch-implement.prompt.md` | `add-game-content` | Nearly identical scope — both describe adding batches of content with the same agent chain. |
| `add-data-files.prompt.md` | `add-game-content` | The prompt is a simpler version of what the skill already describes. |
| `next-task.prompt.md` | `update-backlog` | Both read `backlog.json`; the prompt picks the next task, the skill updates completeness — complementary but the backlog-reading logic is duplicated. |

### Non-Redundant Components

These skills have **no prompt equivalent** and are triggered purely by conversational context:

- **`file-issue`** — Converts casual bug reports into structured GitHub Issues
- **`fix-issue`** — End-to-end issue resolution with git workflow
- **`validate-character`** — Character build verification

These prompts have **no skill equivalent** and serve unique purposes:

- **`check-data-files`** — Schema audit with auto-fix (uses general `agent` mode)
- **`cleanup-project`** — Legacy code removal (one-time architectural task)

### Root Cause

The prompts were written as **explicit orchestration recipes** ("run these agents in this order for class X"), while the skills evolved as **implicit behavioral guides** ("when the user needs game content added, follow this procedure"). Over time they converged on describing the same wiki→data→validate→test workflow from different angles. The prompts also embed git/PR management that the skills don't, creating a slightly different scope but mostly overlapping core procedures.

### Applied Resolution

The 5 redundant prompts have been slimmed down to **thin launchers** that delegate to the canonical skill workflows:

1. **Skills are the canonical workflows** — they contain the full procedures and are auto-detected
2. **Prompts are now thin launchers** that reference skills rather than duplicating procedures
3. **Prompts only retain what skills can't do**: template variables (`{{ class_name }}`), explicit agent targeting (`agent: 'agent'`), and git workflow orchestration (branch/PR/merge steps)

This eliminates the duplicated wiki→data→validate→test pipelines that previously lived in both places, while keeping prompts useful as quick-launch shortcuts with pre-filled parameters.

---

## Common Tasks

### 1. "Implement all features for class X"

**Invoke:** `implement-class` prompt with `class_name = X`  
**What happens:**
1. Creates a git branch `class/X`
2. wiki-fetcher ensures wiki cache exists
3. data-author writes/updates class and subclass JSON files with effects
4. data-validator checks schema compliance
5. feature-implementer adds any new effect handlers to Python code
6. test-writer creates integration tests
7. Backlog is updated, PR is created and merged

### 2. "This damage resistance is missing on Dwarves"

**Invoke:** `file-issue` skill (automatic detection)  
**What happens:**
1. Reads `data/species/dwarf.json` to understand current state
2. Checks for duplicate issues
3. Creates a structured GitHub Issue with severity, affected files, expected behavior
4. Assigns the Copilot coding agent for autonomous fixing

### 3. "Fix issue #42"

**Invoke:** `fix-issue` skill  
**What happens:**
1. Reads the issue from GitHub
2. Classifies the category (class/species/feat/app)
3. Creates a feature branch
4. Verifies correct behavior from wiki source of truth
5. Makes the fix (data JSON and/or Python code)
6. Writes a regression test
7. Creates a PR and waits for user confirmation before merging

### 4. "Add all missing Ranger subclasses"

**Invoke:** `add-game-content` skill or `batch-implement` prompt  
**What happens:**
1. Reads backlog to identify missing subclass files
2. Fetches wiki data for each
3. Creates JSON data files with effects
4. Validates against schemas
5. Writes tests per subclass
6. Updates backlog

### 5. "What should I work on next?"

**Invoke:** `next-task` prompt  
**What happens:**
1. Reads `data/completeness/backlog.json`
2. Applies priority ordering (classes near completion → backgrounds → feats → spells → subclasses)
3. Outputs a work plan specifying which agent chain to use, files to create/update, expected complexity

### 6. "Validate that my Dwarf Cleric build is correct"

**Invoke:** `validate-character` skill  
**What happens:**
1. Builds the character via `CharacterBuilder`
2. Checks HP, AC, proficiencies, spells, effects, and skills against expected D&D 2024 values
3. Compares against reference character files if available
4. Reports pass/fail per category

### 7. "Check all data files for schema issues"

**Invoke:** `check-data-files` prompt  
**What happens:**
1. Runs `validate_data.py` across all data files
2. Fixes simple issues automatically (wrong property names, missing fields)
3. Reports complex issues that need manual intervention
4. Generates a `data-file-report.md` summary

### 8. Editing any Python or JSON file (automatic)

**Triggered by:** Hooks (no manual invocation needed)  
**What happens:**
- Python file edit → pytest runs automatically, catches regressions
- JSON data file edit → schema validator runs automatically, catches violations

### 9. "Implement Elf species features"

**Invoke:** `implement-species` prompt with `species_name = Elf`  
**What happens:**
1. wiki-fetcher ensures `wiki_data/species/elf.json` exists
2. data-author updates species JSON and variant files (no ability score increases)
3. data-validator confirms schema compliance
4. feature-implementer adds any needed effect handlers
5. test-writer creates species trait tests with multiple class combinations
6. Backlog updated

### 10. "Clean up legacy code"

**Invoke:** `cleanup-project` prompt  
**What happens:**
1. Scans for references to old `session['character']` approach
2. Removes dead code, old helpers, outdated documentation
3. Ensures all routes use `CharacterBuilder` + session helpers
4. Applies DRY principles to eliminate duplicated logic
