# docs/

## Core Contract

- This AGENTS.md is the binding work contract for the `docs/` subtree
- All documentation artifacts must stay understandable from this doc plus the parent root AGENTS.md
- No content in this subtree may weaken the contracts in the parent root AGENTS.md

## Read Before Editing

1. Read the parent root `AGENTS.md` first
2. Read this `docs/AGENTS.md` before creating or modifying any document
3. Read the target subdir's AGENTS.md if one exists
4. Read the target document before editing
5. Re-read every session — do not rely on memory

## Update After Editing

- Update this doc when: adding/removing doc categories, changing naming conventions or status workflows
- Update subdir AGENTS.md when: subdir-specific contracts change
- Update parent root AGENTS.md when: doc structure affects entry points or architecture docs

## Purpose

Project documentation for a0_agent_skills — architecture decisions, feature specifications, implementation plans, analysis reports, ideas, and intent definitions. Documents follow the spec-driven-development lifecycle: idea → spec → plan → build → verify → report.

**Owns:** All documentation artifacts, naming conventions, status workflows, doc lifecycle.

**Does NOT own:** Production code, test code, prompt templates.

## Child DOX Index

Before creating or modifying any document, read the target subdirectory's AGENTS.md first to understand local patterns and invariants.

| Child | AGENTS.md | Purpose |
|-------|-----------|---------|
| **Specs** | `specs/AGENTS.md` | Feature specifications (DEFINE phase output) |
| **Plans** | `plans/AGENTS.md` | Implementation plans (PLAN phase output) |
| **ADRs** | `adrs/AGENTS.md` | Architecture Decision Records |
| **Reports** | `reports/AGENTS.md` | Analysis reports, audits, research |
| **Reviews** | *(no AGENTS.md)* | Code review and security audit output from REVIEW/SHIP phases |
| **Ideas** | *(no AGENTS.md)* | Raw ideas and early-stage proposals |
| **Intent** | *(no AGENTS.md)* | Intent definitions for features/commands |
| **Root files** | *(no AGENTS.md)* | `hook-alignment.md`, `managed-fork-surface-mapping.md` — fork maintenance references |

## Naming Conventions

- Specs: `<slug>-spec.md` (e.g., `skill-enforcement-gate-spec.md`)
- Plans: `<slug>-plan.md` (e.g., `durable-workflow-state-plan.md`)
- ADRs: `NNN-<slug>.md` with zero-padded sequence number
- Reports: `<slug>.md` (e.g., `plugin-analysis.md`)
- Slugs are lowercase, hyphenated, descriptive

## Status Workflow

Docs follow the 6-phase lifecycle status progression:

1. **Draft** — Being written, not yet reviewed
2. **Awaiting review** — Complete, pending review before next phase
3. **Active** — Approved, guiding current work
4. **Shipped** — Implementation complete, doc is historical record
5. **Superseded** — Replaced by a newer version

## Style

- Concise, operational — no diary entries
- Status and date in header metadata
- Cross-reference related specs/plans/ADRs when applicable
- Use absolute paths for cross-references

## Closeout Protocol

1. Verify doc status field is current
2. Cross-reference related docs are still accurate
3. Update this doc if new directories or categories are added
4. Update subdir AGENTS.md if subdir contracts changed

## Anti-patterns

- Do NOT create docs without following naming conventions
- Do NOT change doc status without verifying implementation state
- Do NOT duplicate content that belongs in code comments or AGENTS.md files
- Do NOT re-propose SHIPPED specs — create new specs instead

## Related Context

- **Plugin root:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
- **Children:** `adrs/AGENTS.md`, `specs/AGENTS.md`, `plans/AGENTS.md`, `reports/AGENTS.md`
