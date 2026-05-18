import { ChevronLeft, ChevronRight, Compass, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import type { WizardStep } from "@/lib/api";

interface Props {
  steps: WizardStep[];
  currentStepId: string;
}

export function StepNav({ steps, currentStepId }: Props) {
  const navigate = useNavigate();
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const idx = steps.findIndex((s) => s.id === currentStepId);
  const prev = idx > 0 ? steps[idx - 1] : null;
  const next = idx >= 0 && idx < steps.length - 1 ? steps[idx + 1] : null;
  const currentStepNumber = idx + 1;
  const progressPercent = idx >= 0 ? ((idx + 1) / steps.length) * 100 : 0;

  // Fetch validation status for current step
  const validationQuery = useQuery({
    queryKey: ["character", "validate", choicesMade],
    queryFn: () => api.character.validate(choicesMade),
    staleTime: 500,
  });

  // True while a fresh fetch is in-flight (initial load or after a choice changes)
  const isValidating = validationQuery.isFetching;

  // Get the current step's validation status
  const currentStepStatus = validationQuery.data?.steps?.find(
    (s) => s.step === currentStepId
  );
  const hasIncompleteChoices = isValidating || (currentStepStatus?.missing?.length ?? 0) > 0;

  return (
    <div className="mt-10 h-28 sm:h-32">
      <div className="fixed inset-x-3 bottom-3 z-30 mx-auto max-w-4xl">
        <div className="overflow-hidden rounded-2xl border border-border/80 bg-background/95 shadow-2xl backdrop-blur-md">
          <div className="h-1.5 w-full bg-muted">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="flex flex-col gap-4 p-4 sm:p-5">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                  Step navigation
                </p>
                <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                  <Compass className="h-4 w-4 text-primary" />
                  <span>
                    Step {currentStepNumber} of {steps.length}
                  </span>
                  <span className="hidden sm:inline">•</span>
                  <span className="truncate font-medium text-foreground">
                    {steps[idx]?.label ?? "Current step"}
                  </span>
                </div>
              </div>

              {/* Dynamic status message based on step validation */}
              <div className="flex items-center gap-2 text-sm">
                {isValidating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    <span className="text-muted-foreground">Validating choices…</span>
                  </>
                ) : hasIncompleteChoices ? (
                  <>
                    <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-500" />
                    <span className="font-medium text-amber-600 dark:text-amber-500">
                      Choices still pending
                    </span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-500" />
                    <span className="font-medium text-green-600 dark:text-green-500">
                      All choices made
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                disabled={!prev}
                onClick={() => prev && navigate(`/wizard/${prev.id}`)}
                className={cn(
                  "inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-3 text-sm font-medium transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  prev
                    ? "border-border bg-background hover:bg-secondary"
                    : "cursor-not-allowed border-border/60 bg-muted/30 text-muted-foreground opacity-60",
                )}
              >
                <ChevronLeft className="h-4 w-4" />
                {prev?.label ?? "Previous step"}
              </button>

              <button
                type="button"
                disabled={!next}
                onClick={() => next && navigate(`/wizard/${next.id}`)}
                className={cn(
                  "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold transition-all",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  next
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:translate-y-[-1px] hover:opacity-95"
                    : "cursor-not-allowed bg-muted text-muted-foreground opacity-60",
                )}
              >
                {next?.label ?? "Next step"}
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
