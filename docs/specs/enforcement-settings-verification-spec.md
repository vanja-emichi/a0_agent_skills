# Spec: Enforcement Settings Verification and Enablement

**Status:** Shipped
**Parent:** `docs/specs/a0-agent-skills-workflow-governance-spec.md`
**Related ADRs:** ADR-001 (Skill Enforcement Gate), ADR-003 (Phase-Aware Governance), ADR-004 (Skill Contracts)

## Objective

Verify that ALL enforcement and workflow settings in `config.json` / `default_config.yaml` are fully wired and functional, then ensure they are all correctly enabled with live verification. The enforcement mechanisms were built in previous sprints but some are currently disabled, which allowed 7 routing bugs to occur during the artifact-path-wiring-fix session.

## Problem Statement

The 7 reported routing bugs (documented in `docs/reports/agent-ship-phase-routing-bugs.md`) could have been prevented by existing enforcement mechanisms that are currently disabled. Additionally, some settings were enabled during this session (`workflow_state_enabled`, `artifact_inference_enabled`) without proper verification.

### Complete Settings Audit

| Setting | Current | Wired | Status |
|---------|---------|-------|--------|
| `workflow_state_enabled` | `"true"` ← **enabled this session** | ✅ | Needs verification |
| `artifact_inference_enabled` | `"true"` ← **enabled this session** | ✅ | Needs verification |
| `telemetry_enabled` | `true` | ✅ | Working? Needs verification |
| `phase_governance_enabled` | `"false"` | ✅ | Disabled — prevents Bugs 1, 2 |
| `skill_contracts_enabled` | `"false"` | ✅ | Disabled — prevents Bugs 3, 7 |
| `skill_next_skill_hints` | `"false"` | ✅ (OFF only) | Disabled — prevents Bugs 5, 6 |
| `skill_graph_validate_on_build` | `"false"` | ❌ **DEAD** | No code reads this setting |
| `enforcement_mode` | `"observe"` | ✅ | Working — corrections are warnings |
| `telemetry_debug` | `false` (default) | ⚠️ Unknown | Added to default_config.yaml this session |

## Scope

### In Scope

1. **Audit existing test coverage** for each setting (ON and OFF paths)
2. **Wire dead setting** (`skill_graph_validate_on_build`) — connect to existing `validate_graph()` in `skill_contracts.py`
3. **Fill test gaps** — add missing ON-path tests for `skill_next_skill_hints`
4. **Enable settings one at a time** with live verification after each
5. **Fix Bug 4** — check spec status fields before proposing next work, prevent re-proposing shipped specs
6. **Create eval runner** — connect existing skill-activation eval fixtures to enforcement settings for live behavioral verification
7. **Update routing rules** — incorporate the 13 lessons learned from the 7 routing bugs into the plugin's mandatory routing rules

### Out of Scope

- New enforcement mechanisms (the existing ones are sufficient)
- Behavioral evals beyond skill-activation (future work)
- Framework-level changes (settings UI display bug is filed separately)

## Current Test Coverage

### Existing Tests (3,921 lines across 5 files)

| Test File | Lines | Settings Covered | Status |
|-----------|-------|-----------------|--------|
| `test_skill_enforcer.py` | 1,721 | `phase_governance_enabled`, `skill_contracts_enabled` (ON + OFF) | ✅ 143 pass |
| `test_phase_governance.py` | 673 | Phase transitions, skill-per-phase | ✅ Pass |
| `test_enforcement_guardrails.py` | 900 | Correction mechanism, no-mutation | ✅ Pass |
| `test_enforcement_config.py` | 105 | Config surface, defaults | ✅ Pass |
| `test_workflow_rehydrate.py` | — | `skill_next_skill_hints: false` | ⚠️ OFF only |

### Coverage Gaps

| Setting | ON Path | OFF Path | Dead | Evals |
|---------|---------|----------|------|-------|
| `phase_governance_enabled` | ✅ | ✅ | No | ❌ |
| `skill_contracts_enabled` | ✅ | ✅ | No | ❌ |
| `skill_next_skill_hints` | ❌ | ✅ | No | ❌ |
| `skill_graph_validate_on_build` | ❌ | ❌ | **YES** | ❌ |

### Existing Eval Fixtures

`tests/eval_fixtures/skill-activation-evals.json` — 12+ evals mapping intents to expected skills and phases. Not yet connected to enforcement settings.

## Implementation Plan

### Task 1: Wire `skill_graph_validate_on_build`

**Problem:** Setting exists in config but no code reads it. `validate_graph()` exists in `skill_contracts.py` (line 483) but is never called.

**Fix:**
- In `_10_skill_enforcer.py`, read `skill_graph_validate_on_build` from config
- Call `validate_graph()` from `skill_contracts.py` when setting is true
- Add ON/OFF tests

**Files:** `_10_skill_enforcer.py`, `tests/test_skill_enforcer.py`

### Task 2: Add ON-path test for `skill_next_skill_hints`

**Problem:** Only OFF path tested (rehydration omits hints when false). No test for ON behavior.

**Fix:**
- Add test: rehydration includes skill hints when `skill_next_skill_hints: true`
- Add test: hints are populated from `get_skills_for_phase()` for current phase

**Files:** `tests/test_workflow_rehydrate.py`

### Task 3: Enable `phase_governance_enabled` and verify

**Steps:**
1. Change config.json: `"phase_governance_enabled": "true"`
2. Run full test suite
3. Run live eval: create spec → plan → todo → verify phase transitions enforced
4. Verify Bugs 1, 2 would be prevented

### Task 4: Enable `skill_contracts_enabled` and verify

