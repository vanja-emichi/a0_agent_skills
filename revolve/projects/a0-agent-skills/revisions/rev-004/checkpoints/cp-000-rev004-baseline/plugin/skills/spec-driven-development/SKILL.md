---
name: spec-driven-development
description: Creates specs before coding. Use when starting a new project, feature, or significant change and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea.
triggers:
  - "write spec"
  - "requirements"
  - "acceptance criteria"
  - "feature spec"
  - "specification"
  - "technical specification"
  - "spec before code"
  - "project structure"
  - "success criteria"
  - "define requirements"
---

# Spec-Driven Development

## Overview

Write a structured specification before writing any code. The spec is the shared source of truth between you and the human engineer — it defines what we're building, why, and how we'll know it's done. Code without a spec is guessing.

## When to Use

- Starting a new project or feature
- Requirements are ambiguous or incomplete
- The change touches multiple files or modules
- You're about to make an architectural decision
- The task would take more than 30 minutes to implement

**When NOT to use:** Single-line fixes, typo corrections, or changes where requirements are unambiguous and self-contained.

**Related:** `planning-and-task-breakdown` (turn spec into tasks), `incremental-implementation` (execute slices), `context-engineering` (load right spec sections), `documentation-and-adrs` (record architectural decisions), `test-driven-development` (prove each slice works).

### Project Context

Spec-driven development within an active project means the spec must reflect the project's real conventions, structure, and constraints — not generic assumptions:
- Work from the active project directory and use project-relative paths for spec artifacts (`tasks/spec.md`, `tasks/plan.md`)
- Check the project's `AGENTS.md` and project instructions for established tech stack, build commands, and coding conventions before drafting spec content
- Respect `.a0proj/` metadata and project boundaries — the spec defines what to build, not how to reconfigure the project
- Preserve spec decisions and assumption lists across tool sessions so that implementation phases start from a consistent, reviewed baseline

## The Gated Workflow

Spec-driven development has four phases. Do not advance to the next phase until the current one is validated.

```
SPECIFY ──→ PLAN ──→ TASKS ──→ IMPLEMENT
   │          │        │          │
   ▼          ▼        ▼          ▼
 Human      Human    Human      Human
 reviews    reviews  reviews    reviews
```

### Phase 1: Specify

Start with a high-level vision. Ask the human clarifying questions until requirements are concrete.

**Surface assumptions immediately.** Before writing any spec content, list what you're assuming:

```
ASSUMPTIONS I'M MAKING:
1. This is a web application (not native mobile)
2. Authentication uses session-based cookies (not JWT)
3. The database is PostgreSQL (based on existing Prisma schema)
4. We're targeting modern browsers only (no IE11)
→ Correct me now or I'll proceed with these.
```

Don't silently fill in ambiguous requirements. The spec's entire purpose is to surface misunderstandings *before* code gets written — assumptions are the most dangerous form of misunderstanding.

**Write a spec document covering these six core areas:**

1. **Objective** — What are we building and why? Who is the user? What does success look like?

2. **Commands** — Full executable commands with flags, not just tool names.
   ```
   Build: npm run build
   Test: npm test -- --coverage
   Lint: npm run lint --fix
   Dev: npm run dev
   ```

3. **Project Structure** — Where source code lives, where tests go, where docs belong.
   ```
   src/           → Application source code
   src/components → React components
   src/lib        → Shared utilities
   tests/         → Unit and integration tests
   e2e/           → End-to-end tests
   docs/          → Documentation
   ```

4. **Code Style** — One real code snippet showing your style beats three paragraphs describing it. Include naming conventions, formatting rules, and examples of good output.

5. **Testing Strategy** — What framework, where tests live, coverage expectations, which test levels for which concerns.

6. **Boundaries** — Three-tier system:
   - **Always do:** Run tests before commits, follow naming conventions, validate inputs
   - **Ask first:** Database schema changes, adding dependencies, changing CI config
   - **Never do:** Commit secrets, edit vendor directories, remove failing tests without approval

**Spec template:**

```markdown
# Spec: [Project/Feature Name]

## Objective
[What we're building and why. User stories or acceptance criteria.]

## Tech Stack
[Framework, language, key dependencies with versions]

## Commands
[Build, test, lint, dev — full commands]

## Project Structure
[Directory layout with descriptions]

## Code Style
[Example snippet + key conventions]

## Testing Strategy
[Framework, test locations, coverage requirements, test levels]

## Boundaries
- Always: [...]
- Ask first: [...]
- Never: [...]

## Success Criteria
[How we'll know this is done — specific, testable conditions]

## Open Questions
[Anything unresolved that needs human input]
```

**Reframe instructions as success criteria.** When receiving vague requirements, translate them into concrete conditions:

```
REQUIREMENT: "Make the dashboard faster"

REFRAMED SUCCESS CRITERIA:
- Dashboard LCP < 2.5s on 4G connection
- Initial data load completes in < 500ms
- No layout shift during load (CLS < 0.1)
→ Are these the right targets?
```

This lets you loop, retry, and problem-solve toward a clear goal rather than guessing what "faster" means.

### Phase 2: Plan

