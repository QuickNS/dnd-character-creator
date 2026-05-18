/**
 * API client for the D&D Character Creator REST API.
 * 
 * All endpoints are stateless — the frontend holds `choices_made`,
 * the backend calculates character stats.
 */

// ========== Types ==========

export interface ClassAllocation {
  class_name: string;
  level: number;
  subclass?: string;
}

export interface ChoicesMade {
  character_name?: string;
  level?: number;
  class?: string;
  subclass?: string;
  classes?: ClassAllocation[];
  background?: string;
  species?: string;
  lineage?: string;
  ability_scores_method?: "standard_array" | "point_buy" | "manual" | "roll" | "recommended";
  ability_scores?: Record<string, number>;
  additional_ability_modifiers?: Record<string, number>;
  background_bonuses?: Record<string, number>;
  skill_choices?: string[];
  tool_choices?: string[];
  spells?: string[];
  cantrips?: string[];
  languages?: string[];
  fighting_style?: string;
  maneuvers?: string[];
  equipment_selections?: Record<string, string>;
  languages_chosen?: string[];
  background_skill_replacement?: string[];
  species_skill_replacement?: string[];
  species_trait_choices?: Record<string, string>;
  species_feat_choices?: Record<string, string>;
  origin_feat?: string;
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
  },

  // Character building
  character: {
    build: (choices: ChoicesMade): Promise<Character> =>
      apiFetch<{ character: Character }>("/character/build", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices }),
      }).then((r) => r.character),

    validate: (choices: ChoicesMade): Promise<ValidationResponse> =>
      apiFetch<ValidationResponse>("/character/validate", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices }),
      }),

    previewStep: (
      choices: ChoicesMade,
      step: string,
    ): Promise<PreviewStepResponse> =>
      apiFetch<PreviewStepResponse>("/character/preview-step", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices, step }),
      }),

    derived: (choices: ChoicesMade, view: string): Promise<DerivedResponse> =>
      apiFetch<DerivedResponse>("/character/derived", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices, view }),
      }),

    randomLanguages: (choices: ChoicesMade): Promise<string[]> =>
      apiFetch<{ languages: string[] }>("/character/random-languages", {
        method: "POST",
        body: JSON.stringify({ choices_made: choices }),
      }).then((r) => r.languages),
  },
};
