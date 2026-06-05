# a0_agent_skills Plugin DOX

## Purpose

Installed Agent Zero runtime plugin for engineering skills, specialist agent profiles, lifecycle commands, and Python extensions.

## Ownership

This file owns contracts for `/a0/usr/plugins/a0_agent_skills/` because the user explicitly requested DOX integration for this user plugin. Source authoring truth remains `/a0/usr/projects/a0_agent_skills/`.

### Source vs Plugin relationship

- **Source project** (`/a0/usr/projects/a0_agent_skills/`): Historical reference in original format (shell hooks, markdown agents, Claude/Gemini commands). Not modified to match the plugin.
- **Installed plugin** (`/a0/usr/plugins/a0_agent_skills/`): Runtime-ready Agent Zero version with Python extensions, YAML commands, agent profiles. This is what we actively develop.
- Sync direction: plugin → source for test files only. Skills, extensions, commands, and agents are maintained independently in each.

## Local Contracts

- Keep root `plugin.yaml` valid for Agent Zero plugin discovery.
- Skills live under `skills/<skill-name>/SKILL.md` with optional support files in the same skill directory.
- `dox-project-context` owns the runtime workflow for applying `AGENTS.md` project contracts.
- `using-agent-skills` routes project/file work to `dox-project-context`.
- Shared engineering references live only under `skills/using-agent-skills/references/`; other skills must read them via `skills_tool read_file` using `skill_name: "using-agent-skills"`.
- Working lifecycle artifacts live under `tasks/` as `tasks/spec.md`, `tasks/plan.md`, and `tasks/todo.md`; `docs/` is reserved for durable documentation rather than temporary workflow artifacts.
- Commands that mutate or review project files must include DOX preflight and closeout guidance.
- Subordinate profiles must treat applicable project `AGENTS.md` files as binding when reviewing project files.
- Extensions live under `extensions/python/<extension_point>/`.
- Do not add child `AGENTS.md` files under this installed plugin unless a future explicit request creates a durable sub-boundary.
- Skill behavioral evals live under `skills/<skill-name>/evals/evals.json` using the `agent-skills-eval` schema.
- The eval framework (`agent-skills-eval`) is cloned at `/a0/usr/projects/a0_agent_skills/eval/`.
- Eval results are stored in `/a0/usr/projects/a0_agent_skills/eval-workspace/iteration-<N>/`.
- Behavioral fixes are tracked as Fix 1-5 (see Extensions section below).
- Verification utilities (health checks, eval reports, status checks) should be **tests**, not slash commands. Commands are for user-facing agent workflows. Tests are for programmatic verification.

## Work Guidance
 
## Environments
 
 Two Python environments exist inside the Docker container:
 
 | Environment | Path | Python | Purpose |
 |---|---|---|---|
 | **A0 runtime** | `/opt/venv-a0/bin/python` | 3.12 | Full framework deps: `crontab`, `langchain_core`, `litellm`, `pydantic`, `nest_asyncio`. Can import `helpers.task_scheduler`, `agent`, `initialize`, `tools.scheduler`. |
 | **Plugin test** | `/opt/venv/bin/python` | 3.13 | Missing framework deps. Used for structural plugin tests via `pytest`. Cannot import scheduler or agent modules. |
 
 ### Testing constraints
 
 - **Structural plugin tests** (file existence, parity, contract checks) run under `/opt/venv/bin/python` via normal `pytest`
 - **Runtime integration tests** that import framework helpers run under `/opt/venv-a0/bin/python` in a subprocess
 - **Scheduler behavioral tests** that create and run adhoc tasks MUST execute within a running Agent Zero context (live agent session), because scheduler task threads need the RFC server for `call_development_function` / `promptinclude` extensions
 - Standalone scheduler harness scripts will fail with `ConnectionRefusedError` on the RFC port unless the Agent Zero web server is running in the same process
 
 ### How to run real DOX behavioral tests
 
 The correct approach is to use the `scheduler` tool from within a running agent session:
 
 1. Create a fixture project with conflicting `AGENTS.md` contracts
 2. Use `scheduler` tool `create_adhoc_task` to create test tasks
 3. Use `scheduler` tool `run_task` to start each task
 4. Use `scheduler` tool `wait_for_task` to block until completion
 5. Inspect the task result and the modified fixture files
 6. Use `scheduler` tool `delete_task` to clean up
 
 Do NOT attempt to run scheduler tasks from a standalone Python subprocess — the RFC server will not be available and all tasks will fail with connection errors.

### E2e test architecture

E2e tests verify Agent Zero's plugin, skill, agent, and DOX systems through live scheduler tasks via HTTP API.

**4 evidence layers** (checked via `A0E2EClient` helpers):

1. **Task lifecycle** — scheduler task reaches `idle` state
2. **Response text** — agent's last response from `get_last_agent_response()` contains expected markers
3. **Runtime logs** — no unexpected errors via `get_logs()`
4. **Persisted context** — `chat.json` reflects loaded skills and subordinate traces via `get_chat_json()`

