---
name: dox-project-context
description: Applies DOX AGENTS.md project contracts before and after project work. Use when editing, planning, testing, reviewing, documenting, or shipping files in a repository that has AGENTS.md instructions.
---

# DOX Project Context

## Overview

DOX is an `AGENTS.md` hierarchy that gives agents precise local project contracts. Agent Zero injects the active project's root `AGENTS.md`, but child `AGENTS.md` files are not automatically loaded. This skill makes the DOX walk explicit before project work and the DOX closeout explicit after meaningful changes.

## When to Use

Use this skill when:

- editing, creating, deleting, moving, or reviewing project files
- writing specs, plans, tasks, docs, or ADRs that change durable project behavior
- implementing code, tests, plugin behavior, commands, skills, agents, or hooks
- delegating project review to subordinate agents
- shipping work where local contracts, verification, or ownership may matter

Do not use this skill for simple Q&A that does not inspect or modify project artifacts.

## Core Process

### 1. DOX preflight

1. Identify the active project root.
2. Read the root `AGENTS.md`.
3. Identify every file or folder you expect to touch.
4. For each target path, walk from the project root to that path.
5. Read every `AGENTS.md` found along the route.
6. Use the nearest `AGENTS.md` as the local contract, with parent contracts still binding.
7. If two contracts conflict, follow the closer contract for local details, but do not weaken parent DOX requirements.

Use `text_editor` for targeted file reads, or `code_execution_tool` with Linux commands such as `find`, `sed`, and `grep` for concise discovery.

### 2. Work under the local contract

Before changing files, state the relevant contracts you will follow when the task is non-trivial. During work:

- keep edits inside the requested scope
- preserve ownership and workflow boundaries
- follow local verification requirements
- avoid stale or contradictory documentation
- update durable docs when behavior, structure, responsibilities, outputs, or verification change

### 3. DOX closeout

After meaningful edits:

1. Re-check changed paths against the DOX chain.
2. Update the nearest owning `AGENTS.md` if contracts changed.
3. Refresh affected Child DOX Indexes.
4. Remove stale or contradictory instructions.
5. Run relevant verification.
6. Report docs intentionally left unchanged and why.

## Techniques/Patterns

### Target-path walk

For a target such as `skills/example/SKILL.md`, read:

1. `AGENTS.md` at the project root
2. `skills/AGENTS.md` if it exists
3. `skills/example/AGENTS.md` if it exists

The closest file owns local details.

### Lifecycle integration

- `spec` captures durable boundaries that may later become DOX contracts.
- `plan` maps tasks to touched DOX scopes.
- `tasks/todo.md` is the DOX-governed task ledger.
- `build` reads the chain before each edit and closes out after each completed task.
- `test` uses the nearest `AGENTS.md` Verification section.
- `review` checks DOX compliance.
- `ship` checks DOX readiness.

### Subordinate handoff

When calling `call_subordinate`, include either:

- the relevant DOX contract excerpts, or
- an instruction to read the applicable `AGENTS.md` chain before analysis.

Subordinates should report DOX gaps separately from domain findings.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Root AGENTS.md is already loaded, so I'm done." | A0 loads root instructions only; child `AGENTS.md` files must be read manually. |
| "This is a small edit, so docs don't matter." | Small edits can still change durable contracts or invalidate local instructions. |
| "The tests passed, so closeout is complete." | Verification is required, but DOX closeout also checks contracts, indexes, and stale docs. |
| "The subordinate can infer the project rules." | Subordinates do not automatically receive the main agent's loaded skills or all local DOX context. |

## Red Flags

- You are about to edit files without knowing the nearest `AGENTS.md` contract.
- A plan touches multiple directories but names no local contracts.
- A review omits whether docs or Child DOX Indexes changed.
- A shipped change updates workflows or artifacts without updating DOX.
- A subordinate is asked to review project files without DOX context.

## Verification

Before claiming done, verify:

- applicable root and child `AGENTS.md` files were read in the current session
- changed files comply with the nearest local contract
- any changed structure, workflow, ownership, outputs, or verification is reflected in DOX docs
- affected Child DOX Indexes are current
- relevant tests or validators passed
- final response names any DOX docs intentionally left unchanged

Files (use `skills_tool` action=`read_file` to open):
/a0/usr/plugins/a0_agent_skills/skills/dox-project-context/
├── SKILL.md
├── AGENTS.template.md
└── dox-checklist.md
