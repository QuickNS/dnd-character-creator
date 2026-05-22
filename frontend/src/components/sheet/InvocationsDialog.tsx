import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { InvocationPicker } from "@/components/wizard/ClassAdvancedChoices";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

type Loose = Record<string, unknown>;

interface InvocationsDialogProps {
  open: boolean;
  onClose: () => void;
}

export function InvocationsDialog({ open, onClose }: InvocationsDialogProps) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  const query = useQuery({
    queryKey: [
      "character", "derived", "invocation_management",
      choicesMade.class,
      choicesMade.level,
      choicesMade.subclass,
      choicesMade.classes,
    ],
    queryFn: () => api.character.derived(choicesMade as Loose, "invocation_management"),
    enabled: open && Array.isArray(choicesMade["classes"]) && (choicesMade["classes"] as unknown[]).length > 0,
    retry: false,
  });

  const payload = query.data;
  const applicable =
    payload &&
    payload.applicable === true &&
    payload.data &&
    typeof payload.data === "object" &&
    !Array.isArray(payload.data);
  const data = applicable ? (payload!.data as Loose) : null;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose(); }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Eldritch Invocations</DialogTitle>
        </DialogHeader>

        {query.fetchStatus === "fetching" && !data ? (
          <div className="rounded-xl border border-dashed border-border/70 bg-background/60 px-4 py-5 text-sm text-muted-foreground">
            Loading invocations…
          </div>
        ) : data ? (
          <InvocationPicker data={data} />
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
