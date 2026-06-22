# revolve/projects/a0-agent-skills/revisions/rev-005/eval/AGENTS.md — Evaluation Contract

## Purpose

Define a runtime-alignment evaluation for `a0_agent_skills` that rewards truthful Agent Zero integration rather than keyword expansion.

## Harness

`check_a0_runtime_alignment.py` performs static, reproducible checks over a plugin tree. It can run against the live plugin or any checkpointed candidate copy.

## Run Procedure

```bash
cd /a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-005
python3 eval/check_a0_runtime_alignment.py --plugin checkpoints/cp-live-20260620-0129/subject/a0_agent_skills --json-out runs/run-001-baseline-runtime-alignment.json
```

For candidate copies, replace the `--plugin` path with the candidate checkpoint subject path.

Optional regression guard for local candidate copies:

```bash
cd <candidate-subject>/
/opt/venv/bin/python -m pytest tests -q -m 'not e2e' --tb=short
```

Live e2e is tracked separately because it requires the installed plugin, live server on port 80, credentials, and cleanup of scheduler tasks.

## Case/Fixture Format

The rev-005 static harness treats these as first-class fixtures:

- plugin inventory: skills, commands, profiles
- root plugin `AGENTS.md`
- `tests/e2e/test_e2e_command_execution.py`
- `tests/e2e/test_e2e_extension_behavior.py`
- all `tests/e2e/test_*.py` syntax
- all `skills/*/SKILL.md`
- all `skills/*/evals/evals.json`

## Scoring

The harness reports JSON:

- `summary.gate_passed`: boolean
- `summary.gate_failures`: count of blocking failures
- `summary.advisory_failures`: count of non-blocking but quality-relevant failures
- `checks[]`: check-level pass/fail/evidence
- `skill_results[]`: skill-level static findings

## Acceptance Gates

A candidate is eligible for internal promotion only when:

1. `summary.gate_passed == true`
2. non-e2e pytest regression passes on the candidate copy
3. any remaining advisory failures are either fixed or explicitly classified with rationale
4. no new stale runtime claims are introduced

## Evaluator Limits

This harness is intentionally static. It does not prove live scheduler behavior, model compliance, or behavioral eval quality by itself. It is the first gate before deeper e2e or LLM-rubric evaluation.

## Failure Classes

| Class | Description | Required action |
|---|---|---|
| Subject failure | Plugin docs, tests, or skills contradict Agent Zero runtime reality | Fix in candidate branch |
| Harness failure | Static check is wrong, too broad, or misses intended reality | Revise harness in a new revision if comparability changes materially |
| Infrastructure failure | Files unreadable, test env missing, server unavailable | Record separately, do not score as subject behavior |
| Dataset/eval gap | Existing eval fixtures are not executable or not A0-specific | Create branch or future revision for eval runner integration |
| Objective change | User wants live promotion or different quality goal | Create/select a new revision before comparing scores |
