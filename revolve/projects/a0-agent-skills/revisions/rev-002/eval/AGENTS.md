# revolve/projects/a0-agent-skills/revisions/rev-002/eval/AGENTS.md

## Purpose

Evaluation contract for measuring content depth and A0-native integration quality of each skill. Complements rev-001's structural checks with deeper content analysis.

## Harness

Two-part harness: (1) automated content scanner, (2) LLM rubric evaluation.

### Part 1: Automated Content Scanner (`check_content_depth.py`)

Checks each skill for presence/absence of A0-native patterns:

| Check | What it scans for | Score |
|---|---|---|
| `parallel_tool_mentioned` | References to `parallel` tool in any context | 0 or 1 |
| `call_subordinate_mentioned` | References to `call_subordinate` in any context | 0 or 1 |
| `browser_tool_mentioned` | References to `browser` tool (frontend skills only) | 0 or 1 |
| `skills_tool_load_syntax` | At least one `skills_tool` load example with proper syntax | 0 or 1 |
| `project_context_aware` | References to `.a0proj/`, project directory, or project path | 0 or 1 |
| `has_related_section` | Has `**Related:**` section with skill cross-references | 0 or 1 |
| `has_files_section` | Has `## Files` section | 0 or 1 |
| `has_native_triggers` | Triggers are A0-native (not copied from Claude reference) | 0 or 1 |

Total automated score: 0-8 per skill.

### Part 2: Regression Guard (from rev-001)

- Structural + runtime tests (161 tests)
- E2e tests (30 tests)
- Tool name nativity (24/24)
- Cross-references (24/24)

All rev-001 dimensions must stay green.

### Part 3: LLM Rubric (manual, pilot skills only)

Per skill, rate 0-3 on:
1. **A0-native concept coverage** (0=none, 1=mentioned, 2=explained, 3=with examples)
2. **Content adaptation depth** (0=Claude assumptions remain, 1=removed but no A0 replacement, 2=A0 replacement, 3=deep A0 integration)
3. **Eval alignment** (0=generic, 1=skill-relevant, 2=tests unique workflow, 3=tests A0-specific behavior)
4. **Workflow A0-context** (0=none, 1=mentions tools, 2=explains A0 patterns, 3=native A0 workflow)

## Run Procedure

```bash
cd /a0/usr/plugins/a0_agent_skills

# 1. Automated content scanner
python3 revolve/projects/a0-agent-skills/revisions/rev-002/eval/check_content_depth.py

# 2. Regression guard
/opt/venv-a0/bin/python -m pytest tests -v -m 'not e2e' --tb=short

# 3. E2e (if needed)
A0_E2E_USERNAME=$USER A0_E2E_PASSWORD=$PASS /opt/venv-a0/bin/python -m pytest tests -v -m e2e -n 4 --tb=short
```

## Case/Fixture Format

Each skill is a case. Dimensions 1-8 are automated (Part 1). Dimensions 9-12 are LLM rubric (Part 3).

## Scoring

- Automated: 0-8 per skill, average across 24 skills = overall automated score
- Regression: binary (all pass / some fail)
- LLM rubric: 0-12 per skill (pilot only)

## Acceptance Gates

- **Promotion:** Candidate must not regress rev-001 (all structural + e2e pass), and must improve at least one automated content depth check.

## Failure Classes

| Class | Description | Action |
|---|---|---|
| **Subject failure** | Skill lacks A0-native content depth | Fix in candidate checkpoint |
| **Regression** | rev-001 dimension broke | Fix immediately, block promotion |
| **Harness failure** | Content scanner is wrong | Fix harness |
