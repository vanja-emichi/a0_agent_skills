 # Revolve Protocol

Revolve is an instruction-only protocol for reproducible self-improvement.

Use for improve/optimize/evolve/research/benchmark/tune/self-improve requests. For one-offs, answer normally. For iterative work, create or resume `revolve/`.

## Source Principles

This protocol is self-contained. Preserve reproducible research principles over runtime history.

## Architecture-First Research Gate

For runtime-integration projects, especially `a0_agent_skills`, architecture research is a blocking gate before candidate generation, harness edits, content expansion, or live promotion.

Before changing the subject, the main agent must produce or update a compact architecture brief in the active revision that answers these questions from authoritative sources:

1. What is the host runtime architecture?
2. What owns orchestration: main agent, subordinate profiles, skills, commands, plugins, hooks, or APIs?
3. How are prompts inherited, overridden, injected, and persisted?
4. How do projects affect context, metadata, files, skills, agents, settings, and instructions?
5. How are tools, skills, plugins, agents, commands, API handlers, and lifecycle extensions discovered and executed?
6. Which checks can be deterministic runtime/API tests, and which truly require live LLM e2e?
7. Which upstream concepts are portable, and which are platform-specific and must be adapted rather than copied?
8. What would prove correct integration in the host runtime, not merely high documentation coverage?

### Required Source Order

For Agent Zero integration research, read sources in this order before implementation:

1. Project DOX: active project `AGENTS.md`, `revolve/AGENTS.md`, project index, active revision, and the narrow target child docs.
2. Agent Zero DOX: `/a0/AGENTS.md`, then relevant child DOX for `agents/`, `prompts/`, `tools/`, `helpers/`, `api/`, `extensions/`, `plugins/`, `plugins/_skills/`, `plugins/_a0_connector/`, and `skills/`.
3. Runtime source only after DOX: code paths for prompt rendering, project loading, plugin discovery, skills loading/injection, command routing, API handlers, scheduler/chat persistence, and extension hooks.
4. External source context: use `deep_wiki` or equivalent repository analysis for `agent0ai/agent-zero` and `addyosmani/agent-skills`; record what came from upstream, what came from local DOX, and what was verified locally.
5. Live runtime evidence: inspect installed plugin state, active project metadata, available API endpoints, tool schemas, loaded skills, profile inventory, and test harness behavior.

Do not treat upstream docs, local DOX, or source code alone as sufficient when they disagree. Classify disagreements as architecture questions and resolve them with local runtime evidence or an explicit documented assumption.

### Agent Zero Native Integration Contract

For `a0_agent_skills`, the default architecture assumption is:

- `agent0` remains the user-facing orchestrator.
- Skills are repeatable workflows loaded through the native skills system, not a replacement orchestrator.
- Specialist profiles are subordinates with bounded roles; they do not own parent project state, live promotion, or revision control.
- Plugin behavior belongs in native plugin surfaces: `plugin.yaml`, `default_config.yaml`, `skills/`, `agents/<profile>/agent.yaml`, `commands/`, `api/`, `tools/`, `prompts/`, `extensions/`, `hooks.py`, and `webui/` as appropriate.
- Prompt/profile behavior belongs in prompts when always-on or profile-defining; skills should contain task workflows; commands should route user intent; extensions should implement runtime lifecycle effects.
- Project `AGENTS.md` injection and child DOX traversal must match Agent Zero reality. Do not assume recursive child `AGENTS.md` injection unless verified; teach traversal as workflow behavior when it is agent responsibility rather than runtime behavior.

If a candidate introduces a separate main orchestrator, changes agent0 responsibilities, bypasses the native `_skills`/`skills_tool` model, or depends on undocumented prompt inheritance, it must be treated as an architecture decision and evaluated in a new revision before promotion.

### Runtime-First Harness Contract

Prefer deterministic proof before live LLM e2e:

1. Static contract checks: manifests, paths, tool names, prompt filenames, command/profile/skill inventory, JSON/YAML validity, and referenced files.
2. Framework-runtime tests with `/opt/venv-a0/bin/python`: prompt resolution, plugin discovery, project metadata loading, extension import/ordering, API handler contracts, skills catalog, and hook behavior.
3. Execution-runtime tests with `/opt/venv/bin/python`: plugin structural tests, scripts, and repository-local pytest suites when they are designed for the execution environment.
4. HTTP/API tests: deterministic endpoints for commands, skills catalog, projects, plugins, scheduler state, and logs when available.
5. Thin live e2e: only for behavior that requires real agent sessions, LLM turns, subordinate creation, persisted `chat.json`, or cross-turn behavioral evidence.

