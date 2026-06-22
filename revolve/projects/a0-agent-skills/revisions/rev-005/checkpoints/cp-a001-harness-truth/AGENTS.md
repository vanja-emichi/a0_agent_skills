# revolve/projects/a0-agent-skills/revisions/rev-005/checkpoints/cp-a001-harness-truth/AGENTS.md — Harness Truth Candidate

## Checkpoint ID

`cp-a001-harness-truth`

## Parent

`cp-live-20260620-0129`

## Branch

`branch-a-harness-truth`

## Storage

Compressed tarball at:

`checkpoints/cp-a001-harness-truth/subject/a0_agent_skills.tar.gz (compressed)`

Manifest:

`checkpoints/cp-a001-harness-truth/manifest.json`

## Restore Method

Evaluate the subject copy in place. Do not apply to `/a0/usr/plugins/a0_agent_skills/` unless later externally promoted by explicit decision.

## Identity Verification

Manifest records parent, branch, storage path, and base hashes of targeted files before candidate edits. Runtime verification additionally used live-overlay backup and restore with hash equality; see `runs/run-003-cp-a001-live-overlay-runtime-pytest.json`.

## Changes

Minimal runtime-truth/harness-alignment edits:

- fixed root plugin docs from 23 to 24 skills
- removed false claims that `agent-skills-eval` is checked out at `/a0/usr/projects/a0_agent_skills/eval/`
- reframed behavioral eval files as fixtures unless a runner path/result is verified
- added `use-agent-skills` to e2e command discovery coverage
- fixed `task_uuid` assignment in `tests/e2e/test_e2e_extension_behavior.py`
- fixed invalid JSON in `security-and-hardening` command example
- added explicit main-agent ownership wording in three subordinate/delegation sections
- added an A0-runtime-specific eval fixture to `using-agent-skills`

## Rationale

This candidate repairs the measuring stick and runtime-truth claims before any further content optimization. It directly addresses the user's concern that the previous Revolve loop rewarded expansion rather than alignment to `/a0` and the harness.

## Expected Benefit/Risk

Expected benefit: rev-005 can now distinguish runtime-alignment truth from keyword expansion.

Risk: candidate has not been externally promoted to the live plugin; live e2e full suite was not run after candidate overlay beyond runtime-integration tests.

## Results

Official runs:

- `run-002-cp-a001-runtime-alignment`: static runtime-alignment harness passed — gate_failures=0, advisory_failures=0.
- `run-004-cp-a001-structural-pytest`: structural/non-runtime regression passed — 145 passed, 10 skipped, 85 deselected, exit 0.
- `run-003-cp-a001-live-overlay-runtime-pytest`: runtime integration passed — 16 passed, 224 deselected, exit 0; live plugin restored with no hash differences.

## Decision

`internally promoted` as rev-005 current best. Eligible for external promotion if the user explicitly approves live plugin changes.

## Status

`promoted` internally.

## Promotion Status

Internal promotion complete. External promotion complete via `external-promotion-001-cp-a001`.

## Rollback Note

External rollback path: restore `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills` to `/a0/usr/plugins/a0_agent_skills/`. Internal rollback: set revision incumbent back to `cp-live-20260620-0129` and mark `branch-a-harness-truth` superseded or rejected.

## External Promotion

`external-promotion-001-cp-a001` applied `cp-a001-harness-truth` to `/a0/usr/plugins/a0_agent_skills/` and passed post-promotion static, structural, and runtime-integration verification.
