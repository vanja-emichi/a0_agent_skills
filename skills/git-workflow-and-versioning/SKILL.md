---
name: git-workflow-and-versioning
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Git workflow and version control best practices. Use when committing code,
  creating branches, preparing pull requests, or managing release versioning.
  Use when structuring commit messages or planning a branching strategy.
tags:
  - git
  - version-control
  - commits
  - branching
  - pull-requests
trigger_patterns:
  - git-workflow-and-versioning
  - commit message
  - create a branch
  - pull request
  - git workflow
  - conventional commits
  - semantic versioning
  - branch naming
  - squash commits
  - release versioning
  - branching strategy
  - git branching
  - what branch strategy
  - trunk based development
  - feature branch
  - git merge strategy
  - git rebase
  - git flow
  - monorepo git
---

# Git Workflow and Versioning

## Overview

Git history is documentation. A well-structured commit history lets you understand what changed, why it changed, and who changed it — weeks or months later. This skill covers commit practices, branching strategies, pull request quality, and semantic versioning.

## When to Use

- Writing commit messages
- Creating feature branches
- Preparing pull requests for review
- Planning a release or version bump
- Reviewing git history to understand context

## Commit Messages

### The Conventional Commits Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, whitespace (no logic change) |
| `refactor` | Code restructuring (no feature, no bug fix) |
| `test` | Adding or fixing tests |
| `chore` | Build process, dependencies, tooling |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration changes |

**Examples:**

```bash
# Good: clear type, scope, and description
git commit -m "feat(tasks): add priority levels to task creation"
git commit -m "fix(auth): handle expired tokens gracefully"
git commit -m "refactor(api): extract validation middleware"
git commit -m "docs(readme): add deployment instructions"

# With body for non-obvious changes
git commit -m "fix(tasks): prevent duplicate task creation on fast double-click

Added debounce to the create button click handler and optimistic
update deduplication in the React Query mutation. The underlying
API already had idempotency guards, but the UI was sending multiple
requests before the first one resolved.

Fixes #234"

# Breaking changes
git commit -m "feat(api)!: change task status enum values

BREAKING CHANGE: Status values changed from 'todo/done' to
'pending/completed' to match the new backend schema.
Migrate existing data with: npm run migrate:status"
```

### The Subject Line Rules

```
✓ Imperative mood: "Add feature" not "Added feature" or "Adds feature"
✓ 50 characters or fewer
✓ No period at the end
✓ Lowercase after the type prefix
✓ Describes WHAT changed, not HOW it was implemented

✗ Bad: "fixed stuff"
✗ Bad: "WIP"
✗ Bad: "Updates to task component"
✗ Bad: "I changed the validation logic because it wasn't working correctly"
```

## Branching Strategy

### Branch Naming

```bash
# Format: <type>/<short-description>
feat/task-sharing
fix/login-redirect-loop
refactor/extract-validation-middleware
docs/api-authentication-guide
chore/upgrade-to-next-15

# With issue reference when applicable
feat/234-task-priority-levels
fix/189-expired-token-handling
```

### Branch Lifecycle

```
main (or master)
├── Always deployable
├── Protected: no direct commits
└── Merge only via PR with review

develop (if using gitflow)
├── Integration branch
├── Feature branches merge here first
└── Periodic release to main

feature/name
├── Branch from: main (or develop)
├── Merge to: main (or develop)
├── Lifetime: duration of the feature
└── Delete after merge
```

### When to Create a Branch

```
Always branch for:
- New features (no matter how small)
- Bug fixes (even one-liners)
- Refactoring
- Documentation updates

Direct commit to main only:
- Emergency hotfixes (then backport)
- Repository initialization
- Single-developer projects with no CI
```

## Atomic Commits

Each commit should represent one logical change:

```
Good: 3 commits
├── feat(tasks): add priority field to task model
├── feat(api): expose priority in task endpoints
└── feat(ui): add priority selector to task form

Bad: 1 commit
└── add task priority feature + fix validation bug + update README + bump deps
```

**Why atomic commits matter:**
- Easy to revert a specific change without reverting unrelated work
- Easier to understand in `git log` and `git blame`
- `git bisect` works correctly to find regression-introducing commits
- Pull request reviews are clearer

### Staging Partial Changes

Use `code_execution_tool` for precise staging:

