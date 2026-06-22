# revolve/projects/a0-agent-skills/revisions/rev-006/checkpoints/cp-b001-deeper-architecture/AGENTS.md

## Checkpoint ID

`cp-b001-deeper-architecture`

## Parent

`cp-a001-architecture-fixes`

## Branch

`branch-b-deeper-architecture`

## Storage

Lean checkpoint: incremental additions to test_runtime_architecture.py from cp-a001.

## Changes (applied)

1. Added TestPromptInheritance (3 tests): verifies no global prompt overrides, profiles only override specifics, no agent0 targeting
2. Added TestAPISurface (2 tests): verifies 0 API endpoints (intentional), 8+ extension files
3. Added TestSkillsInjectionMechanism (4 tests): verifies SKILL.md format, frontmatter, auto-load separation from core _skills, activate_on_skill_load extension
4. Added TestWorkflowArtifactLifecycle (6 tests): verifies spec/plan/build commands reference artifacts, skills exist

## Rationale

Branch-a proved discovery and parity. Branch-b proves deeper integration semantics: prompt precedence, workflow paths, and API surface decisions.

## Results

- `run-005`: runtime architecture v2 — 37/37 passed (15 new tests added from branch-a's 22)

Architecture evidence summary:
- Prompt inheritance: profiles only override `specifics.md`, no global overrides, no agent0 targeting
- API surface: 0 API endpoints (intentional), all behavior via extensions
- Skills injection: correct SKILL.md format, auto-load separate from core _skills plugin
- Workflow lifecycle: all spec/plan/build commands and skills exist and reference correct artifacts

## Status

`promoted` externally and internally. All 37 runtime architecture tests pass.

## Rollback Note

Incremental test additions only. Revert by restoring test_runtime_architecture.py from cp-a001 state.
