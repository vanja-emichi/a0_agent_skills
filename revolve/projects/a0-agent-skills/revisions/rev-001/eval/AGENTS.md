# revolve/projects/a0-agent-skills/revisions/rev-001/eval/AGENTS.md

## Purpose

Evaluation contract for auditing and scoring the native Agent Zero integration quality of each skill in the `a0_agent_skills` plugin. Leverages the plugin's existing 2,963-line test harness rather than reinventing it.

## Harness

The harness is the plugin's existing pytest suite plus targeted checks for gaps.

### Existing Test Coverage (leveraged)

| Dimension | Test File(s) | What it checks |
|---|---|---|
| **Frontmatter validity** | `tests/test_structure.py` | plugin.yaml, command YAML, agent.yaml schema validation |
| **Runtime loading** | `tests/test_runtime_skills_and_agents.py` | framework skill discovery, skills_tool read_file, subagent profiles |
| **Runtime commands** | `tests/test_runtime_commands.py` | command discovery, resolution, rendering |
| **Runtime extensions** | `tests/test_runtime_extensions_and_hooks.py` | simplify-ignore, SDD cache, skill auto-unload |
| **Eval schema validity** | `tests/test_eval_report.py` | reads/validates eval workspace data integrity |
| **Behavioral (e2e)** | `tests/e2e/` | full e2e suite (skill loading, command execution, routing, extension behavior) |

### Targeted Checks (to create)

| Dimension | Script | What it checks |
|---|---|---|
| **Tool name nativity** | `eval/check_tool_names.py` | Regex scan of all SKILL.md files for non-native tool names |
| **Cross-references** | `eval/check_cross_refs.py` | Validates skill-to-skill references use `skills_tool` syntax correctly |

## Run Procedure

### Standard baseline/candidate run (deterministic, no server):

```bash
cd /a0/usr/plugins/a0_agent_skills

# 1. Structural + runtime tests
/opt/venv-a0/bin/python -m pytest tests -v -m 'not e2e' --tb=short --junitxml=rev-001-result.xml

# 2. Targeted checks
python3 revolve/projects/a0-agent-skills/revisions/rev-001/eval/check_tool_names.py
python3 revolve/projects/a0-agent-skills/revisions/rev-001/eval/check_cross_refs.py
```

For candidate runs, apply the candidate patch to the live plugin, run the harness, then restore the incumbent.

### E2e run (requires live server):

```bash
A0_E2E_USERNAME=$USER A0_E2E_PASSWORD=$PASS /opt/venv-a0/bin/python -m pytest tests -v -m e2e -n 4 --tb=short
```

## Case/Fixture Format

Each skill is a case. The audit checks 6 dimensions per skill:

| # | Dimension | Existing Coverage | Type |
|---|---|---|---|
| 1 | **Frontmatter validity** | `test_structure.py` | Deterministic |
| 2 | **Tool name nativity** | `check_tool_names.py` (new) | Deterministic |
| 3 | **Cross-references** | `check_cross_refs.py` (new) | Deterministic |  
| 4 | **Runtime loading** | `test_runtime_skills_and_agents.py` | Deterministic (runtime) |
| 5 | **Eval schema validity** | `test_eval_report.py` | Deterministic |
| 6 | **Behavioral correctness** | `tests/e2e/` suite | LLM/Manual |

## Scoring

- Binary pass/fail per dimension per skill
- Per-skill score = dimensions passed / 6
- Overall plugin score = average of per-skill scores
- Test suite results: pass count / total (excluding infrastructure skips)

## Acceptance Gates

- **Candidate promotion gate:** Candidate must not regress any passing test vs incumbent, and must either fix a failing test or improve a targeted check score.
- **No regressions:** All tests that passed on incumbent must still pass on candidate.
- **No overfitting:** Fixes must generalize across skills, not hardcode specific eval cases.

## Evaluator Limits

- Dimension 6 (behavioral) uses the e2e test suite which requires a live server. Run during baseline and candidate evaluation phases.
- Dimensions 1–5 are deterministic. Run on every skill in every batch.
- Targeted check scripts (dimensions 2, 3) must be created before the formal baseline.

## Case Additions

- If new skills are added to the plugin, they become new cases automatically (test_structure.py auto-discovers).
- If `observability-and-instrumentation` is ported, it becomes case 24.

## Failure Classes

| Class | Description | Action |
|---|---|---|
| **Subject failure** | Skill has integration issue (bad tool name, missing trigger, etc.) | Fix in candidate checkpoint |
| **Harness failure** | Test itself is wrong or stale | Fix harness, rerun baseline, create new revision only if scoring changes |
| **Infrastructure failure** | Test fails due to environment issue (missing pytest, wrong Python) | Fix infrastructure before continuing |
| **Dataset gap** | No test covers a real integration issue | Add test or targeted check, potentially new revision |
