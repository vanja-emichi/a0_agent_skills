# branches/branch-c-a0native/AGENTS.md

## Branch ID

`branch-c-a0native`

## Starting Checkpoint

`cp-000-baseline`

## Hypothesis

Adding A0-native concept references (parallel, call_subordinate, browser tool) will deepen native integration and leverage A0's unique capabilities.

## Strategy

Exploratory: add A0-native patterns that are currently absent from adapted skills.

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-001c` | Added parallel tool to TDD verification; browser tool guidance in debugging Step 2; multi-component debugging with call_subordinate; worktree + parallel + call_subordinate in git skill | pending evaluation | `checkpoints/cp-001c/AGENTS.md` |

## Best Result

`cp-001c`: 161/161 tests pass, tool=1.0, xref=1.0. Zero regressions.

## Status

`promising` — candidate ready for promotion. Branch has no further work planned for this round.

## Continuation/Termination Reason

Hypothesis confirmed: A0-native concept references (parallel, call_subordinate, browser) can be safely added without regressions.

## Reusable Insights

- `parallel` + `call_subordinate` patterns are the biggest missed A0 integration across skills.
- Worktree + parallel orchestration is a unique A0 advantage that no reference skill teaches.
- Browser tool guidance should be standard in any skill touching frontend debugging.
