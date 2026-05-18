import { useEffect, useMemo, useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
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

  const rolledCounts = useMemo(() => {
    const counts = new Map<number, number>();
    for (const value of rolledValues) {
      counts.set(value, (counts.get(value) ?? 0) + 1);
    }
    return counts;
  }, [rolledValues]);

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <h3 className="text-sm font-semibold">Generation method</h3>
        <div className="flex flex-wrap gap-2">
          {methodButtons.map(([id, label]) => {
            const disabled = id === "recommended" && !recommended;
            return (
              <button
                key={id}
                type="button"
                onClick={() => !disabled && setMethod(id)}
                disabled={disabled}
                title={
                  disabled ? "Pick a class to see its recommended array." : undefined
                }
                className={
                  "rounded-md border px-3 py-2 text-sm transition-colors " +
                  (method === id
                    ? "border-primary bg-secondary"
                    : "border-border hover:bg-secondary/60") +
                  (disabled ? " opacity-40 cursor-not-allowed" : "")
                }
              >
                {label}
              </button>
            );
          })}
        </div>
        {method === "recommended" && recommended && (
          <p className="text-xs text-muted-foreground">
            Uses the suggested array for your class. Switch to <strong>Standard array</strong>,{" "}
            <strong>Point buy</strong>, or <strong>Manual / Roll</strong> to customize.
          </p>
        )}
      </section>

      {method === "manual" && (
        <section className="rounded-md border border-border bg-card/40 p-4 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">Roll helper (4d6 drop lowest × 6)</h3>
            <button
              type="button"
              onClick={rollAllAbilityScores}
              className="rounded border border-border px-2 py-1 text-xs bg-primary text-primary-foreground hover:translate-y-[-1px] hover:opacity-95"
              
            >
              Roll now
            </button>
          </div>

          {rolledValues.length > 0 && (
            <>
              <p className="text-xs text-muted-foreground">
                Rolled values: {Array.from(rolledCounts.entries())
                  .map(([value, count]) => (count > 1 ? `${value}×${count}` : `${value}`))
                  .join(", ")}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
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
                    <div key={`roll-${ability}`} className="rounded border border-border px-2 py-1">
                      <label
                        htmlFor={`roll-assignment-${ability}`}
                        className="text-xs uppercase text-muted-foreground"
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
                        className="mt-1 w-full rounded border border-input bg-background px-2 py-1 text-sm"
                      >
                        <option value="">--</option>
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
                className={
                  "rounded border px-2 py-1 text-xs " +
                  (rollAssignmentsComplete
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:translate-y-[-1px] hover:opacity-95"
                    : "cursor-not-allowed bg-muted text-muted-foreground opacity-60")
                }
              >
                Apply roll assignments
              </button>
            </>
          )}
        </section>
      )}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold">Assign scores</h3>
          {method === "standard_array" && (
            <p className="text-xs text-muted-foreground">
              Use each of {STANDARD_ARRAY.join(", ")} exactly once.
            </p>
          )}
          {method === "point_buy" && (
            <p className="text-xs text-muted-foreground">
              {pointSpend} / {POINT_BUY_TOTAL} points spent
              {pointSpend > POINT_BUY_TOTAL ? " · over budget" : ""}
            </p>
          )}
          {method === "recommended" && (
            <p className="text-xs text-muted-foreground">
              Class-recommended allocation (read-only)
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {ABILITIES.map((ability) => {
            const pointBuyScore = scores[ability];
            const pointBuyIncrementCost =
              (POINT_BUY_COSTS[pointBuyScore + 1] ?? POINT_BUY_TOTAL + 1) -
              (POINT_BUY_COSTS[pointBuyScore] ?? 0);
            const canPointBuyDecrement = pointBuyScore > POINT_BUY_MIN;
            const canPointBuyIncrement =
              pointBuyScore < POINT_BUY_MAX &&
              pointSpend + pointBuyIncrementCost <= POINT_BUY_TOTAL;

            return (
              <div
                key={ability}
                className="rounded-md border border-border bg-card/40 p-3"
              >
                <label
                  htmlFor={`score-${ability}`}
                  className="text-xs uppercase tracking-widest text-muted-foreground"
                >
                  {ability}
                </label>
                {method === "standard_array" ? (
                  <select
                    id={`score-${ability}`}
                    value={String(standardArrayAssignments[ability] || "")}
                    onChange={(e) =>
                      setStandardArrayScore(
                        ability,
                        e.target.value === "" ? "" : Number(e.target.value),
                      )
                    }
                    className="mt-1 w-full rounded border border-input bg-background px-2 py-1 text-sm"
                  >
                    <option value="">--</option>
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
                ) : method === "point_buy" ? (
                  <div className="mt-1 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => decrementPointBuy(ability)}
                      disabled={!canPointBuyDecrement}
                      className={
                        "h-8 w-8 rounded border text-sm " +
                        (canPointBuyDecrement
                          ? "border-border hover:bg-secondary/60"
                          : "border-border opacity-50 cursor-not-allowed")
                      }
                    >
                      -
                    </button>
                    <div className="min-w-[96px] rounded border border-input bg-background px-2 py-1 text-center text-sm font-semibold">
                      {pointBuyScore} ({formatModifier(pointBuyScore)})
                    </div>
                    <button
                      type="button"
                      onClick={() => incrementPointBuy(ability)}
                      disabled={!canPointBuyIncrement}
                      className={
                        "h-8 w-8 rounded border text-sm " +
                        (canPointBuyIncrement
                          ? "border-border hover:bg-secondary/60"
                          : "border-border opacity-50 cursor-not-allowed")
                      }
                    >
                      +
                    </button>
                  </div>
                ) : method === "recommended" ? (
                  <div className="mt-1 flex items-baseline gap-2">
                    <span className="text-lg font-semibold">{scores[ability]}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatModifier(scores[ability])}
                    </span>
                  </div>
                ) : (
                  <div className="mt-1 flex items-center gap-2">
                    <input
                      id={`score-${ability}`}
                      type="number"
                      min={MANUAL_MIN}
                      max={MANUAL_MAX}
                      value={scores[ability]}
                      onChange={(e) =>
                        setScore(
                          ability,
                          Math.max(
                            MANUAL_MIN,
                            Math.min(MANUAL_MAX, Number(e.target.value) || MANUAL_MIN),
                          ),
                        )
                      }
                      className="w-20 rounded border border-input bg-background px-2 py-1 text-sm"
                    />
                    <span className="text-xs text-muted-foreground">
                      {formatModifier(scores[ability])}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {!arrayValid && method === "standard_array" && (
          <p className="mt-2 text-xs text-destructive">
            Standard array values must each be used exactly once before completing this step.
          </p>
        )}
      </section>

      <section className="rounded-md border border-border bg-card/40 p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold">Additional modifiers</h3>
          <p className="text-xs text-muted-foreground">
            Applied after base scores and background bonuses.
          </p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {ABILITIES.map((ability) => {
            const value = additionalModifiers[ability];
            const canDown = value > EXTRA_MOD_MIN;
            const canUp = value < EXTRA_MOD_MAX;
            return (
              <div
                key={`additional-${ability}`}
                className="rounded border border-border bg-background/40 px-2 py-1"
              >
                <p className="text-xs uppercase text-muted-foreground mb-1">
                  {ability.slice(0, 3)}
                </p>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setAdditionalModifier(ability, value - 1)}
                    disabled={!canDown}
                    className={
                      "h-7 w-7 rounded border text-xs " +
                      (canDown
                        ? "border-border hover:bg-secondary/60"
                        : "border-border opacity-50 cursor-not-allowed")
                    }
                  >
                    -
                  </button>
                  <div className="h-7 min-w-[44px] rounded border border-input bg-background px-2 text-center text-sm leading-7">
                    {value >= 0 ? `+${value}` : value}
                  </div>
                  <button
                    type="button"
                    onClick={() => setAdditionalModifier(ability, value + 1)}
                    disabled={!canUp}
                    className={
                      "h-7 w-7 rounded border text-xs " +
                      (canUp
                        ? "border-border hover:bg-secondary/60"
                        : "border-border opacity-50 cursor-not-allowed")
                    }
                  >
                    +
                  </button>
                </div>
              </div>
            );
          })}
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
      <section className="rounded-md border border-border bg-card/40 p-4">
        <h3 className="text-sm font-semibold mb-1">
          Background ability bonuses
        </h3>
        <p className="text-xs text-muted-foreground">
          No background selected. Pick a background first to distribute its
          ability bonuses.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-border bg-card/40 p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">Background ability bonuses</h3>
        {asi.suggested && Object.keys(asi.suggested).length > 0 && (
          <button
            type="button"
            onClick={applySuggested}
            className="text-xs text-primary underline"
          >
            Use suggested
          </button>
        )}
      </div>
      <p className="text-xs text-muted-foreground mb-3">
        Distribute {total} point{total === 1 ? "" : "s"} (no single ability may
        gain more than 2). {remaining} remaining.
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {options.map((ability) => {
          const v = Number(stored[ability] ?? 0);
          return (
            <div
              key={ability}
              className="rounded border border-border bg-background/40 px-2 py-1"
            >
              <label
                htmlFor={`bonus-${ability}`}
                className="text-xs uppercase text-muted-foreground"
              >
                {ability.slice(0, 3)}
              </label>
              <select
                id={`bonus-${ability}`}
                value={v}
                onChange={(e) => setBonus(ability, Number(e.target.value))}
                className="mt-1 w-full rounded border border-input bg-background px-2 py-0.5 text-sm"
              >
                {[0, 1, 2].map((opt) => (
                  <option key={opt} value={opt}>
                    +{opt}
                  </option>
                ))}
              </select>
            </div>
          );
        })}
      </div>
    </section>
  );
}
