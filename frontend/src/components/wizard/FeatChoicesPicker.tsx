import { ChoiceList } from "./ChoiceList";

/**
 * Renders the `{feat_name, feat_description, feat_benefits, choices: [...]}`
 * shape returned by `builder.get_feat_choices()` /
 * `builder.get_species_feat_choices()` (surfaced via /character/preview-step).
 */
interface FeatChoice {
  title?: string;
  description?: string;
  /** Structured type from the backend: "skills" | "tools" | "languages" | etc. */
  type?: string;
  options?: Array<unknown>;
  count?: number;
  choices_made_key?: string;
  feature_name?: string;
}

interface FeatChoicesData {
  feat_name?: string | null;
  feat_description?: string;
  feat_benefits?: string[];
  choices?: FeatChoice[];
}

interface Props {
  data: FeatChoicesData | undefined;
  heading: string;
  /**
   * Skill and tool proficiencies already granted by other sources (class,
   * background direct grants, etc.). For skill/tool-type choices these are
   * shown grayed out and disabled so the player can see duplicates at a glance.
   */
  grantedProficiencies?: string[];
}

/** Returns true for choice types that deal in skill or tool proficiencies. */
function isProficiencyChoice(choice: FeatChoice): boolean {
  const t = (choice.type ?? "").toLowerCase();
  if (t === "skills" || t === "tools") return true;
  // Fallback: keyword scan on title/feature_name for choices that lack a type.
  const keywords = `${choice.title ?? ""} ${choice.feature_name ?? ""}`.toLowerCase();
  return keywords.includes("skill") || keywords.includes("tool");
}

export function FeatChoicesPicker({ data, heading, grantedProficiencies }: Props) {
  if (!data || !data.feat_name) return null;
  const choices = data.choices ?? [];

  return (
    <section className="rounded-md border border-border bg-card/40 p-4 space-y-3">
      <header>
        <h3 className="text-lg font-semibold">
          {heading}: <span className="text-primary">{data.feat_name}</span>
        </h3>
        {data.feat_description && (
          <p className="mt-1 text-sm text-muted-foreground">
            {data.feat_description}
          </p>
        )}
        {data.feat_benefits && data.feat_benefits.length > 0 && (
          <ul className="mt-2 text-sm text-muted-foreground list-disc pl-5">
            {data.feat_benefits.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        )}
      </header>

      {choices.map((choice, idx) => {
        const key =
          choice.choices_made_key ??
          `feat_${data.feat_name}_${choice.feature_name ?? idx}`;
        const opts = (choice.options ?? []) as Array<unknown>;
        if (opts.length === 0) return null;
        const disabledOptions =
          grantedProficiencies && isProficiencyChoice(choice)
            ? grantedProficiencies
            : undefined;
        return (
          <ChoiceList
            key={key}
            choiceKey={key}
            title={choice.title ?? key}
            description={choice.description}
            options={opts as Array<string | { name?: string }>}
            count={choice.count ?? 1}
            disabledOptions={disabledOptions}
            disabledReason="Already granted"
          />
        );
      })}
    </section>
  );
}
