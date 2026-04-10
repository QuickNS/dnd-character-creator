---
description: 'Implement a batch of game content in parallel'
---

Implement all {{ content_category }} for {{ scope }} in parallel.

Use the `add-game-content` skill for each item. Before parallelizing:

1. Read `data/completeness/backlog.json` to identify all missing items
2. Identify shared dependencies (e.g., new effect types needed by multiple items) — resolve these first via `implement-class-feature` skill
3. Then process each independent item in parallel using the `add-game-content` workflow

## Output

For each item:
- Item name and file path
- Status: created / updated / blocked
- Test status: pass / fail
- Backlog updated: yes / no
