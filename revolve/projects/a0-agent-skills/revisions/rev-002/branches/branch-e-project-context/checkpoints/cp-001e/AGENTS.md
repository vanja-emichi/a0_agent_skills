# checkpoints/cp-001e/AGENTS.md

## Checkpoint ID

`cp-001e`

## Parent

`cp-000-rev002-baseline`

## Branch

`branch-e-project-context`

## Storage

`branches/branch-e-project-context/checkpoints/cp-001e/plugin/skills/` (5 pilot skill folders)

## Restore Method

Copy the 5 pilot skill folders from this checkpoint into `/a0/usr/plugins/a0_agent_skills/skills/` for evaluation.

## Changes

Added explicit project-context guidance to 5 pilot skills:
- `api-and-interface-design` — active project directory, project-relative contracts/schemas, project `AGENTS.md`, `.a0proj/`, context preservation
- `browser-testing-with-devtools` — project-relative artifacts, project test conventions, dev server alignment, `.a0proj/` boundaries
- `ci-cd-and-automation` — project-relative pipeline files, project CI/CD conventions, `.a0proj/` boundaries, context preservation
- `debugging-and-error-recovery` — project-relative source/log/config paths, project constraints and prior debugging notes, `.a0proj/` boundaries
- `using-agent-skills` — project context awareness, project-relative file operations, project `AGENTS.md`, `.a0proj/` boundaries

## Rationale

`project_context_aware` is the largest baseline gap (20/24 missing), so it is the highest-priority content-depth branch.

## Expected Benefit/Risk

- **Benefit:** raises the largest systematic rev-002 gap with low structural risk
- **Risk:** low — additive guidance only

## Results

**Run:** `run-002-branch-e-project-context`
- Automated content depth: 141/192 total, average 5.88/8
- Delta vs baseline: +4 total, +0.17 average
- Improved pilot skills:
  - `api-and-interface-design`: 5 → 6 (`project_context_aware`)
  - `browser-testing-with-devtools`: 5 → 6 (`project_context_aware`)
  - `ci-cd-and-automation`: 5 → 6 (`project_context_aware`)
  - `debugging-and-error-recovery`: 5 → 6 (`project_context_aware`)
- Manual review: additions are natural, project-specific, and grounded in active-project workflow
- Regression clone run: 159 passed, 10 skipped, 69 deselected, 2 failed
- Failure class: harness/comparability issue, not subject regression

**Run:** `run-002b-branch-e-project-context`
- Comparable-layout regression rerun: 160 passed, 10 skipped, 69 deselected, 1 failed
- Remaining failure: `test_plugin_helpers_resolve_plugin_and_route_lifecycle_hooks`
- Interpretation: path-bound live-plugin assertion prevents checkpoint-clone comparability even when skill content is unchanged

## Decision

`promising` — improves the largest baseline gap with low-risk additive guidance, but not promotable yet because regression evidence is blocked by a harness-comparability issue.

## Status

`promising`
