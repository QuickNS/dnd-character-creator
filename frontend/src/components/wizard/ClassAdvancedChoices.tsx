import { useEffect, useMemo } from "react";
import { Check, Sparkles, Wand2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";

type Loose = Record<string, unknown>;

function arr<T = unknown>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}
function rec(v: unknown): Loose {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Loose) : {};
}
function num(v: unknown): number | undefined {
  return typeof v === "number" ? v : undefined;
}
function str(v: unknown): string | undefined {
  return typeof v === "string" ? v : undefined;
}

interface CurrentSpellSelections {
  cantrips: string[];
  spells: string[];
  background_cantrips: string[];
  background_spells: string[];
}

export interface SpellReference {
  name: string;
  level?: number;
  source?: string;
  school?: string;
  description?: string;
  casting_time?: string;
  range?: string;
  duration?: string;
  components?: string[];
  counts_against_limit?: boolean;
}

function normalizeSpellReference(raw: Loose): SpellReference | null {
  const name = str(raw.name);
  if (!name) return null;

  const rawComponents = raw.components;
  const components =
    typeof rawComponents === "string"
      ? [rawComponents]
      : arr<string>(rawComponents).filter(
          (entry): entry is string =>
            typeof entry === "string" && entry.length > 0,
        );

  return {
    name,
    level: num(raw.level),
    source: str(raw.source),
    school: str(raw.school),
    description: str(raw.description),
    casting_time: str(raw.casting_time),
    range: str(raw.range),
    duration: str(raw.duration),
    components: components.length > 0 ? components : undefined,
    counts_against_limit:
      typeof raw.counts_against_limit === "boolean"
        ? raw.counts_against_limit
        : undefined,
  };
}

function spellLevelLabel(level?: number): string {
  if (level === 0) return "Cantrip";
  if (typeof level === "number" && Number.isFinite(level)) {
    return `Level ${level}`;
  }
  return "Spell";
}

function matchesChoiceContext(
  responseChoices: unknown,
  sourceChoices: Loose,
): boolean {
  if (!responseChoices || typeof responseChoices !== "object" || Array.isArray(responseChoices)) {
    return false;
  }

  const response = responseChoices as Loose;
  const responseClass = str(response.class) ?? "";
  const responseSubclass = str(response.subclass) ?? "";
  const responseLevel = num(response.level) ?? 1;
  const sourceClass = str(sourceChoices.class) ?? "";
  const sourceSubclass = str(sourceChoices.subclass) ?? "";
  const sourceLevel = num(sourceChoices.level) ?? 1;

  return (
    responseClass === sourceClass &&
    responseSubclass === sourceSubclass &&
    responseLevel === sourceLevel
  );
}

/**
 * Renders the spell, weapon-mastery, and eldritch-invocation pickers
 * inside the class step. Each picker silently hides itself when the
 * underlying derived view reports `applicable: false`.
 */
export function ClassAdvancedChoices({
  choicesForDerived,
  inspectedSpellName,
  onInspectSpell,
}: {
  choicesForDerived?: Loose;
  inspectedSpellName?: string;
  onInspectSpell?: (spell: SpellReference) => void;
} = {}) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const sourceChoices = choicesForDerived ?? choicesMade;

  const spellsQ = useDerived(sourceChoices, "spell_management");
  const masteryQ = useDerived(sourceChoices, "mastery_management");
  const invocationsQ = useDerived(sourceChoices, "invocation_management");
  const spellsData = getApplicableData(spellsQ, sourceChoices);
  const masteryData = getApplicableData(masteryQ, sourceChoices);
  const invocationsData = getApplicableData(invocationsQ, sourceChoices);

  const anyVisible = Boolean(spellsData || masteryData || invocationsData);
  const isLoading =
    (!spellsQ.error &&
      !spellsData &&
      (spellsQ.fetchStatus === "fetching" || Boolean(spellsQ.data))) ||
    (!masteryQ.error &&
      !masteryData &&
      (masteryQ.fetchStatus === "fetching" || Boolean(masteryQ.data))) ||
    (!invocationsQ.error &&
      !invocationsData &&
      (invocationsQ.fetchStatus === "fetching" || Boolean(invocationsQ.data)));
  if (!anyVisible && !isLoading) return null;

  return (
    <section className="rounded-xl border border-border/70 bg-card/50 p-5 shadow-sm sm:p-6">
      <div className="mb-5 flex items-start gap-3">
        <div className="rounded-full bg-primary/10 p-2 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
            Class refinement
          </p>
          <h3 className="mt-1 font-display text-xl text-primary">Class loadout</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Finish the class-specific picks that shape how this character plays.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {!anyVisible && isLoading ? (
          <div className="rounded-xl border border-dashed border-border/70 bg-background/60 px-4 py-5 text-sm text-muted-foreground">
            Loading class loadout…
          </div>
        ) : (
          <>
            {spellsData && (
              <SpellPicker
                data={spellsData}
                inspectedSpellName={inspectedSpellName}
                onInspectSpell={onInspectSpell}
              />
            )}
            {masteryData && (
              <MasteryPicker data={masteryData} />
            )}
            {invocationsData && (
              <InvocationPicker data={invocationsData} />
            )}
          </>
        )}
      </div>
    </section>
  );
}

