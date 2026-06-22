# revolve/projects/a0-agent-skills/revisions/rev-004/checkpoints/cp-000-rev004-baseline/AGENTS.md

## Checkpoint ID

`cp-000-rev004-baseline`

## Parent

Live plugin state carried forward from rev-003 completion.

## Branch

Baseline — no branch.

## Storage

`checkpoints/cp-000-rev004-baseline/plugin/skills/` (24 skill folders)

## Restore Method

```bash
cp -r checkpoints/cp-000-rev004-baseline/plugin/skills/* /a0/usr/plugins/a0_agent_skills/skills/
```

## Changes

None — this is the rev-004 starting incumbent: current live plugin state as of 2026-06-20 (post rev-003 full-scale content-depth promotion + cleanup).

## Rationale

Preserve the current strong live plugin as the rev-004 baseline before deeper content-quality audit.

## Results

**Run:** `run-001-rev004-baseline-rubric` (2026-06-20)
- LLM rubric: average 8.4/12 across 5 pilot skills
- TDD: 10/12 (gold standard); 4 skills: 8/12 each
- Automated content depth: 7.96/8 (from rev-003)
- Regression guard: 161/161 pass

**Systematic findings:**
- Universal D3=2: no A0-specific evals
- TDD is outlier with concrete JSON examples
- npm/Node.js centrism despite A0 being Python
- No Claude/Codex remnants
- Correctness bug: `memory_save` in code-review-and-quality

## Status

`baseline` — incumbent checkpoint for rev-004.
