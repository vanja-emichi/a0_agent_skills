# a0_agent_skills Plugin DOX

## Purpose

Installed Agent Zero runtime plugin providing 23 production-grade engineering skills, 4 agent profiles (agent0 with prompt override, code-reviewer, security-auditor, test-engineer), 7 slash commands, 5 reference checklists, and Python extensions for DOX interpretation, file protection, and documentation caching.

## Ownership

This file owns contracts for `/a0/usr/plugins/a0_agent_skills/` because the user explicitly requested DOX integration for this user plugin. Source authoring truth remains `/a0/usr/projects/a0_agent_skills/`.

### Source vs Plugin relationship

- **Source project** (`/a0/usr/projects/a0_agent_skills/`): Historical reference in original format (shell hooks, markdown agents, Claude/Gemini commands). Not modified to match the plugin.
- **Installed plugin** (`/a0/usr/plugins/a0_agent_skills/`): Runtime-ready Agent Zero version with Python extensions, YAML commands, agent profiles. This is what we actively develop.
- Sync direction: plugin → source for test files only. Skills, extensions, commands, and agents are maintained independently in each.

## Local Contracts

- Keep root `plugin.yaml` valid for Agent Zero plugin discovery.
- Skills live under `skills/<skill-name>/SKILL.md` with optional support files in the same skill directory.
- DOX authority lives in root and child `AGENTS.md` files. All project/file work must read the applicable `AGENTS.md` chain before mutation.
- `using-agent-skills` is the meta-skill for skill discovery and routing; it does not replace reading `AGENTS.md` directly.
- Shared engineering references live only under `skills/using-agent-skills/references/`; other skills must read them via `skills_tool read_file` using `skill_name: "using-agent-skills"`.
- Working lifecycle artifacts live under `tasks/` as `tasks/spec.md`, `tasks/plan.md`, and `tasks/todo.md`; `docs/` is reserved for durable documentation rather than temporary workflow artifacts.
- Commands that mutate or review project files must include DOX closeout guidance.
- Subordinate profiles must treat applicable project `AGENTS.md` files as binding when reviewing project files.
- Extensions live under `extensions/python/<extension_point>/`.
- The DOX framework uses prompt-based awareness: an agent0 specifics override (`agents/agent0/prompts/agent.system.main.specifics.md`) injects skill discovery and DOX awareness at position 1 of the main prompt, and a system-prompt interpreter (`extensions/python/system_prompt/_10a_dox_interpreter.py` + `prompts/agent.system.dox_interpreter.md`) injects the full DOX framework at position 2. A canonical project-scaffold template lives at `templates/dox/AGENTS.md`.
- Do not add child `AGENTS.md` files under this installed plugin unless a future explicit request creates a durable sub-boundary.
- **Sprint state maintenance:** After completing any task from `tasks/todo.md`, mark it `[x]` and update checkpoints before moving to the next task. Before starting new work, always read the current todo state to avoid re-doing completed work.
- Skill behavioral evals live under `skills/<skill-name>/evals/evals.json` using the `agent-skills-eval` schema.
- The eval framework (`agent-skills-eval`) is cloned at `/a0/usr/projects/a0_agent_skills/eval/`.
- Eval results are stored in `/a0/usr/projects/a0_agent_skills/eval-workspace/iteration-<N>/`.
- Verification utilities (health checks, eval reports, status checks) should be **tests**, not slash commands. Commands are for user-facing agent workflows. Tests are for programmatic verification.

### DOX authority model

1. **Root `AGENTS.md`** defines that DOX is binding for project/file work.
2. **Child `AGENTS.md` files** define local subtree contracts; the nearest contract wins for local details.
3. **DOX interpreter** (position 2 in system prompt) teaches the agent to read AGENTS.md chains before editing and update them after meaningful changes.
4. **Agent0 specifics override** (position 1 in system prompt) reinforces skill discovery and DOX awareness at the highest prominence.
5. **`using-agent-skills`** provides skill discovery and routing only; it does not own DOX workflow.

## Work Guidance

## File Inventory

### Skills (23)

