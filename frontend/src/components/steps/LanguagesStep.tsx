import { keepPreviousData, useMutation, useQuery } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";

interface LanguageOptions {
  base_languages?: string[];
  rare_base_languages?: string[];
  available_languages?: string[];
  selection_count?: number;
  selected_languages?: string[];
}

const LANGUAGES_KEY = "languages";

export function LanguagesStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const rawSelectedLanguages = Array.isArray(choicesMade[LANGUAGES_KEY])
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
  const rareBase = data.rare_base_languages ?? [];
  const available = data.available_languages ?? [];
  const selectionCount = data.selection_count ?? 2;
  const selected = Array.from(
    new Set(rawSelectedLanguages.filter((lang) => available.includes(lang))),
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

  // Show spinner while fetching and no data yet; keepPreviousData means isLoading
  // may be false on subsequent fetches even when available is still empty.
  const isLoadingInitial =
    (previewQuery.isLoading || previewQuery.isFetching) && available.length === 0;
  // Only declare "no languages offered" when the server explicitly returns
  // selection_count === 0. If selectionCount > 0 but available is empty the
  // API hasn't returned the list yet (e.g. empty choices state) — keep showing UI.
  const hasNoChoices = !isLoadingInitial && selectionCount === 0;
  const counterAtMax = selected.length === selectionCount;

  return (
    <div className="space-y-8">
      <section>
        <h3 className="font-semibold text-lg">Already known</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Granted automatically by your background, species, or features.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {base.map((lang) => (
            <span
              key={lang}
              className="inline-flex items-center gap-1.5 rounded-full border border-border bg-secondary px-3 py-1 text-xs text-muted-foreground"
            >
              <Check className="h-3 w-3" aria-hidden="true" />
              {lang}
            </span>
          ))}
        </div>
        {rareBase.length > 0 && (
          <div className="mt-3">
            <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Rare languages
            </p>
            <div className="flex flex-wrap gap-2">
              {rareBase.map((lang) => (
                <span
                  key={lang}
                  className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs text-amber-700 dark:text-amber-400"
                >
                  <Check className="h-3 w-3" aria-hidden="true" />
                  {lang}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-semibold text-lg">Additional languages</h3>
          <span
            className={cn(
              "text-sm font-medium",
              counterAtMax ? "text-primary" : "text-muted-foreground",
            )}
          >
            {selected.length} of {selectionCount} selected
          </span>
        </div>
        <p className="mb-4 text-sm text-muted-foreground">
          Choose exactly {selectionCount} additional language
          {selectionCount === 1 ? "" : "s"}, or use Roll to pick at random.
          Feature-based language grants still stack on top of these.
        </p>

        {isLoadingInitial ? (
          <div className="flex flex-col items-center justify-center gap-2 py-12">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading languages…</p>
          </div>
        ) : hasNoChoices ? (
          <p className="text-sm text-muted-foreground">
            No additional languages are offered by your current selections.
          </p>
        ) : (
          <>
            <div className="mb-3 flex gap-2">
              <button
                type="button"
                onClick={() => randomLanguages.mutate()}
                disabled={previewQuery.isLoading || randomLanguages.isPending}
                className={cn(
                  "inline-flex h-9 items-center justify-center rounded-md border border-border bg-background px-3 text-xs font-medium",
                  "hover:bg-secondary hover:text-foreground transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  "disabled:opacity-50 disabled:pointer-events-none",
                )}
              >
                {randomLanguages.isPending
                  ? "Rolling…"
                  : `Roll ${selectionCount}`}
              </button>
              <button
                type="button"
                onClick={() => setChoice(LANGUAGES_KEY, [])}
                disabled={selected.length === 0}
                className={cn(
                  "inline-flex h-9 items-center justify-center rounded-md px-3 text-xs font-medium",
                  "hover:bg-secondary hover:text-foreground transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  "disabled:opacity-50 disabled:pointer-events-none",
                )}
              >
                Clear
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              {available.map((lang) => {
                const isSelected = selected.includes(lang);
                const isDisabled =
                  !isSelected && selected.length >= selectionCount;
                return (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => toggle(lang)}
                    disabled={isDisabled}
                    aria-pressed={isSelected}
                    className={cn(
                      "rounded-md border px-3 py-2 text-sm transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                      isSelected
                        ? "border-primary bg-secondary ring-2 ring-primary/20 text-foreground"
                        : "border-border hover:bg-secondary/40 hover:border-primary/40",
                      isDisabled && "opacity-40 cursor-not-allowed",
                    )}
                  >
                    <span className="flex items-center justify-between gap-2">
                      <span>{lang}</span>
                      {isSelected && (
                        <span
                          className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-primary bg-background text-primary"
                          aria-hidden="true"
                        >
                          <Check className="h-3 w-3" />
                        </span>
                      )}
                    </span>
                  </button>
                );
              })}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
