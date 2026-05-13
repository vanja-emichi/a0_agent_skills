---
name: using-agent-skills
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Meta-skill for selecting and applying the right skill for any task. Use when
  starting a task and unsure which skill to apply, or when coordinating
  multiple skills for a complex workflow. This is the routing brain for the
  entire skill set. WARNING: load this skill on-demand only — never pin it as
  always-active. Agent Zero enforces a 20-skill active cap; pinning this skill
  would displace one of the 20 lifecycle skills.
tags:
  - meta
  - routing
  - orchestration
  - workflow
  - skills
trigger_patterns:
  - using-agent-skills
  - which skill should I use
  - what skill applies here
  - how to use skills
  - skill selection
  - route to skill
  - agent skill workflow
  - skill orchestration
  - which skill for this task
  - help me pick a skill
---

# Using Agent Skills

> **Supporting files:** This skill has a companion orchestration patterns guide.
> Use `text_editor:read` with the full path shown in the file tree when this
> skill is loaded to open `orchestration-patterns.md` (sibling to this SKILL.md).

## Overview

This meta-skill helps you identify which skill to apply for a given task, and how to combine skills when a task spans multiple domains. Skills are not rigid scripts — they're behavioral frameworks that shape how the agent approaches a type of work.

**How to load a skill in Agent Zero:**
```
skills_tool:load skill_name=<skill-name>
```
Once loaded, the skill's instructions are active for the current session. You can load multiple skills and they compose together.

## The 20-Skill Taxonomy

### Planning & Specification

| Skill | When to Load |
|-------|-------------|
| `spec-driven-development` | Before building anything — turn requirements into a spec first |
| `planning-and-task-breakdown` | Decompose a large feature into a structured implementation plan |
| `idea-refine` | Explore and sharpen an underdeveloped idea before committing to it |

### Implementation

| Skill | When to Load |
|-------|-------------|
| `incremental-implementation` | Building features step by step with verification at each step |
| `test-driven-development` | Implementing with tests written first |
| `source-driven-development` | Before using any library/API that may have changed since training |

### Code Quality

| Skill | When to Load |
|-------|-------------|
| `code-review-and-quality` | Reviewing code before merging or shipping |
| `code-simplification` | Refactoring working code to be cleaner and easier to maintain |
| `debugging-and-error-recovery` | Diagnosing and fixing bugs or failing tests |

### Frontend & APIs

| Skill | When to Load |
|-------|-------------|
| `frontend-ui-engineering` | Building user interfaces with React/Tailwind |
| `api-and-interface-design` | Designing REST/GraphQL APIs or module interfaces |
| `browser-testing-with-devtools` | Testing UI in a real browser, inspecting DOM/console/network |

### Cross-Cutting Concerns

| Skill | When to Load |
|-------|-------------|
| `security-and-hardening` | Implementing auth, validation, secrets management |
| `performance-optimization` | Diagnosing and fixing performance issues |
| `context-engineering` | Setting up project guidance files, managing long sessions |

### Delivery & Operations

| Skill | When to Load |
|-------|-------------|
| `shipping-and-launch` | Pre-launch checklist, feature flags, staged rollouts |
| `git-workflow-and-versioning` | Commit messages, branching, PRs, semantic versioning |
| `ci-cd-and-automation` | CI/CD pipelines, GitHub Actions, Dockerfile |

### Documentation & Lifecycle

| Skill | When to Load |
|-------|-------------|
| `documentation-and-adrs` | READMEs, API docs, Architecture Decision Records |
| `deprecation-and-migration` | Removing APIs, database migrations, dependency upgrades |

## Skill Selection Flowchart

```
What is the task?
│
├── PLANNING
│   ├── I have an idea but it's not fully defined yet
│   │   └── → idea-refine
│   ├── I need to write a spec/requirements before coding
│   │   └── → spec-driven-development
│   └── I need to break a large feature into tasks
│       └── → planning-and-task-breakdown
│
├── IMPLEMENTATION
│   ├── Building a new feature from a spec
│   │   └── → incremental-implementation
│   │       (also load: test-driven-development if TDD)
│   ├── Using a library I'm not sure about
│   │   └── → source-driven-development (fetch docs first)
│   └── Writing tests for existing code
│       └── → test-driven-development
│
├── CODE QUALITY
│   ├── Reviewing code before merge
│   │   └── → code-review-and-quality
│   ├── Refactoring working code
│   │   └── → code-simplification
│   └── Something is broken / tests failing
│       └── → debugging-and-error-recovery
│
├── FRONTEND / API
│   ├── Building UI components or pages
│   │   └── → frontend-ui-engineering
│   │       (+ browser-testing-with-devtools for verification)
│   ├── Designing API endpoints or module interfaces
│   │   └── → api-and-interface-design
│   └── Debugging browser behavior / DOM / network
│       └── → browser-testing-with-devtools
│
├── CROSS-CUTTING CONCERNS
│   ├── Authentication, input validation, security headers
│   │   └── → security-and-hardening
│   ├── App is too slow / performance issues
│   │   └── → performance-optimization
│   └── Agent lacks project context / setting up guidance file
│       └── → context-engineering
│
├── DELIVERY
│   ├── About to deploy to production
│   │   └── → shipping-and-launch
│   ├── Writing commit messages / PRs / versioning
│   │   └── → git-workflow-and-versioning
│   └── Setting up or modifying CI/CD pipelines
│       └── → ci-cd-and-automation
│
└── DOCUMENTATION & LIFECYCLE
    ├── Writing README / ADRs / API docs
    │   └── → documentation-and-adrs
    └── Removing old APIs / database migrations / upgrades
        └── → deprecation-and-migration
```

