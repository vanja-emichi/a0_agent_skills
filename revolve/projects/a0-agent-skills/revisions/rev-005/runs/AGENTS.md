# revolve/projects/a0-agent-skills/revisions/rev-005/runs/AGENTS.md — Run Index

## Purpose

Index official rev-005 runtime-alignment runs and raw outputs.

## Runs

| Run ID | Checkpoint | Suite | Score | Validity | Raw Result | Decision |
|---|---|---|---|---|---|---|
| `run-001-baseline-runtime-alignment` | `cp-live-20260620-0129` | `a0_runtime_alignment_static_v1` | gate_passed=false; gate_failures=5; advisory_failures=1 | valid subject failure evidence | `runs/run-001-baseline-runtime-alignment.json` | baseline rejected; create `branch-a-harness-truth` |
| `run-002-cp-a001-runtime-alignment` | `cp-a001-harness-truth` | `a0_runtime_alignment_static_v1` | gate_passed=true; gate_failures=0; advisory_failures=0 | valid | `runs/run-002-cp-a001-runtime-alignment.json` | passed rev-005 static gates |
| `run-003-cp-a001-live-overlay-runtime-pytest` | `cp-a001-harness-truth` | runtime-integration pytest via live-overlay | 16 passed, 224 deselected; exit=0 | valid; live restored byte-for-byte | `runs/run-003-cp-a001-live-overlay-runtime-pytest.json`; log `runs/run-003-cp-a001-live-overlay-runtime-pytest.log` | runtime integration passed |
| `run-004-cp-a001-structural-pytest` | `cp-a001-harness-truth` | structural/non-runtime pytest | 145 passed, 10 skipped, 85 deselected; exit=0 | valid | `runs/run-004-cp-a001-structural-pytest.json`; log `runs/run-004-cp-a001-structural-pytest.log` | structural regression passed |
| `post-promotion-static-external-promotion-001-cp-a001` | `cp-a001-harness-truth` live | `a0_runtime_alignment_static_v1` | exit=0 | valid post-promotion verification | `promotion/external-promotion-001-cp-a001/logs/post-static-runtime-alignment.json`; log `promotion/external-promotion-001-cp-a001/logs/post-static.log` | live static verification passed |
| `post-promotion-structural-external-promotion-001-cp-a001` | `cp-a001-harness-truth` live | structural/non-runtime pytest | 145 passed, 10 skipped, 85 deselected; exit=0 | valid post-promotion verification | `promotion/external-promotion-001-cp-a001/logs/post-structural.log` | live structural verification passed |
| `post-promotion-runtime-external-promotion-001-cp-a001` | `cp-a001-harness-truth` live | runtime-integration pytest | 16 passed, 224 deselected; exit=0 | valid post-promotion verification | `promotion/external-promotion-001-cp-a001/logs/post-runtime.log` | live runtime verification passed |
| `run-005-post-promotion-full-live-e2e` | `cp-a001-harness-truth` live | full live e2e pytest | invalid; exit=4; pytest rejected `-n` | infrastructure/procedure failure, excluded from leaderboard | `runs/run-005-post-promotion-full-live-e2e.json`; log `runs/run-005-post-promotion-full-live-e2e.log` | rerun without unsupported xdist arg as `run-006` |
| `run-006-post-promotion-full-live-e2e-sequential` | `cp-a001-harness-truth` live | full live e2e sequential | invalid; superseded/aborted by user steering | procedure superseded; excluded from leaderboard | `runs/run-006-post-promotion-full-live-e2e-sequential.json`; log `runs/run-006-post-promotion-full-live-e2e-sequential.log` | controlled parallel batch run-007 completed partially |

## Baseline Failure Summary

`cp-live-20260620-0129` failed because rev-004's scanner-perfect result did not prove runtime-alignment truth:

- stale root docs claimed 23 skills while inventory had 24
- docs claimed an eval framework path that did not exist
- e2e command coverage omitted `use-agent-skills`
- one e2e test used `task_uuid` before assignment
- `security-and-hardening` had an invalid JSON tool example
- advisory gaps existed around subordinate-boundary wording and `using-agent-skills` A0-specific eval assertions

## Candidate Result Summary

`cp-a001-harness-truth` fixed all baseline static gate and advisory failures and passed both regression layers.

## Infrastructure Notes

The direct runtime-integration run against the checkpoint copy had one path-bound failure because Agent Zero plugin discovery resolves the installed live plugin path. This was classified as a checkpoint-copy evaluation limitation. The comparable runtime run used the established live-overlay procedure:

1. backup live plugin
2. overlay candidate at `/a0/usr/plugins/a0_agent_skills`
3. run runtime-integration pytest
4. restore backup
5. verify full hash equality

`run-003` records `restore_ok: true` and no missing/added/changed files.

## Next Action

External promotion `external-promotion-001-cp-a001` has been applied and verified. Full e2e attempt `run-005` was invalid because pytest-xdist is unavailable; next action is `run-006` sequential full e2e without `-n`.

