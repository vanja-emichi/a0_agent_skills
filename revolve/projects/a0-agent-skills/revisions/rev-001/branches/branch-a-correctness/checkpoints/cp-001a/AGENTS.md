# checkpoints/cp-001a/AGENTS.md

## Checkpoint ID

`cp-001a`

## Parent

`cp-000-baseline`

## Branch

`branch-a-correctness`

## Storage

`branches/branch-a-correctness/checkpoints/cp-001a/plugin/skills/` (6 files: 3 SKILL.md + 3 evals.json)

## Restore Method

Copy the 3 skill dirs from this checkpoint to `/a0/usr/plugins/a0_agent_skills/skills/`

## Changes

1. `debugging-and-error-recovery/SKILL.md`: Fixed "Steps 4-10" → "Steps 4-6" (correctness: triage has 6 steps)
2. `debugging-and-error-recovery/evals/evals.json`: Fixed `_mutation_check` for `dbg-intermittent-500` (was copy-pasted from second eval)

## Rationale

These are introduced correctness errors. The "Steps 4-10" reference points to non-existent steps in a 6-step checklist. The mutation check describes breaking the wrong eval.

## Expected Benefit/Risk

- **Benefit:** Correct factual content; eval mutation checks are self-consistent
- **Risk:** None — text-only correctness fix, no structural changes

## Status

`promising` — passed evaluation with zero regressions. Candidate for internal promotion.

## Results

**Run:** `run-002-cp-001a` (2026-06-19)
- pytest: 161 passed, 10 skipped, 41 deselected, 0 failed
- Tool name nativity: PASS (1.0)
- Cross references: PASS (1.0)

**Decision:** `promising` — fixes critical correctness errors with zero regressions. Ready for internal promotion.
