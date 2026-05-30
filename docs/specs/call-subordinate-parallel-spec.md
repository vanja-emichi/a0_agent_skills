# Spec: call_subordinate_parallel — Parallel Subordinate Execution Tool

## Objective

Build a new Agent Zero tool (`call_subordinate_parallel`) that lives entirely in the `a0_agent_skills` plugin, enabling N subordinate agents to run concurrently via `asyncio.gather` with shared workspace (filesystem) and isolated reasoning/history per worker.

**User:** The `a0_agent_skills` plugin — specifically:
- `/ship` command: parallel code-reviewer + security-auditor + test-engineer fan-out
- Future BUILD-phase: parallel `todo.md` item processing

**Success criteria:**
- Tool accepts a list of `{message, profile}` tasks and runs them concurrently
- Returns `[{profile, result, status, error, duration_ms, order}, ...]` per worker
- Zero core framework file modifications — lives entirely in plugin `tools/` directory
- Each worker gets its own dedicated `AgentContext` (isolated reasoning) but shares the same filesystem (shared workspace)
- Failed workers return error info; successful workers return their results (partial results, not all-or-nothing)
- `/ship` command updated to use the new tool instead of sequential `call_subordinate` calls

## Tech Stack

- **Language:** Python 3.12+ (matches Agent Zero runtime)
- **Framework:** Agent Zero plugin system — tool registration via `plugins/<name>/tools/<tool>.py`
- **Base class:** `helpers.tool.Tool` with `async def execute()` returning `Response`
- **Async runtime:** `asyncio.gather()` for concurrent worker execution
- **Context model:** `AgentContext` + `Agent` + `initialize_agent()` — same APIs the scheduler uses
- **No new dependencies** — uses only existing Agent Zero framework APIs

## Commands

```bash
# No build step — Agent Zero discovers tools at runtime via get_paths()
# Tool is auto-registered by placing it in plugins/a0_agent_skills/tools/

# Run existing plugin tests
cd /a0/usr/projects/a0_agent_skills
pytest tests/ -v

# Manual verification: invoke via agent prompt
# "Use call_subordinate_parallel with these tasks: [...]"
```

## Project Structure

```
plugins/a0_agent_skills/
├── tools/
│   └── call_subordinate_parallel.py    ← NEW: parallel fan-out tool (~150-250 lines)
├── commands/
│   └── ship.py                         ← MODIFIED: prompt uses new tool
├── tests/
│   ├── conftest.py                     ← existing
│   └── test_call_subordinate_parallel.py  ← NEW: unit tests
└── docs/
    ├── specs/
    │   ├── parallel-subordinate-execution.md       ← research (existing)
    │   └── call-subordinate-parallel-spec.md        ← this spec (new)
    └── intent/
        └── parallel-subordinate-execution.md       ← confirmed intent (existing)
```

## Code Style

Follow existing Agent Zero tool conventions. Reference: `/a0/plugins/_memory/tools/memory_save.py` (19 lines), `/a0/tools/call_subordinate.py` (55 lines).

```python
# Tool class naming: PascalCase, descriptive
# File naming: snake_case, matches tool invocation name
# Extends Tool from helpers.tool

from agent import Agent, UserMessage
from helpers.tool import Tool, Response
from initialize import initialize_agent
import asyncio
import time
import uuid


class ParallelDelegation(Tool):

    async def execute(self, tasks="", result_order="input", max_concurrency=0, **kwargs):
        """Execute N subordinate agents concurrently.

        Args via tool args (parsed from JSON):
            tasks: JSON string or list of dicts, each with:
                - message: str (required) — task prompt for the subordinate
                - profile: str (optional) — agent profile name
                - timeout_seconds: int (optional, default 300) — per-worker timeout
            result_order: str (optional, default "input") — "input" preserves order,
                "completion" orders by first-to-finish
            max_concurrency: int (optional, default 0) — max simultaneous workers;
                0 = unlimited; uses asyncio.Semaphore when > 0
        """
        # Parse and validate tasks
        # Create N workers with dedicated contexts
        # asyncio.as_completed for progress reporting as each finishes
        # Report progress via self.set_progress() after each worker completes
        # Format and return results
        pass

    def get_log_object(self):
        return self.agent.context.log.log(
            type="subagent",
            heading=f"icon://communication {self.agent.agent_name}: Calling Parallel Subordinates",
            content="",
            kvps=self.args,
        )
```

