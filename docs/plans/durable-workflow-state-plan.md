# Implementation Plan: Durable Workflow State

> Generated from spec `docs/specs/durable-workflow-state-spec.md`.
>
> **Status in broader roadmap:** This is the **Phase 2 / Slice 2** implementation plan under the umbrella workflow-governance roadmap.
> For the broader roadmap, see:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Overview

This plan implements **durable workflow state** for `a0_agent_skills`, ensuring that active workflow context (plan, goal, phase, loaded skills, checkpoints, progress) survives context compaction, session breaks, and agent restarts.

The feature has three interdependent components:

1. **Workflow-state helper** — a dedicated module that owns all read/write to `.a0proj/state/` artifacts.
2. **Persist and rehydrate** — extensions that save state after relevant tool calls and reattach it during prompt assembly.
3. **Progress log and checkpoints** — append-only progress logging and mutable checkpoint artifacts.

The implementation follows the same principles as Slice 1:

1. **User-space only** — all implementation lives in `/a0/usr/plugins/a0_agent_skills`; no core framework edits.
2. **Fail-safe extensions** — all extension bodies wrapped in try/except; state failures never break the agent loop.
3. **Lazy state creation** — `.a0proj/state/` and its files are created only when the first write occurs.
4. **Measure everything** — focused tests for every new behavior before broad rollout.

## Architecture Decisions

- **Single helper ownership:** `helpers/workflow_state.py` is the sole module that reads/writes `.a0proj/state/`. Extensions call helper functions; they never touch state files directly.
- **JSON for snapshots, JSONL for logs:** Snapshot files (`active_plan.json`, `active_goal.json`, `current_phase.json`, `loaded_skills.json`, `checkpoints.json`) are fully overwritten on update. Progress log (`progress_log.jsonl`) is append-only.
- **Rehydration via `message_loop_prompts_after`:** The `_67_reattach_workflow_state.py` extension fires during prompt assembly and appends a consolidated state block when state files exist.
- **No TTL, no rotation in MVP:** State is always considered valid; progress log does not rotate.
- **Compatible with enforcement gate:** `loaded_skills.json` must be compatible with `skill_match.get_loaded_skills()` so the Slice 1 gate can use rehydrated skill state.
- **Handoff as Markdown:** `handoff.md` is a human-readable summary, not machine-parsed.

## Dependency Graph

```text
Slice 1 complete (389 tests passing)
   │
   ├── Task 1: Workflow-state helper + schema
   │       │
   │       ├── Task 2: Persist extension
   │       │       │
   │       │       └── Task 3: Rehydrate extension
   │       │               │
   │       │               └── Integration verification
   │       │
   │       └── Task 4: Progress log + checkpoints
   │               │
   │               └── Task 5: Config surface + documentation
   │
   └── Full regression verification
```

## Task List

### Phase 1: Workflow-State Helper

## Task 1: Create `helpers/workflow_state.py` with state file schema

**Description:**
Build the core helper module that owns all `.a0proj/state/` I/O. This module provides functions to read and write each state artifact type, resolve the state directory path, and handle missing/corrupt files safely. No extensions are built in this task — only the helper and its tests.

**Acceptance criteria:**
- [ ] `resolve_state_dir(agent)` returns the `.a0proj/state/` path using the same project-folder resolution as telemetry
- [ ] `save_active_plan(agent, plan_data)` writes `active_plan.json`
- [ ] `read_active_plan(agent)` returns plan data or safe default
- [ ] `save_active_goal(agent, goal_data)` writes `active_goal.json`
- [ ] `read_active_goal(agent)` returns goal data or safe default
- [ ] `save_current_phase(agent, phase_data)` writes `current_phase.json`
- [ ] `read_current_phase(agent)` returns phase data or safe default
- [ ] `save_loaded_skills(agent, skills_data)` writes `loaded_skills.json`
- [ ] `read_loaded_skills(agent)` returns skills data or safe default
- [ ] `save_checkpoints(agent, checkpoints_data)` writes `checkpoints.json`
- [ ] `read_checkpoints(agent)` returns checkpoints data or safe default
- [ ] `append_progress_event(agent, event_data)` appends a line to `progress_log.jsonl`
- [ ] `read_progress_log(agent)` returns all progress entries
- [ ] `write_handoff(agent)` writes `handoff.md` from current state
- [ ] `read_all_state(agent)` returns a consolidated dict of all state
- [ ] Path traversal prevention — state files cannot escape `.a0proj/state/`
- [ ] Missing state directory is created lazily on first write
- [ ] Corrupt JSON files return safe defaults and log a warning

