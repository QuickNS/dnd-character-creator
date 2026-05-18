import { useCharacterStore } from "@/store/characterStore";

/**
 * Full-height background using the selected class image, flipped and washed out.
 * Positioned behind the central content panel.
 */
export function ClassImageBackground() {
  const selectedClass = useCharacterStore((s) => {
    const rows = s.choicesMade.classes;
    if (Array.isArray(rows) && rows.length > 0) {
      const clampedIndex = Math.max(
        0,
        Math.min(s.activeClassRowIndex, rows.length - 1),
      );
      const active = rows[clampedIndex] as { class_name?: unknown } | undefined;
      const activeClassName = active?.class_name;
      if (typeof activeClassName === "string" && activeClassName.length > 0) {
        return activeClassName;
      }
    }

    const fromLegacy = s.choicesMade.class;
    if (typeof fromLegacy === "string" && fromLegacy.length > 0) {
      return fromLegacy;
    }

    if (!Array.isArray(rows) || rows.length === 0) return undefined;
    const primary = rows[0];
    if (!primary) {
      return undefined;
    }
    const className = primary.class_name;
    return typeof className === "string" && className.length > 0
      ? className
      : undefined;
  });

  // Convert class name to filename (e.g., "Barbarian" -> "barbarian.png")
  const classImageName = selectedClass
    ? `${(selectedClass as string).toLowerCase()}.png`
    : null;

  if (!classImageName) {
    return null;
  }

  return (
    <div className="fixed right-0 top-0 bottom-0 -z-50 pointer-events-none hidden lg:block">
      <img
        src={`/images/classes/${classImageName}`}
        alt=""
        className="h-full w-auto object-cover object-center scale-x-[-1] opacity-60"
        aria-hidden="true"
      />
    </div>
  );
}
