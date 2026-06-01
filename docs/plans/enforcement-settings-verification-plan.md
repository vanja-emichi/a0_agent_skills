# Implementation Plan: Enforcement Settings Verification and Enablement

**Spec:** `docs/specs/enforcement-settings-verification-spec.md`
**Status:** Shipped

## Overview

Verify that ALL enforcement and workflow settings in `config.json` / `default_config.yaml` are fully wired and functional, then ensure they are all correctly enabled. Fix one dead setting (`skill_graph_validate_on_build`), fill test gaps, fix Bug 4, create an eval runner, and update routing rules.

### Important Discovery

During the sprint, we discovered that the enforcement gate is designed for **tool-call-level** violations (detecting when a skill should have been loaded for a specific tool call), NOT for **behavioral-level** violations (phase skipping, missing skill loads, ignored cross-references). The 8 reported routing bugs are behavioral violations that the enforcement gate cannot detect. Behavioral compliance is handled by routing rules and promptinclude guidelines, not enforcement settings. See the spec's "Known Limitations" section for details.

## Architecture Decisions

- **Enable one setting at a time** — each setting gets its own verification cycle
- **Run full test suite before and after each enable** — 825+ tests must pass
- **Observe mode only** — `enforcement_mode` stays `observe` (warnings, not blocks)
- **Dead setting must be wired before enabled** — `skill_graph_validate_on_build` has no code reading it

## Dependency Graph

```
Task 1: Wire skill_graph_validate_on_build (foundation)
    │
    ├── Task 2: Add ON-path test for skill_next_skill_hints
    │
    ├── Task 3: Enable phase_governance_enabled
    │       │
    │       └── Task 4: Enable skill_contracts_enabled
    │               │
    │               └── Task 5: Enable skill_next_skill_hints
    │                       │
    │                       └── Task 6: Enable skill_graph_validate_on_build
    │
    └── Task 7: Fix Bug 4 (spec status checking)
            │
            └── Task 8: Create eval runner
                    │
                    └── Task 9: Update routing rules
```

## Task List

### Phase 1: Foundation — Fix Dead Setting & Test Gaps

#### Task 1: Wire `skill_graph_validate_on_build` setting to code

**Description:** The setting exists in `default_config.yaml` and `config.json` but no code reads it. `validate_graph()` exists in `skill_contracts.py` (line 483) but is never called from config. Wire the setting to the validation function.

**Acceptance criteria:**
- [ ] `_10_skill_enforcer.py` reads `skill_graph_validate_on_build` from config
- [ ] When `true`, calls `validate_graph()` from `skill_contracts.py` on skill load
- [ ] When `false`, skips validation (no change in behavior)
- [ ] ON and OFF tests added to `test_skill_enforcer.py`

**Verification:**
- [ ] Tests pass: `python -m pytest tests/test_skill_enforcer.py -v --tb=short`
- [ ] Full suite passes: `python -m pytest tests/ --tb=short -q`

**Dependencies:** None

**Files likely touched:**
- `extensions/python/tool_execute_before/_10_skill_enforcer.py`
- `tests/test_skill_enforcer.py`

**Estimated scope:** Small (1-2 files)

---

#### Task 2: Add ON-path test for `skill_next_skill_hints`

**Description:** Only the OFF path is tested (rehydration omits hints when false). Add tests for the ON path — rehydration includes skill hints when the setting is true.

**Acceptance criteria:**
- [ ] Test: rehydration includes skill hints when `skill_next_skill_hints: true`
- [ ] Test: hints are populated from `get_skills_for_phase()` for current phase
- [ ] Both ON and OFF tests pass

**Verification:**
- [ ] Tests pass: `python -m pytest tests/test_workflow_rehydrate.py -v --tb=short`

**Dependencies:** None

**Files likely touched:**
- `tests/test_workflow_rehydrate.py`

**Estimated scope:** Small (1 file)

### Checkpoint: Foundation
- [ ] All tests pass (825+)
- [ ] `skill_graph_validate_on_build` is wired (no longer dead)
- [ ] `skill_next_skill_hints` has both ON and OFF tests
- [ ] Review before proceeding to Phase 2

---

### Phase 2: Enable Settings One at a Time

#### Task 3: Enable `phase_governance_enabled` and verify

**Description:** Change `config.json` to set `phase_governance_enabled` to `"true"`. Run tests and live eval to verify.

**Acceptance criteria:**
- [ ] `config.json` has `"phase_governance_enabled": "true"`
- [ ] All 825+ tests pass with setting enabled
- [ ] Live eval: write spec → plan → verify phase transitions are enforced
- [ ] No regressions in existing functionality

