---
description: 'Find the next highest-priority task from the backlog and generate a work plan'
---

Use the `update-backlog` skill to scan current completeness, then identify the highest-priority incomplete item.

## Priority Order

1. **Classes with data files but no validated features** — closest to completion
2. **Missing background data files** — required for character creation
3. **Missing feat data** — origin feats first (needed at level 1), then general feats
4. **Missing spell definitions** — block subclass features that grant spells
5. **Subclasses without effects** — features exist but no mechanical implementation

## Output

Report:
- **Next task**: What to implement
- **Category**: Class/subclass/background/feat/spell
- **Priority**: Why this was selected
- **Skills to use**: Which skills apply (`implement-class-feature`, `add-game-content`, etc.)
- **Dependencies**: Any blockers (missing wiki data, missing effect types)
