# Revolve: A Hierarchical AGENTS.md Protocol for Reproducible Agentic Self-Improvement

**Author:** Jan Tomášek
**Affiliation:** Founder and Development Lead, Agent Zero, s.r.o.; developer of Agent Zero, Space Agent, DOX, and related Agent0AI projects
**Status:** Concept paper and framework blueprint
**Date:** 2026-06-15

---

## Abstract

Revolve is a generic, instruction-only framework for making an existing AI coding agent perform reproducible research, optimization, and self-improvement inside any project. It is designed to be copied into an AGENTS.md file. The user then asks the main agent to improve a subject, research a better solution, optimize behavior, or evolve an artifact. Revolve does not ship a fixed runner, benchmark suite, CLI, library, LLM wrapper, or domain-specific harness. Instead, it gives the agent a strict operating protocol: clarify the goal, build the local evaluation environment, checkpoint the subject, run a baseline, generate candidate branches, evaluate them comparably, document the process hierarchically, and promote only validated improvements.

The motivation is captured by Andrej Karpathy’s MenuGen observation. After building an app that transformed restaurant menus into visual menus, he later described the app as old-paradigm machinery because a multimodal model could perform the task directly. His conclusion was that “that app shouldn’t exist.” Revolve applies the same principle to self-improvement frameworks. If a capable coding agent can inspect a repository, write the needed tests, create the needed scripts, define the needed rubrics, spawn sub-agents when available, and execute the needed comparisons, then the permanent product should not be a static harness. Static harnesses become obsolete when models, tools, modalities, and project requirements change. The permanent product should be the method that tells the agent how to create and govern the correct harness for the current task.

Revolve therefore moves responsibility from fixed framework code into the agent’s instructed workflow. Better coding agents, larger context windows, stronger multimodal models, better tool use, and improved reasoning do not obsolete Revolve; they make it more capable. Because research state is checkpointed and versioned, previous projects can be resumed later with newer models, better tools, stronger evaluators, or parallel agentic systems without losing historical evidence.

The core of Revolve is not automation for one benchmark. It is a disciplined research memory and evolution protocol. It combines evaluation-first improvement with DOX-style hierarchical documentation: every project, revision, branch, checkpoint, harness, run, and parallel work batch has its own local AGENTS.md file. Parent files summarize children; child files preserve local detail. This keeps long-running research navigable without forcing the agent to load the entire history. Revolve is therefore a portable standard operating procedure for safe, scalable, reproducible agentic improvement.

---

## 1. Problem

AI agents can now inspect repositories, write scripts, run tests, edit prompts, evaluate outputs, reason about failures, and sometimes spawn sub-agents for parallel work. Yet most self-improvement systems still package a fixed implementation: a runner, benchmark adapter, trace schema, evaluator, orchestration layer, or domain pipeline.

That approach works when the task matches the assumptions of the tool. It breaks down when the task changes.

A prompt-evaluation loop, a code-performance benchmark, a model-training experiment, and a visual-quality review do not need the same harness. A universal self-improvement framework should not pretend that one static runner can evaluate every domain.

The deeper problem is not lack of harness code. The deeper problem is lack of disciplined process.

Agents fail when they:

* optimize before defining success;
* change tests while comparing old scores;
* forget failed branches;
* promote unreproducible candidates;
* confuse harness failures with subject failures;
* collide while working in parallel;
* accumulate unbounded notes that later agents cannot use;
* lose the ability to revert to a previous state.

Revolve solves the process problem. It does not ship the harness. It instructs the agent how to build, version, execute, document, parallelize, consolidate, and evolve the correct harness for the current task.

---

## 2. Core Thesis

The durable component of generic self-improvement is not a static evaluation harness.

The durable component is a precise protocol for creating, versioning, executing, documenting, parallelizing, and evolving task-specific evaluation environments.

Revolve is strict about method and flexible about implementation.

It is strict about order:

1. Clarify the goal.
2. Define the subject.
3. Create or select the research workspace.
4. Create or select a project.
5. Create or select a revision.
6. Build the evaluation environment.
7. Create or import cases.
8. Checkpoint the incumbent.
9. Run the baseline.
10. Generate candidates.
11. Evaluate candidates under the same revision.
12. Promote, reject, branch, revise, parallelize, or stop.
13. Update the documentation hierarchy.

It is flexible about mechanics:

* the subject can be text, code, prompt, policy, workflow, configuration, or another artifact;
* the harness can be a script, command, test suite, LLM review, human review, or hybrid;
* the case format can be domain-specific;
* the scoring policy can be quantitative, qualitative, or mixed;
* the search strategy and stop condition can be set by the user at runtime;
* parallel execution can be used when the hosting agentic system supports sub-agents.

The invariant is not the tool. The invariant is the research discipline.

---

## 3. Basic Concepts

### 3.1 Main Agent

The main agent is the agent that communicates with the user.

It owns interpretation of user intent, creation of projects and revisions, synchronization of sub-agent outputs, updates to parent AGENTS.md files, promotion decisions, and live project changes.

When sub-agents are available, the main agent may delegate isolated work. It remains responsible for consolidation.

### 3.2 Sub-Agent

A sub-agent is a worker spawned by the main agent.

A sub-agent may explore a branch, create candidate checkpoints, run evaluation shards, analyze failures, or propose cases. It works inside a bounded work packet and reports back to the main agent.

