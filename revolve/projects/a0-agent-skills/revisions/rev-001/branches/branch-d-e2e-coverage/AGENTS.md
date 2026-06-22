# branches/branch-d-e2e-coverage/AGENTS.md

## Branch ID

`branch-d-e2e-coverage`

## Starting Checkpoint

`cp-004-e2e-harness-fix`

## Hypothesis

Adding parametrized e2e tests for all 24 skills will close the coverage gap (20/24 skills have zero e2e coverage) and verify that every skill loads and behaves correctly at runtime.

## Strategy

Expand evaluation coverage: add Level 1 (loading) and Level 2 (discovery) tests.

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-005-e2e-coverage` | New parametrized e2e tests for all 24 skills + discovery test | evaluated — 29/30 pass | `checkpoints/cp-005-e2e-coverage/AGENTS.md` |
| `cp-006-planning-trigger-fix` | Added natural-language triggers to planning skill | promoted — fix verified | `checkpoints/cp-006-planning-trigger-fix/AGENTS.md` |

## Best Result

`cp-006-planning-trigger-fix`: All 30 e2e tests pass. Dimension 6 (behavioral) fully green.

## Status

`promoted` — all e2e tests pass. Branch complete.

## Continuation/Termination Reason

All evaluation dimensions measured and green. E2e coverage closed from 6/24 to 24/24. Discovery gap fixed. No further work planned for this branch.

## Reusable Insights

- Parametrized testing is the most efficient way to cover all 24 skills — one test function, 24 parameters
- Discovery testing via trigger phrases validates the skill-to-intent mapping
- The 3-layer evidence model (task state + response text + log errors) works well for skill verification
- Natural-language triggers matter as much as technical ones — "plan this feature" outranked by "planning" alone wasn't enough
