# checkpoints/cp-001f/AGENTS.md

## Checkpoint ID

`cp-001f`

## Parent

`cp-000-rev002-baseline`

## Branch

`branch-f-parallel-delegation`

## Storage

`branches/branch-f-parallel-delegation/checkpoints/cp-001f/plugin/skills/` (5 pilot skill folders)

## Restore Method

Copy the 5 pilot skill folders from this checkpoint into `/a0/usr/plugins/a0_agent_skills/skills/` for evaluation.

## Changes

Added explicit `parallel` and `call_subordinate` guidance to 5 pilot skills:
- `api-and-interface-design` — parallel verification streams and specialist review (`code-reviewer`, `security-auditor`)
- `browser-testing-with-devtools` — parallel visual/network/console/accessibility checks and delegated test-plan design (`test-engineer`)
- `ci-cd-and-automation` — parallel pipeline tasks, delegated security/test stages, parallel CI failure triage
- `debugging-and-error-recovery` — parallel diagnostic paths, delegated security/test analysis, centralized fix ownership
- `using-agent-skills` — parallel skill discovery, delegated specialist skill execution, centralized skill sequencing

## Rationale

`parallel_tool_mentioned` and `call_subordinate_mentioned` are the second and third largest baseline gaps and together represent the main A0-native content deficit.

## Expected Benefit/Risk

- **Benefit:** improves A0-native concept coverage and deepens adaptation quality
- **Risk:** low to moderate — new examples and workflow guidance must remain natural

## Results

**Run:** `run-003-branch-f-parallel-delegation`
- Automated content depth: 146/192 total, average 6.08/8
- Delta vs baseline: +9 total, +0.37 average
- Improved pilot skills:
  - `api-and-interface-design`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
  - `browser-testing-with-devtools`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
  - `ci-cd-and-automation`: 5 → 6 (`call_subordinate_mentioned`)
  - `debugging-and-error-recovery`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
  - `using-agent-skills`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
- Manual review: additions are domain-specific, use real A0 profiles, and keep main-agent coordination explicit
- Regression clone run: 159 passed, 10 skipped, 69 deselected, 2 failed
- Failure class: harness/comparability issue, not subject regression

**Run:** `run-003b-branch-f-parallel-delegation`
- Comparable-layout regression rerun: 160 passed, 10 skipped, 69 deselected, 1 failed
- Remaining failure: `test_plugin_helpers_resolve_plugin_and_route_lifecycle_hooks`
- Interpretation: path-bound live-plugin assertion prevents checkpoint-clone comparability even when skill content is unchanged

## Decision

`promising` — strongest automated candidate in the pilot batch, but not promotable yet because regression evidence is blocked by a harness-comparability issue.

## Status

`promising`
