# Implementation Plan: Phase-Aware Workflow Governance

> Generated from spec `docs/specs/phase-aware-governance-spec.md`.
>
> **Status in broader roadmap:** This is the **Phase 3 / Slice 3** implementation plan under the umbrella workflow-governance roadmap.
> For the broader roadmap, see:
> - `docs/specs/a0-agent-skills-workflow-governance-spec.md`
> - `docs/plans/a0-agent-skills-workflow-governance-plan.md`
> - `tasks/a0-agent-skills-workflow-governance-todo.md`

## Overview

This plan implements **phase-aware workflow governance** for `a0_agent_skills`, ensuring that the enforcement gate considers the current workflow phase when making correction decisions, and that repeated corrections are suppressed via cooldown-based deduplication.

The feature has two interdependent components:

1. **Phase-state model and phase-aware rules** — a dedicated helper module (`helpers/phase_governance.py`) that defines the six-phase lifecycle, phase-skill mapping, transition validation, and correction deduplication logic.
2. **Phase-aware enforcement** — broadening the existing `_10_skill_enforcer.py` to read current phase, check phase-skill alignment, and suppress duplicate corrections.

The implementation follows the same principles as Slices 1 and 2:

1. **User-space only** — all implementation lives in `/a0/usr/plugins/a0_agent_skills`; no core framework edits.
2. **Fail-safe extensions** — all extension bodies wrapped in try/except; phase-awareness failures never break the agent loop.
3. **Additive, not replacing** — phase-awareness extends the existing enforcer; it does not replace the prefilter/classify flow.
4. **Measure everything** — focused tests for every new behavior before broad rollout.

## Architecture Decisions

- **New helper module:** `helpers/phase_governance.py` owns the phase model, phase-skill mapping, transition validation, and correction deduplication. It does NOT own state I/O — that remains in `helpers/workflow_state.py`.
- **Enforcer extension, not replacement:** The existing `_10_skill_enforcer.py` is extended with phase-aware checks. No new enforcement extension is created.
- **Phase-skill mapping is hardcoded in MVP:** The mapping is a Python dict in the helper module. Future slices may make it YAML-configurable.
- **Cooldown is per-candidate and time-based:** Each candidate skill has its own cooldown window, tracked via progress-log events.
- **`gate_correction` is a first-class event type:** Added to `_VALID_EVENT_TYPES` in `workflow_state.py` so progress-log queries can find it reliably.
- **Backward compatible:** When `phase_governance_enabled: false` or phase is unknown, the enforcer behaves exactly as Slice 1.

## Dependency Graph

```text
Slice 2 complete (473 tests passing)
   │
   ├── Task 1: Phase helper + phase-skill mapping + transition validation
   │       │
   │       ├── Task 2: Correction deduplication logic
   │       │       │
   │       │       └── Task 3: Phase-aware enforcer integration
   │       │               │
   │       │               └── Task 4: Config surface + telemetry enrichment
   │       │
   │       └── Task 5: Integration verification + regression
   │
   └── Full regression verification
```

## Task List

### Phase 1: Phase Helper and Phase-Skill Mapping

## Task 1: Create `helpers/phase_governance.py` with phase model and transition validation

**Description:**
Build the phase governance helper module. This module provides functions to query the current phase, get expected skills for a phase, validate phase transitions, and execute transitions. It depends on the existing `workflow_state` helper for state I/O but owns the phase logic itself.

