/**
 * SheetPdf — printable, PDF-parity character sheet.
 *
 * Mirrors `templates/character_sheet_pdf.html`: an 8.5×11in canvas
 * with the official background image, overlaying read-only fields at
 * pixel-precise positions. Designed for `window.print()` output.
 *
 * Read-only by design — the React SPA's source of truth is the wizard,
 * so this view only renders. Edit in the wizard, print here.
 *
 * Desktop-only: at viewport widths < 900px the sheet is replaced with
 * a friendly "use a desktop" message (the absolute layout is too
 * fragile to reflow).
 */
import { Link } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useCharacterStore } from "@/store/characterStore";
import { useEffect, useState } from "react";

type Char = Record<string, unknown>;
type Row = Record<string, unknown>;

function num(v: unknown): number | undefined {
  return typeof v === "number" ? v : undefined;
}
function str(v: unknown): string | undefined {
  return typeof v === "string" ? v : undefined;
}
function arr<T = unknown>(v: unknown): T[] {
  return Array.isArray(v) ? (v as T[]) : [];
}
function rec(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : {};
}
function signed(n: number | undefined): string {
  if (n === undefined) return "";
  return n >= 0 ? `+${n}` : String(n);
}

function useIsDesktop(min = 900) {
  const [ok, setOk] = useState(
    typeof window === "undefined" ? true : window.innerWidth >= min,
  );
  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${min}px)`);
    const handler = () => setOk(mq.matches);
    handler();
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [min]);
  return ok;
}

export function SheetPdf() {
  const choicesMade = useCharacterStore((s) => s.choicesMade);
  const isDesktop = useIsDesktop();

  const buildQuery = useQuery({
    queryKey: ["character", "build", choicesMade],
    queryFn: () => api.character.build(choicesMade),
    retry: false,
    placeholderData: keepPreviousData,
  });

  const cantripsQuery = useQuery({
    queryKey: ["character", "derived", "damage_cantrips", choicesMade],
    queryFn: () => api.character.derived(choicesMade, "damage_cantrips"),
    retry: false,
    enabled: !!buildQuery.data,
  });

  if (!isDesktop) {
    return (
      <Frame>
        <div className="mx-auto max-w-md p-8 text-center">
          <h1 className="font-display text-2xl text-primary mb-3">
            Desktop view required
          </h1>
          <p className="text-sm text-muted-foreground">
            The printable sheet uses a fixed 8.5×11in layout. Open this
            page on a desktop browser (≥ 900px wide) to view or print.
          </p>
          <p className="mt-4">
            <Link to="/sheet" className="text-primary underline">
              Back to summary sheet →
            </Link>
          </p>
        </div>
      </Frame>
    );
  }

  if (buildQuery.isLoading) {
    return (
      <Frame>
        <div className="p-10 text-muted-foreground">Building character…</div>
      </Frame>
    );
  }
  if (buildQuery.error) {
    return (
      <Frame>
        <div className="p-10 max-w-md mx-auto text-center">
          <p className="text-destructive">
            Cannot build character: {String(buildQuery.error)}
          </p>
          <p className="mt-3 text-sm text-muted-foreground">
            Finish the wizard first.{" "}
            <Link to="/wizard" className="text-primary underline">
              Go to wizard →
            </Link>
          </p>
        </div>
      </Frame>
    );
  }

  const c = (buildQuery.data?.character ?? {}) as Char;
  const cantripData = cantripsQuery.data?.data;
  const damageCantrips = arr<Row>(cantripData);

  return (
    <Frame>
      <Toolbar />
      <Page1 c={c} damageCantrips={damageCantrips} />
      <Page2 c={c} />
    </Frame>
  );
}

function Frame({ children }: { children: React.ReactNode }) {
  return (
    <div className="sheet-pdf-root">
      <style>{SHEET_CSS}</style>
      {children}
    </div>
  );
}

function Toolbar() {
  return (
    <div className="sheet-toolbar no-print">
      <Link to="/sheet" className="sheet-tool-btn sheet-tool-back">
        ← Summary
      </Link>
      <button
        type="button"
        className="sheet-tool-btn sheet-tool-print"
        onClick={() => window.print()}
      >
        🖨️ Print to PDF
      </button>
    </div>
  );
}

// ---------- Page 1 ----------

function Page1({
  c,
  damageCantrips,
}: {
  c: Char;
  damageCantrips: Row[];
}) {
  const combat = rec(c.combat);
  const hp = rec(combat.hit_points);
  const hitDice = rec(combat.hit_dice);
  const skills = rec(c.skills);
  const abilities = rec(c.abilities);
  const acOptions = arr<Row>(c.ac_options);
  const ac =
    num(combat.armor_class) ??
    (acOptions.length > 0 ? num(acOptions[0].ac) : undefined);

  const perception = rec(skills.perception);
  const perceptionMod = num(perception.modifier) ?? num(perception.bonus) ?? 0;
  const passive = 10 + perceptionMod;

  const armorProfs = arr<string>(c.armor_proficiencies);
  const weaponProfs = arr<string>(c.weapon_proficiencies);
  const toolProfs = arr<string>(c.tool_proficiencies);

  const features = rec(c.features);
  const classFeatures = arr<Row>(features.class);
  const speciesFeatures = arr<Row>(features.species);
  const featFeatures = arr<Row>(features.feats);

  const attacks = arr<Row>(c.attacks).slice(0, 6);
  const cantripSlots = Math.max(0, 6 - attacks.length);
  const cantripRows = damageCantrips.slice(0, cantripSlots);

  const lineage = str(c.lineage);
  const speciesText =
    (str(c.species) ?? "") + (lineage ? ` (${lineage})` : "");

  return (
    <div className="sheet-container">
      <div className="sheet-bg sheet-bg-1" />
      <div className="sheet-fields">
        {/* Basic info */}
        <Field id="character-name" value={str(c.name)} />
        <Field id="class" value={str(c.class)} />
        <Field id="background" value={str(c.background)} />
        <Field id="species" value={speciesText || undefined} />
        <Field id="subclass" value={str(c.subclass)} />
        <Field id="level" value={num(c.level)} />
        <Field id="size" value={str(c.size) ?? "Medium"} />
        <Field id="proficiency-bonus" value={signed(num(c.proficiency_bonus))} />

        {/* Combat */}
        <Field id="armor-class" value={ac} />
        <Field
          id="initiative"
          value={signed(num(combat.initiative_bonus) ?? num(combat.initiative))}
        />
        <Field
          id="speed"
          value={
            num(combat.speed) !== undefined
              ? `${num(combat.speed)}ft`
              : num(c.speed) !== undefined
                ? `${num(c.speed)}ft`
                : undefined
          }
        />
        <Field id="hp_max" value={num(hp.maximum) ?? num(combat.hp)} />
        <Field
          id="hit_dice"
          value={str(hitDice.total) ?? num(hitDice.total)}
        />
        <Field id="passive-perception" value={passive} />

        {/* Ability blocks */}
        <AbilityBlock
          id="ability-str"
          name="Strength"
          abilities={abilities}
          skills={skills}
          skillKeys={["athletics"]}
        />
        <AbilityBlock
          id="ability-dex"
          name="Dexterity"
          abilities={abilities}
          skills={skills}
          skillKeys={["acrobatics", "sleight_of_hand", "stealth"]}
        />
        <AbilityBlock
          id="ability-con"
          name="Constitution"
          abilities={abilities}
          skills={skills}
          skillKeys={[]}
        />
        <AbilityBlock
          id="ability-int"
          name="Intelligence"
          abilities={abilities}
          skills={skills}
          skillKeys={[
            "arcana",
            "history",
            "investigation",
            "nature",
            "religion",
          ]}
        />
        <AbilityBlock
          id="ability-wis"
          name="Wisdom"
          abilities={abilities}
          skills={skills}
          skillKeys={[
            "animal_handling",
            "insight",
            "medicine",
            "perception",
            "survival",
          ]}
        />
        <AbilityBlock
          id="ability-cha"
          name="Charisma"
          abilities={abilities}
          skills={skills}
          skillKeys={[
            "deception",
            "intimidation",
            "performance",
            "persuasion",
          ]}
        />

        {/* Weapons & damage cantrips: 6 rows */}
        {Array.from({ length: 6 }).map((_, i) => {
          const top = 272 + i * 26;
          let name = "";
          let atk = "";
          let dmg = "";
          let extra = "";
          if (i < attacks.length) {
            const w = attacks[i];
            name = str(w.name) ?? "";
            atk = str(w.attack_bonus_display) ?? signed(num(w.attack_bonus));
            const damage = str(w.damage) ?? "";
            const dtype = str(w.damage_type) ?? "";
            dmg = `${damage} ${dtype}`.trim();
            const props = arr<string>(w.properties);
            extra = props.length ? props.join(", ") : "";
          } else {
            const cIdx = i - attacks.length;
            if (cIdx < cantripRows.length) {
              const cn = cantripRows[cIdx];
              name = str(cn.name) ?? "";
              atk = str(cn.atk_display) ?? "";
              const damage = str(cn.damage) ?? "";
              const dtype = str(cn.damage_type) ?? "";
              dmg = `${damage} ${dtype}`.trim();
              extra = str(cn.notes) ?? "";
            }
          }
          return (
            <div key={i}>
              <BoxField
                style={{ top, left: 307, width: 152, height: 22, fontSize: 8, textAlign: "left" }}
                value={name}
              />
              <BoxField
                style={{ top, left: 448, width: 70, height: 22, fontSize: 8 }}
                value={atk}
              />
              <BoxField
                style={{ top, left: 520, width: 128, height: 22, fontSize: 8, textAlign: "left" }}
                value={dmg}
              />
              <BoxField
                style={{ top, left: 666, width: 126, height: 22, fontSize: 8, textAlign: "left" }}
                value={extra}
              />
            </div>
          );
        })}

        {/* Armor proficiency checkboxes */}
        <Check
          style={{ top: 878, left: 75 }}
          checked={armorProfs.includes("Light armor")}
        />
        <Check
          style={{ top: 878, left: 122 }}
          checked={armorProfs.includes("Medium armor")}
        />
        <Check
          style={{ top: 878, left: 182 }}
          checked={armorProfs.includes("Heavy armor")}
        />
        <Check
          style={{ top: 878, left: 233 }}
          checked={armorProfs.includes("Shields")}
        />

        <BoxField
          style={{
            top: 910,
            left: 16,
            width: 258,
            height: 52,
            fontSize: 7,
            textAlign: "left",
            lineHeight: 1.3,
            whiteSpace: "normal",
            overflow: "hidden",
          }}
          value={weaponProfs.join(", ")}
          multiline
        />
        <BoxField
          style={{
            top: 992,
            left: 16,
            width: 258,
            height: 28,
            fontSize: 7,
            textAlign: "left",
            lineHeight: 1.3,
            whiteSpace: "normal",
            overflow: "hidden",
          }}
          value={toolProfs.join(", ")}
          multiline
        />

        {/* Features columns */}
        <FeatureColumn
          style={{
            top: 473,
            left: 306,
            width: 490,
            height: 285,
            columnCount: 2,
            columnGap: 10,
          }}
          features={classFeatures}
          titleSize={7}
          bodySize={6}
        />
        <FeatureColumn
          style={{ top: 806, left: 306, width: 227, height: 200 }}
          features={speciesFeatures}
          titleSize={7}
          bodySize={6}
        />
        <FeatureColumn
          style={{ top: 806, left: 558, width: 238, height: 200 }}
          features={featFeatures}
          titleSize={7}
          bodySize={6}
        />
      </div>
    </div>
  );
}

// ---------- Page 2 (placeholder background only) ----------

function Page2({ c: _c }: { c: Char }) {
  return (
    <div className="sheet-container">
      <div className="sheet-bg sheet-bg-2" />
      <div className="sheet-fields">
        {/* Page 2 fields are not positioned yet; this page remains blank for now. */}
      </div>
    </div>
  );
}

// ---------- Field primitives ----------

function Field({
  id,
  value,
}: {
  id: string;
  value: string | number | undefined;
}) {
  if (value === undefined || value === null || value === "") {
    return <div className={`fld fld-${id}`} />;
  }
  return <div className={`fld fld-${id}`}>{value}</div>;
}

function BoxField({
  style,
  value,
  multiline,
}: {
  style: React.CSSProperties;
  value: string | number | undefined;
  multiline?: boolean;
}) {
  const merged: React.CSSProperties = {
    position: "absolute",
    fontFamily: "'Segoe UI', sans-serif",
    textAlign: "center",
    padding: 2,
    color: "#000",
    whiteSpace: multiline ? "normal" : "nowrap",
    overflow: "hidden",
    ...style,
  };
  if (typeof merged.fontSize === "number") {
    merged.fontSize = `${merged.fontSize}pt`;
  }
  if (typeof merged.top === "number") merged.top = `${merged.top}px`;
  if (typeof merged.left === "number") merged.left = `${merged.left}px`;
  if (typeof merged.width === "number") merged.width = `${merged.width}px`;
  if (typeof merged.height === "number") merged.height = `${merged.height}px`;
  return <div style={merged}>{value ?? ""}</div>;
}

function Check({
  style,
  checked,
}: {
  style: React.CSSProperties;
  checked: boolean;
}) {
  const merged: React.CSSProperties = {
    position: "absolute",
    width: 14,
    height: 14,
    border: "1px solid transparent",
    color: "#000",
    fontSize: "13pt",
    lineHeight: "14px",
    textAlign: "center",
    ...style,
  };
  if (typeof merged.top === "number") merged.top = `${merged.top}px`;
  if (typeof merged.left === "number") merged.left = `${merged.left}px`;
  return <div style={merged}>{checked ? "✓" : ""}</div>;
}

// ---------- Ability block ----------

function AbilityBlock({
  id,
  name,
  abilities,
  skills,
  skillKeys,
}: {
  id: string;
  name: string;
  abilities: Record<string, unknown>;
  skills: Record<string, unknown>;
  skillKeys: string[];
}) {
  const a = rec(
    abilities[name.toLowerCase()] ??
      abilities[name] ??
      abilities[name.slice(0, 3).toLowerCase()],
  );
  const score = num(a.score);
  const modifier = num(a.modifier) ?? num(a.mod);
  const save = num(a.saving_throw);
  const saveProf = a.saving_throw_proficient === true;

  return (
    <div className={`ab ab-${id}`}>
      <div
        className="abs-field"
        style={{ top: 37, left: 65, width: 40, height: 30, fontSize: "11pt" }}
      >
        {score ?? ""}
      </div>
      <div
        className="abs-field"
        style={{
          top: 33,
          left: 17,
          width: 50,
          height: 25,
          fontSize: "16pt",
        }}
      >
        {signed(modifier)}
      </div>
      <Check style={{ top: 98, left: 8, width: 12 }} checked={saveProf} />
      <div
        className="abs-field"
        style={{ top: 93, left: 22, width: 20, fontSize: "9pt" }}
      >
        {signed(save)}
      </div>
      {skillKeys.map((key, i) => {
        const s = rec(skills[key]);
        const mod = num(s.modifier) ?? num(s.bonus);
        const prof = s.proficient === true || s.expertise === true;
        return (
          <div key={key}>
            <Check
              style={{ top: 118 + 7 + i * 19, left: 9, width: 12 }}
              checked={prof}
            />
            <div
              className="abs-field"
              style={{
                top: 118 + 2 + i * 19,
                left: 22,
                width: 20,
                fontSize: "9pt",
              }}
            >
              {signed(mod)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------- Feature columns ----------

function FeatureColumn({
  style,
  features,
  titleSize,
  bodySize,
}: {
  style: React.CSSProperties;
  features: Row[];
  titleSize: number;
  bodySize: number;
}) {
  const merged: React.CSSProperties = {
    position: "absolute",
    color: "#000",
    overflow: "hidden",
    ...style,
  };
  if (typeof merged.top === "number") merged.top = `${merged.top}px`;
  if (typeof merged.left === "number") merged.left = `${merged.left}px`;
  if (typeof merged.width === "number") merged.width = `${merged.width}px`;
  if (typeof merged.height === "number") merged.height = `${merged.height}px`;
  return (
    <div style={merged}>
      {features.map((f, i) => {
        const name = str(f.name) ?? "";
        const desc = str(f.description) ?? "";
        return (
          <div
            key={i}
            style={{
              marginBottom: 4,
              breakInside: "avoid",
              fontFamily: "'Segoe UI', sans-serif",
            }}
          >
            <div
              style={{
                fontSize: `${titleSize}pt`,
                fontWeight: "bold",
                lineHeight: 1.1,
              }}
            >
              {name}
            </div>
            <div
              style={{
                fontSize: `${bodySize}pt`,
                lineHeight: 1.1,
                whiteSpace: "pre-wrap",
              }}
            >
              {desc}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------- Stylesheet ----------
//
// Mirrors `templates/character_sheet_pdf.html` field positions exactly
// so the PNG background and the overlay align without further tweaks.

const SHEET_CSS = `
.sheet-pdf-root {
  background-color: #f5f5f5;
  min-height: 100vh;
  padding-bottom: 40px;
  color: #000;
}

