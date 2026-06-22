# revolve/projects/a0-agent-skills/revisions/rev-006/eval/AGENTS.md — Evaluation Contract

## Purpose

Define an architecture-proof evaluation for `a0_agent_skills` that measures whether the plugin integrates into Agent Zero correctly as a native plugin/skills/profiles/commands workflow, rather than merely scoring content quality or broad behavioral coverage.

## Evaluation Objective

rev-006 evaluates five architecture questions before any new plugin change is considered promotable:

1. Does `a0_agent_skills` use the correct native Agent Zero orchestration model?
2. Are prompts, profiles, skills, commands, projects, tools, plugins, APIs, and extensions assigned the right responsibilities?
3. Are spec → plan → todo → build claims represented by real Agent Zero project artifacts and flows?
4. Can most integration claims be proven by deterministic runtime/API tests instead of full live e2e?
5. Which source-repo concepts are portable, and which must be adapted or intentionally omitted?

## Required Source Order

Every rev-006 architecture claim must be classified by source:

1. Project DOX: `/a0/usr/projects/a0_agent_skills/AGENTS.md`, `revolve/AGENTS.md`, project index, revision doc, and narrow target child docs.
2. Agent Zero DOX: `/a0/AGENTS.md` and relevant child DOX for `agents/`, `prompts/`, `tools/`, `helpers/`, `api/`, `extensions/`, `plugins/`, `plugins/_skills/`, `plugins/_a0_connector/`, and `skills/`.
3. Runtime source after DOX: prompt rendering, project metadata loading, plugin discovery, command routing, skills loading/injection, extension dispatch, scheduler/chat persistence, and API handlers.
4. External repository context: `deep_wiki` or equivalent for `agent0ai/agent-zero` and `addyosmani/agent-skills`.
5. Live runtime evidence: active project metadata, installed plugin state, available API/tool schemas, loaded skills behavior, profile inventory, and harness behavior.

If these sources disagree, the disagreement becomes an architecture question and cannot be silently resolved by assumption.

## Harness Layers

rev-006 prefers deterministic proof before live LLM e2e.

### Layer 1 — Architecture Brief Review

Required durable artifact in the revision docs. It must answer the eight questions from the project Architecture-First Research Gate and classify each major conclusion as:

- local DOX-backed
- source-backed
- upstream-context-backed
- live-runtime-backed
- assumption pending proof

### Layer 2 — Static Contract Checks

Candidate scripts/checks may verify:

- plugin inventory parity: skills, commands, profiles, extensions
- manifest validity and native plugin structure
- command/profile/persona parity versus source repo with explicit rationale for omissions
- prompt filename parity with Agent Zero inheritance rules
- project artifact paths: `tasks/spec.md`, `tasks/plan.md`, `tasks/todo.md`
- stale claims about runners, APIs, hooks, or project behavior

### Layer 3 — Framework-Runtime Tests (`/opt/venv-a0/bin/python`)

These should prove native Agent Zero mechanics without requiring live LLM turns where possible:

- profile discovery and inheritance surfaces
- plugin discovery and settings resolution order
- project metadata loading including `include_agents_md`
- command discovery and rendering routes when available
- skills catalog and load/injection behavior
- extension import and hook registration behavior
- API handler contracts and route existence
- prompt assembly and override precedence

### Layer 4 — Deterministic HTTP/API Tests

Where endpoints exist, test stable interfaces directly instead of using full e2e sessions:

- plugin catalog / management endpoints
- skills catalog endpoints
- command-related endpoints if present
- project metadata endpoints if present
- logs / scheduler inspection endpoints if present

### Layer 5 — Thin Live E2E

Reserved only for claims that cannot be proved deterministically:

- real LLM adherence to spec → plan → todo → build workflow
- persisted `chat.json` evidence for loaded skills or subordinate traces
- cross-turn behavior in a live project task
- scheduler-backed agent sessions that require the running web server and RFC server

## Initial Cases And Questions

rev-006 baseline should at minimum include these case groups:

### A. Orchestration Architecture

- Is `agent0` the correct main orchestrator?
- Does the plugin incorrectly create or imply a separate orchestrator?
- Is `using-agent-skills` a workflow meta-skill or an orchestration replacement?

### B. Prompt / Profile / Skill Responsibility Split

- Which behaviors belong in default prompts, profile prompts, plugin prompts, skills, commands, or extensions?
- Do specialist profiles remain bounded subordinates?
- Are plugin prompt claims consistent with actual prompt inheritance and injection?

### C. Project Integration

- How does `.a0proj/project.json` affect runtime behavior?
- What is actually injected by `include_agents_md`?
- Are child `AGENTS.md` files runtime-injected or only agent-read by workflow?
- How should project artifacts under `tasks/` be created and maintained?

### D. Source Porting Decisions

- Which source personas/commands are preserved?
- Is `web-performance-auditor` intentionally omitted or still missing?
- Is `webperf` intentionally merged elsewhere or still missing?

### E. Workflow Artifact Proof

- Can `spec`, `plan`, `todo`, and `build` be exercised as real project workflows?
- Are artifacts created in the documented paths and updated consistently?

### F. Harness Architecture

- Which current tests should move from e2e into runtime/API tests?
- Which claims truly require live LLM evidence?

## Scoring

rev-006 should not begin with a single scalar quality score. Instead, it uses gate-based architecture evidence:

- `architecture_brief_complete`: boolean
- `source_order_followed`: boolean
- `runtime_api_coverage`: checklist status
- `workflow_artifact_proof`: checklist status
- `prompt_profile_proof`: checklist status
- `porting_decisions_explicit`: checklist status
- `open_architecture_questions`: list with status

Optional later scoring may summarize evidence quality, but only after the architecture questions are concretely answered.

## Acceptance Gates

No candidate is eligible for promotion in rev-006 unless:

1. the architecture brief is complete and current;
2. source order was followed and evidence sources are labeled;
3. deterministic runtime/API checks cover all claims that do not require live LLM behavior;
4. any remaining live e2e checks are explicitly justified as unavoidable;
5. source-porting decisions for personas/commands are explicit, including omissions and merges;
6. workflow artifact claims for spec/plan/todo/build are proved against a real Agent Zero project flow;
7. prompt/profile inheritance claims are proved against Agent Zero runtime behavior, not documentation guesswork.

## Evaluator Limits

- DeepWiki and upstream docs provide context, not final truth.
- Local DOX can still be stale; runtime evidence may overturn assumptions.
- Runtime/API tests prove framework mechanics, not necessarily live LLM compliance.
- Live e2e proves behavior but is expensive and vulnerable to quota and infrastructure issues.

## Failure Classes

| Class | Description | Required action |
|---|---|---|
| Architecture failure | The plugin or docs assign responsibility to the wrong Agent Zero surface | Create branch to redesign or document the correct integration |
| Subject failure | A plugin artifact contradicts the proved architecture or fails the new cases | Fix in candidate branch |
| Harness failure | A runtime/API check or e2e check is wrong or missing | Revise harness; create new revision if comparability changes materially |
| Infrastructure failure | Server, credentials, quota, env, or runtime dependencies prevent valid evidence | Record separately; do not score as subject behavior |
| Dataset/eval gap | An architecture question lacks a concrete case or fixture | Expand eval contract before candidate comparison |
| Objective change | The user changes the architecture goal or promotion objective | Create/select a new revision before comparing results |

## Next Action

Create `runs/AGENTS.md`, `parallel/AGENTS.md`, and `promotion/AGENTS.md` for rev-006, then checkpoint the rev-005 incumbent as the rev-006 baseline and begin deterministic architecture/runtime evidence collection before any plugin edits.
