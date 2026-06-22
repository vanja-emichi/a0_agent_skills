# checkpoints/cp-000-rev003-baseline/AGENTS.md

## Checkpoint ID

`cp-000-rev003-baseline`

## Parent

Live plugin state carried forward from rev-002 baseline (which was carried from rev-001 closeout).

## Branch

Baseline — no branch.

## Storage

`checkpoints/cp-000-rev003-baseline/plugin/skills/` (24 skill folders)

## Restore Method

```bash
cp -r checkpoints/cp-000-rev003-baseline/plugin/skills/* /a0/usr/plugins/a0_agent_skills/skills/
```

## Identity Verification

25 entries in the checkpoint snapshot (24 skills + the parent directory entry).

## Changes

None — this is the rev-003 starting incumbent: current live plugin state as of 2026-06-20.

## Rationale

Preserve the current live plugin as the rev-003 baseline before content-depth candidate evaluation under the live-overlay procedure.

## Results

**Run:** `run-001-rev003-baseline` (2026-06-20)
- Automated content depth: 137/192 total, average 5.71/8
- Regression guard (live path): 161 passed, 10 skipped, 69 deselected, 0 failed
- Comparability: confirmed — live path has no path-bound assertion failures

**Systematic gaps:**
- `project_context_aware`: 20/24 missing
- `parallel_tool_mentioned`: 14/24 missing
- `call_subordinate_mentioned`: 13/24 missing

## Status

`baseline` — incumbent checkpoint for rev-003.
