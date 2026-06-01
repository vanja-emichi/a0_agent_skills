# Implementation Plan: Approval Gate Wiring and Governance Hardening

**Spec:** `docs/specs/approval-gate-wiring-spec.md`
**Status:** Shipped

## Overview

Wire the existing approval infrastructure (`mark_artifact_approved`, `is_artifact_approved`) to a natural language trigger, then incrementally harden the governance system with test gates at every step. Each step is small, independently testable, and reversible. The 5 code bugs from the deep analysis are already fixed; this plan covers the remaining wiring and hardening work.

## Architecture Decisions

- **Incremental, gated rollout** — each step has a clear test gate before moving to the next
- **Observe mode until proven** — `enforcement_mode` stays `observe` until Steps 1-5 pass with shadow sample data
- **Reuse existing infrastructure** — `mark_artifact_approved`, `is_artifact_approved`, rehydration display, progress events all already work; we just add the trigger
- **Natural language only** — no slash commands, no auto-approval, no expiry (per interview-me spec)
- **Fail-safe everywhere** — all new functions return safe defaults on exception
- **Word-boundary matching** — avoid false positives like "unapproved" or "disapproved"

## Task List

### Phase 1: Wire the Approval Trigger (Steps 1-3)

#### Task 1: Add Natural Language Approval Detection

**Description:** Create a new extension `_20_approval_gate.py` in `tool_execute_before` that detects approval language in user messages and calls `mark_artifact_approved` for the current phase's artifact.

**Acceptance criteria:**
- [ ] New file: `extensions/python/tool_execute_before/_20_approval_gate.py`
- [ ] `detect_approval_in_text(text) -> bool` function with word-boundary matching
- [ ] Detects: "approved", "approve", "looks good", "good to go", "proceed", "ship it", "lgtm", "let's go"
- [ ] Does NOT detect: "unapproved", "fix section 3", "approved by whom?", silence
- [ ] When approval detected + current phase artifact exists → calls `mark_artifact_approved`
- [ ] Bootstrap pattern matches other extensions (`_plugin_loader` injection)
- [ ] Fail-safe: all exceptions return without blocking tool execution

**Verification:**
- [ ] `python -m pytest tests/test_approval_trigger.py -v --tb=short` → all pass
- [ ] `python -m pytest tests/ -v --tb=short` → full suite still green (839+ pass)
- [ ] Live: in a session, say "approved" after writing a spec → rehydration shows `(approved)` tag

**Dependencies:** None

**Files likely touched:**
- `extensions/python/tool_execute_before/_20_approval_gate.py` (new)
- `tests/test_approval_trigger.py` (new)

**Estimated scope:** S (1-2 files)

#### Task 2: Add Phase Gate Check (Approval Before Transition)

**Description:** Extend `phase_governance.transition_phase` to check if the current phase's artifact is approved before allowing transition. In observe mode, log warning. In enforce mode, block.

**Acceptance criteria:**
- [ ] `phase_governance.transition_phase` calls `is_artifact_approved` before transitioning
- [ ] If unapproved in observe mode: log warning, allow transition (backward compatible)
- [ ] If unapproved in enforce mode: log warning, block transition (return False)
- [ ] If approved: transition proceeds normally
- [ ] Each phase's required artifact type is documented: DEFINE→spec, PLAN→plan, BUILD→todo, REVIEW→review, SHIP→checklist

**Verification:**
- [ ] `python -m pytest tests/test_approval_phase_gate.py -v --tb=short` → all pass
- [ ] `python -m pytest tests/ -v --tb=short` → full suite still green
- [ ] Live: try to advance DEFINE→PLAN without approved spec → warning logged

**Dependencies:** Task 1

**Files likely touched:**
- `helpers/phase_governance.py` (extend)
- `tests/test_approval_phase_gate.py` (new)

**Estimated scope:** S (1-2 files)

#### Task 3: Add Mtime Invalidation

**Description:** Extend `mark_artifact_approved` to also store the artifact's mtime at approval time. Add a check that invalidates approval if the artifact's mtime has changed since approval.

**Acceptance criteria:**
- [ ] `mark_artifact_approved` stores `approved_mtime[artifact_type] = os.path.getmtime(artifact_path)`
- [ ] `is_artifact_approved` checks current mtime against stored mtime; returns False if changed
- [ ] Graceful handling: if artifact file is missing, approval is invalid
- [ ] Existing approval tests still pass (extended with mtime scenarios)

