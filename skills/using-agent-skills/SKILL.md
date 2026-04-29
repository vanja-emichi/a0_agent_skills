---
name: using-agent-skills
description: Discovers and invokes agent skills, and enforces lifecycle discipline. Use when starting a session, discovering which skill applies, working with an active lifecycle, rebooting context, handling repeated errors, or managing trusted vs untrusted findings. This is the meta-skill that governs how all other skills are discovered, invoked, and tracked through lifecycle phases.
---

# Using Agent Skills

## Table of Contents

- [Overview](#overview)
- [When to Use](#when-to-use)
- [Skill Discovery](#skill-discovery)
- [Core Operating Behaviors](#core-operating-behaviors)
- [Common Rationalizations](#common-rationalizations)
- [Skill Rules](#skill-rules)
- [Lifecycle Sequence](#lifecycle-sequence)
- [Quick Reference](#quick-reference)
- [Manus Principles](#manus-principles)
- [The 5-Question Reboot Test](#the-5-question-reboot-test)
- [Read vs Write Decision Matrix](#read-vs-write-decision-matrix)
- [Behavioral Discipline](#behavioral-discipline)
- [Red Flags](#red-flags)
- [Verification](#verification)
- [Planning Runtime Integration](#planning-runtime-integration)

## Overview

Agent Skills is a collection of engineering workflow skills organized by development phase. Each skill encodes a specific process that senior engineers follow. This meta-skill helps you discover and apply the right skill for your current task.

## When to Use

- At the start of a session to understand available skills
- When unsure which skill applies to the current task
- When agent output quality degrades (wrong skill may be active)
- When switching between development phases


## Skill Discovery

When a task arrives, identify the development phase and delegate:

```
Task arrives → determine profile → DELEGATE
    ├── Ideas, research, planning → researcher
    ├── Specs, implementation, simplification → developer
    ├── Tests, TDD → test-engineer
    ├── Code review, quality → code-reviewer
    ├── Security audit → security-auditor
    ├── Skill create/benchmark → skill-creator
    └── Deploying/launching → orchestrator (load skill)
```

## Core Operating Behaviors

These behaviors apply at all times, across all skills. They are non-negotiable.

### 1. Surface Assumptions

Before implementing anything non-trivial, explicitly state your assumptions:

```
ASSUMPTIONS I'M MAKING:
1. [assumption about requirements]
2. [assumption about architecture]
3. [assumption about scope]
→ Correct me now or I'll proceed with these.
```

Don't silently fill in ambiguous requirements. The most common failure mode is making wrong assumptions and running with them unchecked. Surface uncertainty early — it's cheaper than rework.

### 2. Manage Confusion Actively

When you encounter inconsistencies, conflicting requirements, or unclear specifications:

1. **STOP.** Do not proceed with a guess.
2. Name the specific confusion.
3. Present the tradeoff or ask the clarifying question.
4. Wait for resolution before continuing.

**Bad:** Silently picking one interpretation and hoping it's right.
**Good:** "I see X in the spec but Y in the existing code. Which takes precedence?"

### 3. Push Back When Warranted

You are not a yes-machine. When an approach has clear problems:

- Point out the issue directly
- Explain the concrete downside (quantify when possible — "this adds ~200ms latency" not "this might be slower")
- Propose an alternative
- Accept the human's decision if they override with full information

Sycophancy is a failure mode. "Of course!" followed by implementing a bad idea helps no one. Honest technical disagreement is more valuable than false agreement.

### 4. Enforce Simplicity

Your natural tendency is to overcomplicate. Actively resist it.

Before finishing any implementation, ask:
- Can this be done in fewer lines?
- Are these abstractions earning their complexity?
- Would a staff engineer look at this and say "why didn't you just..."?

If you build 1000 lines and 100 would suffice, you have failed. Prefer the boring, obvious solution. Cleverness is expensive.

### 5. Maintain Scope Discipline

Touch only what you're asked to touch.

Do NOT:
- Remove comments you don't understand
- "Clean up" code orthogonal to the task
- Refactor adjacent systems as a side effect
- Delete code that seems unused without explicit approval
- Add features not in the spec because they "seem useful"

Your job is surgical precision, not unsolicited renovation.

### 6. Verify, Don't Assume

Every skill includes a verification step. A task is not complete until verification passes. "Seems right" is never sufficient — there must be evidence (passing tests, build output, runtime data).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I don't need to check for a skill" | Every non-trivial task has a matching skill. Skipping it means skipping proven process. |
| "I'll just start building" | Building without a spec is guessing. Specs surface assumptions before code. |
| "The requirements are obvious" | Obvious requirements have hidden assumptions. Surface them explicitly. |
| "It looks right, no need to verify" | "Seems right" is never sufficient. Every skill includes verification for a reason. |
| "I'll clean up this unrelated code while I'm here" | Scope discipline prevents cascading changes. Touch only what you're asked to touch. |
| "A little complexity is fine" | If 100 lines would suffice and you wrote 1000, you have failed. Prefer the boring solution. |
| "Of course!" (to a bad idea) | Sycophancy is a failure mode. Honest technical disagreement is more valuable than false agreement. |
| "I'll skip verification this time" | Verification is the last line of defense against subtle bugs. Never skip it. |
| "The existing code is probably wrong" | Don't remove things you don't understand. Chesterton's Fence applies. |
| "I can handle multiple skills at once" | Load and follow one skill at a time. Complete its verification before moving to the next. |

## Skill Rules

1. **Check for an applicable skill before starting work.** Skills encode processes that prevent common mistakes.

2. **Skills are workflows, not suggestions.** Follow the steps in order. Don't skip verification steps.

3. **Multiple skills can apply.** A feature implementation might involve `idea-refine` → `spec-driven-development` → `planning-and-task-breakdown` → `incremental-implementation` → `test-driven-development` → `code-review-and-quality` → `shipping-and-launch` in sequence.

4. **When in doubt, start with a spec.** If the task is non-trivial and there's no spec, begin with `spec-driven-development`.

## Lifecycle Sequence

For a complete feature, the typical skill sequence is:

```
1. idea-refine                 → DELEGATE to researcher
2. spec-driven-development     → DELEGATE to developer
3. planning-and-task-breakdown → DELEGATE to researcher
4. context-engineering         → DELEGATE to developer
5. source-driven-development   → DELEGATE to developer
6. incremental-implementation  → DELEGATE to developer
7. test-driven-development     → DELEGATE to test-engineer
8. code-review-and-quality     → DELEGATE to code-reviewer
9. git-workflow-and-versioning → DELEGATE to developer
10. documentation-and-adrs     → DELEGATE to developer
11. shipping-and-launch        → Deploy safely (orchestrator)
```

Not every task needs every skill. A bug fix might only need: `debugging-and-error-recovery` → `test-driven-development` → `code-review-and-quality`.
For security-specific audits at any point, use `/security` → DELEGATE to security-auditor.
For creating, testing, grading, or optimizing skills, use `/test` with skill-creator intent → DELEGATE to skill-creator.

## Quick Reference

| Phase | Skill | Method | One-Line Summary |
|-------|-------|--------|-----------------|
| Define | idea-refine | Delegate → researcher | Refine ideas through structured divergent and convergent thinking |
| Define | spec-driven-development | Delegate → developer | Requirements and acceptance criteria before code |
| Plan | planning-and-task-breakdown | Delegate → researcher | Decompose into small, verifiable tasks |
| Build | incremental-implementation | Delegate → developer | Thin vertical slices, test each before expanding |
| Build | source-driven-development | Delegate → developer | Verify against official docs before implementing |
| Build | context-engineering | Delegate → developer | Right context at the right time |
| Build | frontend-ui-engineering | Delegate → developer | Production-quality UI with accessibility |
| Build | api-and-interface-design | Delegate → developer | Stable interfaces with clear contracts |
| Verify | test-driven-development | Delegate → test-engineer | Failing test first, then make it pass |
| Verify | browser-testing-with-devtools | Delegate → test-engineer | playwright-cli for runtime browser verification |
| Verify | debugging-and-error-recovery | Delegate → developer | Reproduce → localize → fix → guard |
| Review | code-review-and-quality | Delegate → code-reviewer | Five-axis review with quality gates |
| Review | security-and-hardening | Delegate → security-auditor | OWASP prevention, input validation, least privilege |
| Review | performance-optimization | Delegate → developer | Measure first, optimize only what matters |
| Ship | git-workflow-and-versioning | Delegate → developer | Atomic commits, clean history |
| Ship | ci-cd-and-automation | Delegate → developer | Automated quality gates on every change |
| Ship | shipping-and-launch | Load skill | Pre-launch checklist, monitoring, rollback plan |
| Ship | documentation-and-adrs | Delegate → developer | Architecture Decision Records |
| Ship | deprecation-and-migration | Delegate → developer | Safe migration patterns |
| Meta | skill-creator | Delegate → skill-creator | Create, test, grade, benchmark, and optimize skills |

---

## Manus Principles

The lifecycle discipline is grounded in three principles from Manus-style agent design:

### 1. Memory Externalized (KV-Cache Stability)

Plan state is persisted to disk, not held in conversation history. The EXTRAS block injected every turn has a **stable prefix** (goal + phase list with status icons) and a **dynamic suffix** (last-N progress and findings). The stable prefix enables KV-cache hits — the model sees the same bytes for unchanged state, reducing token cost and improving consistency.

**Rule:** Never put timestamps or volatile data in the lifecycle prefix. Dynamic data goes in the suffix.

### 2. Keep-Wrong-Stuff-In

Findings are append-only. Never delete or edit a finding — even if it was later disproven. Instead, log a new finding that supersedes the old one. This creates an audit trail and prevents the model from repeating the same wrong path.

**Rule:** `Append to findings.md with source tag (trusted/untrusted)` appends. There is no `plan:edit_finding` or `plan:delete_finding`.

### 3. Attention via Recitation

The 5-Question Reboot Test forces the model to *recite* the current state before acting. This is not busywork — it primes the attention mechanism with the exact context needed for the next decision. Every `lifecycle:status` call answers all five questions.

**Rule:** After context compaction, conversation resume, or uncertainty — run `lifecycle:status` first.

---

## The 5-Question Reboot Test

When resuming work, recovering from an error, or at the start of any uncertain turn, answer these five questions (via `lifecycle:status`):

| # | Question | Answer Source |
|---|----------|--------------|
| 1 | **Where am I?** | Current phase title + status (⏸️ pending, 🔄 in_progress, ✅ completed) |
| 2 | **Where am I going?** | Plan goal from metadata |
| 3 | **What's the goal?** | Same as #2 — redundant by design (reinforcement) |
| 4 | **What did I learn?** | Findings count + last few findings from findings.md |
| 5 | **What's done?** | Completed phase count / total phases |

**Usage:**
```
lifecycle:status
```

The response includes all five answers in a structured format. Read it. Act on it.

---

## Read vs Write Decision Matrix

Plan state can be read freely but must be written through the lifecycle tool. This prevents corruption and maintains the audit trail.

| Action | How | When |
|--------|-----|------|
| **Read** lifecycle state | `lifecycle:status` or EXTRAS block (automatic) | Anytime — no side effects |
| **Read** findings/progress | Direct file read of `.a0proj/run/current/findings.md` | Anytime — these are append-only logs |
| **Write** phase transitions | `Edit state.md frontmatter: change phase status from ⏸️ to 🔄`, `Edit state.md frontmatter: change phase status from 🔄 to ✅` | When starting or finishing a phase |
| **Write** findings | `Append to findings.md with source tag (trusted/untrusted)` with `source` tag | When discovering information worth keeping |
| **Write** progress | `Append to progress.md with timestamp` | When completing a meaningful step |
| **Write** errors | `Append to errors.md with error hash` | When encountering a failure |
| **Write** new phases | `Lifecycle has fixed 7 phases: IDEA→SPEC→PLAN→BUILD→VERIFY→REVIEW→SHIP` | When scope expands beyond the original plan |
| **Write** archive | `lifecycle:archive` | When the lifecycle is done or abandoned |

**Rule:** The lifecycle tool manages init, status, and archive. Day-to-day operations are direct file edits: edit state.md YAML frontmatter for phase transitions, append to findings.md/progress.md for findings and progress. Read freely via lifecycle:status or direct file reads.

---

## Behavioral Discipline

A0 behavioral discipline (Think-Before-Coding, Surgical-Changes, Safe-Operations, Terse-Commits, Structured-Review, Output-Compression) is embedded directly into plugin skills above.

**Tradeoff:** These guidelines bias toward caution over speed. Apply full rigor to non-trivial tasks. Use judgment on simple one-liners.

## Red Flags

- Writing code before checking for an applicable skill
- Implementing without a spec for non-trivial tasks
- Skipping verification steps because "it looks right"
- Modifying code or comments orthogonal to the task
- Adding features not in the spec because they "seem useful"
- Agreeing with approaches that have clear problems without pushing back
- Building 1000 lines when 100 would suffice
- Removing code without understanding why it exists
- Loading multiple skills simultaneously instead of sequencing
- Proceeding despite confusion without stopping to clarify

## Verification

After skill discovery:
- [ ] Correct skill identified for the task phase
- [ ] Skill loaded via `skills_tool:load <name>`
- [ ] Skill instructions followed in order
- [ ] Output matches the skill's expected format

---

## Planning Runtime Integration

The `lifecycle` tool is part of the skill lifecycle when an active lifecycle exists. Add these method calls to your workflow:

| Lifecycle Phase | Plan Tool Method |
|-----------------|-----------------|
| After `/plan` produces a task breakdown | `lifecycle:init` with goal + phases |
| Before starting work on a task | `Edit state.md frontmatter: change phase status from ⏸️ to 🔄` |
| After completing a task | `Edit state.md frontmatter: change phase status from 🔄 to ✅` |
| When discovering important information | `Append to findings.md with source tag (trusted/untrusted)` |
| After completing a meaningful step | `Append to progress.md with timestamp` |
| When hitting an error | `Append to errors.md with error hash` |
| After `/ship` decision GO | `lifecycle:archive status="completed"` |
| If work is abandoned | `lifecycle:archive status="abandoned"` |

The lifecycle runtime layer persists state across turns and subordinates via `.a0proj/run/current/`, surviving context compaction. Check current state anytime with `lifecycle:status`.
