# TODO: Phase-Aware Workflow Governance

> Generated from:
> - `/a0/usr/projects/a0_agent_skills/docs/specs/phase-aware-governance-spec.md`
> - `/a0/usr/projects/a0_agent_skills/docs/plans/phase-aware-governance-plan.md`
>
> **Status in broader roadmap:** This file tracks **Phase 3 / Slice 3** only.
> The umbrella roadmap tracker is:
> - `/a0/usr/projects/a0_agent_skills/tasks/a0-agent-skills-workflow-governance-todo.md`

## Current decisions

- Phase-aware governance lives entirely in **`/a0/usr/plugins/a0_agent_skills`** — no core edits
- Phase model uses six canonical phases: **DEFINE, PLAN, BUILD, VERIFY, REVIEW, SHIP**
- Phase-skill mapping is hardcoded in a new **`helpers/phase_governance.py`** module — not embedded in enforcer
- Phase-skill mapping is derived from the plugin's existing routing rules
- The existing **`_10_skill_enforcer.py`** is extended, not replaced — no new enforcement extension
- Phase transitions are **advisory** — logged but never blocking
- Correction deduplication uses **time-based cooldown** per candidate (default 300 seconds)
- `gate_correction` is a **first-class event type** in `_VALID_EVENT_TYPES`
- Enforcement behavior remains **observe-first** when `enforcement_mode: observe`
- **No hard human-intervention mode** in MVP
- All extensions are fail-safe — top-level `try/except`, never break the loop
- All imports use **importlib pattern** from Slice 1
- State I/O goes through existing **`helpers/workflow_state.py`** — no direct file access
- Backward compatible: when `phase_governance_enabled: false` or phase unknown, behaves exactly as Slice 1

## Phase 1: Phase helper and phase-skill mapping

### Task 1: Create `helpers/phase_governance.py` with phase model and transition validation
- [x] Define `PHASE_ORDER` constant: `["DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"]`
- [x] Define `PHASE_SKILL_MAP` constant mapping each phase to expected skills
  - [x] DEFINE → `interview-me`, `spec-driven-development`
  - [x] PLAN → `planning-and-task-breakdown`, `context-engineering`
  - [x] BUILD → `incremental-implementation`, `test-driven-development`, `source-driven-development`, `doubt-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`
  - [x] VERIFY → `browser-testing-with-devtools`, `debugging-and-error-recovery`
  - [x] REVIEW → `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`
  - [x] SHIP → `shipping-and-launch`, `ci-cd-and-automation`, `git-workflow-and-versioning`, `documentation-and-adrs`, `deprecation-and-migration`
- [x] Implement `get_current_phase(agent)` — reads `current_phase.json` via `workflow_state`
- [x] Implement `get_expected_skills(phase)` — returns skill list from `PHASE_SKILL_MAP`
- [x] Implement `is_phase_valid_transition(from_phase, to_phase)` — returns transition info dict
  - [x] `initial`: from None to DEFINE
  - [x] `forward`: from earlier to later in PHASE_ORDER
  - [x] `reentry`: from phase to same phase
  - [x] `rewind`: from later to earlier (allowed, with warning)
  - [x] `jump`: from None to non-DEFINE (allowed, with warning)
- [x] Implement `transition_phase(agent, new_phase)` — validate, update state, log progress
  - [x] Calls `is_phase_valid_transition` for validation
  - [x] Calls `workflow_state.save_current_phase` to persist
  - [x] Calls `workflow_state.append_progress_event` with `phase_change` event
  - [x] Returns transition info dict or None on failure
- [x] Handle invalid phase names — return safe defaults, log warning
- [x] All functions are fail-safe — exceptions return safe defaults
- [x] Focused unit tests in `tests/test_phase_governance.py`
  - [x] `get_expected_skills` tested for all 6 phases
  - [x] `get_expected_skills("invalid")` returns empty list
  - [x] `is_phase_valid_transition` tested for: initial, forward, rewind, jump, reentry, invalid
  - [x] `transition_phase` tested with mock agent (state write + progress log)
  - [x] `transition_phase` tested with invalid phase name
  - [x] `get_current_phase` tested with missing state, present state, corrupt state

**Acceptance criteria:**
- [x] Helper provides correct skill lists for all 6 phases
- [x] Transition validation produces correct types and warnings
- [x] `pytest tests/test_phase_governance.py -v` — all green
- [x] Existing 473 tests remain green

**Spec ref:** Phase Model, Phase Helper API
**Plan ref:** Task 1

### Phase 1 checkpoint
- [x] `pytest tests/test_phase_governance.py -v` — all green (63 tests)
- [x] Phase helper provides correct skill lists for all 6 phases
- [x] Transition validation produces correct types and warnings
- [x] Existing 473 tests remain green

