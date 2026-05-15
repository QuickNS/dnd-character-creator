import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { ApiError, api } from "@/lib/api";
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

/**
 * Renders the spell, weapon-mastery, and eldritch-invocation pickers
 * inside the class step. Each picker silently hides itself when the
 * underlying derived view returns 400 ("not applicable to this build").
 */
export function ClassAdvancedChoices() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  const spellsQ = useDerived(choicesMade, "spell_management");
  const masteryQ = useDerived(choicesMade, "mastery_management");
  const invocationsQ = useDerived(choicesMade, "invocation_management");

  const anyVisible =
    isApplicable(spellsQ) ||
    isApplicable(masteryQ) ||
    isApplicable(invocationsQ);
  if (!anyVisible) return null;

  return (
    <section className="space-y-6">
      <h3 className="text-sm font-semibold">Class loadout</h3>
      {isApplicable(spellsQ) && spellsQ.data && (
        <SpellPicker data={spellsQ.data} />
      )}
      {isApplicable(masteryQ) && masteryQ.data && (
        <MasteryPicker data={masteryQ.data} />
      )}
      {isApplicable(invocationsQ) && invocationsQ.data && (
        <InvocationPicker data={invocationsQ.data} />
      )}
    </section>
  );
}

function useDerived(choicesMade: Loose, view: string) {
  return useQuery({
    queryKey: ["character", "derived", view, choicesMade],
    queryFn: () => api.character.derived(choicesMade, view),
    enabled: !!choicesMade["class"],
    retry: false,
    placeholderData: keepPreviousData,
  });
}

/** True when query succeeded — 400 means feature isn't applicable. */
function isApplicable(q: { data?: Loose; error: unknown }): boolean {
  if (q.data) return true;
  if (q.error instanceof ApiError && q.error.status === 400) return false;
  return false;
}

// ---------- Spells ----------

function SpellPicker({ data }: { data: Loose }) {
  const setChoice = useCharacterStore((s) => s.setChoice);
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  const limits = rec(data.limits);
  const maxCantrips = num(limits.cantrips) ?? 0;
  const maxSpells = num(limits.spells) ?? 0;

  const availableCantrips = arr<Loose>(data.available_cantrips);
  const availableSpellsByLevel = rec(data.available_spells);
  const alwaysPrepared = arr<Loose>(data.always_prepared);

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

  return (
    <div className="rounded-md border border-border bg-card/40 p-4 space-y-4">
      <header>
        <h4 className="font-display text-base text-primary">Spells</h4>
        <p className="text-xs text-muted-foreground">
          Cantrips {current.cantrips.length}/{maxCantrips} · Prepared spells{" "}
          {current.spells.length}/{maxSpells}
        </p>
      </header>

      {alwaysPrepared.length > 0 && (
        <div>
          <div className="text-xs uppercase text-muted-foreground mb-1">
            Always prepared
          </div>
          <ul className="text-xs text-muted-foreground space-x-2">
            {alwaysPrepared.map((sp, i) => (
              <li key={i} className="inline-block">
                {str(sp.name) ?? "Spell"}
              </li>
            ))}
          </ul>
        </div>
      )}

      {availableCantrips.length > 0 && maxCantrips > 0 && (
        <SpellGroup
          title="Cantrips"
          spells={availableCantrips}
          selected={current.cantrips}
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
      />
    </div>
  );
}

function SpellGroup({
  title,
  spells,
  selected,
  onToggle,
}: {
  title: string;
  spells: Loose[];
  selected: string[];
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
          return (
            <button
              key={`${name}-${i}`}
              type="button"
              onClick={() => onToggle(name)}
              className={
                "text-left rounded border px-2 py-1 text-sm transition-colors " +
                (isSelected
                  ? "border-primary bg-secondary"
                  : "border-border hover:bg-secondary/60")
              }
            >
              <span>{name}</span>
              {school && (
                <span className="ml-2 text-xs text-muted-foreground">
                  {school}
                </span>
              )}
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
}: {
  requirements: Loose;
  current: CurrentSpellSelections;
  update: (patch: Partial<CurrentSpellSelections>) => void;
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
    <div className="rounded-md border border-border bg-card/40 p-4">
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
              className={
                "text-left rounded border px-2 py-1 text-sm transition-colors " +
                (isSelected
                  ? "border-primary bg-secondary"
                  : "border-border hover:bg-secondary/60")
              }
            >
              <span>{weapon}</span>
              {mastery && (
                <span className="ml-2 text-xs text-muted-foreground">
                  {mastery}
                </span>
              )}
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
    <div className="rounded-md border border-border bg-card/40 p-4">
      <header className="mb-3">
        <h4 className="font-display text-base text-primary">
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
              className={
                "text-left rounded border p-2 transition-colors " +
                (isSelected
                  ? "border-primary bg-secondary"
                  : "border-border hover:bg-secondary/60")
              }
            >
              <div className="text-sm font-medium">{name}</div>
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