A harness that rewards keyword presence, content length, or scanner coverage without runtime/API proof is not sufficient for architecture claims.

### Agent-Skills Porting Contract

When adapting `addyosmani/agent-skills`, preserve portable concepts and adapt platform-specific ones:

- Preserve: skill workflows, verification gates, anti-rationalization checks, specialist personas, orchestration patterns, and spec/plan/todo/build artifacts.
- Adapt: slash-command file formats, hook mechanisms, plugin packaging, MCP assumptions, persona invocation, and runtime-specific skill discovery.
- Explicitly decide whether source personas/commands are ported, merged into existing A0 skills, or intentionally omitted with rationale.
- Prove the lifecycle with artifacts: spec creation, plan breakdown, todo tracking, implementation slices, verification evidence, and documentation updates in an Agent Zero project.

### Lean Workspace Policy

Revolve must remain navigable. Full subject copies are allowed only when they are the cheapest reliable restore method. Before creating another full plugin copy, consider a leaner checkpoint strategy:

- manifest plus content hashes,
- patch/diff from parent checkpoint,
- Git worktree/commit/tag when available,
- tarball or compressed archive for rollback backups,
- selective copy of changed files plus restore recipe,
- run logs outside subject copies.

Do not store repeated live-overlay backups, pytest caches, or copied test trees as durable research state unless they are required for rollback or reproducibility. If a revision grows large, create an archive/compaction plan and keep parent indexes short enough to resume without rereading raw history.

## Research Progress

- Reliability gates are necessary, not sufficient. Passing reliability gates makes a candidate eligible; Do not stop at a merely passing candidate unless the objective, user, or budget says so.
- Research Momentum: a green run is evidence, not a stop condition. Continue from the strongest unresolved opportunity until a meaningful result exists: validated improvement, documented dead end, revised objective/evaluation proposal, or explicit stop; avoid cosmetic churn.
- Iteration must follow evidence: each continuation names an observed failure, opportunity, tradeoff, or uncertainty; the next checkpoint hypothesis; and measurable expected effect.
- Quality Search Batch: for quality objectives, compare an organization branch, navigation branch, and research-momentum branch; choose the next branch from evidence.
- Research Scope: tune a local research copy under `revolve/`; external promotion is optional, not the default goal, and live codebase changes require user intent.
- Internal Incumbent Discipline: track the current best checkpoint, promote internally when evidence passes, base new work on the best comparable checkpoint, do not reset to the original baseline after promotion, and keep external promotion separate.
- External Promotion Boundary: internal promotion is the research default; external promotion is a separate live-file decision; live artifacts remain unchanged unless explicitly promoted.
- Branch Portfolio: keep a leaderboard and Promising Branch Queue; rank by evidence, record selection reason, revisit older promising branches when newer branches stagnate, revisit when active line stalls, and do not flatten research into one round.
- Checkpoint Depth Loop: create the next checkpoint on the same branch, fork from an earlier checkpoint, or repeat or refine before accepting a shallow pass.
- Navigation Quality: parent indexes expose the resume-critical decision, what to open next, why branches stopped, and enough detail to avoid rereading raw history.

## Core Rules

- Evaluation first: define or connect the evaluation environment before changing the subject.
- Checkpoint first: preserve the incumbent subject before candidate work.
- Local research first: tune checkpointed subject copies under `revolve/`; live artifacts stay read-only unless external promotion is explicit.
- Same revision, same comparison: directly compare scores only inside one revision.
- New evaluation, new revision: create/select a new revision when cases, scoring, harness, evaluator rubric, subject definition, objective interpretation, or acceptance gates change.
- Parent docs route; child docs explain.
- Parent indexes expose resume-critical state: active child, current best, tried branch statuses, blocker, and next action; child docs keep detail.
- Documentation gates are blocking: do not advance until required local and parent `AGENTS.md` updates for the current state are complete.
- Do not keep one giant research diary. Store durable state in local `AGENTS.md` files.
- Do not silently mutate an evaluated checkpoint. Any meaningful subject change creates a new checkpoint.
- Do not leave evaluated checkpoints or branches marked `pending` or `active` unless awaiting a run or documented next action.
- Do not overfit. The main agent must not use benchmark memorization, evaluation-set leakage, exact-answer lookup, or test-case-specific hacks to raise a score.
- Promote only with acceptance evidence, or explicit user choice with documented tradeoffs and rollback.
- Treat subject failures, harness failures, infrastructure failures, and dataset gaps as different things.
- If sub-agents are available, the main agent owns synchronization, parent docs, revisions, incumbent changes, promotion, and live-file edits.
- Sub-agents document inside assigned output folders and do not mutate shared parent state.
- Ask blocking questions only; proceed with documented assumptions.

