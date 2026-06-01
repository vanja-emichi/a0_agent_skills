# Implementation Plan: Skill Activation Evals + Functional Dependencies

## Overview

Two independent features to add to the a0_agent_skills plugin:
- **Feature D:** Skill Activation Evals — test harness measuring intent→skill mapping accuracy
- **Feature F:** Functional Skill Dependencies — auto-loading prerequisite skills from DAG

These features are independent and can be developed in parallel. Both must pass the existing 658 tests with no regressions.

## Architecture Decisions

- Feature D adds new test files only — no changes to helpers or extensions
- Feature F modifies `skill_contracts.py` (new function) and `_10_persist_workflow_state.py` (integration)
- Both features use the existing bootstrap patterns and follow fail-safe conventions

## Task List

### Phase 1: Feature D — Skill Activation Evals

#### Task 1: Create eval fixture data
**Description:** Create the JSON fixture file with 30 eval cases covering all 23 skills.

**Acceptance criteria:**
- [ ] `tests/eval_fixtures/skill-activation-evals.json` exists
- [ ] Contains ≥30 test cases
- [ ] All 23 skills have ≥1 positive case
- [ ] ≥7 near-miss cases with `confused_with` field
- [ ] Valid JSON (parseable)

**Verification:**
- [ ] `python -c "import json; d=json.load(open('tests/eval_fixtures/skill-activation-evals.json')); print(len(d), 'cases')"`

**Dependencies:** None

**Files likely touched:**
- `tests/eval_fixtures/skill-activation-evals.json` (NEW)

**Estimated scope:** Small (1 file)

---

#### Task 2: Create eval test runner
**Description:** Implement the pytest test runner with 3 test classes (prefilter accuracy, near-miss discrimination, coverage report).

**Acceptance criteria:**
- [ ] `tests/test_skill_activation_evals.py` exists
- [ ] `TestPrefilterAccuracy` class with parametrized tests
- [ ] `TestNearMissDiscrimination` class with parametrized tests
- [ ] `TestCoverageReport` class with meta-tests
- [ ] Correctly bootstraps `skill_match` module using existing conftest patterns
- [ ] All test cases load from fixture file

**Verification:**
- [ ] `python -m pytest tests/test_skill_activation_evals.py --collect-only` shows all test cases
- [ ] `TestCoverageReport` tests pass (these are structural, not accuracy-dependent)

**Dependencies:** Task 1

**Files likely touched:**
- `tests/test_skill_activation_evals.py` (NEW)

**Estimated scope:** Medium (1 new file, ~150 lines)

---

#### Task 3: Run evals and establish baseline
**Description:** Run the eval suite, collect results, and document the baseline pass rate.

**Acceptance criteria:**
- [ ] Eval suite runs without errors
- [ ] Baseline results documented (pass/fail per case)
- [ ] Per-skill accuracy reported
- [ ] Near-miss discrimination rate reported

**Verification:**
- [ ] `python -m pytest tests/test_skill_activation_evals.py -v` completes
- [ ] Results saved to a summary in the spec file or a separate report

**Dependencies:** Task 2

**Files likely touched:**
- `docs/specs/skill-activation-evals-spec.md` (update with baseline results)

**Estimated scope:** Small (documentation)

---

### Checkpoint: Feature D Complete
- [ ] All 23 skills have eval cases
- [ ] Eval suite runs in CI alongside existing 658 tests
- [ ] Baseline accuracy documented

---

### Phase 2: Feature F — Functional Skill Dependencies

#### Task 4: Implement `resolve_dependencies()` in `skill_contracts.py`
**Description:** Add the core dependency resolution function with topological sort and cycle detection.

**Acceptance criteria:**
- [ ] `resolve_dependencies(skill_name, already_loaded, graph)` function exists
- [ ] Returns ordered list of prerequisite skill names
- [ ] Already-loaded skills are skipped
- [ ] Cycles are detected and broken safely (log warning, skip cycle members)
- [ ] Unknown skills return empty list (fail-safe)
- [ ] Skills with no `depends_on` return empty list

**Verification:**
- [ ] `python -m pytest tests/test_skill_dependencies.py -v -k "resolve"` passes
- [ ] Existing 658 tests still pass

**Dependencies:** None

**Files likely touched:**
- `helpers/skill_contracts.py` (ADD function)

**Estimated scope:** Small (add ~50 lines to existing file)

---

#### Task 5: Create dependency resolution tests
**Description:** Write the test suite covering linear chains, diamonds, cycles, empty deps, and already-loaded skip logic.

**Acceptance criteria:**
- [ ] `tests/test_skill_dependencies.py` exists
- [ ] Tests: linear chain (A→B→C)
- [ ] Tests: diamond dependency (D→B,C→A)
- [ ] Tests: already-loaded skip
- [ ] Tests: no dependencies (empty result)
- [ ] Tests: cycle protection
- [ ] Tests: deep chain (4+ levels)
- [ ] Tests: idempotency