**Acceptance criteria:**
- [ ] `PHASE_ORDER` constant defines the canonical phase sequence
- [ ] `PHASE_SKILL_MAP` constant defines expected skills per phase
- [ ] `get_current_phase(agent)` returns current phase or None
- [ ] `get_expected_skills(phase)` returns correct skill list for all 6 phases
- [ ] `get_expected_skills("invalid")` returns empty list
- [ ] `is_phase_valid_transition(None, "DEFINE")` returns initial transition
- [ ] `is_phase_valid_transition("DEFINE", "PLAN")` returns forward transition
- [ ] `is_phase_valid_transition("BUILD", "DEFINE")` returns rewind with warning
- [ ] `is_phase_valid_transition(None, "BUILD")` returns jump with warning
- [ ] `is_phase_valid_transition("BUILD", "BUILD")` returns reentry
- [ ] `transition_phase(agent, new_phase)` validates, updates state, logs progress
- [ ] `transition_phase` handles invalid phase names gracefully
- [ ] `transition_phase` returns None on failure (missing state dir, etc.)
- [ ] All functions are fail-safe — exceptions return safe defaults

**Verification:**
- [ ] Focused unit tests in `tests/test_phase_governance.py`
- [ ] `get_expected_skills` tested for all 6 phases
- [ ] Transition validation tested for: initial, forward, rewind, jump, reentry, invalid
- [ ] `transition_phase` tested with mock agent (state write + progress log)
- [ ] `transition_phase` tested with invalid phase name
- [ ] `get_current_phase` tested with missing state, present state, corrupt state

**Dependencies:** Slice 2 complete

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/phase_governance.py` (new)
- `/a0/usr/plugins/a0_agent_skills/tests/test_phase_governance.py` (new)

**Estimated scope:** Medium (foundational — Tasks 2-4 depend on this)

### Checkpoint: After Task 1

- [ ] `pytest tests/test_phase_governance.py -v` — all green
- [ ] Phase helper provides correct skill lists for all 6 phases
- [ ] Transition validation produces correct types and warnings
- [ ] Existing 473 tests remain green

---

### Phase 2: Correction Deduplication

## Task 2: Add correction deduplication to `helpers/phase_governance.py`

**Description:**
Add functions that check the progress log for recent correction events and determine whether a new correction should be suppressed. This prevents the enforcer from issuing the same correction repeatedly within a cooldown window.

Also add `gate_correction` to the `_VALID_EVENT_TYPES` in `workflow_state.py` so it is a recognized event type.

**Acceptance criteria:**
- [ ] `gate_correction` added to `_VALID_EVENT_TYPES` in `workflow_state.py`
- [ ] `get_last_correction_for_context(agent, tool_name, candidate)` returns the most recent correction event for that candidate, or None
- [ ] `should_suppress_correction(agent, tool_name, candidate, cooldown_seconds)` returns True when a correction was logged within the cooldown window
- [ ] `should_suppress_correction` returns False when no prior corrections exist
- [ ] `should_suppress_correction` returns False when prior correction is outside the cooldown window
- [ ] Functions handle missing/empty progress log gracefully
- [ ] All functions are fail-safe

**Verification:**
- [ ] Unit tests for `get_last_correction_for_context` with:
  - [ ] No progress log → returns None
  - [ ] Progress log with unrelated events → returns None
  - [ ] Progress log with matching correction → returns the event
  - [ ] Progress log with multiple corrections → returns most recent
- [ ] Unit tests for `should_suppress_correction` with:
  - [ ] No prior corrections → returns False
  - [ ] Recent correction within cooldown → returns True
  - [ ] Old correction outside cooldown → returns False
  - [ ] Recent correction for different candidate → returns False
- [ ] `_VALID_EVENT_TYPES` update verified in `test_workflow_state.py`

**Dependencies:** Task 1

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/helpers/phase_governance.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/helpers/workflow_state.py` (extend: add `gate_correction` to `_VALID_EVENT_TYPES`)
- `/a0/usr/plugins/a0_agent_skills/tests/test_phase_governance.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_workflow_state.py` (extend)

**Estimated scope:** Medium

### Checkpoint: After Task 2

- [ ] `pytest tests/test_phase_governance.py -v` — all green
- [ ] Correction deduplication logic works correctly
- [ ] `gate_correction` is a valid event type
- [ ] Existing tests remain green

---

### Phase 3: Phase-Aware Enforcer Integration

