# revolve/projects/a0-agent-skills/revisions/rev-006/branches/branch-b-deeper-architecture/AGENTS.md

## Branch ID

`branch-b-deeper-architecture`

## Starting Checkpoint

`cp-a001-architecture-fixes`

## Hypothesis

Branch-a proved plugin discovery, skills catalog, profiles, commands, project metadata, extension hooks, and source parity via deterministic runtime tests. Remaining architecture proof needed: prompt inheritance precedence (profile → default → plugin → core), workflow artifact lifecycle behavior, and API endpoint discovery for a future layer-4 harness.

## Strategy

1. Add prompt inheritance tests: verify plugin profile prompts override default, default prompts exist, and plugin prompts don't accidentally override core agent0 behavior
2. Add workflow artifact tests: verify tasks/spec.md, tasks/plan.md, tasks/todo.md paths are referenced and consistent across commands and skills
3. Add API endpoint inventory: verify plugin exposes 0 API endpoints (intentional), document that future API tests require plugin to add endpoints
4. Expand architecture brief in revision doc with these findings

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| none yet | — | — | — | create candidate |

## Best Result

`cp-b001-deeper-architecture`: 37/37 runtime architecture tests passed across 12 test classes.

## Status

`promoted` externally and internally.

## Continuation/Termination Reason

Branch objective achieved. Added prompt inheritance, API surface, skills injection mechanism, and workflow artifact lifecycle tests. All deeper architecture semantics now proven deterministically.

## Reusable Insights

- Plugin prompts are correctly scoped to profiles only — no global overrides.
- `prompts/` dir exists but is empty, which is harmless.
- A0 prompt resolution uses `subagents.get_paths()` with priority: project → usr/agents → plugin agents → agents → usr → plugins → default.
- Core `_skills` plugin injection (via `system_prompt` hook) and plugin auto-load (via `message_loop_start`) are separate mechanisms that do not conflict.
- The 0 API endpoint design is intentional — all plugin behavior is through extensions, skills, and commands.