**Verification:**
- [ ] Focused unit tests cover read/write for each artifact type
- [ ] Missing-files tests confirm safe defaults
- [ ] Corrupt-files tests confirm safe defaults
- [ ] Path traversal tests confirm rejection
- [ ] JSONL append tests confirm valid JSON per line
- [ ] Handoff markdown tests confirm well-formed output
- [ ] `read_all_state` returns consolidated dict when files exist
- [ ] `read_all_state` returns empty dict when no files exist

**Dependencies:** Slice 1 complete

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/workflow_state.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py` (new)

**Estimated scope:** Large (foundational — all other tasks depend on this)

### Checkpoint: After Task 1

- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py -v` — all green
- [ ] Helper can read/write all 7 artifact types
- [ ] No state escapes `.a0proj/state/`

---

### Phase 2: Persist Extension

## Task 2: Create `_10_persist_workflow_state.py`

**Description:**
Build the `tool_execute_after` extension that persists workflow state after relevant tool calls. This extension calls the workflow-state helper (never writes files directly). It detects state changes from tool calls and writes the appropriate artifacts.

**Acceptance criteria:**
- [ ] Extension fires after tool execution and inspects tool_name/tool_args
- [ ] After `skills_tool:load`, extension saves `loaded_skills.json` and appends a `skill_loaded` progress event
- [ ] After tool calls that update plan/goal/phase (detected via tool_args), extension saves the appropriate state files
- [ ] After any state write, extension regenerates `handoff.md`
- [ ] Extension no-ops for non-relevant tool calls
- [ ] Extension does not break when project folder is missing
- [ ] Extension does not break when state directory is missing
- [ ] Extension body is fail-safe (top-level try/except)

**Verification:**
- [ ] Focused tests confirm state is written after `skills_tool:load`
- [ ] Focused tests confirm state is written after plan/goal/phase updates
- [ ] Focused tests confirm no-op for irrelevant tools
- [ ] Focused tests confirm safe behavior with missing project folder
- [ ] Read extension and confirm top-level try/except pattern matches plugin conventions

**Dependencies:** Task 1

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_10_persist_workflow_state.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_persist_workflow_state.py` (new)

**Estimated scope:** Medium

### Checkpoint: After Task 2

- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_persist_workflow_state.py -v` — all green
- [ ] State is durably written after relevant tool calls
- [ ] Extension never breaks the agent loop

---

### Phase 3: Rehydrate Extension

## Task 3: Create `_67_reattach_workflow_state.py`

**Description:**
Build the `message_loop_prompts_after` extension that reads `.a0proj/state/` files and appends a consolidated context block to the assembled prompt. This is the critical "memory recovery" extension — it ensures the agent knows its prior state even after compaction or session resume.

**Acceptance criteria:**
- [ ] Extension fires during prompt assembly (after main prompts, before loop)
- [ ] When state files exist, extension appends a formatted state block to the prompt
- [ ] When no state files exist, extension returns the prompt unmodified
- [ ] Rehydrated `loaded_skills` are injected into `agent.data['loaded_skills']`
- [ ] Rehydrated state block includes: plan, goal, phase, loaded skills, last checkpoint
- [ ] Extension returns unmodified prompt on any error
- [ ] Extension body is fail-safe (top-level try/except)

**Verification:**
- [ ] Focused tests confirm state block is appended when files exist
- [ ] Focused tests confirm prompt is unmodified when no files exist
- [ ] Focused tests confirm prompt is unmodified on simulated errors
- [ ] Focused tests confirm `agent.data['loaded_skills']` is updated from rehydrated state
- [ ] Integration test: write state via helper, read via rehydrate — round-trip confirmed
- [ ] Compatibility test: rehydrated `loaded_skills.json` format is compatible with `skill_match.get_loaded_skills()`

**Dependencies:** Tasks 1, 2

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_rehydrate.py` (new)

**Estimated scope:** Medium

### Checkpoint: After Task 3

- [ ] `pytest /a0/usr/plugins/a0_agent_skills/tests/test_workflow_rehydrate.py -v` — all green
- [ ] State round-trips: write → persist → rehydrate → agent sees state
- [ ] Existing Slice 1 tests remain green (389 passing)

---

### Phase 4: Progress Log and Checkpoints

## Task 4: Add progress-log append and checkpoint create/update behaviors

**Description:**
Extend the workflow-state helper and persist extension to support explicit progress events and checkpoint operations. This includes the full set of progress event types and the checkpoint CRUD operations.

**Acceptance criteria:**
- [ ] `append_progress_event` supports all event types: `phase_change`, `skill_loaded`, `skill_unloaded`, `task_started`, `task_completed`, `checkpoint`, `goal_set`, `plan_set`, `custom`
- [ ] Each JSONL line is valid JSON with a `ts` field and an `event` field
- [ ] Progress log is append-only — existing entries are never mutated
- [ ] `save_checkpoints` supports create and update operations
- [ ] Checkpoint IDs are unique within the `checkpoints.json` array
- [ ] `write_handoff` includes last checkpoint in the handoff markdown
- [ ] Persist extension appends progress events for phase changes, skill loads, and checkpoint creates

**Verification:**
- [ ] Unit tests for each event type confirm correct JSONL format
- [ ] Unit tests confirm append-only behavior (read after write returns both old and new entries)
- [ ] Unit tests for checkpoint CRUD (create, update, list)
- [ ] Unit tests confirm handoff includes checkpoint info
- [ ] Extension tests confirm progress events are appended during workflow transitions

**Dependencies:** Task 3

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/workflow_state.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_10_persist_workflow_state.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_persist_workflow_state.py` (extend)

