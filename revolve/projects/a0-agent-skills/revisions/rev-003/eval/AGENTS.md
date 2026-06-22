# revolve/projects/a0-agent-skills/revisions/rev-003/eval/AGENTS.md

## Purpose

Evaluation contract for rev-003. This revision exists because regression verification must be comparable at the live plugin path; checkpoint-clone regression in rev-002 was invalidated by a path-bound lifecycle-hook assertion.

## Harness

Three-part harness:
1. automated content-depth scan
2. live-overlay regression guard
3. manual pilot-skill rubric review

### Part 1: Automated Content Scanner

Reuse the rev-002 automated content-depth logic for presence/absence of A0-native patterns:
- `parallel_tool_mentioned`
- `call_subordinate_mentioned`
- `browser_tool_mentioned`
- `skills_tool_load_syntax`
- `project_context_aware`
- `has_related_section`
- `has_files_section`
- `has_native_triggers`

Total automated score: 0-8 per skill.

### Part 2: Live-Overlay Regression Guard

Regression evidence must be gathered at the actual live plugin path `/a0/usr/plugins/a0_agent_skills/`.

Procedure:
1. Backup only the candidate-touched skill folders from the live plugin.
2. Overlay candidate skill folders into the live plugin path.
3. Run the non-e2e regression guard from the live plugin path.
4. Optionally rerun e2e when the candidate could affect runtime behavior materially.
5. Restore the original live skill folders immediately after the run.
6. Verify the restore succeeded.

This procedure preserves path comparability while keeping rollback explicit.

### Part 3: Manual Pilot Rubric

For pilot skills, rate 0-3 on:
1. **A0-native concept coverage**
2. **Content adaptation depth**
3. **Eval alignment**
4. **Workflow A0-context**

## Run Procedure

```bash
cd /a0/usr/plugins/a0_agent_skills

# 1. Automated content depth scan
python3 /a0/usr/projects/a0_agent_skills/revolve/projects/a0-agent-skills/revisions/rev-002/eval/check_content_depth.py

# 2. Live-overlay regression guard
/opt/venv-a0/bin/python -m pytest tests -q -m 'not e2e' --tb=short

# 3. E2e if needed
/opt/venv-a0/bin/python -m pytest tests/e2e -v -m e2e -n 4 --tb=short
```

## Case/Fixture Format

Each skill is a case for the automated scanner. Pilot skills additionally receive manual rubric review. Regression guard is binary pass/fail under the live-overlay procedure.

## Scoring

- Automated: 0-8 per skill, average across all skills
- Regression: binary comparable pass/fail
- Manual rubric: 0-12 per pilot skill

## Acceptance Gates

- Candidate must improve at least one rev-003 content-depth dimension.
- Candidate must pass the rev-003 live-overlay regression guard.
- If e2e is rerun, no new failures are allowed.

## Failure Classes

| Class | Description | Action |
|---|---|---|
| **Subject failure** | Candidate content is weaker or regresses behavior | Fix candidate or reject |
| **Regression** | rev-001 dimension breaks under live-overlay evaluation | Block promotion and fix |
| **Harness failure** | Backup/overlay/restore or measurement procedure is wrong | Repair harness before comparing |
| **Comparability failure** | Evidence came from clone/path-mismatched execution | Record as historical only |
