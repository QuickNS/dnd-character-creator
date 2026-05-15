import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";

interface EquipmentOption {
  gold?: number;
  items?: unknown[];
  [key: string]: unknown;
}

type EquipmentBlock = Record<string, EquipmentOption>;

const EQUIPMENT_KEY = "equipment_selections";

const SLOT_LABEL: Record<string, string> = {
  class_equipment: "From your class",
  background_equipment: "From your background",
};

export function EquipmentStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);

  const previewQuery = useQuery({
    queryKey: ["character", "preview-step", "equipment", choicesMade],
    queryFn: () => api.character.previewStep(choicesMade, "equipment"),
    placeholderData: keepPreviousData,
  });

  const stored =
    (choicesMade[EQUIPMENT_KEY] as Record<string, string> | undefined) ?? {};

  function setSelection(slot: string, value: string | null) {
    const next = { ...stored };
    if (value === null) delete next[slot];
    else next[slot] = value;
    setChoice(EQUIPMENT_KEY, next);
  }

  if (previewQuery.isLoading && !previewQuery.data) {
    return <p className="text-xs text-muted-foreground">Loading equipment…</p>;
  }

  const slots: Array<{ key: string; block: EquipmentBlock }> = [
    {
      key: "class_equipment",
      block:
        (previewQuery.data?.class_equipment as EquipmentBlock | undefined) ??
        {},
    },
    {
      key: "background_equipment",
      block:
        (previewQuery.data?.background_equipment as
          | EquipmentBlock
          | undefined) ?? {},
    },
  ];

  return (
    <div className="space-y-6">
      {slots.map(({ key, block }) => (
        <EquipmentSlot
          key={key}
          title={SLOT_LABEL[key] ?? key}
          slot={key}
          block={block}
          selected={stored[key] ?? null}
          onSelect={(option) => setSelection(key, option)}
        />
      ))}
    </div>
  );
}

function EquipmentSlot({
  title,
  slot,
  block,
  selected,
  onSelect,
}: {
  title: string;
  slot: string;
  block: EquipmentBlock;
  selected: string | null;
  onSelect: (option: string | null) => void;
}) {
  const options = Object.entries(block ?? {});

  if (options.length === 0) {
    return (
      <section>
        <h3 className="text-sm font-semibold mb-2">{title}</h3>
        <p className="text-xs text-muted-foreground">
          No starting equipment data available.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-start">
        {options.map(([optKey, opt]) => {
          const isSelected = selected === optKey;
          const items = Array.isArray(opt?.items) ? (opt.items as unknown[]) : [];
          const gold = typeof opt?.gold === "number" ? opt.gold : undefined;
          const label = humanizeOption(optKey);
          return (
            <button
              key={`${slot}-${optKey}`}
              type="button"
              onClick={() => onSelect(isSelected ? null : optKey)}
              aria-pressed={isSelected}
              className={
                "flex h-full w-full flex-col items-stretch text-left rounded-md border p-3 transition-colors " +
                (isSelected
                  ? "border-primary bg-secondary"
                  : "border-border hover:bg-secondary/60")
              }
            >
              <div className="font-display text-lg text-primary">{label}</div>
              {gold !== undefined && (
                <dl className="mt-1 text-xs text-muted-foreground/80 space-y-0.5">
                  <div>
                    <span className="font-semibold">Gold:</span> {gold} gp
                  </div>
                </dl>
              )}
              {items.length > 0 && (
                <ul className="mt-2 text-xs text-muted-foreground list-disc pl-5 space-y-0.5">
                  {items.map((it, i) => (
                    <li key={i}>
                      {typeof it === "string" ? it : JSON.stringify(it)}
                    </li>
                  ))}
                </ul>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}

function humanizeOption(key: string): string {
  // "option_a" → "Option A", "option_b" → "Option B", fallback title-case.
  const m = /^option_([a-z])$/i.exec(key);
  if (m) return `Option ${m[1].toUpperCase()}`;
  return key
    .split("_")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}
