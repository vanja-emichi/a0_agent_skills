# Intent: Parallel Subordinate Execution

> Confirmed via interview-me on 2026-05-28

## Confirmed Intent

- **Outcome:** A new `call_subordinate_parallel` tool in the `a0_agent_skills` plugin, enabling N subordinate agents to run concurrently via `asyncio.gather` with shared workspace (filesystem) and isolated reasoning/history per worker
- **User:** The `a0_agent_skills` plugin — specifically `/ship` command (parallel code-reviewer + security-auditor + test-engineer fan-out) and future BUILD-phase `todo.md` parallel item processing
- **Why now:** `/ship` currently runs 3 specialist reviews sequentially; real parallelism is the missing capability for production-quality orchestration
- **Success:** Tool accepts a list of `{message, profile}` tasks, runs them concurrently, returns `[{profile, result, status}, ...]` — orchestrator merges results
- **Constraint:** Plugin-only — no core file modifications; uses existing `AgentContext`, `Agent`, `initialize_agent()` APIs; dedicated context per worker (like scheduler tasks)
- **Out of scope:** Changing existing `call_subordinate`, modifying the scheduler subsystem, adding shared mutable agent state, building a separate orchestration layer

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Execution model | `asyncio.gather`-style fan-out | Fits existing async monologue loop; simplest concurrency model |
| State sharing | Shared workspace, isolated reasoning | Codex/Devin model; workers share filesystem but have own context/history |
| Context per worker | Dedicated `AgentContext` (like scheduler `_run_task`) | Proven pattern; avoids shared mutable state issues |
| Error semantics | Partial results — return all, mark failures with error info | Orchestrator decides whether a single failure blocks the whole operation |
| Tool placement | Plugin `tools/` directory | Agent Zero plugins can register tools (proven by `_browser`, `_office`, `_memory`) |
| Tool API | New tool, not extending existing `call_subordinate` | Cleaner separation; no risk of breaking existing delegation |
| Fan-in merge | Raw results list — caller merges | Keeps tool simple; intelligence lives in orchestrator (e.g., `/ship` prompt) |
| Concurrency limit | No hard limit in tool; caller's responsibility | `/ship` always fans out 3; BUILD phase would be 2-5 |
| Command integration | `/ship` prompt instructs main agent to call `call_subordinate_parallel` | Same pattern as today — commands are prompt generators |

## Research Foundation

See: `docs/specs/parallel-subordinate-execution.md` — architectural research on Agent Zero's current subordinate and scheduler model.

## Key Code References

| Component | Location | Notes |
|---|---|---|
| Current subordinate tool | `/a0/tools/call_subordinate.py` (55 lines) | Single subordinate, awaited inline |
| Agent class | `/a0/agent.py` | `Agent`, `AgentContext`, `AgentConfig`, monologue loop |
| Scheduler task execution | `/a0/helpers/task_scheduler.py:822-960` | Dedicated context pattern to replicate |
| Plugin tool examples | `/a0/plugins/_browser/tools/`, `/a0/plugins/_office/tools/` | Proves plugins can register tools |
| DeferredTask | `/a0/helpers/` | Already handles async execution |

## Downstream

- **Next skill:** `spec-driven-development` — write implementation spec from this intent
- **Then:** `planning-and-task-breakdown` → `incremental-implementation` → `test-driven-development`
