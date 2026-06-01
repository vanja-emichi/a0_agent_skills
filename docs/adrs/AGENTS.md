# docs/adrs/

## Core Contract

- This AGENTS.md is the binding work contract for the `docs/adrs/` subtree
- All ADRs must stay understandable from this doc plus `docs/AGENTS.md` and the parent root AGENTS.md
- No content in this subtree may weaken the contracts in parent AGENTS.md files

## Read Before Editing

1. Read the parent root `AGENTS.md` and `docs/AGENTS.md` first
2. Read this `adrs/AGENTS.md` before creating or modifying any ADR
3. Read `README.md` for the current ADR index
4. Read the target ADR before editing
5. Re-read every session — do not rely on memory

## Update After Editing

- Update `README.md` index table when: adding, superseding, or changing ADR status
- Update this doc when: changing ADR conventions or format requirements
- Update `docs/AGENTS.md` when: doc-level naming conventions change

## Purpose

Architecture Decision Records for the a0_agent_skills plugin. Each ADR captures a significant architectural decision, its context, rationale, and consequences.

**Owns:** ADR documents (001–NNN) and the README index.

**Does NOT own:** Implementation code, specs, or plans that result from decisions.

## ADR Format

Every ADR must include these sections:

```markdown
# ADR-NNN: <Title>

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded

## Context
<What is the issue that we're seeing that is motivating this decision?>

## Decision
<What is the change that we're proposing/making?>

## Consequences
<What becomes easier or harder because of this change?>
```

Optional sections: `Alternatives Considered`, `References`.

## Current ADRs

| ADR | Title | Status |
|-----|-------|--------|
| 001 | Skill Enforcement Gate Design | Accepted |
| 002 | Durable Workflow State via File System | Accepted |
| 003 | Phase-Aware Governance Model | Accepted |
| 004 | Skill Contracts via YAML Frontmatter | Accepted |
| 005 | Importlib-based Module Loading | Accepted |
| 006 | Enforcement Strict Mode Decision | Deferred |
| 007 | Artifact Path Resolution with No-Project Fallback | Accepted |
| 008 | Artifact Path Wiring — Merge Semantics and Display Resolution | Accepted |
| 009 | Approval Gate System — From Dead Code to Enforced Lifecycle Gates | Accepted |

## Conventions

- Sequence numbers are zero-padded 3 digits (`001`, `002`, ...)
- File naming: `NNN-<slug>.md` (lowercase, hyphenated)
- Status values: `Proposed`, `Accepted`, `Deprecated`, `Superseded`, `Deferred`
- Superseded ADRs link to their replacement: `Superseded by ADR-NNN`
- New ADRs take the next number in sequence — never reuse or renumber

## Style

- Concise, operational — no diary entries
- Focus on context → decision → consequences
- Alternatives section records rejected options with rationale

## Closeout Protocol

1. Verify ADR status matches actual implementation state
2. Update `README.md` index table with any new or changed ADRs
3. Cross-reference related specs and plans if decision affects them
4. Never delete ADRs — only deprecate or supersede

## Anti-patterns

- Do NOT skip sections in the ADR format
- Do NOT renumber existing ADRs
- Do NOT delete ADRs — use `Deprecated` or `Superseded` status
- Do NOT write ADRs for trivial decisions — reserve for architectural choices
- Do NOT update an accepted ADR's decision section — create a new ADR instead

## Related Context

- **Parent:** `/a0/usr/projects/a0_agent_skills/docs/AGENTS.md`
- **Related specs:** `/a0/usr/projects/a0_agent_skills/docs/specs/AGENTS.md`
- **Related plans:** `/a0/usr/projects/a0_agent_skills/docs/plans/AGENTS.md`
- **Plugin root:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
