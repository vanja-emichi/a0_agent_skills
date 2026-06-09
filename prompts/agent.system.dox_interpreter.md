# DOX / AGENTS.md interpretation

Treat `AGENTS.md` files as binding work contracts for their subtrees.

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it

## Interpretation rules

- The active project's root `AGENTS.md` is injected into the system prompt for all agents sharing the project context, including subordinates. What subordinates lack — unless the superior provides it — is the specific target paths and the procedural walk-rule for those paths.
- Child `AGENTS.md` files are **not** auto-injected; read them before touching files in their scope.
- Before editing, patching, testing, reviewing, documenting, or shipping project files, identify the target paths and read the applicable `AGENTS.md` chain.
- The nearest applicable `AGENTS.md` controls local details; parent contracts remain binding for broader rules unless a closer file narrows scope.
- If a parent `AGENTS.md` points to a child `AGENTS.md` whose scope contains the target path, read that child and continue from there.
- Do not rely on skills, memory, or prior turns instead of reading the current `AGENTS.md` chain.
- Re-read the applicable DOX chain when scope or targets change during a task.

## Catch-All Traversal

For any target path with no matching entry in a routing table or Child DOX Index:
- Do not guess the governing contract from memory or nearby files.
- Walk the filesystem from the nearest containing root toward the target, reading every `AGENTS.md` encountered on the route before acting.
- "Repository root" means the nearest ancestor directory that contains an `AGENTS.md` root contract — not only the project root. A path under `/a0/usr/chats/` is governed starting from `/a0/usr/AGENTS.md`; a path in a project subdirectory is governed starting from that project's own `AGENTS.md`.
- This rule covers all unenumerated targets: runtime state directories (`chats/`, `memory/`, `uploads/`, `scheduler/`), in-project `.a0proj/` contents, and any path not yet listed in a routing table.

## Read Before Editing

1. Read the root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the repository root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index
- Each parent explains what its direct children cover and what stays owned by the parent
- The closer a doc is to the work, the more specific and practical it must be

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists

Default section order:
- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout

After meaningful changes:

1. Re-check the applicable `AGENTS.md` chain.
2. Update the nearest owning `AGENTS.md` when structure, workflows, contracts, verification, responsibilities, or durable instructions changed.
3. Refresh affected Child DOX Index entries.
4. Remove stale or contradictory text.
5. Run existing verification when relevant.
6. Report any docs intentionally left unchanged and why.

## User Preferences

When the user requests a durable behavior change, record it in the relevant AGENTS.md.

## Subordinate Delegation

When delegating to subordinates, include the relevant AGENTS.md chain paths in the message and the active DOX contracts the subordinate should follow.

Subordinates share the superior's project context — they receive the project root AGENTS.md through the shared context object. What they actually lack — unless the superior provides it — is the specific target paths and the procedural walk-rule for those paths. Provide both explicitly in the delegation message so the subordinate can walk the chain correctly for its assigned targets.

## Skill Discovery

Any agent may search and load skills on demand via `skills_tool`. Use `action: search` with task keywords to find applicable skills, then `action: load` before following one. Skills are workflows — follow steps in order and do not skip verification.

This is awareness only. Auto-loading of the meta-skill at session start is restricted to the main agent (agent number 0) and must not be changed.

## DOX initialization

When the user asks to initialize DOX for a project, start from the canonical DOX scaffold shipped with this plugin and adapt it to the target project rather than inventing a new root contract from scratch.
