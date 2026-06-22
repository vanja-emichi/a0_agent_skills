# checkpoints/cp-000-rev002-baseline/AGENTS.md

## Checkpoint ID

`cp-000-rev002-baseline`

## Parent

Live incumbent carried forward from `rev-001` closeout.

## Branch

Baseline — no branch yet.

## Storage

`checkpoints/cp-000-rev002-baseline/plugin/skills/` (24 skill folders, 58 files)

## Restore Method

```bash
cp -r checkpoints/cp-000-rev002-baseline/plugin/skills/* /a0/usr/plugins/a0_agent_skills/skills/
```

## Identity Verification

58 files in the checkpoint snapshot.

## Changes

None — this is the rev-002 starting incumbent: post rev-001 scaling, post e2e harness repair, post e2e coverage additions, and post planning trigger fix.

## Rationale

Preserve the current all-green live plugin as the rev-002 baseline before content-depth improvements.

## Results

**Run:** `run-001-rev002-baseline` (2026-06-20)
- Automated content depth: 137/192 total, average 5.71/8
- Regression guard: 161 passed, 10 skipped, 0 failed
- E2e carry-forward from rev-001: 30/30 pass

**Systematic gaps:**
- `project_context_aware`: 20/24 missing
- `parallel_tool_mentioned`: 14/24 missing
- `call_subordinate_mentioned`: 13/24 missing

## Status

`baseline` — incumbent checkpoint for rev-002.
