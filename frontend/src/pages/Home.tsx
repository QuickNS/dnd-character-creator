import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useCharacterStore } from "@/store/characterStore";

export function Home() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const reset = useCharacterStore((s) => s.reset);
  const [importError, setImportError] = useState<string | null>(null);
  const [importOpen, setImportOpen] = useState(false);
  const [pasteText, setPasteText] = useState("");

  function applyChoices(choices: Record<string, unknown>) {
    // Replace persisted store state directly so the import lands atomically
    // without firing per-key cascade invalidation.
    useCharacterStore.setState({ choicesMade: choices, currentStepId: null });
    queryClient.removeQueries({ queryKey: ["character"] });
    queryClient.removeQueries({ queryKey: ["wizard"] });
  }

  function extractChoices(parsed: unknown): Record<string, unknown> {
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("File does not contain a valid choices object.");
    }
    const obj = parsed as Record<string, unknown>;
    let choices: unknown = obj;
    if (
      obj.choices_made &&
      typeof obj.choices_made === "object" &&
      !Array.isArray(obj.choices_made)
    ) {
      choices = obj.choices_made;
    } else if (
      obj.choices &&
      typeof obj.choices === "object" &&
      !Array.isArray(obj.choices)
    ) {
      choices = obj.choices;
    }
    if (!choices || typeof choices !== "object" || Array.isArray(choices)) {
      throw new Error("File does not contain a valid choices object.");
    }
    return choices as Record<string, unknown>;
  }

  function importFromText(text: string) {
    const trimmed = text.trim();
    if (!trimmed) {
      throw new Error("Paste some JSON first.");
    }
    const parsed: unknown = JSON.parse(trimmed);
    const choices = extractChoices(parsed);
    applyChoices(choices);
  }

  async function handleFile(file: File) {
    setImportError(null);
    try {
      importFromText(await file.text());
      setImportOpen(false);
      setPasteText("");
      navigate("/wizard");
    } catch (err) {
      setImportError(
        err instanceof Error ? err.message : "Failed to read character file.",
      );
    }
  }

  function handlePasteImport() {
    setImportError(null);
    try {
      importFromText(pasteText);
      setImportOpen(false);
      setPasteText("");
      navigate("/wizard");
    } catch (err) {
      setImportError(
        err instanceof Error ? err.message : "Invalid JSON.",
      );
    }
  }

  function handleStartFresh(e: React.MouseEvent) {
    e.preventDefault();
    reset();
    queryClient.removeQueries({ queryKey: ["character"] });
    queryClient.removeQueries({ queryKey: ["wizard"] });
    navigate("/wizard");
  }

  return (
    <main className="min-h-dvh bg-background text-foreground font-sans">
      <div className="container py-16 max-w-3xl">
        <div className="flex justify-end mb-4">
          <ThemeToggle />
        </div>
        <h1 className="font-display text-5xl text-primary tracking-wide">
          D&amp;D 2024 Character Creator
        </h1>
        <p className="mt-6 text-lg text-muted-foreground">
          Build a Dungeons &amp; Dragons 2024 character with a guided wizard.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link
            to="/wizard"
            className="inline-flex items-center rounded-md bg-primary px-6 py-3 text-primary-foreground font-semibold shadow hover:opacity-90"
          >
            Continue Wizard
          </Link>
          <button
            type="button"
            onClick={handleStartFresh}
            className="inline-flex items-center rounded-md border border-border px-6 py-3 text-foreground hover:bg-secondary"
          >
            Start Fresh
          </button>
          <button
            type="button"
            onClick={() => {
              setImportError(null);
              setImportOpen((v) => !v);
            }}
            className="inline-flex items-center rounded-md border border-border px-6 py-3 text-foreground hover:bg-secondary"
            aria-expanded={importOpen}
          >
            Import Character
          </button>
          <Link
            to="/sheet"
            className="inline-flex items-center rounded-md border border-border px-6 py-3 text-foreground hover:bg-secondary"
          >
            View Sheet
          </Link>
        </div>

        {importOpen && (
          <section className="mt-6 rounded-md border border-border bg-card/50 p-5">
            <h2 className="font-display text-lg text-primary mb-3">
              Import character
            </h2>
            <p className="text-xs text-muted-foreground mb-4">
              Use a previously exported{" "}
              <code className="text-foreground">choices.json</code> file, or
              paste the JSON directly. <strong>Importing replaces</strong> any
              character currently in progress.
            </p>

            <div className="flex flex-wrap gap-3 mb-4">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-secondary"
              >
                Choose file…
              </button>
              <button
                type="button"
                onClick={() => {
                  setImportOpen(false);
                  setPasteText("");
                  setImportError(null);
                }}
                className="inline-flex items-center rounded-md border border-border px-4 py-2 text-sm hover:bg-secondary"
              >
                Cancel
              </button>
            </div>

            <label
              htmlFor="paste-json"
              className="block text-xs uppercase tracking-widest text-muted-foreground mb-2"
            >
              Or paste JSON
            </label>
            <textarea
              id="paste-json"
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder='{ "choices_made": { "character_name": "Aria", ... } }'
              spellCheck={false}
              rows={10}
              className="w-full rounded-md border border-border bg-background px-3 py-2 font-mono text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={handlePasteImport}
                disabled={!pasteText.trim()}
                className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground font-semibold hover:opacity-90 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Import pasted JSON
              </button>
            </div>
          </section>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              void handleFile(file);
            }
            // Reset so re-importing the same file fires onChange again.
            e.target.value = "";
          }}
        />
        {importError && (
          <p className="mt-4 text-sm text-destructive">
            Import failed: {importError}
          </p>
        )}
      </div>
    </main>
  );
}
