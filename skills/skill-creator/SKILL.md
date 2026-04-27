---
name: skill-creator
description: Create, edit, test, grade, benchmark, and optimize Agent Zero skills. Full lifecycle skill development with scheduler-based evaluation. Use this skill when users want to create a skill, improve an existing skill, run skill tests, grade outputs, benchmark performance, or optimize skill descriptions. Also use when users mention skills, skill creation, skill testing, skill evaluation, or want to package a skill.
---

# Skill Creator

## Overview

Create, test, grade, benchmark, and optimize Agent Zero skills through a scheduler-driven evaluation workflow. This skill manages the full skill lifecycle from creation through validation, testing, and iterative improvement.

## When to Use

- Creating a new Agent Zero skill from scratch
- Editing or improving an existing skill's SKILL.md
- Running test evaluations against a skill (with-skill vs without-skill)
- Grading skill test outputs against expectations
- Benchmarking skill performance across multiple runs
- Optimizing a skill's trigger description for better activation
- Packaging a skill for distribution
- User mentions "create a skill", "test this skill", "benchmark", "optimize description"

## Anatomy of a Skill

```
skill-name/
├── SKILL.md (required — YAML frontmatter + Markdown instructions)
└── Bundled Resources (optional)
    ├── scripts/    — Executable code for deterministic tasks
    ├── references/ — Docs loaded into context as needed
    └── assets/     — Files used in output
```

## Progressive Disclosure

- **Metadata** (name + description) — Always in context
- **SKILL.md body** — Loaded when skill triggers
- **Bundled resources** — Loaded as needed

Keep SKILL.md under 500 lines. Move detail to references/.

## Script Paths

All scripts live in this skill's `scripts/` directory.
Resolve `<scripts-dir>` to the absolute path of `skills/skill-creator/scripts/` at runtime.

- `<scripts-dir>/quick_validate.py <skill-path>` — Validate skill structure
- `<scripts-dir>/package_skill.py <skill-path> [output-dir]` — Package into .zip
- `<scripts-dir>/aggregate_benchmark.py <workspace-path>` — Aggregate results
- `<scripts-dir>/generate_review.py <workspace-path>` — Markdown review
- `<scripts-dir>/run_loop.py init <skill-path> <evals-path> [--workspace <dir>]` — Initialize optimization
- `<scripts-dir>/run_loop.py record-results <workspace>` — Record iteration results (reads stdin)
- `<scripts-dir>/run_loop.py iteration-status <workspace>` — Print current status
- `<scripts-dir>/run_loop.py select-best <workspace>` — Select best description
- `<scripts-dir>/run_loop.py report <workspace>` — Generate final report
- `<scripts-dir>/improve_description.py <workspace>` — Generate LLM improvement context

## Evaluation Workers

You orchestrate three evaluation workers via `scheduler:create_adhoc_task`:

| Worker | Profile | Purpose | Output |
|--------|---------|---------|--------|
| Grader | `skill-grader` | Evaluate assertions against outputs | `grading.json` |
| Comparator | `skill-comparator` | Blind A/B comparison | `comparison.json` |
| Analyzer | `skill-analyzer` | Post-hoc analysis | `benchmark_notes.json` |

Each worker's instructions live in `agents/<worker>/prompts/agent.system.main.role.md`.
Pass that content as the `system_prompt` for scheduler tasks.

## Scheduler Pattern

Follow these rules for all evaluation work:

1. **Only scheduler tasks for real work** — test execution, grading, benchmarking, optimization
2. **All tasks use `dedicated_context: true`** — each task runs in clean isolation
3. **Notification pattern** — `notify_user` at phase transitions (progress at start, success at end)
4. **Create all → run all → wait all** — maximize parallelism within each phase
5. **Never assume success** — always `wait_for_task`
6. **Error recovery** — on task failure, present to user, let human decide: retry, skip, or abort

### Task Lifecycle

```
notify_user type=progress title="Phase X – <Name>"
Loop: scheduler:create_adhoc_task for each work item (dedicated_context: true)
Loop: scheduler:run_task for each created task
Loop: scheduler:wait_for_task for each task
Read results from filesystem
notify_user type=success title="Phase X Complete"
```

## Schema Reference

Key JSON schemas (full details in `references/schemas.md`):