## Terms

- Main agent: user-facing owner of intent, projects, revisions, integration, parent docs, promotion, live changes.
- Sub-agent: bounded worker; explores, evaluates, analyzes, or proposes, then reports without shared-state changes.
- Subject: improved prompt, code, config, workflow, policy, dataset, model, evaluator, or artifact.
- Evaluation environment: harness, cases, fixtures, scoring, acceptance gates, result schema, and run procedure.
- Harness: subject evaluator: code, commands, tests, benchmark, LLM review, human review, or hybrid.
- Case: reproducible scenario with input, expected behavior or metric, and pass/fail criteria.
- Checkpoint: recoverable state with parent, rationale, results, status, and restore method.
- Branch: line of checkpoints pursuing one search hypothesis.
- Revision: versioned evaluation context; scores are comparable only within the same revision.
- Parallel batch: revision-level unit that freezes context and assigns isolated work packets.
- Incumbent: accepted checkpoint for a revision.
- Candidate: proposed improvement checkpoint.
- Runtime stop directive: current user stop rule; not permanent unless made stable.

## Default Structure

Default structure:

```text
revolve/
  AGENTS.md
  projects/
    <project-id>/
      AGENTS.md
      revisions/
        <revision-id>/
          AGENTS.md
          subject/
          eval/
            AGENTS.md
          branches/
            <branch-id>/
              AGENTS.md
          checkpoints/
            <checkpoint-id>/
              AGENTS.md
          runs/
            AGENTS.md
          parallel/
            AGENTS.md
          promotion/
            AGENTS.md
```

Durable subtrees have local `AGENTS.md` with purpose, artifacts, rules, status, child index, next action. Raw logs use nearest local `AGENTS.md`.

## Documentation Hierarchy

### Documentation Organization

Keep a top-down map: parent summaries answer where and why; child docs answer what changed. Open the narrowest file for the current decision.

### Path-First Documentation Titles

Use path-shaped headings: every documented file or durable `AGENTS.md` uses its literal path, with placeholders `<project-id>`, `<revision-id>`, `<branch-id>`, `<checkpoint-id>`; put role label after the path. Do not mix role-only headings; same path may appear more than once.

### Parent Index Snapshots

Every parent `AGENTS.md` should include a compact resume snapshot: active child, current best/latest result, blocker, next action, and child index. Child rows stay short: id, status, result, blocker/stop reason, next action or `none`, and detail path.

### Resume Drill

When resuming, read the root-to-active path first: `revolve/AGENTS.md`, `revolve/projects/<project-id>/AGENTS.md`, `revolve/projects/<project-id>/revisions/<revision-id>/AGENTS.md`, then branch/run/promotion indexes named by `Next Action`. Open only selected child detail.

### `AGENTS.md`

Defines the protocol. Do not store runtime research history here.

### `revolve/AGENTS.md`

Workspace index. Records purpose, projects, active project, archives, descriptions, resume path. Update after project creation, archive, rename, active-project change.

### `revolve/projects/<project-id>/AGENTS.md`

One long-lived improvement goal. Records objective, subject, live artifact, constraints, revision index, active revision, archives, cross-revision lessons. Update after revision changes, external promotion, conclusion.

### `revolve/projects/<project-id>/AGENTS.md`: Project Branch Memory

The project index keeps compact cross-revision branch ledger and Candidate Lineage: branch id, revision, hypothesis, candidate checkpoints, best result, not promotable/regression reason, status, stop reason, detail path.

### `revolve/projects/<project-id>/revisions/<revision-id>/AGENTS.md`

Main control file. Records reason, parent, subject, incumbent, evaluation, scoring, active/inactive branches, promising-branch queue with selection reason, current best, blocker, stop directive, and next action. The branch index shows id, status, hypothesis, best result, blocker/stop reason, next action, and detail path. Update after harness, cases, scoring, incumbent, branches, parallel, stop, current best, blocker, next-action changes.

### `revolve/projects/<project-id>/revisions/<revision-id>/eval/AGENTS.md`

Evaluation contract. Records harness purpose, run command/procedure, case/fixture format, scoring, acceptance gates, evaluator limits, case additions, failure classes. Evaluation mechanics changes require a new revision.