**Verification:**
- [ ] `python -m pytest tests/test_approval_mtime.py -v --tb=short` → all pass
- [ ] `python -m pytest tests/ -v --tb=short` → full suite still green
- [ ] Live: approve spec → modify spec → phase gate now blocks

**Dependencies:** Task 1

**Files likely touched:**
- `helpers/workflow_state.py` (extend)
- `tests/test_approval_mtime.py` (new)
- `tests/test_workflow_state.py` (extend)

**Estimated scope:** S (2-3 files)

### Checkpoint: Phase 1 Complete

- [ ] All 3 tasks complete
- [ ] Full test suite green (839+ pass)
- [ ] Approval trigger works in a live session
- [ ] Phase gate warns when unapproved
- [ ] Mtime invalidation works
- [ ] Review with user before proceeding to Phase 2

---

### Phase 2: Enable Data Collection (Step 4)

#### Task 4: Enable Shadow Sampling

**Description:** Set `enforcement_shadow_sample_rate` to 0.1 (10%) so the classifier runs on 10% of tool calls in observe mode. This collects accuracy data without changing behavior.

**Acceptance criteria:**
- [ ] `config.json` has `enforcement_shadow_sample_rate: 0.1`
- [ ] `default_config.yaml` has `enforcement_shadow_sample_rate: 0.1`
- [ ] Telemetry shows classifier decisions for sampled calls
- [ ] No behavioral change (still observe mode, no corrections injected)

**Verification:**
- [ ] `python tests/run_enforcement_evals.py` → runs without errors
- [ ] Telemetry JSONL shows classifier calls
- [ ] No regressions in 839+ tests

**Dependencies:** None (can be done in parallel with Phase 1)

**Files likely touched:**
- `config.json`
- `default_config.yaml`

**Estimated scope:** XS (config change)

### Checkpoint: Phase 2 Complete

- [ ] Shadow sampling enabled
- [ ] Telemetry shows classifier activity
- [ ] Review with user before Phase 3

---

### Phase 3: Improve Classifier Accuracy (Step 5)

#### Task 5: Tune Classifier to ≥80% Accuracy

**Description:** Analyze shadow sample data and existing eval fixtures. If accuracy is below 80%, tune the classifier prompt in `skill_match.py`.

**Acceptance criteria:**
- [ ] Run `python tests/run_enforcement_evals.py` → document current accuracy
- [ ] If < 80%: identify failure patterns, update classifier prompt, retest
- [ ] If ≥ 80%: skip tuning, document baseline
- [ ] Document changes in `docs/reports/classifier-tuning.md`

**Verification:**
- [ ] Eval suite accuracy ≥ 80%
- [ ] Documented in report with before/after metrics
- [ ] No regressions in test suite

**Dependencies:** Task 4 (needs shadow sample data)

**Files likely touched:**
- `helpers/skill_match.py` (tune prompt)
- `docs/reports/classifier-tuning.md` (new)

**Estimated scope:** M (3-5 files, depends on tuning iterations)

### Checkpoint: Phase 3 Complete

- [ ] Classifier accuracy ≥ 80%
- [ ] Tuning documented
- [ ] Review with user before Phase 4

---

### Phase 4: Enable Enforce Mode (Step 6)

#### Task 6: Switch to Enforce Mode

**Description:** Set `enforcement_mode` to `"enforce"` in `config.json`. This enables corrections for skill skips.

**Acceptance criteria:**
- [ ] `config.json` has `enforcement_mode: "enforce"`
- [ ] `default_config.yaml` has comment explaining when to use observe vs enforce
- [ ] Telemetry shows `state: should_correct` entries being injected
- [ ] No false positives on legitimate skill-loaded calls

**Verification:**
- [ ] `python -m pytest tests/ -v --tb=short` → full suite still green
- [ ] `python tests/run_enforcement_evals.py` → still passes
- [ ] Live: in a session, the agent receives corrections for skill skips
- [ ] No regression in normal skill usage (no false positive corrections)

**Dependencies:** Tasks 1-5 complete

**Files likely touched:**
- `config.json`
- `default_config.yaml` (comment)

**Estimated scope:** XS (config change + verification)

### Checkpoint: Phase 4 Complete

- [ ] Enforce mode enabled
- [ ] Corrections being injected in live session
- [ ] No false positives
- [ ] Review with user before Phase 5

---

### Phase 5: Strengthen Routing Rules (Step 7)

#### Task 7: Add 4 Mandatory Gates to Routing Rules

