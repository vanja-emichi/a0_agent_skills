# Spec: Durable Workflow State

*Phase 2 / Slice 2 of the `a0_agent_skills` workflow-governance roadmap.*
*Date: 2026-05-30*

> **Status in broader roadmap:** This document defines **Phase 2 / Slice 2** of the larger `a0_agent_skills` workflow-governance roadmap.
> The primary long-range roadmap documents are:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Assumptions

1. This slice lives entirely in `a0_agent_skills` (user-space plugin); no edits to `/a0/agent.py`, `models.py`, `history.py`, or any core framework module.
2. State artifacts live in **`.a0proj/state/`** — project-scoped, never global.
3. The existing enforcement gate (Slice 1) is complete and stable: 389 tests passing, observe-first default.
4. The workflow-state helper is a new module (`helpers/workflow_state.py`) that owns all read/write to `.a0proj/state/` — extensions never touch state files directly.
5. State file format: **JSON** for snapshot files, **JSONL** for append-only logs.
6. Rehydration uses the `message_loop_prompts_after` extension hook — it appends context lines after prompt assembly so the agent sees prior workflow state after compaction or session resume.
7. Progress logging is append-only — entries are never mutated or deleted.
8. Checkpoints are mutable snapshot artifacts — they are overwritten, not appended.
9. The handoff artifact (`handoff.md`) is human-readable Markdown, not JSON — it serves as an operator-facing summary.
10. All imports of plugin helpers from extensions use the `importlib` / direct-import pattern established in Slice 1 (e.g., `from helpers.skills import ...`, `from helpers.workflow_state import ...`).
11. Path resolution for `.a0proj/state/` follows the same project-folder resolution pattern as telemetry (using `helpers.projects.get_context_project_name` + `get_project_folder`).

## Objective

Give the plugin **durable memory of active workflow state** so that long-running engineering work survives context compaction, session breaks, and agent restarts.

Specifically, this slice ensures:

- The agent's active **plan, goal, phase, and loaded skills** are persisted to `.a0proj/state/` after every relevant change.
- After compaction or session resume, a `message_loop_prompts_after` extension **reattaches** these state artifacts into the agent's context so work continues without manual re-priming.
- An **append-only progress log** records every significant workflow event durably.
- Explicit **checkpoints** capture milestones for handoff or rollback.

**Users:** (a) the maintainer running their own A0 instance; (b) the community installing the distributable plugin; (c) future agents resuming long-running project work.

**Success looks like:** the agent can lose its entire conversation history, start a fresh loop iteration, and still know what phase it is in, what plan it is executing, what goal it is pursuing, what skills it had loaded, and what progress has been made — all reconstructed from `.a0proj/state/` files rather than from prompt-only context.

## Tech Stack

- Python 3.11+
- Agent Zero plugin extension system (`helpers.extension.Extension`)
- Existing `helpers.skills` API (`get_loaded_skill_entries`, `search_skills`)
- Existing `helpers.projects` API (`get_context_project_name`, `get_project_folder`)
- Existing `helpers.plugins` API (`get_plugin_config`)
- Project-scoped persistence in `.a0proj/state/`
- JSON for snapshot state files, JSONL for append-only progress log
- Markdown for human-readable handoff artifact
- pytest for verification

## Commands

```
Test (all):        cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short
Test (one):        python -m pytest tests/test_workflow_state.py -v
Test (rehydrate):  python -m pytest tests/test_workflow_rehydrate.py -v
Parity report:     python scripts/parity_report.py
```

## State File Schema

All state files live under `.a0proj/state/` relative to the project folder. Each file is created lazily — it exists only after the first write.

### `active_plan.json`

> **Note (two-store model):** `plan_path` is owned by `workflow_artifacts.json`, not this file.
> See ADR-007 (`docs/adrs/007-artifact-path-resolution.md`) for the rationale.

```json
{
  "version": 1,
  "updated_at": 1234567890.0,
  "plan_name": "durable-workflow-state",
  "slug": "durable-workflow-state",
  "current_task": "Task 2: Add workflow-state helper",
  "tasks_total": 3,
  "tasks_completed": 0
}
```

### `active_goal.json`

```json
{
  "version": 1,
  "updated_at": 1234567890.0,
  "goal": "Persist workflow state durably across compaction and session breaks",
  "source": "user message or slash command"
}
```

### `current_phase.json`

```json
{
  "version": 1,
  "updated_at": 1234567890.0,
  "phase": "BUILD",
  "phases_completed": ["DEFINE", "PLAN"],
  "entered_at": 1234567890.0
}
```

Valid phases: `DEFINE`, `PLAN`, `BUILD`, `VERIFY`, `REVIEW`, `SHIP`.

### `loaded_skills.json`

```json
{
  "version": 1,
  "updated_at": 1234567890.0,
  "skills": [
    {
      "name": "incremental-implementation",
      "loaded_at": 1234567890.0
    },
    {
      "name": "test-driven-development",
      "loaded_at": 1234567891.0
    }
  ]
}
```