A sub-agent must not update parent documentation, promote candidates, mutate the active evaluation environment, or edit live project files unless the main agent explicitly assigns that as an isolated local task with a separate output path.

### 3.3 Subject

The subject is the artifact being improved.

Examples:

* a system prompt;
* a code module;
* a research workflow;
* an evaluation or generation procedure.

The subject replaces the narrow term “dataset.” In Revolve, the thing being molded may be text, code, configuration, policy, workflow, model output procedure, or another artifact.

### 3.4 Evaluation Environment

The evaluation environment is everything used to judge the subject.

It includes:

* harness;
* cases;
* fixtures or inputs;
* scoring rules;
* acceptance gates;
* result schema;
* run procedure.

A result is meaningful only relative to the evaluation environment that produced it.

### 3.5 Harness

The harness is the procedure that runs evaluations.

It may be code, commands, existing tests, a benchmark, an LLM judging process, a manual review process, or a hybrid. Revolve does not prescribe the harness implementation. The agent creates or connects the harness that best fits the project.

### 3.6 Case

A case is one reproducible evaluation scenario.

A case states what is being tested, what input or fixture is used, how the subject is evaluated, and what counts as success or failure.

### 3.7 Checkpoint

A checkpoint is a recoverable snapshot of the subject at a specific point in the search.

Every meaningful subject change becomes a new checkpoint. A checkpoint has a parent, rationale, results, status, and restore method.

A checkpoint should be logically immutable. That means the represented subject state must not silently change after evaluation. It does not always mean the system must physically copy every byte.

### 3.8 Branch

A branch is a line of checkpoints pursuing a search strategy or hypothesis.

A branch can be active, promising, plateaued, dead, archived, superseded, or promoted.

### 3.9 Revision

A revision is a versioned evaluation context for one improvement project.

A new revision is created when the evaluation environment changes in a way that affects comparability. This includes changing the case suite, scoring policy, harness semantics, objective interpretation, or subject definition.

Scores from different revisions are historical evidence, not direct competitors, unless the same checkpoints are re-run under a shared revision.

### 3.10 Parallel Batch

A parallel batch is an optional revision-level synchronization unit created by the main agent.

It freezes the current revision context, base checkpoint, evaluation environment, case suite, scoring policy, and stop directive. The main agent then gives sub-agents isolated work packets. Sub-agents work independently and report back. The main agent integrates the results.

The highest safe synchronization point for parallel work is the active revision, because the revision defines comparability. Sub-agents may operate below the revision level, but consolidation happens at the revision level.

### 3.11 Incumbent

The incumbent is the currently accepted checkpoint. Candidates are evaluated against the incumbent unless the revision defines a different baseline.

### 3.12 Candidate

A candidate is a checkpoint proposed as an improvement. It is not accepted until it passes the revision’s acceptance policy or the user explicitly chooses it with documented tradeoffs.

### 3.13 Runtime Stop Directive

A runtime stop directive is the user’s current instruction for when the active loop should stop.

Examples:

* continue until accuracy reaches 99 percent;
* improve this script until it runs under one second;
* search for three viable alternatives;
* continue until no branch improves after five cycles;
* stop after this candidate batch.

The stop directive may be temporary. It should not be permanently hardcoded into the project unless it is part of the stable objective.

---

## 4. What Revolve Is and Is Not

Revolve is:

* an AGENTS.md protocol;
* a reproducible self-improvement method;
* a hierarchical research memory system;
* a checkpoint and branch discipline;
* a guide for agent-authored evaluation;
* an optional parallel work protocol;
* a generic framework for optimization and research.

Revolve is not:

* a Python package;
* a JavaScript package;
* a CLI;
* a benchmark suite;
* a fixed LLM wrapper;
* a multi-agent orchestration layer;
* a static research pipeline;
* a universal evaluator.

This distinction is central. Revolve does not compete by shipping more code. It competes by avoiding premature code. The agent writes or connects code only when the current task requires it. When parallel sub-agents are available, Revolve does not implement orchestration. It defines the rules that let the main agent delegate safely.

---

## 5. Runtime Structure

The default runtime folder is revolve/.

The recommended structure is:

* revolve/AGENTS.md

  * Indexes all Revolve projects.
  * Defines workspace rules.
  * Points to active projects.

* revolve/projects/<project-id>/AGENTS.md

  * Defines one improvement project.
  * Indexes revisions.
  * Stores durable lessons across revisions.

* revolve/projects/<project-id>/revisions/<revision-id>/AGENTS.md

  * Defines one evaluation context.
  * Names the subject, incumbent, harness, cases, scoring policy, active branches, result schema, current stop directive, and active parallel batches if applicable.

* subject/

  * Stores or references the subject artifact.
  * Contains checkpoints or checkpoint manifests.

* branches/

  * Stores branch summaries and search strategies.

* eval/

  * Stores harness documentation, cases, fixtures, scoring rules, and evaluator notes.

* runs/

  * Stores execution results and run summaries.

* parallel/

  * Stores optional parallel batches, work packets, sub-agent outputs, and integration records.

* promotion/

  * Stores promotion records and rollback instructions.

The exact file layout may vary by project. The invariant is that every important subtree has a local AGENTS.md file describing its purpose, rules, children, and current status.

