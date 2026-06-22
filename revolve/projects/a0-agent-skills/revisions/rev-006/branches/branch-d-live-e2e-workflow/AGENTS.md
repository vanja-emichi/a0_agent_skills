# revolve/projects/a0-agent-skills/revisions/rev-006/branches/branch-d-live-e2e-workflow/AGENTS.md

## Branch ID

`branch-d-live-e2e-workflow`

## Starting Checkpoint

`cp-b001-deeper-architecture`

## Hypothesis

Branch-a and branch-b proved architecture deterministically. Branch-d adds Layer 5: thin live e2e proof that verifies the spec → plan → build workflow produces real Agent Zero project artifacts in a live LLM session using the `a0-skills-test` project.

## Strategy

1. Switch active project to `a0-skills-test` for live e2e
2. Run a thin live workflow: use `/spec` or skills to produce a `tasks/spec.md` artifact
3. Verify `tasks/spec.md` is created in the test project
4. Use `/plan` to produce `tasks/plan.md` and `tasks/todo.md`
5. Verify artifacts are created and updated
6. Record evidence as Layer 5 (truly requires live LLM)

## Candidate Checkpoints

| Checkpoint | Parent | Status | Result | Detail |
|---|---|---|---|---|
| none yet | — | — | — | create candidate after branch-c |

## Best Result

`cp-d001-live-workflow`: PASSED. Agent used spec-driven-development skill in `a0-skills-test` project, created `tasks/spec.md` with problem statement, key features, and success criteria.

## Status

`promoted` — Layer 5 live evidence collected.

## Continuation/Termination Reason

Branch objective achieved. Live LLM session proved that the spec-driven-development workflow produces real project artifacts.

## Reusable Insights

- `A0E2EClient.create_and_run_task()` requires `name` parameter.
- Scheduler task with `project_name` correctly switches project context for the agent.
- `agent_skills_enabled: true` in test project is correctly read by the auto-load extension.
- Agent used the skill workflow and wrote the spec to `tasks/spec.md` as documented.
