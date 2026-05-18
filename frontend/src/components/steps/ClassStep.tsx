import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  Check,
  ChevronRight,
  Layers3,
  Plus,
  Shield,
  Sparkles,
  Sword,
  Trash2,
} from "lucide-react";
import { api, type ChoicesMade, type ClassAllocation } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";
import { ChoiceList } from "@/components/wizard/ChoiceList";
import {
  ClassAdvancedChoices,
  type SpellReference,
} from "@/components/wizard/ClassAdvancedChoices";
import { useWizardSidebarPanel } from "@/components/layout/useWizardSidebarPanel";

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

type ClassInfoTarget =
  | { kind: "class" }
  | { kind: "subclass"; id: string };

function clampLevel(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return 1;
  return Math.max(1, Math.min(20, Math.floor(value)));
}

function normalizeAllocations(value: unknown): ClassAllocation[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((entry) => {
      if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
        return null;
      }
      const row = entry as Record<string, unknown>;
      const className =
        typeof row.class_name === "string" ? row.class_name : "";
      const level = clampLevel(row.level);
      const subclass =
        typeof row.subclass === "string" && row.subclass.length > 0
          ? row.subclass
          : undefined;
      return {
        class_name: className,
        level,
        ...(subclass ? { subclass } : {}),
      };
    })
    .filter((entry): entry is ClassAllocation => Boolean(entry));
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

function matchesPreviewContext(
  previewData: Record<string, unknown> | undefined,
  selectedClass: string,
  level: number,
  selectedSubclass: string,
): boolean {
  if (!previewData) return false;
  const previewChoices = previewData["choices_made"];
  if (!previewChoices || typeof previewChoices !== "object" || Array.isArray(previewChoices)) {
    return false;
  }

  const choices = previewChoices as Record<string, unknown>;
  const previewClass = typeof choices.class === "string" ? choices.class : "";
  const previewLevel = clampLevel(choices.level);
  const previewSubclass =
    typeof choices.subclass === "string" ? choices.subclass : "";

  return (
    previewClass === selectedClass &&
    previewLevel === clampLevel(level) &&
    previewSubclass === selectedSubclass
  );
}


