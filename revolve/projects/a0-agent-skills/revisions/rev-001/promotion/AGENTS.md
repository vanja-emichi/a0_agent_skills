# promotion/AGENTS.md

## Purpose

Records of internal and external promotions for revision rev-001.

## Promotion Records

### Promotion 001: cp-002-merged (Internal + External)

- **Date:** 2026-06-19
- **Promoted checkpoint:** `cp-002-merged` (3 pilot skills merged from branches A+B+C)
- **Previous incumbent:** `cp-000-baseline`
- **Evidence:** 161/161 tests pass, tool=1.0, xref=1.0, zero regressions across all 3 branches
- **Affected files:**
  - `skills/test-driven-development/SKILL.md` — triggers, Related, parallel tool, verification
  - `skills/debugging-and-error-recovery/SKILL.md` — Steps 4-6 fix, Related, Files, browser tool, multi-component debugging, triggers
  - `skills/debugging-and-error-recovery/evals/evals.json` — mutation check fix
  - `skills/git-workflow-and-versioning/SKILL.md` — Related, Files, triggers, worktree+parallel, bare-ref fix
- **Rollback path:** `checkpoints/cp-000-baseline/plugin/` → copy to live plugin
- **Promotion type:** Internal (incumbent update) + External (live plugin applied)

### Promotion 002: cp-003-scaled (External — full 24-skill scaling)

- **Date:** 2026-06-19
- **Promoted checkpoint:** `cp-003-scaled` (all 24 skills with scaled integration improvements)
- **Previous incumbent:** `cp-002-merged` (3 skills only)
- **Evidence:** 161/161 tests pass, tool=1.0, xref=1.0, zero regressions on full 24-skill plugin
- **Affected files:**
  - ALL 24 skills: triggers expanded, Related sections, Files sections, bare-ref fixes, A0-native concepts
  - `skills/observability-and-instrumentation/SKILL.md` + `evals/evals.json` — NEW skill ported
  - `plugin.yaml` — skill count 23 → 24
  - `tests/test_structure.py` — expected count 23 → 24
  - `AGENTS.md` — skill inventory updated
- **Rollback path:** `checkpoints/cp-000-baseline/plugin/` → copy to live plugin
- **Promotion type:** External (live plugin applied at scale)
