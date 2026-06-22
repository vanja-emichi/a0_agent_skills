# revolve/projects/a0-agent-skills/revisions/rev-005/checkpoints/cp-live-20260620-0129/AGENTS.md — Incumbent Checkpoint

## Checkpoint ID

`cp-live-20260620-0129`

## Parent

Live plugin at `/a0/usr/plugins/a0_agent_skills/` as of rev-005 start.

## Branch

Incumbent baseline, no branch.

## Storage

Compressed tarball at:

`checkpoints/cp-live-20260620-0129/subject/a0_agent_skills.tar.gz (compressed)`

Manifest:

`checkpoints/cp-live-20260620-0129/manifest.json`

## Restore Method

Extract tarball to restore: `tar xzf checkpoints/cp-live-20260620-0129/subject/a0_agent_skills.tar.gz -C checkpoints/cp-live-20260620-0129/subject/`

Use the extracted subject copy directly for local evaluation. To restore live state for rollback comparison, copy from `subject/a0_agent_skills/` back to `/a0/usr/plugins/a0_agent_skills/` only after explicit external promotion/rollback approval.

## Identity Verification

Manifest records file count, skill count, command count, profile count, and hashes of representative key files.

## Changes

None. This is an unmodified checkpoint of the live plugin.

## Rationale

Preserve the rev-004 externally promoted live plugin before recalibrating rev-005 evaluation.

## Expected Benefit/Risk

Benefit: provides comparable baseline for honest runtime-alignment scoring.

Risk: copy-based evaluation cannot prove live scheduler behavior; e2e remains a separate live-installed-plugin evidence layer.

## Results

Official run: `run-001-baseline-runtime-alignment`

- Harness: `a0_runtime_alignment_static_v1`
- Raw result: `runs/run-001-baseline-runtime-alignment.json`
- Validity: valid subject-failure evidence
- Gate result: failed
- Gate failures: 5
- Advisory failures: 1

Failure cluster:
- `docs.skill_count_not_stale` — root plugin AGENTS.md must not claim 23 skills when inventory has 24
- `docs.eval_framework_claim_truthful` — docs must not claim a cloned eval framework path unless it exists
- `e2e.command_discovery_covers_all_commands` — e2e command discovery list should match installed command manifests
- `e2e.no_obvious_task_uuid_bug` — e2e extension behavior test should not use task_uuid before assignment
- `skills.no_invalid_tool_or_forbidden_refs` — skills should not contain nonexistent tools, Claude artifacts, invalid tool JSON, or missing evals


## Status

`rejected` under rev-005 gates; retained as baseline incumbent lineage.

## Promotion Status

Not promotable under rev-005. Use as parent for candidate fixes.

## Rollback Note

Live plugin remains untouched by this checkpoint operation.

## Supersession

Superseded by `cp-a001-harness-truth` as rev-005 current best after `cp-a001-harness-truth` passed static runtime-alignment, structural, and runtime-integration checks.
