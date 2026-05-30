# Agent Zero Subordinate Orchestration And Parallelization

This page documents the current subordinate model in Agent Zero, the existing task and scheduler foundation around it, and how future parallelization work should build on both.

Code citations reference the live codebase under `/a0`.

## Why this matters

Agent Zero already has a real delegation model. Future work on multi-agent orchestration or parallel subordinate execution should start from the existing subordinate architecture rather than inventing a separate unrelated mechanism.

This is especially important for high-context work such as:
- architecture research
- code audits
- split implementation tasks
- review passes
- future parallel task execution

## Harness context — what you are developing inside

Before working on orchestration or parallelization, understand the runtime you are developing inside:

### The monologue loop is the primary runtime

The real execution center is `Agent.monologue()` + `prepare_prompt()` + tool processing, not the subordinate tool by itself.

- `agent.py:373-512` — the monologue loop
- `agent.py:538-591` — prompt preparation

### Prompt assembly is extension-driven and rebuilt every iteration

Main prompt, tools prompt, skills prompt, project prompt, and promptinclude are composed through `system_prompt` extensions:

- `agent.py:634-639` — extension point call
- `helpers/extension.py:223-246` — extension mechanism
- `extensions/python/system_prompt/_10_main_prompt.py` — main prompt
- `extensions/python/system_prompt/_11_tools_prompt.py` — tools prompt
- `extensions/python/system_prompt/_13_skills_prompt.py` — skills prompt
- `extensions/python/system_prompt/_14_project_prompt.py` — project prompt
- `plugins/_promptinclude/extensions/python/system_prompt/_16_promptinclude.py` — promptinclude

Future parallelization must fit this extension-driven runtime, not bypass it.

### Two orchestration layers already exist

1. **Synchronous nested delegation**: `call_subordinate` — awaited inline delegation
2. **Persisted/background task execution**: `scheduler` + `TaskScheduler` + `job_loop` — background agent-context execution

Future parallelization should say how it composes with both, rather than only treating one as the orchestration layer.

---

## Proposed direction: tasks as the default container for concrete work

> **Note**: This section describes a proposed future direction, not the current system behavior.

For concrete project work, Agent Zero should not jump straight from chat intent into one long monologue when there is clear todo.

If there is real todo — multiple steps, implementation slices, review items, verification passes, or independent work items — the work should be represented as tasks.

This does not mean everything should run in parallel. It means taskification should come first. Parallelism is then an execution mode for tasks, not a separate planning model.

Proposed stance:
- if there is todo, make tasks
- let the orchestrator own task creation, ordering, and completion
- use scheduler-backed or background execution when tasks need to outlive one monologue or run concurrently
- subordinate agents become workers that execute tasks

**Current reality**: The main runtime does not auto-taskify. The default problem-solving prompt says "solve or delegate" via tools/subordinates. Tasks are explicit scheduler records created only when the `scheduler` tool is used. (`agent.py:373-512`, `prompts/agent.system.main.solving.md:11-20`)

---

## Current subordinate model

Subordinate execution is currently centered on the `call_subordinate` tool.

At a high level:
- the superior agent requests subordinate work
- a new subordinate agent is created when needed
- a profile override can be applied
- the subordinate receives a user-style task message
- the subordinate runs its own monologue
- the result is returned to the superior
- the subordinate topic is sealed after completion

Code: `tools/call_subordinate.py:9-47`

## What `call_subordinate` actually does

Important behaviors of the current implementation:
- reuses an existing subordinate unless reset is requested or none exists yet (`call_subordinate.py:11-14`)
- creates the subordinate with the same context object but a separate agent instance (primary: `call_subordinate.py:24`, constructor: `agent.py:351-359`)
- can switch the subordinate's profile before creation (`call_subordinate.py:18-22`)
- stores superior and subordinate links in live agent data, not an external registry (`call_subordinate.py:25-27`, `agent.py:659-663`)
- appends a user message to the subordinate history (`call_subordinate.py:29-31`)
- runs subordinate monologue to completion, awaited inline (`call_subordinate.py:33-35`)
- returns the subordinate result without breaking the parent's loop (`call_subordinate.py:47`)

Development implication:
- today's delegation is a nested execution pattern, not a fire-and-forget task graph

## Subordinate isolation

Subordinates isolate reasoning history, but **not the full context**.

**History-isolated, context-shared.**

The subordinate gets a separate `Agent` instance with its own `history` and `data`, but shares the parent's `AgentContext`. This means:
- the parent agent can keep a cleaner history
- the subordinate can work within a narrower task boundary
- profile specialization can be applied per delegated task
- the subordinate's current topic is explicitly sealed after completion (`call_subordinate.py:36-37`; sealing action: `helpers/history.py:343-346`; Topic class: `helpers/history.py:136-164`)