**grading.json**: `{eval_id, overall_pass: bool, assertions: [{name, pass, evidence, severity}]}`

**comparison.json**: `{eval_id, preferred: "A"|"B", reasoning, criteria: {criterion, winner, rationale}}`

**benchmark_notes.json**: `[{note, category, severity, suggestion}]`

**benchmark.json**: `{evals: [{eval_id, configurations: {with_skill: {runs}, without_skill: {runs}}}]}]`

**optimization_history.json**: `{iterations: [{description, train_score, test_score, timestamp}]}`

---

## Feature 1: Create a Skill

Determine where the user is in the process and jump in.
Extract workflow context from conversation if user says "turn this into a skill".
Ask the user: "What should this skill enable the agent to do?"
Ask the user: "When should this skill trigger? What phrases or contexts?"
Ask the user: "What's the expected output format?"
Determine if test cases would be valuable based on output objectivity.
Suggest testing default based on skill type; let the user decide.
Create the skill directory at the specified path.
Write the SKILL.md with YAML frontmatter (name + description).
Make the description pushy — include trigger phrases and contexts to combat under-triggering.
Write the body with atomic instructions (one action per line).
Include examples, edge cases, and output format templates where helpful.
Present the draft SKILL.md to the user for review.
Create 2-3 realistic test prompts if testing was agreed upon.
Save test prompts to `evals/evals.json` in the skill directory.
Run: `python <scripts-dir>/quick_validate.py <skill-path>`
Fix any validation errors.

---

## Feature 2: Edit / Improve an Existing Skill

Read the existing SKILL.md.
Preserve the original skill name and directory location.
Identify issues the user wants addressed.
Read any existing eval results from the workspace if present.
Copy the skill to a writable location if the original is read-only.
Create a workspace directory `<skill-name>-workspace/` sibling to the skill.
Initialize `history.json` with the current version as v0 baseline.
Apply the requested edits to the SKILL.md.
Run: `python <scripts-dir>/quick_validate.py <skill-path>`
Ask the user to confirm the changes.
Offer to re-run tests against the updated skill.
Save the new version as v1 in history.json.
Repeat the edit-test cycle until the user is satisfied.

---

## Feature 3: Test a Skill

Read `evals/evals.json` from the skill directory.
Create the workspace directory `<skill-name>-workspace/` if it doesn't exist.
Create `iteration-1/` in the workspace.
notify_user type=progress title="Phase Test – Running test cases"
For each test case in evals.json:
  Create `eval-<id>/` in the iteration directory.
  Create adhoc task: `scheduler:create_adhoc_task`
    name: `test-eval-<id>-with-skill`
    system_prompt: "You are a test executor. Load the specified skill via skills_tool:load, execute the task, save all outputs and metrics."
    dedicated_context: true
    message: "Load skill at <skill-path> via skills_tool:load. Execute this task: <prompt>. Save all outputs to <workspace>/iteration-<N>/eval-<id>/with-skill/outputs/. Save a metrics.json with tool usage stats."
  Create adhoc task: `scheduler:create_adhoc_task`
    name: `test-eval-<id>-without-skill`
    system_prompt: "You are a test executor. Execute the task without loading any skill, save all outputs and metrics."
    dedicated_context: true
    message: "Execute this task without loading any skill: <prompt>. Save all outputs to <workspace>/iteration-<N>/eval-<id>/without-skill/outputs/. Save a metrics.json with tool usage stats."
Run all tasks: `scheduler:run_task` for each.
Wait for all tasks: `scheduler:wait_for_task` for each.
  If a task failed: present failure to user with options (retry, skip, abort).
Save timing data to `timing.json` in each run directory.
Draft assertions for each test case while reviewing results.
Add assertions to `evals/evals.json` under `expectations` for each eval.
notify_user type=success title="Phase Test Complete"
Proceed to Feature 4 (Grade) with the collected outputs.

---

## Feature 4: Grade Outputs

notify_user type=progress title="Phase Grade – Evaluating outputs"
For each eval directory in the current iteration:
  Read the expectations from `evals/evals.json` for this eval.
  Read the grader instructions from `agents/skill-grader/prompts/agent.system.main.role.md`.
  Create adhoc task: `scheduler:create_adhoc_task`
    name: `grade-eval-<id>`
    system_prompt: <grader instructions content>
    dedicated_context: true
    message: "Grade the outputs at <workspace>/iteration-<N>/eval-<id>/. Expectations: <expectations list>. Write results to <workspace>/iteration-<N>/eval-<id>/grading.json. Use programmatic checks where possible via code_execution_tool."
