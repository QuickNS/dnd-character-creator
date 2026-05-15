import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { ChoiceList } from "@/components/wizard/ChoiceList";
import { FeatChoicesPicker } from "@/components/wizard/FeatChoicesPicker";

interface SkillReplacement {
  needed?: number;
  options?: string[];
  already_chosen?: string[];
}

const BG_SKILL_REPLACEMENT_KEY = "background_skill_replacement";

export function BackgroundStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selectedBg = (choicesMade["background"] as string | undefined) ?? "";

  const bgQuery = useQuery({
    queryKey: ["catalog", "backgrounds"],
    queryFn: api.catalog.backgrounds,
  });

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "background", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "background"),
    enabled: !!selectedBg,
    placeholderData: keepPreviousData,
  });

  const skillReplacement =
    (previewQuery.data?.skill_replacement as SkillReplacement | undefined) ??
    undefined;

  const featData = previewQuery.data?.origin_feat_choices as
    | Parameters<typeof FeatChoicesPicker>[0]["data"]
    | undefined;

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold mb-3">Choose a background</h3>
        {bgQuery.isLoading && (
          <p className="text-xs text-muted-foreground">Loading backgrounds…</p>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(bgQuery.data ?? []).map((bg) => {
            const isSelected = selectedBg === bg.id;
            return (
              <button
                key={bg.id}
                type="button"
                onClick={() => setChoice("background", bg.id)}
                className={
                  "text-left rounded-md border p-3 transition-colors " +
                  (isSelected
                    ? "border-primary bg-secondary"
                    : "border-border hover:bg-secondary/60")
                }
              >
                <div className="font-display text-lg text-primary">{bg.name}</div>
                {bg.feat && (
                  <dl className="mt-1 text-xs text-muted-foreground/80 space-y-0.5">
                    <div>
                      <span className="font-semibold">Feat:</span> {bg.feat}
                    </div>
                  </dl>
                )}
                {bg.description && (
                  <div className="text-xs text-muted-foreground mt-1 line-clamp-3">
                    {bg.description}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </section>

      {skillReplacement &&
        (skillReplacement.needed ?? 0) > 0 &&
        (skillReplacement.options?.length ?? 0) > 0 && (
          <ChoiceList
            choiceKey={BG_SKILL_REPLACEMENT_KEY}
            title="Replacement skill proficiencies"
            description={`Your background grants skills you already have. Choose ${
              skillReplacement.needed
            } replacement${skillReplacement.needed === 1 ? "" : "s"} from your class's skill list.`}
            options={skillReplacement.options ?? []}
            count={skillReplacement.needed ?? 1}
          />
        )}

      {featData && featData.feat_name && (
        <FeatChoicesPicker data={featData} heading="Origin feat" />
      )}
    </div>
  );
}