### `checkpoints.json`

```json
{
  "version": 1,
  "updated_at": 1234567890.0,
  "checkpoints": [
    {
      "id": "cp-001",
      "label": "Helper module complete",
      "created_at": 1234567890.0,
      "phase": "BUILD",
      "task": "Task 2",
      "notes": "All CRUD operations and tests passing"
    }
  ]
}
```

### `progress_log.jsonl`

Append-only. Each line is a self-contained JSON event:

```jsonl
{"ts":1234567890.0,"event":"phase_change","from":"DEFINE","to":"PLAN"}
{"ts":1234567891.0,"event":"skill_loaded","skill":"incremental-implementation"}
{"ts":1234567892.0,"event":"task_started","task":"Task 2: Add workflow-state helper"}
{"ts":1234567893.0,"event":"checkpoint","checkpoint_id":"cp-001","label":"Helper module complete"}
{"ts":1234567894.0,"event":"task_completed","task":"Task 2: Add workflow-state helper"}
```

Event types: `phase_change`, `skill_loaded`, `skill_unloaded`, `task_started`, `task_completed`, `checkpoint`, `goal_set`, `plan_set`, `custom`.

### `handoff.md`

Human-readable Markdown summarizing current workflow state. Not machine-parsed — intended for operator review or cross-agent handoff.

```markdown
# Workflow Handoff

**Project:** a0_agent_skills
**Phase:** BUILD
**Goal:** Persist workflow state durably across compaction and session breaks
**Plan:** docs/plans/durable-workflow-state-plan.md
**Current Task:** Task 2: Add workflow-state helper
**Loaded Skills:** incremental-implementation, test-driven-development
**Last Checkpoint:** cp-001 — Helper module complete
**Updated:** 2026-05-30T09:00:00Z
```

## Extension Points

### Where state is saved (write paths)

| Hook | Extension | What it persists |
|------|-----------|-----------------|
| `tool_execute_after` | `_05_skill_telemetry.py` (extend) | `loaded_skills.json` — after every `skills_tool:load` call |
| `tool_execute_after` | `_10_persist_workflow_state.py` (new) | `active_plan.json`, `active_goal.json`, `current_phase.json` — after every target tool call when state has changed |
| `tool_execute_after` | `_10_persist_workflow_state.py` (new) | `progress_log.jsonl` — appends events as they happen |
| `tool_execute_after` | `_10_persist_workflow_state.py` (new) | `checkpoints.json` — after checkpoint create/update |
| `tool_execute_after` | `_10_persist_workflow_state.py` (new) | `handoff.md` — after any state file update |

### Where state is rehydrated (read path)

| Hook | Extension | What it reattaches |
|------|-----------|-------------------|
| `message_loop_prompts_after` | `_67_reattach_workflow_state.py` (new) | Reads all `.a0proj/state/` files and appends a consolidated context block to the assembled prompt so the agent sees its prior state |

### When rehydration fires

- Every message loop iteration (but only appends content when state files exist).
- Most impactful after compaction (history truncated) or session resume (fresh agent context).

## What Gets Persisted

| Artifact | Trigger | Format |
|----------|---------|--------|
| Active plan | Plan created or task status changes | JSON snapshot |
| Active goal | Goal set or updated | JSON snapshot |
| Current phase | Phase transition | JSON snapshot |
| Loaded skills | `skills_tool:load` call completes | JSON snapshot |
| Checkpoints | Explicit checkpoint creation/update | JSON snapshot |
| Progress log | Any tracked event | JSONL append |
| Handoff | Any state change | Markdown overwrite |

## What Gets Rehydrated

| Artifact | Rehydrated as | Consumed by |
|----------|---------------|-------------|
| `active_plan.json` | Context line in `message_loop_prompts_after` | Agent loop — sees current plan |
| `active_goal.json` | Context line in `message_loop_prompts_after` | Agent loop — sees current goal |
| `current_phase.json` | Context line in `message_loop_prompts_after` | Agent loop + enforcer — knows current phase |
| `loaded_skills.json` | Context line + `agent.data['loaded_skills']` update | Agent loop — knows what skills are active |
| `checkpoints.json` | Context line in `message_loop_prompts_after` | Agent loop — knows milestones |
| `progress_log.jsonl` | Not rehydrated (log only) | Operator / debugging |
| `handoff.md` | Not rehydrated (operator artifact) | Operator / cross-agent handoff |

## Project Structure

```
helpers/workflow_state.py                                              ← NEW: state CRUD helper
extensions/python/tool_execute_after/_10_persist_workflow_state.py     ← NEW: persist extension
extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py  ← NEW: rehydrate extension

tests/test_workflow_state.py                                           ← NEW: helper unit tests
tests/test_workflow_rehydrate.py                                        ← NEW: rehydration tests
tests/test_persist_workflow_state.py                                    ← NEW: persist extension tests
```

## Code Style

Follow Slice 1 patterns exactly:

- Top-level fail-safe `try/except` in all extensions — never break the agent loop.
- Config access via `helpers.plugins.get_plugin_config("a0_agent_skills", agent=agent)`.
- Lazy imports of plugin helpers to reduce unnecessary coupling.
- The workflow-state helper is the **sole owner** of `.a0proj/state/` I/O — extensions call the helper, never write state files directly.
- Path resolution uses the same `_resolve_log_path` / project-folder pattern as telemetry.

```python
# Extension pattern (from Slice 1)
class PersistWorkflowState(Extension):
    async def execute(self, tool_name=None, tool_args=None, response=None, **kwargs):
        try:
            from helpers.workflow_state import (
                save_active_plan,
                save_loaded_skills,
                append_progress_event,
            )
            # ... persist logic ...
        except Exception:
            pass  # never break the loop
```

```python
# Rehydrate extension pattern
class ReattachWorkflowState(Extension):
    async def execute(self, prompt, **kwargs):
        try:
            from helpers.workflow_state import read_all_state
            state = read_all_state(self.agent)
            if state:
                return {"prompt": prompt + format_state_block(state)}
            return {"prompt": prompt}
        except Exception:
            return {"prompt": prompt}  # never break prompt assembly
```

## Testing Strategy

### Unit tests (`test_workflow_state.py`)
- Read/write for each state artifact type (plan, goal, phase, loaded skills, checkpoints, progress log, handoff)
- Missing state files handled safely (returns empty/default, never raises)
- Corrupt state files handled safely (logged, returns empty/default)
- Path traversal prevention (state files cannot escape `.a0proj/state/`)
- Append-only guarantee for progress log (no mutation of existing entries)
- JSONL line format is valid JSON
- Handoff markdown is well-formed

### Persist extension tests (`test_persist_workflow_state.py`)
- Extension fires after target tool calls and writes state
- Extension no-ops for non-relevant tool calls
- Extension does not break when project folder is missing
- Extension does not break when state directory is missing
- State is written after `skills_tool:load` (loaded skills update)
- Progress events are appended correctly

### Rehydrate extension tests (`test_workflow_rehydrate.py`)
- Extension appends state context when state files exist
- Extension returns unmodified prompt when no state files exist
- Extension returns unmodified prompt on any error
- Rehydrated loaded skills are injected into `agent.data['loaded_skills']`
- Rehydrated content is human-readable and includes plan, goal, phase

### Integration considerations
- Rehydration produces output that the enforcement gate (Slice 1) can consume — specifically, `loaded_skills.json` must be compatible with `skill_match.get_loaded_skills()`.
- State written by the persist extension must be readable by the rehydrate extension without coupling to agent internals beyond documented APIs.

## Boundaries

### Always
- Wrap all extension bodies in try/except — state persistence failures must not break the agent loop.
- Create `.a0proj/state/` directory lazily — only when the first write occurs.
- Handle missing state files with safe defaults (return empty, never raise).
- Use JSON for snapshot files, JSONL for append-only logs.
- Keep the handoff artifact as human-readable Markdown.
- All state I/O goes through the workflow-state helper — no direct file writes from extensions.

### Ask first
- Changing the state file schema (additive-only is safe; removal or rename needs coordination).
- Adding new event types to the progress log (additive, but should be documented).
- Making rehydration conditional on phase or task state.

### Never
- Edit core framework files.
- Store state outside `.a0proj/state/`.
- Use `nudge()` or raise `InterventionException` in state extensions.
- Mutate existing progress log entries (append-only).
- Fall back to a global state directory if the project folder is unavailable.
- Couple state persistence to `_permissions` or `_tracing`.

## Success Criteria (testable)

1. The workflow-state helper can read and write all 7 state artifact types (`active_plan`, `active_goal`, `current_phase`, `loaded_skills`, `checkpoints`, `progress_log`, `handoff`).
2. Missing state files return safe defaults — no exceptions propagate to the agent loop.
3. The persist extension writes `loaded_skills.json` after every `skills_tool:load` call.
4. The persist extension appends progress events to `progress_log.jsonl` for tracked events.
5. The rehydrate extension appends a consolidated state block to the prompt when state files exist.
6. The rehydrate extension returns an unmodified prompt when no state files exist.
7. After simulating compaction (clearing agent history), the rehydrate extension restores plan, goal, phase, and loaded-skills awareness.
8. All state paths are validated to remain within `.a0proj/state/` — no path traversal.
9. Full pytest suite remains green (389 Slice 1 tests + new Slice 2 tests).
10. No core framework edits required.

## Open Questions

1. **Progress event granularity:** Should the persist extension log every tool call, or only tracked workflow events (phase change, skill load, task start/complete, checkpoint)? Current design: tracked events only — keeps the log meaningful without flooding.
2. **State file rotation:** Should `progress_log.jsonl` rotate after a configurable line count (like `telemetry_max_lines`)? Current design: no rotation in MVP — additive for future config.
3. **Rehydration freshness:** Should the rehydrate extension skip state older than a configurable TTL? Current design: no TTL — all state is considered valid until overwritten.
