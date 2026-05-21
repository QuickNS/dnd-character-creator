/**
 * API client for the D&D Character Creator REST API.
 * 
 * All endpoints are stateless — the frontend holds `choices_made`,
 * the backend calculates character stats.
 */

import { z } from "zod";

// ========== Types ==========

export interface ClassAllocation {
  class_name: string;
  level: number;
  subclass?: string;
}

export type AbilityName =
  | "Strength"
  | "Dexterity"
  | "Constitution"
  | "Intelligence"
  | "Wisdom"
  | "Charisma";

/** All six ability scores must be present; unset abilities should be 0. */
export type AbilityModifierMap = Record<AbilityName, number>;

/** Loose spell selection storage. Keys are spell-list buckets the wizard
 * tracks (`cantrips`, `spells`, `background_cantrips`, `background_spells`,
 * etc.); the backend resolves the canonical shape. */
export interface SpellSelections {
  cantrips?: string[];
  spells?: string[];
  background_cantrips?: string[];
  background_spells?: string[];
  [bucket: string]: string[] | undefined;
}

export interface ChoicesMade {
  character_name?: string;
  classes?: ClassAllocation[];
  background?: string;
  species?: string;
  lineage?: string;
  ability_scores_method?: "standard_array" | "point_buy" | "manual" | "roll" | "recommended";
  ability_scores?: Record<string, number>;
  additional_ability_modifiers?: AbilityModifierMap;
  background_bonuses?: Record<string, number>;
  skill_choices?: string[];
  tool_choices?: string[];
  languages?: string[];
  fighting_style?: string;
  maneuvers?: string[];
  equipment_selections?: Record<string, string>;
  background_skill_replacement?: string[];
  species_skill_replacement?: string[];
  /** Nested species trait picks, keyed by trait name (e.g. `"Draconic Ancestry": "Red"`). */
  species_trait_choices?: Record<string, string>;
  /** Class spell / cantrip selections (see `SpellSelections`). */
  spell_selections?: SpellSelections;
  /**
   * Catch-all for dynamic per-feat / per-choice keys (e.g.
   * `feat_Skilled_skills_or_tools`, `class_choice_*`, ad-hoc trait picks
   * the wizard hasn't yet promoted to a nested home). Treated as opaque
   * by the frontend; the backend resolves and normalizes them.
   */
  [key: string]: unknown;
}

export interface WizardStep {
  id: string;
  label: string;
  description: string;
  required_keys: string[];
  nested_choices?: string[];
}

export interface WizardDependencies {
  [key: string]: string[];
}

export interface Character {
  name: string;
  level: number;
  class: string;
  subclass?: string;
  background: string;
  species: string;
  lineage?: string;
  ability_scores: Record<string, number>;
  ability_modifiers: Record<string, number>;
  saving_throws: Record<string, { modifier: number; proficient: boolean }>;
  skills: Record<string, { modifier: number; proficient: boolean }>;
  hp: { max: number; current: number };
  ac: number;
  proficiency_bonus: number;
  speed: number;
  features: string[];
  proficiencies: {
    armor: string[];
    weapons: string[];
    tools: string[];
    languages: string[];
    saving_throws: string[];
    skills: string[];
  };
  spells?: {
    cantrips: string[];
    known: string[];
    prepared?: string[];
    slots?: Record<string, number>;
  };
  equipment?: unknown[];
  choices_made: ChoicesMade;
  [key: string]: unknown;
}

export interface ValidationStatus {
  step: string;
  complete: boolean;
  missing: string[];
}

export interface ValidationResponse {
  valid: boolean;
  steps: ValidationStatus[];
  missing_top_level: string[];
}

export interface PreviewStepRowContext {
  row_index: number;
  is_primary: boolean;
  total_class_rows: number;
}

export interface PreviewStepResponse {
  step: string;
  row_context?: PreviewStepRowContext;
  [key: string]: unknown;
}

export interface MulticlassingSkillProficiencies {
  count: number;
  /** Either a closed list of skills, or the literal string "any". */
  options: string[] | "any";
}

export interface Multiclassing {
  hit_die_granted: number;
  armor_training: string[];
  weapon_training: string[];
  tool_training: string[];
  skill_proficiencies: MulticlassingSkillProficiencies | null;
  saving_throw_proficiencies: string[];
  other_proficiencies: string[];
  notes: string | null;
  source_text: string;
}

