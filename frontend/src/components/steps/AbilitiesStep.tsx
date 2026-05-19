import { useEffect, useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { AlertCircle, Check, ChevronDown, ChevronUp, Dice6, Info, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";

const ABILITIES = [
  "Strength",
  "Dexterity",
  "Constitution",
  "Intelligence",
  "Wisdom",
  "Charisma",
] as const;
type Ability = (typeof ABILITIES)[number];

const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8] as const;

// D&D 2024 point-buy table (matches modules/ability_scores.POINT_BUY_COSTS).
const POINT_BUY_COSTS: Record<number, number> = {
  8: 0,
  9: 1,
  10: 2,
  11: 3,
  12: 4,
  13: 5,
  14: 7,
  15: 9,
};
const POINT_BUY_MIN = 8;
const POINT_BUY_MAX = 15;
const POINT_BUY_TOTAL = 27;
const MANUAL_MIN = 3;
const MANUAL_MAX = 18;
const EXTRA_MOD_MIN = -5;
const EXTRA_MOD_MAX = 5;

type Method = "standard_array" | "point_buy" | "manual" | "recommended";
type RollAssignments = Record<Ability, number | null>;

const EMPTY_ROLL_ASSIGNMENTS: RollAssignments = {
  Strength: null,
  Dexterity: null,
  Constitution: null,
  Intelligence: null,
  Wisdom: null,
  Charisma: null,
};

function defaultScores(
  method: Method,
  recommended?: Record<string, number>,
): Partial<Record<Ability, number>> {
  if (method === "standard_array") {
    return {};
  }
  if (method === "recommended" && recommended) {
    return Object.fromEntries(
      ABILITIES.map((a) => [a, Number(recommended[a] ?? 10)]),
    ) as Record<Ability, number>;
  }
  return Object.fromEntries(ABILITIES.map((a) => [a, 8])) as Record<
    Ability,
    number
  >;
}

function normalizeMethod(method: unknown): Method {
  if (method === "roll" || method === "manual") return "manual";
  if (
    method === "standard_array" ||
    method === "point_buy" ||
    method === "recommended"
  ) {
    return method;
  }
  return "standard_array";
}

function formatModifier(score: number) {
  const mod = Math.floor((score - 10) / 2);
  return mod >= 0 ? `+${mod}` : `${mod}`;
}

function modifierColor(score: number): string {
  const mod = Math.floor((score - 10) / 2);
  if (mod > 0) return "text-green-600 dark:text-green-400";
  if (mod < 0) return "text-destructive/80";
  return "text-muted-foreground";
}

function roll4d6DropLowest() {
  const rolls = Array.from({ length: 4 }, () => Math.floor(Math.random() * 6) + 1);
  // Descending sort keeps the highest three values in indices 0..2.
  rolls.sort((a, b) => b - a);
  return rolls[0] + rolls[1] + rolls[2];
}

interface BackgroundAsi {
  total_points?: number;
  suggested?: Record<string, number>;
  ability_options?: string[];
}

export function AbilitiesStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);

  const method = normalizeMethod(choicesMade["ability_scores_method"]);

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "abilities", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "abilities"),
    placeholderData: keepPreviousData,
  });
  const recommended = previewQuery.data?.recommended_array as
    | Record<string, number>
    | undefined;
  const asi = (previewQuery.data?.background_asi as BackgroundAsi | undefined) ??
    { total_points: 3, suggested: {}, ability_options: [...ABILITIES] };

  const storedScores = (choicesMade["ability_scores"] as
    | Record<string, unknown>
    | undefined) ??
    {};
  const fallbackScores = defaultScores(method, recommended);

  const scores = ABILITIES.reduce(
    (acc, a) => {
      const stored = Number(storedScores[a]);
      if (Number.isFinite(stored)) {
        acc[a] = stored;
      } else if (typeof fallbackScores[a] === "number") {
        acc[a] = Number(fallbackScores[a]);
      } else {
        acc[a] = 8;
      }
      return acc;
    },
    {} as Record<Ability, number>,
  );

  const standardArrayAssignments = ABILITIES.reduce(
    (acc, a) => {
      const value = Number(storedScores[a]);
      acc[a] = STANDARD_ARRAY.includes(value as (typeof STANDARD_ARRAY)[number])
        ? value
        : "";
      return acc;
    },
    {} as Record<Ability, number | "">,
  );

  const [rolledValues, setRolledValues] = useState<number[]>([]);
  const [rollAssignments, setRollAssignments] =
    useState<RollAssignments>(EMPTY_ROLL_ASSIGNMENTS);

  function setMethod(next: Method) {
    setChoice("ability_scores_method", next);
    setChoice("ability_scores", defaultScores(next, recommended));
  }

  // Keep `recommended` mode in sync with whatever the class-recommended
  // array currently is (e.g. after switching class).
  useEffect(() => {
    if (method !== "recommended" || !recommended) return;
    const current = (choicesMade["ability_scores"] as
      | Record<string, number>
      | undefined) ??
      {};
    const matches = ABILITIES.every(
      (a) => Number(current[a]) === Number(recommended[a]),
    );
    if (!matches) {
      setChoice("ability_scores", defaultScores("recommended", recommended));
    }
  }, [method, recommended, choicesMade, setChoice]);

  function setScore(ability: Ability, value: number) {
    const next = { ...scores, [ability]: value };
    setChoice("ability_scores", next);
  }

  function setStandardArrayScore(ability: Ability, value: number | "") {
    const next = { ...standardArrayAssignments, [ability]: value };
    const normalized = ABILITIES.reduce(
      (acc, a) => {
        const picked = next[a];
        if (typeof picked === "number") acc[a] = picked;
        return acc;
      },
      {} as Partial<Record<Ability, number>>,
    );
    setChoice("ability_scores", normalized);
  }

  function decrementPointBuy(ability: Ability) {
    if (scores[ability] <= POINT_BUY_MIN) return;
    setScore(ability, scores[ability] - 1);
  }

  function incrementPointBuy(ability: Ability) {
    const score = scores[ability];
    if (score >= POINT_BUY_MAX) return;
    const delta = (POINT_BUY_COSTS[score + 1] ?? POINT_BUY_TOTAL) - POINT_BUY_COSTS[score];
    if (pointSpend + delta > POINT_BUY_TOTAL) return;
    setScore(ability, score + 1);
  }

  function rollAllAbilityScores() {
    setRolledValues(Array.from({ length: 6 }, () => roll4d6DropLowest()));
    setRollAssignments(EMPTY_ROLL_ASSIGNMENTS);
  }

  function assignRolledValue(ability: Ability, index: number | null) {
    setRollAssignments((prev) => ({ ...prev, [ability]: index }));
  }

  function applyRollAssignments() {
    const complete = ABILITIES.every((a) => rollAssignments[a] !== null);
    if (!complete || rolledValues.length !== 6) return;

    const assigned = ABILITIES.reduce(
      (acc, ability) => {
        const index = rollAssignments[ability];
        if (index !== null) acc[ability] = rolledValues[index] ?? 8;
        return acc;
      },
      {} as Record<Ability, number>,
    );

    setChoice("ability_scores_method", "manual");
    setChoice("ability_scores", assigned);
  }

  // Standard array: each value used once.
  const arraySelections = ABILITIES.map((a) => standardArrayAssignments[a]).filter(
    (v): v is number => typeof v === "number",
  );
  const arrayComplete = arraySelections.length === ABILITIES.length;
  const arrayValid =
    method !== "standard_array" ||
    (arrayComplete &&
      [...arraySelections].sort((a, b) => a - b).join(",") ===
        [...STANDARD_ARRAY].sort((a, b) => a - b).join(","));

  // Point buy: total spend.
  const pointSpend =
    method === "point_buy"
      ? ABILITIES.reduce((sum, a) => sum + (POINT_BUY_COSTS[scores[a]] ?? 0), 0)
      : 0;

  const additionalStored = (choicesMade["additional_ability_modifiers"] as
    | Record<string, number>
    | undefined) ??
    {};
  const additionalModifiers = ABILITIES.reduce(
    (acc, ability) => {
      acc[ability] = Number(additionalStored[ability] ?? 0);
      return acc;
    },
    {} as Record<Ability, number>,
  );

  function setAdditionalModifier(ability: Ability, value: number) {
    const next = {
      ...additionalModifiers,
      [ability]: Math.max(EXTRA_MOD_MIN, Math.min(EXTRA_MOD_MAX, value)),
    };
    const compact = Object.fromEntries(
      Object.entries(next).filter(([, v]) => Number(v) !== 0),
    );
    setChoice("additional_ability_modifiers", compact);
  }

  const methodButtons = [
    ["standard_array", "Standard array"],
    ["point_buy", "Point buy"],
    ["manual", "Manual / Roll"],
    ["recommended", "Recommended"],
  ] as Array<[Method, string]>;

  const rollAssignmentsComplete =
    rolledValues.length === 6 && ABILITIES.every((a) => rollAssignments[a] !== null);

  return (
    <div className="space-y-8">

      {/* ── Generation method ─────────────────────────────────────────── */}
      <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
        <div className="border-b border-border/70 px-5 py-5 sm:px-6">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2 text-primary">
              <Dice6 className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">
                Step 1 of 2
              </p>
              <h3 className="mt-1 font-display text-2xl text-primary font-bold">
                Generation method
              </h3>
              <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
                Choose how to determine your six ability scores. Standard array and Point Buy are the balanced options; roll or enter values manually for a more adventurous approach.
              </p>
            </div>
          </div>
        </div>

        <div className="px-5 py-5 sm:px-6 space-y-4">
          <div className="flex flex-wrap gap-2">
            {methodButtons.map(([id, label]) => {
              const disabled = id === "recommended" && !recommended;
              const isSelected = method === id;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => !disabled && setMethod(id)}
                  disabled={disabled}
                  aria-pressed={isSelected}
                  title={disabled ? "Pick a class to see its recommended array." : undefined}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-medium transition-all duration-200",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    isSelected
                      ? "border-primary bg-muted/60 text-foreground shadow-sm ring-1 ring-primary/20"
                      : "border-border/80 bg-background/75 text-muted-foreground hover:bg-secondary/50 hover:border-primary/40 hover:text-foreground",
                    disabled && "cursor-not-allowed opacity-40",
                  )}
                >
                  {isSelected && <Check className="h-3.5 w-3.5 text-primary" />}
                  {label}
                </button>
              );
            })}
          </div>

          {method === "recommended" && recommended && (
            <div className="flex items-start gap-2 rounded-lg border border-border/60 bg-secondary/30 px-4 py-3">
              <Info className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
              <p className="text-sm text-muted-foreground">
                Uses the suggested array for your class. Switch to{" "}
                <strong className="text-foreground">Standard array</strong>,{" "}
                <strong className="text-foreground">Point buy</strong>, or{" "}
                <strong className="text-foreground">Manual / Roll</strong> to customize.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* ── Roll helper (manual mode only) ────────────────────────────── */}
      {method === "manual" && (
        <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
          <div className="border-b border-border/70 px-5 py-4 sm:px-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold text-lg">Roll helper</h3>
                <p className="text-sm text-muted-foreground">
                  4d6 drop lowest × 6 — then assign each result to an ability.
                </p>
              </div>
              <button
                type="button"
                onClick={rollAllAbilityScores}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg border border-primary bg-primary px-4 py-2 text-sm font-medium text-primary-foreground",
                  "transition-all duration-200 hover:-translate-y-0.5 hover:opacity-95",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                )}
              >
                <Dice6 className="h-4 w-4" />
                Roll now
              </button>
            </div>
          </div>

          {rolledValues.length > 0 && (
            <div className="px-5 py-5 sm:px-6 space-y-5">
              {/* Dice chips — one per rolled value */}
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Rolled values</p>
                <div className="flex flex-wrap gap-2">
                  {rolledValues.map((value, idx) => {
                    const assignedTo = ABILITIES.find((a) => rollAssignments[a] === idx);
                    const mod = Math.floor((value - 10) / 2);
                    const modStr = mod >= 0 ? `+${mod}` : `${mod}`;
                    return (
                      <div
                        key={idx}
                        className={cn(
                          "flex flex-col items-center rounded-xl border px-3 py-2 min-w-[54px] transition-all duration-200",
                          assignedTo
                            ? "border-border/50 bg-muted/30 opacity-50"
                            : "border-border/80 bg-background/80 shadow-sm",
                        )}
                      >
                        <span className="text-xl font-bold text-foreground leading-tight">{value}</span>
                        <span className={cn("text-xs font-medium", modifierColor(value))}>{modStr}</span>
                        {assignedTo && (
                          <span className="text-[10px] uppercase tracking-wider text-muted-foreground mt-0.5">
                            {assignedTo.slice(0, 3)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {ABILITIES.map((ability) => {
                  const current = rollAssignments[ability];
                  const usedByOthers = new Set<number>(
                    ABILITIES.filter((a) => a !== ability)
                      .map((a) => rollAssignments[a])
                      .filter((i): i is number => i !== null),
                  );
                  const options = rolledValues
                    .map((value, idx) => ({ value, idx }))
                    .filter(({ idx }) => idx === current || !usedByOthers.has(idx));

                  return (
                    <div key={`roll-${ability}`} className="rounded-xl border border-border/80 bg-background/75 px-3 py-3">
                      <label
                        htmlFor={`roll-assignment-${ability}`}
                        className="text-xs uppercase tracking-[0.2em] text-muted-foreground"
                      >
                        {ability}
                      </label>
                      <select
                        id={`roll-assignment-${ability}`}
                        value={current === null ? "" : String(current)}
                        onChange={(e) =>
                          assignRolledValue(
                            ability,
                            e.target.value === "" ? null : Number(e.target.value),
                          )
                        }
                        className={cn(
                          "mt-2 w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm",
                          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
                        )}
                      >
                        <option value="">— assign —</option>
                        {options.map(({ value, idx }) => (
                          <option key={`${ability}-${idx}-${value}`} value={idx}>
                            {value}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>

              <button
                type="button"
                onClick={applyRollAssignments}
                disabled={!rollAssignmentsComplete}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-medium transition-all duration-200",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  rollAssignmentsComplete
                    ? "border-primary bg-primary text-primary-foreground shadow-sm hover:-translate-y-0.5 hover:opacity-95"
                    : "cursor-not-allowed border-border bg-muted text-muted-foreground opacity-60",
                )}
              >
                {rollAssignmentsComplete && <Check className="h-3.5 w-3.5" />}
                Apply assignments
              </button>
            </div>
          )}
        </section>
      )}

      {/* ── Assign scores ─────────────────────────────────────────────── */}
      <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
        <div className="border-b border-border/70 px-5 py-4 sm:px-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-semibold text-lg">Assign scores</h3>
              {method === "standard_array" && (
                <p className="text-sm text-muted-foreground">
                  Assign each of {STANDARD_ARRAY.join(", ")} to exactly one ability.
                </p>
              )}
              {method === "point_buy" && (
                <p className="text-sm text-muted-foreground">
                  Spend up to {POINT_BUY_TOTAL} points. Higher scores cost more.
                </p>
              )}
              {method === "recommended" && (
                <p className="text-sm text-muted-foreground">
                  Class-recommended allocation — read-only.
                </p>
              )}
              {method === "manual" && (
                <p className="text-sm text-muted-foreground">
                  Enter scores between {MANUAL_MIN} and {MANUAL_MAX} for each ability.
                </p>
              )}
            </div>

            {method === "point_buy" && (
              <div className={cn(
                "flex-shrink-0 rounded-lg border px-3 py-2 text-center min-w-[108px]",
                pointSpend > POINT_BUY_TOTAL
                  ? "border-destructive/40 bg-destructive/10 text-destructive"
                  : pointSpend === POINT_BUY_TOTAL
                    ? "border-green-500/40 bg-green-500/10 text-green-700 dark:text-green-400"
                    : "border-border bg-secondary/30 text-muted-foreground",
              )}>
                {pointSpend > POINT_BUY_TOTAL ? (
                  <>
                    <p className="text-xs uppercase tracking-widest mb-0.5">Over budget</p>
                    <p className="text-lg font-bold">+{pointSpend - POINT_BUY_TOTAL}</p>
                  </>
                ) : pointSpend === POINT_BUY_TOTAL ? (
                  <>
                    <p className="text-xs uppercase tracking-widest mb-0.5">Complete</p>
                    <p className="text-lg font-bold flex items-center justify-center gap-1">
                      <Check className="h-5 w-5" />
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-xs uppercase tracking-widest mb-0.5">Remaining</p>
                    <p className="text-lg font-bold">{POINT_BUY_TOTAL - pointSpend}</p>
                  </>
                )}
              </div>
            )}

            {method === "standard_array" && (
              <div className={cn(
                "flex-shrink-0 rounded-lg border px-3 py-2 text-center min-w-[100px]",
                arrayComplete
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-border bg-secondary/30 text-muted-foreground",
              )}>
                <p className="text-xs uppercase tracking-widest mb-0.5">Assigned</p>
                <p className="text-lg font-bold">
                  {arraySelections.length}
                  <span className="text-sm font-normal">/{ABILITIES.length}</span>
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="px-5 py-5 sm:px-6 space-y-4">
          {previewQuery.isLoading && method === "recommended" && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading recommended scores…
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ABILITIES.map((ability) => {
              const currentScore = scores[ability];
              const pointBuyIncrementCost =
                (POINT_BUY_COSTS[currentScore + 1] ?? POINT_BUY_TOTAL + 1) -
                (POINT_BUY_COSTS[currentScore] ?? 0);
              const canPointBuyDecrement = currentScore > POINT_BUY_MIN;
              const canPointBuyIncrement =
                currentScore < POINT_BUY_MAX &&
                pointSpend + pointBuyIncrementCost <= POINT_BUY_TOTAL;

              const displayScore =
                method === "standard_array"
                  ? standardArrayAssignments[ability] || null
                  : currentScore;

              return (
                <div
                  key={ability}
                  className="rounded-xl border border-border/80 bg-background/75 p-4"
                >
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">
                    {ability}
                  </p>

                  {/* Score + modifier display */}
                  {method !== "standard_array" && (
                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="text-2xl font-bold text-foreground">
                        {displayScore ?? "—"}
                      </span>
                      {displayScore !== null && (
                        <span className={cn("text-sm font-medium", modifierColor(displayScore))}>
                          {formatModifier(displayScore)}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Controls */}
                  {method === "standard_array" ? (
                    <div>
                      <div className="flex items-baseline gap-2 mb-2">
                        <span className="text-2xl font-bold text-foreground">
                          {standardArrayAssignments[ability] || "—"}
                        </span>
                        {standardArrayAssignments[ability] && (
                          <span className={cn("text-sm font-medium", modifierColor(standardArrayAssignments[ability] as number))}>
                            {formatModifier(standardArrayAssignments[ability] as number)}
                          </span>
                        )}
                      </div>
                      <select
                        id={`score-${ability}`}
                        value={String(standardArrayAssignments[ability] || "")}
                        onChange={(e) =>
                          setStandardArrayScore(
                            ability,
                            e.target.value === "" ? "" : Number(e.target.value),
                          )
                        }
                        className={cn(
                          "w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm",
                          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
                        )}
                      >
                        <option value="">— choose —</option>
                        {STANDARD_ARRAY.filter((value) => {
                          const current = standardArrayAssignments[ability];
                          if (current === value) return true;
                          return !ABILITIES.some(
                            (a) => a !== ability && standardArrayAssignments[a] === value,
                          );
                        }).map((value) => (
                          <option key={`${ability}-${value}`} value={value}>
                            {value}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : method === "point_buy" ? (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => decrementPointBuy(ability)}
                        disabled={!canPointBuyDecrement}
                        aria-label={`Decrease ${ability}`}
                        className={cn(
                          "h-8 w-8 rounded-md border text-sm font-bold transition-colors",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                          canPointBuyDecrement
                            ? "border-border hover:bg-secondary/60 hover:border-primary/40"
                            : "cursor-not-allowed border-border opacity-40",
                        )}
                      >
                        <ChevronDown className="h-4 w-4 mx-auto" />
                      </button>
                      <button
                        type="button"
                        onClick={() => incrementPointBuy(ability)}
                        disabled={!canPointBuyIncrement}
                        aria-label={`Increase ${ability}`}
                        className={cn(
                          "h-8 w-8 rounded-md border text-sm font-bold transition-colors",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                          canPointBuyIncrement
                            ? "border-border hover:bg-secondary/60 hover:border-primary/40"
                            : "cursor-not-allowed border-border opacity-40",
                        )}
                      >
                        <ChevronUp className="h-4 w-4 mx-auto" />
                      </button>
                      {method === "point_buy" && (
                        <span className="text-xs text-muted-foreground">
                          costs {POINT_BUY_COSTS[currentScore] ?? 0} pts
                        </span>
                      )}
                    </div>
                  ) : method === "recommended" ? null : (
                    <div className="flex items-center gap-2">
                      <input
                        id={`score-${ability}`}
                        type="number"
                        min={MANUAL_MIN}
                        max={MANUAL_MAX}
                        value={currentScore}
                        onChange={(e) =>
                          setScore(
                            ability,
                            Math.max(
                              MANUAL_MIN,
                              Math.min(MANUAL_MAX, Number(e.target.value) || MANUAL_MIN),
                            ),
                          )
                        }
                        className={cn(
                          "w-20 rounded-md border border-input bg-background px-3 py-1.5 text-sm",
                          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
                        )}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {!arrayValid && method === "standard_array" && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-destructive text-sm mb-1">
                    Incomplete assignment
                  </h4>
                  <p className="text-sm text-destructive/80">
                    Each value in the standard array must be used exactly once before continuing.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── Additional modifiers (optional) ───────────────────────────── */}
      <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
        <div className="border-b border-border/70 px-5 py-4 sm:px-6">
          <h3 className="font-semibold text-lg">
            Additional modifiers
            <span className="text-sm font-normal text-muted-foreground ml-2">(Optional)</span>
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Applied on top of base scores and background bonuses — for magic items, feats, or DM rulings.
          </p>
        </div>

        <div className="px-5 py-5 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {ABILITIES.map((ability) => {
              const value = additionalModifiers[ability];
              const canDown = value > EXTRA_MOD_MIN;
              const canUp = value < EXTRA_MOD_MAX;
              return (
                <div
                  key={`additional-${ability}`}
                  className="rounded-xl border border-border/80 bg-background/75 px-3 py-3"
                >
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-2">
                    {ability.slice(0, 3)}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => setAdditionalModifier(ability, value - 1)}
                      disabled={!canDown}
                      aria-label={`Decrease ${ability} modifier`}
                      className={cn(
                        "h-7 w-7 rounded-md border text-xs font-bold transition-colors",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                        canDown
                          ? "border-border hover:bg-secondary/60 hover:border-primary/40"
                          : "cursor-not-allowed border-border opacity-40",
                      )}
                    >
                      −
                    </button>
                    <div className={cn(
                      "h-7 min-w-[44px] rounded-md border border-input bg-background px-2 text-center text-sm leading-7 font-medium",
                      value > 0 && "text-green-600 dark:text-green-400",
                      value < 0 && "text-destructive/80",
                    )}>
                      {value >= 0 ? `+${value}` : value}
                    </div>
                    <button
                      type="button"
                      onClick={() => setAdditionalModifier(ability, value + 1)}
                      disabled={!canUp}
                      aria-label={`Increase ${ability} modifier`}
                      className={cn(
                        "h-7 w-7 rounded-md border text-xs font-bold transition-colors",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                        canUp
                          ? "border-border hover:bg-secondary/60 hover:border-primary/40"
                          : "cursor-not-allowed border-border opacity-40",
                      )}
                    >
                      +
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <BackgroundAsiPicker
        asi={asi}
        hasBackground={!!choicesMade["background"]}
      />
    </div>
  );
}

function BackgroundAsiPicker({
  asi,
  hasBackground,
}: {
  asi: BackgroundAsi;
  hasBackground: boolean;
}) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const total = asi.total_points ?? 3;
  const options = (asi.ability_options ?? ABILITIES) as string[];
  const stored =
    (choicesMade["background_bonuses"] as Record<string, number> | undefined) ??
    {};

  const spent = Object.values(stored).reduce(
    (sum, v) => sum + Math.max(0, Number(v) || 0),
    0,
  );
  const remaining = total - spent;

  function setBonus(ability: string, value: number) {
    const next = { ...stored, [ability]: value };
    // Drop zeros so the payload stays tidy.
    if (value <= 0) delete next[ability];
    setChoice("background_bonuses", next);
  }

  function applySuggested() {
    if (asi.suggested) setChoice("background_bonuses", asi.suggested);
  }

  if (total <= 0) return null;

  if (!hasBackground) {
    return (
      <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
        <div className="px-5 py-5 sm:px-6">
          <h3 className="font-semibold text-lg mb-1">Background ability bonuses</h3>
          <p className="text-sm text-muted-foreground">
            No background selected yet — pick a background first to distribute its ability bonuses here.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-2xl border border-border/80 bg-gradient-to-br from-card via-card to-secondary/40 shadow-sm">
      <div className="border-b border-border/70 px-5 py-4 sm:px-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="font-semibold text-lg">Background ability bonuses</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Distribute {total} point{total === 1 ? "" : "s"} across abilities (max +2 per ability).{" "}
              <span className={cn(
                "font-medium",
                remaining === 0 ? "text-green-600 dark:text-green-400" : "text-muted-foreground",
              )}>
                {remaining} remaining.
              </span>
            </p>
          </div>
          {asi.suggested && Object.keys(asi.suggested).length > 0 && (
            <button
              type="button"
              onClick={applySuggested}
              className={cn(
                "flex-shrink-0 inline-flex items-center gap-1.5 rounded-lg border border-border/80 px-3 py-2 text-sm font-medium",
                "bg-background/75 text-muted-foreground hover:bg-secondary/50 hover:border-primary/40 hover:text-foreground",
                "transition-all duration-200",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              )}
            >
              Use suggested
            </button>
          )}
        </div>
      </div>

      <div className="px-5 py-5 sm:px-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {options.map((ability) => {
            const v = Number(stored[ability] ?? 0);
            return (
              <div
                key={ability}
                className="rounded-xl border border-border/80 bg-background/75 px-3 py-3"
              >
                <label
                  htmlFor={`bonus-${ability}`}
                  className="text-xs uppercase tracking-[0.2em] text-muted-foreground"
                >
                  {ability.slice(0, 3)}
                </label>
                <div className="flex items-baseline gap-2 mt-1 mb-2">
                  <span className={cn(
                    "text-xl font-bold",
                    v > 0 ? "text-green-600 dark:text-green-400" : "text-muted-foreground",
                  )}>
                    +{v}
                  </span>
                </div>
                <select
                  id={`bonus-${ability}`}
                  value={v}
                  onChange={(e) => setBonus(ability, Number(e.target.value))}
                  className={cn(
                    "w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm",
                    "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-1",
                  )}
                >
                  {[0, 1, 2].map((opt) => {
                    const wouldExceed = spent - v + opt > total;
                    return (
                      <option key={opt} value={opt} disabled={wouldExceed}>
                        +{opt}{wouldExceed ? " (over budget)" : ""}
                      </option>
                    );
                  })}
                </select>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