| `run-007-post-promotion-full-live-e2e-parallel` | `cp-a001-harness-truth` live | controlled parallel live e2e (4 groups concurrent + extension-behavior sequential) | 68 passed, 1 failed of 69 collected; full suite complete | valid; full suite complete | `runs/run-007-post-promotion-full-live-e2e-parallel.json`; group logs `runs/run-007-post-promotion-full-live-e2e-parallel/*.log` | complete; 1 pre-existing framework-level failure unrelated to rev-005 |

| `run-008-semantic-depth-baseline` | `cp-b001-runtime-contract-depth` | `semantic_depth_v1` | avg=11.12/15 (74.2%); D1 avg=0.75/3 (weakest); D2 avg=2.88/3; D3 avg=2.96/3; D4 avg=2.42/3; D5 avg=2.12/3 | valid baseline evidence | `runs/run-008-semantic-depth-baseline.json` | D1 (A0 Runtime Model Awareness) is universally weak; deepen runtime-contract references in all 24 skills |

| `run-009-semantic-depth-after-d1-edits` | `cp-b001-runtime-contract-depth` | `semantic_depth_v1` | avg=13.29/15 (88.6%); D1 avg=2.79/3 | valid; major improvement from baseline | `runs/run-009-semantic-depth-after-d1-edits.json` | D1 raised from 0.75 to 2.79; candidate eligible for promotion |
| `run-010-cp-b001-static-gates` | `cp-b001-runtime-contract-depth` | `a0_runtime_alignment_static_v1` | gate_passed=true; gate_failures=0; advisory_failures=0 | valid | `runs/run-010-cp-b001-static-gates.json` | static gates maintained after D1 edits |
| `run-011-cp-b001-structural-pytest` | `cp-b001-runtime-contract-depth` | structural/non-runtime pytest | 145 passed, 10 skipped, 85 deselected; exit=0 | valid | `runs/run-011-cp-b001-structural-pytest.log` | structural regression passed |
| `run-012-cp-b001-live-overlay-runtime-pytest` | `cp-b001-runtime-contract-depth` | runtime-integration pytest via live-overlay | 16 passed, 224 deselected; exit=0 | valid; live restored byte-for-byte | `runs/run-012-cp-b001-live-overlay-runtime-pytest.json`; log `runs/run-012-cp-b001-live-overlay-runtime-pytest.log` | runtime regression passed |

| `run-013-cp-d001-semantic-depth` | `cp-d001-d4-d5-e2e-evalrunner` | `semantic_depth_v1` | avg=14.54/15 (96.9%); D4=2.96/3; D5=2.92/3 | valid | `runs/run-013-cp-d001-semantic-depth.json` | D4 and D5 improved |
| `run-014-cp-d001-static-gates` | `cp-d001-d4-d5-e2e-evalrunner` | `a0_runtime_alignment_static_v1` | gate_passed=true; gate_failures=0; advisory_failures=0 | valid | `runs/run-014-cp-d001-static-gates.json` | static gates maintained |
| `run-015-cp-d001-structural-pytest` | `cp-d001-d4-d5-e2e-evalrunner` | structural/non-runtime pytest | 145 passed, 10 skipped, 85 deselected; exit=0 | valid | `runs/run-015-cp-d001-structural-pytest.log` | structural regression passed |
| `run-016-cp-d001-live-overlay-runtime-pytest` | `cp-d001-d4-d5-e2e-evalrunner` | runtime-integration pytest via live-overlay | 16 passed, 224 deselected; exit=0; restore_ok=true | valid | `runs/run-016-cp-d001-live-overlay-runtime-pytest.json` | runtime regression passed |
| `post-promotion-static-external-promotion-003-cp-d001` | `cp-d001-d4-d5-e2e-evalrunner` live | `a0_runtime_alignment_static_v1` | exit=0 | valid post-promotion | `promotion/external-promotion-003-cp-d001/logs/post-static.json` | live static verified |
| `post-promotion-semantic-external-promotion-003-cp-d001` | `cp-d001-d4-d5-e2e-evalrunner` live | `semantic_depth_v1` | exit=0; avg=14.54/15 | valid post-promotion | `promotion/external-promotion-003-cp-d001/logs/post-semantic.json` | live semantic verified |
| `post-promotion-structural-external-promotion-003-cp-d001` | `cp-d001-d4-d5-e2e-evalrunner` live | structural pytest | 145 passed; exit=0 | valid post-promotion | `promotion/external-promotion-003-cp-d001/logs/post-structural.log` | live structural verified |
| `post-promotion-runtime-external-promotion-003-cp-d001` | `cp-d001-d4-d5-e2e-evalrunner` live | runtime-integration pytest | 16 passed; exit=0 | valid post-promotion | `promotion/external-promotion-003-cp-d001/logs/post-runtime.log` | live runtime verified |
