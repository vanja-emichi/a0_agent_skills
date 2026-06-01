# Todo: Enforcement Settings Verification

## Phase 1: Foundation

- [x] **Task 1: Wire `skill_graph_validate_on_build` (dead setting)** ✅
  - Wired in `_10_skill_enforcer.py` — reads config, calls `validate_graph()`, logs findings
  - 4 ON/OFF tests added in `test_skill_enforcer.py`
  - Verified: `grep -rn 'skill_graph_validate'` returns hits in both helpers and extensions

- [x] **Task 2: Add ON-path test for `skill_next_skill_hints`** ✅
  - ON-path test added in `test_workflow_rehydrate.py`
  - Verified: both ON and OFF tests pass

### Checkpoint: Foundation ✅
- [x] All Phase 1 tests pass (830 passed)
- [x] `skill_graph_validate_on_build` reads from config
- [x] `skill_next_skill_hints` has ON/OFF coverage

---

## Phase 2: Enable Settings One at a Time ✅

- [x] **Task 3: Enable `phase_governance_enabled`** ✅
  - Set `phase_governance_enabled` to `"true"` in config.json
  - Full test suite: 830 passed, 43 skipped ✅
  - No fixes needed — enabled cleanly

- [x] **Task 4: Enable `skill_contracts_enabled`** ✅
  - Set `skill_contracts_enabled` to `"true"` in config.json
  - Full test suite: 830 passed, 43 skipped ✅
  - No fixes needed — enabled cleanly

- [x] **Task 5: Enable `skill_next_skill_hints`** ✅
  - Set `skill_next_skill_hints` to `"true"` in config.json
  - Full test suite: 830 passed, 43 skipped ✅
  - No fixes needed — enabled cleanly

- [x] **Task 6: Enable `skill_graph_validate_on_build`** ✅
  - Set `skill_graph_validate_on_build` to `"true"` in config.json
  - Full test suite: 830 passed, 43 skipped ✅
  - No fixes needed — enabled cleanly

### Checkpoint: All Settings Enabled ✅
- [x] All 4 settings enabled ✅
- [x] All tests pass (830 passed, 43 skipped) ✅
- [x] No regressions ✅

---

## Phase 3: Already-Enabled Settings Verification ✅

- [x] **Task 10: Verify `workflow_state_enabled` (currently ON)** ✅
  - ON + OFF tests already exist in test_workflow_rehydrate.py (TestConfigDisabled: 3 tests)
  - ON + OFF tests already exist in test_persist_workflow_state.py (TestConfigDisabled: 2 tests)
  - No new tests needed

- [x] **Task 11: Verify `artifact_inference_enabled` (currently ON)** ✅
  - ON + OFF tests already exist in test_artifact_inference.py (TestConfigDisabled: 2 tests)
  - test_artifact_inference_disabled verifies no state written when OFF
  - No new tests needed

- [x] **Task 12: Verify `telemetry_enabled` (currently ON)** ✅
  - Extensive ON/OFF coverage in test_skill_telemetry.py, test_telemetry_default_and_hooks.py, test_gate_telemetry.py
  - Tests cover: bool True/False, string "true"/"false", int 1/0, string "yes"/"1"
  - No new tests needed

- [x] **Task 13: Verify `telemetry_debug` wiring (default OFF)** ✅
  - Already wired: extensions/python/tool_execute_after/_05_skill_telemetry.py line 231
  - ON/OFF tests exist: test_skill_telemetry.py (test_debug_log_emits_when_enabled + test_debug_log_silent_when_disabled)
  - No new tests or wiring needed

### Checkpoint: All Settings Verified ✅
- [x] All 4 already-enabled settings have ON/OFF test coverage ✅
- [x] `telemetry_debug` is wired and confirmed working ✅
- [x] All tests pass (830 passed, 43 skipped) ✅

---

## Phase 4: Bug Fix & Eval Runner ✅

- [x] **Task 7: Fix Bug 4 — spec status checking** ✅
  - Added `_scan_active_specs()` and `_format_active_specs_block()` to rehydrate extension
  - Scans docs/specs/*-spec.md files, reads `**Status:**` field from header
  - Filters out SHIPPED/Approved/Completed/Done specs from "Active Specs" section in state block
  - Shows Draft/In Progress specs with status tags
  - Tests: 4 new tests in TestSpecStatusFiltering (shipped excluded, approved excluded, in-progress shown, no specs dir safe)

- [x] **Task 8: Create eval runner** ✅
  - Created `tests/eval_runner.py` — standalone script runnable via `python tests/eval_runner.py`
  - Reads eval fixtures from `tests/eval_fixtures/skill-activation-evals.json`
  - Simulates enforcement pipeline with ON/OFF for each setting
  - Outputs JSON report with ON vs OFF comparison and behavioral change detection
  - Tested with 3+ fixtures: 12 comparisons, 4 behavioral changes detected

### Checkpoint: Bug Fix & Eval Runner ✅
- [x] Bug 4 fixed and tested ✅
- [x] Eval runner created ✅
- [x] Eval report shows behavioral difference between ON/OFF ✅
- [x] All tests pass (834 passed, 43 skipped) ✅

---

## Phase 5: Routing Rules ✅

- [x] **Task 9: Update routing rules with 13 lessons learned** ✅
  - Applied doubt-driven-development: adversarial review found 3 critical + 6 important issues
  - Revised approach: only 5 net lines added (129 → 129), behavioral guidelines moved to promptinclude
  - Routing rules changes: SHIP row updated, 2 anti-rationalization rows added, phase transition note added
  - Behavioral guidelines (delegation, session start, skill execution) moved to `.a0proj/instructions/session-and-delegation-guidelines.promptinclude.md`
  - All 834 tests pass, line budget enforced (129 ≤ 130)

### Checkpoint: Complete ✅
- [x] All outcome criteria met
- [x] All implementation criteria met
- [x] Full test suite passes (834 passed, 43 skipped)
- [x] Ready for REVIEW phase
