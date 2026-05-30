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

Git is your safety net. Treat commits as save points, branches as sandboxes, and history as documentation. With AI agents generating code at high speed, disciplined version control is the mechanism that keeps changes manageable, reviewable, and reversible.

## When to Use

Always. Every code change flows through git.

- Writing commit messages
- Creating feature branches
- Preparing pull requests for review
- Planning a release or version bump
- Reviewing git history to understand context

## Core Principles

### Trunk-Based Development (Recommended)

Keep `main` always deployable. Work in short-lived feature branches that merge back within 1-3 days. Long-lived development branches are hidden costs — they diverge, create merge conflicts, and delay integration. DORA research consistently shows trunk-based development correlates with high-performing engineering teams.

```
main ──●──●──●──●──●──●──●──●──●──  (always deployable)
        ╲      ╱  ╲    ╱
         ●──●─╱    ●──╱    ← short-lived feature branches (1-3 days)
```

This is the recommended default. Teams using gitflow or long-lived branches can adapt the principles (atomic commits, small changes, descriptive messages) to their branching model — the commit discipline matters more than the specific branching strategy.

- **Dev branches are costs.** Every day a branch lives, it accumulates merge risk.
- **Release branches are acceptable.** When you need to stabilize a release while main moves forward.
- **Feature flags > long branches.** Prefer deploying incomplete work behind flags rather than keeping it on a branch for weeks.

### 1. Commit Early, Commit Often

Each successful increment gets its own commit. Don't accumulate large uncommitted changes.

```
Work pattern:
  Implement slice → Test → Verify → Commit → Next slice

Not this:
  Implement everything → Hope it works → Giant commit
```

Commits are save points. If the next change breaks something, you can revert to the last known-good state instantly.

### 2. Atomic Commits

Each commit does one logical thing:

```
# Good: Each commit is self-contained
git log --oneline
a1b2c3d Add task creation endpoint with validation
d4e5f6g Add task creation form component
h7i8j9k Connect form to API and add loading state
m1n2o3p Add task creation tests (unit + integration)

# Bad: Everything mixed together
git log --oneline
x1y2z3a Add task feature, fix sidebar, update deps, refactor utils
```

**Why atomic commits matter:**
- Easy to revert a specific change without reverting unrelated work
- Easier to understand in `git log` and `git blame`
- `git bisect` works correctly to find regression-introducing commits
- Pull request reviews are clearer

### 3. Descriptive Messages

Commit messages explain the *why*, not just the *what*:

```
# Good: Explains intent
feat: add email validation to registration endpoint

Prevents invalid email formats from reaching the database.
Uses Zod schema validation at the route handler level,
consistent with existing validation patterns in auth.ts.

# Bad: Describes what's obvious from the diff
update auth.ts
```

**Format:**
```
<type>: <short description>

<optional body explaining why, not what>
```

**Types:**

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring (no feature, no bug fix) |
| `test` | Adding or fixing tests |
| `docs` | Documentation changes only |
| `chore` | Build process, dependencies, tooling |
| `style` | Formatting, whitespace (no logic change) |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration changes |

**Breaking changes:**
```bash
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

### 4. Keep Concerns Separate

Don't combine formatting changes with behavior changes. Don't combine refactors with features. Each type of change should be a separate commit — and ideally a separate PR:

```bash
# Good: Separate concerns
git commit -m "refactor: extract validation logic to shared utility"
git commit -m "feat: add phone number validation to registration"

# Bad: Mixed concerns
git commit -m "refactor validation and add phone number field"
```

**Separate refactoring from feature work.** A refactoring change and a feature change are two different changes — submit them separately. This makes each change easier to review, revert, and understand in history. Small cleanups (renaming a variable) can be included in a feature commit at reviewer discretion.

### 5. Size Your Changes

Target ~100 lines per commit/PR. Changes over ~1000 lines should be split. See the splitting strategies in `code-review-and-quality` for how to break down large changes.

```
~100 lines  → Easy to review, easy to revert
~300 lines  → Acceptable for a single logical change
~1000 lines → Split into smaller changes
```

## Branching Strategy

### Feature Branches

```
main (always deployable)
  │
  ├── feature/task-creation    ← One feature per branch
  ├── feature/user-settings    ← Parallel work
  └── fix/duplicate-tasks      ← Bug fixes
```

- Branch from `main` (or the team's default branch)
- Keep branches short-lived (merge within 1-3 days) — long-lived branches are hidden costs
- Delete branches after merge
- Prefer feature flags over long-lived branches for incomplete features

### Branch Naming

```bash
# Format: <type>/<short-description>
feature/task-sharing
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

## Working with Worktrees

For parallel AI agent work, use git worktrees to run multiple branches simultaneously:

```bash
# Create a worktree for a feature branch
git worktree add ../project-feature-a feature/task-creation
git worktree add ../project-feature-b feature/user-settings

# Each worktree is a separate directory with its own branch
# Agents can work in parallel without interfering
ls ../
  project/              ← main branch
  project-feature-a/    ← task-creation branch
  project-feature-b/    ← user-settings branch

# When done, merge and clean up
git worktree remove ../project-feature-a
```

