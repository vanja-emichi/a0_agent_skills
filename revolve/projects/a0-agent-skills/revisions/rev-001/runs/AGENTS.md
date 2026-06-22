# revolve/projects/a0-agent-skills/revisions/rev-001/runs/AGENTS.md

## Purpose

Run index for revision rev-001. Records every official evaluation run with scores, validity, and raw result locations.

## Run Index

| Run ID | Checkpoint | Suite | Score | Validity | Raw Result | Decision |
|---|---|---|---|---|---|---|
| `run-001-baseline` | `cp-000-baseline` | structural+runtime+targeted | 161 pass / 0 fail; tool=1.0; xref=1.0 | valid | `run-001-baseline.xml`, `run-001-tool-names.json`, `run-001-cross-refs.json` | Baseline established — incumbent is strong on deterministic dimensions |
| `run-002-cp-001a` | `cp-001a` (branch-a) | structural+runtime+targeted | 161 pass / 0 fail; tool=1.0; xref=1.0 | valid | `candidate-evaluation-results.json` | Promising — correctness fixes, zero regressions |
| `run-003-cp-001b` | `cp-001b` (branch-b) | structural+runtime+targeted | 161 pass / 0 fail; tool=1.0; xref=1.0 | valid | `candidate-evaluation-results.json` | Promising — structural completeness, zero regressions |
| `run-004-cp-001c` | `cp-001c` (branch-c) | structural+runtime+targeted | 161 pass / 0 fail; tool=1.0; xref=1.0 | valid | `candidate-evaluation-results.json` | Promising — A0-native concepts, zero regressions |
| `run-005-scaled-verification` | `cp-003-scaled` | structural+runtime+targeted (24 skills) | 161 pass / 0 fail; tool=1.0; xref=1.0 | valid | live plugin verification | Promoted — full 24-skill scaling, zero regressions |
| `run-006-e2e-harness-fix` | `cp-003-scaled` | structural+runtime (post-e2e-fix) | 161 pass / 0 fail; 7 e2e structural pass | valid | live plugin | Harness fix — 12 e2e bugs repaired, dimension 6 now trustworthy |
| `run-007-e2e-coverage` | `cp-005-e2e-coverage` | structural+runtime (post-coverage) | 161 pass / 0 fail; 69 deselected (39→69: +30 new e2e); 30 e2e collected | valid | live plugin | Coverage expanded — 24/24 skills now have e2e loading tests |
| `run-008-e2e-live` | `cp-005-e2e-coverage` | e2e live server | 29 pass / 1 fail (190s) | valid | `run-008-e2e-coverage-live.log` | 24/24 skills load ✅; 4/5 discovery pass; 1 discovery fail: "plan this feature" → deprecation instead of planning |
| `run-009-planning-trigger-fix` | `cp-006-planning-trigger-fix` | e2e single test re-run | 1 pass / 0 fail (21s) | valid | live plugin | Trigger fix verified — "plan this feature" now resolves correctly |

## Run Details

### run-001-baseline

- **Date:** 2026-06-19
- **Checkpoint:** `cp-000-baseline`
- **Harness:** Fixed test suite (7 harness bugs repaired) + targeted check scripts
- **Command:** `/opt/venv-a0/bin/python -m pytest tests -v -m 'not e2e'` + `check_tool_names.py` + `check_cross_refs.py`
- **Duration:** 17.87s (pytest)

**Results:**
- Structural + Runtime tests: 161 passed, 10 skipped, 41 deselected, 0 failed
- Tool name nativity: 23/23 skills passed (score=1.0)
- Cross references: 23/23 skills passed (score=1.0)
- Eval schema: covered by test_eval_report.py (passed)
- Frontmatter: covered by test_structure.py (passed)
- Runtime loading: covered by test_runtime_skills_and_agents.py (passed)

**Infrastructure notes:**
- pytest installed in /opt/venv (was missing — Bug 7 fixed)
- 7 harness bugs fixed before baseline run
- e2e dimension (6) not yet run — requires live server

**Decision:** Baseline is valid. Incumbent is strong on all deterministic dimensions. No failures to fix in dimensions 1–5.
