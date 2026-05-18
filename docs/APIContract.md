# API Contract — `/api/v1`

The REST API is **stateless JSON**. No Flask sessions, no cookies. The frontend is the source of truth for in-progress `choices_made`; the backend (`CharacterBuilder`) is the source of truth for every calculated value.

Source layout:

| Blueprint          | Mount        | File                     |
|--------------------|--------------|--------------------------|
| `api_v1_bp`        | `/api/v1`    | [routes/api/__init__.py](../routes/api/__init__.py) |
| `catalog_bp`       | `/catalog`   | [routes/api/catalog.py](../routes/api/catalog.py) |
| `character_bp`     | `/character` | [routes/api/character.py](../routes/api/character.py) |
| `wizard_bp`        | `/wizard`    | [routes/api/wizard.py](../routes/api/wizard.py) |

All paths below are prefixed with `/api/v1`.

## Health

| Method | Path      | Response                              |
|--------|-----------|---------------------------------------|
| GET    | `/health` | `{ "status": "ok", "version": "v1" }` |

## Catalog

Read-only access to game data. Cached aggressively on the client.

| Method | Path                                                         | Response (success)                                  |
|--------|--------------------------------------------------------------|-----------------------------------------------------|
| GET    | `/catalog/classes`                                           | `{ "classes": ClassSummary[] }`                     |
| GET    | `/catalog/classes/<class_name>`                              | Full class JSON (raw `data/classes/<n>.json`)       |
| GET    | `/catalog/classes/<class_name>/subclasses`                   | `{ "class": str, "subclasses": Summary[] }`         |
| GET    | `/catalog/classes/<class_name>/subclasses/<subclass_name>`   | Full subclass JSON                                  |
| GET    | `/catalog/species`                                           | `{ "species": SpeciesSummary[] }`                   |
| GET    | `/catalog/species/<species_name>`                            | Full species JSON (with `lineages`, `traits`)       |
| GET    | `/catalog/backgrounds`                                       | `{ "backgrounds": BackgroundSummary[] }`            |
| GET    | `/catalog/backgrounds/<background_name>`                     | Full background JSON                                |
| GET    | `/catalog/feats?type=origin\|general`                        | `{ "feats": FeatSummary[] }` (optional filter)      |
| GET    | `/catalog/feats/<feat_name>`                                 | Full feat JSON                                      |
| GET    | `/catalog/spells/<class_name>?level=N`                       | Class spell list. `level=0` returns cantrips. Omit `level` for the full list. |
| GET    | `/catalog/spells/definitions/<spell_name>`                   | Single spell definition (`data/spells/definitions/<slug>.json`) |
| GET    | `/catalog/equipment/<kind>`                                  | Raw equipment JSON. `kind ∈ { weapons, armor, adventuring_gear, weapon_masteries }` |
| GET    | `/catalog/reference/<name>`                                  | Top-level reference JSON. `name ∈ { fighting_styles, eldritch_invocations, origin_feats, general_feats, trait_patterns }` |

### Summary shapes

```ts
interface ClassSummary {
  id: string; name: string; description?: string;
  hit_die?: number; primary_ability?: string;
  subclass_selection_level?: number;
}

interface SpeciesSummary {
  id: string; name: string; description?: string;
  creature_type?: string; size?: string; speed?: number; darkvision?: number;
  has_lineages: boolean;     // true if `lineages` is non-empty
  has_trait_choices: boolean;// true if any trait has type === "choice"
}

interface BackgroundSummary {
  id: string; name: string; description?: string;
  skill_proficiencies?: string[]; ability_scores?: string[]; feat?: string;
}

interface FeatSummary {
  id: string; name: string; description?: string;
  category?: "origin" | "general"; prerequisites?: unknown;
}
```

### Errors

- `404` with `{ "description": "..." }` for unknown class, subclass, species, background, feat, spell or equipment kind.
- `400` with `{ "description": "level must be an integer" }` from `/catalog/spells/<class>` when `level` is not numeric.

## Wizard

| Method | Path                  | Response                                                |
|--------|-----------------------|---------------------------------------------------------|
| GET    | `/wizard/steps`       | `{ "steps": WizardStep[] }`                             |
| GET    | `/wizard/dependencies`| `{ "dependencies": Record<string, string[]> }`          |

