# Tasks: Approval Gate Wiring and Governance Hardening

**Spec:** `docs/specs/approval-gate-wiring-spec.md`
**Plan:** `docs/plans/approval-gate-wiring-plan.md`
**Status:** Shipped

## Phase 1: Wire the Approval Trigger

### Task 1: Add Natural Language Approval Detection
- [x] Create `extensions/python/tool_execute_before/_20_approval_gate.py`
- [x] Add `detect_approval_in_text(text) -> bool` with word-boundary matching
- [x] Approval phrases: "approved", "approve", "looks good", "good to go", "proceed", "ship it", "lgtm", "let's go"
- [x] NOT detect: "unapproved", "fix section 3", "approved by whom?", silence
- [x] When approval detected + artifact exists → call `mark_artifact_approved`
- [x] Bootstrap pattern matches other extensions
- [x] Fail-safe: all exceptions return without blocking

**Acceptance:** 6+ unit tests pass; full suite green (839+); live test shows `(approved)` tag after saying "approved"
- **Result:** 32 unit tests pass; full suite 871 passed, 43 skipped, 0 failures
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/test_approval_trigger.py tests/ -v --tb=short`

### Task 2: Add Phase Gate Check (Approval Before Transition)
- [x] Add `is_artifact_approved(agent, artifact_type)` to `workflow_state.py`
- [x] Add `PHASE_ARTIFACT_MAP` to `phase_governance.py` (canonical mapping)
- [x] Add `check_phase_approval_gate(agent, from, to, enforcement_mode)` to `phase_governance.py`
- [x] Observe mode + unapproved → log warning, allow transition
- [x] Enforce mode + unapproved → log warning, block transition
- [x] Approved → transition proceeds normally
- [x] Document phase→artifact mapping: DEFINE→spec, PLAN→plan, BUILD→todo, REVIEW→review, SHIP→report
- [x] VERIFY phase intentionally has no artifact mapping (skips gate)
- [x] Reentry, rewind, initial/jump entries skip the gate
- [x] Fail-safe: errors return True (never blocks agent loop)

**Acceptance:** 32 unit tests for blocked/allowed/observe/no-mapping/non-forward/fail-safe/logging cases pass; full suite green (903 passed)
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/test_approval_phase_gate.py tests/ -v --tb=short`

### Task 3: Add Mtime Invalidation
- [x] `mark_artifact_approved` stores `approved_mtime[artifact_type] = os.path.getmtime(artifact_path)`
- [x] `is_artifact_approved` checks current mtime against stored; returns False if changed
- [x] Graceful handling: missing file → approval invalid
- [x] Existing approval tests extended with mtime scenarios

**Acceptance:** 9 mtime tests pass; full suite 912 passed, 43 skipped, 0 failures
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/test_workflow_state.py::TestMtimeInvalidation -v --tb=short`

### Checkpoint: Phase 1 Complete
- [ ] All 3 tasks complete
- [ ] Full test suite green (839+ pass)
- [ ] Approval trigger works in live session
- [ ] Phase gate warns when unapproved
- [ ] Mtime invalidation works
- [ ] **Review with user before Phase 2**

---

## Phase 2: Enable Data Collection

### Task 4: Enable Shadow Sampling
- [x] `default_config.yaml` has `enforcement_shadow_sample_rate: 0.1`
- [x] Shadow sampling logic implemented in `_10_skill_enforcer.py` (observe branch)
- [x] Classifier invoked on sampled calls (mocked tests confirm)
- [x] Telemetry logs shadow decisions with `mode='observe_shadow'`
- [x] No behavioral change (observe mode, no corrections injected)
- [x] 8 new tests for shadow sampling (rate 0/1/triggered/skipped/no-correction/no-mutation/fail-safe/enforce-mode)

**Acceptance:** 920 passed, 43 skipped, 0 failures; shadow sampling tests verify classifier invocation at 10% rate
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/test_skill_enforcer.py::TestShadowSampling -v --tb=short`

### Checkpoint: Phase 2 Complete
- [ ] Shadow sampling enabled
- [ ] Telemetry shows classifier activity
- [ ] **Review with user before Phase 3**

---

## Phase 3: Improve Classifier Accuracy

