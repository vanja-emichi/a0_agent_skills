# TODO: Durable Workflow State

> Generated from:
> - `/a0/usr/projects/a0_agent_skills/docs/specs/durable-workflow-state-spec.md`
> - `/a0/usr/projects/a0_agent_skills/docs/plans/durable-workflow-state-plan.md`
>
> **Status in broader roadmap:** This file tracks **Phase 2 / Slice 2** only.
> The umbrella roadmap tracker is:
> - `/a0/usr/projects/a0_agent_skills/tasks/a0-agent-skills-workflow-governance-todo.md`

## Current decisions

- Workflow state lives entirely in **`/a0/usr/plugins/a0_agent_skills`** — no core edits
- State artifacts live in **`.a0proj/state/`** — project-scoped, never global
- All state I/O goes through **`helpers/workflow_state.py`** — extensions never touch files directly
- JSON for snapshot files, **JSONL** for append-only progress log
- **Markdown** for handoff artifact (human-readable, not machine-parsed)
- Rehydration uses **`message_loop_prompts_after`** extension hook
- No TTL, no rotation in MVP
- Compatible with enforcement gate (Slice 1) — `loaded_skills.json` works with `skill_match.get_loaded_skills()`
- Lazy state creation — `.a0proj/state/` created on first write
- All extensions are fail-safe — top-level `try/except`, never break the loop

## Phase 1: Workflow-state helper

### Task 1: Create `helpers/workflow_state.py` with state file schema
- [x] Implement `resolve_state_dir(agent)` — project-folder resolution matching telemetry pattern
- [x] Implement `save_active_plan(agent, plan_data)` → `active_plan.json`
- [x] Implement `read_active_plan(agent)` → plan data or safe default
- [x] Implement `save_active_goal(agent, goal_data)` → `active_goal.json`
- [x] Implement `read_active_goal(agent)` → goal data or safe default
- [x] Implement `save_current_phase(agent, phase_data)` → `current_phase.json`
- [x] Implement `read_current_phase(agent)` → phase data or safe default
- [x] Implement `save_loaded_skills(agent, skills_data)` → `loaded_skills.json`
- [x] Implement `read_loaded_skills(agent)` → skills data or safe default
- [x] Implement `save_checkpoints(agent, checkpoints_data)` → `checkpoints.json`
- [x] Implement `read_checkpoints(agent)` → checkpoints data or safe default
- [x] Implement `append_progress_event(agent, event_data)` → `progress_log.jsonl`
- [x] Implement `read_progress_log(agent)` → all progress entries
- [x] Implement `write_handoff(agent)` → `handoff.md` from current state
- [x] Implement `read_all_state(agent)` → consolidated dict of all state
- [x] Path traversal prevention — reject paths escaping `.a0proj/state/`
- [x] Lazy directory creation on first write
- [x] Corrupt JSON returns safe defaults and logs warning
- [x] Focused unit tests in `tests/test_workflow_state.py`
  - [x] Read/write for each artifact type (7 types × read + write)
  - [x] Missing-files return safe defaults
  - [x] Corrupt-files return safe defaults
  - [x] Path traversal is rejected
  - [x] JSONL append produces valid JSON per line
  - [x] Handoff markdown is well-formed
  - [x] `read_all_state` returns consolidated dict when files exist
  - [x] `read_all_state` returns empty dict when no files exist

**Acceptance criteria:**
- [x] Helper can read/write all 7 state artifact types
- [x] Missing state files return safe defaults — no exceptions
- [x] No state escapes `.a0proj/state/`
- [x] `pytest tests/test_workflow_state.py -v` — all green

**Spec ref:** State File Schema, Testing Strategy
**Plan ref:** Task 1

### Phase 1 checkpoint
- [x] `pytest tests/test_workflow_state.py -v` — all green
- [x] Helper is the sole owner of `.a0proj/state/` I/O
- [x] No state escapes `.a0proj/state/`

---

## Phase 2: Persist extension

### Task 2: Create `_10_persist_workflow_state.py`
- [x] Create extension class `PersistWorkflowState(Extension)`
- [x] Top-level `try/except` — never break the loop
- [x] After `skills_tool:load`: save `loaded_skills.json` + append `skill_loaded` progress event
- [x] After plan/goal/phase update (detected via tool_args): save appropriate state file
- [x] After any state write: regenerate `handoff.md`
- [x] No-op for non-relevant tool calls
- [x] Safe behavior when project folder is missing
- [x] Safe behavior when state directory is missing
- [x] Read `workflow_state_enabled` from config — no-op when `false`
- [x] Focused tests in `tests/test_persist_workflow_state.py`
  - [x] State written after `skills_tool:load`
  - [x] State written after plan/goal/phase updates
  - [x] No-op for irrelevant tools (parametrized)
  - [x] Safe with missing project folder
  - [x] Safe with missing state directory
  - [x] Extension body has top-level try/except (source-level test)
  - [x] Config disabled → no state written

**Acceptance criteria:**
- [x] State durably written after relevant tool calls
- [x] Extension never breaks the agent loop
- [x] `pytest tests/test_persist_workflow_state.py -v` — all green

**Spec ref:** Extension Points (write paths), What Gets Persisted
**Plan ref:** Task 2

### Phase 2 checkpoint
- [x] `pytest tests/test_persist_workflow_state.py -v` — all green
- [x] State is durably written after relevant tool calls
- [x] Extension never breaks the agent loop

---

## Phase 3: Rehydrate extension

