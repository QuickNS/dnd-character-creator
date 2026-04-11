---
description: 'Implement a batch of missing game content for a category'
agent: 'agent'
argument-hint: 'e.g., content_category=subclasses, scope=Ranger'
---

Implement all missing {{ content_category }} for {{ scope }}.

1. Check `data/completeness/backlog.json` for missing items
2. Resolve shared dependencies first (e.g., new effect types)
3. Process each independent item using the appropriate prompt (`/implement-class`, `/add-data-files`, etc.)
