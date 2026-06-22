# revolve/projects/a0-agent-skills/revisions/rev-001/checkpoints/cp-000-baseline/AGENTS.md

## Checkpoint ID

`cp-000-baseline`

## Parent

Incumbent (no parent checkpoint — this is the initial baseline)

## Branch

Baseline — no branch yet.

## Storage

Local copy at: `revolve/projects/a0-agent-skills/revisions/rev-001/checkpoints/cp-000-baseline/plugin.tar.gz (compressed)`
Contains: `skills/`, `commands/`, `agents/`, `extensions/`, `plugin.yaml`, `hooks.py` (104 files)

## Restore Method

```bash
cp -r checkpoints/cp-000-baseline/plugin.tar.gz (compressed)* /a0/usr/plugins/a0_agent_skills/
```

## Identity Verification

104 files. Verify with: `find checkpoints/cp-000-baseline/plugin -type f | wc -l`

## Changes

None — this is the incumbent snapshot as of 2026-06-19. Captures the current live plugin state including known bugs (harness issues, stale tests, missing features).

## Rationale

Preserve the current plugin state as baseline for Revolve comparison. The plugin works (161 tests pass) but has known integration issues:
- 7 test harness bugs (NameErrors, missing pytestmark, stale test expectations, missing pytest in /opt/venv)
- 1 missing skill (`observability-and-instrumentation`)
- Subtle integration gaps to be discovered through systematic audit

## Expected Benefit/Risk

- **Benefit:** Rollback point and baseline for comparison
- **Risk:** None — this is a snapshot

## Status

`baseline` — incumbent. Formal baseline run complete.

## Results

**Run:** `run-001-baseline` (2026-06-19)
- Structural + Runtime tests: 161 passed, 10 skipped, 41 deselected, 0 failed
- Tool name nativity: 23/23 passed (score=1.0)
- Cross references: 23/23 passed (score=1.0)
- Dimensions 1, 4, 5: all pass (covered by existing tests)
- Dimension 6 (behavioral/e2e): not yet measured

**Decision:** Baseline established. Incumbent is strong on deterministic dimensions. Opportunities for improvement lie in: (1) e2e behavioral dimension, (2) missing skill port (`observability-and-instrumentation`), (3) deeper structural audit for subtle integration issues.

## Promotion Status

Current incumbent. No promotion action.

## Rollback Note

N/A — this is the starting point.
