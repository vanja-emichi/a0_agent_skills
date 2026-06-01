# Todo: Artifact Path Wiring Fix

> **Spec:** `docs/specs/artifact-path-wiring-fix-spec.md`
> **Plan:** `docs/plans/artifact-path-wiring-fix-plan.md`

## Phase 1: Foundation

- [ ] **Task 1:** Add `merge_workflow_artifact` helper to `workflow_state.py`
  - File: `helpers/workflow_state.py`
  - Add `merge_workflow_artifact(agent, key, value) -> str | None` after ~line 172
  - Pattern: read → merge key → write back
  - Never raises — wrapped in try/except
  - Acceptance: writes to `workflow_artifacts.json`, preserves existing keys, returns path or None
  - Verify: `pytest tests/test_workflow_state.py -v`

## Phase 2: Path Population

- [ ] **Task 2:** Wire artifact inference to write paths via `merge_workflow_artifact`
  - File: `extensions/python/tool_execute_after/_10_persist_workflow_state.py`
  - Add `merge_workflow_artifact` to existing import block at line 314
  - SPEC block (~line 372-408): merge `spec_path` and `feature_slug` into `workflow_artifacts.json`
  - PLAN block (~line 411-430): merge `plan_path` into `workflow_artifacts.json`
  - TODO block (~line 432-450): merge `todo_path` into `workflow_artifacts.json`
  - Acceptance: `workflow_artifacts.json` contains `spec_path`, `plan_path`, `todo_path` after spec→plan→todo
  - Verify: run live eval sequence, check file after each step

### Checkpoint: Path Population

- [ ] `merge_workflow_artifact` helper works in isolation
- [ ] Artifact inference writes all three paths to `workflow_artifacts.json`
- [ ] Existing tests still pass: `pytest tests/test_workflow_state.py tests/test_artifact_inference.py -v`
- [ ] `workflow_artifacts.json` survives multiple writes without losing keys

## Phase 3: Reader Fixes

- [ ] **Task 3:** Fix `write_handoff()` to read `plan_path` from `workflow_artifacts.json` with fallback
  - File: `helpers/workflow_state.py` line 553, `tests/test_workflow_state.py`
  - Replace `plan.get('plan_path', '(unknown)')` → `artifacts.get('plan_path') or plan.get('plan_path', '(unknown)')`
  - **Backward-compat fallback:** old state files with `plan_path` only in `active_plan.json` still display
  - Keep `current_task` reading from `active_plan.json` (correct owner)
  - Update test fixtures:
    - `test_workflow_state.py` line 631: `TestHandoff.test_write_creates_markdown`
    - `test_workflow_state.py` line 698: `TestHandoff.test_overwrite_updates_file`
    - `test_workflow_state.py` line 723: `TestHandoff.test_no_project_uses_workdir_fallback`
  - Acceptance: handoff shows `**Plan:** docs/plans/<slug>-plan.md` after plan write, backward-compat works
  - Verify: `pytest tests/test_workflow_state.py -v -k handoff`

- [ ] **Task 4:** Fix rehydration to read `plan_path` from `workflow_artifacts.json` (no new param)
  - File: `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py`, `tests/test_workflow_rehydrate.py`
  - `state` dict already has `workflow_artifacts` from `read_all_state()` — extract `artifacts = state.get("workflow_artifacts") or {}`
  - Replace line 80: `plan.get('plan_path')` → `artifacts.get('plan_path', plan.get('plan_path', '(unknown)'))` (backward-compat fallback)
  - Keep `plan_name` and `current_task` reading from `active_plan.json`
  - Update test fixtures:
    - `test_workflow_rehydrate.py` line 164: `TestStateBlockAppended.test_appends_state_block_when_state_exists`
    - `test_workflow_rehydrate.py` line 349: `TestRoundTrip.test_full_roundtrip`
    - `test_workflow_rehydrate.py` lines 422, 435: any test asserting `**Plan Path:**`
  - Acceptance: rehydration shows `**Plan Path:** docs/plans/<slug>-plan.md`, backward-compat works
  - Verify: `pytest tests/test_workflow_rehydrate.py -v`

### Checkpoint: Reader Fixes

- [ ] `handoff.md` shows real plan path (not `(unknown)`) after plan write
- [ ] Rehydration shows real plan path (not `(unknown)`) after plan write
- [ ] `**Current Task:**` still works correctly from `active_plan.json`
- [ ] Backward-compat: old state with `plan_path` only in `active_plan.json` still displays in both handoff and rehydration
- [ ] All updated tests pass: `pytest tests/test_workflow_state.py tests/test_workflow_rehydrate.py -v`

## Phase 4: Merge Semantics

- [x] **Task 5:** Fix both `save_active_plan` callers to merge instead of replace
  - File: `extensions/python/tool_execute_after/_10_persist_workflow_state.py`, test files
  - **Path A — TODO handler (~line 435-438):** read existing plan, merge slug + current_task, preserve plan_name
  - **Path B — Explicit args handler (~line 612-616):** merge plan-owned keys into `active_plan.json`, route `plan_path` to `merge_workflow_artifact` instead (per two-store model)
  - Update test fixtures:
    - `test_persist_workflow_state.py` line 215: `TestStateUpdates.test_saves_plan_when_plan_name_in_args` — `plan_path` in args should now route to `workflow_artifacts.json`
    - `test_artifact_inference.py` lines 375, 424, 445 — verify plan data after individual artifact writes
    - `test_artifact_inference_integration.py` lines 210, 253 — integration tests for full sequence
  - Add new test: verify `_persist_state_from_args` with `current_task` preserves pre-existing `plan_name`
  - Update `docs/specs/durable-workflow-state-spec.md` — remove `plan_path` from `active_plan.json` schema, note two-store model
  - Acceptance: `active_plan.json` contains both `plan_name` AND `current_task` after spec→plan→todo
  - Verify: `pytest tests/test_persist_workflow_state.py tests/test_artifact_inference.py -v`

### Checkpoint: Complete

- [x] All acceptance criteria from all 5 tasks met
- [ ] Run live eval: spec → plan → todo, no `(unknown)` in handoff or rehydration
- [x] `workflow_artifacts.json` populated with all three paths
- [x] `active_plan.json` has `plan_name` + `current_task` (not erased)
- [x] `pytest tests/ -v` passes
- [x] Ready for review
