import { useEffect } from "react";
import { Outlet, useNavigate, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { StepSidebar } from "@/components/wizard/StepSidebar";
import { ThemeToggle } from "@/components/ThemeToggle";

export function WizardLayout() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { stepId } = useParams();
  const setDependencies = useCharacterStore((s) => s.setDependencies);
  const setCurrentStep = useCharacterStore((s) => s.setCurrentStep);
  const reset = useCharacterStore((s) => s.reset);

  const stepsQuery = useQuery({
    queryKey: ["wizard", "steps"],
    queryFn: api.wizard.steps,
  });

  const depsQuery = useQuery({
    queryKey: ["wizard", "dependencies"],
    queryFn: api.wizard.dependencies,
  });

  useEffect(() => {
    if (depsQuery.data) setDependencies(depsQuery.data);
  }, [depsQuery.data, setDependencies]);

  useEffect(() => {
    setCurrentStep(stepId ?? null);
  }, [stepId, setCurrentStep]);

  // Redirect /wizard → first step once steps load.
  useEffect(() => {
    if (!stepId && stepsQuery.data && stepsQuery.data.length > 0) {
      navigate(`/wizard/${stepsQuery.data[0].id}`, { replace: true });
    }
  }, [stepId, stepsQuery.data, navigate]);

  if (stepsQuery.isLoading || depsQuery.isLoading) {
    return (
      <div className="min-h-dvh grid place-items-center bg-background text-muted-foreground">
        Loading wizard…
      </div>
    );
  }

  if (stepsQuery.error || depsQuery.error) {
    return (
      <div className="min-h-dvh grid place-items-center bg-background text-destructive">
        Failed to load wizard.{" "}
        {String(stepsQuery.error ?? depsQuery.error ?? "")}
      </div>
    );
  }

  const steps = stepsQuery.data ?? [];

  function handleStartOver() {
    if (
      !window.confirm(
        "Start over? This will discard all your current choices.",
      )
    ) {
      return;
    }
    reset();
    // Drop any cached /character/* and /wizard/* responses so the new
    // wizard session doesn't render stale build/preview data.
    queryClient.removeQueries({ queryKey: ["character"] });
    queryClient.removeQueries({ queryKey: ["wizard"] });
    if (steps.length > 0) {
      navigate(`/wizard/${steps[0].id}`, { replace: true });
    }
  }

  return (
    <div className="min-h-dvh bg-background text-foreground font-sans">
      <div className="grid grid-cols-1 md:grid-cols-[16rem_1fr] gap-0 min-h-dvh">
        <aside className="border-r border-border bg-card/50">
          <div className="px-5 py-6 border-b border-border flex items-center justify-between gap-2">
            <h2 className="text-2xl font-semibold text-primary">D&D Character Creator</h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleStartOver}
                title="Discard all choices and restart the wizard"
                className="inline-flex h-9 items-center rounded-md border border-border bg-background px-3 text-xs text-foreground hover:bg-secondary transition-colors"
              >
                Reset
              </button>
              <ThemeToggle />
            </div>
          </div>
          <StepSidebar steps={steps} currentStepId={stepId ?? null} />
        </aside>
        <main className="px-6 md:px-10 py-8 w-full min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
