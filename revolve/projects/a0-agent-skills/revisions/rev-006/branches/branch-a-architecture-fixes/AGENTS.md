# revolve/projects/a0-agent-skills/revisions/rev-006/branches/branch-a-architecture-fixes/AGENTS.md

## Branch ID

`branch-a-architecture-fixes`

## Starting Checkpoint

`cp-000-rev006-baseline`

## Hypothesis

The baseline architecture evidence revealed real integration gaps: missing source parity (web-performance-auditor, webperf), no deterministic runtime/API-first tests, and no test project context for workflow verification. Fixing these by porting missing personas/commands, creating architecture-proof tests, and recording explicit decisions will make the plugin provably native to Agent Zero.

## Strategy

1. Decide web-performance-auditor / webperf porting with explicit rationale
2. Create deterministic runtime/API-first test harness targeting `a0-skills-test` project
3. Expand architecture brief with runtime-verified evidence
4. Verify prompt inheritance, project metadata, skill discovery, and extension behavior against A0 reality

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| `cp-a001-architecture-fixes` | `cp-000-rev006-baseline` | `pending evaluation` | pending | `../../checkpoints/cp-a001-architecture-fixes/AGENTS.md` |

## Best Result

`cp-a001-architecture-fixes`: 22/22 runtime architecture, 145 structural, 12 runtime passed.

## Status

`promoted` externally and internally.

## Continuation/Termination Reason

Branch objective achieved. Fixed source parity (web-performance-auditor, webperf), created runtime architecture test harness, and documented A0 integration via test project.

## Reusable Insights

- The architecture-first protocol immediately found real gaps that content scanners missed.
- `get_plugins_list()` can return empty when cache is cold; tests should use structural existence as fallback.
- `list_skill_catalog()` returns `CatalogSkill` dataclass objects with `.name` attribute.
- Separate test projects with `agent_skills_enabled: true` are the correct way to test auto-load behavior.
