# Implementation Plan: Artifact Path Wiring Fix

> **Spec:** `docs/specs/artifact-path-wiring-fix-spec.md`
> **Parent plan:** Phase 5 of `docs/plans/markdown-artifact-and-state-alignment-plan.md`
> **ADR-007:** `docs/adrs/007-artifact-path-resolution.md`

## Overview

Wire the two-store model so `write_handoff()` and rehydration read `plan_path` from `workflow_artifacts.json` (the canonical path store) while `active_plan.json` keeps owning `plan_name`/`current_task`. Fix both the artifact inference and explicit-args write paths to write paths to `workflow_artifacts.json` and merge instead of replace for `active_plan.json`.

## Architecture Decisions

- **Two-store model (ADR-007):** `workflow_artifacts.json` owns paths, `active_plan.json` owns name/task. Do NOT merge into one store.
- **Merge helper:** Add a reusable `merge_workflow_artifact(agent, key, value)` helper in `workflow_state.py` instead of inline read-merge-write everywhere. This follows the DRY principle and reduces bug surface.
- **Both write paths covered:** The artifact inference path (`_persist_artifact_state`) AND the explicit-args path (`_persist_state_from_args`) both need fixes.

## Dependency Graph

```
Task 1 (add merge helper)
    │
Task 2 (inference writes paths to workflow_artifacts.json)
    │
    ├── Task 3 (handoff reads paths from workflow_artifacts.json)
    │       + update tests in test_workflow_state.py
    │
    ├── Task 4 (rehydration reads paths from workflow_artifacts.json)
    │       + update tests in test_workflow_rehydrate.py
    │
    └── Task 5 (both save_active_plan callers merge instead of replace)
            + update tests in test_persist_workflow_state.py + test_artifact_inference.py
```

Task 1 must land first (provides the helper). Task 2 must land before Tasks 3/4 (populates the store). Task 5 is logically grouped but independent of Tasks 3/4.

---

## Phase 1: Foundation

### Task 1: Add `merge_workflow_artifact` helper to `workflow_state.py`

**File:** `helpers/workflow_state.py`

**Description:** Create a reusable helper that reads `workflow_artifacts.json`, updates a single key, and writes back. This avoids inline read-merge-write in every caller.

**Change:**
- Add `merge_workflow_artifact(agent, key, value) -> str | None` after the existing `save_workflow_artifacts` / `read_workflow_artifacts` functions (after ~line 172).
- Pattern: `read_workflow_artifacts` → get dict or `{}` → set `dict[key] = value` → `save_workflow_artifacts`
- Also set `feature_slug` on first write if the slug is provided and not already set
- Optionally set `updated_at` timestamp for the specific key

**Acceptance criteria:**
- [ ] `merge_workflow_artifact(agent, "plan_path", "docs/plans/foo-plan.md")` writes to `workflow_artifacts.json`
- [ ] Subsequent calls preserve existing keys
- [ ] Returns the file path on success, None on failure
- [ ] Never raises — wrapped in try/except

**Verification:**
- [ ] Unit test: call `merge_workflow_artifact` with different keys, confirm all survive
- [ ] `pytest tests/test_workflow_state.py -v`

**Dependencies:** None

**Files likely touched:**
- `helpers/workflow_state.py` (add function)
- `tests/test_workflow_state.py` (add test)

**Estimated scope:** S (1-2 files)

---

## Phase 2: Path Population

### Task 2: Wire artifact inference to write paths via `merge_workflow_artifact`

**File:** `extensions/python/tool_execute_after/_10_persist_workflow_state.py`

**Description:** After each artifact-type block (spec, plan, todo), call `merge_workflow_artifact` to store the artifact's file path. Also set `feature_slug` on first write.

