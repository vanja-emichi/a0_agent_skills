# revolve/projects/a0-agent-skills/revisions/rev-002/runs/AGENTS.md

## Purpose

Run index for revision rev-002.

## Run Index

| Run ID | Checkpoint | Suite | Score | Validity | Raw Result | Decision |
|---|---|---|---|---|---|---|
| `run-001-rev002-baseline` | `cp-000-rev002-baseline` | content depth + regression | avg 5.71/8; 161 tests pass; 30 e2e pass | valid | `run-001-rev002-content-depth.json` | Baseline established — 3 systematic gaps found |
| `run-002-branch-e-project-context` | `cp-001e` | content depth scan + regression guard on checkpoint clone | avg 5.88/8; delta +4 total / +0.17 avg; regression clone run 159 pass, 10 skip, 69 deselect, 2 fail | partially valid | `runs/raw/run-002-branch-e-scan.json`, `runs/raw/run-002-branch-e-pytest.txt` | Candidate improved project-context depth; promotion blocked pending comparable regression verification |
| `run-002b-branch-e-project-context` | `cp-001e` | comparable-layout regression rerun | 160 pass, 10 skip, 69 deselect, 1 fail | invalid for comparison | `runs/raw/run-002b-branch-e-pytest.txt` | Confirms only remaining failure is a path-bound lifecycle-hook assertion in the harness |
| `run-003-branch-f-parallel-delegation` | `cp-001f` | content depth scan + regression guard on checkpoint clone | avg 6.08/8; delta +9 total / +0.37 avg; regression clone run 159 pass, 10 skip, 69 deselect, 2 fail | partially valid | `runs/raw/run-003-branch-f-scan.json`, `runs/raw/run-003-branch-f-pytest.txt` | Strongest automated candidate; promotion blocked pending comparable regression verification |
| `run-003b-branch-f-parallel-delegation` | `cp-001f` | comparable-layout regression rerun | 160 pass, 10 skip, 69 deselect, 1 fail | invalid for comparison | `runs/raw/run-003b-branch-f-pytest.txt` | Confirms only remaining failure is a path-bound lifecycle-hook assertion in the harness |

## Run Details

### run-001-rev002-baseline

- **Date:** 2026-06-20
- **Content depth:** Average 5.71/8 across 24 skills (137/192 total)
- **Regression guard:** 161 passed, 10 skipped, 0 failed
- **E2e (from rev-001 run-009):** 30/30 pass

**Systematic gaps identified:**
1. `project_context_aware` — 20/24 skills missing (biggest gap)
2. `parallel_tool_mentioned` — 14/24 skills missing
3. `call_subordinate_mentioned` — 13/24 skills missing
4. `has_files_section` — 4/24 skills missing

**Weakest skills (5/8):** api-and-interface-design, browser-testing-with-devtools, ci-cd-and-automation, code-simplification, debugging-and-error-recovery, deprecation-and-migration, idea-refine, interview-me, using-agent-skills

**Best skills (7/8):** code-review-and-quality, planning-and-task-breakdown

### run-002-branch-e-project-context

- **Checkpoint:** `cp-001e`
- **Automated content depth:** Average 5.88/8 across 24 skills (141/192 total)
- **Delta vs baseline:** +4 total, +0.17 average
- **Improved pilot skills:**
  - `api-and-interface-design`: 5 → 6 (`project_context_aware`)
  - `browser-testing-with-devtools`: 5 → 6 (`project_context_aware`)
  - `ci-cd-and-automation`: 5 → 6 (`project_context_aware`)
  - `debugging-and-error-recovery`: 5 → 6 (`project_context_aware`)
- **Manual pilot review:** Added natural project-context sections grounded in active project directory, `AGENTS.md`, `.a0proj/`, project-relative paths, and context preservation.
- **Regression clone run:** 159 passed, 10 skipped, 69 deselected, 2 failed
- **Failure class:** harness/comparability issue, not subject failure

### run-002b-branch-e-project-context

- **Purpose:** Rerun regression guard in a temp directory named `a0_agent_skills` to remove the directory-name artifact from `run-002`
- **Result:** 160 passed, 10 skipped, 69 deselected, 1 failed
- **Remaining failure:** `test_plugin_helpers_resolve_plugin_and_route_lifecycle_hooks`
- **Why invalid for comparison:** the test asserts that plugin resolution equals the live path `/a0/usr/plugins/a0_agent_skills`, so checkpoint-clone evaluation cannot satisfy it even when skill content is unchanged.
- **Decision impact:** `cp-001e` remains promising but not promotable from this evidence alone.

### run-003-branch-f-parallel-delegation

- **Checkpoint:** `cp-001f`
- **Automated content depth:** Average 6.08/8 across 24 skills (146/192 total)
- **Delta vs baseline:** +9 total, +0.37 average
- **Improved pilot skills:**
  - `api-and-interface-design`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
  - `browser-testing-with-devtools`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
  - `ci-cd-and-automation`: 5 → 6 (`call_subordinate_mentioned`)
  - `debugging-and-error-recovery`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
  - `using-agent-skills`: 5 → 7 (`parallel_tool_mentioned`, `call_subordinate_mentioned`)
- **Manual pilot review:** Added domain-specific `parallel` and `call_subordinate` guidance, including profile-targeted delegation (`code-reviewer`, `security-auditor`, `test-engineer`) and centralized main-agent coordination.
- **Regression clone run:** 159 passed, 10 skipped, 69 deselected, 2 failed
- **Failure class:** harness/comparability issue, not subject failure

### run-003b-branch-f-parallel-delegation

- **Purpose:** Rerun regression guard in a temp directory named `a0_agent_skills` to remove the directory-name artifact from `run-003`
- **Result:** 160 passed, 10 skipped, 69 deselected, 1 failed
- **Remaining failure:** `test_plugin_helpers_resolve_plugin_and_route_lifecycle_hooks`
- **Why invalid for comparison:** the test asserts that plugin resolution equals the live path `/a0/usr/plugins/a0_agent_skills`, so checkpoint-clone evaluation cannot satisfy it even when skill content is unchanged.
- **Decision impact:** `cp-001f` is the strongest automated candidate so far, but promotion remains blocked until regression evidence is gathered in a comparable harness.
