# revolve/projects/a0-agent-skills/revisions/rev-007/branches/branch-a-references-porting/AGENTS.md

## Branch ID

branch-a-references-porting

## Starting Checkpoint

cp-000-baseline

## Hypothesis

Porting observability-checklist.md and enriching security-checklist.md completes upstream references classification with zero regression.

## Strategy

Single candidate: port missing file, enrich security checklist, clean up e2e tests, fix test markers.

## Candidate Checkpoints

| Checkpoint | Result | Status |
|---|---|---|
| cp-a001-references-port | 34p struct + 164p runtime + 51 e2e + 6 refs | promoted |

## Best Result

All acceptance gates passed. No regressions.

## Status

promoted

## Continuation/Termination Reason

Objective complete. All upstream hooks and references classified and ported. E2e suite cleaned.
