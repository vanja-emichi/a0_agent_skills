# revolve/projects/a0-agent-skills/revisions/rev-003/promotion/AGENTS.md

## Purpose

Promotion records for rev-003.

## Status Snapshot

- Pilot external promotion: completed (5 skills)
- Full-scale external promotion: completed (24 skills)
- Rollback available: `promotion/pre-promotion-backup/`

## Promotion Records

### Promotion 001: `cp-001-merged` (internal + pilot external)

| Field | Value |
|---|---|
| **Promoted checkpoint** | `cp-001-merged` (branch-g-merged) |
| **Previous incumbent** | `cp-000-rev003-baseline` |
| **Evidence** | Content depth 5.71→6.25 (+13 total); regression 161/161 pass (live-overlay); restoration verified |
| **Tradeoffs** | 5 pilot skills improved; 19 skills remain at baseline scores for future scaling |
| **Affected files** | 5 SKILL.md files (api-and-interface-design, browser-testing-with-devtools, ci-cd-and-automation, debugging-and-error-recovery, using-agent-skills) |
| **Verification** | Live-overlay regression guard at real plugin path; content-only hash restoration check passed |
| **Rollback path** | `promotion/pre-promotion-backup/` |
| **Promotion type** | Internal + external (pilot) |

### Promotion 002: Full-scale external promotion (all 24 skills)

| Field | Value |
|---|---|
| **Promoted checkpoint** | Live plugin (all 24 skills externally promoted) |
| **Previous state** | 5 pilot skills promoted; 19 skills at baseline |
| **Evidence** | Content depth 5.71→7.54 (+44 total, +1.83 avg); regression 161/161 pass |
| **Affected files** | 24 SKILL.md files — all skills received Project Context + Parallel Work and Delegation sections |
| **Verification** | Full-scale regression guard on live plugin: 161 passed, 0 failed |
| **Rollback path** | `promotion/pre-promotion-backup/` (pilot) + `checkpoints/cp-000-rev003-baseline/` (full) |
| **Promotion type** | External (full-scale) |
| **Remaining minor gaps** | 7 skills: scanner regex false negative; 4 skills: missing `## Files` section |