**Verification:**
- [ ] Tests pass: `python -m pytest tests/ --tb=short -q`
- [ ] Live eval: restart agent, write spec, verify phase governance fires

**Dependencies:** Task 1

**Files likely touched:**
- `config.json`

**Estimated scope:** Small (1 file, config change)

---

#### Task 4: Enable `skill_contracts_enabled` and verify

**Description:** Change `config.json` to set `skill_contracts_enabled` to `"true"`. Run tests and live eval.

**Acceptance criteria:**
- [ ] `config.json` has `"skill_contracts_enabled": "true"`
- [ ] All 825+ tests pass with setting enabled
- [ ] Live eval: load a skill → verify cross-references surfaced
- [ ] No regressions

**Verification:**
- [ ] Tests pass: `python -m pytest tests/ --tb=short -q`
- [ ] Live eval: restart agent, load skill, verify contract enforcement

**Dependencies:** Task 3

**Files likely touched:**
- `config.json`

**Estimated scope:** Small (1 file, config change)

---

#### Task 5: Enable `skill_next_skill_hints` and verify

**Description:** Change `config.json` to set `skill_next_skill_hints` to `"true"`. Run tests and live eval.

**Acceptance criteria:**
- [ ] `config.json` has `"skill_next_skill_hints": "true"`
- [ ] All 825+ tests pass
- [ ] Live eval: verify rehydrated state includes skill recommendations for current phase
- [ ] No regressions

**Verification:**
- [ ] Tests pass: `python -m pytest tests/ --tb=short -q`
- [ ] Live eval: restart agent, verify hints in rehydrated state

**Dependencies:** Tasks 2, 4

**Files likely touched:**
- `config.json`

**Estimated scope:** Small (1 file, config change)

---

#### Task 6: Enable `skill_graph_validate_on_build` and verify

**Description:** Change `config.json` to set `skill_graph_validate_on_build` to `"true"`. Run tests and live eval.

**Acceptance criteria:**
- [ ] `config.json` has `"skill_graph_validate_on_build": "true"`
- [ ] All 825+ tests pass
- [ ] Live eval: verify skill graph validation runs on build
- [ ] No regressions

**Verification:**
- [ ] Tests pass: `python -m pytest tests/ --tb=short -q`
- [ ] Live eval: restart agent, trigger skill build, verify validation

**Dependencies:** Task 1, Task 5

**Files likely touched:**
- `config.json`

**Estimated scope:** Small (1 file, config change)

### Checkpoint: All Settings Enabled
- [ ] All 4 previously-disabled settings are now enabled
- [ ] All tests pass (825+)
- [ ] No regressions
- [ ] Review before proceeding to Phase 3

---

### Phase 3: Bug Fix & Eval Runner

#### Task 7: Fix Bug 4 — Check spec status before proposing work

**Description:** The agent proposed already-shipped specs as new work because it only checked file existence, not spec status fields. Add spec status checking to prevent this.

**Acceptance criteria:**
- [ ] Function reads spec status field from spec files
- [ ] Specs with status `SHIPPED` are excluded from "next work" proposals
- [ ] Tests: shipped specs excluded, in-progress specs included

**Verification:**
- [ ] Tests pass: `python -m pytest tests/ --tb=short -q`

**Dependencies:** None (independent of settings)

**Files likely touched:**
- `helpers/workflow_state.py` or new helper
- `_10_skill_enforcer.py` or `_67_reattach_workflow_state.py`
- New test file or existing test file

**Estimated scope:** Medium (3-4 files)

---

#### Task 8: Create eval runner connecting fixtures to enforcement settings

**Description:** Create an eval runner that loads the existing `skill-activation-evals.json` fixtures and verifies behavioral difference between settings ON vs OFF.

**Acceptance criteria:**
- [ ] Eval runner script created
- [ ] Loads `tests/eval_fixtures/skill-activation-evals.json` fixtures
- [ ] For each eval: runs with setting ON → verifies correct skill matched
- [ ] For each eval: runs with setting OFF → verifies no enforcement
- [ ] Reports pass/fail per setting per eval

**Verification:**
- [ ] Runner executes: `python tests/run_enforcement_evals.py`
- [ ] Produces pass/fail report

**Dependencies:** Tasks 3-6 (settings must be enabled to test)

**Files likely touched:**
- `tests/run_enforcement_evals.py` (check if exists)
- `tests/eval_fixtures/`

**Estimated scope:** Medium (new file + fixture updates)

### Checkpoint: Bug Fix & Eval Runner
- [ ] Bug 4 fixed — shipped specs excluded from proposals
- [ ] Eval runner created and producing results
- [ ] All tests still pass
- [ ] Review before proceeding to Phase 4

---

### Phase 4: Routing Rules

#### Task 9: Update routing rules with 13 lessons learned