| # | Skill | Has evals | Extra files |
|---|---|---|---|
| 1 | `api-and-interface-design` | yes | - |
| 2 | `browser-testing-with-devtools` | yes | - |
| 3 | `ci-cd-and-automation` | yes | - |
| 4 | `code-review-and-quality` | yes | - |
| 5 | `code-simplification` | yes | - |
| 6 | `context-engineering` | yes | - |
| 7 | `debugging-and-error-recovery` | yes | - |
| 8 | `deprecation-and-migration` | yes | - |
| 9 | `documentation-and-adrs` | yes | - |
| 10 | `doubt-driven-development` | yes | - |
| 11 | `frontend-ui-engineering` | yes | - |
| 12 | `git-workflow-and-versioning` | yes | - |
| 13 | `idea-refine` | yes | `AGENTS.md`, `examples.md`, `frameworks.md`, `refinement-criteria.md`, `scripts/idea-refine.sh` |
| 14 | `incremental-implementation` | yes | - |
| 15 | `interview-me` | yes | - |
| 16 | `performance-optimization` | yes | - |
| 17 | `planning-and-task-breakdown` | yes | - |
| 18 | `security-and-hardening` | yes | - |
| 19 | `shipping-and-launch` | yes | - |
| 20 | `source-driven-development` | yes | - |
| 21 | `spec-driven-development` | yes | - |
| 22 | `test-driven-development` | yes | - |
| 23 | `using-agent-skills` | yes | `references/` (5 checklists: accessibility, orchestration, performance, security, testing) |

### Agent Profiles (4)

| Profile | Files |
|---|---|
| `agent0` | `agent.yaml`, `prompts/agent.system.main.specifics.md` |
| `code-reviewer` | `agent.yaml`, `prompts/agent.system.main.specifics.md` |
| `security-auditor` | `agent.yaml`, `prompts/agent.system.main.specifics.md` |
| `test-engineer` | `agent.yaml`, `prompts/agent.system.main.specifics.md` |

### Commands (7)

| Command | Backend | Template/Script |
|---|---|---|
| `build` | text | `build.txt` |
| `code-simplify` | text | `code-simplify.txt` |
| `plan` | text | `plan.txt` |
| `review` | text | `review.txt` |
| `ship` | Python | `ship.py` |
| `spec` | text | `spec.txt` |
| `test` | text | `test.txt` |

### Extensions

