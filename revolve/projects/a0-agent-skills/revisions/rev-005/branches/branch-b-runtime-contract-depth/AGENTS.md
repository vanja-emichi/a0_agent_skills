# revolve/projects/a0-agent-skills/revisions/rev-005/branches/branch-b-runtime-contract-depth/AGENTS.md — Runtime Contract Depth Branch

## Branch ID

`branch-b-runtime-contract-depth`

## Starting Checkpoint

`cp-a001-harness-truth`

## Hypothesis

Skills pass static truth checks but lack genuine A0 runtime-contract depth. A semantic-depth audit will identify shallow guidance and produce genuinely A0-native skill content.

## Strategy

1. ✅ Build semantic-depth harness (5 dimensions, 0-15 per skill)
2. ✅ Run baseline — avg 11.12/15 (74.2%); D1 universally weakest at 0.75/3
3. ✅ Apply D1-deepening edits to all 24 skills
4. ✅ Re-run semantic-depth + static gates + regression

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| `cp-b001-runtime-contract-depth` | `cp-a001-harness-truth` | promoted internally | semantic avg 13.29/15; D1 2.79/3; static/structural/runtime all pass | `../../checkpoints/cp-b001-runtime-contract-depth/AGENTS.md` |

## Best Result

`cp-b001-runtime-contract-depth` is the rev-005 current best:

- Semantic depth: **13.29/15 (88.6%)** — up from 11.12/15
- D1 (A0 Runtime Model): **2.79/3** — up from 0.75/3
- Static gates: passed (0 failures)
- Structural: 145 passed
- Runtime: 16 passed

## Status

`promoted` internally and externally.

## Reusable Insights

- D1 was the critical gap: skills had correct tool names but no genuine understanding of A0's runtime model
- Domain-specific runtime model sections (not boilerplate) are key — each skill explains how ITS workflow intersects with A0 internals
- D2 (non-boilerplate) and D3 (tool patterns) remained strong, confirming rev-003/rev-004 work was solid
- D4 and D5 have moderate room for improvement but are less critical now that D1 is addressed

## External Promotion

`external-promotion-002-cp-b001` applied this branch to the live plugin and passed all verification checks.
