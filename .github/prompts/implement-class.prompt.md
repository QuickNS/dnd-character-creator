---
description: 'Implements class features end-to-end with automatic branch management and PR creation'
---

Implement all features for **{{ class_name }}** end-to-end.

## Branch Setup

Create and switch to a new branch from `main`:
- Run `git checkout main && git pull`
- Run `git checkout -b class/{{ class_name }}`

## Implementation

Use the `implement-class-feature` and `add-game-content` skills to implement all class and subclass features for **{{ class_name }}**:
- Class data: `data/classes/{{ class_name }}.json`
- Subclass data: `data/subclasses/{{ class_name }}/`
- Wiki data: `wiki_data/classes/{{ class_name }}.json`
- Tests: `tests/{{ class_name }}/test_{{ class_name }}_features.py`

Update `data/completeness/backlog.json` to mark {{ class_name }} features as validated.

## Push, Create PR, and Merge

Commit all changes, push, create a PR, and merge:
- Run `git add -A && git commit -m "feat({{ class_name }}): implement class and subclass features"`
- Run `git push -u origin class/{{ class_name }}`
- Use `mcp_github_create_pull_request` to create a PR:
  - Title: `feat({{ class_name }}): implement class and subclass features`
  - Base: `main`, Head: `class/{{ class_name }}`
  - Body: summary of added/updated data files, new effect handlers, and tests
- Use `mcp_github_merge_pull_request` to merge the PR (squash merge, delete_branch: true)
- Run `git checkout main && git pull && git branch -d class/{{ class_name }}`