## Task 3: Extend `_10_skill_enforcer.py` with phase-aware decision flow

**Description:**
Broaden the existing enforcement gate to read the current phase, check phase-skill alignment, and suppress duplicate corrections. The existing prefilter → classify → correct flow is preserved; phase-aware checks are inserted as additional decision points.

**Acceptance criteria:**
- [ ] Enforcer reads `phase_governance_enabled` from config
- [ ] When `phase_governance_enabled: true` and phase is known:
  - [ ] Enforcer checks if candidate is expected in current phase
  - [ ] If candidate is NOT expected: logs `unexpected_for_phase` and skips correction
  - [ ] If candidate IS expected: checks correction dedup before proceeding
  - [ ] If correction was recently issued: logs `suppressed_duplicate` and skips
  - [ ] If correction is fresh: proceeds with normal correction flow
- [ ] When `phase_governance_enabled: true` but phase is unknown: falls back to phase-agnostic logic
- [ ] When `phase_governance_enabled: false`: enforcer behaves exactly as Slice 1
- [ ] Corrective warning message includes phase context when phase is known
- [ ] Telemetry decision records include `phase` field when phase is known
- [ ] After correction is issued, a `gate_correction` progress event is logged
- [ ] Enforcer remains fail-safe — phase logic exceptions don't break the loop

**Verification:**
- [ ] Behavioral tests in `tests/test_skill_enforcer.py` (extend existing):
  - [ ] DEFINE phase + missing `spec-driven-development` → correction issued
  - [ ] BUILD phase + missing `test-driven-development` → correction issued
  - [ ] BUILD phase + missing `shipping-and-launch` → suppressed (`unexpected_for_phase`)
  - [ ] SHIP phase + missing `shipping-and-launch` → correction issued
  - [ ] Unknown phase + missing skill → phase-agnostic correction (backward compat)
  - [ ] `phase_governance_enabled: false` → Slice 1 behavior preserved
  - [ ] Repeated correction within cooldown → suppressed (`suppressed_duplicate`)
  - [ ] Correction after cooldown → allowed
  - [ ] Telemetry includes `phase` field
  - [ ] Correction message includes phase context
- [ ] Source-level test: enforcer body still has top-level try/except

