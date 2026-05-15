import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
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

export function ClassStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selectedClass = (choicesMade["class"] as string | undefined) ?? "";

  const classesQuery = useQuery({
    queryKey: ["catalog", "classes"],
    queryFn: api.catalog.classes,
  });

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "class", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "class"),
    enabled: !!selectedClass,
    placeholderData: keepPreviousData,
  });

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold mb-3">Choose a class</h3>
        {classesQuery.isLoading && (
          <p className="text-xs text-muted-foreground">Loading classes…</p>
        )}
        {classesQuery.error && (
          <p className="text-xs text-destructive">
            Failed to load classes: {String(classesQuery.error)}
          </p>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(classesQuery.data ?? []).map((cls) => {
            const isSelected = selectedClass === cls.id;
            return (
              <button
                key={cls.id}
                type="button"
                onClick={() => setChoice("class", cls.id)}
                className={
                  "text-left rounded-md border p-3 transition-colors " +
                  (isSelected
                    ? "border-primary bg-secondary"
                    : "border-border hover:bg-secondary/60")
                }
              >
                <div className="font-display text-lg text-primary">
                  {cls.name}
                </div>
                <dl className="mt-1 text-xs text-muted-foreground/80 space-y-0.5">
                  {cls.primary_ability && (
                    <div>
                      <span className="font-semibold">Primary:</span>{" "}
                      {Array.isArray(cls.primary_ability)
                        ? cls.primary_ability.join(" / ")
                        : cls.primary_ability}
                    </div>
                  )}
                  {cls.hit_die !== undefined && (
                    <div>
                      <span className="font-semibold">Hit Die:</span> d
                      {cls.hit_die}
                    </div>
                  )}
                </dl>
                {cls.description && (
                  <div className="text-xs text-muted-foreground mt-2 line-clamp-3">
                    {cls.description}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </section>

      {selectedClass && previewQuery.isLoading && !previewQuery.data && (
        <p className="text-xs text-muted-foreground">Loading class details…</p>
      )}

      {selectedClass && previewQuery.data && (
        <ClassDetail
          previewData={previewQuery.data}
          choicesMade={choicesMade}
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

function ClassDetail({
  previewData,
  choicesMade,
  selectedSubclass,
  onSubclass,
}: {
  previewData: Record<string, unknown>;
  choicesMade: Record<string, unknown>;
  selectedSubclass: string;
  onSubclass: (v: string) => void;
}) {
  const needsSubclass = previewData["needs_subclass"] === true;
  const availableSubclasses =
    (previewData["available_subclasses"] as SubclassSummary[] | undefined) ?? [];
  const nestedChoices =
    (previewData["nested_choices"] as PreviewChoice[] | undefined) ?? [];

  return (
    <div className="space-y-6">
      {needsSubclass && (
        <section>
          <h3 className="text-sm font-semibold mb-3">Choose a subclass</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-start">
            {availableSubclasses.map((sub) => {
              const isSelected = selectedSubclass === sub.id;
              return (
                <button
                  key={sub.id}
                  type="button"
                  onClick={() => onSubclass(sub.id)}
                  className={
                    "text-left rounded-md border p-3 transition-colors " +
                    (isSelected
                      ? "border-primary bg-secondary"
                      : "border-border hover:bg-secondary/60")
                  }
                >
                  <div className="font-display text-lg text-primary">
                    {sub.name}
                  </div>
                  {sub.description && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      {sub.description}
                    </div>
                  )}
                  {(sub.level_3_feature_names ?? []).length > 0 && (
                    <div className="mt-3 border-t border-border pt-3">
                      <div className="text-xs font-semibold">Level 3 features</div>
                      <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                        {sub.level_3_feature_names?.map((featureName) => (
                          <li key={featureName}>• {featureName}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </section>
      )}

      {nestedChoices.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-sm font-semibold">Class choices</h3>
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
        </section>
      )}
    </div>
  );
}
