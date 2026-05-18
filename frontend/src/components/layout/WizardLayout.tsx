import { useEffect, useState, type ReactNode } from "react";
import { Outlet, useNavigate, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { StepSidebar } from "@/components/wizard/StepSidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ConfirmDialog } from "@/components/ConfirmDialog";

export function WizardLayout() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { stepId } = useParams();
  const setDependencies = useCharacterStore((s) => s.setDependencies);
  const setCurrentStep = useCharacterStore((s) => s.setCurrentStep);
  const reset = useCharacterStore((s) => s.reset);
  const [sidebarPanel, setSidebarPanel] = useState<ReactNode | null>(null);
  const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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

  function handleConfirmStartOver() {
    reset();
    // Drop any cached /character/* and /wizard/* responses so the new
    // wizard session doesn't render stale build/preview data.
    queryClient.removeQueries({ queryKey: ["character"] });
    queryClient.removeQueries({ queryKey: ["wizard"] });
    if (steps.length > 0) {
      navigate(`/wizard/${steps[0].id}`, { replace: true });
    }
    setIsResetDialogOpen(false);
  }

  function handleStartOver() {
    setIsResetDialogOpen(true);
  }

  function handleSetSidebarPanel(panel: ReactNode | null) {
    setSidebarPanel(panel);
  }

  return (
    <div className="min-h-dvh bg-background text-foreground font-sans">
      <div
        className={`grid grid-cols-1 gap-0 min-h-dvh relative z-10 ${sidebarCollapsed ? 'md:grid-cols-[3rem_minmax(0,1fr)_24rem]' : 'md:grid-cols-[16rem_minmax(0,1fr)_24rem]'}`}
      >
        <aside className="border-r border-border bg-card/50 transition-[grid-template-columns] overflow-hidden">
          <div className={`border-b border-border flex items-center gap-2 ${sidebarCollapsed ? 'px-2 py-6 justify-center flex-col' : 'px-5 py-6 justify-between'}`}>
            {!sidebarCollapsed && (
              <img
                src="/images/logos/logo.png"
                alt="D&D Character Creator"
                className="h-28 w-auto object-contain"
              />
            )}
            <div className={`flex items-center gap-2 ${sidebarCollapsed ? 'flex-col' : ''}`}>
              {!sidebarCollapsed && (
                <>
                  <button
                    type="button"
                    onClick={handleStartOver}
                    aria-label="Reset wizard"
                    title="Discard all choices and restart the wizard"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-foreground hover:bg-secondary transition-colors"
                  >
                    <RotateCcw className="h-4 w-4" aria-hidden="true" />
                    <span className="sr-only">Reset</span>
                  </button>
                  <ThemeToggle />
                </>
              )}
              <button
                type="button"
                onClick={() => setSidebarCollapsed((c) => !c)}
                aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-foreground hover:bg-secondary transition-colors"
              >
                {sidebarCollapsed
                  ? <ChevronRight className="h-4 w-4" aria-hidden="true" />
                  : <ChevronLeft className="h-4 w-4" aria-hidden="true" />}
                <span className="sr-only">{sidebarCollapsed ? "Expand" : "Collapse"}</span>
              </button>
            </div>
          </div>
          {!sidebarCollapsed && <StepSidebar steps={steps} currentStepId={stepId ?? null} />}
        </aside>
        <main className="px-6 md:px-10 py-8 w-full min-w-0">
          <Outlet context={{ setSidebarPanel: handleSetSidebarPanel }} />
        </main>
        <aside className="hidden lg:block border-l border-border bg-card/30">
          <div className="sticky top-0 p-6 min-h-[100dvh]">
            {sidebarPanel}
          </div>
        </aside>
      </div>

      <ConfirmDialog
        open={isResetDialogOpen}
        title="Start over?"
        description="This will discard all your current choices and return you to the first wizard step."
        confirmLabel="Reset"
        onConfirm={handleConfirmStartOver}
        onCancel={() => setIsResetDialogOpen(false)}
      />
    </div>
  );
}
