import { Link } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api, type WizardStep } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";

interface Props {
  steps: WizardStep[];
}

type Char = Record<string, unknown>;

function num(v: unknown): number | undefined {
  return typeof v === "number" ? v : undefined;
}
function str(v: unknown): string | undefined {
  return typeof v === "string" ? v : undefined;
}
function arr<T = unknown>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}
function rec(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : {};
}
function signed(v: number | undefined): string {
  if (v === undefined) return "—";
  return v >= 0 ? `+${v}` : String(v);
}

function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function safeFilename(name: string): string {
  return (
    name
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9._-]+/g, "-")
      .replace(/^-+|-+$/g, "") || "character"
  );
}

export function SummaryStep({ steps }: Props) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);

  const validateQuery = useQuery({
    queryKey: ["character", "validate", choicesMade],
    queryFn: () => api.character.validate(choicesMade),
    placeholderData: keepPreviousData,
  });

  const buildQuery = useQuery({
    queryKey: ["character", "build", choicesMade],
    queryFn: () => api.character.build(choicesMade),
    retry: false,
    placeholderData: keepPreviousData,
  });

  const stepLabel = new Map(steps.map((s) => [s.id, s.label]));
  const statuses = validateQuery.data?.steps ?? [];
  const incomplete = statuses.filter((s) => !s.complete);
  const allComplete = statuses.length > 0 && incomplete.length === 0;

  const character = (buildQuery.data ?? {}) as Char;
  const buildError = buildQuery.error ? String(buildQuery.error) : null;

  const name = str(character.name) ?? str(character.character_name) ?? "Unnamed";
  const cls = str(character.class);
  const sub = str(character.subclass);
  const species = str(character.species);
  const lineage = str(character.lineage);
  const bg = str(character.background);
  const level = num(character.level);
  const alignment = str(character.alignment);

  const combat = rec(character.combat);
  const hp = rec(combat.hit_points);
  const hpMax = num(hp.maximum) ?? num(combat.hp);
  const acOptions = arr<Record<string, unknown>>(character.ac_options);
  const topAc = acOptions[0] ? num(rec(acOptions[0]).ac) : undefined;
  const speed = num(character.speed) ?? num(combat.speed);
  const init = num(combat.initiative_bonus) ?? num(combat.initiative);
  const pb = num(character.proficiency_bonus);
  const passive = num(combat.passive_perception);

  const abilityOrder = [
    "Strength",
    "Dexterity",
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma",
  ];
  const abilities = rec(character.abilities);
  const abilityScores = rec(character.ability_scores);
  function abilityRow(a: string) {
    const direct = rec(abilities[a.toLowerCase()]);
    const score =
      num(direct.score) ??
      num(abilityScores[a]) ??
      num(abilityScores[a.toLowerCase()]);
    const mod = num(direct.modifier) ?? num(direct.mod);
    return { score, mod };
  }

  const languages = arr<string>(character.languages);
  const features = arr<Record<string, unknown>>(character.features);

  function handleExport() {
    const baseName = safeFilename(name);
    downloadJson(`${baseName}-choices.json`, {
      version: 1,
      exported_at: new Date().toISOString(),
      choices_made: choicesMade,
    });
  }

  function handleExportFull() {
    if (!buildQuery.data) return;
    const baseName = safeFilename(name);
    downloadJson(`${baseName}-character.json`, buildQuery.data);
  }

  return (
    <div className="space-y-6">
      {/* Validation */}
      <section className="rounded-md border border-border bg-card/50 p-4">
        <h2 className="font-display text-lg text-primary mb-2">
          Completion checklist
        </h2>
        {validateQuery.isLoading && (
          <p className="text-xs text-muted-foreground">Checking…</p>
        )}
        {validateQuery.error && (
          <p className="text-xs text-destructive">
            {String(validateQuery.error)}
          </p>
        )}
        {!validateQuery.isLoading && !validateQuery.error && (
          <>
            {allComplete ? (
              <p className="text-sm">
                <span className="text-primary font-semibold">
                  ✓ All required choices made.
                </span>{" "}
                Ready to play.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                {incomplete.length} step{incomplete.length === 1 ? "" : "s"}{" "}
                still need attention:
              </p>
            )}
            <ul className="mt-3 space-y-1 text-sm">
              {statuses.map((s) => {
                const label = stepLabel.get(s.step) ?? s.step;
                return (
                  <li key={s.step} className="flex items-start gap-2">
                    <span
                      className={
                        s.complete
                          ? "text-primary"
                          : "text-destructive"
                      }
                      aria-hidden
                    >
                      {s.complete ? "✓" : "○"}
                    </span>
                    <div className="flex-1">
                      <Link
                        to={`/wizard/${s.step}`}
                        className={
                          s.complete
                            ? "text-foreground hover:text-primary"
                            : "text-foreground hover:text-primary underline"
                        }
                      >
                        {label}
                      </Link>
                      {!s.complete && s.missing.length > 0 && (
                        <span className="ml-2 text-xs text-muted-foreground">
                          missing: {s.missing.join(", ")}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </section>

      {/* Build error */}
      {buildError && (
        <section className="rounded-md border border-destructive/40 bg-destructive/10 p-4">
          <h2 className="font-display text-lg text-destructive mb-1">
            Build failed
          </h2>
          <p className="text-sm text-destructive">{buildError}</p>
          <p className="text-xs text-muted-foreground mt-2">
            Resolve the items above and the character will rebuild
            automatically.
          </p>
        </section>
      )}

      {/* Character preview */}
      {!buildError && (
        <section className="rounded-md border border-border bg-card/50 p-4">
          <h2 className="font-display text-lg text-primary mb-3">
            Character preview
          </h2>

          <div className="mb-4">
            <div className="font-display text-2xl text-foreground">{name}</div>
            <div className="text-sm text-muted-foreground">
              {level !== undefined ? `Level ${level}` : "Level —"}{" "}
              {cls ?? "—"}
              {sub ? ` (${sub})` : ""} · {species ?? "—"}
              {lineage ? ` (${lineage})` : ""}
              {bg ? ` · ${bg}` : ""}
              {alignment ? ` · ${alignment}` : ""}
            </div>
          </div>

          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-y-3 gap-x-6 text-sm mb-4">
            <Stat label="HP" value={hpMax} />
            <Stat label="AC" value={topAc} />
            <Stat
              label="Speed"
              value={speed !== undefined ? `${speed} ft` : undefined}
            />
            <Stat label="Initiative" value={signed(init)} />
            <Stat label="Prof. Bonus" value={signed(pb)} />
            <Stat label="Passive Perc." value={passive} />
          </dl>

          <div className="grid grid-cols-6 gap-2 mb-4">
            {abilityOrder.map((a) => {
              const v = abilityRow(a);
              return (
                <div
                  key={a}
                  className="rounded border border-border bg-background/40 p-2 text-center"
                >
                  <div className="text-[10px] uppercase text-muted-foreground">
                    {a.slice(0, 3)}
                  </div>
                  <div className="text-lg font-semibold">
                    {v.score ?? "—"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {signed(v.mod)}
                  </div>
                </div>
              );
            })}
          </div>

          {languages.length > 0 && (
            <div className="text-sm mb-3">
              <span className="text-xs uppercase tracking-widest text-muted-foreground mr-2">
                Languages
              </span>
              {languages.join(", ")}
            </div>
          )}

          {features.length > 0 && (
            <details className="rounded border border-border bg-background/40 p-2">
              <summary className="cursor-pointer text-xs uppercase tracking-widest text-muted-foreground">
                Features ({features.length})
              </summary>
              <ul className="mt-2 space-y-1 text-sm">
                {features.slice(0, 30).map((f, i) => {
                  const fname = str(f.name) ?? str(f.feature) ?? "Feature";
                  const source = str(f.source);
                  return (
                    <li key={i} className="flex justify-between gap-3">
                      <span>{fname}</span>
                      {source && (
                        <span className="text-xs text-muted-foreground">
                          {source}
                        </span>
                      )}
                    </li>
                  );
                })}
                {features.length > 30 && (
                  <li className="text-xs text-muted-foreground">
                    + {features.length - 30} more…
                  </li>
                )}
              </ul>
            </details>
          )}
        </section>
      )}

      {/* Actions */}
      <section className="rounded-md border border-border bg-card/50 p-4">
        <h2 className="font-display text-lg text-primary mb-3">Next steps</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            to="/sheet"
            className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground font-semibold hover:opacity-90"
          >
            View full character sheet →
          </Link>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-secondary"
          >
            Download choices (JSON)
          </button>
          <button
            type="button"
            onClick={handleExportFull}
            disabled={!buildQuery.data || !!buildError}
            className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-secondary disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Download character (JSON)
          </button>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Your progress is saved automatically in this browser. Use{" "}
          <strong>Start over</strong> in the sidebar to begin a new
          character.
        </p>
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
}: {
  label: string;
  value: string | number | undefined;
}) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-widest text-muted-foreground">
        {label}
      </dt>
      <dd className="text-lg font-semibold">{value ?? "—"}</dd>
    </div>
  );
}
