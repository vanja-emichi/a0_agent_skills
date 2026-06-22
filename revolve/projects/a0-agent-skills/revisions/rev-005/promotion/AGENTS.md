# revolve/projects/a0-agent-skills/revisions/rev-005/promotion/AGENTS.md — Promotion Records

## Purpose

Track internal and external promotions for rev-005.

## Promotions

| Promotion | Type | Promoted Checkpoint | Previous Incumbent/Live | Evidence | Affected Live Files | Rollback |
|---|---|---|---|---|---|---|
| `promotion-001-internal-cp-a001` | internal | `cp-a001-harness-truth` | `cp-live-20260620-0129` | `run-002`, `run-003`, `run-004` | none | set incumbent back to `cp-live-20260620-0129` |
| `external-promotion-001-cp-a001` | external | `cp-a001-harness-truth` | live plugin pre-promotion backup | post-static=0; post-structural=0; post-runtime=0; identity match=true | `/a0/usr/plugins/a0_agent_skills/` | restore `/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills.tar.gz` |

## promotion-001-internal-cp-a001

### Promoted Checkpoint

`cp-a001-harness-truth`

### Previous Incumbent

`cp-live-20260620-0129`

### Evidence

- Static runtime-alignment harness: `runs/run-002-cp-a001-runtime-alignment.json` — gate_passed=true, gate_failures=0, advisory_failures=0.
- Structural/non-runtime regression: `runs/run-004-cp-a001-structural-pytest.json` — exit 0, 145 passed, 10 skipped, 85 deselected.
- Runtime-integration regression: `runs/run-003-cp-a001-live-overlay-runtime-pytest.json` — exit 0, 16 passed, 224 deselected.
- Live-overlay restore verification: `restore_ok=true`, no missing/added/changed files.

### Affected Files

Internal checkpoint files only for the internal promotion.

## external-promotion-001-cp-a001

### Promoted Checkpoint

`cp-a001-harness-truth`

### Previous Live Artifact

`/a0/usr/plugins/a0_agent_skills/` before external promotion.

### Backup / Rollback Path

Pre-promotion backup:

`/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills.tar.gz`

Rollback command if needed:

```bash
rm -rf /a0/usr/plugins/a0_agent_skills
cp -a /a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-001-cp-a001/pre-promotion-live-backup-a0_agent_skills /a0/usr/plugins/a0_agent_skills
```

### Identity Verification

- Candidate matched live after apply: `True`
- Final live state matched expected candidate: `True`
- Missing files: `[]`
- Added files: `[]`
- Changed files: `[]`

### Post-Promotion Verification

| Check | Exit | Evidence |
|---|---:|---|
| Static runtime-alignment | 0 | `promotion/external-promotion-001-cp-a001/logs/post-static-runtime-alignment.json`; `promotion/external-promotion-001-cp-a001/logs/post-static.log` |
| Structural/non-runtime pytest | 0 | `promotion/external-promotion-001-cp-a001/logs/post-structural.log` |
| Runtime-integration pytest | 0 | `promotion/external-promotion-001-cp-a001/logs/post-runtime.log` |

### Result

External promotion applied successfully. Live plugin now matches `cp-a001-harness-truth`.

## Boundary

External live promotion is complete. Further changes require a new checkpoint/branch or user-directed follow-up.

## external-promotion-002-cp-b001

### Promoted Checkpoint

`cp-b001-runtime-contract-depth`

### Previous Live Artifact

`/a0/usr/plugins/a0_agent_skills/` before external promotion (was `cp-a001-harness-truth`).

### Backup / Rollback Path

`/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-002-cp-b001/pre-promotion-live-backup-a0_agent_skills.tar.gz`

Rollback command:
```bash
rm -rf /a0/usr/plugins/a0_agent_skills
cp -a /a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-002-cp-b001/pre-promotion-live-backup-a0_agent_skills /a0/usr/plugins/a0_agent_skills
```

### Post-Promotion Verification

| Check | Exit | Evidence |
|---|---:|---|
| Static runtime-alignment | 0 | `promotion/external-promotion-002-cp-b001/logs/post-static.json` |
| Semantic depth | 0 | `promotion/external-promotion-002-cp-b001/logs/post-semantic.json` |
| Structural pytest | 0 | `promotion/external-promotion-002-cp-b001/logs/post-structural.log` |
| Runtime-integration pytest | 0 | `promotion/external-promotion-002-cp-b001/logs/post-runtime.log` |
| Identity match | true | `promotion/external-promotion-002-cp-b001/promotion-result.json` |

### Result

External promotion applied successfully. Live plugin now matches `cp-b001-runtime-contract-depth` with domain-specific A0 Runtime Model sections in all 24 skills.

## external-promotion-003-cp-d001

### Promoted Checkpoint

`cp-d001-d4-d5-e2e-evalrunner`

### Previous Live Artifact

`/a0/usr/plugins/a0_agent_skills/` (was `cp-b001-runtime-contract-depth`).

### Backup / Rollback Path

`/a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005/promotion/external-promotion-003-cp-d001/pre-promotion-live-backup-a0_agent_skills.tar.gz`

### Post-Promotion Verification

| Check | Exit |
|---|---:|
| Static runtime-alignment | 0 |
| Semantic depth | 0 (avg 14.54/15) |
| Structural pytest | 0 (145 passed) |
| Runtime-integration pytest | 0 (16 passed) |
| Identity match | true |

### Result

External promotion applied successfully. Live plugin now matches `cp-d001-d4-d5-e2e-evalrunner`.