---

## 6. Documentation Model

Revolve applies the DOX-style hierarchy to research and optimization.

The agent must not maintain one massive research diary. It must maintain a tree of local contracts and summaries.

Each AGENTS.md file has a defined responsibility.

### 6.1 Root Project AGENTS.md

The root AGENTS.md contains the Revolve protocol.

It should not accumulate runtime history. It explains how the agent should operate, but it does not store project-specific research logs.

### 6.2 revolve/AGENTS.md

The workspace AGENTS.md indexes all Revolve projects.

It should document:

* workspace purpose;
* folder conventions;
* list of projects;
* active project;
* archived projects;
* short project descriptions;
* where the agent should continue.

After creating, archiving, renaming, or changing the active status of a project, the main agent updates this file.

### 6.3 Project AGENTS.md

A project AGENTS.md defines one long-lived improvement goal.

It should document:

* project objective;
* subject category;
* live artifact location if applicable;
* constraints that apply across revisions;
* revision index;
* active revision;
* archived or superseded revisions;
* durable lessons learned across revisions.

After creating a new revision or changing the active revision, the main agent updates this file.

### 6.4 Revision AGENTS.md

A revision AGENTS.md is the main operational document for current work.

It should document:

* revision id;
* reason the revision exists;
* parent revision if any;
* subject definition;
* incumbent checkpoint;
* evaluation environment summary;
* harness location and run instructions;
* case suite identity;
* scoring policy;
* acceptance policy;
* result schema;
* active branches;
* active parallel batches if any;
* current best result;
* current blocker;
* current runtime stop directive if one is active;
* next intended action.

After changing the harness, cases, scoring, incumbent, branch status, result schema, active stop directive, or parallel batch status, the main agent updates this file.

### 6.5 Branch AGENTS.md

A branch AGENTS.md documents one line of search.

It should document:

* branch id;
* starting checkpoint;
* search hypothesis;
* strategy;
* candidate checkpoints;
* best result;
* current status;
* reason for continuation, termination, or promotion;
* reusable insights.

After evaluating a candidate or changing branch status, the main agent updates this file. A sub-agent may create a local branch report inside its assigned output folder, but the official branch AGENTS.md is updated by the main agent.

### 6.6 Checkpoint AGENTS.md

A checkpoint AGENTS.md documents one subject state.

It should document:

* checkpoint id;
* parent checkpoint;
* branch id;
* storage method;
* subject artifact location or reference;
* restore method;
* changes from parent;
* rationale;
* expected benefit;
* expected risk;
* evaluation results;
* promotion status;
* rollback note if promoted.

After creating or evaluating the checkpoint, the responsible worker writes local checkpoint documentation. The main agent imports or updates the official checkpoint documentation during integration.

The subject content itself should not be silently edited after evaluation. If the subject changes, a new checkpoint is created.

### 6.7 Eval AGENTS.md

The evaluation subtree documents how testing works.

It should document:

* harness purpose;
* run command or procedure;
* case format;
* fixture format;
* scoring rules;
* evaluator limitations;
* how to add new cases;
* how to distinguish subject failure, harness failure, and infrastructure failure.

After changing evaluation mechanics, the main agent updates this file and usually creates a new revision. Sub-agents may propose evaluation changes, but they do not apply them to the active revision.

### 6.8 Runs AGENTS.md

The runs subtree indexes evaluation records.

It should document:

* run ids;
* checkpoint evaluated;
* revision used;
* score summary;
* validity status;
* raw result location;
* infrastructure failures;
* comparison notes.

After every official run, the main agent creates or imports a run record and updates the runs index. A sub-agent may store local run records inside its assigned output folder.

### 6.9 Parallel AGENTS.md

The parallel subtree documents optional parallel work.

It should document:

* active and completed batches;
* frozen revision context for each batch;
* work packet index;
* assigned objectives;
* sub-agent output locations;
* integration status;
* stale or invalid outputs;
* imported candidates and runs.

Sub-agents may update only their assigned local output AGENTS.md files. The main agent updates the parallel parent indexes.

### 6.10 Promotion AGENTS.md

The promotion subtree stores accepted transitions.

It should document:

* promoted checkpoint;
* previous incumbent;
* evidence summary;
* affected live files if any;
* verification result;
* rollback path.

After promotion, the main agent updates the promotion record, revision AGENTS.md, branch AGENTS.md, checkpoint AGENTS.md, and project AGENTS.md if the active state changed.

---

## 7. Documentation Update Rules

Documentation is part of the algorithm, not an afterthought.

The main agent follows these rules:

1. Before working in a subtree, read every AGENTS.md from the root to that subtree.
2. After creating a child folder, create its local AGENTS.md.
3. After changing a child’s status, update the parent index.
4. After creating a checkpoint, update the branch and revision indexes.
5. After running or importing an evaluation, create a run record and update the checkpoint, branch, revision, and runs indexes.
6. After changing cases, scoring, or harness behavior, create or select a new revision and update the project index.
7. After receiving a runtime stop directive or steering instruction, record it in the active revision or branch only if it affects current work.
8. After creating a parallel batch, record the frozen context and work packet index.
9. After integrating sub-agent outputs, update the official branch, checkpoint, run, parallel, and revision indexes.
10. After promoting a candidate, update the promotion record and all affected parent summaries.
11. After archiving a branch, compact its parent summary but preserve local details.
12. Do not duplicate raw logs into parent files.
13. Parent files route; child files explain.