**Key conventions:**
- Tool args arrive as parsed JSON values (str, int, float, bool, list, dict, None) — NOT always strings. Validate types explicitly (`helpers/extract_tools.py:23-45`)
- `tasks` arg may be a JSON string OR a list of dicts — handle both cases
- Use `self.agent.read_prompt()` for any prompt templates
- Return `Response(message=result, break_loop=False)`
- Log via `get_log_object()` for UI visibility
- Follow `call_subordinate.py` patterns for consistency

## Tool API

### Input (tool args)

```json
{
    "tasks": [
        {
            "message": "Conduct a five-axis code review...",
            "profile": "code-reviewer",
            "timeout_seconds": 300
        },
        {
            "message": "Run a security and vulnerability pass...",
            "profile": "security-auditor",
            "timeout_seconds": 300
        },
        {
            "message": "Analyze test coverage...",
            "profile": "test-engineer",
            "timeout_seconds": 300
        }
    ],
    "result_order": "input",
    "max_concurrency": 0
}
```

### Output (returned to caller)

```json
[
    {
        "profile": "code-reviewer",
        "result": "## Code Review Report\n...",
        "status": "ok",
        "error": null,
        "duration_ms": 45230,
        "order": 0
    },
    {
        "profile": "security-auditor",
        "result": "## Security Audit Report\n...",
        "status": "ok",
        "error": null,
        "duration_ms": 52100,
        "order": 1
    },
    {
        "profile": "test-engineer",
        "result": "",
        "status": "fail",
        "error": "Timeout after 300s",
        "duration_ms": 300000,
        "order": 2
    }
]
```

## Worker Lifecycle

Each parallel worker follows this lifecycle (modeled on scheduler `_run_task`):

1. **Initialize**: `initialize_agent()` → get `AgentConfig`
2. **Set profile**: Apply `profile` override if provided
3. **Create context**: `AgentContext(config, id=<uuid>, name=<task-name>)` — dedicated, isolated
4. **Create agent**: `Agent(number, config, context)` — fresh instance per worker
5. **Inject message**: `agent.hist_add_user_message(UserMessage(message=...))`
6. **Execute**: `await agent.monologue()` — runs to completion or timeout
7. **Collect result**: Capture monologue output, seal topic
8. **Persist**: Call `save_tmp_chat(worker_ctx)` to persist context for debugging. Use `AgentContextType.TASK` (not `BACKGROUND` which skips persistence per `helpers/persist_chat.py:47-49`)

### Timeout handling

Per-worker timeout via `asyncio.wait_for(coro, timeout=seconds)`:
- Default: 300 seconds (5 minutes)
- On timeout: `asyncio.TimeoutError` → status="fail", error="Timeout after {N}s"
- Other exceptions: caught → status="fail", error=str(exception)

### Logging

Each worker should log to its own context's log. The parent tool logs a summary:
- Start: "Launching N parallel subordinates: [profiles]"
- Complete: "N/M subordinates completed successfully"
- Each worker's individual logs are visible in their dedicated context

## Testing Strategy

**Framework:** pytest (existing in plugin)

**Test file:** `tests/test_call_subordinate_parallel.py`

### Test levels

1. **Unit tests** (mocked — no real LLM calls):
   - Task parsing: valid input, invalid input, empty list, missing message
   - Worker creation: dedicated context, profile override, agent config
   - Result formatting: success case, failure case, timeout case, mixed
   - Result ordering: "input" order vs "completion" order