Benefits:
- Multiple agents can work on different features simultaneously
- No branch switching needed (each directory has its own branch)
- If one experiment fails, delete the worktree — nothing is lost
- Changes are isolated until explicitly merged

## The Save Point Pattern

```
Agent starts work
    │
    ├── Makes a change
    │   ├── Test passes? → Commit → Continue
    │   └── Test fails? → Revert to last commit → Investigate
    │
    ├── Makes another change
    │   ├── Test passes? → Commit → Continue
    │   └── Test fails? → Revert to last commit → Investigate
    │
    └── Feature complete → All commits form a clean history
```

This pattern means you never lose more than one increment of work. If an agent goes off the rails, `git reset --hard HEAD` takes you back to the last successful state.

## Change Summaries

After any modification, provide a structured summary. This makes review easier, documents scope discipline, and surfaces unintended changes:

```
CHANGES MADE:
- src/routes/tasks.ts: Added validation middleware to POST endpoint
- src/lib/validation.ts: Added TaskCreateSchema using Zod

THINGS I DIDN'T TOUCH (intentionally):
- src/routes/auth.ts: Has similar validation gap but out of scope
- src/middleware/error.ts: Error format could be improved (separate task)

POTENTIAL CONCERNS:
- The Zod schema is strict — rejects extra fields. Confirm this is desired.
- Added zod as a dependency (72KB gzipped) — already in package.json
```

This pattern catches wrong assumptions early and gives reviewers a clear map of the change. The "DIDN'T TOUCH" section is especially important — it shows you exercised scope discipline and didn't go on an unsolicited renovation.

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

## Pre-Commit Hygiene

Before every commit:

```bash
# 1. Check what you're about to commit
git diff --staged

# 2. Ensure no secrets
git diff --staged | grep -i "password\|secret\|api_key\|token"

# 3. Run tests
npm test

# 4. Run linting
npm run lint

# 5. Run type checking
npx tsc --noEmit
```

Automate this with git hooks:

```json
// package.json (using lint-staged + husky)
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

## Handling Generated Files

- **Commit generated files** only if the project expects them (e.g., `package-lock.json`, Prisma migrations)
- **Don't commit** build output (`dist/`, `.next/`), environment files (`.env`), or IDE config (`.vscode/settings.json` unless shared)
- **Have a `.gitignore`** that covers: `node_modules/`, `dist/`, `.env`, `.env.local`, `*.pem`

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

## Using Git for Debugging

```bash
# Find which commit introduced a bug
git bisect start
git bisect bad HEAD
git bisect good <known-good-commit>
# Git checkouts midpoints; run your test at each to narrow down

# View what changed recently
git log --oneline -20
git diff HEAD~5..HEAD -- src/

# Find who last changed a specific line
git blame src/services/task.ts

# Search commit messages for a keyword
git log --grep="validation" --oneline

# See history for a specific file
git log --follow --oneline src/api/tasks.ts

# See who changed a specific line
git blame src/api/tasks.ts -L 45,60
```

Run all git commands via `code_execution_tool`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll commit when the feature is done" | One giant commit is impossible to review, debug, or revert. Commit each slice. |
| "The message doesn't matter" | Messages are documentation. Future you (and future agents) will need to understand what changed and why. |
| "I'll squash it all later" | Squashing destroys the development narrative. Prefer clean incremental commits from the start. |
| "Branches add overhead" | Short-lived branches are free and prevent conflicting work from colliding. Long-lived branches are the problem — merge within 1-3 days. |
| "I'll split this change later" | Large changes are harder to review, riskier to deploy, and harder to revert. Split before submitting, not after. |
| "I don't need a .gitignore" | Until `.env` with production secrets gets committed. Set it up immediately. |

## Red Flags

- Commits with messages like "fix", "update", "WIP", or "changes"
- Committing directly to main/master for new features
- Large uncommitted changes accumulating
- No `.gitignore` in the project
- Committing `node_modules/`, `.env`, or build artifacts
- PRs with 1000+ lines changed
- No tests in a PR that adds features
- Multiple unrelated changes in a single commit
- Long-lived branches that diverge significantly from main
- Force-pushing to shared branches

## Verification

Before opening a PR:

- [ ] Commit does one logical thing
- [ ] All commits follow Conventional Commits format
- [ ] Message explains the why, follows type conventions
- [ ] Tests pass before committing via `code_execution_tool`
- [ ] No secrets in the diff
- [ ] No formatting-only changes mixed with behavior changes
- [ ] Branch name follows `<type>/<description>` convention
- [ ] PR is < 400 lines changed (or has a justification for being larger)
- [ ] PR description explains what, why, and how
- [ ] `.gitignore` covers standard exclusions
- [ ] No debug code or `console.log` left in commits
