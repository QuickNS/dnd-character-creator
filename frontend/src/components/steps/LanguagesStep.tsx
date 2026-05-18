import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { Check } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useCharacterStore } from "@/store/characterStore";

interface LanguageOptions {
  base_languages?: string[];
  available_languages?: string[];
}

const LANGUAGES_KEY = "languages";

export function LanguagesStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);
  const selected = Array.isArray(choicesMade[LANGUAGES_KEY])
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

  function toggle(lang: string) {
    const set = new Set(selected);
    if (set.has(lang)) set.delete(lang);
    else set.add(lang);
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
          Bonus languages{" "}
          <span className="text-xs text-muted-foreground font-normal">
            ({selected.length} selected)
          </span>
        </h3>
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
                aria-pressed={isSelected}
                className={cn(
                  "rounded border px-3 py-2 text-sm transition-colors",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                  isSelected
                    ? "border-primary bg-secondary text-foreground"
                    : "border-border hover:bg-secondary/60",
                )}
              >
                <span className="flex items-center justify-between gap-2">
                  <span>{lang}</span>
                  <span
                    className={cn(
                      "inline-flex h-4 w-4 items-center justify-center rounded-full border",
                      isSelected
                        ? "border-primary bg-background text-primary"
                        : "border-border text-transparent",
                    )}
                    aria-hidden="true"
                  >
                    <Check className="h-3 w-3" />
                  </span>
                </span>
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Bonus language grants come from class, background, or feats. The
          backend validates which selections are actually granted.
        </p>
      </section>
    </div>
  );
}
