# revolve/projects/a0-agent-skills/revisions/rev-006/runs/AGENTS.md — Run Index

## Purpose

Index official rev-006 architecture, runtime, API, and thin-e2e evidence runs.

## Runs

| Run ID | Checkpoint | Suite | Score | Validity | Raw Result | Decision |
|---|---|---|---|---|---|---|
| `run-001-baseline-architecture-state` | `cp-000-rev006-baseline` | `architecture_state_inspection` | 6 architecture findings (1 critical) | valid; live-runtime-backed evidence via `/opt/venv-a0/bin/python` | `runs/run-001-baseline-architecture-state.json` | baseline collected; critical: agent_skills_enabled NOT SET; create architecture branch |

## Run Policy

- Record every official rev-006 run here after raw output is saved.
- Separate deterministic runtime/API evidence from live e2e evidence.
- Mark infrastructure-invalid runs explicitly and exclude them from architecture comparisons.

## Next Action

### Baseline Findings Summary

1. **Reclassified**: `agent_skills_enabled` not set in dev project — correct behavior; dedicated test project `a0-skills-test` created with opt-in
2. Plugin discovery, skills catalog, and profiles all verified working
3. Source parity gap: `web-performance-auditor` persona and `webperf` command missing
4. Plugin has 0 API endpoints
5. 217 child AGENTS.md files confirm no recursive framework injection
6. Correct A0 runtime APIs mapped for future deterministic tests

## Next Action

| `run-002-cp-a001-runtime-architecture` | `cp-a001-architecture-fixes` | `runtime_architecture_v1` | 22/22 passed | valid | `runs/run-002-cp-a001-runtime-architecture.json` | all architecture gates passed |
| `run-003-cp-a001-structural` | `cp-a001-architecture-fixes` | structural_non_e2e | 145 passed, 10 skipped | valid | `runs/run-003-cp-a001-structural.json` | no regressions |
| `run-004-cp-a001-existing-runtime` | `cp-a001-architecture-fixes` | existing_runtime_integration | 12/12 passed | valid | `runs/run-004-cp-a001-existing-runtime.json` | no runtime regressions |

## Next Action

| `run-005-cp-b001-deeper-architecture` | `cp-b001-deeper-architecture` | `runtime_architecture_v2` | 37/37 passed | valid | `runs/run-005-cp-b001-deeper-architecture.json` | all deeper architecture gates passed |

## Next Action

| `run-006-cp-c001-http-api` | `cp-c001-api-harness` | `http_api_v1` | 4/4 passed | valid | `runs/run-006-cp-c001-http-api.json` | all HTTP API gates passed |

## Next Action

branch-c API tests complete (4/4). branch-d live workflow proof complete: tasks/spec.md created successfully.
