# revolve/projects/a0-agent-skills/revisions/rev-007/checkpoints/cp-a001-references-port/AGENTS.md

## Checkpoint ID

cp-a001-references-port

## Parent

cp-000-baseline (live plugin pre-rev-007)

## Branch

branch-a-references-porting

## Storage

Live plugin at `/a0/usr/plugins/a0_agent_skills/`. Changes applied directly (lean revision).

## Restore Method

Revert: remove `observability-checklist.md`, revert `security-checklist.md` to 134-line version, restore 4 deleted e2e test files, remove runtime_integration markers from 4 test files, revert SHARED_REFERENCES to 5-item set.

## Changes

1. **Ported** `observability-checklist.md` (91 lines) — copied from upstream, canonical reference for observability-and-instrumentation skill
2. **Enriched** `security-checklist.md` (134→179 lines) — added Threat Modeling, SSRF check, Supply-chain hygiene, AI/LLM Security, OWASP Top 10 for LLMs sections
3. **E2e test cleanup**: deleted 4 deterministic e2e files (command_execution, command_rendering, extensions, skill_loading), cleaned 2 files of structural methods (reference_access, extension_behavior)
4. **Test marker fix**: added runtime_integration marker to 4 test files for clean venv separation
5. **Updated** SHARED_REFERENCES in test_structure.py to include observability-checklist.md

## Rationale

Completes upstream references classification. Hooks already fully ported as Python extensions. All 6 reference files now present. E2e cleanup removes ~500 lines of deterministic cruft testing things through LLM sessions unnecessarily.

## Results

- Structural: 34 passed, 10 skipped
- Runtime: 164 passed
- E2E: 51 collected (down from ~80+)
- All acceptance gates passed

## Status

promoted
