# revolve/projects/a0-agent-skills/revisions/rev-005/branches/branch-a-harness-truth/AGENTS.md — Harness Truth Branch

## Branch ID

`branch-a-harness-truth`

## Starting Checkpoint

`cp-live-20260620-0129`

## Hypothesis

The main rev-005 gate failures are shallow but important truth/alignment issues: stale docs, missing eval framework claim, incomplete e2e command coverage, an obvious e2e variable bug, and one invalid JSON tool example. Fixing these without changing evaluation semantics should make the plugin pass rev-005 gate checks and provide a cleaner basis for deeper semantic alignment.

## Strategy

Make minimal focused edits in a local candidate copy only, then verify with static runtime-alignment, structural pytest, and runtime-integration pytest.

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| `cp-a001-harness-truth` | `cp-live-20260620-0129` | promoted internally | static 0 failures; structural 145 passed; runtime 16 passed | `../../checkpoints/cp-a001-harness-truth/AGENTS.md` |

## Best Result

`cp-a001-harness-truth` is the rev-005 current best:

- `run-002`: gate_passed=true; gate_failures=0; advisory_failures=0
- `run-004`: 145 passed, 10 skipped, 85 deselected
- `run-003`: 16 passed, 224 deselected; live restore verified

## Status

`promoted` internally and externally.

## Continuation/Termination Reason

Branch objective achieved. It fixed the concrete baseline failure cluster and established a stricter runtime-alignment harness. Further work should not continue this branch with cosmetic mutations; it should either continue from `cp-a001-harness-truth` in a deeper semantic/e2e branch if desired.

## Reusable Insights

- Scanner-perfect content coverage can hide stale docs and false harness claims.
- Runtime-integration tests are path-bound to the installed plugin; local checkpoint copies require live-overlay evaluation for comparable runtime proof.
- Eval fixture claims must distinguish JSON fixture existence from executable runner evidence.

## External Promotion

`external-promotion-001-cp-a001` applied this branch's best checkpoint to the live plugin and passed post-promotion verification.