### `revolve/projects/<project-id>/revisions/<revision-id>/branches/<branch-id>/AGENTS.md`

One search line. Records branch id, starting checkpoint, hypothesis, strategy, candidate checkpoints, best result, status, continuation/termination/promotion reason, and reusable insights. Statuses: `active`, `promising`, `plateaued`, `dead`, `archived`, `superseded`, `promoted`.

### `revolve/projects/<project-id>/revisions/<revision-id>/checkpoints/<checkpoint-id>/AGENTS.md`

One subject state. It records checkpoint id, parent, branch, storage, subject reference, restore method, identity verification, changes, rationale, benefit/risk, results, promotion status, and rollback note.

### `revolve/projects/<project-id>/revisions/<revision-id>/runs/AGENTS.md`

Run index. It records run ids, checkpoint, revision, suite, score, validity, raw result, infrastructure failures, and comparison notes. The main agent updates it after every official or imported run.

### `revolve/projects/<project-id>/revisions/<revision-id>/parallel/AGENTS.md`

Parallel work index. It records batches, frozen context, work packets, write/output locations, integration, stale/invalid outputs, and imports. Sub-agents update assigned docs; the main agent updates parent indexes.

### `revolve/projects/<project-id>/revisions/<revision-id>/promotion/AGENTS.md`

Promotion records. It records promoted checkpoint, previous incumbent, evidence, affected files, verification, and rollback path.

### `PROGRESS.md`: Progress Compaction

`PROGRESS.md` is optional, short, user-facing, and compact. Keep recent status under `Current Best`, `Recent Progress`, and `Next`; point to authoritative `AGENTS.md`; it is not the durable source of truth.

## Documentation Gates

Documentation is part of the algorithm. Treat each update as a state-transition gate.

These gates govern official main-agent transitions. Sub-agents apply them only inside assigned folders: record local evidence, request imports, and leave parent index sync to the main agent.

### Blocking Rules

The main agent must not evaluate, generate candidates, switch revisions, promote, pause, stop, or summarize until evidence is synchronized.

Required invariants:

- Every durable folder has a local `AGENTS.md` before work continues inside it. Durable means it owns rules, status, decisions, candidate identity, run records, promotion evidence, or resume state.
- Every official checkpoint has a checkpoint `AGENTS.md` before it is evaluated.
- Every official run has a raw result record and an entry in `runs/AGENTS.md`.
- Every evaluated checkpoint has its score, validity, and decision recorded in its checkpoint `AGENTS.md`.
- Every branch containing an evaluated checkpoint has a status, best result, and continuation or termination reason in its branch `AGENTS.md`.
- Every child status change is reflected in its parent index before moving on.
- Every revision `AGENTS.md` records current best, active branches, stale/dead/plateaued branches, blocker if any, stop directive, and next action.
- No branch may remain `active` merely because it exists. It is `active` only when more work is planned and named.
- No checkpoint may remain `pending` or `Pending` after an official run exists for it. Mark it `promoted`, `promising`, `rejected`, `plateaued`, `tied`, `invalid`, `stale`, or `needs repeat`.
- If a run is invalid or not comparable, record why and exclude it from the leaderboard.
- If a revision is superseded, close or summarize active branches before switching the project active revision, unless a branch is carried forward and rerun.

### Required Update Order

After creating a child in the official hierarchy:

1. Create the child folder and local `AGENTS.md`.
2. Update the parent index to list the child.
3. Update the revision next action if the child affects current work.

For sub-agent-local children, update assigned docs; the main agent handles parent indexes during integration.

After creating a checkpoint:

1. Write or store the subject state.
2. Create checkpoint `AGENTS.md` with parent, branch, storage, restore method, changes, rationale, expected benefit/risk, and status `pending evaluation`.
3. Update the branch candidate list.
4. Update the revision active branch/checkpoint summary.

After running or importing an evaluation:

1. Save the raw run output.
2. Add or update the entry in `runs/AGENTS.md`.
3. Update the checkpoint `AGENTS.md` with score, validity, failed/regressed case summary, infrastructure notes, and decision.
4. Update the branch `AGENTS.md` with candidate history, best result, current status, and reason to continue or stop.
5. Update revision `AGENTS.md` with current best, leaderboard summary, blocker if any, and next action.
6. Only then continue to another candidate, repeat run, promotion, revision change, stop, or final response.

After analyzing a candidate batch:

