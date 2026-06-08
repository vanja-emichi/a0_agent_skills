# ADR-006: HTTP-API-Driven E2E Test Harness for Agent Zero Plugins

## Status

Accepted

## Date

2026-06-05

## Context

The `a0_agent_skills` plugin needed end-to-end tests that verify real agent behavior — skill loading, DOX contract resolution, subordinate profile calls, and command execution. Traditional unit tests can verify file structure and Python syntax, but cannot verify that an Agent Zero agent actually loads a skill, follows a DOX contract, or responds with the correct markers.

Agent Zero runs as a Flask web application with an HTTP API. The scheduler subsystem allows creating ad-hoc tasks that spawn fresh agent contexts. Each task runs independently with its own conversation history, persisted to `chat.json`.

### Constraints

- Agent Zero has no JSON login API — authentication is form-based (`POST /login` with `username` and `password` fields)
- Scheduler tasks store conversation history in `chat.json` under `current.messages[]`, not in `bulks` or `topics`
- Commands are resolved via the Commands plugin API at `/api/plugins/commands/commands`, not through the scheduler
- The scheduler runs tasks asynchronously — `run_task` returns immediately and the task executes in a background thread
- LLM agent responses are non-deterministic — exact text matching is fragile

## Decision

Build an HTTP-API-driven e2e test harness with three test categories and a four-layer evidence model.

### Test Categories

| Category | Runs where | Count | Needs |
|---|---|---|---|
| Structural | Local + CI | 151 | Python 3.13, pytest, pyyaml |
| Runtime integration | Local only | 22 | A0 framework (`/opt/venv-a0/bin/python`) |
| E2e behavioral | Live server only | 22 | Server on port 80, env vars for credentials |

CI excludes runtime integration tests (import `helpers.*` which isn't available on GitHub Actions).

### Four-Layer Evidence Model

Each e2e test verifies up to four layers:

1. **Task lifecycle** — scheduler task reaches `idle` state via `wait_for_task`
2. **Response text** — agent's last response from `get_last_agent_response()` contains expected markers
3. **Runtime logs** — no unexpected errors via `get_logs()` (soft check)
4. **Persisted context** — `chat.json` reflects loaded skills and subordinate traces (soft check)

### Response Extraction Strategy

Scheduler tasks store conversation history in `current.messages[]` as a JSON array. The `get_last_agent_response()` method walks the history in priority order:

1. `current.messages[]` — scheduler task responses (primary for e2e)
2. `bulks[].records[].messages[]` — main agent long-conversation responses
3. `topics[]` — greeting messages only (lowest priority)

Within each source, it filters for messages where `"tool_name": "response"` appears in the content, extracting the AI agent's final answer. It falls back to the last AI message if no response tool call is found.

### Authentication

The e2e client authenticates via form-based POST to `/login`, then fetches a CSRF token from `/api/csrf_token`. All subsequent API calls include the CSRF token. Credentials come from environment variables `A0_E2E_USERNAME` and `A0_E2E_PASSWORD` — never hardcoded.

### Commands Testing

Commands are tested via the resolve API (`/api/plugins/commands/commands`) with `action: "resolve"`, not through the scheduler. This is deterministic and instant (<1s per test). The scheduler is only used for behavioral tests that need a real LLM agent.

### Activity-Based Polling

`wait_for_task` monitors log progress and extends timeout while the agent is active (default 600s wall clock, 300s activity timeout). The task must have `last_run is not None` before accepting idle as a terminal state — tasks that start in idle (before first execution) are not considered complete.

### Parallel Execution

E2e tests run with `-n 4` workers (pytest-xdist). The scheduler handles multiple concurrent tasks — each spawns its own `DeferredTask` thread. Workers above 4 may overload the single-process Flask server.

## Alternatives Considered

### Standalone Python Scripts

- **Pros:** No server dependency, faster execution
- **Cons:** Cannot test real agent behavior — only framework plumbing. Would miss the most important bugs (wrong search order, response parsing failures, DOX contract misresolution)
- **Rejected:** Unit tests already cover structural checks; e2e must test real agent behavior

### File-Write Verification

- **Pros:** Simple — agent writes a marker file, test checks it exists
- **Cons:** LLM agents don't always write verification files within timeout. Fragile to prompt changes. One failed write = false negative
- **Rejected:** Replaced with `get_last_agent_response()` reading from `chat.json`

### JSON API Login

- **Pros:** Cleaner, more test-friendly
- **Cons:** Agent Zero doesn't have one. The login handler only accepts form data (`request.form['username']`)
- **Rejected:** Not available in the current framework

### Scheduler-Based Command Tests

- **Pros:** Tests the full agent pipeline including command resolution
- **Cons:** Commands resolve via a separate API (`/api/plugins/commands/commands`), not through the scheduler. Scheduler tasks with command prompts would test the wrong thing and timeout
- **Rejected:** Commands use resolve API for instant, deterministic testing

### Single-Worker Execution

- **Pros:** No concurrency issues, deterministic ordering
- **Cons:** 22 e2e tests × ~60s each = ~22 minutes. With `-n 4` it's ~6 minutes
- **Rejected:** Too slow for iterative development

## Consequences

### Positive

- **Real behavioral verification** — tests prove agents actually load skills, follow DOX contracts, and respond correctly
- **Resilient to LLM variance** — marker-based checks tolerate wording differences
- **Fast enough for iteration** — 22 e2e tests in ~4 minutes with parallel execution
- **CI-compatible** — structural tests (151) run on GitHub Actions; e2e tests run locally with live server
- **No credential leaks** — environment variables only, `.gitignore` excludes `secrets.env`

### Negative

- **Requires live server** — e2e tests skip when server is down (handled by conftest skip logic)
- **Non-deterministic** — LLM responses vary between runs; tests check for markers, not exact text
- **Flaky potential** — timeout-sensitive; tasks that take longer than 600s will fail
- **Discovery cost** — `chat.json` history structure was discovered empirically, not documented in framework

### Risks Mitigated

- **Chat.json format changes** — `get_last_agent_response()` checks multiple locations (`current` → `bulks` → `topics`) with fallbacks
- **Framework auth changes** — auth is behind `_ensure_authenticated()` / `_ensure_csrf()` methods, easy to update
- **Test isolation** — `task_tracker` fixture cleans up all tasks created during a test session

## Key Files

| File | Purpose |
|---|---|
| `tests/_a0_e2e_client.py` | HTTP client with auth, CSRF, task lifecycle, response extraction |
| `tests/conftest.py` | Fixtures, skip logic, task_tracker cleanup |
| `tests/test_e2e_dox_behavior.py` | DOX contract resolution with real agents |
| `tests/test_e2e_skill_loading.py` | Skill discovery and loading |
| `tests/test_e2e_agent_profiles.py` | Subordinate profile calls |
| `tests/test_e2e_command_execution.py` | Command resolution via resolve API |
| `tests/test_e2e_extensions.py` | Extension injection verification |