```ts
interface WizardStep {
  id: string;
  label: string;
  description: string;
  required_keys: string[];
  nested_choices?: string[];
}
```

See [docs/WizardFlow.md](WizardFlow.md) for the full step list, dependency map, and cascade semantics.

## Character

All character endpoints are `POST` with `Content-Type: application/json` and a body containing `choices_made` (and, where required, `step` or `view`).

### `POST /character/build`

Build the complete calculated character.

Request:
```json
{ "choices_made": { /* ChoicesMade */ } }
```

Response (200):
```json
{ "character": { /* Character — see "Character Shape" below */ } }
```

Errors:
- `400` `{ "error": "Body must be JSON with 'choices_made'" }`
- `500` `{ "error": "<message>", "traceback": "<python traceback>" }`

### `POST /character/validate`

Per-step completion status.

Request:
```json
{ "choices_made": { /* ChoicesMade */ } }
```

Response (200):
```json
{
  "complete": true,
  "steps": [
    { "step": "basics",     "complete": true,  "missing": [] },
    { "step": "class",      "complete": false, "missing": ["subclass"] },
    { "step": "background", "complete": true,  "missing": [] },
    { "step": "species",    "complete": true,  "missing": [] },
    { "step": "languages",  "complete": true,  "missing": [] },
    { "step": "abilities",  "complete": true,  "missing": [] },
    { "step": "equipment",  "complete": true,  "missing": [] }
  ]
}
```

`complete` is `all(s.complete for s in steps)`. Conditional checks: subclass when level qualifies, species/background skill-replacement when there is overlap, species trait choices, lineage when species has lineages, background ASI when offered, class feature `nested_choices`.

Errors: same as `/build`.

> **Type drift to fix on the frontend:** `frontend/src/lib/api.ts` declares `ValidationResponse` as `{ valid, steps, missing_top_level }`, but the server returns `{ complete, steps }`. The frontend types must be updated to match.

### `POST /character/preview-step`

Return the dynamic, data-driven options for a given wizard step. This is the data feed for nested-choice rendering.

Request:
```json
{ "choices_made": { /* ChoicesMade */ }, "step": "class" }
```

Response (200) — **always includes `step`**, plus a step-specific payload. Examples:

```jsonc
// step: "class"
{
  "step": "class",
  "needs_subclass": true,
  "available_subclasses": [{
    "id": "...",
    "name": "...",
    "description": "...",
    "level_3_feature_names": ["Feature A", "Feature B", "Feature C"]
  }],
  "features_by_level": { "1": { "Feature": "Description" } },
  "nested_choices": [ /* choice descriptors */ ]
}

// step: "species"
{
  "step": "species",
  "traits": { /* species traits */ },
  "lineages": [{ "id": "...", "name": "...", "description": "...", "traits": {} }],
  "trait_choices": { /* per-trait option lists */ },
  "species_feat_choices": { /* */ },
  "skill_replacement": { "needed": false }
}

// step: "background"
{
  "step": "background",
  "skill_replacement": { "needed": 0 },
  "origin_feat_choices": [/* */]
}

// step: "languages"
{
  "step": "languages",
  "language_options": {
    "base_languages": ["Common"],
    "available_languages": [
      "Common Sign Language",
      "Draconic",
      "Dwarvish",
      "Elvish",
      "Giant",
      "Gnomish",
      "Goblin",
      "Halfling",
      "Orc"
    ],
    "selection_count": 2,
    "selected_languages": ["Elvish", "Dwarvish"]
  }
}

// step: "abilities"
{
  "step": "abilities",
  "background_asi": { "total_points": 3, "options": [/* */] },
  "recommended_array": { "STR": 8, "DEX": 14, /* … */ }
}

// step: "equipment"
{
  "step": "equipment",
  "class_equipment": { /* class starting_equipment */ },
  "background_equipment": { /* background starting_equipment */ }
}
```

Errors:
- `400` `{ "error": "Body must be JSON with 'choices_made' and 'step'" }`
- `500` `{ "error": "<message>", "traceback": "<python traceback>" }`

