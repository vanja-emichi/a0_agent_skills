# Spec: Artifact Path Wiring Fix

> **Parent:** `docs/specs/markdown-artifact-and-state-alignment-spec.md`
> **ADR:** `docs/adrs/007-artifact-path-resolution.md` (Accepted)
> **Plan reference:** Phase 5 (Tasks 5.1–5.3) of `docs/plans/markdown-artifact-and-state-alignment-plan.md`
> **Status:** SHIPPED — All 5 tasks implemented, reviewed by 3 agents (code-reviewer APPROVE, security-auditor PASS, test-engineer FAIL→fixed). 825 tests pass. Clean eval from wiped state PASSED.

## Objective

Wire the artifact path store (`workflow_artifacts.json`) to the handoff and rehydration readers so that `Plan`, `Plan Path`, and `Current Task` display real values instead of `(unknown)` after a spec→plan→todo sequence.

## Why Now

Live eval (2026-06-01) proved the bug persists after the alignment project was marked SHIPPED:

```
handoff.md:     **Plan:** (unknown)
rehydration:     **Active Plan:** (unknown) / **Plan Path:** (unknown)
```

Root cause: Task 9 added `read_workflow_artifacts()` infrastructure but `write_handoff()` (line 553) and `_67_reattach_workflow_state.py` (lines 79–80) still read `plan_path` from `active_plan.json`, where it was never written. The TODO handler (lines 435–438) compounds the problem by doing a full-replace that erases `plan_name`.

## Architecture (from ADR-007 + alignment spec line 130)

Two-store model — **do not merge**:

| Store | Owns | Does NOT own |
|-------|------|-------------|
| `workflow_artifacts.json` | `feature_slug`, `spec_path`, `plan_path`, `todo_path`, approval state | plan_name, current_task |
| `active_plan.json` | `plan_name`, `slug`, `current_task` | artifact paths |

Readers must pull each field from its canonical owner.

## Scope

### In scope

1. **Fix `write_handoff()`** — read `plan_path` from `workflow_artifacts.json` via `read_workflow_artifacts(agent)`
2. **Fix rehydration** — read `plan_path` from `workflow_artifacts.json` in `_67_reattach_workflow_state.py`
3. **Fix TODO handler merge** — preserve existing `plan_name`/`slug` when writing `active_plan.json`
4. **Wire artifact inference** — `_10_persist_workflow_state.py` writes `spec_path`/`plan_path`/`todo_path` to `workflow_artifacts.json` on each artifact write

### Out of scope

- Artifact lifecycle states (active/superseded/completed) — deferred in alignment plan
- Approval invalidation on material changes — premature
- `tasks_total`/`tasks_completed` progress counters — separate gap
- `--slug` override — auto-discovery sufficient

## Acceptance Criteria

1. After writing a spec: `handoff.md` shows `**Plan:** (unknown)` (no plan yet — correct), `**Goal:** <slug>`
2. After writing a plan: `handoff.md` shows `**Plan:** docs/plans/<slug>-plan.md` (real path)
3. After writing a todo: `handoff.md` shows `**Current Task:** <first unchecked item>`, `**Plan:**` still shows the real path (not erased)
4. Rehydration shows `**Active Plan:** <name>` and `**Plan Path:** docs/plans/<slug>-plan.md`
5. `workflow_artifacts.json` contains `spec_path`, `plan_path`, `todo_path` after the sequence
6. `active_plan.json` still contains `plan_name` + `current_task` (not erased by TODO write)
7. Existing tests pass: `pytest tests/ -v`

## Files to Change

| File | Change |
|------|--------|
| `helpers/workflow_state.py` line 553 | Read `plan_path` from `workflow_artifacts.json` |
| `helpers/workflow_state.py` line 554 | Read `current_task` from `active_plan.json` (already correct owner) |
| `extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py` lines 79–80 | Read paths from `workflow_artifacts.json` |
| `extensions/python/tool_execute_after/_10_persist_workflow_state.py` lines 414–417, 435–438 | Write paths to `workflow_artifacts.json`; merge instead of replace for TODO handler |

## Verification

1. Run the live eval sequence (spec → plan → todo) and confirm no `(unknown)` in handoff or rehydration
2. `pytest tests/test_workflow_state.py tests/test_persist_workflow_state.py -v`
3. Confirm `workflow_artifacts.json` is populated after each artifact write
