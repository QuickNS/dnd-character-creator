---
name: fix-class-issues
description: "Pick up and resolve bugs, missing features, or inaccuracies tracked as GitHub Issues. Use when fixing known problems for a specific class or subclass."
---

# Fix Class Issues

Workflow for resolving issues (bugs, missing features, inaccuracies) tracked as GitHub Issues in `QuickNS/dnd-character-creator`.

## When to Use

- When asked to fix bugs or missing features for a class
- When asked "what issues are open?" and then to resolve them
- When assigned a specific GitHub Issue number

## Issue Conventions

Issues follow this title format: `[ClassName] Short description`

Labels used:
- `bug` — Something is broken or incorrect
- `enhancement` — Missing feature or improvement needed

The issue body contains structured sections: Issue Type, Severity, Class/Feature, Affected Levels, Description, Current Behavior, Expected Behavior, and Files.

## Procedure

### 1. Find Open Issues

Use the GitHub MCP tools to list or search issues:

```
mcp_github_list_issues(owner="QuickNS", repo="dnd-character-creator", state="OPEN")
```

Or search for a specific class:
```
mcp_github_search_issues(query="repo:QuickNS/dnd-character-creator is:open [Monk]")
```

Pick the highest-severity open issue to fix first (severity is noted in the issue body).

### 2. Read the Issue

```
mcp_github_issue_read(owner="QuickNS", repo="dnd-character-creator", issueNumber=N)
```

Parse the issue body to understand: affected levels, current vs expected behavior, and which files to change.

### 3. Create a Feature Branch

Create a branch from `main` for this fix. Use the naming convention `fix/issue-N-short-description`:

```bash
git checkout main && git pull
git checkout -b fix/issue-N-short-description
```

### 4. Verify Against Wiki Source

Check wiki data to confirm the correct D&D 2024 rules:

```bash
# Check class cache
cat wiki_data/classes/{class_name}.json | python -m json.tool | head -100

# If missing, fetch it
python update_classes.py --class {class_name}
```

Parse `content.text` to understand the feature's intended mechanics. Never guess — the wiki is the source of truth.

### 5. Fix the Issue

Depending on issue type:

**`enhancement` (missing feature)**: Add or update effects in the class/subclass JSON:
```json
"Feature Name": {
  "description": "...",
  "effects": [
    {"type": "...", ...}
  ]
}
```

**`bug`**: Fix the incorrect data or effect in the JSON. May also require fixing effect handlers in `modules/character_builder.py` → `_apply_effect()`.

### 6. Validate

```bash
python validate_data.py
pytest tests/ -x -q --tb=short
```

### 7. Write or Update Tests

Every fix should have a test proving it works. Follow the patterns in `tests/`:

```python
from modules.character_builder import CharacterBuilder

def test_feature_name_effect():
    """Regression test for GitHub Issue #N: title"""
    builder = CharacterBuilder()
    builder.apply_choices({
        "character_name": "Test",
        "level": ...,  # affected level
        "class": "...",
        ...
    })
    character = builder.to_character()
    # Assert the fix is correct
    assert ...
```

### 8. Commit, Push, and Create a Pull Request

Commit the changes and push the branch:

```bash
git add -A
git commit -m "Fix #N: short description"
git push -u origin fix/issue-N-short-description
```

Create a pull request linking the issue:

```
mcp_github_create_pull_request(
    owner="QuickNS",
    repo="dnd-character-creator",
    head="fix/issue-N-short-description",
    base="main",
    title="Fix #N: short description",
    body="## Summary\n\n{what was changed and why}\n\nCloses #N\n\n## Changes\n- {file}: {what changed}\n\n## Testing\n- All existing tests pass\n- Added: {new test file or function}"
)
```

### 9. Present Summary and Ask for Confirmation

Report what was fixed and **ask the user to confirm before merging**:

```
PR #{pr_number} created for issue #N — {title}
  - Branch: fix/issue-N-short-description
  - Changed: data/classes/{class}.json (added effects for {feature})
  - Added: tests/test_{class}_{feature}.py
  - Tests: all passing

Please review the PR. Ready to merge and close issue #N?
```

**Do NOT merge or close until the user explicitly confirms.** Wait for approval.

### 10. Merge and Close

Only after user confirmation:

1. Merge the PR:
```
mcp_github_merge_pull_request(owner="QuickNS", repo="dnd-character-creator", pullNumber=PR_NUMBER)
```

2. Close the issue with a comment:
```
mcp_github_add_issue_comment(owner="QuickNS", repo="dnd-character-creator", issue_number=N,
    body="Fixed in PR #PR_NUMBER.")
mcp_github_issue_write(owner="QuickNS", repo="dnd-character-creator", issue_number=N,
    method="update", state="closed", state_reason="completed")
```

3. Switch back to main locally:
```bash
git checkout main && git pull
```

If ALL issues for a class are resolved and the class is verified complete, also update boolean flags in `data/completeness/backlog.json`:
```json
"features_validated": true,
"effects_implemented": true,
"tests_written": true
```

## Tips

- Fix one issue at a time. Run tests between each fix.
- For missing feature issues, use the implement-class-feature skill's effect mapping table to choose the right effect types.
- When an issue requires a new effect type, also update `FEATURE_EFFECTS.md` and `_apply_effect()`.
- Subclass issues will have titles like `[Monk/Warrior of Shadow] ...`.
