# branches/branch-a-correctness/AGENTS.md

## Branch ID

`branch-a-correctness`

## Starting Checkpoint

`cp-000-baseline`

## Hypothesis

Fixing introduced correctness errors ("Steps 4-10" factual error, eval mutation check copy-paste) will improve integration quality without regressions.

## Strategy

Conservative: target factual correctness bugs introduced during adaptation from reference.

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-001a` | Fixed "Steps 4-10" → "Steps 4-6" in debugging skill; fixed eval mutation check copy-paste error | pending evaluation | `checkpoints/cp-001a/AGENTS.md` |

## Best Result

`cp-001a`: 161/161 tests pass, tool=1.0, xref=1.0. Zero regressions.

## Status

`promising` — candidate ready for promotion. Branch has no further work planned for this round.

## Continuation/Termination Reason

Hypothesis confirmed: correctness errors fixed with zero regressions. Branch complete for pilot round.

## Reusable Insights

- Introduced correctness errors (like "Steps 4-10") are a real adaptation risk — more careful diff review needed when adapting reference content.
- Eval mutation checks need self-consistency validation.
