# branches/branch-b-structural/AGENTS.md

## Branch ID

`branch-b-structural`

## Starting Checkpoint

`cp-000-baseline`

## Hypothesis

Adding missing structural elements (Related sections, file listings, expanded triggers, proper cross-ref syntax) will improve structural completeness and skill discoverability without regressions.

## Strategy

Moderate: fill structural gaps that affect consistency and discoverability.

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-001b` | Added Related sections to debugging + git; added file listings to debugging + git; expanded triggers for all 3 skills; converted bare-text ref to skills_tool syntax | pending evaluation | `checkpoints/cp-001b/AGENTS.md` |

## Best Result

`cp-001b`: 161/161 tests pass, tool=1.0, xref=1.0. Zero regressions.

## Status

`promising` — candidate ready for promotion. Branch has no further work planned for this round.

## Continuation/Termination Reason

Hypothesis confirmed: structural additions (Related sections, triggers, file listings) are safe and additive.

## Reusable Insights

- Related sections and file listings should be standardized across all skills in future rounds.
- Trigger expansion is safe and low-risk.
- Cross-reference syntax conversion (bare-text → skills_tool) is a real integration gap.