function useDerived(choicesMade: Loose, view: string) {
  return useQuery({
    queryKey: ["character", "derived", view, choicesMade],
    queryFn: () => api.character.derived(choicesMade, view),
    enabled: !!choicesMade["class"],
    retry: false,
  });
}

function getApplicableData(
  q: { data?: unknown },
  sourceChoices: Loose,
): Loose | null {
  if (!q.data || typeof q.data !== "object") return null;
  const payload = q.data as Loose;
  if (!matchesChoiceContext(payload.choices_made, sourceChoices)) {
    return null;
  }
  if (payload.applicable !== true) return null;
  const data = payload.data;
  if (data && typeof data === "object" && !Array.isArray(data)) {
    return data as Loose;
  }
  return null;
}

// ---------- Spells ----------

function SpellPicker({
  data,
  inspectedSpellName,
  onInspectSpell,
}: {
  data: Loose;
  inspectedSpellName?: string;
  onInspectSpell?: (spell: SpellReference) => void;
}) {
  const setChoice = useCharacterStore((s) => s.setChoice);
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  const limits = rec(data.limits);
  const maxCantrips = num(limits.cantrips) ?? 0;
  const maxSpells = num(limits.spells) ?? 0;

  const availableCantrips = arr<Loose>(data.available_cantrips);
  const availableSpellsByLevel = rec(data.available_spells);
  const alwaysPrepared = useMemo(
    () =>
      arr<Loose>(data.always_prepared)
        .map(normalizeSpellReference)
        .filter((spell): spell is SpellReference => Boolean(spell)),
    [data.always_prepared],
  );
  const alwaysPreparedNames = useMemo(
    () => new Set(alwaysPrepared.map((spell) => spell.name)),
    [alwaysPrepared],
  );

  const current =
    (choicesMade["spell_selections"] as CurrentSpellSelections | undefined) ??
    normalizeCurrent(rec(data.current_selections));

  function update(patch: Partial<CurrentSpellSelections>) {
    const next: CurrentSpellSelections = {
      cantrips: current.cantrips,
      spells: current.spells,
      background_cantrips: current.background_cantrips,
      background_spells: current.background_spells,
      ...patch,
    };
    setChoice("spell_selections", next);
  }

  function toggle(
    list: string[],
    name: string,
    cap: number,
  ): string[] | null {
    if (list.includes(name)) {
      return list.filter((n) => n !== name);
    }
    if (list.length >= cap) return null;
    return [...list, name];
  }

  useEffect(() => {
    if (alwaysPreparedNames.size === 0) return;

    const nextCantrips = current.cantrips.filter(
      (name) => !alwaysPreparedNames.has(name),
    );
    const nextSpells = current.spells.filter(
      (name) => !alwaysPreparedNames.has(name),
    );
    const nextBackgroundCantrips = current.background_cantrips.filter(
      (name) => !alwaysPreparedNames.has(name),
    );
    const nextBackgroundSpells = current.background_spells.filter(
      (name) => !alwaysPreparedNames.has(name),
    );

    const changed =
      nextCantrips.length !== current.cantrips.length ||
      nextSpells.length !== current.spells.length ||
      nextBackgroundCantrips.length !== current.background_cantrips.length ||
      nextBackgroundSpells.length !== current.background_spells.length;

    if (!changed) return;

    setChoice("spell_selections", {
      cantrips: nextCantrips,
      spells: nextSpells,
      background_cantrips: nextBackgroundCantrips,
      background_spells: nextBackgroundSpells,
    });
  }, [
    alwaysPreparedNames,
    current.background_cantrips,
    current.background_spells,
    current.cantrips,
    current.spells,
    setChoice,
  ]);

  return (
    <div className="rounded-xl border border-border/70 bg-background/70 p-4 shadow-sm space-y-4 sm:p-5">
      <header>
        <h4 className="font-display text-base text-primary">Spells</h4>
        <p className="text-xs text-muted-foreground">
          Cantrips {current.cantrips.length}/{maxCantrips} · Prepared spells{" "}
          {current.spells.length}/{maxSpells}
        </p>
      </header>

      {alwaysPrepared.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs uppercase text-muted-foreground">
            Always prepared
          </div>
          <ul className="space-y-2">
            {alwaysPrepared.map((spell) => {
              const isInspected = inspectedSpellName === spell.name;
              return (
                <li key={`${spell.name}-${spell.source ?? "always-prepared"}`}>
                  <button
                    type="button"
                    onClick={() => onInspectSpell?.(spell)}
                    aria-pressed={isInspected}
                    className={cn(
                      "w-full rounded-lg border px-3 py-3 text-left transition-all duration-200",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                      isInspected
                        ? "border-primary bg-muted/60 shadow-sm ring-1 ring-primary/20"
                        : "border-border/80 bg-background/80 hover:border-primary/30 hover:bg-secondary/60",
                    )}
                  >
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="font-medium text-foreground">{spell.name}</span>
                      <span className="rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-[11px] uppercase tracking-wide text-primary">
                        Always prepared
                      </span>
                      <span className="rounded-full border border-border/70 bg-background px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                        {spellLevelLabel(spell.level)}
                      </span>
                      {spell.source && (
                        <span className="rounded-full border border-border/70 bg-background px-2 py-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                          {spell.source}
                        </span>
                      )}
                      {spell.counts_against_limit === false && (
                        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[11px] uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                          Doesn’t count against limit
                        </span>
                      )}
                    </div>
                    {(spell.school || spell.description) && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        {spell.school && <span>{spell.school}</span>}
                        {spell.school && spell.description && <span> · </span>}
                        {spell.description && (
                          <span className="line-clamp-2">{spell.description}</span>
                        )}
                      </div>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {availableCantrips.length > 0 && maxCantrips > 0 && (
        <SpellGroup
          title="Cantrips"
          spells={availableCantrips}
          selected={current.cantrips}
          disabledNames={alwaysPreparedNames}
          onToggle={(name) => {
            const next = toggle(current.cantrips, name, maxCantrips);
            if (next) update({ cantrips: next });
          }}
        />
      )}

      {Object.keys(availableSpellsByLevel)
        .sort((a, b) => Number(a) - Number(b))
        .map((lvl) => {
          if (lvl === "0") return null;
          const list = arr<Loose>(availableSpellsByLevel[lvl]);
          if (list.length === 0) return null;
          return (
            <SpellGroup
              key={lvl}
              title={`Level ${lvl}`}
              spells={list}
              selected={current.spells}
              disabledNames={alwaysPreparedNames}
              onToggle={(name) => {
                const next = toggle(current.spells, name, maxSpells);
                if (next) update({ spells: next });
              }}
            />
          );
        })}

      <BackgroundSpells
        requirements={rec(data.background_requirements)}
        current={current}
        update={update}
        disabledNames={alwaysPreparedNames}
      />
    </div>
  );
}

function SpellGroup({
  title,
  spells,
  selected,
  disabledNames,
  onToggle,
}: {
  title: string;
  spells: Loose[];
  selected: string[];
  disabledNames?: Set<string>;
  onToggle: (name: string) => void;
}) {
  return (
    <div>
      <div className="text-xs uppercase text-muted-foreground mb-1">
        {title}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
        {spells.map((sp, i) => {
          const name = str(sp.name) ?? `Spell ${i}`;
          const school = str(sp.school);
          const isSelected = selected.includes(name);
          const isDisabled = disabledNames?.has(name) ?? false;
          return (
            <button
              key={`${name}-${i}`}
              type="button"
              onClick={() => {
                if (!isDisabled) onToggle(name);
              }}
              aria-pressed={isSelected}
              aria-disabled={isDisabled}
              disabled={isDisabled}
              className={cn(
                "flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                isDisabled
                  ? "cursor-not-allowed border-border/70 bg-muted/30 text-muted-foreground opacity-80"
                  : isSelected
                  ? "border-primary bg-muted/60 shadow-sm ring-1 ring-primary/20"
                  : "border-border bg-background/70 hover:border-primary/30 hover:bg-secondary/60",
              )}
            >
              <span className="min-w-0">
                <span>{name}</span>
                {(school || isDisabled) && (
                  <span className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                    {school && <span>{school}</span>}
                    {isDisabled && (
                      <span className="rounded-full border border-border/70 bg-background px-2 py-0.5 uppercase tracking-wide">
                        Always prepared
                      </span>
                    )}
                  </span>
                )}
              </span>
              <span
                className={cn(
                  "inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border",
                  isDisabled
                    ? "border-border/70 bg-background text-muted-foreground"
                    : isSelected
                    ? "border-primary bg-background text-primary"
                    : "border-border bg-background text-transparent",
                )}
              >
                <Check className="h-3 w-3" />
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function BackgroundSpells({
  requirements,
  current,
  update,
  disabledNames,
}: {
  requirements: Loose;
  current: CurrentSpellSelections;
  update: (patch: Partial<CurrentSpellSelections>) => void;
  disabledNames?: Set<string>;
}) {
  const cantripReq = rec(requirements.cantrips);
  const spellReq = rec(requirements.spells);
  const cantripsNeeded = num(cantripReq.count);
  const spellsNeeded = num(spellReq.count);
  if (!cantripsNeeded && !spellsNeeded) return null;

  return (
    <div className="border-t border-border pt-3 space-y-3">
      <div className="text-xs uppercase text-muted-foreground">
        Background spells
      </div>
      {cantripsNeeded ? (
        <SpellGroup
          title={`Background cantrips (${current.background_cantrips.length}/${cantripsNeeded})`}
          spells={arr<Loose>(cantripReq.available)}
          selected={current.background_cantrips}
          disabledNames={disabledNames}
          onToggle={(name) => {
            const list = current.background_cantrips;
            if (list.includes(name)) {
              update({
                background_cantrips: list.filter((n) => n !== name),
              });
            } else if (list.length < cantripsNeeded) {
              update({ background_cantrips: [...list, name] });
            }
          }}
        />
      ) : null}
      {spellsNeeded ? (
        <SpellGroup
          title={`Background spells (${current.background_spells.length}/${spellsNeeded})`}
          spells={arr<Loose>(spellReq.available)}
          selected={current.background_spells}
          disabledNames={disabledNames}
          onToggle={(name) => {
            const list = current.background_spells;
            if (list.includes(name)) {
              update({
                background_spells: list.filter((n) => n !== name),
              });
            } else if (list.length < spellsNeeded) {
              update({ background_spells: [...list, name] });
            }
          }}
        />
      ) : null}
    </div>
  );
}

function normalizeCurrent(raw: Loose): CurrentSpellSelections {
  return {
    cantrips: arr<string>(raw.cantrips),
    spells: arr<string>(raw.spells),
    background_cantrips: arr<string>(raw.background_cantrips),
    background_spells: arr<string>(raw.background_spells),
  };
}

// ---------- Weapon Masteries ----------

function MasteryPicker({ data }: { data: Loose }) {
  const setChoice = useCharacterStore((s) => s.setChoice);
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const max = num(data.max_masteries) ?? 0;
  const available = arr<string>(data.available_weapons);
  const masteries = rec(data.weapon_masteries);
  const current =
    (choicesMade["weapon_mastery_selections"] as string[] | undefined) ??
    arr<string>(data.current_masteries);

  function toggle(name: string) {
    const list = current;
    if (list.includes(name)) {
      setChoice(
        "weapon_mastery_selections",
        list.filter((n) => n !== name),
      );
    } else if (list.length < max) {
      setChoice("weapon_mastery_selections", [...list, name]);
    }
  }

  if (max === 0) return null;
  return (
    <div className="rounded-xl border border-border/70 bg-background/70 p-4 shadow-sm sm:p-5">
      <header className="mb-3">
        <h4 className="font-display text-base text-primary">Weapon Masteries</h4>
        <p className="text-xs text-muted-foreground">
          {current.length}/{max} chosen
        </p>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
        {available.map((weapon) => {
          const isSelected = current.includes(weapon);
          const mastery = str(masteries[weapon]);
          return (
            <button
              key={weapon}
              type="button"
              onClick={() => toggle(weapon)}
              aria-pressed={isSelected}
              className={cn(
                "flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left text-sm transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                isSelected
                  ? "border-primary bg-muted/60 shadow-sm ring-1 ring-primary/20"
                  : "border-border bg-background/70 hover:border-primary/30 hover:bg-secondary/60",
              )}
            >
              <span className="min-w-0">
                <span>{weapon}</span>
                {mastery && (
                  <span className="ml-2 text-xs text-muted-foreground">
                    {mastery}
                  </span>
                )}
              </span>
              <span
                className={cn(
                  "inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border",
                  isSelected
                    ? "border-primary bg-background text-primary"
                    : "border-border bg-background text-transparent",
                )}
              >
                <Check className="h-3 w-3" />
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------- Eldritch Invocations ----------

function InvocationPicker({ data }: { data: Loose }) {
  const setChoice = useCharacterStore((s) => s.setChoice);
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const max = num(data.max_invocations) ?? 0;
  const available = arr<Loose>(data.available_invocations);
  const current =
    (choicesMade["eldritch_invocation_selections"] as string[] | undefined) ??
    arr<string>(data.current_invocations);

  function toggle(name: string) {
    const list = current;
    if (list.includes(name)) {
      setChoice(
        "eldritch_invocation_selections",
        list.filter((n) => n !== name),
      );
    } else if (list.length < max) {
      setChoice("eldritch_invocation_selections", [...list, name]);
    }
  }

  if (max === 0) return null;
  return (
    <div className="rounded-xl border border-border/70 bg-background/70 p-4 shadow-sm sm:p-5">
      <header className="mb-3">
        <h4 className="flex items-center gap-2 font-display text-base text-primary">
          <Wand2 className="h-4 w-4" />
          Eldritch Invocations
        </h4>
        <p className="text-xs text-muted-foreground">
          {current.length}/{max} chosen
        </p>
      </header>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {available.map((inv, i) => {
          const name = str(inv.name) ?? `Invocation ${i}`;
          const description = str(inv.description);
          const isSelected = current.includes(name);
          return (
            <button
              key={`${name}-${i}`}
              type="button"
              onClick={() => toggle(name)}
              aria-pressed={isSelected}
              className={cn(
                "rounded-lg border p-3 text-left transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                isSelected
                  ? "border-primary bg-muted/60 shadow-sm ring-1 ring-primary/20"
                  : "border-border bg-background/70 hover:border-primary/30 hover:bg-secondary/60",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="text-sm font-medium">{name}</div>
                <span
                  className={cn(
                    "inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border",
                    isSelected
                      ? "border-primary bg-background text-primary"
                      : "border-border bg-background text-transparent",
                  )}
                >
                  <Check className="h-3 w-3" />
                </span>
              </div>
              {description && (
                <div className="text-xs text-muted-foreground line-clamp-3 mt-1">
                  {description}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
