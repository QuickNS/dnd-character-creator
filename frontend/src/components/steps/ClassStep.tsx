import { useQuery, keepPreviousData } from "@tanstack/react-query";
import {
  BookOpen,
  Check,
  ChevronRight,
  Layers3,
  Shield,
  Sparkles,
  Sword,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";
import { ChoiceList } from "@/components/wizard/ChoiceList";
import { ClassAdvancedChoices } from "@/components/wizard/ClassAdvancedChoices";

interface PreviewChoice {
  choice_key?: string;
  name?: string;
  feature_name?: string;
  title?: string;
  description?: string;
  options?: Array<unknown>;
  option_descriptions?: Record<string, string>;
  count?: number;
  depends_on?: string;
  depends_on_value?: string;
}

interface SubclassSummary {
  id: string;
  name: string;
  description?: string;
  level_3_feature_names?: string[];
}

interface SubclassDetail {
  name?: string;
  description?: string;
  features_by_level?: Record<string, Record<string, unknown> | string[]>;
}

interface SubclassFeatureEntry {
  name: string;
  description?: string;
}

/** Generate the variants of a depends_on key the parent choice might be stored under. */
function parentKeyVariants(key: string): string[] {
  const snake = key.toLowerCase().replace(/[\s_-]+/g, "_");
  const titleSpaces = snake
    .split("_")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
  // de-dup while keeping order
  return Array.from(new Set([key, snake, titleSpaces]));
}

function featureLevelEntries(
  featuresByLevel: SubclassDetail["features_by_level"],
): Array<{ level: string; features: SubclassFeatureEntry[] }> {
  if (!featuresByLevel) return [];

  function featureText(raw: unknown): string | undefined {
    if (typeof raw === "string" && raw.trim().length > 0) {
      return raw;
    }
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      return undefined;
    }

    const node = raw as Record<string, unknown>;
    const baseDescription =
      typeof node.description === "string" && node.description.trim().length > 0
        ? node.description
        : "";

    const effects = Array.isArray(node.effects)
      ? (node.effects as Array<Record<string, unknown>>)
      : [];

    const grantedSpells = effects
      .filter((effect) => effect?.type === "grant_spell" && typeof effect.spell === "string")
      .map((effect) => {
        const spell = String(effect.spell);
        const minLevel =
          typeof effect.min_level === "number"
            ? ` (level ${effect.min_level})`
            : "";
        return `${spell}${minLevel}`;
      });

    const extra = grantedSpells.length > 0
      ? `Always prepared spells: ${grantedSpells.join(", ")}.`
      : "";

    const combined = [baseDescription, extra].filter(Boolean).join(" ").trim();
    return combined.length > 0 ? combined : undefined;
  }

  return Object.entries(featuresByLevel)
    .map(([level, value]) => {
      const features: SubclassFeatureEntry[] = Array.isArray(value)
        ? value
            .filter((entry): entry is string => typeof entry === "string")
            .map((name) => ({ name }))
        : Object.entries(value ?? {})
            .filter(([name]) => Boolean(name))
            .map(([name, description]) => ({
              name,
              description: featureText(description),
            }));

      return { level, features };
    })
    .filter((entry) => entry.features.length > 0)
    .sort((a, b) => Number(a.level) - Number(b.level));
}