1. Assign every evaluated candidate a decision: `promote`, `promising`, `continue`, `repeat`, `reject`, `invalid`, `stale`, `plateaued`, or `dead`.
2. Update every affected checkpoint and branch file.
3. Compact the batch outcome in the revision `AGENTS.md`.
4. Mark branches without a planned next action as `plateaued`, `dead`, `superseded`, or `archived`.
5. Record the next selected action before proceeding.

After changing evaluation context:

1. Stop and classify the change: cases, scoring, harness behavior, evaluator rubric, subject definition, objective interpretation, or acceptance gate.
2. Create or select a new revision before comparing further scores.
3. Update project, revision, and eval docs with the reason for the new context.
4. Carry forward only relevant lessons.
5. Rerun the incumbent under the new revision before new candidate comparison.

After promotion:

1. Verify the promoted checkpoint identity.
2. Preserve rollback for the previous incumbent/live artifact.
3. Apply the artifact if promotion is external.
4. Run required post-promotion verification.
5. Update promotion, previous checkpoint, promoted checkpoint, branch, revision, project, and rollback records.

Before stopping, pausing, or responding as complete:

1. Audit every run produced in the turn: it must appear in `runs/AGENTS.md`.
2. Audit every evaluated checkpoint: it must include result and decision.
3. Audit every branch touched in the turn: it must include current status and continuation/termination reason.
4. Audit the revision: current best, active branches, blockers, stop directive, and next action must be current.
5. If switching revisions or ending a search round, inactive branches must be compacted in the parent summary.

Sub-agents audit assigned folders and report needed parent updates; they do not update parent indexes.

Parent files summarize and route. Child files preserve local detail. Do not copy raw logs into parent files.

Sub-agent rules:

- Read the work packet and root-to-revision context.
- Write only inside the assigned output folder.
- Create local documentation for local work.
- Report through the assigned output contract.
- Do not update parent indexes.
- Do not modify the active revision, active harness, active case suite, live subject, incumbent pointer, scoring rules, or promotion records.
- Do not promote.
- Treat official documentation gates as reporting requirements: preserve evidence and import requests; leave shared-state sync to the main agent.

## Operational State Machine

Always know the current state and next state.

### State 0: Clarify

Goal: know subject and success criteria.

Identify subject, incumbent/live artifact, objective, target, regressions, constraints, permissions, budget, tools/tests/data, live scope, stop directive, and sub-agent availability.

If the task is materially new, create a new project. If only evaluation context changed, create a new revision.

Documentation gate: record objective, assumptions, constraints, questions, stop directive, and parallel availability once docs exist.

Next: initialize or resume.

### State 1: Initialize Or Resume

Goal: enter documented state.

Do:

- create `revolve/AGENTS.md` if missing
- read existing Revolve docs if present
- create or select project
- mark active project
- create project `AGENTS.md` if needed

Documentation gate: `revolve/AGENTS.md` lists active project and resume path; project `AGENTS.md` records objective, subject, constraints, and active revision.

Next: create or select revision.

### State 2: Create Or Select Revision

Goal: define comparable evaluation context.

The revision defines subject, incumbent, evaluation, suite identity, scoring, acceptance, result schema, active branches, stop directive, promotion rules, and parallel policy.

Create a new revision when evaluation comparability changes.

Documentation gate: project `AGENTS.md` lists active revision; revision `AGENTS.md` records reason, parent, subject, evaluation summary, acceptance, stop directive, and next action.

Next: build evaluation environment.

### State 3: Build Evaluation Environment

Goal: make success measurable before changes.

Do: reuse fit tests or benchmarks; write or connect a harness; define case/fixture formats, scoring, gates, result schema, infrastructure failures, and run/review procedure.

If the harness cannot run, fix it before optimizing.

Documentation gate: `eval/AGENTS.md` records harness purpose, run procedure, case/fixture format, scoring, schema, gates, evaluator limits, and failure classes; revision points there.

Next: create or import cases.

### State 4: Create Or Import Cases

Goal: build a versioned case suite.

Cases cover expected behavior, known failures, strengths, regression risks, edge cases, and user requirements.

Each case records id, description, category, severity, fixture/input, evaluator, expected behavior/metric, pass/fail criteria, optional weight, and repeats.

If cases change comparability, create/select a new revision and rerun the incumbent.

Documentation gate: eval docs identify suite/categories; revision docs record suite identity and comparability changes. If comparability changed, create the new revision before continuing.

Next: checkpoint incumbent.

### State 5: Checkpoint Incumbent

Goal: preserve rollback and baseline.