**Description:** Update `prompts/agent.skills.routing.md` to include the 4 mandatory approval gates (G1: DEFINE→PLAN, G2: PLAN→BUILD, G3: BUILD→REVIEW→SHIP, G4: REVIEW→SHIP) based on the checkpoint analysis report.

**Acceptance criteria:**
- [ ] Routing rules section for each of the 4 gates
- [ ] Trigger phrases for each gate (e.g., "spec approved", "plan approved")
- [ ] Source skills cited (from `docs/reports/skill-checkpoint-gate-analysis.md`)
- [ ] Anti-rationalization rows for skipping approval

**Verification:**
- [ ] `python -m pytest tests/test_routing_rules_refactor.py -v --tb=short` → all pass
- [ ] `python -m pytest tests/ -v --tb=short` → full suite still green
- [ ] Routing rules include all 4 gates

**Dependencies:** None (can be done in parallel with Phase 4)

**Files likely touched:**
- `prompts/agent.skills.routing.md`
- `tests/test_routing_rules_refactor.py` (if needed)

**Estimated scope:** S (1-2 files)

### Checkpoint: Phase 5 Complete

- [ ] Routing rules include 4 gates
- [ ] Existing routing tests pass
- [ ] No regression in routing behavior

---

### Phase 6: Full Acceptance Test (Step 8)

#### Task 8: End-to-End Session Test

**Description:** Run a complete spec → plan → build cycle and verify all 4 gates trigger correctly. This is the final acceptance test.

**Acceptance criteria:**
- [ ] Full E2E session works: spec → approval → plan → approval → build → review → ship
- [ ] All 4 gates trigger at the correct moments
- [ ] No false approvals detected
- [ ] Rehydration shows correct approval state at each phase
- [ ] Telemetry logs all approval events

**Verification:**
- [ ] Documented test run with screenshots/logs in `docs/reports/approval-gate-e2e-test.md`
- [ ] All success criteria from spec met
- [ ] Spec status updated to "Shipped"

**Dependencies:** Tasks 1-7 complete

**Files likely touched:**
- `docs/reports/approval-gate-e2e-test.md` (new)
- `docs/specs/approval-gate-wiring-spec.md` (status update)

**Estimated scope:** M (documentation + test execution)

### Checkpoint: All Phases Complete

- [ ] All 8 tasks complete
- [ ] 4 approval gates trigger correctly in live session
- [ ] Telemetry shows all decisions
- [ ] Zero regressions in 839+ tests
- [ ] Classifier accuracy ≥ 80%
- [ ] Enforce mode is safe
- [ ] Spec marked Shipped
- [ ] Plan marked Shipped
- [ ] Todo marked complete

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| False positive corrections in enforce mode | High | Stay in observe until eval accuracy ≥ 80%; use shadow sampling first |
| Natural language detection is too aggressive | Medium | Start with tight phrase list; word-boundary matching; iterate based on telemetry |
| Natural language detection is too narrow | Medium | Track false negatives in telemetry; iterate the phrase list based on real user patterns |
| Mtime invalidation breaks legitimate workflows | Low | Only invalidate on actual file write events, not reads |
| Phase gate causes infinite loops | Low | Agent is already designed to loop in current phase; this is expected behavior |
| Test suite grows too large | Low | Each task adds focused tests; total expected ~870+ tests |
| Classifier accuracy doesn't reach 80% | Medium | Document baseline; accept lower accuracy if improvement is marginal |
| Enforce mode causes agent confusion | Medium | Extensive live testing before declaring success |

## Parallelization Opportunities

- **Tasks 1, 2, 3** must be sequential (depend on each other)
- **Task 4** can be done in parallel with Phase 1 (config change only)
- **Task 5** requires Task 4 done first
- **Task 6** requires Tasks 1-5 done first
- **Task 7** can be done in parallel with Task 6 (different files)
- **Task 8** requires all others done first

## Open Questions

None at this time. The spec is self-contained. Any discoveries during implementation should be documented in `docs/reports/` and the spec/plan updated accordingly.

## Related Context

- Spec: `docs/specs/approval-gate-wiring-spec.md`
- Report: `docs/reports/skill-checkpoint-gate-analysis.md` (4 mandatory gates analysis)
- ADR-006: Enforcement strict mode decision (framework constraint)
- Plugin AGENTS.md: `/a0/usr/plugins/a0_agent_skills/AGENTS.md`
- Project AGENTS.md: `/a0/usr/projects/a0_agent_skills/AGENTS.md`
