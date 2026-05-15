import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { ChoiceList } from "@/components/wizard/ChoiceList";
import { FeatChoicesPicker } from "@/components/wizard/FeatChoicesPicker";

interface TraitChoice {
  description?: string;
  options?: Array<string | { name?: string }>;
  option_descriptions?: Record<string, string>;
  count?: number;
}

interface LineageEntry {
  id: string;
  name: string;
  description?: string;
  traits?: Record<string, unknown>;
}

/**
 * The backend returns `lineages` enriched with variant data
 * (`{id, name, description, traits}`). For older payloads we still
 * accept arrays of strings or dict maps and fall back gracefully.
 */
function normalizeLineages(raw: unknown): LineageEntry[] {
  if (!raw) return [];
  if (Array.isArray(raw)) {
    return raw.map((item, i) => {
      if (typeof item === "string") {
        return { id: item, name: item };
      }
      if (item && typeof item === "object") {
        const o = item as Record<string, unknown>;
        const id =
          (typeof o.id === "string" && o.id) ||
          (typeof o.name === "string" && o.name) ||
          String(i);
        return {
          id,
          name: typeof o.name === "string" ? o.name : id,
          description:
            typeof o.description === "string" ? o.description : undefined,
          traits:
            o.traits && typeof o.traits === "object"
              ? (o.traits as Record<string, unknown>)
              : undefined,
        };
      }
      return { id: String(i), name: String(i) };
    });
  }
  if (typeof raw === "object") {
    return Object.entries(raw as Record<string, unknown>).map(([id, v]) => {
      const o = v && typeof v === "object" ? (v as Record<string, unknown>) : {};
      return {
        id,
        name: typeof o.name === "string" ? o.name : id,
        description:
          typeof o.description === "string" ? o.description : undefined,
        traits:
          o.traits && typeof o.traits === "object"
            ? (o.traits as Record<string, unknown>)
            : undefined,
      };
    });
  }
  return [];
}

function traitDescription(value: unknown): string | undefined {
  if (typeof value === "string") return value;
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const d = (value as Record<string, unknown>).description;
    if (typeof d === "string") return d;
  }
  return undefined;
}

export function SpeciesStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selectedSpecies = (choicesMade["species"] as string | undefined) ?? "";

  const speciesQuery = useQuery({
    queryKey: ["catalog", "species"],
    queryFn: api.catalog.species,
  });

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "species", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "species"),
    enabled: !!selectedSpecies,
    placeholderData: keepPreviousData,
  });

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold mb-3">Choose a species</h3>
        {speciesQuery.isLoading && (
          <p className="text-xs text-muted-foreground">Loading species…</p>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(speciesQuery.data ?? []).map((sp) => {
            const isSelected = selectedSpecies === sp.id;
            return (
              <button
                key={sp.id}
                type="button"
                onClick={() => setChoice("species", sp.id)}
                className={
                  "text-left rounded-md border p-3 transition-colors " +
                  (isSelected
                    ? "border-primary bg-secondary"
                    : "border-border hover:bg-secondary/60")
                }
              >
                <div className="font-display text-lg text-primary">{sp.name}</div>
                <dl className="mt-1 text-xs text-muted-foreground/80 space-y-0.5">
                  {sp.size !== undefined && (
                    <div>
                      <span className="font-semibold">Size:</span>{" "}
                      {String(sp.size)}
                    </div>
                  )}
                  {sp.speed !== undefined && (
                    <div>
                      <span className="font-semibold">Speed:</span>{" "}
                      {typeof sp.speed === "number"
                        ? `${sp.speed} ft`
                        : Object.entries(sp.speed)
                            .map(([k, v]) => `${k} ${v} ft`)
                            .join(" · ")}
                    </div>
                  )}
                  {sp.darkvision !== undefined && sp.darkvision > 0 && (
                    <div>
                      <span className="font-semibold">Darkvision:</span>{" "}
                      {sp.darkvision} ft
                    </div>
                  )}
                </dl>
                {sp.description && (
                  <div className="text-xs text-muted-foreground mt-2 line-clamp-3">
                    {sp.description}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </section>

      {selectedSpecies && previewQuery.data && (
        <SpeciesDetail previewData={previewQuery.data} />
      )}
    </div>
  );
}

function SpeciesDetail({
  previewData,
}: {
  previewData: Record<string, unknown>;
}) {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);

  const lineageEntries = normalizeLineages(previewData["lineages"]);
  const selectedLineage = (choicesMade["lineage"] as string | undefined) ?? "";

  const traitChoices = (previewData["trait_choices"] as
    | Record<string, TraitChoice>
    | undefined) ?? {};

  const speciesFeat = previewData["species_feat_choices"] as
    | Parameters<typeof FeatChoicesPicker>[0]["data"]
    | undefined;

  return (
    <div className="space-y-6">
      {lineageEntries.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold mb-3">Choose a lineage</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-start">
            {lineageEntries.map((entry) => {
              const isSelected = selectedLineage === entry.id;
              const traitEntries = Object.entries(entry.traits ?? {});
              return (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => setChoice("lineage", entry.id)}
                  aria-pressed={isSelected}
                  className={
                    "flex h-full w-full flex-col items-stretch text-left rounded-md border p-3 transition-colors " +
                    (isSelected
                      ? "border-primary bg-secondary"
                      : "border-border hover:bg-secondary/60")
                  }
                >
                  <div className="font-display text-lg text-primary">
                    {entry.name}
                  </div>
                  {entry.description && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      {entry.description}
                    </p>
                  )}
                  {traitEntries.length > 0 && (
                    <div className="mt-3 border-t border-border pt-3">
                      <dl className="space-y-2 text-xs">
                        {traitEntries.map(([traitName, traitValue]) => {
                          const desc = traitDescription(traitValue);
                          return (
                            <div key={traitName}>
                              <dt className="inline font-semibold text-foreground">
                                {traitName}:
                              </dt>{" "}
                              {desc && (
                                <dd className="inline text-muted-foreground">
                                  {desc}
                                </dd>
                              )}
                            </div>
                          );
                        })}
                      </dl>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      )}

      {Object.keys(traitChoices).length > 0 && (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold">Species trait choices</h3>
          {Object.entries(traitChoices).map(([traitName, choice]) => (
            <ChoiceList
              key={traitName}
              choiceKey={traitName}
              title={traitName}
              description={choice.description}
              options={choice.options ?? []}
              optionDescriptions={choice.option_descriptions}
              count={choice.count ?? 1}
            />
          ))}
        </section>
      )}

      {speciesFeat && speciesFeat.feat_name && (
        <FeatChoicesPicker data={speciesFeat} heading="Species feat" />
      )}
    </div>
  );
}
