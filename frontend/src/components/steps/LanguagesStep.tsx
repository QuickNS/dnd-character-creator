import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";

interface LanguageOptions {
  base_languages?: string[];
  available_languages?: string[];
  selection_count?: number;
  selected_languages?: string[];
}

const LANGUAGES_KEY = "languages";

export function LanguagesStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selectedFromStore = Array.isArray(choicesMade[LANGUAGES_KEY])
    ? (choicesMade[LANGUAGES_KEY] as string[])
    : [];

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "languages", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "languages"),
    placeholderData: keepPreviousData,
  });

  const data =
    (previewQuery.data?.language_options as LanguageOptions | undefined) ?? {};
  const base = data.base_languages ?? ["Common"];
  const available = data.available_languages ?? [];
  const selectionCount = data.selection_count ?? 2;
  const selected = Array.from(
    new Set(selectedFromStore.filter((lang) => available.includes(lang))),
  ).slice(0, selectionCount);

  const randomLanguages = useMutation({
    mutationFn: () => api.character.randomLanguages(choicesMade),
    onSuccess: (languages) => {
      setChoice(LANGUAGES_KEY, languages);
    },
  });

  function toggle(lang: string) {
    const set = new Set(selected);
    if (set.has(lang)) set.delete(lang);
    else if (set.size < selectionCount) set.add(lang);
    setChoice(LANGUAGES_KEY, Array.from(set));
  }

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold mb-2">Already known</h3>
        <div className="flex flex-wrap gap-2">
          {base.map((lang) => (
            <span
              key={lang}
              className="rounded-full border border-border bg-secondary px-3 py-1 text-xs text-muted-foreground"
            >
              {lang}
            </span>
          ))}
        </div>
      </section>

      <section>
        <h3 className="text-sm font-semibold mb-2">
          Additional languages{" "}
          <span className="text-xs text-muted-foreground font-normal">
            ({selected.length}/{selectionCount} selected)
          </span>
        </h3>
        <div className="mb-3 flex gap-2">
          <button
            type="button"
            onClick={() => randomLanguages.mutate()}
            className="rounded border border-border px-3 py-1.5 text-xs hover:bg-secondary/60 disabled:opacity-50"
            disabled={previewQuery.isLoading || randomLanguages.isPending}
          >
            {randomLanguages.isPending ? "Rolling…" : `Roll ${selectionCount}`}
          </button>
          <button
            type="button"
            onClick={() => setChoice(LANGUAGES_KEY, [])}
            className="rounded border border-border px-3 py-1.5 text-xs hover:bg-secondary/60"
          >
            Clear
          </button>
        </div>
        {previewQuery.isLoading && (
          <p className="text-xs text-muted-foreground">Loading…</p>
        )}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
          {available.map((lang) => {
            const isSelected = selected.includes(lang);
            return (
              <button
                key={lang}
                type="button"
                onClick={() => toggle(lang)}
                disabled={!isSelected && selected.length >= selectionCount}
                className={
                  "rounded border px-3 py-2 text-sm transition-colors " +
                  (isSelected
                    ? "border-primary bg-secondary text-foreground"
                    : "border-border hover:bg-secondary/60 disabled:opacity-50 disabled:hover:bg-transparent")
                }
              >
                {lang}
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          You automatically know Common. Choose exactly {selectionCount} additional
          languages (or use Roll). Other feature-based language grants still stack.
        </p>
      </section>
    </div>
  );
}
