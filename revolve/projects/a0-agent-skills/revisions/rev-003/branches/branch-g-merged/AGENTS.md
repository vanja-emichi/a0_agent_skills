# branches/branch-g-merged/AGENTS.md

## Branch ID

`branch-g-merged`

## Starting Checkpoint

`cp-000-rev003-baseline`

## Hypothesis

Combining the strongest content-depth improvements from rev-002 (parallel/delegation from branch-f + project-context from branch-e) into a single merged candidate will produce the highest content-depth score while passing the rev-003 live-overlay regression guard.

## Strategy

Merge rev-002 seeds `cp-001f` (parallel/delegation) and `cp-001e` (project-context) for the same 5 pilot skills. Both branches are complementary — they touch different sections of each SKILL.md file with zero overlap.

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-001-merged` | Combined parallel/delegation + project-context guidance on 5 pilot skills | promoted | `checkpoints/cp-001-merged/AGENTS.md` |

## Best Result

`cp-001-merged` — automated content depth improved from 5.71/8 to 6.25/8 overall (+13 total, +0.54 avg). Regression guard passed 161/161 with 0 failures under the live-overlay procedure.

## Status

`promoted`

## Continuation/Termination Reason

Candidate passed both rev-003 acceptance gates. Branch is promoted as the new rev-003 incumbent.

## Reusable Insights

- Merging complementary branches is safe and efficient when they touch different file sections.
- The live-overlay procedure produces fully comparable regression evidence.
- The `parallel` regex scanner (`\bparallel\b.*(?:tool|execut|run|concurrent)`) may miss some natural-language mentions — ci-cd-and-automation's parallel guidance wasn't matched despite containing the concept.