export function ClassStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const clearChoice = useCharacterStore((s) => s.clearChoice);
  const activeClassRowIndex = useCharacterStore((s) => s.activeClassRowIndex);
  const setActiveClassRowIndex = useCharacterStore((s) => s.setActiveClassRowIndex);

  const storedRows = useMemo(
    () => normalizeAllocations(choicesMade.classes),
    [choicesMade.classes],
  );
  const fallbackLegacyRow = useMemo<ClassAllocation | null>(() => {
    const className =
      typeof choicesMade.class === "string" && choicesMade.class.length > 0
        ? choicesMade.class
        : "";
    if (!className) return null;
    const subclass =
      typeof choicesMade.subclass === "string" && choicesMade.subclass.length > 0
        ? choicesMade.subclass
        : undefined;
    return {
      class_name: className,
      level: clampLevel(choicesMade.level),
      ...(subclass ? { subclass } : {}),
    };
  }, [choicesMade.class, choicesMade.level, choicesMade.subclass]);

  const classAllocations = useMemo(() => {
    if (storedRows.length > 0) return storedRows;
    return fallbackLegacyRow ? [fallbackLegacyRow] : [];
  }, [storedRows, fallbackLegacyRow]);

  const { setSidebarPanel } = useWizardSidebarPanel();
  const [infoTarget, setInfoTarget] = useState<ClassInfoTarget>({ kind: "class" });
  const [inspectedSpell, setInspectedSpell] = useState<SpellReference | null>(null);

  function writeAllocations(nextRows: ClassAllocation[]) {
    const normalized =
      nextRows.length > 0
        ? normalizeAllocations(nextRows)
        : [{ class_name: "", level: 1 }];

    setChoice("classes", normalized);

    if (normalized.length === 1 && normalized[0].class_name) {
      const primary = normalized[0];
      setChoice("class", primary.class_name);
      setChoice("level", primary.level);
      if (primary.subclass) {
        setChoice("subclass", primary.subclass);
      } else {
        clearChoice("subclass");
      }
      return;
    }

    clearChoice("class");
    clearChoice("subclass");
    clearChoice("level");
  }

  useEffect(() => {
    if (classAllocations.length === 0) {
      writeAllocations([{ class_name: "", level: 1 }]);
    }
  }, [classAllocations.length]);

  useEffect(() => {
    if (classAllocations.length === 0) {
      if (activeClassRowIndex !== 0) {
        setActiveClassRowIndex(0);
      }
      return;
    }

    const maxIndex = classAllocations.length - 1;
    const clampedIndex = Math.min(activeClassRowIndex, maxIndex);
    if (clampedIndex !== activeClassRowIndex) {
      setActiveClassRowIndex(clampedIndex);
    }
  }, [
    activeClassRowIndex,
    classAllocations.length,
    setActiveClassRowIndex,
  ]);

  const activeRowIndex =
    classAllocations.length > 0
      ? Math.min(activeClassRowIndex, classAllocations.length - 1)
      : 0;

  const activeRow =
    classAllocations[activeRowIndex] ?? classAllocations[0] ?? { class_name: "", level: 1 };
  const selectedClass = activeRow.class_name ?? "";
  const selectedSubclass = activeRow.subclass ?? "";
  const multiclassPending = classAllocations.length > 1;
  const activeRowLabel = activeRowIndex + 1;
  const previewChoices: ChoicesMade = useMemo(() => {
    if (!selectedClass) return choicesMade;
    return {
      ...choicesMade,
      class: selectedClass,
      level: clampLevel(activeRow.level),
      ...(selectedSubclass ? { subclass: selectedSubclass } : {}),
    };
  }, [activeRow.level, choicesMade, selectedClass, selectedSubclass]);

  const classesQuery = useQuery({
    queryKey: ["catalog", "classes"],
    queryFn: api.catalog.classes,
  });

  // Fetch full class data (with features_by_level) for the detail panel
  const fullClassQuery = useQuery({
    queryKey: ["catalog", "classes", selectedClass],
    queryFn: () => api.catalog.getClass(selectedClass),
    enabled: !!selectedClass,
  });

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "class", previewChoices],
    queryFn: () => api.character.previewStep(previewChoices, "class"),
    enabled: !!selectedClass,
  });

  // For detail panel: use full class data (which has the complete features_by_level from JSON).
  // When the selected class changes, react-query serves the previous response as placeholder
  // data until the new fetch resolves. Treat that placeholder as "no data yet" so the panel
  // doesn't momentarily render the prior class's features under the new class's name.
  const classSummary = (classesQuery.data ?? []).find((cls) => cls.id === selectedClass);
  const classSummaryById = useMemo(() => {
    return new Map((classesQuery.data ?? []).map((entry) => [entry.id, entry]));
  }, [classesQuery.data]);
  const fullClassData =
    fullClassQuery.isPlaceholderData
      ? undefined
      : (fullClassQuery.data as Record<string, unknown> | undefined);
  const detailClass = selectedClass && classSummary ? ({
    ...classSummary,
    features_by_level: (fullClassData?.features_by_level as Record<string, Record<string, unknown> | string[]> | undefined) ?? {}
  } as any) : undefined;

  const previewDataRaw = previewQuery.data as Record<string, unknown> | undefined;
  const previewData = matchesPreviewContext(
    previewDataRaw,
    selectedClass,
    activeRow.level,
    selectedSubclass,
  )
    ? previewDataRaw
    : undefined;
  const needsSubclass = previewData?.["needs_subclass"] === true;
  const availableSubclasses =
    (previewData?.["available_subclasses"] as SubclassSummary[] | undefined) ?? [];
  const activeSubclassId =
    infoTarget.kind === "subclass"
      ? infoTarget.id
      : (selectedSubclass || availableSubclasses[0]?.id || "");
  const subclassDetailQuery = useQuery({
    queryKey: ["catalog", "subclass", selectedClass, activeSubclassId],
    queryFn: () => api.catalog.getSubclass(selectedClass, activeSubclassId),
    enabled: !!selectedClass && needsSubclass && !!activeSubclassId,
  });
  const activeSubclassDetail = subclassDetailQuery.isPlaceholderData
    ? undefined
    : (subclassDetailQuery.data as SubclassDetail | undefined);
  const activeFeatureLevels = featureLevelEntries(
    activeSubclassDetail?.features_by_level,
  );
  const shouldRenderInfoPanel =
    infoTarget.kind === "subclass"
      ? Boolean(activeSubclassId)
      : Boolean(detailClass);

  useEffect(() => {
    setInspectedSpell(null);
    setInfoTarget({ kind: "class" });
  }, [activeRowIndex, selectedClass]);

  useEffect(() => {
    setSidebarPanel(
      inspectedSpell
        ? (
            <SpellInfoPanel
              spell={inspectedSpell}
              onBack={() => setInspectedSpell(null)}
            />
          )
        : shouldRenderInfoPanel
        ? (
            <ClassInfoPanel
              infoTarget={infoTarget}
              detailClass={detailClass}
              selectedClass={selectedClass}
              classLoading={
                (fullClassQuery.isLoading || fullClassQuery.isPlaceholderData) && !fullClassData
              }
              showClassFeatureFallback={
                !!selectedClass && !!fullClassData && !detailClass?.features_by_level
              }
              needsSubclass={needsSubclass}
              selectedSubclass={selectedSubclass}
              activeSubclassName={availableSubclasses.find((sub) => sub.id === activeSubclassId)?.name}
              activeSubclassDetail={activeSubclassDetail}
              activeFeatureLevels={activeFeatureLevels}
              subclassLoading={
                (subclassDetailQuery.isLoading || subclassDetailQuery.isPlaceholderData) &&
                !activeSubclassDetail
              }
            />
          )
        : null,
    );
    return () => setSidebarPanel(null);
  }, [
    activeFeatureLevels,
    activeSubclassDetail,
    activeSubclassId,
    availableSubclasses,
    detailClass,
    fullClassData,
    fullClassQuery.isLoading,
    fullClassQuery.isPlaceholderData,
    inspectedSpell,
    infoTarget,
    needsSubclass,
    selectedClass,
    selectedSubclass,
    setSidebarPanel,
    shouldRenderInfoPanel,
    subclassDetailQuery.isLoading,
    subclassDetailQuery.isPlaceholderData,
  ]);

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
              <h3 className="mt-1 font-display text-2xl text-primary font-bold">
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
            "px-5 py-5 sm:px-6"
          )}
        >
          <div className="space-y-3">
            {classAllocations.map((row, idx) => {
              const isPrimary = idx === 0;
              const isActiveRow = idx === activeRowIndex;
              const rowClassSummary = classSummaryById.get(row.class_name);
              const rowSubclassThreshold = rowClassSummary?.subclass_selection_level;
              const rowNeedsSubclass =
                isActiveRow && row.class_name
                  ? needsSubclass
                  : Boolean(
                      row.class_name &&
                        typeof rowSubclassThreshold === "number" &&
                        clampLevel(row.level) >= rowSubclassThreshold,
                    );
              const rowSubclassLabel = row.subclass
                ? `Subclass: ${row.subclass}`
                : rowNeedsSubclass
                  ? "Subclass required"
                  : typeof rowSubclassThreshold === "number" && clampLevel(row.level) < rowSubclassThreshold
                    ? `Subclass at level ${rowSubclassThreshold}`
                    : "Subclass optional";
              return (
                <div
                  key={`class-row-${idx}`}
                  className={cn(
                    "rounded-xl border border-border/70 bg-background/75 p-4",
                    isPrimary && "ring-1 ring-primary/20",
                    isActiveRow && "border-primary/40 bg-background ring-2 ring-primary/20",
                  )}
                >
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    {isActiveRow && (
                      <span className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-2.5 py-1 text-[11px] uppercase tracking-wide text-primary">
                        Active row
                      </span>
                    )}
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-wide",
                        row.subclass
                          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                          : rowNeedsSubclass
                            ? "border-amber-400/50 bg-amber-500/10 text-amber-800 dark:text-amber-300"
                            : "border-border/70 bg-background/70 text-muted-foreground",
                      )}
                    >
                      {rowSubclassLabel}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-[minmax(0,1fr)_8rem_auto] md:items-end">
                    <div>
                      <label
                        htmlFor={`class_name_${idx}`}
                        className="text-xs uppercase tracking-wide text-muted-foreground"
                      >
                        {isPrimary ? "Primary class" : `Class ${idx + 1}`}
                      </label>
                      <select
                        id={`class_name_${idx}`}
                        value={row.class_name}
                        onChange={(e) => {
                          const next = classAllocations.map((entry, i) =>
                            i === idx
                              ? {
                                  class_name: e.target.value,
                                  level: clampLevel(entry.level),
                                }
                              : entry,
                          );
                          writeAllocations(next);
                          setActiveClassRowIndex(idx);
                          setInspectedSpell(null);
                          setInfoTarget({ kind: "class" });
                        }}
                        className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      >
                        <option value="">Select class</option>
                        {(classesQuery.data ?? []).map((cls) => (
                          <option key={cls.id} value={cls.id}>
                            {cls.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label
                        htmlFor={`class_level_${idx}`}
                        className="text-xs uppercase tracking-wide text-muted-foreground"
                      >
                        Level
                      </label>
                      <select
                        id={`class_level_${idx}`}
                        value={clampLevel(row.level)}
                        onChange={(e) => {
                          const next = classAllocations.map((entry, i) =>
                            i === idx
                              ? {
                                  ...entry,
                                  level: clampLevel(Number(e.target.value)),
                                }
                              : entry,
                          );
                          writeAllocations(next);
                        }}
                        className="mt-2 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      >
                        {Array.from({ length: 20 }, (_, i) => i + 1).map((lvl) => (
                          <option key={lvl} value={lvl}>
                            {lvl}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setActiveClassRowIndex(idx);
                          setInspectedSpell(null);
                          setInfoTarget({ kind: "class" });
                        }}
                        className={cn(
                          "inline-flex h-9 items-center rounded-md border px-3 text-xs font-medium transition-colors",
                          isActiveRow
                            ? "border-primary/40 bg-primary/10 text-primary"
                            : "border-border bg-background text-foreground hover:bg-secondary",
                        )}
                        aria-pressed={isActiveRow}
                      >
                        {isActiveRow ? "Active" : "Set active"}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          const next = classAllocations.filter((_, i) => i !== idx);
                          writeAllocations(next);
                          const current = activeClassRowIndex;
                          if (current > idx) {
                            setActiveClassRowIndex(current - 1);
                          } else if (current === idx) {
                            setActiveClassRowIndex(Math.max(0, current - 1));
                          }
                          setInspectedSpell(null);
                          setInfoTarget({ kind: "class" });
                        }}
                        disabled={classAllocations.length <= 1}
                        className={cn(
                          "inline-flex h-9 w-9 items-center justify-center rounded-md border transition-colors",
                          classAllocations.length <= 1
                            ? "cursor-not-allowed border-border/60 text-muted-foreground"
                            : "border-border bg-background text-foreground hover:bg-secondary",
                        )}
                        aria-label={`Remove class row ${idx + 1}`}
                        title="Remove class"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() =>
                  writeAllocations([
                    ...classAllocations,
                    { class_name: "", level: 1 },
                  ])
                }
                className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground transition-colors hover:bg-secondary"
              >
                <Plus className="h-4 w-4" />
                Add class
              </button>
              <p className="text-xs text-muted-foreground">
                Select an active row to drive class details, subclass selection, and class loadout picks.
              </p>
            </div>

            {multiclassPending && (
              <div className="rounded-lg border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
                Multiclass rows are saved independently. The detail panel and class refinement
                sections below always reflect the active row.
              </div>
            )}
          </div>

        </div>
      </section>

      {selectedClass && (previewQuery.isLoading || !previewData) && (
        <p className="text-xs text-muted-foreground">Loading class details…</p>
      )}

      {selectedClass && previewData && (
        <ClassDetail
          previewData={previewData}
          choicesMade={choicesMade}
          selectedClassSummary={detailClass}
          selectedSubclass={selectedSubclass}
          activeRowLabel={activeRowLabel}
          needsSubclass={needsSubclass}
          availableSubclasses={availableSubclasses}
          onSelectSubclassInfo={(id) => {
            setInspectedSpell(null);
            setInfoTarget({ kind: "subclass", id });
          }}
          onSubclass={(v) => {
            if (classAllocations.length === 0) return;
            const next = classAllocations.map((row, idx) =>
              idx === activeRowIndex ? { ...row, ...(v ? { subclass: v } : {}) } : row,
            );
            if (!v) {
              const activeRow = next[activeRowIndex];
              if (activeRow) {
                next[activeRowIndex] = {
                  class_name: activeRow.class_name,
                  level: activeRow.level,
                };
              }
            }
            setInspectedSpell(null);
            writeAllocations(next);
          }}
        />
      )}

      {selectedClass && (
        <ClassAdvancedChoices
          choicesForDerived={previewChoices}
          inspectedSpellName={inspectedSpell?.name}
          onInspectSpell={setInspectedSpell}
        />
      )}
    </div>
  );
}

function SpellInfoPanel({
  spell,
  onBack,
}: {
  spell: SpellReference;
  onBack: () => void;
}) {
  const meta: Array<[string, string | undefined]> = [
    ["School", spell.school],
    ["Casting Time", spell.casting_time],
    ["Range", spell.range],
    [
      "Components",
      Array.isArray(spell.components) && spell.components.length > 0
        ? spell.components.join(", ")
        : undefined,
    ],
    ["Duration", spell.duration],
    ["Source", spell.source],
  ];

  return (
    <aside className="info-panel" aria-label="Spell details panel">
      <div className="info-panel-header">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="info-panel-kicker">Spell details</p>
            <h4 className="info-panel-title">{spell.name}</h4>
          </div>
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center rounded-md border border-border/70 bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            Back
          </button>
        </div>
      </div>
      <div className="info-panel-body">
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[11px] uppercase tracking-wide text-primary">
            Always prepared
          </span>
          <span className="rounded-full border border-border/70 bg-background px-2.5 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
            {spell.level === 0 ? "Cantrip" : `Level ${spell.level ?? "—"}`}
          </span>
          {spell.counts_against_limit === false && (
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[11px] uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
              Doesn’t count against limit
            </span>
          )}
        </div>

        {spell.description && (
          <p className="mt-4 text-sm text-muted-foreground">{spell.description}</p>
        )}

        <dl className="mt-4 space-y-3">
          {meta
            .filter(([, value]) => Boolean(value))
            .map(([label, value]) => (
              <div
                key={label}
                className="rounded-lg border border-border/70 bg-background/80 px-3 py-2"
              >
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">
                  {label}
                </dt>
                <dd className="mt-1 text-sm font-medium text-foreground">
                  {value}
                </dd>
              </div>
            ))}
        </dl>
      </div>
    </aside>
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

function ClassInfoPanel({
  infoTarget,
  detailClass,
  selectedClass,
  classLoading,
  showClassFeatureFallback,
  needsSubclass,
  selectedSubclass,
  activeSubclassName,
  activeSubclassDetail,
  activeFeatureLevels,
  subclassLoading,
}: {
  infoTarget: ClassInfoTarget;
  detailClass?: any;
  selectedClass: string;
  classLoading: boolean;
  showClassFeatureFallback: boolean;
  needsSubclass: boolean;
  selectedSubclass: string;
  activeSubclassName?: string;
  activeSubclassDetail?: SubclassDetail;
  activeFeatureLevels: Array<{ level: string; features: SubclassFeatureEntry[] }>;
  subclassLoading: boolean;
}) {
  const showSubclassPanel =
    infoTarget.kind === "subclass" && needsSubclass;

  return (
    <aside
      className="info-panel"
      aria-label={showSubclassPanel ? "Subclass details panel" : "Class details panel"}
    >
      {showSubclassPanel ? (
        <>
          <div className="info-panel-header">
            <p className="info-panel-kicker">Informational panel</p>
            <h4 className="info-panel-title">
              {activeSubclassName ?? "Select a subclass"}
            </h4>
          </div>
          <div className="info-panel-body">
            {!selectedSubclass && (
              <p className="mt-2 text-xs text-muted-foreground">
                Previewing subclass details. Select a subclass card to lock your choice.
              </p>
            )}
            {subclassLoading && (
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
              !subclassLoading && (
                <p className="mt-4 text-sm text-muted-foreground">
                  No additional subclass detail is available from the current catalog payload.
                </p>
              )
            )}
          </div>
        </>
      ) : (
        <>
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
            <div className="mt-4 grid grid-cols-1 gap-2">
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
            {selectedClass && classLoading && (
              <div className="mt-6">
                <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-background px-3 py-1 text-xs font-medium text-primary">
                  <Sparkles className="h-3.5 w-3.5 animate-pulse" />
                  Loading feature progression…
                </div>
              </div>
            )}
            {detailClass?.features_by_level && (
              <ClassFeatureProgression featuresByLevel={detailClass.features_by_level as Record<string, Record<string, unknown> | string[]>} />
            )}
            {showClassFeatureFallback && (
              <div className="mt-6 rounded-lg border border-border/60 bg-background px-4 py-3">
                <p className="text-sm text-muted-foreground">
                  Feature progression details are being prepared…
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </aside>
  );
}

function ClassDetail({
  previewData,
  choicesMade,
  selectedClassSummary,
  selectedSubclass,
  activeRowLabel,
  needsSubclass,
  availableSubclasses,
  onSelectSubclassInfo,
  onSubclass,
}: {
  previewData: Record<string, unknown>;
  choicesMade: Record<string, unknown>;
  selectedClassSummary?: {
    name: string;
    subclass_selection_level: number;
  };
  selectedSubclass: string;
  activeRowLabel: number;
  needsSubclass: boolean;
  availableSubclasses: SubclassSummary[];
  onSelectSubclassInfo: (id: string) => void;
  onSubclass: (v: string) => void;
}) {
  const nestedChoices =
    (previewData["nested_choices"] as PreviewChoice[] | undefined) ?? [];

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
                <h3 className="font-display text-xl text-primary font-bold">Choose a subclass</h3>
                <span className="rounded-full border border-border/70 bg-background/70 px-2.5 py-1 text-[11px] uppercase tracking-wide text-muted-foreground">
                  Row {activeRowLabel}
                </span>
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
            )}
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 items-start">
            {availableSubclasses.map((sub) => {
              const isSelected = selectedSubclass === sub.id;
              return (
                <button
                  key={sub.id}
                  type="button"
                  onClick={() => {
                    onSubclass(sub.id);
                    onSelectSubclassInfo(sub.id);
                  }}
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
                      <div className="font-display text-lg text-primary font-semibold">
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
              <h3 className="font-display text-xl text-primary font-bold">Class choices</h3>
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