> **Type drift to fix on the frontend:** `PreviewStepResponse` in `frontend/src/lib/api.ts` is `{ choices_made, [key]: unknown }`. The server returns `{ step, ... }` and does **not** include `choices_made`. Update the type to `{ step: string; [key: string]: unknown }`.

### `POST /character/derived`

Return a derived view-model for the SPA. Used for screens that need a tailored shape rather than the full `Character`.

Request:
```json
{ "choices_made": { /* ChoicesMade */ }, "view": "damage_cantrips" }
```

Allowed `view` values:

| `view`                  | Built by                                    | Prerequisite (else 400)                |
|-------------------------|---------------------------------------------|----------------------------------------|
| `damage_cantrips`       | `derived_stats.build_damage_cantrip_rows`   | None                                   |
| `spell_management`      | `derived_stats.build_spell_management_view` | Character has spellcasting             |
| `mastery_management`    | `derived_stats.build_mastery_management_view` | Character has weapon mastery         |
| `invocation_management` | `derived_stats.build_invocation_management_view` | Character is a Warlock            |

Response (200):
```json
{ "view": "<name>", "data": { /* view-specific shape */ } }
```

Errors:
- `400` `{ "error": "Body must be JSON with 'choices_made' and 'view'" }`
- `400` `{ "error": "Unknown view '<x>'", "allowed": ["damage_cantrips", "invocation_management", "mastery_management", "spell_management"] }`
- `400` `{ "error": "<prerequisite message>" }` (raised as `ValueError` by the view builder)
- `500` `{ "error": "<message>", "traceback": "<python traceback>" }`

### `POST /character/random-languages`

Return a backend-validated random selection for the language step.

Request:
```json
{ "choices_made": { /* ChoicesMade */ } }
```

Response (200):
```json
{ "languages": ["Elvish", "Gnomish"] }
```

Errors:
- `400` `{ "error": "Body must be JSON with 'choices_made'" }`
- `500` `{ "error": "<message>", "traceback": "<python traceback>" }`

## Canonical Request — `ChoicesMade`

```ts
interface ChoicesMade {
  character_name?: string;
  level?: number;
  class?: string;
  subclass?: string;
  background?: string;
  species?: string;
  lineage?: string;
  ability_scores?: Record<string, number>;
  background_bonuses?: Record<string, number>;
  skill_choices?: string[];
  tool_choices?: string[];
  spells?: string[];
  cantrips?: string[];
  fighting_style?: string;
  maneuvers?: string[];
  equipment_selections?: Record<string, string>;
  languages_chosen?: string[];
  background_skill_replacement?: string[];
  species_skill_replacement?: string[];
  species_trait_choices?: Record<string, string>;
  species_feat_choices?: Record<string, string>;
  origin_feat?: string;
  // Class feature choices keyed by their `choice_key`
  [key: string]: unknown;
}
```

## Canonical Response — `Character` Shape

The `Character` object is the literal output of `CharacterBuilder.to_character()` ([modules/character_builder.py](../modules/character_builder.py), starting around line 4221). `to_character()` is the **source of truth** for the shape; this section catalogues the fields it adds on top of the stored `character_data` so consumers know what to expect.

### Identity / inputs (echoed)

| Field        | Type                                | Notes                                  |
|--------------|-------------------------------------|----------------------------------------|
| `name`       | `string`                            | From `choices_made.character_name`.    |
| `level`      | `number`                            |                                        |
| `class`      | `string`                            |                                        |
| `subclass`   | `string \| undefined`               |                                        |
| `background` | `string`                            |                                        |
| `species`    | `string`                            |                                        |
| `lineage`    | `string \| undefined`               |                                        |

### Calculated stats added by `to_character()`