export interface ClassSummary {
  id: string;
  name: string;
  description?: string;
  hit_die: number;
  /**
   * Raw primary-ability string from the wiki. May be a single ability
   * ("Intelligence"), an AND combo ("Strength & Charisma"), or an OR
   * combo ("Strength or Dexterity"). Not pre-parsed by the backend.
   */
  primary_ability: string;
  subclass_selection_level: number;
  multiclassing?: Multiclassing;
}

/**
 * Full class payload from /catalog/classes/{name}. Includes everything in
 * `ClassSummary` plus the proficiency tables, feature progression, and
 * spellcasting tables consumed by the class info panel.
 */
export interface ClassDetail extends ClassSummary {
  saving_throw_proficiencies: string[];
  armor_proficiencies: string[];
  weapon_proficiencies: string[];
  tool_proficiencies?: string[] | null;
  skill_proficiencies_count: number;
  skill_options: string[];
  features_by_level?: Record<string, Record<string, unknown> | string[]>;
  spellcasting_ability?: string;
  spellcasting_focus?: string[];
  spell_slots_by_level?: Record<string, Record<string, number>>;
  spells_known_by_level?: Record<string, number>;
  prepared_spells_by_level?: Record<string, number>;
  cantrips_known_by_level?: Record<string, number>;
  proficiency_bonus_by_level?: Record<string, number>;
  starting_equipment?: unknown;
  standard_array_assignment?: Record<string, string | number>;
}

export interface BackgroundSummary {
  id: string;
  name: string;
  description?: string;
  feat?: string;
}

export interface SpeciesSummary {
  id: string;
  name: string;
  description?: string;
  creature_type: string;
  size: string;
  speed: number;
  darkvision?: number;
  has_lineages: boolean;
  has_trait_choices: boolean;
}

export interface DerivedResponse {
  view: string;
  applicable: boolean;
  choices_made?: ChoicesMade;
  reason?: string;
  data: unknown | null;
}

export interface SpellDefinition {
  name: string;
  level?: number;
  school?: string;
  description?: string;
  casting_time?: string;
  range?: string;
  duration?: string;
  components?: string | string[];
  source?: string;
  ritual?: boolean;
}

export interface FeatDefinition {
  name?: string;
  description?: string;
  benefits?: string[];
  prerequisite?: string;
  choices?: Array<Record<string, unknown>>;
}

export interface GeneralFeatsReference {
  general_feats: Record<string, FeatDefinition>;
}

export interface OriginFeatsReference {
  origin_feats: Record<string, FeatDefinition>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown,
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

// ========== Zod Schema ==========

const ClassAllocationSchema = z.object({
  class_name: z.string(),
  level: z.number().int().min(1).max(20),
  subclass: z.string().optional(),
});

const SpellSelectionsSchema = z.object({
  cantrips: z.array(z.string()).optional(),
  spells: z.array(z.string()).optional(),
  background_cantrips: z.array(z.string()).optional(),
  background_spells: z.array(z.string()).optional(),
}).catchall(z.array(z.string()).optional());

export const ChoicesMadeSchema = z.object({
  character_name: z.string().optional(),
  classes: z.array(ClassAllocationSchema).optional(),
  background: z.string().optional(),
  species: z.string().optional(),
  lineage: z.string().optional(),
  ability_scores_method: z.enum(["standard_array", "point_buy", "manual", "roll", "recommended"]).optional(),
  ability_scores: z.record(z.number()).optional(),
  additional_ability_modifiers: z.record(z.number()).optional(),
  background_bonuses: z.record(z.number()).optional(),
  skill_choices: z.array(z.string()).optional(),
  tool_choices: z.array(z.string()).optional(),
  languages: z.array(z.string()).optional(),
  fighting_style: z.string().optional(),
  maneuvers: z.array(z.string()).optional(),
  equipment_selections: z.record(z.string()).optional(),
  background_skill_replacement: z.array(z.string()).optional(),
  species_skill_replacement: z.array(z.string()).optional(),
  species_trait_choices: z.record(z.string()).optional(),
  spell_selections: SpellSelectionsSchema.optional(),
}).catchall(z.unknown());

/** Dev-mode only: warn about keys in choicesMade that the server did not echo back. */
function warnStaleChoiceKeys(choicesMade: ChoicesMade, serverChoicesMade: ChoicesMade): void {
  if (!import.meta.env.DEV) return;
  for (const key of Object.keys(choicesMade)) {
    if (!(key in serverChoicesMade)) {
      console.warn('[round-trip] key in choicesMade not echoed by server:', key);
    }
  }
}

// ========== Configuration ==========

const API_BASE_URL = import.meta.env.DEV
  ? "http://localhost:5000/api/v1"
  : "/api/v1";

// ========== Fetch wrapper ==========

async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, response.statusText, data);
  }

  return response.json();
}

