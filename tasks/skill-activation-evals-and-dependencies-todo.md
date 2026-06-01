# Todo: Skill Activation Evals + Functional Skill Dependencies

**Created:** 2026-05-31
**Specs:**
- `docs/specs/skill-activation-evals-spec.md`
- `docs/specs/functional-skill-dependencies-spec.md`
**Plan:** `docs/plans/skill-activation-evals-and-dependencies-plan.md`

---

## Feature D: Skill Activation Evals

- [ ] Task 1: Create eval fixture data
  - Acceptance: `tests/eval_fixtures/skill-activation-evals.json` exists with ≥30 cases covering all 23 skills + ≥7 near-miss cases
  - Verify: `python -c "import json; d=json.load(open('tests/eval_fixtures/skill-activation-evals.json')); print(len(d), 'cases')"`
  - Files: `tests/eval_fixtures/skill-activation-evals.json` (NEW)

- [ ] Task 2: Create eval test runner
  - Acceptance: `tests/test_skill_activation_evals.py` exists with TestPrefilterAccuracy, TestNearMissDiscrimination, TestCoverageReport classes; bootstraps skill_match correctly
  - Verify: `python -m pytest tests/test_skill_activation_evals.py --collect-only` shows all test cases
  - Files: `tests/test_skill_activation_evals.py` (NEW)

- [ ] Task 3: Run evals and establish baseline
  - Acceptance: Eval suite runs without errors; baseline pass rate documented per skill
  - Verify: `python -m pytest tests/test_skill_activation_evals.py -v` completes
  - Files: `docs/specs/skill-activation-evals-spec.md` (update with baseline)

---

## Feature F: Functional Skill Dependencies

- [ ] Task 4: Implement `resolve_dependencies()` in `skill_contracts.py`
  - Acceptance: Function returns ordered prerequisite list; skips already-loaded; detects cycles; returns empty for unknown/no-dep skills
  - Verify: `python -m pytest tests/test_skill_dependencies.py -v -k "resolve"` passes; existing 658 tests still pass
  - Files: `helpers/skill_contracts.py` (ADD ~50 lines)

- [ ] Task 5: Create dependency resolution tests
  - Acceptance: `tests/test_skill_dependencies.py` covers linear chains, diamonds, cycles, empty deps, already-loaded skip, deep chains, idempotency
  - Verify: `python -m pytest tests/test_skill_dependencies.py -v` passes
  - Files: `tests/test_skill_dependencies.py` (NEW ~200 lines)

- [ ] Task 6: Integrate dependency resolution into `_10_persist_workflow_state.py`
  - Acceptance: Extension resolves deps after skills_tool:load; logs to telemetry; returns chain in metadata
  - Verify: `python -m pytest tests/test_workflow_state.py tests/test_persist_workflow_state.py -v` passes
  - Files: `extensions/python/tool_execute_after/_10_persist_workflow_state.py` (MODIFY), `_05_skill_telemetry.py` (MODIFY)

- [ ] Task 7: Populate `depends_on` in 8 skill SKILL.md frontmatter
  - Acceptance: 8 skills declare depends_on; DAG validates without cycles
  - Verify: `python -m pytest tests/test_skill_contracts.py tests/test_skill_graph.py -v` passes
  - Files: 8 SKILL.md files (1 line each in frontmatter)

---

## Phase 3: Verification & Documentation

- [ ] Task 8: Full regression test + documentation update
  - Acceptance: Full test suite green (658 existing + new); AGENTS.md files updated; specs marked complete
  - Verify: `python -m pytest tests/ -v --tb=short` passes
  - Files: `skills/AGENTS.md`, `helpers/AGENTS.md`, both spec files

---

## Checkpoints

### Checkpoint: Feature D Complete
- [ ] All 23 skills have eval cases
- [ ] Eval suite runs in CI alongside existing 658 tests
- [ ] Baseline accuracy documented

### Checkpoint: Feature F Complete
- [ ] `resolve_dependencies()` works correctly
- [ ] Dependency resolution integrated into state persistence
- [ ] Telemetry logs dependency events
- [ ] 8 skills declare dependencies
- [ ] All 658 existing tests pass + new tests pass
