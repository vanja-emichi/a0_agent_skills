---
name: using-agent-skills
description: Discovers and invokes agent skills. Use when starting a session or when you need to discover which skill applies to the current task. This is the meta-skill that governs how all other skills are discovered and invoked.
---

# Using Agent Skills

## Overview

Agent Skills is a collection of engineering workflow skills organized by development phase. Each skill encodes a specific process that senior engineers follow. This meta-skill helps you discover and apply the right skill for your current task.

## When to Use

- At the start of a session to understand available skills
- When unsure which skill applies to the current task
- When agent output quality degrades (wrong skill may be active)
- When switching between development phases


## Skill Discovery

When a task arrives, identify the development phase and apply the corresponding skill:

```
Task arrives
    │
    ├── Vague idea/need refinement? ──→ idea-refine
    ├── New project/feature/change? ──→ spec-driven-development
    ├── Have a spec, need tasks? ──────→ planning-and-task-breakdown
    ├── Implementing code? ────────────→ incremental-implementation
    │   ├── UI work? ─────────────────→ frontend-ui-engineering
    │   ├── API work? ────────────────→ api-and-interface-design
    │   ├── Need better context? ─────→ context-engineering
    │   └── Need doc-verified code? ───→ source-driven-development
    ├── Writing/running tests? ────────→ DELEGATE to test-engineer
    │   └── Browser-based? ───────────→ browser-testing-with-devtools
    ├── Something broke? ──────────────→ debugging-and-error-recovery
    ├── Reviewing code? ───────────────→ DELEGATE to code-reviewer
    │   ├── Security concerns? ───────→ DELEGATE to security-auditor
    │   └── Performance concerns? ────→ performance-optimization
    ├── Committing/branching? ─────────→ git-workflow-and-versioning
    ├── CI/CD pipeline work? ──────────→ ci-cd-and-automation
    ├── Writing docs/ADRs? ───────────→ documentation-and-adrs
    ├── Creating/testing/optimizing skills? → DELEGATE to skill-creator
    └── Deploying/launching? ─────────→ shipping-and-launch
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
1. idea-refine                 → Refine vague ideas
2. spec-driven-development     → Define what we're building
3. planning-and-task-breakdown → Break into verifiable chunks
4. context-engineering         → Load the right context
5. source-driven-development   → Verify against official docs
6. incremental-implementation  → Build slice by slice
7. test-driven-development     → DELEGATE to test-engineer
8. code-review-and-quality     → DELEGATE to code-reviewer
9. git-workflow-and-versioning → Clean commit history
10. documentation-and-adrs     → Document decisions
11. shipping-and-launch        → Deploy safely
```

Not every task needs every skill. A bug fix might only need: `debugging-and-error-recovery` → `test-driven-development` → `code-review-and-quality`.
For security-specific audits at any point, use `/security` → DELEGATE to security-auditor.
For creating, testing, grading, or optimizing skills, use `/test` with skill-creator intent → DELEGATE to skill-creator.

## Quick Reference

| Phase | Skill | Method | One-Line Summary |
|-------|-------|--------|-----------------|
| Define | idea-refine | Load skill | Refine ideas through structured divergent and convergent thinking |
| Define | spec-driven-development | Load skill | Requirements and acceptance criteria before code |
| Plan | planning-and-task-breakdown | Load skill | Decompose into small, verifiable tasks |
| Build | incremental-implementation | Load skill | Thin vertical slices, test each before expanding |
| Build | source-driven-development | Load skill | Verify against official docs before implementing |
| Build | context-engineering | Load skill | Right context at the right time |
| Build | frontend-ui-engineering | Load skill | Production-quality UI with accessibility |
| Build | api-and-interface-design | Load skill | Stable interfaces with clear contracts |
| Verify | test-driven-development | Delegate → test-engineer | Failing test first, then make it pass |
| Verify | browser-testing-with-devtools | Load skill | playwright-cli for runtime browser verification |
| Verify | debugging-and-error-recovery | Load skill | Reproduce → localize → fix → guard |
| Review | code-review-and-quality | Delegate → code-reviewer | Five-axis review with quality gates |
| Review | security-and-hardening | Delegate → security-auditor | OWASP prevention, input validation, least privilege |
| Review | performance-optimization | Load skill | Measure first, optimize only what matters |
| Ship | git-workflow-and-versioning | Load skill | Atomic commits, clean history |
| Ship | ci-cd-and-automation | Load skill | Automated quality gates on every change |
| Ship | shipping-and-launch | Load skill | Pre-launch checklist, monitoring, rollback plan |
| Meta | skill-creator | Delegate → skill-creator | Create, test, grade, benchmark, and optimize skills |

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

The `plan` tool is part of the skill lifecycle when an active lifecycle exists. Add these method calls to your workflow:

| Lifecycle Phase | Plan Tool Method |
|-----------------|-----------------|
| After `/plan` produces a task breakdown | `lifecycle:init` with goal + phases |
| Before starting work on a task | `Edit state.md frontmatter: change phase status from ⏸️ to 🔄` |
| After completing a task | `Edit state.md frontmatter: change phase status from 🔄 to ✅` |
| When discovering important information | `Append to findings.md with source tag (trusted/untrusted)` |
| After completing a meaningful step | `Append to progress.md with timestamp` |
| When hitting an error | `Errors are auto-tracked by StrikeTracker (3-strike protocol)` |
| After `/ship` decision GO | `lifecycle:archive status="completed"` |
| If work is abandoned | `lifecycle:archive status="abandoned"` |

The lifecycle runtime layer persists state across turns and subordinates via `.a0proj/run/current/`, surviving context compaction. Check current state anytime with `lifecycle:status`.