**Changes:**
- Import `merge_workflow_artifact` by adding it to the existing local import block at line 314 (`from helpers.workflow_state import ...`). This maintains consistency with the codebase pattern of local imports from `helpers.workflow_state`.
- In the SPEC block (~line 372-408): after `save_active_goal()`, call `merge_workflow_artifact(self.agent, "spec_path", path)` and `merge_workflow_artifact(self.agent, "feature_slug", slug)`
- In the PLAN block (~line 411-430): after `save_active_plan()`, call `merge_workflow_artifact(self.agent, "plan_path", path)` and set `feature_slug` if not already set
- In the TODO block (~line 432-450): after `save_active_plan()`, call `merge_workflow_artifact(self.agent, "todo_path", path)`

**Acceptance criteria:**
- [ ] After spec write: `workflow_artifacts.json` contains `spec_path`
- [ ] After plan write: `workflow_artifacts.json` contains `plan_path`
- [ ] After todo write: `workflow_artifacts.json` contains `todo_path`
- [ ] `feature_slug` is set from the first artifact's slug and preserved across subsequent writes
- [ ] Existing fields are preserved on each write

**Verification:**
- [ ] Run live eval sequence (spec → plan → todo), check `workflow_artifacts.json` after each step
- [ ] `pytest tests/test_artifact_inference.py -v`

**Dependencies:** Task 1

**Files likely touched:**
- `extensions/python/tool_execute_after/_10_persist_workflow_state.py`
- `tests/test_artifact_inference.py` (update/add tests)

**Estimated scope:** S (1-2 files)

### Checkpoint: Path Population

- [ ] `merge_workflow_artifact` helper works in isolation
- [ ] Artifact inference writes all three paths to `workflow_artifacts.json`
- [ ] Existing tests still pass: `pytest tests/test_workflow_state.py tests/test_artifact_inference.py -v`
- [ ] `workflow_artifacts.json` survives multiple writes without losing keys

---

## Phase 3: Reader Fixes

### Task 3: Fix `write_handoff()` to read `plan_path` from `workflow_artifacts.json`

**File:** `helpers/workflow_state.py`, `tests/test_workflow_state.py`

**Description:** Replace line 553's `plan.get('plan_path', '(unknown)')` with a read from `workflow_artifacts.json`, with a backward-compat fallback to `active_plan.json` for existing state files.

**Changes:**
- In `write_handoff()`: `artifacts` is already read on line 536 via `read_workflow_artifacts(agent)` — reuse it
- Replace line 553: `plan.get('plan_path', '(unknown)')` → `artifacts.get('plan_path') or plan.get('plan_path', '(unknown)')`
  - **Backward-compat fallback:** If `workflow_artifacts.json` has no `plan_path` but the old `active_plan.json` does, the fallback reads from the old location. This handles existing state files without requiring a migration step.
- Keep line 554: `plan.get('current_task', '(unknown)')` reading from `active_plan.json` (correct owner per two-store model)
- **Update tests:** All tests that set up handoff data and assert the Plan field must be updated:
  - `test_workflow_state.py` line 631: `TestHandoff.test_write_creates_markdown` — writes `plan_path` in `active_plan.json`, must ALSO write to `workflow_artifacts.json`
  - `test_workflow_state.py` line 698: `TestHandoff.test_overwrite_updates_file` — same pattern
  - `test_workflow_state.py` line 723: `TestHandoff.test_no_project_uses_workdir_fallback` — same pattern

**Acceptance criteria:**
- [ ] `handoff.md` shows `**Plan:** docs/plans/<slug>-plan.md` after plan write
- [ ] `handoff.md` shows `**Plan:** (unknown)` before plan write (correct — no plan yet)
- [ ] `**Current Task:**` still reads from `active_plan.json` (unchanged)
- [ ] Backward-compat: old state files with `plan_path` only in `active_plan.json` still display correctly
- [ ] All handoff tests updated to write `plan_path` to `workflow_artifacts.json`

**Verification:**
- [ ] Write spec only → handoff shows Plan: (unknown). Write plan → handoff shows real path.
- [ ] Test backward-compat: set `plan_path` only in `active_plan.json` (not `workflow_artifacts.json`) → handoff still shows it
- [ ] `pytest tests/test_workflow_state.py -v -k handoff`

**Dependencies:** Task 2