**Critical: do NOT rely on file writes as primary evidence.** LLM agents do not always write verification files within the test timeout. Use `get_last_agent_response()` to check the agent's actual response text from chat history instead.

**Activity-based polling:** `wait_for_task` monitors log progress and extends timeout while the agent is active (default 600s wall clock, 300s activity timeout).

**Run all tests together:** `python3 -m pytest tests/ -v -n 4 --tb=short`
**Run e2e only:** `python3 -m pytest tests/ -v -m e2e -n 4 --tb=short`
**Run structural only:** `python3 -m pytest tests/ -v -m 'not e2e' --tb=short`

**Credentials:** Must come from env vars `A0_E2E_USERNAME` and `A0_E2E_PASSWORD`. Never hardcode defaults.

Read this file before editing installed plugin runtime files. Keep changes mirrored with the source project when the source project is the canonical authoring surface.

## Verification

- `cd /a0/usr/plugins/a0_agent_skills && python3 -m pytest tests -q`
- `cd /a0/usr/plugins/a0_agent_skills && node scripts/validate-skills.js`

### Test categories

| Category | Files | Runs where | Needs |
|---|---|---|---|
| Structural | test_structure, test_extension_inject, test_sdd_cache, test_simplify_ignore, test_ship_command, test_e2e_extensions (presence+compile) | Local + CI | Python 3.13, pytest, pyyaml |
| Runtime integration | test_dox_behavior, test_runtime_commands, test_runtime_extensions_and_hooks, test_runtime_skills_and_agents | Local only (A0 runtime) | `/opt/venv-a0/bin/python` with A0 framework |
| E2e behavioral | test_e2e_dox_behavior, test_e2e_skill_loading, test_e2e_agent_profiles, test_e2e_extensions (injection), test_e2e_command_execution | Live server only | A0 server on port 80, env vars `A0_E2E_USERNAME`/`A0_E2E_PASSWORD` |

