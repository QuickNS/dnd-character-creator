import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StepRenderer } from "@/components/wizard/StepRenderer";

export function WizardStep() {
  const { stepId } = useParams<{ stepId: string }>();
  const navigate = useNavigate();

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
  useEffect(() => {
    if (!step && stepsQuery.data.length > 0) {
      navigate(`/wizard/${stepsQuery.data[0].id}`, { replace: true });
    }
  }, [navigate, step, stepsQuery.data]);

  if (!step) {
    return <p className="text-muted-foreground">Loading wizard step…</p>;
  }

  return <StepRenderer step={step} steps={stepsQuery.data} />;
}