Run all tasks: `scheduler:run_task` for each.
Wait for all tasks: `scheduler:wait_for_task` for each.
  If a task failed: present failure to user with options.
Read all `grading.json` files from each eval directory.
Use programmatic checks where possible (run scripts via `code_execution_tool`).
notify_user type=success title="Phase Grade Complete"
Present a summary to the user: pass rates, failures, evidence.
Flag any weak assertions identified by the grader.
Ask the user for feedback on the results.
If the user wants improvements, proceed to Feature 2 (Edit) and re-test.

---

## Feature 5: Benchmark

Read `evals/evals.json` from the skill directory.
Determine the number of runs per configuration (default: 3).
notify_user type=progress title="Phase Benchmark – Running benchmarks"
For each eval, for each run number (1 to N), for each configuration (with_skill, without_skill):
  Create adhoc task: `scheduler:create_adhoc_task`
    name: `bench-eval-<id>-run-<n>-<config>`
    system_prompt: "You are a test executor. Execute the task and save outputs with metrics."
    dedicated_context: true
    message: "<Load skill if with_skill: Load skill at <skill-path> via skills_tool:load.> Execute: <prompt>. Save outputs to <workspace>/iteration-<N>/eval-<id>/<config>-run-<n>/outputs/. Save metrics.json with tool usage stats."
Run all tasks: `scheduler:run_task` for each.
Wait for all tasks: `scheduler:wait_for_task` for each.
  If a task failed: present failure to user with options.
Collect `metrics.json` and `timing.json` from each run.
Run: `python <scripts-dir>/aggregate_benchmark.py <workspace>/iteration-<N>`
Verify the resulting `benchmark.json` uses correct field names.
Create adhoc task for comparison: `scheduler:create_adhoc_task`
  name: `compare-eval-<id>`
  system_prompt: <comparator instructions from agents/skill-comparator/prompts/agent.system.main.role.md>
  dedicated_context: true
  message: "Blind compare outputs for eval <id>. With-skill outputs: <path>. Without-skill outputs: <path>. Write comparison.json to <workspace>/iteration-<N>/comparison.json."
Create adhoc task for analysis: `scheduler:create_adhoc_task`
  name: `analyze-benchmark`
  system_prompt: <analyzer instructions from agents/skill-analyzer/prompts/agent.system.main.role.md>
  dedicated_context: true
  message: "Analyze benchmark at <workspace>/iteration-<N>/benchmark.json. Skill path: <skill-path>. Write notes as JSON array to <workspace>/iteration-<N>/benchmark_notes.json."
Run and wait for comparator and analyzer tasks.
Run: `python <scripts-dir>/generate_review.py <workspace>/iteration-<N>`
notify_user type=success title="Phase Benchmark Complete"
Present the terminal markdown review to the user.
Discuss the results with the user.
Decide whether to iterate (return to Feature 2) or proceed.

---

## Feature 6: Optimize Skill Description

Generate trigger evals → Train/test split → Evaluate triggers → Improve description → Select best → Apply.

Ask the user: "Ready to optimize the skill description for better triggering?"
Locate the skill directory and resolve `<scripts-dir>`.
Create a workspace directory sibling to the skill directory.
Ask the user for 20 trigger evaluation queries: mix of should-trigger and should-not-trigger cases.
Include near-miss false-trigger cases (queries that seem related but should NOT trigger).
Write evals to `workspace/evals.json` with `should_trigger` boolean for each query.
Initialize the optimization workspace:
  `python <scripts-dir>/run_loop.py init <skill-path> <evals-path> --workspace <workspace>`