export function ClassStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selectedClass = (choicesMade["class"] as string | undefined) ?? "";

  const classesQuery = useQuery({
    queryKey: ["catalog", "classes"],
    queryFn: api.catalog.classes,
  });

  // Fetch full class data (with features_by_level) for the detail panel
  const fullClassQuery = useQuery({
    queryKey: ["catalog", "classes", selectedClass],
    queryFn: () => api.catalog.getClass(selectedClass),
    enabled: !!selectedClass,
    placeholderData: keepPreviousData,
  });

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "class", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "class"),
    enabled: !!selectedClass,
    placeholderData: keepPreviousData,
  });

  // For detail panel: use full class data (which has the complete features_by_level from JSON)
  const classSummary = (classesQuery.data ?? []).find((cls) => cls.id === selectedClass);
  const fullClassData = fullClassQuery.data as Record<string, unknown> | undefined;
  const detailClass = selectedClass && classSummary ? ({
    ...classSummary,
    features_by_level: (fullClassData?.features_by_level as Record<string, Record<string, unknown> | string[]> | undefined) ?? {}
  } as any) : undefined;

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
        <div className="border-b border-border/70 px-5 py-5 sm:px-6">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <Sword className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                Primary choice
              </p>
              <h3 className="mt-1 font-display text-2xl text-primary">
                Choose your class first
              </h3>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Your class defines the core fantasy, early play pattern, and which
                follow-up choices appear below.
              </p>
            </div>
          </div>
        </div>

        <div
          className={cn(
            "grid grid-cols-1 gap-6 lg:items-start",
            "lg:grid-cols-[minmax(0,1.4fr)_minmax(20rem,1fr)]",
            "px-5 py-5 sm:px-6"
          )}
        >
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 items-start">
            {(classesQuery.data ?? []).map((cls) => {
              const isSelected = selectedClass === cls.id;
              return (
                <button
                  key={cls.id}
                  type="button"
                  onClick={() => {
                    setChoice("class", cls.id);
                  }}
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
                    <div>
                      <div className="font-display text-xl text-primary">
                        {cls.name}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2 text-[11px] uppercase tracking-wide text-muted-foreground">
                        <span className="rounded-full border border-border/70 bg-background/80 px-2 py-1">
                          {Array.isArray(cls.primary_ability)
                            ? cls.primary_ability.join(" / ")
                            : cls.primary_ability}
                        </span>
                        <span className="rounded-full border border-border/70 bg-background/80 px-2 py-1">
                          Hit Die d{cls.hit_die}
                        </span>
                      </div>
                    </div>
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
                  {cls.description && (
                    <div className="text-sm text-muted-foreground line-clamp-3">
                      {cls.description}
                    </div>
                  )}
                  <div className="mt-4 flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>
                      {isSelected ? "Selected class" : "Click to select"}
                    </span>
                    <span className="inline-flex items-center gap-1 text-primary/80">
                      {isSelected ? "Details on panel" : "Select to view details"}
                      <ChevronRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          <aside className="info-panel lg:sticky lg:top-6 mt-6 lg:mt-0" aria-label="Class details panel">
            <div className="info-panel-header">
              <p className="info-panel-kicker">Informational panel</p>
              <h4 className="info-panel-title">
                {detailClass?.name ?? "Select a class"}
              </h4>
            </div>
            <div className="info-panel-body">
              {!detailClass && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Previewing class details. Select a class card to view its full feature progression.
                </p>
              )}
              {detailClass?.description && (
                <p className="mt-3 text-sm text-muted-foreground">
                  {detailClass.description}
                </p>
              )}
              <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {detailClass && (
                  <>
                    <div className="rounded-lg border border-border/70 bg-background/80 px-3 py-2">
                      <div className="text-xs uppercase tracking-wide text-muted-foreground">
                        Primary ability
                      </div>
                      <div className="mt-1 font-medium text-foreground">
                        {Array.isArray(detailClass.primary_ability)
                          ? detailClass.primary_ability.join(" / ")
                          : detailClass.primary_ability}
                      </div>
                    </div>
                    <div className="rounded-lg border border-border/70 bg-background/80 px-3 py-2">
                      <div className="text-xs uppercase tracking-wide text-muted-foreground">
                        Hit Die
                      </div>
                      <div className="mt-1 font-medium text-foreground">
                        d{detailClass.hit_die}
                      </div>
                    </div>
                    <div className="rounded-lg border border-border/70 bg-background/80 px-3 py-2">
                      <div className="text-xs uppercase tracking-wide text-muted-foreground">
                        Subclass choice
                      </div>
                      <div className="mt-1 font-medium text-foreground">
                        Level {detailClass.subclass_selection_level}
                      </div>
                    </div>
                  </>
                )}
              </div>
              {/* Feature progression for class (level 1+) */}
              {selectedClass && fullClassQuery.isLoading && !detailClass?.features_by_level && (
                <div className="mt-6">
                  <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background px-3 py-1 text-xs font-medium text-primary">
                    <Sparkles className="h-3.5 w-3.5 animate-pulse" />
                    Loading feature progression…
                  </div>
                </div>
              )}
              {detailClass && detailClass.features_by_level && (
                <ClassFeatureProgression featuresByLevel={detailClass.features_by_level as Record<string, Record<string, unknown> | string[]>} />
              )}
              {selectedClass && fullClassQuery.data && !detailClass?.features_by_level && (
                <div className="mt-6 rounded-lg border border-border/60 bg-background px-4 py-3">
                  <p className="text-sm text-muted-foreground">
                    Feature progression details are being prepared…
                  </p>
                </div>
              )}
            </div>
          </aside>
        </div>
      </section>

      {selectedClass && previewQuery.isLoading && !previewQuery.data && (
        <p className="text-xs text-muted-foreground">Loading class details…</p>
      )}

      {selectedClass && previewQuery.data && (
        <ClassDetail
          previewData={previewQuery.data}
          choicesMade={choicesMade}
          selectedClass={selectedClass}
          selectedClassSummary={detailClass}
          selectedSubclass={
            (choicesMade["subclass"] as string | undefined) ?? ""
          }
          onSubclass={(v) => setChoice("subclass", v)}
        />
      )}

      {selectedClass && <ClassAdvancedChoices />}
    </div>
  );
}

function ClassFeatureProgression({ featuresByLevel }: { featuresByLevel: Record<string, Record<string, unknown> | string[]> }) {
  // Reuse featureLevelEntries logic for robust feature extraction
  const levels = featureLevelEntries(featuresByLevel);
  if (levels.length === 0) return null;
  return (
    <div className="mt-6">
      <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background px-3 py-1 text-xs font-medium text-primary">
        <Sparkles className="h-3.5 w-3.5" />
        Feature progression
      </div>
      <div className="max-h-[28rem] space-y-3 overflow-y-auto pr-1 mt-2">
        {levels.map((entry) => (
          <div key={entry.level} className="info-panel-block">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
              <Shield className="h-3.5 w-3.5 text-primary" />
              Level {entry.level}
              <span className="text-[11px] normal-case tracking-normal text-muted-foreground">
                ({entry.features.length} feature{entry.features.length === 1 ? "" : "s"})
              </span>
            </div>
            <ul className="mt-2 space-y-3 text-sm text-foreground/90">
              {entry.features.map((feature) => (
                <li key={feature.name}>
                  <p className="font-semibold">• {feature.name}</p>
                  {feature.description && (
                    <div className="mt-1 rounded-md border border-border/60 bg-background px-3 py-2">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                        Feature details
                      </p>
                      <p className="mt-1 text-sm text-foreground/85">
                        {feature.description}
                      </p>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

function ClassDetail({
  previewData,
  choicesMade,
  selectedClass,
  selectedClassSummary,
  selectedSubclass,
  onSubclass,
}: {
  previewData: Record<string, unknown>;
  choicesMade: Record<string, unknown>;
  selectedClass: string;
  selectedClassSummary?: {
    name: string;
    subclass_selection_level: number;
  };
  selectedSubclass: string;
  onSubclass: (v: string) => void;
}) {
  const needsSubclass = previewData["needs_subclass"] === true;
  const availableSubclasses =
    (previewData["available_subclasses"] as SubclassSummary[] | undefined) ?? [];
  const nestedChoices =
    (previewData["nested_choices"] as PreviewChoice[] | undefined) ?? [];
  const activeSubclassId = selectedSubclass || availableSubclasses[0]?.id || "";
  const subclassDetailQuery = useQuery({
    queryKey: ["catalog", "subclass", selectedClass, activeSubclassId],
    queryFn: () => api.catalog.getSubclass(selectedClass, activeSubclassId),
    enabled: needsSubclass && !!activeSubclassId,
    placeholderData: keepPreviousData,
  });

  const activeSubclassDetail = subclassDetailQuery.data as SubclassDetail | undefined;
  const activeFeatureLevels = featureLevelEntries(
    activeSubclassDetail?.features_by_level,
  );

  return (
    <div className="space-y-6">
      {needsSubclass && (
        <section className="rounded-xl border border-border/70 bg-card/60 p-5 shadow-sm sm:p-6">
          <div className="mb-5 flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <Layers3 className="h-4 w-4" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-display text-xl text-primary">Choose a subclass</h3>
                {selectedClassSummary && (
                  <span className="rounded-full border border-border/70 bg-background/70 px-2.5 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                    Available at level {selectedClassSummary.subclass_selection_level}
                  </span>
                )}
              </div>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Scan the themes first, then open the detail panel for a quick look at
                the feature progression before you lock one in.
              </p>
            </div>
          </div>

          <div
            className={cn(
              "grid grid-cols-1 gap-3 lg:items-start",
              "lg:grid-cols-[minmax(0,1.4fr)_minmax(18rem,1fr)]",
            )}
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 items-start">
            {availableSubclasses.map((sub) => {
              const isSelected = selectedSubclass === sub.id;
              return (
                <button
                  key={sub.id}
                  type="button"
                  onClick={() => onSubclass(sub.id)}
                  aria-pressed={isSelected}
                  className={cn(
                    "rounded-xl border p-4 text-left transition-all duration-200",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    isSelected
                      ? "border-primary bg-muted/60 shadow-sm ring-1 ring-primary/20"
                      : "border-border/80 bg-background/80 hover:border-primary/40 hover:bg-secondary/50",
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-display text-lg text-primary">
                        {sub.name}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2 text-[11px] uppercase tracking-wide text-muted-foreground">
                        <span className="rounded-full border border-border/70 bg-background/70 px-2 py-1">
                          Subclass path
                        </span>
                        {(sub.level_3_feature_names ?? []).length > 0 && (
                          <span className="rounded-full border border-border/70 bg-background/70 px-2 py-1">
                            {(sub.level_3_feature_names ?? []).length} early features
                          </span>
                        )}
                      </div>
                    </div>
                    <span
                      className={cn(
                        "inline-flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border",
                        isSelected
                            ? "border-primary bg-background text-primary"
                          : "border-border bg-background text-transparent",
                      )}
                    >
                      <Check className="h-3.5 w-3.5" />
                    </span>
                  </div>
                  {sub.description && (
                    <div className="mt-3 text-sm text-muted-foreground line-clamp-4">
                      {sub.description}
                    </div>
                  )}
                  {(sub.level_3_feature_names ?? []).length > 0 && (
                    <div className="mt-4 border-t border-border/70 pt-3">
                      <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Signature features
                      </div>
                      <ul className="mt-2 space-y-1 text-sm text-foreground/90">
                        {sub.level_3_feature_names?.map((featureName) => (
                          <li key={featureName}>• {featureName}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="mt-4 flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>{isSelected ? "Selected subclass" : "Click card to select"}</span>
                    <span className="inline-flex items-center gap-1 text-primary/80">
                      {isSelected ? "Details on panel" : "Select to view details"}
                      <ChevronRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </button>
              );
            })}
            </div>

            <aside className="info-panel lg:sticky lg:top-6" aria-label="Subclass details panel">
              <div className="info-panel-header">
                <p className="info-panel-kicker">Informational panel</p>
                <h4 className="info-panel-title">
                {availableSubclasses.find((sub) => sub.id === activeSubclassId)?.name ??
                  "Select a subclass"}
                </h4>
              </div>

              <div className="info-panel-body">
              {!selectedSubclass && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Previewing subclass details. Select a subclass card to lock your choice.
                </p>
              )}
              {subclassDetailQuery.isLoading && !activeSubclassDetail && (
                <p className="mt-3 text-sm text-muted-foreground">
                  Loading subclass details…
                </p>
              )}
              {activeSubclassDetail?.description && (
                <p className="mt-3 text-sm text-muted-foreground">
                  {activeSubclassDetail.description}
                </p>
              )}
              {activeFeatureLevels.length > 0 ? (
                <div className="mt-4 space-y-3">
                  <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background px-3 py-1 text-xs font-medium text-primary">
                    <Sparkles className="h-3.5 w-3.5" />
                    Feature progression
                  </div>
                  <div className="max-h-[28rem] space-y-3 overflow-y-auto pr-1">
                    {activeFeatureLevels.map((entry) => (
                      <div key={entry.level} className="info-panel-block">
                        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
                          <Shield className="h-3.5 w-3.5 text-primary" />
                          Level {entry.level}
                          <span className="text-[11px] normal-case tracking-normal text-muted-foreground">
                            ({entry.features.length} feature{entry.features.length === 1 ? "" : "s"})
                          </span>
                        </div>
                        <ul className="mt-2 space-y-3 text-sm text-foreground/90">
                          {entry.features.map((feature) => (
                            <li key={feature.name}>
                              <p className="font-semibold">• {feature.name}</p>
                              {feature.description && (
                                <div className="mt-1 rounded-md border border-border/60 bg-background px-3 py-2">
                                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                                    Feature details
                                  </p>
                                  <p className="mt-1 text-sm text-foreground/85">
                                    {feature.description}
                                  </p>
                                </div>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                !subclassDetailQuery.isLoading && (
                  <p className="mt-4 text-sm text-muted-foreground">
                    No additional subclass detail is available from the current catalog payload.
                  </p>
                )
              )}
              </div>
            </aside>
          </div>
        </section>
      )}

      {nestedChoices.length > 0 && (
        <section className="rounded-xl border border-border/70 bg-card/50 p-5 shadow-sm sm:p-6">
          <div className="mb-5 flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <BookOpen className="h-4 w-4" />
            </div>
            <div>
              <h3 className="font-display text-xl text-primary">Class choices</h3>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                These selections refine the class you picked above, such as spell lists,
                fighting styles, or other feature-specific choices.
              </p>
            </div>
          </div>

          <div className="space-y-4">
          {nestedChoices.map((choice, idx) => {
            const key =
              choice.choice_key ??
              choice.feature_name ??
              choice.name ??
              `class_choice_${idx}`;
            const opts = (choice.options ?? []) as Array<unknown>;
            // Only render renderable shapes; otherwise skip silently.
            if (opts.length === 0) return null;
            // Honor depends_on / depends_on_value: hide nested bonus
            // choices (e.g. Thaumaturge bonus cantrip) until the parent
            // option is actually selected. Backend may emit depends_on
            // in snake_case while the parent is stored under its
            // Title Case feature name, so try a few normalized matches.
            if (choice.depends_on) {
              const variants = parentKeyVariants(choice.depends_on);
              const parent = variants
                .map((k) => choicesMade[k])
                .find((v) => v !== undefined);
              const matches =
                choice.depends_on_value === undefined
                  ? Boolean(parent)
                  : Array.isArray(parent)
                    ? parent.includes(choice.depends_on_value)
                    : parent === choice.depends_on_value;
              if (!matches) return null;
            }
            return (
              <ChoiceList
                key={key}
                choiceKey={key}
                title={choice.title ?? choice.name ?? key}
                description={choice.description}
                options={opts as Array<string | { name?: string }>}
                optionDescriptions={choice.option_descriptions}
                count={choice.count ?? 1}
              />
            );
          })}
          </div>
        </section>
      )}
    </div>
  );
}
