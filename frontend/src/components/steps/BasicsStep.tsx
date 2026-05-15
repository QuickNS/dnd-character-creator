import { useCharacterStore } from "@/store/characterStore";

export function BasicsStep() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const setChoice = useCharacterStore((s) => s.setChoice);

  const name = (choicesMade.character_name as string | undefined) ?? "";
  const level = (choicesMade.level as number | undefined) ?? 1;

  return (
    <div className="space-y-6 max-w-md">
      <div>
        <label
          htmlFor="character_name"
          className="block text-sm font-medium mb-2"
        >
          Character name
        </label>
        <input
          id="character_name"
          type="text"
          value={name}
          onChange={(e) => setChoice("character_name", e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="e.g. Thorin Ironfist"
        />
      </div>

      <div>
        <label htmlFor="level" className="block text-sm font-medium mb-2">
          Starting level
        </label>
        <input
          id="level"
          type="number"
          min={1}
          max={20}
          value={level}
          onChange={(e) =>
            setChoice("level", Math.max(1, Math.min(20, Number(e.target.value) || 1)))
          }
          className="w-32 rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
    </div>
  );
}