// ========== API Client ==========

export const api = {
  // Wizard metadata
  wizard: {
    steps: (): Promise<WizardStep[]> =>
      apiFetch<{ steps: WizardStep[] }>("/wizard/steps").then((r) => r.steps),

    dependencies: (): Promise<WizardDependencies> =>
      apiFetch<{ dependencies: WizardDependencies }>("/wizard/dependencies").then(
        (r) => r.dependencies,
      ),
  },

  // Catalog (read-only game data)
  catalog: {
    classes: (): Promise<ClassSummary[]> =>
      apiFetch<{ classes: ClassSummary[] }>("/catalog/classes").then(
        (r) => r.classes,
      ),

    getClass: (className: string): Promise<ClassDetail> =>
      apiFetch<ClassDetail>(`/catalog/classes/${encodeURIComponent(className)}`),

    subclasses: (className: string) =>
      apiFetch(`/catalog/classes/${encodeURIComponent(className)}/subclasses`),

    getSubclass: (className: string, subclassName: string) =>
      apiFetch(
        `/catalog/classes/${encodeURIComponent(className)}/subclasses/${encodeURIComponent(subclassName)}`,
      ),

    species: (): Promise<SpeciesSummary[]> =>
      apiFetch<{ species: SpeciesSummary[] }>("/catalog/species").then(
        (r) => r.species,
      ),

    getSpecies: (speciesName: string) =>
      apiFetch(`/catalog/species/${encodeURIComponent(speciesName)}`),

    backgrounds: (): Promise<BackgroundSummary[]> =>
      apiFetch<{ backgrounds: BackgroundSummary[] }>("/catalog/backgrounds").then(
        (r) => r.backgrounds,
      ),

    getBackground: (backgroundName: string) =>
      apiFetch(`/catalog/backgrounds/${encodeURIComponent(backgroundName)}`),

    getReference: <T>(name: string): Promise<T> =>
      apiFetch<T>(`/catalog/reference/${encodeURIComponent(name)}`),

    getSpellDefinition: (spellName: string): Promise<SpellDefinition> =>
      apiFetch(
        `/catalog/spells/definitions/${encodeURIComponent(spellName)}`,
      ),
  },

  // Character building
  character: {
    build: (choices: ChoicesMade): Promise<Character> => {
      const validated = ChoicesMadeSchema.parse(choices);
      return apiFetch<{ character: Character }>("/character/build", {
        method: "POST",
        body: JSON.stringify({ choices_made: validated }),
      }).then((r) => {
        warnStaleChoiceKeys(choices, r.character.choices_made ?? {});
        return r.character;
      });
    },

    validate: (choices: ChoicesMade): Promise<ValidationResponse> =>
      apiFetch<ValidationResponse>("/character/validate", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices }),
      }),

    previewStep: (
      choices: ChoicesMade,
      step: string,
    ): Promise<PreviewStepResponse> => {
      const validated = ChoicesMadeSchema.parse(choices);
      return apiFetch<PreviewStepResponse>("/character/preview-step", {
        method: "POST",
        body: JSON.stringify({ choices_made: validated, step }),
      });
    },

    derived: (choices: ChoicesMade, view: string): Promise<DerivedResponse> =>
      apiFetch<DerivedResponse>("/character/derived", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices, view }),
      }),

    /**
     * Ask the backend for a SUGGESTED random language set for the current
     * choices. This is a read-only suggestion — the server does NOT persist
     * the result. Callers should render it as a default the user can accept
     * or override; commit happens only when the user writes back through
     * `setChoice("languages", ...)`.
     */
    suggestRandomLanguages: (choices: ChoicesMade): Promise<string[]> =>
      apiFetch<{ languages: string[] }>("/character/random-languages", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices }),
      }).then((r) => r.languages),
  },
};
