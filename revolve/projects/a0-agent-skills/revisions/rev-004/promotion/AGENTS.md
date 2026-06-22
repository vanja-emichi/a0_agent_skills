# revolve/projects/a0-agent-skills/revisions/rev-004/promotion/AGENTS.md

## Purpose

Promotion records for rev-004.

## Status Snapshot

- Pilot external promotion: completed (5 skills)
- Rollback available: `promotion/pre-promotion-backup/`

## Promotion Records

### Promotion 001: `cp-001-merged` (pilot external)

| Field | Value |
|---|---|
| **Promoted checkpoint** | `cp-001-merged` (branch-k-merged) |
| **Previous state** | rev-004 baseline (8.4/12 rubric, 7.96/8 automated) |
| **Evidence** | Automated 7.96/8 (no regression); regression 161/161 pass; LLM rubric improvements: D3 (A0-specific evals added), D2 (JSON examples), D1 (memory_save fix), D4 (pytest alternatives) |
| **Affected files** | 5 SKILL.md + 5 evals.json files |
| **Verification** | Live-overlay regression guard: 161/161 pass; restoration verified |
| **Rollback path** | `promotion/pre-promotion-backup/` |
| **Promotion type** | External (pilot) |
| **Changes** | 7 new A0-specific evals, JSON tool-call examples in 4 skills, memory_save→text_editor fix, pytest alternatives in 5 skills, Python security examples in security-and-hardening |
