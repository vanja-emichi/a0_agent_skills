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