---

## Phase 2: Correction deduplication

### Task 2: Add correction deduplication to `helpers/phase_governance.py`
- [x] Add `gate_correction` to `_VALID_EVENT_TYPES` in `helpers/workflow_state.py`
- [x] Implement `get_last_correction_for_context(agent, tool_name, candidate)`
  - [x] Reads progress log via `workflow_state.read_progress_log`
  - [x] Filters for `gate_correction` events matching candidate
  - [x] Returns most recent matching event or None
  - [x] Handles missing/empty progress log gracefully
- [x] Implement `should_suppress_correction(agent, tool_name, candidate, cooldown_seconds=300.0)`
  - [x] Calls `get_last_correction_for_context` to find recent correction
  - [x] Returns True if correction exists within cooldown window
  - [x] Returns False if no correction exists or outside cooldown
  - [x] Returns False for different candidate (per-candidate cooldown)
- [x] All functions are fail-safe — exceptions return safe defaults (False for `should_suppress`)
- [x] Focused unit tests extending `tests/test_phase_governance.py`
  - [x] `get_last_correction_for_context` with no progress log → returns None
  - [x] `get_last_correction_for_context` with unrelated events → returns None
  - [x] `get_last_correction_for_context` with matching correction → returns event
  - [x] `get_last_correction_for_context` with multiple corrections → returns most recent
  - [x] `should_suppress_correction` with no prior corrections → returns False
  - [x] `should_suppress_correction` with recent correction within cooldown → returns True
  - [x] `should_suppress_correction` with old correction outside cooldown → returns False
  - [x] `should_suppress_correction` with recent correction for different candidate → returns False
- [x] Extend `tests/test_workflow_state.py` for `gate_correction` event type
  - [x] `gate_correction` is accepted by `append_progress_event`
  - [x] Event is readable via `read_progress_log`

**Acceptance criteria:**
- [x] Correction deduplication logic works correctly
- [x] `gate_correction` is a valid event type
- [x] `pytest tests/test_phase_governance.py -v` — all green
- [x] Existing tests remain green

**Spec ref:** Checkpoint-Aware Deduplication, Phase Helper API
**Plan ref:** Task 2

### Phase 2 checkpoint
- [x] `pytest tests/test_phase_governance.py -v` — all green
- [x] Correction deduplication logic works correctly
- [x] `gate_correction` is a valid event type
- [x] Existing tests remain green

---

## Phase 3: Phase-aware enforcer integration

### Task 3: Extend `_10_skill_enforcer.py` with phase-aware decision flow
- [x] Add `phase_governance` to `_import_helpers` in the enforcer
  - [x] Import `get_current_phase`, `get_expected_skills`, `should_suppress_correction` from `helpers.phase_governance`
  - [x] Use importlib pattern (load via `_load_module_by_path`)
- [x] Add phase-aware decision flow in the enforcer's `execute` method
  - [x] Read `phase_governance_enabled` from config (default: true)
  - [x] When enabled and phase known:
    - [x] Get expected skills for current phase
    - [x] Check if candidate is expected in current phase
    - [x] If candidate is NOT expected in this phase:
      - [x] Log `unexpected_for_phase` telemetry decision
      - [x] Skip correction (return without action)
    - [x] If candidate IS expected:
      - [x] Check `should_suppress_correction` for cooldown
      - [x] If suppressed: log `suppressed_duplicate` telemetry, skip correction
      - [x] If not suppressed: proceed with normal correction flow
  - [x] When enabled but phase unknown: proceed with phase-agnostic logic
  - [x] When disabled: proceed with Slice 1 logic unchanged
- [x] Enrich corrective warning message with phase context
  - [x] Include "In the BUILD phase, this skill is expected" when phase is known
- [x] Log `gate_correction` progress event after correction is issued
  - [x] Event includes: `candidate`, `phase`, `tool`, `ts`
- [x] Enrich telemetry decision records with `phase` field
  - [x] `phase` field set when phase is known, omitted when unknown
- [x] Enforcer remains fail-safe — phase logic exceptions don't break the loop
  - [x] Phase logic is inside the existing top-level try/except
- [x] Behavioral tests in `tests/test_skill_enforcer.py` (extend existing)
  - [x] DEFINE phase + missing `spec-driven-development` → correction issued
  - [x] BUILD phase + missing `test-driven-development` → correction issued
  - [x] BUILD phase + missing `shipping-and-launch` → suppressed (`unexpected_for_phase`)
  - [x] SHIP phase + missing `shipping-and-launch` → correction issued
  - [x] Unknown phase + missing skill → phase-agnostic correction (backward compat)
  - [x] `phase_governance_enabled: false` → Slice 1 behavior preserved
  - [x] Repeated correction within cooldown → suppressed (`suppressed_duplicate`)
  - [x] Correction after cooldown → allowed
  - [x] Telemetry includes `phase` field when known
  - [x] Correction message includes phase context when known
  - [x] Source-level test: enforcer body still has top-level try/except
  - [x] No nudge() used

