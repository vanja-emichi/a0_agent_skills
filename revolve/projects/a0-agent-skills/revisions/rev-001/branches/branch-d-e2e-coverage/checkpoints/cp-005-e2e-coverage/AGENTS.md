# checkpoints/cp-005-e2e-coverage/AGENTS.md

## Checkpoint ID

`cp-005-e2e-coverage`

## Parent

`cp-004-e2e-harness-fix`

## Branch

`branch-d-e2e-coverage`

## Storage

Live plugin at: `/a0/usr/plugins/a0_agent_skills/tests/e2e/test_e2e_skill_coverage.py` (246 lines, 30 tests)

## Restore Method

Delete the test file to revert.

## Changes

New file: `tests/e2e/test_e2e_skill_coverage.py`
- **TestSkillLoadingCoverage**: 24 parametrized tests — loads every skill via skills_tool, verifies SKILL.md content returned
- **TestSkillDiscoveryCoverage**: 5 parametrized tests — trigger phrases resolve to correct skills
- **TestSkillLoadingNegative**: 1 test — nonexistent skill handled gracefully

Total: 30 new test cases. Closes coverage gap from 6/24 to 24/24 skills.

## Rationale

20 of 24 skills had zero e2e coverage. This parametrized test ensures every skill loads and returns content at runtime. Discovery tests verify trigger phrases work.

## Results

**Collection:** 30 tests collected successfully
**File syntax:** Valid Python (ast.parse passes)
**Runtime:** Not yet run (requires live server session)

## Status

`evaluated` — 29/30 passed live e2e. 1 discovery failure found (planning trigger gap).

## Results

**Run:** `run-008-e2e-live` (2026-06-19)
- Skill loading (Level 1): **24/24 passed** — every skill loads and returns content ✅
- Skill discovery (Level 2): **4/5 passed** — 1 failure: trigger "plan this feature" returned `deprecation-and-migration` instead of `planning-and-task-breakdown`
- Negative test: **1/1 passed** — nonexistent skill handled gracefully ✅

**Failure analysis:**
- Subject failure: `planning-and-task-breakdown` triggers don't include natural-language phrases like "plan this feature" or "create a plan". The word "planning" exists but "plan this feature" doesn't match strongly enough.
- Root cause: trigger expansion during scaling added phrases like "implementation plan" and "work breakdown" but missed user-facing phrases like "plan this feature", "create a plan", "feature plan".

**Decision:** `promising` — test suite is validated. One trigger gap found, needs fix candidate.
