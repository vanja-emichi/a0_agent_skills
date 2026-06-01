# ADR-008: Artifact Path Wiring — Merge Semantics and Display Resolution

**Date**: 2026-06-01
**Status**: Accepted
**Supersedes**: N/A (complements ADR-007)

## Context

ADR-007 established the two-store model (`workflow_artifacts.json` owns paths, `active_plan.json` owns name/task). However, the original implementation had five bugs:

1. `plan_path` was never written to `workflow_artifacts.json` — readers showed `(unknown)`
2. TODO handler did a full replace of `active_plan.json`, erasing `plan_name`
3. `_persist_state_from_args` also did a full replace, same data loss
4. Artifact display list used wrong keys (`spec` vs `spec_path`) — always empty
5. Lifecycle reset passed `None` to `save_active_plan`, silently failing

These bugs meant the two-store model from ADR-007 was never actually functional in practice.

## Decision

### 1. Merge Semantics for Artifact Updates

Use read-merge-write instead of full replace for both stores:

```python
def merge_workflow_artifact(agent, key, value):
    existing = read_workflow_artifacts(agent) or {}
    existing[key] = value
    return save_workflow_artifacts(agent, existing)
```

**Contract:** Never raises. Returns path on success, `None` on failure.

### 2. Batch Merge for Single I/O

When multiple keys need updating simultaneously (e.g., SPEC block writes `spec_path` + `feature_slug`), use a batch helper to avoid two sequential read-merge-write cycles:

```python
def merge_workflow_artifacts_batch(agent, updates: dict):
    existing = read_workflow_artifacts(agent) or {}
    existing.update(updates)
    return save_workflow_artifacts(agent, existing)
```

### 3. Backward-Compatible Dual-Read Fallback

Both `write_handoff()` and rehydration read `plan_path` from the new store first, falling back to the old store for state files written by pre-fix code:

```python
plan_path = artifacts.get('plan_path') or plan.get('plan_path', '(unknown)')
```

This allows gradual migration — no state file upgrade needed.

### 4. Artifact Display Key Mapping

Stored keys use `_path` suffix (`spec_path`, `plan_path`, `todo_path`). Display names use plain names (`spec`, `plan`, `todo`). A mapping dict translates between them:

```python
artifact_key_map = {
    "idea": "idea", "intent": "intent",
    "spec_path": "spec", "plan_path": "plan", "todo_path": "todo",
}
```

### 5. Lifecycle Reset Uses Empty Dict

When clearing plan state on goal change, pass `{}` instead of `None`:

```python
save_active_plan(self.agent, {})  # was: None
```

`None` raises `TypeError` in `_save_artifact` because it tries `data["version"] = VERSION`.

### 6. Slug None Guard

Prevent overwriting a valid slug with `None` during TODO writes:

```python
if slug:
    existing_plan["slug"] = slug
```

## Alternatives Considered

### Alternative A: Merge into `_save_artifact` directly
- **Pros:** No new functions, all saves merge automatically
- **Cons:** Changes behavior for ALL state consumers (goal, phase, skills, checkpoints) — too wide a blast radius
- **Rejected:** Risk of breaking unrelated state persistence

### Alternative B: Single store (paths + name in one file)
- **Pros:** Simpler — no dual-read fallback needed
- **Cons:** Violates ADR-007 two-store model; path data mixed with task data
- **Rejected:** ADR-007 was accepted for good reasons (separation of concerns)

### Alternative C: State migration on load
- **Pros:** Clean state — move `plan_path` from old store to new store on first read
- **Cons:** Destructive migration; can't roll back to old code; harder to test
- **Rejected:** Non-destructive fallback is safer for gradual rollout

## Consequences

- **Handoff and rehydration now show real values** instead of `(unknown)`
- `plan_name` survives TODO writes via merge semantics
- Backward compatible — old state files still work
- Two new helper functions (`merge_workflow_artifact`, `merge_workflow_artifacts_batch`) added to `workflow_state.py`
- Future artifact types need to be added to `artifact_key_map` in two places (handoff + rehydration)

## Follow-Up Items

- Extract `artifact_key_map` to a shared constant (currently duplicated in handoff + rehydration)
- Extract backward-compat fallback to a helper function
- Add `os.chmod(path, 0o640)` to `write_handoff()` for consistent permissions
- Extend `_write_lock` scope to cover full read-merge-write cycle (prevent TOCTOU races)