Sub-agents follow stricter rules:

1. Read the work packet and the root-to-revision context provided by the main agent.
2. Write only inside the assigned output folder.
3. Create local documentation for their own work.
4. Report results back to the main agent through the assigned output contract.
5. Do not update parent indexes.
6. Do not modify the active revision, active harness, active case suite, live subject, incumbent pointer, or promotion records.
7. Do not promote.

This keeps the system scalable. A dead branch may contain many runs, but the parent only needs a compact conclusion: what was tried, best result, why it stopped, and whether any insight should be reused.

---

## 8. Subject Checkpointing and Storage Strategy

Revolve requires recoverable checkpoints, not naive infinite copying.

For small subjects, the default strategy is full-copy checkpointing. The agent creates a new checkpoint folder and stores the complete subject state there.

This is appropriate for:

* prompts;
* configuration files;
* small scripts;
* workflow documents;
* compact datasets;
* small generated artifacts.

For large subjects, full-copy checkpointing may be wasteful or impossible. The agent should choose a storage strategy that preserves reproducibility without unnecessary duplication.

Valid strategies include:

* full copy for small artifacts;
* Git commit, branch, worktree, or tag for repository-backed subjects;
* patch or diff against the parent checkpoint;
* content-addressed storage with deduplication;
* manifest referencing external immutable artifacts;
* pointer to a model registry, dataset registry, or artifact store;
* generation recipe plus seed and dependency record when exact storage is not practical;
* hybrid strategy, such as copying metadata while storing large blobs externally.

Every checkpoint must include a manifest in its AGENTS.md or adjacent metadata.

The manifest should state:

* what storage strategy is used;
* where the subject state is stored;
* how to restore it;
* how to verify identity when practical;
* what parent it depends on;
* whether any external artifact is required;
* whether exact reproducibility is guaranteed or approximate.

The agent should avoid copying large artifacts repeatedly unless the user explicitly approves the storage cost. For multi-gigabyte subjects, the preferred strategy is usually Git-backed state, deltas, content-addressed references, or external artifact pointers with hashes.

The invariant is:

A checkpoint must be recoverable and auditable. It does not have to be a physical full copy.

If a checkpoint cannot be reliably restored, the agent must label it as non-reproducible and avoid treating it as a strong promotion candidate until the problem is fixed or accepted by the user.

---

## 9. Operational Flow

Revolve operates in a strict semantic order.

### 9.1 Clarify

The agent first clarifies the objective.

It identifies:

* what subject is being improved;
* what success means;
* what must not regress;
* what constraints apply;
* what tools, tests, or data already exist;
* whether final changes should stay inside Revolve or be applied to live project files;
* whether the user has provided a runtime stop directive;
* whether parallel sub-agents are available and useful.

The agent should ask only the questions needed to avoid blind optimization. If the task is clear enough to start safely, it may proceed with documented assumptions.

Documentation after this step:

* create or update the project AGENTS.md;
* record objective, assumptions, constraints, and open questions;
* record the current stop directive if one exists;
* record whether parallel execution is available or disabled;
* if the objective is materially new, create a new project.

### 9.2 Initialize or Resume

The agent enters the revolve/ folder.

If it does not exist, the agent creates it and writes revolve/AGENTS.md.

If it exists, the agent reads revolve/AGENTS.md and determines whether to continue an existing project or create a new one.

Documentation after this step:

* update revolve/AGENTS.md with the project index;
* mark the active project;
* create the project AGENTS.md if needed.

### 9.3 Create or Select a Revision

The agent creates or selects a revision for the current evaluation context.

A revision defines:

* subject definition;
* harness;
* case suite;
* scoring policy;
* acceptance policy;
* result schema;
* active incumbent;
* active branches;
* promotion rules;
* current runtime stop directive if applicable;
* parallel policy if sub-agents will be used.

Documentation after this step:

* create the revision AGENTS.md;
* update the project AGENTS.md revision index;
* record why the revision exists and whether it descends from another revision.

### 9.4 Build the Evaluation Environment

The agent builds or connects the harness before serious optimization begins.

This may mean reusing existing tests, writing a script, defining an LLM review rubric, building a benchmark command, or combining methods. The implementation is local to the task.

Documentation after this step:

* create or update eval/AGENTS.md;
* document how to run the harness;
* document case format and scoring rules;
* update the revision AGENTS.md with the evaluation summary.

### 9.5 Create the Initial Cases

The agent creates or imports cases.

Cases should cover:

* expected normal behavior;
* known failures;
* important regressions;
* relevant edge cases.

The first case suite does not need to be perfect. It needs to be explicit, runnable, and versioned.

Documentation after this step:

* document case suite identity in eval/AGENTS.md;
* document case categories and severity rules;
* update the revision AGENTS.md;
* if cases were added to an existing revision in a way that affects comparability, create a new revision.

### 9.6 Checkpoint the Incumbent

The current subject is saved as the incumbent checkpoint before optimization.

The agent chooses the checkpoint storage strategy based on subject size and project constraints.

Documentation after this step:

