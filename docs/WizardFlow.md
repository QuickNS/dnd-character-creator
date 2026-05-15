# Wizard Flow

The character-creation wizard is **data-driven**: step ordering, required keys and cascade rules come from `/api/v1/wizard/*`, and the choice surface for every step is computed by `/api/v1/character/preview-step`. Adding a class, species, feat or spell in `data/` automatically surfaces in the wizard with no frontend change.

## Steps

The canonical step list is served by `GET /api/v1/wizard/steps` (source: [routes/api/wizard.py](../routes/api/wizard.py)).

| # | `id`         | Label           | Required keys                | Nested choices (conditional)                                                  |
|---|--------------|-----------------|------------------------------|-------------------------------------------------------------------------------|
| 1 | `basics`     | Basics          | `character_name`, `level`    | —                                                                             |
| 2 | `class`      | Class           | `class`                      | `subclass`, `fighting_style`, `maneuvers`, `spells`, `cantrips`               |
| 3 | `background` | Background      | `background`                 | `background_skill_replacement`, `origin_feat`                                 |
| 4 | `species`    | Species         | `species`                    | `lineage`, `species_trait_choices`, `species_feat_choices`, `species_skill_replacement` |
| 5 | `languages`  | Languages       | —                            | —                                                                             |
| 6 | `abilities`  | Ability Scores  | `ability_scores`             | `background_bonuses`                                                          |
| 7 | `equipment`  | Equipment       | —                            | —                                                                             |
| 8 | `complete`   | Summary         | —                            | —                                                                             |

The breadcrumb in the SPA renders one entry per step in this order. The current step is held in the Zustand store as `currentStepId`.

## Nesting Rules

- A step's "required keys" are the unconditional ones — they must be present in `choices_made` for the step to validate.
- Nested choices are surfaced **only when the prerequisite is met**. Examples:
  - `subclass` only when `level >= class.subclass_selection_level` (default 3).
  - `fighting_style` / `maneuvers` only when the class grants them.
  - `lineage` only when the chosen species has lineages.
  - `species_trait_choices` only when traits expose `type: "choice"`.
  - `background_skill_replacement` only when the background's granted skills overlap with class skills.
  - `origin_feat` always (every background grants one in 2024).
  - `background_bonuses` only when the background offers ASI options.
- The `preview-step` endpoint computes these on the fly from current `choices_made` and returns the structured options the UI should render.
- The `validate` endpoint checks the same conditions and returns `missing` keys per step.

## Choice Dependencies (Cascade Behaviour)

Source: `_DEPENDENCIES` in `routes/api/wizard.py`, served by `GET /api/v1/wizard/dependencies`. When a key on the left changes, all keys on the right are **deleted from `choices_made`** before the rebuild request — preventing stale subclass / spell / feat picks from surviving an upstream change.

| Changed key  | Invalidates                                                                                     |
|--------------|-------------------------------------------------------------------------------------------------|
| `level`      | `subclass`, `spells`, `cantrips`, `fighting_style`, `maneuvers`, `class_features`               |
| `class`      | `subclass`, `fighting_style`, `maneuvers`, `spells`, `cantrips`, `class_features`, `skill_choices`, `tool_choices`, `background_skill_replacement`, `equipment_selections` |
| `subclass`   | `subclass_features`, `spells`, `cantrips`                                                       |
| `background` | `background_bonuses`, `background_skill_replacement`, `origin_feat`, `feat_choices`, `equipment_selections` |
| `species`    | `lineage`, `species_trait_choices`, `species_feat_choices`, `species_skill_replacement`, `languages` |
| `lineage`    | `lineage_features`, `lineage_spells`, `languages`                                               |

The cascade is implemented in `frontend/src/store/characterStore.ts` (`cascade()`). Setting a key always re-asserts that key after pruning dependents, in case of accidental self-reference. Changing `class` additionally wipes any positional `class_choice_*` legacy keys.

## Frontend Layout

```
WizardLayout (frontend/src/components/layout/WizardLayout.tsx)
├── <aside>  StepSidebar (steps + Start over + ThemeToggle)
└── <main>   <Outlet>
              └── StepRenderer (frontend/src/components/wizard/StepRenderer.tsx)
                  ├── <article>
                  │     header (step number, label, description)
                  │     section → renderStepBody(step)
                  │       ├── BasicsStep / ClassStep / SpeciesStep / …
                  │       └── GenericStep (fallback, data-driven)
                  │     StepNav (Prev / Next)
                  └── <aside>  class portrait  (placeholder for EffectsPanel)
```

Per-step components in `frontend/src/components/steps/` own the rendering of choice options returned by `preview-step`. The `GenericStep` fallback exists so a brand-new step added to `_STEPS` will render a usable form even before a bespoke component is written.

## Persistence Keys

| Concern                  | Storage        | Key                          | Owner                                          |
|--------------------------|----------------|------------------------------|------------------------------------------------|
| In-progress wizard draft | `localStorage` | `dnd-creator-character-v1`   | Zustand `persist` in `characterStore.ts` (`version: 1`, `migrate` shim) |
| Saved character roster   | `localStorage` | `dnd-character-roster`       | `LocalStoragePersistence` in `lib/persistence.ts` |

The Zustand `partialize` config persists `choicesMade` and `currentStepId` only; the dependency map and other transient state are not written to disk.

## "Start Over"

`WizardLayout.handleStartOver`:
1. Confirms with the user.
2. Calls `useCharacterStore.reset()`.
3. Removes `["character"]` and `["wizard"]` query caches from react-query so the new session does not render stale build/preview data.
4. Navigates to the first step.

## Open Follow-Ups

- **`EffectsPanel` is wired up but intentionally hidden.** `frontend/src/components/wizard/EffectsPanel.tsx` posts the current `choices_made` to `/api/v1/character/build` and renders the headline calculated values (HP, AC, speed, initiative, prof bonus, ability modifiers). `StepRenderer` notes the placeholder explicitly: the right `<aside>` currently shows a class portrait, with a comment indicating how to restore the live preview. Re-enabling the panel is a UI polish task — verify performance with the rapid `choicesMade`-keyed query and confirm the placeholder no longer carries design value before swapping it in.

## See Also

- [docs/APIContract.md](APIContract.md)
- [docs/Architecture.md](Architecture.md)
- [docs/DesignSystem.md](DesignSystem.md)