**Files likely touched:**
- `helpers/workflow_state.py` (1 line change + fallback)
- `tests/test_workflow_state.py` (update test fixtures at lines 631, 698, 723)

**Estimated scope:** S (2 files)

### Task 4: Fix rehydration to read `plan_path` from `workflow_artifacts.json`

**File:** `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py`, `tests/test_workflow_rehydrate.py`

**Description:** Change line 80 to read `plan_path` from the `workflow_artifacts` key already present in the `state` dict (populated by `read_all_state()` at line 676-696). No new parameter needed.

**Changes:**
- In `_format_state_block(state)`: the `state` dict already contains `workflow_artifacts` (from `read_all_state`). Extract it before the plan block:
  ```python
  artifacts = state.get("workflow_artifacts") or {}
  ```
- Replace line 80: `plan.get('plan_path', '(unknown)')` → `artifacts.get('plan_path', plan.get('plan_path', '(unknown)'))`
  - **Backward-compat fallback:** same pattern as Task 3 — if `workflow_artifacts.json` has no `plan_path`, fall back to the old `active_plan.json` location.
- Keep line 79: `plan.get('plan_name', '(unknown)')` reading from `active_plan.json` (correct owner)
- Keep line 81: `plan.get('current_task', '(unknown)')` reading from `active_plan.json` (correct owner)
- **Update tests:** All rehydration tests that set up `plan_path` must be updated:
  - `test_workflow_rehydrate.py` line 164: `TestStateBlockAppended.test_appends_state_block_when_state_exists` — must ALSO write `plan_path` to `workflow_artifacts.json` via `save_workflow_artifacts`
  - `test_workflow_rehydrate.py` line 349: `TestRoundTrip.test_full_roundtrip` — same pattern
  - `test_workflow_rehydrate.py` line 422, 435: any test asserting `**Plan Path:**` in rehydrated output

**Acceptance criteria:**
- [ ] Rehydration shows `**Plan Path:** docs/plans/<slug>-plan.md` after plan write
- [ ] Rehydration shows `**Active Plan:** <name>` from `active_plan.json`
- [ ] Rehydration shows `**Current Task:** <task>` from `active_plan.json`
- [ ] Backward-compat: old state with `plan_path` only in `active_plan.json` still displays
- [ ] All existing rehydration tests updated and passing

**Verification:**
- [ ] Check rehydrated state in EXTRAS after each artifact write
- [ ] `pytest tests/test_workflow_rehydrate.py -v`

**Dependencies:** Task 2

**Files likely touched:**
- `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` (2-3 lines)
- `tests/test_workflow_rehydrate.py` (update test fixtures at lines 164, 349, 422, 435)

**Estimated scope:** S (2 files)

### Checkpoint: Reader Fixes

- [ ] `handoff.md` shows real plan path (not `(unknown)`) after plan write
- [ ] Rehydration shows real plan path (not `(unknown)`) after plan write
- [ ] `**Current Task:**` still works correctly from `active_plan.json`
- [ ] All updated tests pass: `pytest tests/test_workflow_state.py tests/test_workflow_rehydrate.py -v`

---

## Phase 4: Merge Semantics

### Task 5: Fix both `save_active_plan` callers to merge instead of replace

**File:** `extensions/python/tool_execute_after/_10_persist_workflow_state.py`, `tests/test_persist_workflow_state.py`, `tests/test_artifact_inference.py`

**Description:** Fix both code paths that write `active_plan.json` to merge with existing data instead of doing a full replace.

**Two code paths to fix:**

**Path A — TODO artifact handler (~line 435-438):**
```python
# BEFORE (full replace):
plan_data: dict = {"slug": slug}
if current_task:
    plan_data["current_task"] = current_task
save_active_plan(self.agent, plan_data)

# AFTER (merge):
from helpers.workflow_state import read_active_plan
existing_plan = read_active_plan(self.agent) or {}
existing_plan["slug"] = slug
if current_task:
    existing_plan["current_task"] = current_task
save_active_plan(self.agent, existing_plan)
```

