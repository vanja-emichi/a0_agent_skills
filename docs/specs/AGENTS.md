# docs/specs/

## Core Contract

- This AGENTS.md is the binding work contract for the `docs/specs/` subtree
- All specs must stay understandable from this doc plus `docs/AGENTS.md` and the parent root AGENTS.md
- No content in this subtree may weaken the contracts in parent AGENTS.md files

## Read Before Editing

1. Read the parent root `AGENTS.md` and `docs/AGENTS.md` first
2. Read this `specs/AGENTS.md` before creating or modifying any spec
3. Read the target spec before editing
4. Re-read every session — do not rely on memory

## Update After Editing

- Update this doc when: adding/removing specs, changing spec conventions
- Update `docs/AGENTS.md` when: doc-level naming conventions change
- Update related plans when: spec scope or requirements change

## Purpose

Feature specifications produced during the DEFINE phase of the 6-phase lifecycle. Each spec defines what to build, success criteria, assumptions, and constraints before implementation begins.

**Owns:** Specification documents, acceptance criteria, scope boundaries.

**Does NOT own:** Implementation code, plans, or ADRs.

## Spec Format

Specs follow the `spec-driven-development` skill output conventions:

```markdown
# Spec: <Title>

*Phase 1 (Specify) artifact of spec-driven-development. Status: <status>*
*Source idea: <path> · Date: YYYY-MM-DD*

> **Status in broader roadmap:** Cross-reference to umbrella spec if applicable.

## Assumptions (correct before PLAN)
## Objective
## Success Criteria
## Scope
## Out of Scope
## Dependencies
```

## Status Values

Check status before proposing work on any spec:

| Status | Meaning |
|--------|----------|
| Draft | Being written, not yet reviewed |
| Awaiting review | Complete, pending review |
| Active | Approved, ready for PLAN phase |
| Shipped | Implementation complete — do NOT re-propose |
| Superseded | Replaced by newer spec |

## Current Specs

| Spec | Topic | Status |
|------|-------|--------|
| `a0-agent-skills-workflow-governance-spec` | Umbrella workflow governance roadmap | Active |
| `skill-enforcement-gate-spec` | Enforcement gate + eval harness | Shipped |
| `durable-workflow-state-spec` | Durable state persistence | Shipped |
| `phase-aware-governance-spec` | 6-phase advisory model | Shipped |
| `skill-activation-evals-spec` | Activation accuracy evaluation | Active |
| `skill-registry-strengthening-spec` | Skill registry improvements | Active |
| `managed-fork-alignment-spec` | Upstream parity alignment | Active |
| `call-subordinate-parallel-spec` | Parallel subordinate execution | Active |
| `call-subordinate-parallel-tasks` | Parallel task definitions | Active |
| `parallel-subordinate-execution` | Parallel execution design | Active |
| `enforcement-settings-verification-spec` | Enforcement settings ON/OFF verification | Active |
| `artifact-inference-fix-spec` | Artifact inference bug fix | Active |
| `artifact-path-wiring-fix-spec` | Artifact path wiring fix | Active |
| `functional-skill-dependencies-spec` | Functional skill dependency DAG | Active |
| `live-harness-persistence-enforce-spec` | Live harness persistence enforcement | Active |
| `markdown-artifact-and-state-alignment-spec` | Markdown artifact alignment | Active |
| `approval-gate-wiring-spec` | Approval gate wiring (detection, gates, mtime, enforce mode) | Shipped |

## Conventions

- File naming: `<slug>-spec.md`
- Slugs are lowercase, hyphenated, match the feature name
- Every spec cross-references its umbrella roadmap spec if it's a sub-slice
- Specs link to their corresponding plan in `docs/plans/`
- Status field is authoritative — check before proposing work

## Style

- Concise, operational — no diary entries
- Assumptions section must be correctable before PLAN phase
- Success criteria must be testable

## Closeout Protocol

1. Verify spec status matches implementation state
2. Ensure corresponding plan exists and is aligned
3. Update this doc index if specs are added/removed/retired
4. Never re-propose a SHIPPED spec — create a new one

## Anti-patterns

- Do NOT start implementation without a spec in at least `Active` status
- Do NOT re-propose SHIPPED specs — check status field first
- Do NOT skip the assumptions section — incorrect assumptions cause rework
- Do NOT modify shipped spec content — create superseding spec instead
- Do NOT create specs without testable success criteria

## Related Context

- **Parent:** `/a0/usr/projects/a0_agent_skills/docs/AGENTS.md`
- **Plans:** `/a0/usr/projects/a0_agent_skills/docs/plans/AGENTS.md`
- **ADRs:** `/a0/usr/projects/a0_agent_skills/docs/adrs/AGENTS.md`
- **Plugin root:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
