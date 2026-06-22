# revolve/projects/a0-agent-skills/revisions/rev-005/branches/branch-d-d4-d5-e2e-evalrunner/AGENTS.md — D4/D5/e2e/eval-runner Branch

## Branch ID

`branch-d-d4-d5-e2e-evalrunner`

## Starting Checkpoint

`cp-b001-runtime-contract-depth`

## Hypothesis

D4 (project context depth) and D5 (eval specificity) had moderate room for improvement. The e2e failure was a test expectation issue, not a plugin bug. Eval-runner claims needed formalization.

## Strategy

1. Deepen D4 project context in 11 weak skills with AGENTS.md chain, promptinclude persistence, and live-plugin awareness
2. Enhance D5 eval specificity in 17 weak eval fixtures with A0-runtime assertions
3. Fix e2e test to check for specific auto-load injection text
4. Formalize eval-runner status as fixture-only

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| `cp-d001-d4-d5-e2e-evalrunner` | `cp-b001-runtime-contract-depth` | promoted externally | semantic 14.54/15; D4 2.96/3; D5 2.92/3; all checks pass | `../../checkpoints/cp-d001-d4-d5-e2e-evalrunner/AGENTS.md` |

## Best Result

Semantic depth: **14.54/15 (96.9%)** — up from 13.29/15

## Status

`promoted` externally.

## Reusable Insights

- The e2e failure was a test expectation issue: the framework's `_13_skills_prompt.py` injects a universal `## skills` listing into ALL agents. The test was asking about generic 'skill discovery' rather than the specific auto-load injection text.
- D4 and D5 were addressable with targeted additions: AGENTS.md chain + cross-session + live-plugin awareness for D4; A0-runtime assertions for D5.
- Eval-runner formalization is a documentation truth issue, not a code issue.
