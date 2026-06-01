# Changelog

## [Unreleased] - 2026-06-01

### Added
- Artifact path wiring fix: wire `workflow_artifacts.json` paths to handoff and rehydration readers so Plan, Plan Path, and Current Task display real values instead of `(unknown)`
- `merge_workflow_artifact()` helper for atomic key-level merges into `workflow_artifacts.json`
- `merge_workflow_artifacts_batch()` helper for multi-key merges in a single read-modify-write cycle
- Backward-compat fallback: both handoff and rehydration fall back to old `plan_path` in `active_plan.json` if `workflow_artifacts.json` is empty
- Artifact display key mapping in handoff and rehydration (spec_path→spec, plan_path→plan, todo_path→todo)
- Slug None guard in TODO handler to prevent overwriting valid slugs
- `telemetry_debug` setting to `default_config.yaml`
- `artifact_inference_enabled` setting to `config.json`
- ADR-007: artifact-path-resolution (two-store model)
- 25 new/updated tests across 5 test files (825 total, was 818)

### Fixed
- `plan_path` never written to `workflow_artifacts.json` — readers now pull from the correct store
- TODO handler full-replace bug — `plan_name` now survives TODO writes via merge semantics
- `save_active_plan(None)` silent TypeError during lifecycle reset — changed to `save_active_plan({})`
- Artifact display list always empty — key mapping now matches stored keys
- Explicit args handler routes `plan_path` to `workflow_artifacts.json` per two-store model
- Double I/O in SPEC block — uses `merge_workflow_artifacts_batch` for single write
- Duplicate `artifacts` variable in rehydration removed

### Changed
- Spec `durable-workflow-state-spec.md` schema updated to reflect two-store model
- Spec `artifact-path-wiring-fix-spec.md` status updated to SHIPPED
- Config `workflow_state_enabled` set to `true` for testing

### Reports
- Framework settings UI bug report (`docs/reports/framework-settings-ui-bug.md`)
- Agent SHIP phase routing bugs (`docs/reports/agent-ship-phase-routing-bugs.md`) — 6 bugs documented with 12 lessons learned