**Critical for future parallelism**: shared `AgentContext` means true parallel subordinate execution would need careful handling around shared context state/logging, even if histories remain separate. (`call_subordinate.py:24`, `agent.py:358-368`)

## Profiles and path resolution

Subordinates are not only new agents; they can also use profile-specific prompt behavior.

Agent/profile data is layered across:
- default built-in agent definitions
- plugin-contributed agents
- user agents
- project agents

Two separate mechanisms operate here:

1. **Agent metadata/prompt merge**: `load_agent_data` / `_merge_agents` merges dictionaries across layers. (`helpers/subagents.py:113-155`, `helpers/subagents.py:224-241`)

2. **Runtime prompt/tool lookup**: `get_paths` searches in order: project agent profile → project `.a0proj` → user agent profile → plugin agent profile → default agent profile → `usr/` → enabled plugins → default root. Uses search-path precedence, not a generic deep merge of prompt text. (`helpers/subagents.py:339-432`, `agent.py:651-657`)

Development implication:
- future multi-agent orchestration should preserve this layered agent-definition model rather than bypassing it with hard-coded role logic

## What is already supported

The current subordinate model already supports:
- scoped delegation
- role specialization by profile
- isolated histories (separate `Agent.history`, not separate `AgentContext`)
- chained/recursive delegation (not visibly blocked in the inspected path)
- superior/subordinate linkage (in live agent data)
- iterative use of the same subordinate until reset

That means future parallelization does not need to start from zero. It should start from the existing delegation semantics and execution contracts.

## What is not yet a first-class parallel runtime

The current model is still primarily sequential from the superior's point of view.

Notably:
- subordinate execution is awaited to completion in the current call path
- the parent stores a single `_subordinate` pointer, not a list/pool (`agent.py:346-348`)
- there is no first-class built-in fan-out or fan-in orchestration primitive in the subordinate tool path

This is scoped to the subordinate tool path. The broader harness already has a generic background concurrency substrate:

- **Scheduler tasks** are persisted records that run in background `DeferredTask` threads (`helpers/task_scheduler.py:755-758`, `helpers/task_scheduler.py:865-1020`)
- **Job loop** launches due tasks every ~60 seconds (`helpers/job_loop.py:16-45`, `initialize.py:64-67`)
- Multiple scheduler tasks can overlap because each runs in its own `DeferredTask`

## Scheduler today

The scheduler is a real persisted subsystem, not just a concept:

- tasks are persisted in `usr/scheduler/tasks.json` (`helpers/task_scheduler.py:519-579`)
- tasks carry `context_id`, `state`, `last_result`, and by default use a dedicated context
- `_run_task` creates an `AgentContext`, gets `context.agent0`, injects a user message, and runs `agent.monologue()` directly — it does **not** invoke `call_subordinate` (`helpers/task_scheduler.py:822-838`, `helpers/task_scheduler.py:840-960`, `helpers/task_scheduler.py:1013-1020`)
- `wait_for_task` only works for dedicated contexts (`tools/scheduler.py:399-431`)
- scheduler use is opt-in via the `scheduler` tool, not the default chat container

**Key fact**: scheduler tasks currently run standard `agent0` conversations, not subordinate workers. A future parallel fan-out design should explicitly decide how it relates to this existing substrate.

## Good starting points for future task-backed parallelization work

If implementing parallel subordinate work, inspect these first:

**Subordinate path:**
- `tools/call_subordinate.py`
- `helpers/subagents.py`
- `agent.py`
- prompt rules related to delegation in `prompts/agent.system.main.solving.md`

**Scheduler/task path:**
- `helpers/task_scheduler.py`
- `tools/scheduler.py`
- `helpers/job_loop.py`
- `initialize.py` (startup wiring for job loop)

**Harness composition:**
- `helpers/extension.py` — extension mechanism
- `extensions/python/system_prompt/_10_main_prompt.py`
- `extensions/python/system_prompt/_11_tools_prompt.py`
- `extensions/python/system_prompt/_13_skills_prompt.py`
- `extensions/python/system_prompt/_14_project_prompt.py`
- `plugins/_promptinclude/extensions/python/system_prompt/_16_promptinclude.py`

Key design question:
- how should task creation, scheduling, and subordinate execution fit together so that tasks become the default unit of concrete work?

Proposed default: use tasks as the orchestration layer and subordinate agents as task workers, rather than inventing a separate parallel-only abstraction. This is a design recommendation, not a description of the current codebase.

## Validation appendix

Research validated against live codebase on 2026-05-28. Results:

- **24 claims fully confirmed** — all behavioral descriptions match the codebase
- **0 factually incorrect** — no errors found
- **2 range imprecisions** — fixed above (history.py sealing range, agent.py cite precision)

### Additional findings from validation

1. **AgentContextType enum** (`agent.py:36-39`): Context types are `USER`, `TASK`, `BACKGROUND` — relevant for typing parallel worker contexts (should use `TASK`)