Create a checkpoint manifest. Choose cheap reproducible storage: full copy, Git commit/branch/worktree/tag, patch, content-addressed storage, immutable pointer with hash, registry pointer, generation recipe, or hybrid.

Record restore method and identity verification. If a checkpoint cannot be restored reliably, label it non-reproducible and not strongly promotable unless the user accepts risk.

Documentation gate: incumbent checkpoint `AGENTS.md` records storage, restore, identity verification, parent/source, rationale, and status; revision names it.

Next: run baseline.

### State 6: Run Baseline

Goal: measure the incumbent.

Record run id, project/revision/checkpoint id, harness/suite identity, score, failures, regressions, raw output, infrastructure errors, evaluator notes, blocker, and next action.

If baseline is invalid because of harness or infrastructure failure, fix that before candidate generation.

Documentation gate: raw run is saved; `runs/AGENTS.md`, incumbent checkpoint `AGENTS.md`, and revision `AGENTS.md` record baseline score, validity, failures, infrastructure notes, current blocker, and next action.

Next: choose sequential or parallel search.

### State 7: Choose Sequential Or Parallel Search

Goal: choose search mode after baseline.

Sequential search is default.

Use parallel search only when sub-agents are supported, evaluation is stable, baseline exists, work isolates, each sub-agent has a separate folder, and budget allows.

If parallel:

- create `parallel/AGENTS.md` if missing
- create a parallel batch under the active revision
- freeze revision context, base checkpoint, incumbent, evaluation, suite, scoring policy, and stop directive
- create work packets with read paths, write path, forbidden actions, expected output, completion criteria, and report format
- record the batch in revision and parallel docs

Do not use parallel search before baseline exists.

Documentation gate: revision records sequential or parallel mode. If parallel, `parallel/AGENTS.md` and batch/work-packet docs record frozen context, permissions, outputs, and integration policy before sub-agents start.

Next: generate candidate checkpoints or assign work packets.

### State 8: Generate Candidate Checkpoints

Goal: create a comparable search batch.

Default batch:

- `A`: conservative, low-risk change close to incumbent
- `B`: moderate structural or conceptual change
- `C`: exploratory redesign or alternate hypothesis

Use a different search strategy only when the task calls for it; document why.

In sequential mode, the main agent creates candidates. In parallel mode, sub-agents create local outputs; the main agent imports valid candidates.

For each official candidate, create a checkpoint and record parent, branch/hypothesis, rationale, expected benefit/risk, storage, and restore.

Documentation gate: every official candidate branch and checkpoint has a local `AGENTS.md`; branch index and revision active-branch summary are updated before evaluation.

Next: evaluate candidates.

### State 9: Evaluate Candidates

Goal: compare candidates under the baseline revision.

Do:

- run the same case suite and scoring policy
- save raw outputs
- classify failures
- record regressions
- record infrastructure failures separately
- repeat stochastic, borderline, or promising cases when needed
- update run, checkpoint, branch, and revision docs before the next evaluation

In parallel mode, sub-agents may evaluate candidates, shards, repeats, or failure clusters. Outputs stay local until import.

Documentation gate: after each official run, save raw output and update run, checkpoint, branch, and revision docs with score, validity, failure class, decision, current best, and next action before another candidate.

Next: analyze.

### State 10: Analyze And Decide

Goal: choose next state.

Classify each issue:

- Subject failure: candidate behavior failed.
- Harness failure: evaluator, fixture, or run procedure is wrong.
- Infrastructure failure: result validity is questionable.
- Dataset gap: current cases miss important behavior.
- Objective change: the project goal changed.

Then choose one: internally promote, continue a promising branch, revisit an older promising checkpoint, create/revise evaluation, repair harness/cases, stop, or pause.

In parallel mode, classify each sub-agent output as valid, invalid, incomplete, stale, duplicate, analysis-only, importable checkpoint/run, branch seed, or revision-change proposal. Mark stale if revision, incumbent, or evaluation changed. Do not merge stale scores unless rerun under the active revision.

Do not continue plateaued branches with trivial mutations. When the active branch stagnates, select the strongest unresolved promising branch, including older branches or earlier checkpoints; document why skipped branches are no longer worth continuing.

Documentation gate: every evaluated candidate has a decision; every touched branch has status and continuation/termination reason; revision records current best, summary, blocker, and next state.

Next: promote, revise, generate candidates, or stop.

### State 11: Promote Or Roll Back

Goal: controlled transition.

Promote only if the active revision acceptance policy passes, or the user explicitly chooses the checkpoint with documented tradeoffs.

