# revolve/projects/a0-agent-skills/revisions/rev-004/eval/AGENTS.md

## Purpose

Evaluation contract for rev-004. This revision assesses deeper content quality beyond automated presence/absence checks. Uses LLM-graded rubric evaluation combined with the rev-003 automated scanner as regression guard.

## Harness

Three-part harness:
1. automated content-depth scan (rev-003 regression guard)
2. LLM-graded deeper-audit rubric
3. regression guard (structural tests)

### Part 1: Automated Content Scanner (regression guard)

Reuse the rev-003 scanner with the fixed regex. Must maintain ≥7.96/8 average.

### Part 2: LLM-Graded Deeper-Audit Rubric

For each skill, rate 0-3 on four dimensions:

#### Dimension 1: Claude/Codex Assumption Removal
- 0 = Multiple Claude/Codex-specific patterns remain (e.g., `str_replace_editor`, `Bash>`, `.claude` references, Claude-specific workflow steps)
- 1 = Some remnants but mostly cleaned
- 2 = No obvious Claude/Codex remnants; tool names are A0-native
- 3 = Fully A0-native; workflow patterns actively leverage A0's unique capabilities

#### Dimension 2: A0-Native Guidance Quality
- 0 = Parallel/delegation/project-context sections are boilerplate copy-paste
- 1 = Sections exist but feel generic, not domain-specific
- 2 = Sections are domain-tailored and reasonably actionable
- 3 = Sections are deeply domain-specific, include concrete examples, and genuinely improve workflow

#### Dimension 3: Eval Alignment
- 0 = Evals test generic domain knowledge with no A0-specific behavior
- 1 = Some evals reference skills/tools but are still generic
- 2 = Evals test skill-specific behavior
- 3 = Evals test A0-specific behavior (parallel, subordinate, project context)

#### Dimension 4: Workflow Naturalness
- 0 = Skill reads like a Claude skill with A0 tool names swapped in
- 1 = Partially adapted but still feels mechanical
- 2 = Reads naturally as an A0 skill
- 3 = Reads as a purpose-built A0 skill that couldn't exist for Claude

Total rubric score: 0-12 per skill.

### Part 3: Regression Guard

161 structural/runtime tests must pass. Automated content depth must stay ≥7.96/8.

## Run Procedure

```bash
cd /a0/usr/plugins/a0_agent_skills

# 1. Automated content depth (regression guard)
python3 /a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-002/eval/check_content_depth.py

# 2. Regression tests
/opt/venv-a0/bin/python -m pytest tests -q -m 'not e2e' --tb=short

# 3. LLM rubric (pilot skills only, delegated to subordinate with rubric)
# Use call_subordinate with researcher/developer profile to grade each skill
```

## Scoring

- Automated: 0-8 per skill (must stay ≥7.96/8 average)
- Rubric: 0-12 per skill (pilot only)
- Regression: binary pass/fail

## Acceptance Gates

- Automated score must not regress below 7.96/8
- Structural regression: 161/161 pass
- Rubric improvement: candidate must improve at least one dimension for at least one pilot skill

## Failure Classes

| Class | Description | Action |
|---|---|---|
| **Subject failure** | Skill content is weak or has Claude remnants | Fix in candidate |
| **Regression** | Automated score or structural tests regress | Block promotion |
| **Harness failure** | Rubric evaluation is inconsistent | Calibrate rubric |
