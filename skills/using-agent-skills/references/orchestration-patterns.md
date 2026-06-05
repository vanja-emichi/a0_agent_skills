# Orchestration Patterns

Reference catalog of agent orchestration patterns this plugin endorses, plus anti-patterns to avoid. Read this before adding a new command that coordinates multiple personas, or before introducing a new persona that "wraps" existing ones.

The governing rule: **the user (or a command) is the orchestrator. Personas do not invoke other personas.** Skills are mandatory hops inside a persona's workflow.

---

## Endorsed patterns

### 1. Direct invocation (no orchestration)

Single persona, single perspective, single artifact. The default and the cheapest option.

```
user → call_subordinate(profile="code-reviewer") → report → user
```

**Use when:** the work is one perspective on one artifact and you can describe it in one sentence.

**Examples:**
- "Review this PR" → `call_subordinate(profile="code-reviewer")`
- "Find security issues in `auth.ts`" → `call_subordinate(profile="security-auditor")`
- "What tests are missing for the checkout flow?" → `call_subordinate(profile="test-engineer")`

**Cost:** one round trip. The baseline you should always compare orchestrated patterns against.

---

### 2. Single-persona command

A command that wraps one persona with the project's skills. Saves the user from re-explaining the workflow every time.

```
review command → call_subordinate(profile="code-reviewer") (with code-review-and-quality skill) → report
```

**Use when:** the same single-persona invocation happens repeatedly with the same setup.

**Examples in this plugin:** `review` command, `test` command, `code-simplify` command.

**Cost:** same as direct invocation. The command is just a saved prompt.

**Anti-signal:** if the command's body is mostly "decide which persona to call," delete it and let the user call the persona directly.

---

### 3. Sequential fan-out with merge

Multiple personas operate on the same input sequentially, each producing an independent report. A merge step (in the main agent's context) synthesizes them into a single decision.

```
ship command → call_subordinate(profile="code-reviewer") → call_subordinate(profile="security-auditor") → call_subordinate(profile="test-engineer") → merge → go/no-go + rollback
```

**Use when:**
- The sub-tasks are genuinely independent (no shared mutable state, no ordering dependency)
- Each subordinate agent benefits from its own context window
- The merge step is small enough to stay in the main context
- Thorough, multi-perspective analysis matters more than wall-clock latency

**Examples in this plugin:** `ship` command.

**Cost:** N sequential subordinate contexts + one merge turn. Higher than direct invocation, but produces better reports because each subordinate stays focused on its single perspective.

**Validation checklist before adopting this pattern:**
- [ ] Can I run all sub-agents without ordering issues?
- [ ] Does each persona produce a different *kind* of finding, not just the same finding from a different angle?
- [ ] Will the merge step fit in the main agent's remaining context?
- [ ] Is the multi-perspective analysis worth the additional token cost?

If any answer is "no," fall back to direct invocation or a single-persona command.

---

### 4. Sequential pipeline as user-driven commands

The user runs commands in a defined order, carrying context (or commit history) between them. There is no orchestrator agent — the user IS the orchestrator.

```
user runs:  spec command  →  plan command  →  build command  →  test command  →  review command  →  ship command
```

**Use when:** the workflow has dependencies (each step needs the previous step's output) and human judgment between steps adds value.

**Examples in this plugin:** the entire DEFINE → PLAN → BUILD → VERIFY → REVIEW → SHIP lifecycle.

**Cost:** one subordinate context per step. Free for the orchestration layer because there is no orchestrator agent.

**Why not automate it:** an LLM "lifecycle orchestrator" would (a) lose nuance between steps because it has to summarize for hand-off, (b) skip the human checkpoints that catch wrong-direction work early, and (c) double the token cost via paraphrasing turns.

---

### 5. Research isolation (context preservation)

When a task requires reading large amounts of material that shouldn't pollute the main context, spawn a research subordinate that returns only a digest.

```
main agent → call_subordinate(profile="researcher") (reads 50 files) → digest → main agent continues
```

**Use when:**
- The main session needs to stay focused on a downstream task
- The investigation result is much smaller than the input it consumes
- The decision quality benefits from the main agent having room to think after

**Examples:** "Find every call site of this deprecated API across the monorepo," "Summarize what these 30 ADRs say about caching."

**Cost:** one isolated subordinate context. Worth it any time the alternative is loading hundreds of files into the main context.

**In Agent Zero, use the built-in `researcher` profile** via `call_subordinate(profile="researcher")` for research-isolated tasks. Define a custom research profile only when the built-in researcher doesn't fit (e.g. you need a domain-specific system prompt the model wouldn't infer).

---

## Anti-patterns

### A. Router persona ("meta-orchestrator")

A persona whose job is to decide which other persona to call.

```
user → router-persona → "this needs a review" → call_subordinate(profile="code-reviewer") → router (paraphrases) → user
```

**Why it fails:**
- Pure routing layer with no domain value
- Adds two paraphrasing hops → information loss + roughly 2× token cost
- The user already knew they wanted a review; they could have called `review` command directly
- Replicates the work that commands and intent mapping in `AGENTS.md` already do

**What to do instead:** add or refine commands. Document intent → command mapping in `AGENTS.md`.

---

### B. Persona that calls another persona

A `code-reviewer` that internally invokes `security-auditor` when it sees auth code.

**Why it fails:**
- Personas were designed to produce a single perspective; chaining them defeats that
- The summary the calling persona passes loses context the called persona needs
- Failure modes multiply (which persona's output format wins? whose rules apply?)
- Hides cost from the user

**What to do instead:** have the calling persona *recommend* a follow-up audit in its report. The user or a command runs the second pass.

---

### C. Sequential orchestrator that paraphrases

An agent that calls the `spec` command, then the `plan` command, then the `build` command, etc. on the user's behalf.

**Why it fails:**
- Loses the human checkpoints that catch wrong-direction work
- Each hand-off summarizes context — accumulated drift over a long pipeline
- Doubles token cost: orchestrator turn + subordinate turn for every step
- Removes user agency at exactly the points where judgment matters most

**What to do instead:** keep the user as the orchestrator. Document the recommended sequence in `README.md` and let users invoke it.

---

### D. Deep persona trees

`ship` command calls a `pre-ship-coordinator` that calls a `quality-coordinator` that calls `code-reviewer`.

**Why it fails:**
- Each layer adds latency and tokens with no decision value
- Debugging becomes a multi-level investigation
- The leaf personas lose context to multiple summarization steps

**What to do instead:** keep the orchestration depth at most 1 (command → personas). The merge happens in the main agent.

---

## Decision flow

When considering a new orchestrated workflow, walk this flow:

```
Is the work one perspective on one artifact?
├── Yes → Direct invocation. Stop.
└── No  → Will the same composition repeat?
         ├── No  → Direct invocation, ad hoc. Stop.
         └── Yes → Are sub-tasks independent?
                  ├── No  → Sequential commands run by user (Pattern 4).
                  └── Yes → Sequential fan-out with merge (Pattern 3).
                           Validate against the checklist above.
                           If any check fails → fall back to single-persona command (Pattern 2).
```

---

## When to add a new pattern to this catalog

Add a new entry only after:

1. You've used the pattern at least twice in real work
2. You can name a concrete artifact in this plugin that demonstrates it
3. You can explain why an existing pattern wouldn't have worked
4. You can describe its anti-pattern shadow (what people will mistakenly build instead)

Premature catalog entries become aspirational documentation that no one follows.
