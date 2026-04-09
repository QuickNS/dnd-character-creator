---
description: 'Generate parallel task assignments for a batch of game content: all subclasses for a class, all missing backgrounds, etc.'
---

Implement all {{ content_category }} for {{ scope }} in parallel.

## Procedure

1. Read `data/completeness/backlog.json` to identify all missing items in the specified category
2. For each missing item, generate an independent task:
   - Fetch wiki data if not cached
   - Create/update data file with effects
   - Validate against schema
   - Write tests
3. Identify shared dependencies (e.g., new effect types needed by multiple items)
4. Resolve shared dependencies first, then parallelize independent items

## Agent Assignment

Each item gets the standard chain:
1. @wiki-fetcher — Ensure wiki cache exists
2. @data-author — Create JSON data file
3. @data-validator — Verify schema compliance
4. @test-writer — Write tests

If new effect types are needed, @feature-implementer runs first for the shared handler.

## Output

For each item:
- Item name and file path
- Status: created / updated / blocked
- Test status: pass / fail
- Backlog updated: yes / no
