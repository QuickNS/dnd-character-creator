/**
 * Character wizard store.
 *
 * The frontend is the source of truth for in-progress `choices_made`.
 * The backend `CharacterBuilder` is the source of truth for calculated
 * stats — we POST `choices_made` to `/api/v1/character/*` to derive
 * everything else.
 *
 * Cascade invalidation: when a key listed in `/wizard/dependencies`
 * changes, all dependent keys are removed from `choices_made` so stale
 * subclass/spell/feat picks don't survive a class change.
 *
 * Persisted to localStorage so a refresh during character creation
 * doesn't lose progress.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { ChoicesMade, WizardDependencies } from "@/lib/api";

interface CharacterState {
  choicesMade: ChoicesMade;
  dependencies: WizardDependencies;
  currentStepId: string | null;

  setDependencies: (deps: WizardDependencies) => void;
  setCurrentStep: (stepId: string | null) => void;
  setChoice: (key: string, value: unknown) => void;
  clearChoice: (key: string) => void;
  reset: () => void;
}

const STORAGE_KEY = "dnd-creator-character-v1";

function cascade(
  choices: ChoicesMade,
  deps: WizardDependencies,
  changedKey: string,
): ChoicesMade {
  const dependents = deps[changedKey];
  const next = { ...choices };
  if (dependents) {
    for (const k of dependents) {
      delete next[k];
    }
  }
  // Special-case class: also wipe any positional `class_choice_*` keys
  // that older builds stored before nested choices got stable keys.
  if (changedKey === "class") {
    for (const k of Object.keys(next)) {
      if (k.startsWith("class_choice_")) delete next[k];
    }
  }
  return next;
}

export const useCharacterStore = create<CharacterState>()(
  persist(
    (set) => ({
      choicesMade: {},
      dependencies: {},
      currentStepId: null,

      setDependencies: (dependencies) => set({ dependencies }),
      setCurrentStep: (currentStepId) => set({ currentStepId }),

      setChoice: (key, value) =>
        set((state) => {
          let nextChoices: ChoicesMade = { ...state.choicesMade, [key]: value };
          nextChoices = cascade(nextChoices, state.dependencies, key);
          // Re-set the changed key in case cascade dropped it (it
          // shouldn't, but guard against accidental self-reference).
          nextChoices[key] = value;
          return { choicesMade: nextChoices };
        }),

      clearChoice: (key) =>
        set((state) => {
          const next = { ...state.choicesMade };
          delete next[key];
          return {
            choicesMade: cascade(next, state.dependencies, key),
          };
        }),

      reset: () => set({ choicesMade: {}, currentStepId: null }),
    }),
    {
      name: STORAGE_KEY,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        choicesMade: state.choicesMade,
        currentStepId: state.currentStepId,
      }),
    },
  ),
);
