# branches/branch-f-parallel-delegation/AGENTS.md

## Branch ID

`branch-f-parallel-delegation`

## Starting Checkpoint

Pending creation of `cp-000-rev003-baseline`.

## Hypothesis

The rev-002 `parallel` + `call_subordinate` content additions are the strongest content-depth improvement so far and will remain valid once rerun under a comparable live-overlay regression procedure.

## Strategy

Carry forward rev-002 seed `cp-001f` as historical evidence, create an official rev-003 checkpoint from it, and rerun it first under the new revision.

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| _(pending)_ | Import rev-002 `cp-001f` into rev-003 after baseline creation | stale until rerun | none yet |

## Best Result

Historical only: rev-002 `cp-001f` scored 6.08/8 average (+9 total), but it is not directly comparable until rerun under rev-003.

## Status

`stale until rerun`

## Continuation/Termination Reason

Carry-forward seed from rev-002. This is the first branch to rerun once the rev-003 live-overlay regression procedure is established.

## Reusable Insights

- Domain-specific `parallel` and `call_subordinate` guidance produced the largest pilot-batch score lift.
- Use concrete specialist profiles and keep main-agent coordination explicit.