**Acceptance criteria:**
- [x] Phase-aware corrections are contextually appropriate
- [x] Duplicate corrections are suppressed
- [x] `pytest tests/test_skill_enforcer.py -v` — all green (38 tests)
- [x] `pytest tests/test_phase_governance.py -v` — all green (63 tests)
- [x] Existing tests remain green

**Spec ref:** Phase-Aware Enforcement, Enforcement Decision Flow, Checkpoint-Aware Deduplication
**Plan ref:** Task 3

### Phase 3 checkpoint
- [x] `pytest tests/test_skill_enforcer.py -v` — all green (including new phase-aware tests)
- [x] `pytest tests/test_phase_governance.py -v` — all green
- [x] Phase-aware corrections are contextually appropriate
- [x] Duplicate corrections are suppressed
- [x] Existing tests remain green

---

## Phase 4: Config surface and telemetry enrichment

### Task 4: Add config keys and enrich telemetry
- [x] Add `phase_governance_enabled: true` to `default_config.yaml`
  - [x] Add comment: "# Set to false to disable phase-aware enforcement"
- [x] Add `enforcement_correction_cooldown_seconds: 300` to `default_config.yaml`
  - [x] Add comment: "# Minimum seconds between corrections for the same candidate"
- [x] Verify telemetry `gate_decision` events include `phase` field when phase is known
- [x] Verify telemetry records include relevant phase context
- [x] Config-disabled test: `phase_governance_enabled: false` → zero behavioral change
- [x] Focused tests for config-disabled behavior
  - [x] Enforcer ignores phase when disabled
  - [x] Correction dedup is skipped when disabled

**Acceptance criteria:**
- [x] Config file has new keys with sensible defaults and comments
- [x] Telemetry records include phase context
- [x] Config opt-out produces zero behavioral change
- [x] `pytest tests/test_skill_enforcer.py -v` — all green

**Spec ref:** Config Surface
**Plan ref:** Task 4

### Phase 4 checkpoint
- [x] `default_config.yaml` has new keys with sensible defaults
- [x] Telemetry records include phase context
- [x] Existing tests remain green

---

## Phase 5: Integration verification and regression

### Task 5: Full integration verification and regression testing
- [x] Run full test suite: `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short`
  - [x] All existing 473+ tests green
  - [x] All new phase-aware tests green
  - [x] Zero regressions
- [x] Verify phase-aware enforcement in observe mode
  - [x] Logs would-fire with phase context
  - [x] Does NOT call classifier
  - [x] Does NOT mutate tool_args
- [x] Verify phase-aware enforcement in enforce mode
  - [x] Corrects with phase context in message
  - [x] Suppresses wrong-phase candidates
  - [x] Suppresses duplicate corrections
- [x] Verify correction deduplication prevents loops
- [x] Verify phase-agnostic fallback when phase is unknown
- [x] Verify config opt-out when `phase_governance_enabled: false`
- [x] Verify progress log records `gate_correction` events
- [x] Verify rehydrate extension restores phase state (no changes needed, verify it works)
- [x] Verify persist extension saves phase transitions (no changes needed, verify it works)
- [x] Manual review: no `nudge()` or forced tool rewrites
- [x] Manual review: enforcer body has top-level try/except
- [x] Manual review: no `InterventionException` or hard human-intervention mode

**Acceptance criteria:**
- [x] Full suite green, no regressions (550 passed, 42 skipped)
- [x] All phase-aware behaviors work end-to-end
- [x] Slice 1 and Slice 2 integration verified

**Spec ref:** Success Criteria, Boundaries
**Plan ref:** Task 5

### Final checkpoint: Slice 3 complete
- [x] Workflow state influences enforcement
- [x] Corrections are smarter and less stateless
- [x] Plugin now owns workflow governance and workflow durability together
- [x] Full suite green, no regressions

---

## Notes

- Planning/spec/docs live in **`/a0/usr/projects/a0_agent_skills`**
- Implementation lives in **`/a0/usr/plugins/a0_agent_skills`**
- Do not confuse the umbrella roadmap with the current shipped slice
- Do not broaden scope into `_permissions` or `_tracing`
- Phase-skill mapping matches the plugin's existing routing rules from the system prompt
- `gate_correction` events in progress_log.jsonl enable future analytics on correction patterns
