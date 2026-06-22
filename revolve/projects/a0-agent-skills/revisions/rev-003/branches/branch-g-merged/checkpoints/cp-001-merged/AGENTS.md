# checkpoints/cp-001-merged/AGENTS.md

## Checkpoint ID

`cp-001-merged`

## Parent

`cp-000-rev003-baseline`

## Branch

`branch-g-merged`

## Storage

`branches/branch-g-merged/checkpoints/cp-001-merged/plugin/skills/` (5 pilot skill folders)

## Restore Method

Copy the 5 pilot skill folders from this checkpoint into `/a0/usr/plugins/a0_agent_skills/skills/` for evaluation.

## Changes

Merged candidate combining:
- **Branch F gains** — `parallel` + `call_subordinate` guidance (domain-specific, specialist profiles, centralized coordination)
- **Branch E gains** — project-context awareness (active project directory, `.a0proj/`, project `AGENTS.md`, context preservation)

Pilot skills affected:
- `api-and-interface-design`
- `browser-testing-with-devtools`
- `ci-cd-and-automation`
- `debugging-and-error-recovery`
- `using-agent-skills`

## Rationale

Both rev-002 seeds were complementary with zero overlap. Merging saves an evaluation cycle and produces a stronger candidate than either branch alone.

## Expected Benefit/Risk

- **Benefit:** highest content-depth score from combined gains; single evaluation cycle
- **Risk:** low — both changes are additive and touch different file sections

## Results

**Run:** `run-002-rev003-merged` (content depth, live-overlay)
- Automated content depth: 150/192 total, average 6.25/8
- Delta vs baseline: +13 total, +0.54 average

**Run:** `run-002b-rev003-merged` (regression guard, live-overlay)
- 161 passed, 10 skipped, 69 deselected, 0 failed — exit code 0
- Fully comparable at the real live plugin path

**Live plugin restoration:** verified via content-only hash comparison — all 5 skills match baseline after evaluation

## Decision

`promoted` — candidate passes both rev-003 acceptance gates:
1. Improves content-depth dimensions (project-context, parallel, call_subordinate)
2. Passes live-overlay regression guard (161/161, 0 failed)

## Status

`promoted` — new rev-003 incumbent
