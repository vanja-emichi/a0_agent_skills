# docs/plans/

## Core Contract

- This AGENTS.md is the binding work contract for the `docs/plans/` subtree
- All plans must stay understandable from this doc plus `docs/AGENTS.md` and the parent root AGENTS.md
- No content in this subtree may weaken the contracts in parent AGENTS.md files

## Read Before Editing

1. Read the parent root `AGENTS.md` and `docs/AGENTS.md` first
2. Read this `plans/AGENTS.md` before creating or modifying any plan
3. Read the target plan and its corresponding spec before editing
4. Re-read every session — do not rely on memory

## Update After Editing

- Update this doc when: adding/removing plans, changing plan conventions
- Update `docs/AGENTS.md` when: doc-level naming conventions change
- Update related specs when: plan scope diverges from spec

## Purpose

Implementation plans produced during the PLAN phase of the 6-phase lifecycle. Each plan breaks a spec into ordered, testable implementation increments with architecture decisions and task decomposition.

**Owns:** Plan documents, task breakdowns, implementation ordering.

**Does NOT own:** Specs (DEFINE phase), implementation code (BUILD phase), or test results (VERIFY phase).

## Plan Format

Plans follow the `planning-and-task-breakdown` skill output conventions:

```markdown
# Implementation Plan: <Title>

> Generated from spec `docs/specs/<slug>-spec.md`.
> **Status in broader roadmap:** Cross-reference if applicable.

## Overview
## Architecture Decisions
## Implementation Steps (ordered, testable)
## Testing Strategy
## Risks and Mitigations
```

## Status Values

| Status | Meaning |
|--------|----------|
| Draft | Being written, not yet reviewed |
| Awaiting review | Complete, pending review |
| Active | Approved, guiding BUILD phase |
| Shipped | Implementation complete — historical reference |
| Superseded | Replaced by newer plan |

## Current Plans

| Plan | Source Spec | Status |
|------|-----------|--------|
| `a0-agent-skills-workflow-governance-plan` | `a0-agent-skills-workflow-governance-spec` | Active |
| `skill-enforcement-gate-plan` | `skill-enforcement-gate-spec` | Shipped |
| `durable-workflow-state-plan` | `durable-workflow-state-spec` | Shipped |
| `phase-aware-governance-plan` | `phase-aware-governance-spec` | Shipped |
| `skill-activation-evals-and-dependencies-plan` | `skill-activation-evals-spec` | Active |
| `skill-registry-strengthening-plan` | `skill-registry-strengthening-spec` | Active |
| `managed-fork-alignment-plan` | `managed-fork-alignment-spec` | Active |
| `enforcement-settings-verification-plan` | `enforcement-settings-verification-spec` | Active |
| `artifact-path-wiring-fix-plan` | `artifact-path-wiring-fix-spec` | Active |
| `markdown-artifact-and-state-alignment-plan` | `markdown-artifact-and-state-alignment-spec` | Active |
| `live-harness-persistence-enforce-plan` | `live-harness-persistence-enforce-spec` | Active |
| `approval-gate-wiring-plan` | `approval-gate-wiring-spec` | Shipped |

## Conventions

- File naming: `<slug>-plan.md` matching the corresponding `<slug>-spec.md`
- Every plan must reference its source spec
- Implementation steps are ordered, testable, and atomic
- Umbrella roadmap plans link to sub-slice plans
- Plans link to task lists in `tasks/` directory

## Style

- Concise, operational — no diary entries
- Steps are actionable, not aspirational
- Architecture decisions reference ADRs when applicable

## Closeout Protocol

1. Verify plan status matches implementation state
2. Ensure task list in `tasks/` is aligned with plan steps
3. Update this doc index if plans are added/removed/retired
4. Never re-propose a SHIPPED plan — create a new one

## Anti-patterns

- Do NOT create plans without a corresponding spec
- Do NOT re-propose SHIPPED plans — check status field first
- Do NOT skip architecture decisions in the plan
- Do NOT create implementation steps without testable outcomes
- Do NOT diverge plan scope from spec scope without updating the spec

## Related Context

- **Parent:** `/a0/usr/projects/a0_agent_skills/docs/AGENTS.md`
- **Specs:** `/a0/usr/projects/a0_agent_skills/docs/specs/AGENTS.md`
- **ADRs:** `/a0/usr/projects/a0_agent_skills/docs/adrs/AGENTS.md`
- **Plugin root:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