### Task 3: Create `_67_reattach_workflow_state.py`
- [x] Create extension class `ReattachWorkflowState(Extension)`
- [x] Top-level `try/except` — never break prompt assembly
- [x] When state files exist: append formatted state block to prompt
- [x] When no state files exist: return prompt unmodified
- [x] On any error: return prompt unmodified
- [x] Rehydrate `loaded_skills` into `agent.data['loaded_skills']`
- [x] State block includes: plan, goal, phase, loaded skills, last checkpoint
- [x] Read `workflow_state_enabled` from config — no-op when `false`
- [x] Focused tests in `tests/test_workflow_rehydrate.py`
  - [x] State block appended when files exist
  - [x] Prompt unmodified when no files exist
  - [x] Prompt unmodified on simulated errors
  - [x] `agent.data['loaded_skills']` updated from rehydrated state
  - [x] Round-trip test: write via helper → read via rehydrate
  - [x] Compatibility test: rehydrated `loaded_skills.json` works with `skill_match.get_loaded_skills()`
  - [x] Config disabled → prompt unmodified

**Acceptance criteria:**
- [x] State round-trips: write → persist → rehydrate → agent sees state
- [x] Existing Slice 1 tests remain green (389 passing)
- [x] `pytest tests/test_workflow_rehydrate.py -v` — all green

**Spec ref:** Extension Points (read paths), What Gets Rehydrated
**Plan ref:** Task 3

### Phase 3 checkpoint
- [x] `pytest tests/test_workflow_rehydrate.py -v` — all green
- [x] State round-trips end-to-end
- [x] Existing Slice 1 tests remain green

---

## Phase 4: Progress log and checkpoints

### Task 4: Add progress-log append and checkpoint CRUD
- [x] Extend `append_progress_event` for all event types
  - [x] `phase_change`
  - [x] `skill_loaded`
  - [x] `skill_unloaded`
  - [x] `task_started`
  - [x] `task_completed`
  - [x] `checkpoint`
  - [x] `goal_set`
  - [x] `plan_set`
  - [x] `custom`
- [x] Validate each JSONL line has `ts` and `event` fields
- [x] Verify progress log is append-only (read after write returns old + new)
- [x] Extend `save_checkpoints` for create and update
- [x] Enforce unique checkpoint IDs within `checkpoints.json`
- [x] Update `write_handoff` to include last checkpoint
- [x] Extend persist extension to append progress events for transitions
- [x] Focused tests extending existing test files
  - [x] Unit tests for each event type → correct JSONL format
  - [x] Append-only verification
  - [x] Checkpoint CRUD (create, update, list)
  - [x] Handoff includes checkpoint info
  - [x] Extension appends progress events during workflow transitions

**Acceptance criteria:**
- [x] Progress log is append-only and machine-readable
- [x] Checkpoints are mutable and durable
- [x] Handoff includes checkpoint information

**Spec ref:** State File Schema (progress_log.jsonl, checkpoints.json)
**Plan ref:** Task 4

### Phase 4 checkpoint
- [x] Progress log is append-only
- [x] Checkpoints are mutable
- [x] Handoff includes checkpoint info

---

## Phase 5: Configuration and documentation

### Task 5: Add config surface and update README
- [x] Add `workflow_state_enabled: true` to `default_config.yaml`
- [x] Add `workflow_state_path: .a0proj/state/` to `default_config.yaml`
- [x] Persist extension reads `workflow_state_enabled` and no-ops when disabled
- [x] Rehydrate extension reads `workflow_state_enabled` and no-ops when disabled
- [x] README: document durable workflow state feature
- [x] README: explain how to inspect `.a0proj/state/` files
- [x] README: explain rehydration behavior after compaction/session resume
- [x] README: note compatibility with enforcement gate (Slice 1)
- [x] Focused tests for config-disabled behavior
  - [x] Persist extension no-ops when `workflow_state_enabled: false`
  - [x] Rehydrate extension no-ops when `workflow_state_enabled: false`

**Acceptance criteria:**
- [x] Config surface exists with sensible defaults
- [x] README is consistent with spec and actual behavior
- [x] Operator can disable workflow state via config

**Spec ref:** Boundaries
**Plan ref:** Task 5

### Phase 5 checkpoint
- [x] Config keys are documented and have safe defaults
- [x] README matches spec wording
- [x] Operator can disable the feature

---

## Phase 6: Final verification

### Task 6: Final verification pass
- [x] Run `python -m pytest tests/ --tb=short` — all green
- [x] Verify 389 Slice 1 tests still pass
- [x] Verify all new Slice 2 tests pass
- [x] Manual spot-check of `.a0proj/state/` file contents after simulated workflow
- [x] Re-read spec, plan, config, tests, and docs for contradictions
- [x] Verify all 10 spec success criteria are met
- [x] Verify no core framework edits were made

### Final release gate
- [x] `python -m pytest tests/ --tb=short` — all green
- [x] All spec success criteria met
- [x] No contradiction across spec, plan, config, tests, and docs
- [x] Ready for phase-aware governance work (Slice 3)

---

## Notes

- Planning/spec/docs live in **`/a0/usr/projects/a0_agent_skills`**
- Implementation lives in **`/a0/usr/plugins/a0_agent_skills`**
- Do not confuse the umbrella roadmap with the current shipped slice
- Do not broaden scope into `_permissions` or `_tracing`
- Task numbering starts at Task 1 within this slice (matches umbrella plan Tasks 2–4 but numbered independently here)