Promotion types:

- Internal promotion: default research transition; update the active incumbent inside `revolve/`.
- External promotion: optional live-file application; do it only by user request or task-specific decision.

Promotion record includes promoted checkpoint, previous incumbent, evidence summary, tradeoffs, affected files, verification, and rollback path.

Only the main agent may promote. Sub-agents may recommend promotion.

After promotion, update all affected docs.

Documentation gate: promotion, previous checkpoint, promoted checkpoint, branch, revision, project, and rollback records are updated before live-file change is complete or work continues.

Next: continue from the new incumbent or the next strongest unresolved branch.

### State 12: Stop, Pause, Or Continue

Stop only when the stable objective, user directive, budget/cycle limit, required solution, or declared stagnation limit says to stop; stagnation requires no unresolved promising branches or checkpoints.

Before stopping, update revision/project status, record next action, compact inactive branch summaries, and preserve rollback/resume path.

Documentation gate: perform closeout audit: runs indexed, evaluated checkpoints decided, touched branches statused, revision current best and next action recorded, inactive branches compacted, and resume pointers current.

## Revision And Comparability

A revision is a comparable evaluation context. Create a new revision when changing:

- case list or case content
- scoring rules
- acceptance gates
- harness semantics
- evaluator rubric
- subject definition
- objective interpretation
- result schema in a way that affects interpretation

When a new revision is created:

1. Explain why it exists.
2. Link parent revision if any.
3. Carry forward only relevant lessons.
4. Re-run the incumbent under the new revision.
5. Compare future candidates only under the new revision.

Old results are historical evidence, not leaderboard competitors unless rerun under the same revision.

Parallel outputs follow the same rule. If a sub-agent produced output under an older revision, older incumbent, or older evaluation environment, keep it as historical evidence or rerun it before comparing.

Before switching the active revision, close the previous revision's bookkeeping: update run index, checkpoint results, branch statuses, current best, supersession reason, and next resume action. Do not leave stale `active` branches behind unless they are explicitly carried forward to the new revision and marked stale until rerun.

## User Intervention Handling

Classify every user intervention before applying it.

### Temporary Steering

Action: stay in same revision; update branch/revision docs only if it affects future work.

### Stop Directive

Action: record as active runtime stop directive; do not make permanent unless user makes it part of the stable objective.

A user score target or stop directive does not permit overfit work, benchmark memorization, or evaluation-set leakage.

### Evaluation Change

Action: create/select a new revision or version evaluation; rerun incumbent; do not compare old scores as unchanged benchmark results.

### Objective Change

Action: create a new project or major revision; record relationship to prior work; copy only relevant lessons.

### Manual Selection

The user may prefer a non-top-scoring candidate.

Action: treat preference as evidence, not automatic benchmark proof. If promoted, mark as user-directed promotion and document tradeoffs and rollback.

## Optional Parallelization

Parallelization is optional. Revolve defines coordination rules; it does not implement orchestration.

Synchronization principle:

- Sub-agents work below the revision.
- The main agent consolidates at the revision.
- Parent docs, revision changes, incumbent changes, promotion, and live-file edits remain main-agent responsibilities.

### Parallel Batch

A parallel batch records batch id, project/revision id, base checkpoint, incumbent, frozen evaluation, suite/harness identity, scoring policy, stop directive, work packets, write locations, integration policy, and status.

During a batch, sub-agents do not change the frozen context. They may propose changes for a future revision.

### Work Packet

A work packet records id, objective, base checkpoint, target branch/local name, frozen revision, read paths, write path, forbidden actions, expected output, completion criteria, and reporting format.

The packet must be narrow enough to avoid sibling coordination.

### Sub-Agent Permissions

A sub-agent may read frozen revision context, inspect assigned checkpoint, create local candidate outputs inside its assigned folder, run permitted harness commands, evaluate assigned cases, analyze failures, propose branches/cases/harness changes, write local `AGENTS.md` files inside its output folder, and report back.

A sub-agent must not edit `revolve/AGENTS.md`, project or active revision `AGENTS.md`, official branch/checkpoint/run/parallel/promotion indexes, active harness, active case suite, scoring rules, incumbent pointer, live project files, another sub-agent folder, or promote.

### Sub-Agent Report

A sub-agent output package should include local `AGENTS.md`, work packet id, base checkpoint, candidate or analysis, changed artifacts/patch, restore instructions, run results, failures, regressions, assumptions, blockers, and recommendation.

The report is evidence for integration, not an official parent-doc update.

### Integration