CI excludes runtime integration tests (they import `helpers.*` from the A0 framework which isn't available on GitHub Actions).

### E2E tests (require live Agent Zero server)

- `cd /a0/usr/plugins/a0_agent_skills && python3 -m pytest tests/ -v -m e2e -n 4` — parallel e2e via pytest-xdist
- `cd /a0/usr/plugins/a0_agent_skills && python3 -m pytest tests/ -v -m "not e2e"` — structural only, no server needed
- Tests use `tests/_a0_e2e_client.py` (HTTP client with auth, CSRF, retry, task lifecycle)
- Fixtures in `tests/conftest.py` skip e2e tests when server is down; task_tracker isolates cleanup per test
- Recommended worker count: `-n 4` (8 workers may overload single-process Flask + LLM inference)

**Chat.json history structure (discovered during e2e harness development):**

| Context type | Where agent responses live |
|---|---|
| Main agent (long conversation) | `agents[0].history` → JSON string → `bulks[].records[].messages[]` where `ai:true` |
| Scheduler tasks | `agents[0].history` → JSON string → `current.messages[]` where `ai:true` and `"tool_name": "response"` in content |
| Both | `topics[]` contains only the greeting message, not the task response |

The `get_last_agent_response()` method in `_a0_e2e_client.py` handles this by checking `current` → `topics` → `bulks` in priority order, filtering for `"tool_name": "response"` messages.

## E2e test credentials

- Credentials MUST come from environment variables `A0_E2E_USERNAME` and `A0_E2E_PASSWORD`
- Never hardcode credentials in test files or commit them to GitHub
- The server runs on **port 80** (auto-detected by `_a0_e2e_client.py`)
- Login is form-based POST to `/login` with `username` and `password` form fields
- CSRF token obtained from `/api/csrf_token` after authentication
- To run e2e tests: `A0_E2E_USERNAME=xxx A0_E2E_PASSWORD=yyy python3 -m pytest tests/ -v -m e2e -n 4`

## E2e testing procedures

### Task lifecycle

1. **Create and run** — `a0_client.create_and_run_task(name, prompt)` creates and starts a scheduler task
2. **Poll ticks** — `a0_client.wait_for_task(uuid)` polls with activity-based timeouts (600s wall clock, 300s activity)
3. **Gather evidence** — `gather_evidence(a0_client, result)` extracts task state, chat response, and logs
4. **Delete tasks** — ALWAYS delete test tasks after completion via `a0_client.delete_task(uuid)`. The `clean_tasks` fixture handles this automatically when task UUIDs are tracked in `task_tracker`

### Key rules

- **Never blindly wait** — poll the scheduler ticks to check progress
- **Always clean up** — delete test tasks after assertion, whether pass or fail
- **Fixture names** — use `a0_client` (not `client`), include `task_tracker` and `clean_tasks` in behavioral test signatures
- **Sequential vs parallel** — extension behavior tests MUST run sequentially (`-n 0`) because they create temp files; other e2e tests can use `-n 4`
- **Simplify-ignore markers** — when writing test files that contain `simplify-ignore-start/end` strings, use string concatenation (e.g. `"# simplify" + "-ignore-start"`) to avoid triggering the extension on the test file itself
- **Credentials** — always inline: `A0_E2E_USERNAME=xxx A0_E2E_PASSWORD=yyy python3 -m pytest ...`

## Eval framework

Behavioral evals measure whether skills actually improve agent output. The framework is `agent-skills-eval` (TypeScript CLI) cloned at `/a0/usr/projects/a0_agent_skills/eval/`.

### Eval file structure

Each skill may have an `evals/evals.json` containing eval cases:

```
skills/<skill-name>/
├── SKILL.md
└── evals/
    └── evals.json    # array of eval cases with prompts and assertions
```

Eval schema per case:
- `id`: unique identifier
- `prompt`: the task given to the model
- `assertions`: array of `{ type, text }` where type is `llm-judge` or `tool-called`

### How to run evals

```bash
cd /a0/usr/projects/a0_agent_skills
node eval/dist/cli.js --config agent-skills-eval.yaml              # all skills
node eval/dist/cli.js --config agent-skills-eval.yaml --skills ci-cd-and-automation  # single skill
```

Results are stored in `eval-workspace/iteration-<N>/<skill-name>/benchmark.json`.

### Interpreting results

Each eval runs in two modes:
- **with_skill**: SKILL.md content is injected into the prompt
- **without_skill**: model receives only the prompt

**Delta pass rate** (`with_skill` minus `without_skill`) measures the skill's behavioral lift. Positive delta = skill helps. Zero/negative = eval needs rewriting or skill needs simplification.

### Baseline results (iteration-7, 24 skills)

| Metric | Value |
|---|---|
| Skills with positive lift | 21/24 (87.5%) |
| Average delta | +34.4pp |
| Top skill | context-engineering (+83.3pp) |

After fixing 4 underperforming skills (iterations 8-19):
- 23/24 skills show positive or zero lift (ci-cd-and-automation fixed from -10pp to +12pp)
- 1 skill (code-review-and-quality) shows floor effect — model already scores 100% without skill

### Adding new evals

1. Create `skills/<skill-name>/evals/evals.json`
2. Write evals that test the skill's **unique workflow**, not basic domain knowledge
3. Run the eval: `node eval/dist/cli.js --config agent-skills-eval.yaml --skills <skill-name>`
4. Check delta pass rate — aim for >+20pp lift

### Eval constraints

- **Single-turn only**: The framework tests single LLM completions, not multi-turn Agent Zero sessions
- **Model-dependent**: Results vary by model (glm-5.1 used for baselines)
- **LLM variance**: ±10-20pp swing between iterations is normal; run multiple iterations for significance
- **Floor effects**: Some skills test knowledge the model already possesses; these need harder evals

## Extensions (Fix 1-5)

Five extensions address the root causes of DOX non-compliance:

| Fix | Extension | Root Cause | What it does |
|---|---|---|---|
| 1 | `agent_init/_00_inject_meta_skill.py` | DOX skill not auto-loaded | Auto-loads `using-agent-skills` and `dox-project-context` at session start |
| 2 | `tool_execute_before/_30_dox_subordinate_handoff.py` | Subordinates DOX-blind | Injects `[DOX HANDOFF]` prefix in `call_subordinate` messages when missing |
| 3 | `text_editor_write_before/_10_dox_preflight_check.py` + `text_editor_patch_before/_10_dox_preflight_check.py` | No gate before edits | Logs warning if DOX skill not loaded before write/patch |
| 4 | `core-behaviors.promptinclude.md` | Behaviors buried in context | 30-line condensed rules auto-injected into system prompt |
| 5 | `monologue_end/_20_dox_compliance_check.py` | No compliance feedback | Reminds if files edited without reading AGENTS.md |

### Design principles

- Extensions are **advisory** (log warnings), not **blocking** (prevent edits)
- All extensions only affect the main agent (number == 0), not subordinates
- Fix 2 (subordinate handoff) is the exception — it modifies subordinate messages
- Extensions do not add log entries during `agent_init` (would suppress the greeting)

## Child DOX Index

No child DOX files.


### Commands architecture

Plugin commands are YAML-configured slash commands backed by text templates or Python scripts.

- **Discovery**: Commands plugin scans all plugin `commands/` directories via `_discover_plugin_commands()`
- **Resolution**: API at `/api/plugins/commands/commands` with action `resolve`
- **Text commands**: Template rendering with `{raw}`, `{args}` placeholders
- **Script commands**: Python `run(payload)` with context and history
- **Testing**: Commands are tested via the resolve API (deterministic, no LLM needed)
- **Not scheduler tasks**: Commands resolve to text that gets injected into the chat