### Task 5: Tune Classifier to ≥80% Accuracy
- [x] Create eval runner script (`tests/eval_classifier.py`) with test fixtures
- [x] Measure baseline accuracy (87.2% on 94 fixtures)
- [x] Tune classifier patterns and prompt
- [x] Achieve ≥80% accuracy on eval fixtures (93.6%)
- [x] Document what was changed and why (`docs/reports/classifier-tuning.md`)
- [x] Full suite green (920 passed, 43 skipped, 0 failures)

**Acceptance:** 93.6% accuracy (88/94 fixtures); near-miss 100%; positive 89.1%; full suite 920 passed
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python tests/eval_classifier.py && python -m pytest tests/ -v --tb=short 2>&1 | tail -5`

### Checkpoint: Phase 3 Complete
- [ ] Classifier accuracy ≥ 80%
- [ ] Tuning documented
- [ ] **Review with user before Phase 4**

---

## Phase 4: Enable Enforce Mode

### Task 6: Switch to Enforce Mode
- [x] `config.json` has `enforcement_mode: "enforce"`
- [x] `default_config.yaml` has comment explaining observe vs enforce
- [x] Telemetry shows `state: should_correct` entries being injected
- [x] No false positives on legitimate skill-loaded calls
- [x] 8 new enforce mode tests pass (correction injection, no false positives, dedup, fail-safe, config regression guards, gate_correction event)
- [x] Existing enforcement config test updated for enforce mode
- [x] Full suite: 928 passed, 43 skipped, 0 failures
- [x] Classifier eval: 93.6% accuracy (88/94 fixtures)

**Acceptance:** 928 passed, 43 skipped, 0 failures; 93.6% accuracy; enforce mode tests verify correction injection, no false positives, dedup, fail-safe
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ -v --tb=short && python tests/eval_classifier.py`

### Checkpoint: Phase 4 Complete
- [ ] Enforce mode enabled
- [ ] Corrections being injected in live session
- [ ] No false positives
- [ ] **Review with user before Phase 5**

---

## Phase 5: Strengthen Routing Rules

### Task 7: Add 4 Mandatory Gates to Routing Rules
- [x] Routing rules section for each of G1-G4 gates
- [x] Trigger phrases for each gate
- [x] Source skills cited from checkpoint analysis report
- [x] Anti-rationalization rows for skipping approval

**Acceptance:** Existing routing tests pass; routing rules include all 4 gates
- **Result:** 928 passed, 43 skipped, 0 failures; 123-line prompt within 130-line budget
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/test_routing_rules_refactor.py tests/ -v --tb=short`

### Checkpoint: Phase 5 Complete
- [ ] Routing rules include 4 gates
- [ ] Existing routing tests pass
- [ ] No regression in routing behavior

---

## Phase 6: Full Acceptance Test

### Task 8: End-to-End Session Test
- [x] Full E2E session: spec → approval → plan → approval → build → review → ship
- [x] All 4 gates trigger at correct moments
- [x] No false approvals detected
- [x] Rehydration shows correct approval state at each phase
- [x] Telemetry logs all approval events
- [x] Document test run in `docs/reports/approval-gate-acceptance.md`
- [x] Update spec status to "Shipped"

**Acceptance:** All success criteria from spec met; documentation complete
**Result:** 968 passed, 43 skipped, 0 failures; 93.6% accuracy; 40 integration tests; acceptance report created
**Verify:** `cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ -v --tb=short && python tests/eval_classifier.py`

### Checkpoint: All Phases Complete
- [x] All 8 tasks complete
- [x] 4 approval gates trigger correctly in live session
- [x] Telemetry shows all decisions
- [x] Zero regressions in 839+ tests
- [x] Classifier accuracy ≥ 80%
- [x] Enforce mode is safe
- [x] Spec marked Shipped
- [x] Plan marked Shipped
- [x] Todo marked complete

---

## Quick Reference

**Spec:** `docs/specs/approval-gate-wiring-spec.md`
**Plan:** `docs/plans/approval-gate-wiring-plan.md`
**Report:** `docs/reports/skill-checkpoint-gate-analysis.md`

**Test commands:**
```bash
# Plugin tests
cd /a0/usr/plugins/a0_agent_skills && python -m pytest tests/ -v --tb=short

# Eval suite
cd /a0/usr/plugins/a0_agent_skills && python tests/run_enforcement_evals.py
```

**Key files:**
- `extensions/python/tool_execute_before/_20_approval_gate.py` (new)
- `helpers/phase_governance.py` (extend)
- `helpers/workflow_state.py` (extend for mtime)
- `prompts/agent.skills.routing.md` (update)
- `config.json` (update settings)