.sheet-toolbar {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background: #fff;
  padding: 10px;
  border-radius: 5px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  display: flex;
  gap: 6px;
}
.sheet-tool-btn {
  padding: 8px 14px;
  border-radius: 4px;
  font-size: 14px;
  text-decoration: none;
  color: #fff;
  border: none;
  cursor: pointer;
}
.sheet-tool-print { background-color: #28a745; }
.sheet-tool-back { background-color: #6c757d; display: inline-flex; align-items: center; }

.sheet-container {
  position: relative;
  width: 8.5in;
  height: 11in;
  margin: 20px auto;
  background-color: #fff;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  page-break-after: always;
  color: #000;
}
.sheet-container:last-child { page-break-after: auto; }

.sheet-bg {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background-size: cover;
  background-position: center;
  z-index: 1;
}
.sheet-bg-1 { background-image: url('/pdf_template/sheet1.png'); }
.sheet-bg-2 { background-image: url('/pdf_template/sheet2.png'); }

.sheet-fields {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  z-index: 2;
}

.fld {
  position: absolute;
  font-family: 'Segoe UI', sans-serif;
  text-align: center;
  font-size: 11pt;
  padding: 2px;
  color: #000;
  white-space: nowrap;
  overflow: hidden;
}

/* Field positions — mirror character_sheet_pdf.html exactly. */
.fld-character-name { top: 21px; left: 32px; width: 290px; height: 20px; font-size: 14pt; font-weight: 600; text-align: left; }
.fld-class          { top: 51px; left: 200px; width: 127px; height: 20px; text-align: left; }
.fld-subclass       { top: 81px; left: 200px; width: 127px; height: 20px; text-align: left; }
.fld-background     { top: 51px; left: 32px;  width: 150px; height: 20px; text-align: left; }
.fld-species        { top: 81px; left: 32px;  width: 150px; height: 20px; text-align: left; }
.fld-level          { top: 38px; left: 358px; width: 30px;  height: 20px; font-size: 14pt; }
.fld-size           { top: 181px; left: 589px; width: 48px; height: 20px; font-size: 9pt; }
.fld-passive-perception { top: 181px; left: 718px; width: 48px; height: 20px; font-size: 9pt; }

.fld-armor-class       { top: 56px;  left: 445px; width: 30px; height: 20px; font-size: 14pt; }
.fld-initiative        { top: 181px; left: 339px; width: 30px; height: 20px; }
.fld-speed             { top: 181px; left: 453px; width: 60px; height: 20px; }
.fld-hp_max            { top: 79px;  left: 595px; width: 60px; height: 20px; }
.fld-hit_dice          { top: 79px;  left: 665px; width: 56px; height: 20px; }
.fld-proficiency-bonus { top: 196px; left: 58px;  width: 30px; height: 20px; font-size: 16pt; }

.ab { position: absolute; }
.ab-ability-str { top: 257px; left: 12px; }
.ab-ability-dex { top: 418px; left: 12px; }
.ab-ability-con { top: 617px; left: 12px; }
.ab-ability-int { top: 151px; left: 156px; }
.ab-ability-wis { top: 389px; left: 156px; }
.ab-ability-cha { top: 626px; left: 156px; }

.abs-field {
  position: absolute;
  font-family: 'Segoe UI', sans-serif;
  text-align: center;
  padding: 2px;
  color: #000;
  white-space: nowrap;
  overflow: hidden;
}

@media print {
  .no-print { display: none !important; }
  .sheet-pdf-root { background: #fff; padding: 0; }
  .sheet-container {
    margin: 0;
    box-shadow: none;
    page-break-after: always;
  }
  .sheet-container:last-child { page-break-after: auto; }
  @page { size: letter; margin: 0; }
}
`;
