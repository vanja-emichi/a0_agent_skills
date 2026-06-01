# docs/reports/

## Core Contract

- This AGENTS.md is the binding work contract for the `docs/reports/` subtree
- All reports must stay understandable from this doc plus `docs/AGENTS.md` and the parent root AGENTS.md
- No content in this subtree may weaken the contracts in parent AGENTS.md files

## Read Before Editing

1. Read the parent root `AGENTS.md` and `docs/AGENTS.md` first
2. Read this `reports/AGENTS.md` before creating or modifying any report
3. Read the target report before editing
4. Re-read every session — do not rely on memory

## Update After Editing

- Update this doc when: adding/removing report categories, changing report conventions
- Update `docs/AGENTS.md` when: doc-level naming conventions change

## Purpose

Analysis reports, audits, and research documents produced during REVIEW, VERIFY, and ad-hoc analysis phases. Reports capture findings, recommendations, bug analyses, and comparative studies.

**Owns:** Report documents, findings, recommendations, audit results.

**Does NOT own:** Specs, plans, ADRs, or implementation code.

## Report Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **Audit** | Comprehensive code/plugin analysis | `plugin-analysis.md`, `implementation-audit.md`, `agents-best-practices-audit.md` |
| **Bug Analysis** | Root cause and fix documentation | `agent-ship-phase-routing-bugs.md`, `framework-settings-ui-bug.md` |
| **Review** | Multi-perspective review output | `parallel-review-full.md` |
| **Research** | Question-driven investigation | `research-questions-q1-q7.md` |

## Current Reports

| Report | Type | Date |
|--------|------|------|
| `plugin-analysis.md` | Audit | 2026-05-31 |
| `implementation-audit.md` | Audit | — |
| `agents-best-practices-audit.md` | Audit | — |
| `agent-ship-phase-routing-bugs.md` | Bug Analysis | — |
| `framework-settings-ui-bug.md` | Bug Analysis | — |
| `parallel-review-full.md` | Review | — |
| `research-questions-q1-q7.md` | Research | — |
| `approval-gate-verification.md` | Review | 2026-06-02 |
| `approval-gate-acceptance.md` | Review | 2026-06-02 |
| `classifier-tuning.md` | Research | 2026-06-02 |
| `skill-checkpoint-gate-analysis.md` | Research | 2026-06-02 |

## Report Format

Reports should include:

```markdown
# <Title>

**Date:** YYYY-MM-DD | **Type:** Audit | Bug | Review | Research

## Summary / Table of Contents
## Findings
## Recommendations
## References
```

## Conventions

- File naming: `<slug>.md` (lowercase, hyphenated)
- Audit reports include date and analyst attribution
- Bug reports include root cause, impact, and fix recommendation
- Review reports use structured finding format (Critical/Important/Suggestion)
- Research reports are question-driven with evidence-based answers
- Reports are historical records — do not delete, supersede with newer reports

## Style

- Concise, operational — no diary entries
- Findings are evidence-based with file/line references
- Recommendations are actionable

## Closeout Protocol

1. Verify report findings are still accurate
2. Update this doc index if new reports are added
3. Cross-reference related specs/plans if findings affect them
4. Archive rather than delete outdated reports

## Anti-patterns

- Do NOT delete reports — they are historical records
- Do NOT create reports without actionable findings
- Do NOT duplicate information that belongs in specs or ADRs
- Do NOT modify report findings after the fact — add corrigendum notes instead

## Related Context

- **Parent:** `/a0/usr/projects/a0_agent_skills/docs/AGENTS.md`
- **Specs:** `/a0/usr/projects/a0_agent_skills/docs/specs/AGENTS.md`
- **ADRs:** `/a0/usr/projects/a0_agent_skills/docs/adrs/AGENTS.md`
- **Plugin root:** `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
