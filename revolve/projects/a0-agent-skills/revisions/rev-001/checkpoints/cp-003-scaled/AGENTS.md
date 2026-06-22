# checkpoints/cp-003-scaled/AGENTS.md

## Checkpoint ID

`cp-003-scaled`

## Parent

`cp-002-merged` (3 pilot skills merged)

## Branch

Scaled promotion — all branches merged + applied to all 24 skills

## Storage

Live plugin at: `/a0/usr/plugins/a0_agent_skills/` (24 skills, all scaled)

## Restore Method

Rollback to baseline: `cp -r checkpoints/cp-000-baseline/plugin/* /a0/usr/plugins/a0_agent_skills/`

## Changes

### All 24 Skills (scaled from pilot patterns)
- Expanded triggers across all skills
- Added `**Related:**` sections with proper `skills_tool` syntax
- Added `## Files` sections
- Fixed bare-text cross-references
- Added A0-native concepts (`parallel`, `call_subordinate`, `browser`)

### New Skill
- Ported `observability-and-instrumentation` from reference repo with full A0 adaptation

### Infrastructure
- Updated `plugin.yaml` skill count: 23 → 24
- Updated `test_structure.py` expected count: 23 → 24
- Updated `AGENTS.md` skill inventory

## Rationale

Scale proven pilot patterns to all skills + port the one missing skill. The pilot batch validated that all fix categories are safe and additive.

## Results

**Run:** `run-005-scaled-verification` (2026-06-19)
- Structural + Runtime tests: 161 passed, 10 skipped, 41 deselected, 0 failed
- Tool name nativity: 24/24 passed (1.0)
- Cross references: 24/24 passed (1.0)

## Status

`promoted` — externally promoted to live plugin. Current incumbent.
