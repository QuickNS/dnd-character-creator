import { useCharacterStore } from "@/store/characterStore";

/**
 * Generic single- or multi-select renderer for a {choice_key, options, count}
 * shape. Used for class/subclass skill picks, fighting style choices,
 * species trait choices, etc.
 *
 * Stores selection in `choices_made[choiceKey]`:
 *   - count === 1 → single string
 *   - count > 1   → array of strings (length capped at `count`)
 */
interface Option {
  id?: string;
  name?: string;
  label?: string;
  description?: string;
}

interface Props {
  choiceKey: string;
  title?: string;
  description?: string;
  options: Array<string | Option>;
  /** Optional map of option value → description, merged with per-option `description`. */
  optionDescriptions?: Record<string, string>;
  count?: number;
}

function normalize(opt: string | Option): { value: string; label: string; description?: string } {
  if (typeof opt === "string") return { value: opt, label: opt };
  const value = opt.id ?? opt.name ?? opt.label ?? "";
  const label = opt.label ?? opt.name ?? opt.id ?? value;
  return { value, label, description: opt.description };
}

export function ChoiceList({
  choiceKey,
  title,
  description,
  options,
  optionDescriptions,
  count = 1,
}: Props) {
  const value = useCharacterStore((s) => s.choicesMade[choiceKey]);
  const setChoice = useCharacterStore((s) => s.setChoice);

  const normalized = options.map((opt) => {
    const n = normalize(opt);
    if (!n.description && optionDescriptions) {
      const fromMap =
        optionDescriptions[n.value] ?? optionDescriptions[n.label];
      if (fromMap) n.description = fromMap;
    }
    return n;
  });
  const isMulti = count > 1;

  const selected = new Set<string>(
    isMulti
      ? Array.isArray(value)
        ? (value as string[])
        : []
      : typeof value === "string" && value
        ? [value]
        : [],
  );

  function toggle(v: string) {
    if (!isMulti) {
      setChoice(choiceKey, v);
      return;
    }
    const next = new Set(selected);
    if (next.has(v)) {
      next.delete(v);
    } else {
      if (next.size >= count) return;
      next.add(v);
    }
    setChoice(choiceKey, Array.from(next));
  }

  return (
    <fieldset className="rounded-md border border-border bg-card/40 p-4">
      <legend className="px-2 text-sm font-semibold">
        {title ?? choiceKey}{" "}
        {isMulti && (
          <span className="text-xs text-muted-foreground font-normal">
            (choose {count} — {selected.size}/{count} selected)
          </span>
        )}
      </legend>
      {description && (
        <p className="text-xs text-muted-foreground mb-3">{description}</p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {normalized.map((opt) => {
          const isSelected = selected.has(opt.value);
          const disabled =
            isMulti && !isSelected && selected.size >= count;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => toggle(opt.value)}
              disabled={disabled}
              className={
                "text-left rounded border px-3 py-2 text-sm transition-colors " +
                (isSelected
                  ? "border-primary bg-secondary text-foreground"
                  : disabled
                    ? "border-border opacity-40 cursor-not-allowed"
                    : "border-border hover:bg-secondary/60")
              }
            >
              <div className="font-medium">{opt.label}</div>
              {opt.description && (
                <div className="text-xs text-muted-foreground mt-0.5">
                  {opt.description}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
