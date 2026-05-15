import { useEffect } from "react";
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

type Method = "standard_array" | "point_buy" | "recommended";

function defaultScores(
  method: Method,
  recommended?: Record<string, number>,
): Record<Ability, number> {
  if (method === "standard_array") {
    return Object.fromEntries(
      ABILITIES.map((a, i) => [a, STANDARD_ARRAY[i] ?? 10]),
    ) as Record<Ability, number>;
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

interface BackgroundAsi {
  total_points?: number;
  suggested?: Record<string, number>;
  ability_options?: string[];
}

export function AbilitiesStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);

  const method = ((choicesMade["ability_scores_method"] as Method | undefined) ??
    "standard_array") as Method;

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

  const stored = (choicesMade["ability_scores"] as
    | Record<string, number>
    | undefined) ?? defaultScores(method, recommended);
  const scores = ABILITIES.reduce(
    (acc, a) => {
      acc[a] = Number(stored[a] ?? defaultScores(method, recommended)[a]);
      return acc;
    },
    {} as Record<Ability, number>,
  );

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
      | undefined) ?? {};
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

  // Standard array: each value used once. Show used set.
  const usedFromArray = new Set<number>(
    method === "standard_array" ? Object.values(scores) : [],
  );
  const arrayValid =
    method !== "standard_array" ||
    [...STANDARD_ARRAY].sort().join(",") ===
      [...Object.values(scores)].sort().join(",");

  // Point buy: total spend.
  const pointSpend =
    method === "point_buy"
      ? ABILITIES.reduce((sum, a) => sum + (POINT_BUY_COSTS[scores[a]] ?? 0), 0)
      : 0;
  const pointBuyValid =
    method === "point_buy"
      ? ABILITIES.every(
          (a) => scores[a] >= POINT_BUY_MIN && scores[a] <= POINT_BUY_MAX,
        ) && pointSpend <= POINT_BUY_TOTAL
      : true;

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <h3 className="text-sm font-semibold">Generation method</h3>
        <div className="flex flex-wrap gap-2">
          {(
            [
              ["standard_array", "Standard array"],
              ["point_buy", "Point buy"],
              ["recommended", "Recommended"],
            ] as Array<[Method, string]>
          ).map(([id, label]) => {
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
            Uses the suggested array for your class. Switch to{" "}
            <strong>Standard array</strong> or <strong>Point buy</strong> to
            customize.
          </p>
        )}
      </section>

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
              {pointBuyValid ? "" : " · over budget"}
            </p>
          )}
          {method === "recommended" && (
            <p className="text-xs text-muted-foreground">
              Class-recommended allocation (read-only)
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {ABILITIES.map((ability) => (
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
                  value={scores[ability]}
                  onChange={(e) => setScore(ability, Number(e.target.value))}
                  className="mt-1 w-full rounded border border-input bg-background px-2 py-1 text-sm"
                >
                  {STANDARD_ARRAY.map((v) => (
                    <option key={v} value={v}>
                      {v}
                      {usedFromArray.has(v) && v !== scores[ability]
                        ? " (used)"
                        : ""}
                    </option>
                  ))}
                </select>
              ) : method === "point_buy" ? (
                <input
                  id={`score-${ability}`}
                  type="number"
                  min={POINT_BUY_MIN}
                  max={POINT_BUY_MAX}
                  value={scores[ability]}
                  onChange={(e) =>
                    setScore(
                      ability,
                      Math.max(
                        POINT_BUY_MIN,
                        Math.min(POINT_BUY_MAX, Number(e.target.value) || POINT_BUY_MIN),
                      ),
                    )
                  }
                  className="mt-1 w-full rounded border border-input bg-background px-2 py-1 text-sm"
                />
              ) : (
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="text-lg font-semibold">
                    {scores[ability]}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {(() => {
                      const mod = Math.floor((scores[ability] - 10) / 2);
                      return mod >= 0 ? `+${mod}` : `${mod}`;
                    })()}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {!arrayValid && method === "standard_array" && (
          <p className="mt-2 text-xs text-destructive">
            Standard array values must each be used exactly once.
          </p>
        )}
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
