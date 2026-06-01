# Changelog

## [Unreleased] - 2026-06-02

### Added — Approval Gate Wiring (Tasks 1–8)
- Natural language approval detection extension (`_20_approval_gate.py`) — detects phrases like "approved", "looks good", "proceed", "ship it" with word-boundary matching and negation/question rejection
- Phase gate check (`check_phase_approval_gate`) — blocks forward transitions in enforce mode when artifact is not approved; warns in observe mode
- Mtime invalidation — `mark_artifact_approved` stores file mtime; `is_artifact_approved` checks mtime and invalidates if file changed since approval
- Shadow sampling at 10% rate — classifier invoked on sampled tool calls in observe mode for accuracy data
- Classifier tuned to 93.6% accuracy (88/94 fixtures) — improved prompt patterns in `skill_match.py`
- Enforce mode enabled — corrections injected when skills are skipped; no false positives on skill-loaded calls
- 4 mandatory approval gates in routing rules (`agent.skills.routing.md`) — G1: DEFINE→PLAN, G2: PLAN→BUILD, G3: BUILD→REVIEW→SHIP, G4: REVIEW→SHIP
- 40 acceptance integration tests (`test_acceptance_approval_gates.py`) — full pipeline: detection → approval → gate → mtime invalidation
- DOX initialization — 14 AGENTS.md files created/updated across plugin and project paths

### Fixed
- 5 governance bugs identified during skill checkpoint analysis (approval infrastructure was dead code, no phase gates, no mtime tracking, advisory-only enforcement, 40.6% classifier accuracy)
- 5 pre-existing test failures (fixture data issues, import errors, assertion mismatches)
- 2 important code review findings (edge case in negation detection, missing type validation in gate check)
- 3 medium security issues (output sanitization in classifier logging, approval state not cleared on error paths, missing input bounds check)

### Changed
- `config.json` enforcement mode set to `enforce`
- `config.json` shadow sample rate set to 0.1
- Spec `approval-gate-wiring-spec.md` status updated to Shipped

### Test Results
- 981 passed, 43 skipped, 0 failures

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
