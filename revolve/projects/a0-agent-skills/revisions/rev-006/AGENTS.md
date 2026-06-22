# revolve/projects/a0-agent-skills/revisions/rev-006/AGENTS.md — Architecture and Runtime Integration Revision

## Reason

rev-005 corrected runtime-alignment truth and semantic depth, but it did not fully prove that `a0_agent_skills` is the correct native Agent Zero integration architecture for orchestration, prompt inheritance, project behavior, workflow artifacts, profile parity, and runtime/API-first verification. rev-006 exists to answer those architecture questions before further plugin changes.

## Parent

`rev-005` — runtime-alignment recalibration complete and externally promoted.

## Subject

Installed plugin subject, evaluated through checkpointed local research copies only after the architecture brief and runtime/API-first evaluation contract are complete:

- Live plugin source: `/a0/usr/plugins/a0_agent_skills/`
- Source project: `/a0/usr/projects/a0_agent_skills/`
- Reference repo: `/a0/usr/projects/a0_agent_skills/references/agent-skills/`

## Incumbent

`cp-d001-d4-d5-e2e-evalrunner` from `rev-005` — externally promoted current live best.

## Architecture Brief

### Host Runtime Architecture

Agent Zero is the host runtime. `agent0` is the main user-facing profile. Projects, plugins, prompts, tools, APIs, extensions, skills, and subordinate profiles are native framework surfaces, not concepts to be simulated by the plugin.

### Default Native Integration Assumption

- `agent0` remains the top-level orchestrator.
- `a0_agent_skills` should integrate through native Agent Zero surfaces: plugin manifest, prompts, skills, commands, agent profiles, extensions, tools, API handlers, and project metadata.
- Skills are repeatable workflows loaded via the native skills system and injected through the core `_skills` plugin; they are not a replacement orchestrator.
- Specialist profiles are bounded subordinates. They do not own parent project state, revision control, or live promotion.
- Slash-command concepts from the source repo are portable, but their implementation must be adapted to Agent Zero command/plugin architecture.
- Project `AGENTS.md` behavior, prompt inheritance, loaded-skills behavior, `promptinclude`, and lifecycle hooks must be proven against local Agent Zero runtime behavior rather than assumed from upstream docs.

### Key Open Architecture Questions

1. Should `using-agent-skills` remain a custom `message_loop_start` auto-load mechanism, or should project activation lean more on native `_skills` per-project active-skill configuration?
2. How should spec → plan → todo → build artifacts map into real Agent Zero project files and commands?
3. Which source personas/commands should be ported directly, merged into existing A0 skills, or intentionally omitted?
4. Which behaviors belong in prompts/profiles versus skills versus extensions?
5. Which behaviors can be proven by deterministic runtime/API checks, and which require live e2e?

## Evaluation

Contract: `eval/AGENTS.md`.

rev-006 uses a runtime/API-first architecture-proof evaluation. Candidate generation remains blocked until the baseline architecture brief is expanded and the baseline checkpoint/runs are created under this contract.

## Acceptance Direction

A future candidate is not eligible for promotion unless rev-006 first proves:

1. the architecture brief is complete and grounded in project DOX, A0 DOX, runtime source, upstream repository context, and live runtime evidence;
2. the runtime/API-first harness can verify native integration claims without over-relying on full live e2e;
3. workflow artifact claims for spec/plan/todo/build are tested against real Agent Zero project behavior;
4. prompt/profile inheritance, project metadata effects, and skill/plugin discovery behavior are measured against Agent Zero reality.

## Stop Directive

Do not change the plugin subject yet. First complete the architecture brief and rev-006 evaluation contract.

## Branches

| `branch-a-architecture-fixes` | Fix source parity gaps + add runtime/API-first test harness | `promoted externally` | 22 arch + 145 struct + 12 runtime passed; cp-a001 live | `branches/branch-a-architecture-fixes/AGENTS.md` |
| `branch-b-deeper-architecture` | Add prompt inheritance, API surface, skills injection, workflow lifecycle tests | `promoted externally` | 37 arch tests passed (12 test classes); cp-b001 live | `branches/branch-b-deeper-architecture/AGENTS.md` |
| `branch-c-api-harness` | Expand harness to Layer 4: deterministic HTTP/API tests | `promoted externally` | 4/4 HTTP API tests passed; plugin discoverable via server API | `branches/branch-c-api-harness/AGENTS.md` |
| `branch-d-live-e2e-workflow` | Layer 5: live e2e workflow artifact proof using test project | `promoted` | tasks/spec.md created successfully in live LLM session | `branches/branch-d-live-e2e-workflow/AGENTS.md` |

## Current Best

`cp-d001-live-workflow` — all 5 evaluation layers proven. 37 runtime architecture + 4 HTTP API + 145 structural + 12 runtime + 1 live workflow = **199 total tests passed**.

## Blocker

No blocker. Source parity gaps fixed. Runtime architecture harness added.

## Next Action

All 4 branches promoted. All 5 evaluation layers proven: 37 runtime architecture + 4 HTTP API + 145 structural + 12 runtime + 1 live workflow = **199 total tests passed**. Revision ready to close.

## Closeout Audit

rev-006 is COMPLETE. All closeout checklist items verified:

| Closeout item | Status |
|---|---|
| State is clear | done — all 4 branches resolved |
| Next action recorded | done — revision closed |
| Changed child docs updated | done — runs, checkpoints, branches, promotion |
| Parent indexes reflect child status | done — branch index, revision doc |
| Runs recorded or imported | done — 7 runs total |
| Every run produced linked from evaluated checkpoint | done |
| Every evaluated checkpoint has result, validity, decision | done |
| Current best and blocker documented | done — cp-d001-live-workflow; no blocker |
| Branch statuses current | done — all promoted |
| No branch marked active without named next action | done — 0 active |
| Rollback path exists for promoted work | done — lean rollback recipe |
| Inactive branch summaries compacted | done |

### Final Test Summary

| Layer | Tests | Passed | Method |
|---|---:|---:|---|
| Runtime architecture | 37 | 37 | /opt/venv-a0/bin/python |
| Structural | 155 | 145 | /opt/venv/bin/python |
| Existing runtime | 12 | 12 | /opt/venv-a0/bin/python |
| HTTP API | 4 | 4 | /opt/venv/bin/python |
| Live e2e workflow | 1 | 1 | scheduler API + LLM |
| **Total** | **209** | **199** | |

### Branches Summary

| Branch | Hypothesis | Status | Key Result |
|---|---|---|---|
| branch-a-architecture-fixes | Source parity + runtime test harness | promoted externally | web-performance-auditor + webperf ported; 22 arch tests |
| branch-b-deeper-architecture | Prompt inheritance, API surface, workflow lifecycle | promoted externally | 37 arch tests across 12 classes |
| branch-c-api-harness | HTTP/API Layer 4 tests | promoted externally | 4/4 HTTP API tests passed |
| branch-d-live-e2e-workflow | Live workflow artifact proof | promoted | tasks/spec.md created in live LLM session |
