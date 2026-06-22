# branches/branch-e-project-context/AGENTS.md

## Branch ID

`branch-e-project-context`

## Starting Checkpoint

`cp-000-rev002-baseline`

## Hypothesis

Adding explicit A0 project-context guidance (`.a0proj/`, active project directory, project path awareness) to representative weak skills will materially improve rev-002 content-depth scores without risking rev-001 regressions.

## Strategy

Pilot 5 representative weak skills across different domains:
- `api-and-interface-design`
- `browser-testing-with-devtools`
- `ci-cd-and-automation`
- `debugging-and-error-recovery`
- `using-agent-skills`

## Candidate Checkpoints

| Checkpoint | Changes | Status | Detail |
|---|---|---|---|
| `cp-001e` | Add project-context awareness to 5 pilot skills | promising | `checkpoints/cp-001e/AGENTS.md` |

## Best Result

`cp-001e` — automated content depth improved from 5.71/8 to 5.88/8 overall (+4 total, +0.17 avg). Four pilot skills gained `project_context_aware` coverage with no subject regressions observed.

## Status

`promising`

## Continuation/Termination Reason

Promising but not yet promotable. The candidate improved the largest systematic gap, but regression verification on checkpoint clones is blocked by a path-bound lifecycle-hook harness assertion that expects the live plugin path.

## Reusable Insights

- Short `Project Context` sections can add meaningful A0-project grounding without heavy rewrites.
- The most natural signals are: active project directory, project-relative paths, project `AGENTS.md`, `.a0proj/` boundaries, and context preservation across tool sessions.
- `using-agent-skills` already partially satisfied project-context awareness before this branch, so broad gaps may hide skill-level variation.