## Multi-Skill Combinations

Many real tasks benefit from loading multiple skills. Common combinations:

### Feature Development (End-to-End)

```
1. spec-driven-development        → Write the spec
2. planning-and-task-breakdown    → Break into tasks
3. incremental-implementation     → Build step by step
4. test-driven-development        → Tests first
5. code-review-and-quality        → Review before merge
6. shipping-and-launch            → Deploy safely
```

### New Project Setup

```
1. context-engineering            → Write AGENTS.md
2. spec-driven-development        → Define what to build
3. api-and-interface-design       → Design the API layer
4. ci-cd-and-automation           → Set up the pipeline
5. documentation-and-adrs         → Initial ADRs
```

### Bug Investigation

```
1. debugging-and-error-recovery   → Systematic diagnosis
2. browser-testing-with-devtools  → Browser-side investigation
3. test-driven-development        → Regression test
4. git-workflow-and-versioning    → Clean fix commit
```

### Security Audit

```
1. security-and-hardening         → Run security checklist
2. code-review-and-quality        → Code-level review
3. documentation-and-adrs         → Record decisions
```

### Performance Investigation

```
1. performance-optimization       → Profile and fix
2. browser-testing-with-devtools  → Browser metrics
3. source-driven-development      → Verify library usage
```

## Core Operating Behaviors

These behaviors apply in every session, regardless of which skills are loaded:

### 1. Verify Before Assuming

Never assume code works. Run it. Test it. Check the actual output.

```
CHECK BEFORE CLAIMING SUCCESS:
→ Run the tests via code_execution_tool
→ Check the browser via browser tool (for UI)
→ Read the actual output, don't predict it
```

### 2. Understand Before Changing

Don't modify code you don't understand. Read it first.

```
BEFORE EDITING:
→ text_editor:read the file
→ grep -rn for usages (code_execution_tool)
→ git log to understand history
```

### 3. Scope Discipline

Do what was asked. Don't refactor unrelated code. Don't add unasked features.

```
FOR EVERY CHANGE ASK:
→ Was this asked for?
→ Is it required to complete the task?
→ If no to both — don't make it
```

### 4. Explicit Over Implicit

Make assumptions visible. State constraints. Document decisions.

```
MAKE THESE EXPLICIT:
→ What you're about to do and why
→ Trade-offs in your approach
→ What you're NOT doing and why
→ Decisions that future agents need to know
```

### 5. Trust the Source

When in doubt about an API, library, or framework — read the docs. Don't rely on memory.

```
→ Load source-driven-development for any external library
→ Use document_query or browser to fetch current docs
→ Verify before implementing
```

## How Skills Compose

Loaded skills modify agent behavior without overriding each other:

```
# Loading multiple skills composes their behaviors:
skills_tool:load skill_name=incremental-implementation
skills_tool:load skill_name=test-driven-development
skills_tool:load skill_name=security-and-hardening

# Now the agent:
# → Builds incrementally (incremental-implementation)
# → Writes tests first (test-driven-development)
# → Validates input at boundaries (security-and-hardening)
# All three behaviors are active simultaneously
```

When skills conflict (rare), the most recently loaded skill takes precedence for that specific behavior.

## Quick Reference: Load Commands

```bash
# Planning
skills_tool:load skill_name=idea-refine
skills_tool:load skill_name=spec-driven-development
skills_tool:load skill_name=planning-and-task-breakdown

# Implementation
skills_tool:load skill_name=incremental-implementation
skills_tool:load skill_name=test-driven-development
skills_tool:load skill_name=source-driven-development

# Quality
skills_tool:load skill_name=code-review-and-quality
skills_tool:load skill_name=code-simplification
skills_tool:load skill_name=debugging-and-error-recovery

# Frontend & API
skills_tool:load skill_name=frontend-ui-engineering
skills_tool:load skill_name=api-and-interface-design
skills_tool:load skill_name=browser-testing-with-devtools

# Cross-Cutting
skills_tool:load skill_name=security-and-hardening
skills_tool:load skill_name=performance-optimization
skills_tool:load skill_name=context-engineering

# Delivery
skills_tool:load skill_name=shipping-and-launch
skills_tool:load skill_name=git-workflow-and-versioning
skills_tool:load skill_name=ci-cd-and-automation

# Documentation & Lifecycle
skills_tool:load skill_name=documentation-and-adrs
skills_tool:load skill_name=deprecation-and-migration
```

## See Also

For advanced orchestration patterns — parallel skill execution, skill chaining, agent delegation templates — use `text_editor:read` on the `orchestration-patterns.md` file in this skill's directory (path shown in file tree when this skill is loaded).

## Red Flags

- Jumping into implementation without loading any skill
- Loading skills but not following their verification checklists
- Loading a skill then ignoring its Red Flags section
- Using a skill as a rigid checklist instead of a behavioral framework
- Not updating the task tracking file during long multi-skill sessions

## Verification

At any point in a session:

- [ ] The right skill(s) are loaded for the current task type
- [ ] Core Operating Behaviors are active (verify, understand, scope, explicit, source)
- [ ] Loaded skills' Red Flags sections have been checked
- [ ] Loaded skills' Verification checklists will be completed before marking done
- [ ] For complex tasks: a session tracking file exists at `/tmp/session-tasks.md`