notify_user type=progress title="Phase Optimize – Description optimization"
For each iteration (max 5):
  Set current_iteration from `optimization_history.json`.
  For each eval in `train_evals.json`:
    Create 3 adhoc tasks (majority vote for reliability):
      `scheduler:create_adhoc_task`
        name: `opt-eval-<id>-vote-<n>`
        system_prompt: "You are a skill trigger evaluator. Given a skill description and a query, decide if the skill should be loaded."
        dedicated_context: true
        message: "Given this skill description: <current_description>. Would you load this skill for this query: <query>? Answer only YES or NO."
    Record majority vote (2+ YES = triggered).
  For each eval in `test_evals.json`:
    Same process — 3 tasks per query.
  Build a results JSON array with: query, should_trigger, triggered (majority vote), run_details.
  Pipe results: `echo '<results_json>' | python <scripts-dir>/run_loop.py record-results <workspace>`
  Print status: `python <scripts-dir>/run_loop.py iteration-status <workspace>`
  If training score < 100%:
    Generate context: `python <scripts-dir>/improve_description.py <workspace>`
    Read `improve_context.json` from the workspace.
    Create adhoc task: `scheduler:create_adhoc_task`
      name: `improve-description-iter-<N>`
      system_prompt: "You are a skill description writer. Generate improved descriptions for Agent Zero skills."
      dedicated_context: true
      message: "Improve this skill description based on the context. Constraints: imperative phrasing ('Use this skill for...'), intent-focused, under 1024 characters. Context: <improve_context.json contents>"
    Wait for improvement task.
    Read the new description from the task output.
  If training score = 100%: break and move to select-best.
Select the best description: `python <scripts-dir>/run_loop.py select-best <workspace>`
Generate the final report: `python <scripts-dir>/run_loop.py report <workspace>`
notify_user type=success title="Phase Optimize Complete"
Present the `optimization_report.md` to the user.
Ask the user: "Apply this optimized description?"
If the user confirms, update the SKILL.md frontmatter `description` field.
Run: `python <scripts-dir>/quick_validate.py <skill-path>`

---

## Package and Present

Run: `python <scripts-dir>/quick_validate.py <skill-path>`
Fix any validation errors.
Run: `python <scripts-dir>/package_skill.py <skill-path> [output-dir]`
Report the .zip file path to the user.

---

## Workflow Summary

The core loop:
1. Figure out what the skill is about and where the user is in the process.
2. Draft or edit the skill.
3. Create scheduler tasks for test prompts (with-skill and without-skill).
4. Create scheduler tasks for grading outputs.
5. Evaluate with the user — iterate if needed.
6. Optionally optimize the description via scheduler-based trigger evaluation.
7. Package and deliver.
Be flexible. If the user says "I don't need to run evaluations, just vibe with me", do that instead.

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This skill is too simple to test" | Simple skills still have trigger conditions and output expectations. Test the triggers. |
| "I'll just improve the description myself" | LLM-based optimization explores descriptions you wouldn't think of. Let the loop run. |
| "One test run is enough" | LLM outputs vary. Benchmark with 3+ runs for statistical significance. |
| "The skill works for me" | You are not the target agent. Test with fresh dedicated contexts. |
| "I don't need evals, just vibe with me" | Fine — skip evaluations. But don't skip validation (quick_validate.py). |

## Red Flags

- Writing a SKILL.md over 500 lines (move detail to references/)
- Skipping quick_validate.py after edits
- Running benchmarks with only 1 run per configuration
- Not using dedicated_context: true for scheduler tasks
- Auto-retrying failed scheduler tasks without user approval
- Creating skills without trigger phrases in the description

## Verification

After completing any skill lifecycle phase:

- [ ] SKILL.md passes `quick_validate.py`
- [ ] SKILL.md is under 500 lines
- [ ] Frontmatter has name and description fields
- [ ] Description includes trigger phrases
- [ ] All scheduler tasks completed successfully
- [ ] Evaluation results are saved to the workspace
- [ ] User has reviewed and approved the results

## Boundaries

- Always: Run `quick_validate.py` after any SKILL.md edit
- Always: Use `dedicated_context: true` for all scheduler tasks
- Always: Present failures to the user for decision (retry, skip, abort)
- Always: Keep SKILL.md under 500 lines (move detail to references/)
- Never: Auto-retry failed scheduler tasks without user approval
- Never: Skip validation when packaging a skill
- Never: Run benchmarks with only 1 run per configuration
- Never: Create skills without trigger phrases in the description
- Ask first: Before skipping evaluations (user may want data)
- Ask first: Before applying optimized descriptions to production skills