2. **Integration tests** (live agent, mocked monologue):
   - asyncio.gather runs N workers concurrently
   - Partial results: one worker fails, others succeed
   - Timeout: worker exceeds timeout, returns error
   - Cleanup: no leaked contexts after execution

3. **Manual verification**:
   - `/ship` command uses the new tool
   - Three specialist reviews run in parallel
   - Results merge correctly in final GO/NO-GO decision

### Coverage expectations
- Core logic (parse, gather, format) → >90%
- Error paths → all branches covered
- Edge cases → empty tasks, single task, all-fail, all-succeed

## Boundaries

- **Always do:**
  - Validate task input before creating workers
  - Use dedicated `AgentContext` per worker (never shared)
  - Return partial results on failure (never silently drop a worker)
  - Include duration_ms and order in every result
  - Follow existing `call_subordinate.py` conventions
  - Run existing tests before committing

- **Ask first:**
  - Adding new dependencies
  - Changing the tool API signature
  - Persisting worker contexts beyond the fan-out scope
  - Adding shared mutable state between workers

- **Never do:**
  - Modify any core framework files (`/a0/tools/`, `/a0/agent.py`, `/a0/helpers/`)
  - Share `AgentContext` between parallel workers
  - Add blocking/synchronous operations in the async path
  - Commit without tests
  - Hardcode profile names or task counts in the tool

## Success Criteria

- [ ] `call_subordinate_parallel` tool is discovered and invocable by the agent
- [ ] Accepts list of `{message, profile}` tasks
- [ ] Runs N workers concurrently via `asyncio.as_completed` (for progress reporting)
- [ ] Each worker has isolated `AgentContext` (shared workspace, separate reasoning)
- [ ] Returns structured results list with status/duration per worker
- [ ] Handles timeouts and exceptions gracefully (partial results)
- [ ] `/ship` command updated to use the new tool
- [ ] Unit tests pass with >90% coverage on core logic
- [ ] Zero modifications to core framework files
- [ ] No new dependencies

## Resolved Questions (verified against codebase)

### Q1: Context persistence — YES, persist for debugging

Workers should use `type=AgentContextType.TASK` (not `BACKGROUND` — which skips persistence per `helpers/persist_chat.py:47-49`). After a worker completes, call `save_tmp_chat(worker_ctx)` to enable inspection. This mirrors the scheduler pattern.

### Q2: Progress callbacks — YES, via parent tool `set_progress()`

The parent tool instance (`self`) persists throughout the entire fan-out. Use `asyncio.as_completed()` instead of `asyncio.gather()` so workers are collected as they finish. After each worker completes, call `await self.set_progress(f"Worker {i}/{n} completed ({profile})")` — this fires `tool_output_update` on the **parent** agent (`helpers/tool.py:32-35`), updating the UI in real-time. No cross-agent mechanism needed — progress reporting is a parent-side operation.

### Q3: Max concurrency — implement `asyncio.Semaphore` in the tool

No built-in concurrency limiter in the framework. The tool should accept an optional `max_concurrency` parameter (default: unlimited) and wrap worker execution with `asyncio.Semaphore` when set. This protects against resource exhaustion when many tasks are submitted.

## References

- **Confirmed intent:** `docs/intent/parallel-subordinate-execution.md`
- **Validated research:** `docs/specs/parallel-subordinate-execution.md`
- **Existing subordinate tool:** `/a0/tools/call_subordinate.py` (55 lines)
- **Scheduler context creation:** `/a0/helpers/task_scheduler.py:822-838`
- **Plugin tool examples:** `/a0/plugins/_browser/tools/`, `/a0/plugins/_memory/tools/`
- **Tool base class:** `/a0/helpers/tool.py`
- **Agent class:** `/a0/agent.py` (Agent, AgentContext, AgentConfig)