**Path B — Explicit args handler (~line 612-616):**
```python
# BEFORE (full replace):
save_active_plan(self.agent, {
    k: args[k] for k in ("plan_name", "plan_path", "current_task",
                         "tasks_total", "tasks_completed")
    if k in args
})

# AFTER (merge + route plan_path to correct store):
from helpers.workflow_state import read_active_plan, merge_workflow_artifact
existing_plan = read_active_plan(self.agent) or {}
# Merge plan-owned keys into active_plan.json (NOT plan_path — that's owned by workflow_artifacts.json)
for k in ("plan_name", "current_task", "tasks_total", "tasks_completed"):
    if k in args:
        existing_plan[k] = args[k]
save_active_plan(self.agent, existing_plan)
# Route plan_path to its canonical owner
if "plan_path" in args:
    merge_workflow_artifact(self.agent, "plan_path", args["plan_path"])
```
> **Note:** Per ADR-007 two-store model, `plan_path` is owned by `workflow_artifacts.json`, NOT `active_plan.json`. Path B must route it to the correct store.

**Update tests:**
- `test_persist_workflow_state.py` — any test that verifies `active_plan.json` after a TODO write must now confirm `plan_name` survives
- `test_persist_workflow_state.py` line 215: `TestStateUpdates.test_saves_plan_when_plan_name_in_args` — passes `plan_path` in args; after Path B fix, this should route to `workflow_artifacts.json`, not `active_plan.json`
- `test_artifact_inference.py` — test the spec→plan→todo sequence and assert `plan_name` is present after all three
- `test_artifact_inference.py` lines 375, 424, 445 — verify plan data after individual artifact writes
- `test_artifact_inference_integration.py` lines 210, 253 — integration tests for full sequence
- Add new test: verify `_persist_state_from_args` with `current_task` preserves pre-existing `plan_name`

**Acceptance criteria:**
- [ ] After spec → plan → todo sequence: `active_plan.json` contains both `plan_name` AND `current_task`
- [ ] `plan_name` is NOT erased by the TODO write
- [ ] `slug` is updated correctly
- [ ] `_persist_state_from_args` with `current_task` preserves pre-existing `plan_name`
- [ ] All existing tests updated and passing

**Verification:**
- [ ] Run full sequence, read `active_plan.json` after TODO write
- [ ] `pytest tests/test_persist_workflow_state.py tests/test_artifact_inference.py -v`

**Dependencies:** None (independent of Tasks 2-4, logically grouped in Phase 4)

**Files likely touched:**
- `extensions/python/tool_execute_after/_10_persist_workflow_state.py` (both code paths)
- `tests/test_persist_workflow_state.py` (update/add tests)
- `tests/test_artifact_inference.py` (update/add tests)

**Estimated scope:** M (3 files)

### Checkpoint: Complete

- [ ] All acceptance criteria from all 5 tasks met
- [ ] Run live eval: spec → plan → todo, no `(unknown)` in handoff or rehydration
- [ ] `workflow_artifacts.json` populated with all three paths
- [ ] `active_plan.json` has `plan_name` + `current_task` (not erased)
- [ ] `pytest tests/ -v` passes
- [ ] Ready for review

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `merge_workflow_artifact` races with concurrent writes from multi-instance setup | Medium — data loss | `_save_artifact` already uses file lock; merge helper reuses same lock |
| Test breakage from changing read source for `plan_path` | High — false red CI | Each reader task (3, 4) explicitly includes test updates in scope |
| `_persist_state_from_args` merge changes semantics for explicit `plan_path` in args | Low — `plan_path` key was dead code anyway | Path B merge is additive; it never removes keys from existing plan |
| `workflow_artifacts.json` grows unbounded over time | Low — only 5-6 keys max | Schema is bounded (spec_path, plan_path, todo_path, feature_slug, approved, approved_at) |
| Existing tests in `test_workflow_state.py` test handoff with `active_plan.json` containing `plan_path` | High — tests assert wrong source | Task 3 explicitly covers updating these tests |

## Open Questions

- None — all gaps from the review have been addressed in the plan.