**Verification:**
- [ ] `python -m pytest tests/test_skill_dependencies.py -v` passes
- [ ] All 6+ test cases pass

**Dependencies:** Task 4

**Files likely touched:**
- `tests/test_skill_dependencies.py` (NEW)

**Estimated scope:** Medium (1 new file, ~200 lines)

---

#### Task 6: Integrate dependency resolution into `_10_persist_workflow_state.py`
**Description:** Hook dependency resolution into the existing state persistence extension so it triggers after `skills_tool:load` calls.

**Acceptance criteria:**
- [ ] After `skills_tool:load`, extension checks for dependencies
- [ ] Missing prerequisites are logged
- [ ] Dependency chain is returned in tool result metadata
- [ ] Already-loaded skills are not re-loaded
- [ ] Telemetry logs `dependency_resolution` events when enabled

**Verification:**
- [ ] `python -m pytest tests/test_workflow_state.py -v` passes (no regressions)
- [ ] `python -m pytest tests/test_persist_workflow_state.py -v` passes
- [ ] Integration test: load a skill with deps → verify deps resolved

**Dependencies:** Task 5

**Files likely touched:**
- `extensions/python/tool_execute_after/_10_persist_workflow_state.py` (MODIFY)
- `extensions/python/tool_execute_after/_05_skill_telemetry.py` (MODIFY for dep event)

**Estimated scope:** Medium (modify 2 existing files)

---

#### Task 7: Populate `depends_on` in skill SKILL.md frontmatter
**Description:** Add `depends_on` declarations to the 8 skills identified in the spec.

**Acceptance criteria:**
- [ ] 8 skills have `depends_on` in their YAML frontmatter
- [ ] DAG validates without cycles
- [ ] `resolve_dependencies()` returns correct chains for each

**Verification:**
- [ ] `python -m pytest tests/test_skill_contracts.py -v` passes
- [ ] `python -m pytest tests/test_skill_graph.py -v` passes
- [ ] Cycle detection confirms no cycles

**Dependencies:** Task 4

**Files likely touched:**
- `skills/planning-and-task-breakdown/SKILL.md`
- `skills/incremental-implementation/SKILL.md`
- `skills/test-driven-development/SKILL.md`
- `skills/code-review-and-quality/SKILL.md`
- `skills/shipping-and-launch/SKILL.md`
- `skills/code-simplification/SKILL.md`
- `skills/security-and-hardening/SKILL.md`
- `skills/performance-optimization/SKILL.md`

**Estimated scope:** Medium (8 files, 1 line each)

---

### Checkpoint: Feature F Complete
- [ ] `resolve_dependencies()` works correctly
- [ ] Dependency resolution integrated into state persistence
- [ ] Telemetry logs dependency events
- [ ] 8 skills declare dependencies
- [ ] All 658 existing tests pass + new tests pass

---

### Phase 3: Verification & Documentation

#### Task 8: Full regression test + documentation update
**Description:** Run the complete test suite, update AGENTS.md files, and update the specs.

**Acceptance criteria:**
- [ ] `python -m pytest tests/ -v --tb=short` passes (658 existing + new tests)
- [ ] `skills/AGENTS.md` updated to reflect `depends_on` is now functional
- [ ] `helpers/AGENTS.md` updated with `resolve_dependencies` entry point
- [ ] Both spec files updated with ✅ completion markers

**Verification:**
- [ ] Full test suite green
- [ ] AGENTS.md files accurate

**Dependencies:** Tasks 3, 6, 7

**Files likely touched:**
- `skills/AGENTS.md`
- `helpers/AGENTS.md`
- `docs/specs/skill-activation-evals-spec.md`
- `docs/specs/functional-skill-dependencies-spec.md`

**Estimated scope:** Small (documentation)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| skill_match.search_skills() API doesn't match spec assumptions | Medium | Verify API by reading `helpers/skill_match.py` before implementing Task 2 |
| Dependency resolution breaks existing skill_contracts DAG validation | High | Task 5 includes cycle and regression tests |
| Extension integration can't call skills_tool directly | Medium | Design Task 6 to inject observations, not direct tool calls |
| Eval suite reveals skill_match accuracy < 90% | Low | Document baseline; improve trigger_patterns in follow-up work |

## Parallelization

Tasks 1-3 (Feature D) and Tasks 4-7 (Feature F) are fully independent and can be developed in parallel.
Task 8 requires both features to be complete.

```
Track A (Feature D):     Track B (Feature F):
  Task 1 → Task 2 → Task 3   Task 4 → Task 5 → Task 6
                                      Task 7 (parallel with 5-6)
                    └──→ Task 8 (merge) ←──┘
```

## Open Questions

- Should we implement Task 6 as observation injection or direct tool call? (Spec proposes observations)
- What's the acceptable eval baseline accuracy? (Spec proposes ≥90% prefilter, ≥80% near-miss)