With the validated spec, generate a technical implementation plan:

1. Identify the major components and their dependencies
2. Determine the implementation order (what must be built first)
3. Note risks and mitigation strategies
4. Identify what can be built in parallel vs. what must be sequential
5. Define verification checkpoints between phases

The plan should be reviewable: the human should be able to read it and say "yes, that's the right approach" or "no, change X."

### Phase 3: Tasks

Break the plan into discrete, implementable tasks:

- Each task should be completable in a single focused session
- Each task has explicit acceptance criteria
- Each task includes a verification step (test, build, manual check)
- Tasks are ordered by dependency, not by perceived importance
- No task should require changing more than ~5 files

**Task template:**
```markdown
- [ ] Task: [Description]
  - Acceptance: [What must be true when done]
  - Verify: [How to confirm — test command, build, manual check]
  - Files: [Which files will be touched]
```

### Phase 4: Implement

Execute tasks one at a time. Use `skills_tool` with `action: load, skill_name: "incremental-implementation"` for the implementation workflow and `skills_tool` with `action: load, skill_name: "test-driven-development"` for testing. Use `skills_tool` with `action: load, skill_name: "context-engineering"` to load the right spec sections and source files at each step rather than flooding context with the entire spec.

## A0-Native Concepts

### Using `call_subordinate` for Spec Validation

For large specs, delegate validation of individual sections to subordinate agents:

```
Main agent: Use call_subordinate with profile: "developer" to validate
the spec's technical feasibility:
  1. Are the commands correct for the stated tech stack?
  2. Is the project structure consistent with the framework?
  3. Are the testing strategy and coverage targets realistic?
  4. Are there any missing sections from the six core areas?

Subordinate: Validates spec sections, reports gaps and issues.

Main agent: Incorporates feedback, updates spec via text_editor.
```

### Using `parallel` for Multi-Component Specs

When a spec covers multiple independent components, use `parallel` to draft sections concurrently:

```json
{
  "tool_name": "parallel",
  "tool_args": {
    "tool_calls": [
      {"tool_name": "call_subordinate", "tool_args": {"message": "Draft the Commands and Project Structure sections for a React/Node.js monorepo spec.", "profile": "developer", "reset": true}},
      {"tool_name": "call_subordinate", "tool_args": {"message": "Draft the Testing Strategy section for a React/Node.js monorepo with Jest and Playwright.", "profile": "test-engineer", "reset": true}}
    ],
    "wait": true
  }
}
```

The main agent consolidates the outputs into a single spec document.

### Persisting with `text_editor`

Always save the spec using `text_editor` with `action: write` to `tasks/spec.md`. This ensures the spec is part of the project and can be referenced during implementation.

## Keeping the Spec Alive

The spec is a living document, not a one-time artifact:

- **Update when decisions change** — If you discover the data model needs to change, update the spec first, then implement.
- **Update when scope changes** — Features added or cut should be reflected in the spec.
- **Commit the spec** — The spec belongs in version control alongside the code.
- **Reference the spec in PRs** — Link back to the spec section that each PR implements.

## Persisting the Spec

When the spec is complete and approved, persist it using `text_editor` with `action: write` to save it as `tasks/spec.md` in the project. Deliver the spec to the user via the `response` tool.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is simple, I don't need a spec" | Simple tasks don't need *long* specs, but they still need acceptance criteria. A two-line spec is fine. |
| "I'll write the spec after I code it" | That's documentation, not specification. The spec's value is in forcing clarity *before* code. |
| "The spec will slow us down" | A 15-minute spec prevents hours of rework. Waterfall in 15 minutes beats debugging in 15 hours. |
| "Requirements will change anyway" | That's why the spec is a living document. An outdated spec is still better than no spec. |
| "The user knows what they want" | Even clear requests have implicit assumptions. The spec surfaces those assumptions. |

## Parallel Work and Delegation

Spec creation and validation involve distinct workstreams that benefit from delegation:

- Use `parallel` to draft independent spec sections (Commands, Project Structure, Testing Strategy) concurrently — see the detailed patterns in [A0-Native Concepts](#a0-native-concepts) above
- Use `call_subordinate` with `profile: "developer"` for spec feasibility validation, `profile: "test-engineer"` for testing-strategy review, and `profile: "security-auditor"` for security boundary review
- The main agent keeps spec authority centralized — it owns the assumption list, conflict resolution, spec persistence, and human-review gate, not the subordinates

## Red Flags

- Starting to write code without any written requirements
- Asking "should I just start building?" before clarifying what "done" means
- Implementing features not mentioned in any spec or task list
- Making architectural decisions without documenting them
- Skipping the spec because "it's obvious what to build"

## Verification

Before proceeding to implementation, confirm:

- [ ] The spec covers all six core areas
- [ ] The human has reviewed and approved the spec
- [ ] Success criteria are specific and testable
- [ ] Boundaries (Always/Ask First/Never) are defined
- [ ] The spec is saved as `tasks/spec.md` in the repository using `text_editor` with `action: write`

## Files

(use `skills_tool` action `read_file` to open)

- `SKILL.md` — This skill file
- `evals/evals.json` — Behavioral evaluations
