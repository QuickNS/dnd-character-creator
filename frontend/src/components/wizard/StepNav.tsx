import { useNavigate } from "react-router-dom";
import type { WizardStep } from "@/lib/api";

interface Props {
  steps: WizardStep[];
  currentStepId: string;
}

export function StepNav({ steps, currentStepId }: Props) {
  const navigate = useNavigate();
  const idx = steps.findIndex((s) => s.id === currentStepId);
  const prev = idx > 0 ? steps[idx - 1] : null;
  const next = idx >= 0 && idx < steps.length - 1 ? steps[idx + 1] : null;

  return (
    <div className="mt-10 flex justify-between border-t border-border pt-6">
      <button
        type="button"
        disabled={!prev}
        onClick={() => prev && navigate(`/wizard/${prev.id}`)}
        className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-secondary disabled:opacity-30 disabled:cursor-not-allowed"
      >
        ← {prev?.label ?? "Prev"}
      </button>
      <button
        type="button"
        disabled={!next}
        onClick={() => next && navigate(`/wizard/${next.id}`)}
        className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground font-semibold hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        {next?.label ?? "Next"} →
      </button>
    </div>
  );
}