See [Extensions section](#extensions) below for descriptions.

| Extension Point | File | Purpose |
|---|---|---|
| `text_editor_write_after` | `_10_simplify_ignore.py` | Expand simplify-ignore placeholders after write |
| `text_editor_patch_after` | `_10_simplify_ignore.py` | Expand simplify-ignore placeholders after patch |
| `tool_execute_before` | `_10_sdd_cache.py` | Cache check before browser tool |
| `tool_execute_before` | `_20_simplify_ignore.py` | Filter simplify-ignore blocks before text_editor read |
| `tool_execute_after` | `_10_sdd_cache.py` | Store/serve browser cache after tool execution |
| `system_prompt` | `_10a_dox_interpreter.py` | Inject DOX/AGENTS.md interpretation rules into the system prompt |
| `monologue_end` | `_10_simplify_ignore.py` | Restore files from backup on session end |
| `monologue_end` | `_15_skill_auto_unload.py` | Unload skills at session end |

**Shared utility:**

| File | Purpose |
|---|---|
| `_simplify_ignore_util.py` | Shared simplify-ignore logic (cache, filter, expand, backup, restore) |

### Docs

| File | Description |
|---|---|
| `docs/decisions/ADR-001-python-extensions-over-shell-hooks.md` | Python extensions design decision |
| `docs/decisions/ADR-002-dox-runtime-skill-lifecycle-gates.md` | DOX gate design decision |
| `docs/decisions/ADR-003-source-historical-plugin-canonical.md` | Source vs plugin relationship |
| `docs/decisions/ADR-004-sdd-documentation-cache.md` | SDD cache design decision |
| `docs/decisions/ADR-005-simplify-ignore-file-protection.md` | Simplify-ignore design decision |
| `docs/decisions/ADR-006-e2e-test-harness.md` | E2E test harness design decision |

### DOX Framework Assets

| File | Purpose |
|---|---|
| `prompts/agent.system.dox_interpreter.md` | System-prompt interpreter explaining how Agent Zero should apply AGENTS.md / DOX contracts |
| `templates/dox/AGENTS.md` | Canonical DOX root scaffold copied from `source_dox/_AGENTS.md` for project initialization |
| `agents/agent0/prompts/agent.system.main.specifics.md` | Agent0 specifics override injecting skill discovery and DOX awareness at position 1 of the main prompt |
| `core-behaviors.promptinclude.md` | Legacy condensed operating rules reference retained for compatibility |

### Config

| File | Purpose |
|---|---|
| `plugin.yaml` | Plugin metadata (name, version, author) |
| `pytest.ini` | Pytest markers: `runtime_integration`, `dox_behavioral`, `dox_contract`, `e2e` |

### Other

| File | Purpose |
|---|---|
| `hooks.py` | Plugin lifecycle hooks (`install()`/`uninstall()`) |
| `scripts/validate-skills.js` | Skill structure validation script |
| `.github/workflows/test-plugin.yml` | CI workflow for structural tests |

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

## Verification

- `cd /a0/usr/plugins/a0_agent_skills && /opt/venv/bin/python -m pytest tests -v -m 'not e2e' -q`
- `cd /a0/usr/plugins/a0_agent_skills && node scripts/validate-skills.js`

### Test categories

| Category | Files | Runs where | Needs |
|---|---|---|---|
| Structural | `test_structure`, `test_sdd_cache`, `test_simplify_ignore`, `test_ship_command`, `test_e2e_extensions` (presence+compile) | Local + CI | Python 3.13, pytest, pyyaml |
| Isolated imports | `test_extension_imports_isolated` | Local + CI | Python 3.13, subprocess isolation |
| DOX contract | `test_dox_behavior` (marked `@pytest.mark.dox_contract`), `test_dox_interpreter` | Local + CI | Python 3.13 |
| Eval report | `test_eval_report` | Local + CI | Python 3.13 |
| Runtime integration | `test_runtime_commands`, `test_runtime_extensions_and_hooks`, `test_runtime_skills_and_agents` (marked `@pytest.mark.runtime_integration`) | Local only (A0 runtime) | `/opt/venv-a0/bin/python` with A0 framework |
| Framework conformance | `test_framework_conformance` | Local only (A0 runtime) | `/opt/venv-a0/bin/python` — compares LogItem dataclass fields against plugin mocks |
| E2e behavioral | `test_e2e_dox_behavior`, `test_e2e_dox_closeout`, `test_e2e_skill_loading`, `test_e2e_agent_profiles`, `test_e2e_extensions` (injection), `test_e2e_command_execution`, `test_e2e_command_rendering`, `test_e2e_reference_access`, `test_e2e_extension_behavior` | Live server only | A0 server on port 80, env vars `A0_E2E_USERNAME`/`A0_E2E_PASSWORD` |

CI excludes runtime integration tests (they import `helpers.*` from the A0 framework which isn't available on GitHub Actions).

## Extensions

### DOX Interpreter

| Extension | Extension Point | Behavior |
|---|---|---|
| `_10a_dox_interpreter.py` | `system_prompt` | **System-level.** Appends the full DOX interpreter to the assembled system prompt so Agent Zero treats root AGENTS.md as active project context, child AGENTS.md files as on-demand contracts, and DOX closeout as mandatory after meaningful changes. |
| `_15_skill_auto_unload.py` | `monologue_end` | Unloads skills at session end to keep context clean. |

### File Protection (Simplify-Ignore)

| Extension | Extension Point | Behavior |
|---|---|---|
| `_20_simplify_ignore.py` | `tool_execute_before` | Before `text_editor action=read`, checks for `simplify-ignore-start/end` blocks. Backs up original and replaces blocks with `BLOCK_<hash>` placeholders in-place. |
| `_10_simplify_ignore.py` | `text_editor_write_after` | After write, expands `BLOCK_<hash>` placeholders back to original content, then re-filters so blocks stay hidden on disk. Updates backup. |
| `_10_simplify_ignore.py` | `text_editor_patch_after` | After patch, same expand/re-filter cycle as write_after. Updates backup. |
| `_10_simplify_ignore.py` | `monologue_end` | On session end, restores all files from backup and cleans up cache. |
| `_simplify_ignore_util.py` | (shared utility) | Core logic: filter, expand, backup, restore. Cache stored in `.a0proj/simplify-ignore-cache/`. Stdlib only. |

### Documentation Cache (SDD Cache)

| Extension | Extension Point | Behavior |
|---|---|---|
| `_10_sdd_cache.py` | `tool_execute_before` | Before `browser` tool navigate/content actions, checks cache for URL. If cached and server returns HTTP 304, redirects to no-op (`action=list`) and stores cached content for post-extension to surface. |
| `_10_sdd_cache.py` | `tool_execute_after` | After `browser` tool, either serves cached content (on hit) or stores new response with ETag/Last-Modified from HEAD request. Cache stored in `.a0proj/sdd-cache/<hash>.json`. |

### Prompt Include

| File | Purpose |
|---|---|
| `core-behaviors.promptinclude.md` | Condensed operating rules reference retained for compatibility. The authoritative runtime path is the agent0 specifics override (position 1) plus the DOX interpreter system_prompt extension (position 2). |

### Design principles

- DOX awareness is **prompt-based** — the agent0 specifics override and DOX interpreter teach the agent to read AGENTS.md chains before editing and update them after meaningful changes.
- DOX interpretation belongs in the **system prompt**; no runtime enforcement hooks.
- Simplify-ignore and SDD cache extensions are **non-blocking** — they modify data but never prevent actions.
- Skill auto-unload at monologue end keeps context clean for subsequent tasks.

### Framework integration

Extensions that interact with Agent Zero internals (context log, tool args, agent state) must be verified against the actual framework source code, not just mock tests. Key files:

- `/a0/helpers/log.py` — LogItem dataclass format for context log entries
- `/a0/helpers/extension.py` — Extension base class and call signature
- `/a0/plugins/_text_editor/tools/text_editor.py` — How text_editor calls before/after extensions

Unit test mocks must match the real LogItem dataclass fields: `.type`, `.heading`, `.content`, `.kvps` (not dict keys `"tool"` or `"message"`).

## E2e test architecture

E2e tests verify Agent Zero's plugin, skill, agent, and DOX systems through live scheduler tasks via HTTP API.

**4 evidence layers** (checked via `A0E2EClient` helpers):

1. **Task lifecycle** — scheduler task reaches `idle` state
2. **Response text** — agent's last response from `get_last_agent_response()` contains expected markers
3. **Runtime logs** — no unexpected errors via `get_logs()`
4. **Persisted context** — `chat.json` reflects loaded skills and subordinate traces via `get_chat_json()`

**Critical: do NOT rely on file writes as primary evidence.** LLM agents do not always write verification files within the test timeout. Use `get_last_agent_response()` to check the agent's actual response text from chat history instead.

**Activity-based polling:** `wait_for_task` monitors log progress and extends timeout while the agent is active (default 600s wall clock, 300s activity timeout).

**Run all tests together:** `/opt/venv/bin/python -m pytest tests/ -v -n 4 --tb=short`
**Run e2e only:** `/opt/venv/bin/python -m pytest tests/ -v -m e2e -n 4 --tb=short`
**Run structural only:** `/opt/venv/bin/python -m pytest tests/ -v -m 'not e2e' --tb=short`

**Credentials:** Must come from env vars `A0_E2E_USERNAME` and `A0_E2E_PASSWORD`. Never hardcode defaults.

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
- To run e2e tests: `A0_E2E_USERNAME=xxx A0_E2E_PASSWORD=yyy /opt/venv/bin/python -m pytest tests/ -v -m e2e -n 4`

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
- **Credentials** — always inline: `A0_E2E_USERNAME=xxx A0_E2E_PASSWORD=yyy /opt/venv/bin/python -m pytest ...`

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

## Child DOX Index

| Path | Scope |
|---|---|
| `commands/AGENTS.md` | Command contracts |
| `docs/decisions/AGENTS.md` | ADR indexing rules |
| `extensions/python/monologue_end/AGENTS.md` | Monologue-end extension contracts |
| `extensions/python/tool_execute_before/AGENTS.md` | Tool-execute-before extension contracts |
| `skills/idea-refine/AGENTS.md` | Idea-refine skill contracts |
| `tests/AGENTS.md` | Test file contracts |

## Commands architecture

Plugin commands are YAML-configured slash commands backed by text templates or Python scripts.

- **Discovery**: Commands plugin scans all plugin `commands/` directories via `_discover_plugin_commands()`
- **Resolution**: API at `/api/plugins/commands/commands` with action `resolve`
- **Text commands**: Template rendering with `{raw}`, `{args}` placeholders
- **Script commands**: Python `run(payload)` with context and history
- **Testing**: Commands are tested via the resolve API (deterministic, no LLM needed)
- **Not scheduler tasks**: Commands resolve to text that gets injected into the chat