The main agent may import candidate checkpoints into official checkpoints, branch summaries into official branches, valid runs into official runs, proposed cases into a new revision, proposed harness changes into a new revision, and reusable insights into project or revision summaries.

Parallel work should be divided by objective, not by competition. Assign distinct hypotheses, risk profiles, failure clusters, or evaluation shards.

Stop a parallel batch when all packets finish, enough packets finish to decide, a candidate satisfies the stop directive, budget is exhausted, the batch becomes stale, or the user stops it.

## Evaluation Guidance

Prefer deterministic scoring first. Add LLM or human review only where deterministic checks cannot capture quality.

A good evaluation environment includes success, known-failure, regression, and edge cases; must-pass gates; scoring; stochastic repeat policy; infrastructure-failure policy; raw results; and short summaries.

Do not weaken a case to make a candidate pass. If a case is wrong, fix it, create/select a new revision, and rerun the incumbent.

## Anti-Overfitting Policy

Revolve optimizes for reproducible improvement, not benchmark memorization. The main agent must not overfit or create candidates that depend on evaluation leakage.

Forbidden overfitting includes:

- exact-input lookup tables, answer-key lookup tables, answer tables, known answers, or case-id routing for active evaluation cases
- training, tuning, prompting, selecting, or optimizing candidates on evaluation labels, hidden answers, test case content, holdout answers, or fixture-specific output keys
- local-suite distribution hacks, benchmark-specific constants, or rules that only work because the active cases are known
- copying expected outputs into the subject, prompt, code, fine-tune data, retrieval corpus, cache, or post-processing layer

A user score target or stop directive does not permit overfit work. If a user asks for an overfit route, refuse it and offer honest alternatives: improve generally, add/reserve holdouts, create a broader revision, repair the harness, or change the objective.

Do not promote overfit checkpoints, internally or externally. If a checkpoint is later found to depend on evaluation leakage, mark it invalid, preserve it only as historical evidence, restore or select a non-overfit incumbent, and create a new revision if the evaluation context was contaminated.

## Result Records

Each run should preserve run id, project/revision/checkpoint id, branch or work-packet id if applicable, harness/suite identity, score, failures, regressions, raw output, infrastructure/evaluator notes, and decision or next action.

Task-specific fields are allowed: latency for code, rubric scores for prompts, review dimensions for visual work.

A run record is incomplete until the evaluated checkpoint and branch also name the run and record a decision. Do not rely on `runs/AGENTS.md` alone as the source of branch status.

## Branch Discipline

Branches prevent linear, fragile search.

Each branch needs starting checkpoint, hypothesis, strategy, candidate history, best result, status, and continuation/termination reason.

A branch becomes `plateaued` when it stops producing meaningful improvement. A branch becomes `dead` when its strategy failed or tradeoffs are unacceptable.

One-checkpoint branches are allowed, but they still need a lifecycle decision after evaluation:

- `promoted`: candidate became the incumbent.
- `promising`: candidate did not yet satisfy promotion but has a documented reason and next experiment.
- `plateaued`: candidate was close or tied but did not improve enough; no immediate continuation planned.
- `dead`: candidate underperformed, regressed unacceptable behavior, or invalidated the branch hypothesis.
- `superseded`: branch was made obsolete by a new incumbent, revision, or user direction.
- `active`: only for a branch with a named next checkpoint, repeat run, analysis task, or work packet.

After a candidate batch, status every touched branch. A branch with an evaluated checkpoint and no named next action must not remain `active`.

Do not delete dead branches. Compact the parent summary and preserve detail so future agents do not repeat failed research.

In parallel mode, sub-agents may create local branch proposals. They become official branches only when the main agent imports them.

## Promotion Discipline

Declare acceptance before candidate generation. Promotion is evidence-backed, non-overfit, rollback-recorded, and main-agent-only. Internal promotion updates the local incumbent; external promotion remains separate and requires live backup, verification, rollback instructions, and docs.

## Closeout Checklist

Before ending a Revolve work turn:

- state is clear
- next action is recorded
- changed child docs are updated
- parent indexes reflect child status
- runs are recorded or imported
- every run produced this turn is linked from the evaluated checkpoint
- every evaluated checkpoint has result, validity, and decision
- current best and blocker are documented
- branch statuses are current
- no branch is marked `active` without a named next action
- parallel batch statuses are current
- new revision was created if evaluation changed
- previous revision was closed or explicitly superseded if active revision changed
- rollback path exists for promoted work
- inactive branch summaries are compacted in parent indexes
