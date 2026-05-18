#!/usr/bin/env python3
"""
Migration script: update all spell definition JSON files.

For each file in data/spells/definitions/:
  1. Remove the "source" key (if present).
  2. Add/set "ritual" boolean:
       True  if the file already has "ritual": true
             OR if casting_time contains the word "ritual" (case-insensitive)
       False otherwise.
  3. Write back with 2-space indentation and a trailing newline.
"""

import json
import pathlib
import sys

DEFINITIONS_DIR = pathlib.Path(__file__).parent.parent / "data" / "spells" / "definitions"


def main() -> None:
    files = sorted(DEFINITIONS_DIR.glob("*.json"))
    if not files:
        print(f"ERROR: no JSON files found in {DEFINITIONS_DIR}", file=sys.stderr)
        sys.exit(1)

    total = 0
    ritual_true = 0
    ritual_false = 0
    missing_fields: list[str] = []
    source_removed: list[str] = []

    for path in files:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)

        total += 1
        changed = False

        # ── 1. Determine ritual value ──────────────────────────────────────────
        already_ritual = bool(data.get("ritual"))
        casting_time = data.get("casting_time", "")
        if not isinstance(casting_time, str):
            missing_fields.append(f"{path.name}: casting_time is not a string ({casting_time!r})")
            casting_time = ""

        is_ritual = already_ritual or ("ritual" in casting_time.lower())

        if data.get("ritual") != is_ritual:
            changed = True
        data["ritual"] = is_ritual

        if is_ritual:
            ritual_true += 1
        else:
            ritual_false += 1

        # ── 2. Remove "source" ─────────────────────────────────────────────────
        if "source" in data:
            del data["source"]
            changed = True
            source_removed.append(path.name)

        # Track files missing expected fields (but still process them)
        for field in ("name", "level", "school", "casting_time", "description"):
            if field not in data:
                missing_fields.append(f"{path.name}: missing field '{field}'")

        # ── 3. Write back ──────────────────────────────────────────────────────
        if changed:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    # ── Report ─────────────────────────────────────────────────────────────────
    print(f"Files processed : {total}")
    print(f"  ritual=true   : {ritual_true}")
    print(f"  ritual=false  : {ritual_false}")
    print(f"  source removed: {len(source_removed)}")

    if missing_fields:
        print(f"\nFiles with unexpected/missing fields ({len(missing_fields)}):")
        for note in missing_fields:
            print(f"  {note}")
    else:
        print("\nNo unexpected/missing fields found.")


if __name__ == "__main__":
    main()
