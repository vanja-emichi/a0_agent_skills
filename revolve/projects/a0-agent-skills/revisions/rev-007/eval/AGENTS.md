# revolve/projects/a0-agent-skills/revisions/rev-007/eval/AGENTS.md — Evaluation Contract

## Purpose

Verify references porting completeness without regression.

## Run Procedure

1. Run structural tests: `cd /a0/usr/plugins/a0_agent_skills && /opt/venv/bin/python -m pytest tests/ -x -q --tb=short`
2. Run runtime tests: `cd /a0/usr/plugins/a0_agent_skills && /opt/venv-a0/bin/python -m pytest tests/test_runtime_architecture.py tests/test_runtime_skills_and_agents.py -x -q --tb=short`
3. Verify observability-checklist.md exists
4. Verify security-checklist.md contains adapted Threat Modeling + AI/LLM Security sections

## Case Format

| Case | Type | Pass Criteria |
|---|---|---|
| EC-001 | regression | All 145+ structural tests pass |
| EC-002 | regression | All runtime architecture tests pass |
| EC-003 | new content | observability-checklist.md exists in references/ |
| EC-004 | enriched content | security-checklist.md has Threat Modeling section |
| EC-005 | enriched content | security-checklist.md has AI/LLM Security section |
| EC-006 | enriched content | security-checklist.md adapted for A0 (no Claude/npm-specific language) |

## Failure Classes

- Regression: existing tests fail → candidate rejected.
- Content gap: new file missing or incomplete → candidate needs rework.
- Adaptation failure: upstream content copied verbatim without A0 adaptation → candidate needs rework.
