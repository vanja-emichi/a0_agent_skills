# a0_agent_skills (project)

## Core Contract

- This AGENTS.md is the binding work contract for the entire `a0_agent_skills` project
- It connects the development workspace (this folder) to the runtime plugin (installed at `/a0/usr/plugins/a0_agent_skills/`)
- All work products, source materials, instructions, records, and durable docs must stay understandable from this doc plus the nearest applicable child AGENTS.md
- No child doc may weaken the contracts in this root doc

## Read Before Editing

1. Read this root AGENTS.md first
2. Identify every file or folder you expect to touch
3. Walk from the project root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for project-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken this root contract

Do not rely on memory. Re-read the applicable AGENTS.md chain in the current session before editing.

## Update After Editing

Every meaningful change requires an AGENTS.md pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the AGENTS.md pass still must happen.

## Child DOX Index

Before modifying code or docs in a subdirectory, read its AGENTS.md first to understand local patterns and invariants.

| Child | AGENTS.md Path | Scope |
|-------|---------------|-------|
| **Documentation** | `docs/AGENTS.md` | Specs, plans, ADRs, reports, ideas, intent — full doc lifecycle |
| **Specs** | `docs/specs/AGENTS.md` | Feature specifications (DEFINE phase output) |
| **Plans** | `docs/plans/AGENTS.md` | Implementation plans (PLAN phase output) |
| **ADRs** | `docs/adrs/AGENTS.md` | Architecture Decision Records |
| **Reports** | `docs/reports/AGENTS.md` | Analysis reports, audits, research |
| **Tasks** | *(todo files, no AGENTS.md)* | Task tracking and progress |
| **Comparison** | *(reference repos, no AGENTS.md)* | Upstream and DOX reference clones |
| **Tests** | `tests/` *(no AGENTS.md)* | Live harness tests |
| **Plugin** | `/a0/usr/plugins/a0_agent_skills/AGENTS.md` | Installed plugin — the runtime target of all this work |

## Purpose

This project is the **development workspace** for the `a0_agent_skills` Agent Zero plugin. It contains the engineering artifacts (specs, plans, ADRs, reports, tasks) that drive the plugin's evolution, plus reference clones of the upstream `agent-skills` and the `dox` framework.

**Owns:** Documentation artifacts, task tracking, reference clones, live tests, project-level governance.

**Does NOT own:** Runtime plugin code (lives in `/a0/usr/plugins/a0_agent_skills/`), Agent Zero framework internals, downstream user code.

## Project ↔ Plugin Relationship

| Aspect | Project (this folder) | Plugin (`/a0/usr/plugins/a0_agent_skills/`) |
|--------|----------------------|--------------------------------------------|
| **Role** | Development workspace | Runtime deployment |
| **Audience** | Developers, AI agents editing docs | Agent Zero at runtime |
| **Lifecycle** | Ephemeral, under active development | Stable, versioned, distributed |
| **Content** | Specs, plans, ADRs, reports, tasks | Code, tests, skills, agents, commands, prompts |
| **AGENTS.md** | This doc + docs/ subdirs | 8 AGENTS.md files (fully DOX-initialized) |

**Key flows:**
- A **spec** is written here → approved → a **plan** is created → **tasks** track progress → **code changes** are made in the plugin → **ADRs** document decisions → **reports** capture results
- The plugin's own AGENTS.md files document the runtime architecture and contracts
- Both sides must stay in sync via the closeout protocol

## Entry Points

| File/Folder | Role |
|------------|------|
| `docs/` | All documentation artifacts (see Child DOX Index) |
| `tasks/` | Todo files tracking active work |
| `comparison/official_agent_skills/` | Upstream reference clone |
| `comparison/dox/` | DOX framework reference clone |
| `tests/` | Live harness integration tests |
| `.a0proj/` | Agent Zero project metadata, state, memory |
| `CHANGELOG.md` | Project-level changelog |
| `/a0/usr/plugins/a0_agent_skills/` | The runtime plugin this project builds |

## Workflow

1. **Define** — Write a spec in `docs/specs/<slug>-spec.md`
2. **Plan** — Break work into tasks in `docs/plans/<slug>-plan.md` and `tasks/<slug>-todo.md`
3. **Build** — Implement in the plugin (`/a0/usr/plugins/a0_agent_skills/`)
4. **Verify** — Run tests, capture evidence
5. **Review** — Use the code-reviewer profile, document decisions in `docs/adrs/`
6. **Ship** — Update plugin, update this project's `CHANGELOG.md`

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout Protocol

1. Re-check changed paths against the AGENTS.md chain
2. Update nearest owning AGENTS.md and any affected parents or children
3. Refresh the Child DOX Index if structure changed
4. Remove stale or contradictory text
5. Run existing verification when relevant (`python -m pytest tests/ -v --tb=short` for the plugin)
6. Report any docs intentionally left unchanged and why

## Related Context

- Plugin: `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
- DOX framework: `comparison/dox/AGENTS.md`
- Upstream: `comparison/official_agent_skills/AGENTS.md`
- ADRs: `docs/adrs/AGENTS.md`
- Active workflow: `.a0proj/state/active_goal.json`