```bash
# Stage specific files
git add src/components/TaskForm.tsx src/api/tasks.ts

# Interactive staging (choose which hunks to include)
git add -p src/components/TaskForm.tsx

# Check what you're about to commit
git diff --staged

# Amend the last commit (before pushing)
git commit --amend --no-edit  # Add staged changes
git commit --amend -m "new message"  # Fix the message
```

## Pull Request Quality

### PR Size

```
Target: < 400 lines changed
Acceptable: 400–800 lines
Needs splitting: > 800 lines

Large PRs:
- Take longer to review
- Get less careful review
- Are harder to test
- Are harder to revert
```

### PR Description Template

```markdown
## What

Add priority levels (low/medium/high) to tasks. Users can set priority
when creating or editing a task, and filter the task list by priority.

## Why

Addresses #234. Users need to distinguish urgent tasks from low-priority
backlog items without manual workarounds like title prefixes.

## How

- Added `priority` enum to the task schema
- Extended the POST/PATCH /api/tasks endpoints
- Added priority selector to TaskForm component
- Added priority filter to TaskList

## Testing

- [ ] Unit tests for priority validation
- [ ] API tests for priority in request/response
- [ ] Manual: create task with each priority level
- [ ] Manual: filter tasks by priority

## Screenshots (if UI changes)

[Before/after screenshots if applicable]

## Checklist

- [ ] Tests pass
- [ ] No console errors
- [ ] Documentation updated (if applicable)
```

## Semantic Versioning

### The Rules

```
Format: MAJOR.MINOR.PATCH  (e.g., 2.4.1)

PATCH (2.4.1 → 2.4.2)
  → Bug fixes, no API change
  → "It was broken, now it's fixed"

MINOR (2.4.1 → 2.5.0)
  → New features, backward compatible
  → "New stuff, nothing old broke"

MAJOR (2.4.1 → 3.0.0)
  → Breaking changes
  → "Old code won't work without changes"
```

### Pre-release and Build Metadata

```bash
1.0.0-alpha.1    # Alpha — unstable, internal only
1.0.0-beta.2     # Beta — feature complete, testing
1.0.0-rc.1       # Release candidate — ready for final testing
1.0.0            # Stable release
```

### Version Bump Workflow

```bash
# Using npm/standard-version
npm run release          # Auto-bump based on commit types
npm run release -- --patch  # Force patch bump
npm run release -- --minor  # Force minor bump
npm run release -- --major  # Force major bump

# Manual
npm version patch  # Bumps package.json + creates git tag
npm version minor
npm version major

# What it does:
# 1. Updates package.json version
# 2. Commits: "chore(release): 2.5.0"
# 3. Tags: git tag v2.5.0
```

## Useful Git Commands for Common Scenarios

```bash
# Undo the last commit (keep changes staged)
git reset --soft HEAD~1

# Undo the last commit (discard changes)
git reset --hard HEAD~1

# Remove a file from staging
git restore --staged src/file.ts

# Stash work in progress
git stash push -m "WIP: task priority feature"
git stash pop

# Cherry-pick a commit from another branch
git cherry-pick abc123

# Find which commit introduced a bug
git bisect start
git bisect bad HEAD
git bisect good v2.3.0
# ... git bisect good/bad after each checkout

# See history for a specific file
git log --follow --oneline src/api/tasks.ts

# See who changed a specific line
git blame src/api/tasks.ts -L 45,60
```

Run all git commands via `code_execution_tool`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll clean up the commits before merging" | Squashing loses valuable context. Atomic commits from the start are better. |
| "The commit message doesn't matter" | git blame and git log are daily tools for debugging. Bad messages mean lost context. |
| "One big commit is easier" | One big commit is easier to write and harder for everyone else forever after. |
| "I'll branch after I start" | Branch first, then code. Retroactively creating branches is awkward and error-prone. |
| "We don't need versioning for an internal tool" | Versioning communicates stability and enables safe dependency pinning for all consumers. |

## Red Flags

- Commits with messages like "fix", "update", "WIP", or "changes"
- Committing directly to main/master for new features
- PRs with 1000+ lines changed
- No tests in a PR that adds features
- Multiple unrelated changes in a single commit
- Force-pushing to shared branches

## Verification

Before opening a PR:

- [ ] All commits follow Conventional Commits format
- [ ] Branch name follows `<type>/<description>` convention
- [ ] PR is < 400 lines changed (or has a justification for being larger)
- [ ] PR description explains what, why, and how
- [ ] All tests pass via `code_execution_tool`
- [ ] No unintended files staged (check with `git status`)
- [ ] No debug code or `console.log` left in commits
