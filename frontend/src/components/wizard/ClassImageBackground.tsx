import { useEffect, useState } from "react";
import { useCharacterStore } from "@/store/characterStore";

/**
 * Full-height background using the selected class image, flipped and washed out.
 * Positioned behind the central content panel.
 */
export function ClassImageBackground() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.classList.contains("dark"),
  );

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains("dark"));
    });
    observer.observe(document.documentElement, { attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const theme = isDark ? "dark" : "light";
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

    const fallbackClassChoice = s.choicesMade.class;
    if (
      typeof fallbackClassChoice === "string" &&
      fallbackClassChoice.length > 0
    ) {
      return fallbackClassChoice;
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

  // Try the theme-specific variant first (e.g. "monk-dark.png"), fall back to base.
  const baseName = selectedClass
    ? (selectedClass as string).toLowerCase()
    : null;
  const classImageSrc = baseName
    ? `/images/classes/${baseName}-${theme}.png`
    : null;
  const fallbackSrc = baseName ? `/images/classes/${baseName}.png` : null;

  if (!classImageSrc || !fallbackSrc) {
    return null;
  }

  return (
    <div className="fixed right-0 top-0 bottom-0 -z-50 pointer-events-none hidden lg:block">
      <img
        src={classImageSrc}
        alt=""
        className="h-full w-auto object-cover object-center scale-x-[-1] opacity-60 [mask-image:linear-gradient(to_left,transparent_0%,black_35%)]"
        aria-hidden="true"
        onError={(e) => {
          const img = e.currentTarget;
          if (img.src !== window.location.origin + fallbackSrc) {
            img.src = fallbackSrc;
          }
        }}
      />
    </div>
  );
}
