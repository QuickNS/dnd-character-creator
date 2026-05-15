import type { WizardStep } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { StepNav } from "./StepNav";
// NOTE: The live character preview (`EffectsPanel` from "./EffectsPanel")
// is intentionally hidden in the wizard for now. The component is kept
// in the codebase — to restore the preview, import it here and render it
// inside the <aside> below in place of the class image.

const KNOWN_CLASS_IMAGES = new Set([
  "artificer",
  "barbarian",
  "bard",
  "cleric",
  "druid",
  "fighter",
  "monk",
  "paladin",
  "ranger",
  "rogue",
  "sorcerer",
  "warlock",
  "wizard",
]);

function classImageSrc(choicesMade: Record<string, unknown>): string {
  const raw = choicesMade["class"];
  if (typeof raw === "string") {
    const slug = raw.toLowerCase().trim();
    if (KNOWN_CLASS_IMAGES.has(slug)) {
      return `/images/classes/${slug}.png`;
    }
  }
  return "/images/classes/bar-l.png";
}
import { BasicsStep } from "@/components/steps/BasicsStep";
import { ClassStep } from "@/components/steps/ClassStep";
import { SpeciesStep } from "@/components/steps/SpeciesStep";
import { BackgroundStep } from "@/components/steps/BackgroundStep";
import { LanguagesStep } from "@/components/steps/LanguagesStep";
import { AbilitiesStep } from "@/components/steps/AbilitiesStep";
import { EquipmentStep } from "@/components/steps/EquipmentStep";
import { SummaryStep } from "@/components/steps/SummaryStep";
import { GenericStep } from "@/components/steps/GenericStep";

interface Props {
  step: WizardStep;
  steps: WizardStep[];
}

function renderStepBody(
  step: WizardStep,
  steps: WizardStep[],
  choicesMade: Record<string, unknown>,
) {
  switch (step.id) {
    case "basics":
      return <BasicsStep />;
    case "class":
      return <ClassStep />;
    case "species":
      return <SpeciesStep />;
    case "background":
      return <BackgroundStep />;
    case "languages":
      return <LanguagesStep />;
    case "abilities":
      return <AbilitiesStep />;
    case "equipment":
      return <EquipmentStep />;
    case "complete":
      return <SummaryStep steps={steps} />;
    default:
      return <GenericStep step={step} choicesMade={choicesMade} />;
  }
}

export function StepRenderer({ step, steps }: Props) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  return (
    <article className="grid grid-cols-1 lg:grid-cols-[1fr_20rem] gap-8">
      <div className="relative z-10">
        <header className="mb-6">
          <p className="text-xs uppercase tracking-widest text-muted-foreground">
            Step {steps.findIndex((s) => s.id === step.id) + 1} of{" "}
            {steps.length}
          </p>
          <h1 className="font-display text-3xl font-semibold text-primary mt-1">
            {step.label}
          </h1>
          <p className="mt-2 text-muted-foreground">{step.description}</p>
        </header>

        <section>{renderStepBody(step, steps, choicesMade)}</section>

        <StepNav steps={steps} currentStepId={step.id} />
      </div>

      <aside className="hidden lg:block lg:sticky lg:top-0 self-start lg:h-dvh relative lg:-mr-10">
        {/*
          Live character preview is temporarily hidden. Restore by
          replacing the <img> below with <EffectsPanel />.
        */}
        <img
          src={classImageSrc(choicesMade)}
          alt=""
          aria-hidden="true"
          className="absolute right-0 top-0 h-full w-[40rem] max-w-none object-cover object-right opacity-90 pointer-events-none select-none -scale-x-100"
        />
      </aside>
    </article>
  );
}