* create checkpoint folder or checkpoint manifest;
* create checkpoint AGENTS.md;
* record subject location, parent if any, storage method, restore method, and rationale;
* update the revision AGENTS.md with the incumbent checkpoint id.

### 9.7 Run the Baseline

The incumbent is evaluated before candidate generation.

The baseline establishes starting score, known failures, existing strengths, and comparison point.

If the baseline cannot run, the agent fixes the evaluation environment before improving the subject.

Documentation after this step:

* create a run record under runs/;
* update runs/AGENTS.md;
* update the incumbent checkpoint AGENTS.md;
* update the revision AGENTS.md with baseline score and current blocker.

### 9.8 Choose Sequential or Parallel Search

After the baseline exists, the main agent decides whether to proceed sequentially or spawn sub-agents.

Sequential search is the default.

Parallel search is appropriate when:

* the host environment supports sub-agents;
* the evaluation environment is defined and stable;
* independent branches or case shards can be assigned;
* the work can be isolated into non-overlapping output folders;
* the user’s budget allows parallel exploration.

Parallel search should not be used before the baseline exists. Without a baseline and stable revision, sub-agents would be exploring against an undefined target.

Documentation after this step:

* record selected search mode in the revision AGENTS.md;
* if parallel, create a parallel batch and work packet index.

### 9.9 Evolve Candidates

The agent generates a small batch of candidate checkpoints.

The default search strategy is A/B/C:

* A: conservative change, low risk, close to the incumbent;
* B: moderate change, structural improvement, medium risk;
* C: exploratory change, larger redesign or alternative hypothesis.

This is a default, not a hardcoded law. The agent may choose another search strategy when the task requires it, but it must document that strategy.

In sequential mode, the main agent creates candidates directly.

In parallel mode, the main agent assigns candidate-generation work packets to sub-agents. Each sub-agent creates local candidate outputs under its assigned folder. The main agent imports valid candidates into the official checkpoint tree during integration.

Documentation after this step:

* create or update branch AGENTS.md files;
* create checkpoint AGENTS.md files for official candidates;
* record the checkpoint storage strategy for each candidate;
* update the revision AGENTS.md active branch index;
* if parallel, update the parallel batch status.

### 9.10 Evaluate Candidates

Candidates are evaluated under the same revision as the incumbent.

For every run, the agent records:

* checkpoint id;
* revision id;
* case suite id;
* harness identity;
* score;
* failures;
* regressions;
* raw result location;
* infrastructure errors;
* judgment notes when applicable.

In parallel mode, sub-agents may evaluate different candidates, case shards, repeat runs, or failure clusters. Their outputs remain local until the main agent imports and validates them.

Documentation after this step:

* create one run record per evaluation batch or candidate, depending on the harness;
* update runs/AGENTS.md;
* update each checkpoint AGENTS.md;
* update each branch AGENTS.md;
* update the revision AGENTS.md with current best, regressions, and next action;
* if parallel, update the parallel integration record.

### 9.11 Analyze and Branch

The agent compares candidates against the incumbent using the declared scoring policy.

The agent may:

* promote a candidate;
* reject a candidate;
* refine a promising branch;
* archive a dead branch;
* create a new exploratory branch;
* create a new revision if evaluation must change;
* stop if the active stop directive is satisfied.

If progress stagnates, the agent should not continue minor variations indefinitely. It should mark the branch as plateaued or dead, summarize why, and branch from a more promising checkpoint or earlier state.

Documentation after this step:

* update branch statuses;
* compact dead branch summaries in the revision AGENTS.md;
* preserve detailed evidence in branch and run subtrees;
* update the revision next-action field;
* record whether the current stop directive is met, still active, or superseded.

### 9.12 Promote or Roll Back

A candidate is promoted only if it satisfies the revision’s acceptance policy or if the user explicitly chooses it with documented tradeoffs.

Internal promotion changes the active incumbent inside Revolve.

External promotion applies the artifact back to live project files.

Only the main agent may promote.

Documentation after this step:

* create a promotion record;
* update previous and new incumbent checkpoint files;
* update branch status;
* update revision incumbent pointer;
* update project summary if externally promoted;
* record rollback instructions.

### 9.13 Stop, Pause, or Continue

The agent considers the active loop complete when the active stop directive is satisfied, the stable objective is solved, the user asks to stop, or further progress is blocked by declared limits.

Stop conditions may include:

* target score reached;
* performance target reached;
* required solution found;
* all must-pass cases pass;
* maximum budget reached;
* maximum candidate cycles reached;
* no meaningful improvement after the declared stagnation limit;
* user chooses a checkpoint;
* user pauses or stops the run.

The stop condition is normally a runtime instruction, not a permanent property of the framework. It should be documented as the active stop directive for the current revision or branch, but it should not become part of the stable project objective unless the user clearly defines it as such.

For open-ended optimization, the agent should treat the stop directive as session-scoped. For bounded research, the agent may treat the found solution as project-level completion.

Documentation after this step:

* record completion, pause, or continuation status in the revision AGENTS.md;
* update the project AGENTS.md if the project reached a stable conclusion;
* preserve the next recommended action for future resumption.

---

## 10. Runtime Steering and User Intervention

The user may intervene at any time.

User intervention is not an exception to Revolve. It is part of the operating model.

The agent classifies each intervention before applying it.

### 10.1 Temporary Steering