| Field                       | Source                                              | Notes                                                                 |
|-----------------------------|-----------------------------------------------------|-----------------------------------------------------------------------|
| `ability_scores`            | `self.ability_scores.final_scores`                  | Map of ability → final score.                                         |
| `abilities`                 | `calculate_processed_ability_scores()`              | Map of ability → `{ score, modifier, save_modifier, save_proficient, ... }`. |
| `skills`                    | `calculate_skills()`                                | Map of skill → `{ modifier, proficient, expertise?, ... }`.           |
| `combat`                    | `calculate_combat_stats()`                          | `{ armor_class, initiative, initiative_bonus, speed, hit_point_maximum, hit_points: { current, maximum, temporary }, hp_breakdown, hit_dice: { total, spent }, passive_perception }`. |
| `attacks`                   | `calculate_weapon_attacks().attacks`                | List of attack rows.                                                  |
| `attack_combinations`       | `calculate_weapon_attacks().combinations`           | List of multi-weapon combinations.                                    |
| `ac_options`                | `calculate_ac_options()`                            | List of AC formulas with their components.                            |
| `spells_by_level`           | Computed inline                                     | `{ [level: number]: SpellDefinition[] }` — flattens `always_prepared`, `prepared`, `known`, `background_spells` and merges with definitions from `data/spells/definitions/`. |
| `spell_slots`               | Inline (session > class > subclass > level)         | `{ "1st": n, "2nd": n, ... }` (English ordinals).                     |
| `proficiency_bonus`         | `calculate_proficiency_bonus(level)`                |                                                                       |
| `spellcasting_stats`        | `calculate_spellcasting_stats()`                    | Save DC, attack bonus, ability, prepared count.                       |
| `weapon_mastery_stats`      | `calculate_weapon_mastery_stats()`                  | Mastery slots, selected weapons, available masteries.                 |
| `eldritch_invocation_stats` | `calculate_eldritch_invocation_stats()`             | Warlock only; populated otherwise as an empty/zero shape.             |
| `effects`                   | `self.applied_effects` (copied)                     | Each entry is the original effect dict augmented with `source` and `source_type`. |

### Flattened proficiencies

| Field                  | Source                              |
|------------------------|-------------------------------------|
| `languages`            | `proficiencies.languages`           |
| `skill_proficiencies`  | `proficiencies.skills`              |
| `weapon_proficiencies` | `proficiencies.weapons`             |
| `armor_proficiencies`  | `proficiencies.armor`               |
| `tool_proficiencies`   | `proficiencies.tools`               |

The original nested `proficiencies` object is also preserved.

### `choices_made` echo

`to_character()` re-injects three derived selection lists into `choices_made` so the dict round-trips cleanly through export/import:

| Key                              | When present                                  |
|----------------------------------|-----------------------------------------------|
| `spell_selections`               | Any cantrip/spell/background spell selected. Shape: `{ cantrips, spells, background_cantrips, background_spells }` (lists of names). |
| `weapon_mastery_selections`      | Any weapon masteries selected.                |
| `eldritch_invocation_selections` | Warlock with at least one invocation chosen.  |

### Other fields

`features`, `proficiencies`, `equipment`, `spells` (raw store), `class_data`, `subclass_data`, `species_data`, `background_data` and any other keys placed on `character_data` during the build are passed through unchanged. Treat any field not listed above as **read-through from the underlying `character_data`** and verify against `to_character()` if you need a guarantee.

## Type Drift Follow-Ups for the Frontend

These are gaps between `frontend/src/lib/api.ts` and the server. Filed as follow-ups for the `frontend` agent:

1. **`ValidationResponse`** — frontend declares `{ valid, steps, missing_top_level }`; server returns `{ complete, steps }`. Update the type and any consumer.
2. **`PreviewStepResponse`** — frontend declares `{ choices_made, [key]: unknown }`; server returns `{ step, ... }` with no `choices_made`. Update the type.
3. **Catalog client coverage** — `api.catalog` is missing typed methods for `feats`, `feat`, `spells/<class>`, `spells/definitions/<spell>`, `equipment/<kind>`, and `reference/<name>`. Add wrappers consistent with the existing `classes` / `species` / `backgrounds` helpers.

## See Also

- [docs/Architecture.md](Architecture.md)
- [docs/WizardFlow.md](WizardFlow.md)
- [docs/character_builder_guide.md](character_builder_guide.md)
- [docs/FEATURE_EFFECTS.md](FEATURE_EFFECTS.md)
- [.github/instructions/character-builder-api.instructions.md](../.github/instructions/character-builder-api.instructions.md)