**Dependencies:** Tasks 1, 2

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/extensions/python/tool_execute_before/_10_skill_enforcer.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_phase_governance.py` (extend)

**Estimated scope:** Large (core behavioral change — needs thorough testing)

### Checkpoint: After Task 3

- [ ] `pytest tests/test_skill_enforcer.py -v` — all green (including new phase-aware tests)
- [ ] `pytest tests/test_phase_governance.py -v` — all green
- [ ] Phase-aware corrections are contextually appropriate
- [ ] Duplicate corrections are suppressed
- [ ] Existing 473 tests remain green

---

### Phase 4: Config Surface and Telemetry Enrichment

## Task 4: Add config keys and enrich telemetry with phase context

**Description:**
Add the new config keys to `default_config.yaml` and ensure telemetry decision records include phase information when available.

**Acceptance criteria:**
- [ ] `phase_governance_enabled: true` added to `default_config.yaml`
- [ ] `enforcement_correction_cooldown_seconds: 300` added to `default_config.yaml`
- [ ] Telemetry `gate_decision` events include `phase` field when phase is known
- [ ] Telemetry `gate_decision` events include `transition_type` or `phase_context` when relevant
- [ ] Config keys are documented with comments in `default_config.yaml`

**Verification:**
- [ ] Config file contains both new keys with correct defaults
- [ ] Telemetry tests confirm `phase` field presence
- [ ] Config disabled (`phase_governance_enabled: false`) produces zero behavioral change

**Dependencies:** Task 3

**Files likely touched:**
- `/a0/usr/plugins/a0_agent_skills/default_config.yaml` (extend)
- `/a0/usr/plugins/a0_agent_skills/tests/test_skill_enforcer.py` (extend)

**Estimated scope:** Small

### Checkpoint: After Task 4

- [ ] `default_config.yaml` has new keys with sensible defaults
- [ ] Telemetry records include phase context
- [ ] Existing tests remain green

---

### Phase 5: Integration and Regression

## Task 5: Full integration verification and regression testing

**Description:**
Run the full test suite to verify no regressions, confirm all new behaviors work end-to-end, and validate that the phase-aware governance integrates cleanly with both Slice 1 (enforcement gate) and Slice 2 (durable state).

**Acceptance criteria:**
- [ ] Full test suite green (473+ existing + new tests)
- [ ] Phase-aware enforcement works in observe mode (logs only)
- [ ] Phase-aware enforcement works in enforce mode (corrects with phase context)
- [ ] Correction deduplication prevents loops
- [ ] Phase-agnostic fallback works when phase is unknown
- [ ] Config opt-out works when `phase_governance_enabled: false`
- [ ] Progress log records `gate_correction` events
- [ ] Rehydrate extension correctly restores phase state (no changes needed, but verify)
- [ ] Persist extension correctly saves phase transitions (no changes needed, but verify)

**Verification:**
- [ ] `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ --tb=short` — all green
- [ ] Manual review: no `nudge()`, no forced tool rewrites, no core edits
- [ ] Manual review: enforcer body has top-level try/except
- [ ] Manual review: no `InterventionException` or hard human-intervention mode

**Dependencies:** Tasks 1-4

**Files likely touched:** None (verification only)

**Estimated scope:** Small

### Final Checkpoint: Slice 3 Complete

- [ ] Workflow state influences enforcement
- [ ] Corrections are smarter and less stateless
- [ ] Plugin now owns workflow governance and workflow durability together
- [ ] Full suite green, no regressions

---

## Risk Areas and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Phase-skill mapping is too narrow (misses valid skills) | False negatives — enforcer suppresses valid corrections | Medium | Default to permissive: if candidate is not in phase-skill map at all, proceed with normal correction logic. Only suppress when candidate is explicitly known to belong to a different phase. |
| Phase-skill mapping is too broad (allows wrong-phase skills) | Some false positives persist | Low | Acceptable in MVP — the classifier still runs in enforce mode. Phase filtering is a first-pass screen, not a replacement. |
| Cooldown window too long | Real corrections suppressed | Low | Default 300 seconds (5 minutes). Configurable via `enforcement_correction_cooldown_seconds`. |
| Cooldown window too short | Correction loops persist | Low | 5 minutes is conservative enough for typical agent loop cadence. |
| Phase state goes stale | Corrections based on wrong phase | Medium | Phase is re-read from state on every enforcer invocation. Rehydration ensures phase survives compaction. |
| Enforcer import failures break the loop | Agent loop crash | Very Low | All new imports wrapped in the existing top-level try/except. Import failures produce a debug log and skip phase-aware logic. |
| `gate_correction` event type conflicts | Progress log schema drift | Very Low | Added as a first-class type alongside existing types. Structured fields match existing patterns. |

## Summary

| Task | Scope | New Files | Modified Files | Estimated Tests |
|------|-------|-----------|----------------|-----------------|
| 1. Phase helper | Medium | `helpers/phase_governance.py`, `tests/test_phase_governance.py` | — | ~20 |
| 2. Correction dedup | Medium | — | `helpers/phase_governance.py`, `helpers/workflow_state.py`, `tests/*` | ~15 |
| 3. Phase-aware enforcer | Large | — | `_10_skill_enforcer.py`, `tests/test_skill_enforcer.py`, `tests/test_phase_governance.py` | ~15 |
| 4. Config + telemetry | Small | — | `default_config.yaml`, `tests/test_skill_enforcer.py` | ~5 |
| 5. Integration verify | Small | — | — | 0 (verification) |
| **Total** | | **2 new** | **4 modified** | **~55 new** |