**Steps:**
1. Change config.json: `"skill_contracts_enabled": "true"`
2. Run full test suite
3. Run live eval: load a skill → verify cross-references surfaced
4. Verify Bugs 3, 7 would be prevented

### Task 5: Enable `skill_next_skill_hints` and verify

**Steps:**
1. Change config.json: `"skill_next_skill_hints": "true"`
2. Run full test suite
3. Run live eval: verify rehydrated state includes skill recommendations
4. Verify Bugs 5, 6 would be prevented

### Task 6: Enable `skill_graph_validate_on_build` and verify

**Steps:**
1. Change config.json: `"skill_graph_validate_on_build": "true"`
2. Run full test suite
3. Run live eval: verify skill graph validation runs on build

### Task 7: Fix Bug 4 — Check spec status before proposing work

**Problem:** Agent proposed already-shipped specs as new work because it only checked file existence, not spec status fields.

**Fix:**
- In `_10_skill_enforcer.py` or rehydration, add a function that reads spec status fields
- Before proposing next steps, filter out specs with status `SHIPPED`
- Add tests: verify shipped specs are excluded from proposals

**Files:** `helpers/workflow_state.py` or new helper, `_10_skill_enforcer.py`, tests

### Task 8: Create eval runner connecting fixtures to enforcement settings

**Problem:** Existing eval fixtures (`tests/eval_fixtures/skill-activation-evals.json`) have 12+ test cases mapping intents to expected skills and phases, but no runner connects them to enforcement settings.

**Fix:**
- Create eval runner script that loads fixtures, configures settings ON/OFF, and verifies behavioral change
- For each eval: run with setting ON → verify correct skill matched; run with setting OFF → verify no enforcement
- Report pass/fail per setting per eval

**Files:** `tests/run_enforcement_evals.py` (may already exist — check `tests/run_enforcement_evals.py`), `tests/eval_fixtures/`

### Task 9: Update routing rules with 13 lessons learned

**Problem:** The 13 lessons learned from the 7 routing bugs are documented in `docs/reports/agent-ship-phase-routing-bugs.md` but not incorporated into the plugin's mandatory routing rules.

**Fix:**
- Update the routing rules in `prompts/agent.skills.routing.md` to include:
  - Session start protocol: load `using-agent-skills` first, check project state
  - Phase transition gates: re-verify skill assignments when transitioning
  - Cross-reference following rule: when a skill references another skill, follow it
  - Checklist enforcement: follow the FULL verification checklist, not just the obvious deliverable
- Add tests: verify routing rules include the new constraints

**Files:** `prompts/agent.skills.routing.md`, tests

## Success Criteria

### Outcome Criteria (how we know it worked)

**Tool-Call-Level Enforcement (what the enforcement gate does):**
- [x] Enforcement settings are wired and active — config reads happen on every tool call
- [x] Enforcement observe mode logs gate decisions to telemetry (660 decisions logged)
- [ ] Enforcement detect violations when skills should have been loaded for tool calls (needs live eval with tool-call-level violations)

**Behavioral-Level Compliance (handled by routing rules + promptinclude, not enforcement):**
- [x] Routing rules updated with anti-rationalization rows, phase transition reminder
- [x] Promptinclude guidelines created for session start, delegation, and skill execution
- [x] Spec status checking prevents re-proposing shipped work (Bug 4)
- [x] Skill hints injection provides next-skill recommendations

**Test Coverage:**
- [x] Each enforcement feature has ON + OFF test coverage
- [x] All existing tests pass regardless of settings state (837 tests)
- [x] Eval runner created and produces ON vs OFF comparison reports

### Implementation Criteria (what was done)

- [x] `skill_graph_validate_on_build` is wired to code (no longer dead)
- [x] `skill_next_skill_hints` has ON-path tests
- [x] Eval runner created connecting existing fixtures to enforcement settings
- [x] Bug 4 fix implemented — spec status checked before proposing next work
- [x] Routing rules updated with anti-rationalization rows and phase transition reminder
- [x] Behavioral guidelines moved to promptinclude (not routing rules)
- [x] All 8 enforcement settings verified with ON/OFF test coverage
- [x] Review fixes applied (validate_graph once-per-session, spec scan caching)
- [x] Follow-up fixes applied (eval runner pattern drift guard, graph validation simulation, config formatting)

### Known Limitations

1. **Enforcement is advisory-only** (ADR-006): the gate can nudge and warn but cannot block tool calls. This is a framework-level constraint (`tool_execute_before` return value is ignored).
2. **Enforcement is tool-call-level only**: it detects when a skill should have been loaded for a specific tool call. It does NOT detect behavioral violations (phase skipping, missing skill loads, ignored cross-references, partial checklist execution). These are handled by routing rules and promptinclude guidelines.
3. **Trigger-side classifier accuracy is 40.6%** (ADR-006): the utility-model classifier sometimes rejects valid skill matches. Suppress-side accuracy is 100%.
4. **Bug 8 (skipped VERIFY phase) occurred with all enforcement settings enabled**: this confirms that behavioral violations are not caught by the current enforcement mechanism.

## Risks

| Risk | Mitigation |
|------|------------|
| Enabling settings breaks existing tests | Test suite is comprehensive (3,921 lines) — run before each enable |
| Enforcement corrections conflict with agent behavior | Settings default to `observe` mode (corrections are warnings, not blocks) |
| `skill_graph_validate_on_build` wiring has side effects | `validate_graph()` is read-only — no state mutation |
| Settings UI shows wrong values (existing framework bug) | Filed as `framework-settings-ui-bug.md` — not blocking |