**Description:** Incorporate the 13 lessons from `docs/reports/agent-ship-phase-routing-bugs.md` into the plugin's routing rules (`prompts/agent.skills.routing.md`).

**Key rules to add:**
- Session start protocol: load `using-agent-skills` first, check project state
- Phase transition gates: re-verify skill assignments when transitioning
- Cross-reference following: when a skill references another skill, follow it
- Checklist enforcement: follow the FULL verification checklist

**Acceptance criteria:**
- [ ] Routing rules updated with session start protocol
- [ ] Routing rules updated with phase transition gates
- [ ] Routing rules updated with cross-reference following rule
- [ ] Routing rules updated with checklist enforcement rule
- [ ] Tests verify rules include new constraints

**Verification:**
- [ ] Tests pass: `python -m pytest tests/ --tb=short -q`
- [ ] Manual review: read routing rules, verify all 13 lessons covered

**Dependencies:** Tasks 3-8 (lessons confirmed by live verification)

**Files likely touched:**
- `prompts/agent.skills.routing.md`
- Tests

**Estimated scope:** Medium (1 file + tests)

### Checkpoint: Complete
- [ ] All 9 tasks complete
- [ ] All outcome criteria from spec met
- [ ] All implementation criteria from spec met
- [ ] Ready for SHIP phase

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Enabling settings breaks existing tests | High | Run full test suite before each enable |
| Enforcement corrections conflict with agent behavior | Medium | `enforcement_mode` stays `observe` (warnings only) |
| `skill_graph_validate_on_build` wiring has side effects | Low | `validate_graph()` is read-only — no mutation |
| Settings UI shows wrong values (framework bug) | Low | Filed separately — not blocking |
| Enabling all settings at once causes cascading failures | High | Enable ONE AT A TIME with verification between each |
| Bug 4 fix changes agent behavior unexpectedly | Medium | Add tests for both shipped and in-progress specs |
| Eval runner false positives | Medium | Test with both ON and OFF settings to prove behavioral difference |

## Open Questions

~~- Should `telemetry_debug` also be verified and wired? (Added to default_config.yaml this session but unknown if wired)~~ → **YES, added to plan**
~~- Should `telemetry_enabled` be verified? (Currently true — is it working correctly?)~~ → **YES, added to plan**
~~- Should we verify already-enabled settings (`workflow_state_enabled`, `artifact_inference_enabled`) as part of this plan?~~ → **YES, added to plan**

### Additional Tasks for Already-Enabled Settings

#### Task 10: Verify `workflow_state_enabled` (currently ON)

**Description:** This setting was enabled during the artifact-path-wiring-fix session without proper verification. Confirm it works correctly ON and doesn't break when OFF.

**Acceptance criteria:**
- [ ] Verify ON: workflow state files are created and updated correctly
- [ ] Verify OFF: no state files created, no errors
- [ ] Both ON and OFF tests exist

**Dependencies:** None
**Files likely touched:** `tests/test_workflow_state.py`
**Estimated scope:** Small (1 file, tests)

#### Task 11: Verify `artifact_inference_enabled` (currently ON)

**Description:** This setting was added and enabled during the artifact-path-wiring-fix session. Confirm it works correctly ON and doesn't break when OFF.

**Acceptance criteria:**
- [ ] Verify ON: artifact paths are inferred from file writes
- [ ] Verify OFF: no artifact inference, no errors
- [ ] Both ON and OFF tests exist

**Dependencies:** None
**Files likely touched:** `tests/test_artifact_inference.py`
**Estimated scope:** Small (1 file, tests)

#### Task 12: Verify `telemetry_enabled` (currently ON)

**Description:** This setting has been on throughout. Verify it's actually working — telemetry events are being logged.

**Acceptance criteria:**
- [ ] Verify ON: telemetry events written to `skill_activations.jsonl`
- [ ] Verify OFF: no telemetry events, no errors
- [ ] Both ON and OFF tests exist

**Dependencies:** None
**Files likely touched:** `tests/test_skill_telemetry.py`
**Estimated scope:** Small (1 file, tests)

#### Task 13: Verify `telemetry_debug` wiring (default OFF)

**Description:** Added to `default_config.yaml` during this session but unknown if any code reads it. Check if it's wired and add tests if so, or wire it if not.

**Acceptance criteria:**
- [ ] Determine if any code reads `telemetry_debug` from config
- [ ] If wired: add ON/OFF tests
- [ ] If not wired: wire it to debug-level logging in telemetry extension

**Dependencies:** None
**Files likely touched:** `extensions/python/tool_execute_after/_05_skill_telemetry.py`, `tests/test_skill_telemetry.py`
**Estimated scope:** Small (1-2 files)
