# branches/branch-f-parallel-delegation/AGENTS.md

## Branch ID

`branch-f-parallel-delegation`

## Starting Checkpoint

`cp-000-rev002-baseline`

## Hypothesis

Adding explicit `parallel` and `call_subordinate` usage guidance to representative weak skills will improve A0-native concept coverage scores and deepen content adaptation.

## Strategy

Pilot the same 5 representative weak skills:
- `api-and-interface-design`
- `browser-testing-with-devtools`
- `ci-cd-and-automation`
- `debugging-and-error-recovery`
- `using-agent-skills`

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-001f` | Add explicit parallel + subordinate guidance to 5 pilot skills | promising | `checkpoints/cp-001f/AGENTS.md` |

## Best Result

`cp-001f` — automated content depth improved from 5.71/8 to 6.08/8 overall (+9 total, +0.37 avg). This is the strongest pilot candidate and improved 5 pilot skills across the two largest A0-native concept gaps.

## Status

`promising`

## Continuation/Termination Reason

Promising but not yet promotable. The candidate produced the strongest automated improvement, but checkpoint-clone regression verification is blocked by a path-bound lifecycle-hook harness assertion that expects the live plugin path.

## Reusable Insights

- Explicit `parallel` and `call_subordinate` guidance adds measurable A0-native depth quickly.
- The strongest wording is domain-specific: tie delegation to concrete specialist profiles and keep main-agent coordination centralized.
- Parallel/delegation guidance appears to yield a larger score lift than project-context guidance in the pilot batch.
