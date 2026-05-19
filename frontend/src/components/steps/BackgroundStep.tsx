import { useEffect } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { BookOpen, Check, ChevronRight, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { BackgroundSummary } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";
import { ChoiceList } from "@/components/wizard/ChoiceList";
import { FeatChoicesPicker } from "@/components/wizard/FeatChoicesPicker";
import { useWizardSidebarPanel } from "@/components/layout/useWizardSidebarPanel";

interface SkillReplacement {
  needed?: number;
  options?: string[];
  already_chosen?: string[];
}

const BG_SKILL_REPLACEMENT_KEY = "background_skill_replacement";

interface FullBackground {
  name?: string;
  description?: string;
  feat?: string;
  skill_proficiencies?: string[];
  tool_proficiencies?: string[];
  languages?: number | string;
  ability_score_increase?: {
    total?: number;
    options?: string[];
    suggested?: Record<string, number>;
  };
}

export function BackgroundStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selectedBg = (choicesMade["background"] as string | undefined) ?? "";
  const { setSidebarPanel } = useWizardSidebarPanel();

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

  const fullBgQuery = useQuery({
    queryKey: ["catalog", "background", selectedBg],
    queryFn: () => api.catalog.getBackground(selectedBg),
    enabled: !!selectedBg,
    placeholderData: keepPreviousData,
  });

  const selectedBgSummary = (bgQuery.data ?? []).find((bg) => bg.id === selectedBg);
  const fullBgData = fullBgQuery.isPlaceholderData
    ? undefined
    : (fullBgQuery.data as FullBackground | undefined);

  useEffect(() => {
    setSidebarPanel(
      selectedBgSummary
        ? (
            <BackgroundInfoPanel
              summary={selectedBgSummary}
              fullData={fullBgData}
              loading={(fullBgQuery.isLoading || fullBgQuery.isPlaceholderData) && !fullBgData}
            />
          )
        : null,
    );
    return () => setSidebarPanel(null);
  }, [selectedBgSummary, fullBgData, fullBgQuery.isLoading, fullBgQuery.isPlaceholderData, setSidebarPanel]);

  const skillReplacement =
    (previewQuery.data?.skill_replacement as SkillReplacement | undefined) ??
    undefined;
  const neededSkillReplacements = skillReplacement?.needed ?? 0;
  const alreadyChosenReplacements = skillReplacement?.already_chosen ?? [];
  const replacementOptions = Array.from(
    new Set([
      ...alreadyChosenReplacements,
      ...(skillReplacement?.options ?? []),
    ]),
  );
  const remainingSkillReplacements = Math.max(
    neededSkillReplacements - alreadyChosenReplacements.length,
    0,
  );
  const hasSkillReplacementChoice =
    neededSkillReplacements > 0 || alreadyChosenReplacements.length > 0;
  const skillReplacementCount =
    neededSkillReplacements > 0
      ? neededSkillReplacements
      : alreadyChosenReplacements.length;

  const featData = previewQuery.data?.origin_feat_choices as
    | Parameters<typeof FeatChoicesPicker>[0]["data"]
    | undefined;

  const grantedProficiencies = (() => {
    const gp = previewQuery.data?.granted_proficiencies as
      | { skills?: string[]; tools?: string[] }
      | undefined;
    return [
      ...(gp?.skills ?? []),
      ...(gp?.tools ?? []),
    ];
  })();

  const hasDependentChoices =
    hasSkillReplacementChoice ||
    (featData && featData.feat_name);

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
        <div className="border-b border-border/70 px-5 py-5 sm:px-6">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                Primary choice
              </p>
              <h3 className="mt-1 font-display text-2xl text-primary font-bold">
                Choose your background
              </h3>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Your background defines your character's history and grants ability score improvements,
                skill and tool proficiencies, and an Origin feat.
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                Select a background to see its full details in the side panel.
              </p>
            </div>
          </div>
        </div>

        <div className="px-5 py-5 sm:px-6">
          {bgQuery.isLoading && (
            <p className="text-xs text-muted-foreground">Loading backgrounds…</p>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 items-start">
            {(bgQuery.data ?? []).map((bg) => {
              const isSelected = selectedBg === bg.id;
              return (
                <button
                  key={bg.id}
                  type="button"
                  onClick={() => setChoice("background", bg.id)}
                  aria-pressed={isSelected}
                  className={cn(
                    "group rounded-xl border p-4 text-left transition-all duration-200",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    isSelected
                      ? "border-primary bg-muted/60 shadow-md ring-1 ring-primary/20"
                      : "border-border/80 bg-background/75 hover:-translate-y-1 hover:border-primary/40 hover:bg-secondary/50 hover:shadow-md",
                  )}
                >
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="font-display text-xl text-primary font-semibold">{bg.name}</div>
                    <span
                      className={cn(
                        "inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border transition-colors",
                        isSelected
                          ? "border-primary bg-background text-primary"
                          : "border-border bg-background text-transparent group-hover:border-primary/40",
                      )}
                    >
                      <Check className="h-4 w-4" />
                    </span>
                  </div>
                  {bg.feat && (
                    <dl className="text-xs text-muted-foreground/80 space-y-1">
                      <div>
                        <span className="font-semibold">Feat:</span> {bg.feat}
                      </div>
                    </dl>
                  )}
                  {bg.description && (
                    <div className="mt-2 text-sm text-muted-foreground line-clamp-3">
                      {bg.description}
                    </div>
                  )}
                  <div className="mt-4 flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>{isSelected ? "Selected background" : "Click to select"}</span>
                    <span className="inline-flex items-center gap-1 text-primary/80">
                      {isSelected ? "Details on panel" : "Select to view details"}
                      <ChevronRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {hasDependentChoices && (
        <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
          <div className="border-b border-border/70 px-5 py-4 sm:px-6">
            <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
              Follow-up choices
            </p>
            <h3 className="mt-1 font-display text-xl text-primary font-bold">
              {selectedBgSummary?.name ?? "Background"} options
            </h3>
          </div>
          <div className="space-y-6 px-5 py-5 sm:px-6">
            {hasSkillReplacementChoice && replacementOptions.length > 0 && (
                <ChoiceList
                  choiceKey={BG_SKILL_REPLACEMENT_KEY}
                  title="Replacement skill proficiencies"
                  description={`Your background grants skills you already have. Choose ${
                    neededSkillReplacements
                  } replacement${
                    neededSkillReplacements === 1 ? "" : "s"
                  } from your class's skill list.${
                    remainingSkillReplacements === 0
                      ? " Selection complete."
                      : ` ${remainingSkillReplacements} remaining.`
                  }`}
                  options={replacementOptions}
                  count={skillReplacementCount}
                />
              )}

            {featData && featData.feat_name && (
              <FeatChoicesPicker
                data={featData}
                heading="Origin feat"
                grantedProficiencies={grantedProficiencies}
              />
            )}
          </div>
        </section>
      )}

    </div>
  );
}

function BackgroundInfoPanel({
  summary,
  fullData,
  loading,
}: {
  summary: BackgroundSummary;
  fullData?: FullBackground;
  loading?: boolean;
}) {
  const abilityIncrease = fullData?.ability_score_increase;
  const abilityOptions = abilityIncrease?.options ?? [];
  const skills = fullData?.skill_proficiencies ?? [];
  const tools = fullData?.tool_proficiencies ?? [];
  const languages = fullData?.languages;

  return (
    <aside className="info-panel" aria-label="Background details panel">
      <div className="info-panel-header">
        <p className="info-panel-kicker">Background details</p>
        <h4 className="info-panel-title">{summary.name}</h4>
      </div>
      <div className="info-panel-body space-y-4">
        {summary.description && (
          <p className="text-sm text-muted-foreground">{summary.description}</p>
        )}

        {loading && (
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background px-3 py-1 text-xs font-medium text-primary">
            <Sparkles className="h-3.5 w-3.5 animate-pulse" />
            Loading details…
          </div>
        )}

        {fullData && (
          <div className="grid grid-cols-1 gap-2">
            {abilityOptions.length > 0 && (
              <div className="info-panel-block">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  Ability score increases
                </div>
                <div className="mt-1 font-medium text-foreground text-sm">
                  +{abilityIncrease?.total ?? 3} distributed among{" "}
                  {abilityOptions.join(", ")}
                </div>
              </div>
            )}

            {skills.length > 0 && (
              <div className="info-panel-block">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  Skill proficiencies
                </div>
                <div className="mt-1 font-medium text-foreground text-sm">
                  {skills.join(", ")}
                </div>
              </div>
            )}

            {tools.length > 0 && (
              <div className="info-panel-block">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  Tool proficiencies
                </div>
                <div className="mt-1 font-medium text-foreground text-sm">
                  {tools.join(", ")}
                </div>
              </div>
            )}

            {languages !== undefined && (
              <div className="info-panel-block">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  Languages
                </div>
                <div className="mt-1 font-medium text-foreground text-sm">
                  {typeof languages === "number"
                    ? `${languages} of your choice`
                    : String(languages)}
                </div>
              </div>
            )}

            {(fullData.feat ?? summary.feat) && (
              <div className="info-panel-block">
                <div className="text-xs uppercase tracking-wide text-muted-foreground">
                  Origin feat
                </div>
                <div className="mt-1 font-medium text-foreground text-sm">
                  {fullData.feat ?? summary.feat}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
