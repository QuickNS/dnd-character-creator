---
description: 'Find the next highest-priority task from the backlog and generate a work plan'
---

Read `data/completeness/backlog.json` and identify the highest-priority incomplete item.

## Priority Order

1. **Classes with data files but no validated features** — These are closest to completion
2. **Missing background data files** — Required for character creation
3. **Missing feat data** — Origin feats first (needed at level 1), then general feats
4. **Missing spell definitions** — Block subclass features that grant spells
5. **Subclasses without effects** — Features exist but no mechanical implementation

## Task Generation

For the highest-priority item, generate a work plan:

1. What agent chain to use (wiki-fetcher → data-author → feature-implementer → test-writer)
2. What specific files need to be created or updated
3. What effect types are likely needed
4. What tests should be written
5. Estimated complexity (simple data entry vs new effect types needed)

## Output

Report:
- **Next task**: What to implement
- **Category**: Class/subclass/background/feat/spell
- **Priority**: Why this was selected
- **Agent chain**: Which agents in what order
- **Dependencies**: Any blockers (missing wiki data, missing effect types)
