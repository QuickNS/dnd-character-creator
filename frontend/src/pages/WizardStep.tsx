import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StepRenderer } from "@/components/wizard/StepRenderer";

export function WizardStep() {
  const { stepId } = useParams<{ stepId: string }>();

  const stepsQuery = useQuery({
    queryKey: ["wizard", "steps"],
    queryFn: api.wizard.steps,
  });

  if (stepsQuery.isLoading) {
    return <p className="text-muted-foreground">Loading…</p>;
  }
  if (stepsQuery.error || !stepsQuery.data) {
    return (
      <p className="text-destructive">
        Failed to load wizard steps.
      </p>
    );
  }

  const step = stepsQuery.data.find((s) => s.id === stepId);
  if (!step) {
    return (
      <p className="text-destructive">Unknown step: {stepId}</p>
    );
  }

  return <StepRenderer step={step} steps={stepsQuery.data} />;
}
