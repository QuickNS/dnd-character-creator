import { NavLink } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api, type WizardStep } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { cn } from "@/lib/utils";

interface Props {
  steps: WizardStep[];
  currentStepId: string | null;
}

export function StepSidebar({ steps, currentStepId: _ }: Props) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  const validateQuery = useQuery({
    queryKey: ["character", "validate", choicesMade],
    queryFn: () => api.character.validate(choicesMade),
    placeholderData: keepPreviousData,
  });

  const statusByStep = new Map(
    (validateQuery.data?.steps ?? []).map((s) => [s.step, s]),
  );

  return (
    <nav className="py-3">
      <ol className="flex flex-col">
        {steps.map((step, idx) => {
          const status = statusByStep.get(step.id);
          const complete = status?.complete ?? false;
          return (
            <li key={step.id}>
              <NavLink
                to={`/wizard/${step.id}`}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 px-5 py-3 border-l-2 text-sm transition-colors",
                    isActive
                      ? "border-l-primary bg-secondary text-foreground"
                      : "border-l-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/50",
                  )
                }
              >
                <span
                  className={cn(
                    "inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold",
                    complete
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground",
                  )}
                  aria-label={complete ? "complete" : "pending"}
                >
                  {complete ? "✓" : idx + 1}
                </span>
                <span className="font-medium">{step.label}</span>
              </NavLink>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
