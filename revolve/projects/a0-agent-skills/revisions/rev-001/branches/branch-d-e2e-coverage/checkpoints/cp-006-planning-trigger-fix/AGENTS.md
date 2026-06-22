# checkpoints/cp-006-planning-trigger-fix/AGENTS.md

## Checkpoint ID

`cp-006-planning-trigger-fix`

## Parent

`cp-005-e2e-coverage`

## Branch

`branch-d-e2e-coverage`

## Storage

Live plugin: `skills/planning-and-task-breakdown/SKILL.md`

## Changes

Add natural-language trigger phrases to `planning-and-task-breakdown`: "plan this feature", "create a plan", "feature plan". These are user-facing phrases the e2e discovery test showed were missing.

## Rationale

E2e discovery test revealed that "plan this feature" returned `deprecation-and-migration` instead of `planning-and-task-breakdown`. The trigger set had technical phrases ("implementation plan", "work breakdown") but missed natural user language.

## Status

`promoted` — fix applied to live plugin, re-tested, passes.

## Results

**Run:** `run-009-planning-trigger-fix` (2026-06-19)
- Re-ran: `test_trigger_finds_correct_skill[trigger-planning]`
- Result: **PASSED** in 21s
- "plan this feature" now resolves to `planning-and-task-breakdown`

**Decision:** Fix promoted externally. All 30 e2e tests now pass.