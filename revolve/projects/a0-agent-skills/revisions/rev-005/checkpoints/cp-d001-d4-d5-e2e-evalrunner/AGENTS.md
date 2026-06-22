# revolve/projects/a0-agent-skills/revisions/rev-005/checkpoints/cp-d001-d4-d5-e2e-evalrunner/AGENTS.md — D4/D5/e2e/eval-runner Candidate

## Checkpoint ID

`cp-d001-d4-d5-e2e-evalrunner`

## Parent

`cp-b001-runtime-contract-depth`

## Branch

`branch-d-d4-d5-e2e-evalrunner`

## Storage

`checkpoints/cp-d001-d4-d5-e2e-evalrunner/subject/a0_agent_skills.tar.gz (compressed)`

## Changes

1. D4 Project Context Depth: deepened 11 skills with AGENTS.md chain behavior, cross-session promptinclude persistence, and live-plugin runtime-override awareness
2. D5 Eval Specificity: added A0-runtime-specific assertions to 17 eval fixtures
3. E2e test fix: changed `test_subordinate_does_not_see_override` to check for specific auto-load injection text instead of generic 'skill discovery' content that all agents see
4. Eval-runner formalization: added explicit 'Eval Runner Status' section in root AGENTS.md confirming no runner is installed and fixtures are review-only

## Results

- `run-013`: semantic depth avg **14.54/15 (96.9%)**
  - D1: 2.79/3 | D2: 2.88/3 | D3: 3.0/3 | D4: **2.96/3** | D5: **2.92/3**
- `run-014`: static gates passed (0 failures, 0 advisory)
- `run-015`: structural 145 passed, 10 skipped
- `run-016`: runtime 16 passed; live restored byte-for-byte
- Post-promotion: all 4 checks exit 0 on live plugin

## Status

`promoted` internally and externally.

## Rollback Note

External rollback: restore `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-003-cp-d001/pre-promotion-live-backup-a0_agent_skills` to `/a0/usr/plugins/a0_agent_skills/`.