**Estimated scope:** Medium

### Checkpoint: After Task 4

- [ ] Progress log is append-only and machine-readable
- [ ] Checkpoints are mutable and durable
- [ ] Handoff includes checkpoint information

---

### Phase 5: Configuration and Documentation

## Task 5: Add config surface and update README

**Description:**
Extend plugin configuration to support workflow-state settings and update the README with documentation on durable state, how to inspect state files, and how the rehydration mechanism works.

**Acceptance criteria:**
- [ ] `default_config.yaml` includes `workflow_state_enabled: true` key
- [ ] `default_config.yaml` includes `workflow_state_path: .a0proj/state/` key
- [ ] Persist extension reads `workflow_state_enabled` and no-ops when disabled
- [ ] Rehydrate extension reads `workflow_state_enabled` and no-ops when disabled
- [ ] README documents durable workflow state feature
- [ ] README explains how to inspect `.a0proj/state/` files
- [ ] README explains rehydration behavior after compaction/session resume
- [ ] README notes compatibility with enforcement gate (Slice 1)

**Verification:**
- [ ] Read `default_config.yaml` and confirm new keys
- [ ] Test that persist extension respects `workflow_state_enabled: false`
- [ ] Test that rehydrate extension respects `workflow_state_enabled: false`
- [ ] Re-read README sections for consistency with the spec

**Dependencies:** Tasks 3, 4

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/default_config.yaml` (extend)
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_after/_10_persist_workflow_state.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/README.md` (extend)

**Estimated scope:** Small

### Checkpoint: After Task 5

- [ ] Config surface exists with sensible defaults
- [ ] README is consistent with spec and actual behavior
- [ ] Operator can disable workflow state if needed

---

### Phase 6: Final Verification

## Task 6: Final verification pass

**Description:**
Run the full test suite, verify no regressions, and confirm that all Slice 2 success criteria from the spec are met.

**Acceptance criteria:**
- [ ] Full plugin suite passes: 389 Slice 1 tests + all new Slice 2 tests
- [ ] No test failures, no unexpected skips
- [ ] All 10 spec success criteria verified
- [ ] No core framework edits were made
- [ ] State round-trips work end-to-end (write → persist → rehydrate → agent sees state)

**Verification:**
- [ ] `python -m pytest tests/ --tb=short` — all green
- [ ] Manual spot-check of `.a0proj/state/` file contents after a simulated workflow
- [ ] Re-read spec, plan, config, tests, and docs for contradictions

**Dependencies:** Task 5

**Files likely touched:** None (verification only)

**Estimated scope:** Small

### Final release gate

- [ ] `python -m pytest tests/ --tb=short` — all green
- [ ] All spec success criteria met
- [ ] No contradiction across spec, plan, config, tests, and docs
- [ ] Ready for phase-aware governance work (Slice 3)

---

## Risk Areas and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| State files become stale after abandoned workflows | Medium | Low | Handoff markdown is human-readable; operator can delete `.a0proj/state/` to reset |
| Progress log grows unbounded | Low | Low | JSONL format is cheap; rotation can be added later via config |
| Rehydration adds latency to every prompt assembly | Low | Medium | Helper reads are small JSON files; benchmark and optimize if needed |
| `loaded_skills.json` format diverges from `skill_match.get_loaded_skills()` | Low | High | Compatibility test in Task 3; shared schema version |
| Path traversal in state file names | Very Low | High | Helper validates all paths stay within `.a0proj/state/` |
| Concurrent writes from parallel tool calls | Low | Medium | Thread-safe write lock (same pattern as telemetry `_write_lock`) |

## Notes

- Planning/spec/docs live in **`/a0/usr/projects/a0_agent_skills`**
- Implementation lives in **`/a0/usr/plugins/a0_agent_skills`**
- Do not confuse the umbrella roadmap with the current shipped slice
- Do not broaden scope into `_permissions` or `_tracing`
- Task numbering starts at Task 1 within this slice (matches umbrella plan Tasks 2–4 but numbered independently here)
