# revolve/projects/a0-agent-skills/revisions/rev-006/checkpoints/cp-a001-architecture-fixes/AGENTS.md

## Checkpoint ID

`cp-a001-architecture-fixes`

## Parent

`cp-000-rev006-baseline`

## Branch

`branch-a-architecture-fixes`

## Storage

Lean checkpoint: diff/patch-based from baseline. Only new/changed files tracked.

## Restore Method

Baseline manifest at `cp-000-rev006-baseline/manifest.sha256` covers 155 original files. New files can be selectively removed for rollback.

## Identity Verification

Pending — will generate delta manifest after changes are applied.

## Changes (applied)

1. Ported `web-performance-auditor` agent profile from source repo to A0 native format
2. Added `webperf` command in A0 native format (`webperf.command.yaml` + `webperf.txt`)
3. Created `tests/test_runtime_architecture.py` with 22 deterministic runtime tests across 8 classes
4. Updated plugin AGENTS.md: 3 to 4 profiles, 8 to 9 commands
5. Updated test files to include `webperf` in expected command lists
6. Created `a0-skills-test` project with `agent_skills_enabled: true` for test isolation

## Rationale

Baseline evidence confirmed source parity gaps and lack of deterministic runtime tests. This candidate addresses both while proving the plugin integrates natively.

## Benefit/Risk

Benefit: full source parity, provable architecture integration via runtime/API-first tests.
Risk: new profile/command needs testing.

## Results

- `run-002`: runtime architecture — 22/22 passed
- `run-003`: structural — 145 passed, 10 skipped
- `run-004`: existing runtime — 12/12 passed

## Status

`promising` — all evaluation gates passed; eligible for internal promotion.

## Rollback Note

Remove new files (web-performance-auditor profile, webperf command, test harness). Restore changed files from baseline manifest.