2. **_run_task reuses streaming_agent** (`task_scheduler.py:907`): If a context was previously used, it may reuse its last active agent rather than always creating fresh. Parallel workers should use fresh contexts to avoid this.

3. **context_id defaults to task uuid** (`task_scheduler.py:179-180`): Every task automatically gets `context_id = self.uuid` in `__init__`, making `is_dedicated()` return True by default. Confirms the scheduler's dedicated-context-by-default pattern.

4. **100ms yield after DeferredTask start** (`task_scheduler.py:1020`): After starting a DeferredTask, the scheduler yields briefly via `asyncio.sleep(0.1)`. Relevant for parallel launching — there's an intentional 100ms yield to let the thread spin up.

5. **Development mode pauses job loop** (`job_loop.py:20-26`): The job loop pauses itself if running in development mode. Relevant for testing parallel execution during development.

6. **call_subordinate has a file-saving hint** (`call_subordinate.py:39-44`): When result length exceeds `save_tool_call_file.LEN_MIN`, it reads and attaches a hint prompt (`fw.hint.call_sub.md`) suggesting use of `§§include()`. The parallel tool should replicate this optimization.

7. **Plugin tool registration confirmed**: Plugins register tools by placing Python files in their `tools/` directory. Verified in `_browser/tools/browser.py`, `_office/tools/office_artifact.py`, `_memory/tools/memory_*.py`.

## Design constraints future work should respect

> **Note**: These are recommended design principles for future work, not descriptions of current behavior.

### Preserve reasoning isolation

Parallel work is only valuable if each subordinate still has an isolated task boundary and history. Remember: current isolation is history-level (`Agent`), not context-level (`AgentContext`).

### Preserve explicit orchestration ownership

A superior agent, planner, or orchestration layer should own:
- spawning
- task partitioning
- result aggregation
- failure handling
- cancellation or timeout handling

### Preserve profile specialization

Parallel subordinates should still be able to run under different profiles where appropriate.

### Preserve durable auditability

If parallel orchestration becomes more complex, result aggregation and traceability will matter more, not less.

### Avoid prompt-only orchestration hacks

A real parallelization feature should not rely only on prompt instructions pretending concurrency exists. It should have real runtime support where needed.

## Integration options for future parallelization

> **Note**: These are design options, not implemented features.

Potential directions include:
- extending `call_subordinate` with orchestration-aware modes
- introducing a higher-level orchestration tool that still creates normal subordinate agents underneath
- using background task scheduling for long-running subordinate work where appropriate
- adding result aggregation contracts or shared task metadata for multi-subordinate runs

The current harness already has waiting and result retrieval contracts at the task layer (`wait_for_task`, `state`, `last_result`, `context_id`) that are directly relevant to any future fan-in design. (`tools/scheduler.py:399-431`, `helpers/task_scheduler.py:162-176`)

Any of these approaches should still respect existing subordinate creation, profile selection, and history boundaries.

## Task-first stance for future work

> **Note**: This is a proposed policy, not current system behavior.

Future work should keep the policy simple:
- when there is todo, create tasks
- tasks may execute sequentially or in parallel, but the task layer comes first
- parallelization should improve how tasks are dispatched, monitored, and merged rather than encouraging ad hoc fan-out from the main agent loop
- task state, progress, partial results, failure handling, and cancellation should live in the task and scheduler layer where possible
- the orchestrator should remain responsible for final synthesis and user-facing completion

**Current task data model**: tasks expose `state`, `last_run`, `last_result`, `context_id`, plus the persisted chat/log context. Partial results and progress tracking are not yet first-class task features. (`helpers/task_scheduler.py:162-176`, `helpers/task_scheduler.py:249-279`, `helpers/task_scheduler.py:973-1015`)

## Recommended development stance

When designing a parallelization feature for Agent Zero:
- use tasks whenever concrete project work has real todo (proposed direction)
- treat parallel execution as a task-execution capability, not a separate planning model
- treat current subordinate execution as the baseline abstraction
- integrate with scheduler-backed task infrastructure instead of bypassing it
- preserve profile layering and path resolution
- preserve auditability and context separation
- avoid inventing a second unrelated agent system
- add orchestration features in a way that future agents can reason about from the existing code structure

## Good starting files for future agents

- `tools/call_subordinate.py`
- `helpers/subagents.py`
- `agent.py`
- `helpers/task_scheduler.py`
- `tools/scheduler.py`
- `helpers/job_loop.py`
- `initialize.py`
- `helpers/extension.py`
- `prompts/agent.system.main.solving.md`
- `extensions/python/system_prompt/_10_main_prompt.py`
- `extensions/python/system_prompt/_11_tools_prompt.py`
- `plugins/_promptinclude/extensions/python/system_prompt/_16_promptinclude.py`

This is the current architectural foundation for subordinate orchestration. Future parallel work should evolve this model into a task-first orchestration system, not replace it with a separate mechanism built in ignorance of it.