Temporary steering changes the direction of the current search without changing the evaluation environment.

Examples:

* focus more on this branch;
* try a more aggressive redesign;
* explore this candidate further;
* I like this result, compare it more carefully.

Action:

* continue in the same revision;
* create or update a branch if needed;
* record the steering note in the branch or revision AGENTS.md only if it affects future work.

### 10.2 Stop Directive

A stop directive tells the agent when to stop the current loop.

Examples:

* continue until 99 percent accuracy;
* stop after three more candidate batches;
* optimize until runtime is below one second;
* stop once a usable solution is found.

Action:

* record it as the active runtime stop directive;
* do not treat it as permanent unless the user makes it part of the objective.

### 10.3 Evaluation Change

An evaluation change alters what counts as success.

Examples:

* add this new failure as a test;
* change the scoring weights;
* make this case must-pass;
* use a stricter judge.

Action:

* create a new revision or explicitly version the evaluation environment;
* re-run the incumbent under the new context;
* do not compare old scores as if the benchmark were unchanged.

### 10.4 Objective Change

An objective change alters what the project is trying to achieve.

Examples:

* stop optimizing speed and optimize quality instead;
* use this workflow for a different product;
* change the subject being improved.

Action:

* create a new project or major revision;
* record the relationship to the prior work;
* copy only relevant lessons and artifacts.

### 10.5 User Preference or Manual Selection

The user may prefer a candidate that is not the top metric winner.

Action:

* treat the preference as evidence, not as an automatic benchmark result;
* if the user chooses promotion, record it as user-directed promotion;
* document known tradeoffs;
* preserve rollback.

This lets the user steer research without breaking reproducibility.

---

## 11. Optional Parallelization

Revolve supports optional parallel execution when the hosting agentic environment provides sub-agents.

Parallelization is not implemented by Revolve. It is coordinated by the main agent using the host system’s native sub-agent mechanism.

The model is:

1. The user speaks to the main agent.
2. The main agent creates a parallel batch under the active revision.
3. The main agent assigns isolated work packets to sub-agents.
4. Sub-agents work independently inside assigned output folders.
5. Sub-agents report back by writing local results and summaries.
6. The main agent integrates outputs.
7. The main agent updates parent documentation.
8. The main agent decides whether to promote, reject, branch, revise, stop, or continue.

This preserves Revolve’s hierarchy while allowing parallel search.

### 11.1 Highest Synchronization Point

The highest efficient synchronization point is the active revision.

The reason is that the revision defines the evaluation environment. It freezes the harness, cases, scoring policy, subject definition, incumbent, and comparability rules. Sub-agents can work below this level without needing to coordinate with siblings.

Sub-agents may operate inside:

* assigned branch workspaces;
* assigned checkpoint workspaces;
* assigned case-shard evaluation folders;
* assigned failure-analysis folders;
* assigned proposal folders.

They should not meet at the project level because that would make evaluation context ambiguous. They should not update root or project indexes because that would create shared-state collisions. They meet at the revision-level parallel batch, where the main agent consolidates their outputs.

The synchronization principle is:

Sub-agents work below the revision. The main agent consolidates at the revision.

### 11.2 Parallel Batch

A parallel batch is created under the active revision.

It should document:

* batch id;
* project id;
* revision id;
* base checkpoint;
* incumbent at batch start;
* frozen evaluation environment;
* case suite identity;
* harness identity;
* scoring policy;
* runtime stop directive;
* work packet index;
* allowed write locations;
* integration policy;
* batch status.

During a batch, the frozen context should not be changed by sub-agents. If the evaluation environment must change, the sub-agent proposes a revision change instead of applying it.

### 11.3 Work Packet

A work packet is the unit of delegation.

It should define:

* work packet id;
* assigned objective;
* base checkpoint;
* target branch or local branch name;
* frozen revision;
* allowed read paths;
* allowed write path;
* forbidden actions;
* expected output;
* completion criteria;
* reporting format.

A work packet should be narrow enough that the sub-agent can work without coordination.

Examples:

* create a conservative candidate from checkpoint X;
* explore a radical branch from checkpoint X;
* continue branch Y for two candidate cycles;
* evaluate checkpoint Z on case shard 2;
* analyze failure cluster F and propose fixes;
* propose new cases for an observed dataset gap without applying them.

### 11.4 Sub-Agent Permissions

A sub-agent may:

* read the frozen revision context;
* inspect the assigned subject checkpoint;
* create local candidate checkpoints inside its assigned output folder;
* run the harness if permitted;
* evaluate assigned cases;
* analyze failures;
* propose new branches;
* propose new cases or harness changes;
* write local AGENTS.md files inside its output folder;
* report back to the main agent.

A sub-agent must not:

* edit revolve/AGENTS.md;
* edit the project AGENTS.md;
* edit the active revision AGENTS.md;
* edit official branch indexes;
* edit official checkpoint indexes;
* edit the active harness;
* edit the active case suite;
* change scoring rules;
* change the incumbent pointer;
* promote;
* edit live project files;
* write into another sub-agent’s folder.

This gives sub-agents autonomy without shared mutable state.

### 11.5 Sub-Agent Reporting

A sub-agent reports by writing a local output package.

The output package should include:

* local AGENTS.md;
* work packet id;
* base checkpoint;
* produced candidate or analysis;
* changed artifacts or patch;
* restore instructions;
* run results if any;
* failed cases;
* regressions observed;
* assumptions;
* blocker if any;
* recommendation to import, reject, continue, or revise.

The report is not a parent-doc update. It is evidence for the main agent.

### 11.6 Main Agent Integration

The main agent owns integration.

It reads each sub-agent output and decides whether it is:

* valid;
* invalid;
* incomplete;
* stale;
* duplicate;
* useful as analysis only;
* importable as an official checkpoint;
* importable as an official run;
* grounds for a new branch;
* grounds for a new revision.

Only after integration does the main agent update official parent docs.

The main agent may import:

* candidate checkpoints into subject/checkpoints/;
* branch summaries into branches/;
* valid runs into runs/;
* proposed cases into a new revision;
* proposed harness changes into a new revision;
* reusable insights into the project or revision summary.

The main agent must label outputs as stale if the revision, incumbent, or evaluation environment changed before integration.

### 11.7 Parallel Work Types

Parallel work should be divided by objective, not by competition.

Useful work types:

* candidate generation;
* branch continuation;
* case-shard evaluation;
* repeated stochastic evaluation;
* failure analysis;
* regression analysis;
* proposal of new cases;
* proposal of new harness improvements;
* exploration of alternative subject strategies.

Sub-agents should not be told to “beat each other.” They should be assigned different hypotheses, risk profiles, failure clusters, or evaluation shards.

Good assignment:

* one sub-agent creates a conservative candidate;
* one sub-agent creates an exploratory candidate;
* one sub-agent analyzes regressions;
* one sub-agent evaluates the best candidate on a case shard.

Bad assignment:

* multiple sub-agents edit the same branch;
* multiple sub-agents write to the same checkpoint folder;
* multiple sub-agents update parent docs;
* multiple sub-agents change the test suite.

### 11.8 Parallel Stop Conditions

A parallel batch may stop when:

* all work packets finish;
* enough work packets finish to make a decision;
* one candidate satisfies the runtime stop directive;
* budget is exhausted;
* the main agent detects that the batch is no longer useful;
* the user stops the batch.

If a candidate satisfies the user’s target before all sub-agents finish, the main agent may either stop the batch early or allow remaining work to finish for confidence, depending on the user’s directive.

### 11.9 Parallel Documentation Rule

Parallelism does not change the documentation hierarchy. It only adds a temporary layer below the revision.

The rule is:

Sub-agents document locally. The main agent consolidates upward.

This means sub-agents can work freely inside their assigned folders, but the main agent remains the single writer for shared parent state.

---

## 12. Versioning and Comparability

Revolve treats evaluation changes as first-class events.

A new revision should be created when the agent changes:

* case content or case list;
* scoring rules;
* harness behavior;
* evaluator rubric;
* subject definition;
* objective interpretation;
* required acceptance gates.

This prevents false progress.

If the user reports a new failure and asks the agent to add a case, the evaluation environment has changed. The old leaderboard cannot be compared directly to the new one. The agent should create a new revision or explicitly version the evaluation environment, re-run the incumbent, and compare future candidates under that new context.

Old results remain useful. They explain what was tried and where promising branches came from. They are not direct competitors unless re-run under the same evaluation environment.

Parallel outputs follow the same rule. If a sub-agent produced output under an older revision or older incumbent, the main agent may keep it as historical evidence, but it must not merge its score into the current leaderboard unless the candidate is re-evaluated under the current revision.

---

## 13. Result Recording

Each revision defines its own result schema because different tasks need different measurements.

Every run should preserve minimum provenance:

* run id;
* project id;
* revision id;
* checkpoint id;
* branch id if applicable;
* work packet id if generated in parallel;
* harness identity;
* case suite identity;
* score summary;
* failed cases;
* regression notes;
* raw output location;
* infrastructure errors;
* evaluator notes;
* decision or next action.

The schema may add task-specific fields. A code benchmark may record latency. A prompt evaluation may record rubric scores. A visual task may record review dimensions.

Revolve does not impose one universal trace schema. It requires each revision to define the schema that makes evidence meaningful for that task.

---

## 14. Branch Lifecycle

Branches prevent the search from becoming linear and fragile.

A branch should have:

* starting checkpoint;
* search hypothesis;
* strategy;
* candidate history;
* best result;
* current status;
* reason for continuation or termination.

Possible statuses:

* active;
* promising;
* plateaued;
* dead;
* archived;
* promoted;
* superseded.

A branch becomes plateaued when it stops producing meaningful improvement under the declared criteria. A branch becomes dead when its strategy has failed or its tradeoffs are unacceptable.

Dead branches are not deleted. They are compacted. The branch keeps its detailed records, but the parent index stores only the conclusion. This allows the agent to avoid repeating failed research without carrying the whole failed branch in active context.

In parallel mode, sub-agents may create local branch proposals. These become official branches only when the main agent imports them.

---

## 15. Promotion Discipline

Promotion is not a score update. It is a controlled state transition.

A candidate may be promoted when it passes the active revision’s acceptance policy. A candidate may also be promoted by explicit user choice, but that choice must be documented with known tradeoffs.

The acceptance policy should be declared before candidate generation and may include:

* must-pass cases;
* primary score threshold;
* regression limits;
* stability requirements;
* cost or latency limits;
* manual or LLM review when needed.

A promotion record should include:

* promoted checkpoint;
* previous incumbent;
* reason for promotion;
* evidence summary;
* affected files if applied externally;
* verification result;
* rollback instructions.

Hashes, backups, and post-promotion checks are optional mechanisms for promotion reliability. They confirm that the artifact being promoted is the artifact that was evaluated, preserve the previous state, and verify that the change was applied correctly.

In parallel mode, sub-agents may recommend promotion, but only the main agent may promote.

---

## 16. Why Revolve Is Different From Static Auto-Research

Static auto-research systems ship an implementation. Revolve ships a method.

A static system says: use this runner, this benchmark, this trace format, this model interface, and this project layout.

Revolve says: determine the local objective, build the correct evaluation environment, checkpoint the subject, run the baseline, branch candidates, evaluate comparably, document hierarchically, parallelize safely when possible, and promote only validated improvements.

This matters because the correct evaluator is domain-dependent. Some tasks need deterministic scripts. Some need existing tests. Some need LLM or human judgment. Some need a hybrid. A framework that hardcodes the evaluator becomes narrow by design.

Revolve avoids that limitation. It lets the agent create the local harness while enforcing the global discipline that makes the search reliable.

As AI models improve, they become better at writing scripts, designing tests, judging outputs, inspecting multimodal artifacts, selecting tools, and coordinating sub-agents. Static harnesses may become obsolete. Revolve is designed to benefit from stronger agents because it delegates implementation to the agent while preserving the method.

This also makes previous research reusable. A project started with one model can be resumed later with a stronger model. The new agent reads the hierarchy, understands the active revision, sees dead branches and promoted checkpoints, sees prior parallel batches if any, and continues from a documented state instead of starting over.

---

## 17. Reliability Claims and Limits

Revolve improves operational reliability. It makes research easier to resume, audit, compare, parallelize, and roll back.

It does not guarantee that an evaluator is scientifically correct. It does not remove the need for domain expertise in high-stakes work. It does not make weak cases strong by default. It does not guarantee that a hosting agentic system will implement sub-agents safely; it defines the rules such systems should follow.

Reliability in Revolve means:

* the objective is explicit;
* the baseline is known;
* the evaluation environment is documented;
* checkpoints are recoverable;
* comparisons are valid within revisions;
* branch history is preserved;
* sub-agent outputs are isolated before integration;
* promotions are justified;
* rollback is possible;
* future agents can resume without reconstructing the entire past.

The quality of the final improvement still depends on the quality of the cases, harness, scoring policy, agent judgment, and available execution environment. Revolve’s role is to force these elements into a reproducible structure.

---

## 18. Minimal Protocol Summary

Revolve can be summarized as the following loop:

1. Clarify the objective and active stop directive.
2. Create or resume revolve/.
3. Create or select a project.
4. Create or select a revision.
5. Define the subject.
6. Build or connect the evaluation environment.
7. Create or import cases.
8. Checkpoint the incumbent.
9. Run the baseline.
10. Choose sequential or parallel search.
11. Generate candidate checkpoints.
12. Evaluate candidates under the same revision.
13. Analyze failures, regressions, and branch progress.
14. Promote, reject, branch, revise, stop, parallelize, or continue.
15. Update the local AGENTS.md hierarchy.
16. Compact inactive branches.
17. Resume later from the documented state if needed.

This loop is the stable part of Revolve. Everything else is task-specific.

---

## 19. Conclusion

Revolve is a generic framework for agentic self-improvement that deliberately avoids becoming a static harness.

Its purpose is not to provide one evaluator for every domain. Its purpose is to instruct an existing coding agent to construct the right evaluator, run it reproducibly, checkpoint every subject state, manage branches, accept user steering, coordinate sub-agents when available, and document the process in a scalable hierarchy.

The framework combines five ideas.

First, evaluation-first improvement. The agent must define how success is measured before it tries to improve the subject.

Second, checkpointed branching search. The agent must preserve subject states, explore alternatives, detect stagnation, and retain dead-branch memory without polluting active context.

Third, runtime-directed completion. The user can define the current stop condition at the beginning or during the loop. The agent treats this as active guidance, not as a permanent objective unless the user makes it one.

Fourth, DOX-style hierarchical documentation. Research memory is stored as a tree of local AGENTS.md files, so the agent can resume deep work without loading the entire history.

Fifth, main-agent-controlled parallelization. Sub-agents can explore independently below the active revision, but synchronization, parent documentation, promotion, and revision changes remain the responsibility of the main agent.

Revolve is portable because it is instruction-only. It is generic because the harness is created locally. It is reproducible because subjects, revisions, runs, branches, stop directives, parallel batches, and promotions are versioned. It is future-facing because stronger agents make the framework more capable instead of obsolete.

The long-term value of Revolve is that it defines the discipline around self-improvement rather than freezing one implementation of it. As coding agents become more capable, they will build better local harnesses, run richer evaluations, and coordinate more effective parallel searches. Revolve remains the protocol that keeps those harnesses reproducible, navigable, and trustworthy.

[1]: https://karpathy.bearblog.dev/sequoia-ascent-2026/?utm_source=chatgpt.com "Sequoia Ascent 2026 summary"
