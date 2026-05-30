---
name: documentation-and-adrs
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Writes technical documentation and Architecture Decision Records. Use when
  creating READMEs, API docs, ADRs, or any documentation that needs to explain
  a system, a decision, or how to use something.
tags:
  - documentation
  - adr
  - readme
  - technical-writing
  - architecture
trigger_patterns:
  - documentation-and-adrs
  - write documentation
  - update the readme
  - architecture decision record
  - write an adr
  - document this decision
  - api documentation
  - technical docs
  - why did we choose
  - document the architecture
  - update readme
  - write the readme
  - readme for this
  - module documentation
  - update docs
  - improve documentation
  - document this module
  - add documentation
  - document the api
---

# Documentation and ADRs

## Overview

Document decisions, not just code. The most valuable documentation captures the *why* — the context, constraints, and trade-offs that led to a decision. Code shows *what* was built; documentation explains *why it was built this way* and *what alternatives were considered*. This context is essential for future humans and agents working in the codebase.

## When to Use

- Making a significant architectural decision
- Choosing between competing approaches
- Adding or changing a public API
- Shipping a feature that changes user-facing behavior
- Onboarding new team members (or agents) to the project
- When you find yourself explaining the same thing repeatedly

**When NOT to use:** Don't document obvious code. Don't add comments that restate what the code already says. Don't write docs for throwaway prototypes.

## Architecture Decision Records (ADRs)

ADRs capture the reasoning behind significant technical decisions. They're the highest-value documentation you can write.

### When to Write an ADR

- Choosing a framework, library, or major dependency
- Designing a data model or database schema
- Selecting an authentication strategy
- Deciding on an API architecture (REST vs. GraphQL vs. tRPC)
- Choosing between build tools, hosting platforms, or infrastructure
- Any decision that would be expensive to reverse

### ADR Template

Store ADRs in `docs/decisions/` (or `docs/adrs/`) with sequential numbering:

```markdown
# ADR-[number]: [Short title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-[X]

## Context

What situation led to this decision? What problem are we solving?
Include relevant constraints, requirements, and background.

## Decision

What did we decide? State it clearly and directly.

## Alternatives Considered

### Option A: [Name]
- **Pros**: ...
- **Cons**: ...

### Option B: [Name]
- **Pros**: ...
- **Cons**: ...

### Option C: [Name] ← Chosen
- **Pros**: ...
- **Cons**: ...

## Rationale

Why did we choose Option C? What factors were decisive?
What are the trade-offs we're accepting?

## Consequences

What becomes easier as a result? What becomes harder?
Are there follow-up decisions or actions needed?
```

### ADR Example

```markdown
# ADR-001: Use PostgreSQL for primary database

## Status
Accepted

## Date
2025-01-15

## Context
We need a primary database for the task management application. Key requirements:
- Relational data model (users, tasks, teams with relationships)
- ACID transactions for task state changes
- Support for full-text search on task content
- Managed hosting available (for small team, limited ops capacity)

## Decision
Use PostgreSQL with Prisma ORM.

## Alternatives Considered

### MongoDB
- Pros: Flexible schema, easy to start with
- Cons: Our data is inherently relational; would need to manage relationships manually
- Rejected: Relational data in a document store leads to complex joins or data duplication

### SQLite
- Pros: Zero configuration, embedded, fast for reads
- Cons: Limited concurrent write support, no managed hosting for production
- Rejected: Not suitable for multi-user web application in production

### MySQL
- Pros: Mature, widely supported
- Cons: PostgreSQL has better JSON support, full-text search, and ecosystem tooling
- Rejected: PostgreSQL is the better fit for our feature requirements

## Consequences
- Prisma provides type-safe database access and migration management
- We can use PostgreSQL's full-text search instead of adding Elasticsearch
- Team needs PostgreSQL knowledge (standard skill, low risk)
- Hosting on managed service (Supabase, Neon, or RDS)
```

### ADR Lifecycle

```
PROPOSED → ACCEPTED → (SUPERSEDED or DEPRECATED)
```

- **Don't delete old ADRs.** They capture historical context.
- When a decision changes, write a new ADR that references and supersedes the old one.

### ADR File Organization

```
docs/
  adrs/
    001-database-orm.md
    002-authentication-strategy.md
    003-testing-framework.md
    004-state-management.md
    README.md  # Index of all ADRs with one-line summaries
```

ADR index (`docs/adrs/README.md`):

```markdown
# Architecture Decision Records

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [001](./001-database-orm.md) | Use Prisma as the ORM | Accepted | 2025-03-15 |
| [002](./002-authentication.md) | JWT session authentication | Accepted | 2025-03-16 |
| [003](./003-testing.md) | Vitest + Testing Library | Accepted | 2025-03-17 |
```

## Inline Documentation

### When to Comment

Comment the *why*, not the *what*:

```typescript
// BAD: Restates the code
// Increment counter by 1
counter += 1;

// GOOD: Explains non-obvious intent
// Rate limit uses a sliding window — reset counter at window boundary,
// not on a fixed schedule, to prevent burst attacks at window edges
if (now - windowStart > WINDOW_SIZE_MS) {
  counter = 0;
  windowStart = now;
}
```

### When NOT to Comment

```typescript
// Don't comment self-explanatory code
function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// Don't leave TODO comments for things you should just do now
// TODO: add error handling  ← Just add it

// Don't leave commented-out code
// const oldImplementation = () => { ... }  ← Delete it, git has history
```

### Document Known Gotchas

```typescript
/**
 * IMPORTANT: This function must be called before the first render.
 * If called after hydration, it causes a flash of unstyled content
 * because the theme context isn't available during SSR.
 *
 * See ADR-003 for the full design rationale.
 */
export function initializeTheme(theme: Theme): void {
  // ...
}
```

### JSDoc for Public APIs

```typescript
/**
 * Creates a task and sends a notification to the assignee.
 *
 * @param input - Task creation data
 * @returns The created task with server-generated fields
 * @throws {ValidationError} If input is invalid
 * @throws {NotFoundError} If assignee doesn't exist
 *
 * @example
 * const task = await createTask({ title: 'Buy groceries' });
 * console.log(task.id); // "task_abc123"
 */
export async function createTask(input: CreateTaskInput): Promise<Task> { ... }
```

## API Documentation

For public APIs (REST, GraphQL, library interfaces):

### OpenAPI / Swagger for REST APIs

```yaml
paths:
  /api/tasks:
    post:
      summary: Create a task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTaskInput'
      responses:
        '201':
          description: Task created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
        '422':
          description: Validation error
```

### API Documentation with Examples

```markdown
## POST /api/tasks

Create a new task.

**Authentication**: Required (Bearer token)

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Task title (1–200 chars) |
| `description` | string | No | Task description (max 2000 chars) |
| `priority` | `low` \| `medium` \| `high` | No | Default: `medium` |

**Request Example**

```json
{
  "title": "Review API documentation",
  "priority": "high"
}
```

**Response: 201 Created**

```json
{
  "id": "task_abc123",
  "title": "Review API documentation",
  "priority": "high",
  "status": "pending",
  "createdAt": "2025-03-15T10:00:00.000Z"
}
```

**Error Responses**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `BAD_REQUEST` | Malformed JSON |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 422 | `VALIDATION_ERROR` | Invalid field values |
```

## README Structure

Every project MUST have a README that covers:

```markdown
# Project Name

One sentence: what this is and who it's for.

## Quick Start

1. Clone the repo
2. Install dependencies: `npm install`
3. Set up environment: `cp .env.example .env`
4. Run the dev server: `npm run dev`

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm test` | Run tests |
| `npm run build` | Production build |
| `npm run lint` | Run linter |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SESSION_SECRET` | Yes | Random secret for session encryption |

Copy `.env.example` to `.env` and fill in the values.

## Project Structure

src/
  api/        # API route handlers
  components/ # React components
  lib/        # Shared utilities
  types/      # TypeScript type definitions

## Architecture

Brief overview of the project structure and key design decisions.
Link to ADRs for details.

## Contributing

How to contribute, coding standards, PR process.
```

## Changelog Maintenance

For shipped features:

```markdown
# Changelog

## [1.2.0] - 2025-01-20
### Added
- Task sharing: users can share tasks with team members (#123)
- Email notifications for task assignments (#124)

### Fixed
- Duplicate tasks appearing when rapidly clicking create button (#125)

### Changed
- Task list now loads 50 items per page (was 20) for better UX (#126)
```

## Documentation for Agents

Special consideration for AI agent context:

- **CLAUDE.md / rules files** — Document project conventions so agents follow them
- **Spec files** — Keep specs updated so agents build the right thing
- **ADRs** — Help agents understand why past decisions were made (prevents re-deciding)
- **Inline gotchas** — Prevent agents from falling into known traps
- **Agent Zero promptinclude files** — Use `*.promptinclude.md` files in workdir for persistent project context injected into system prompt

## Documentation Quality Standards

```
Good documentation:
✓ Answers the question a reader actually has
✓ Has working code examples (tested, not hypothetical)
✓ Is updated when the code changes
✓ Explains WHY decisions were made, not just WHAT was built
✓ Is written for the reader's knowledge level, not the author's

Bad documentation:
✗ Describes what the code does (the code does that)
✗ Has examples that don't run
✗ Is never updated
✗ Only records what was built, not why
✗ Is written to demonstrate expertise rather than enable understanding
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code is self-documenting" | Code shows what. It doesn't show why, what alternatives were rejected, or what constraints apply. |
| "We'll write docs when the API stabilizes" | APIs stabilize faster when you document them. The doc is the first test of the design. |
| "Nobody reads docs" | Agents do. Future engineers do. Your 3-months-later self does. |
| "ADRs are overhead" | A 10-minute ADR prevents a 2-hour debate about the same decision six months later. |
| "Comments get outdated" | Comments on *why* are stable. Comments on *what* get outdated — that's why you only write the former. |

## Red Flags

- Architectural decisions with no written rationale
- Public APIs with no documentation or types
- README that doesn't explain how to run the project
- Commented-out code instead of deletion
- TODO comments that have been there for weeks
- No ADRs in a project with significant architectural choices
- Documentation that restates the code instead of explaining intent
- ADRs that only record the decision, not the alternatives considered
- API documentation without request/response examples

## Verification

After documenting:

- [ ] ADRs exist for all significant architectural decisions
- [ ] ADR records: context, decision, alternatives considered, rationale, and consequences
- [ ] README covers quick start, commands, and architecture overview
- [ ] README setup instructions work on a clean machine
- [ ] API functions have parameter and return type documentation
- [ ] Code examples in docs are syntactically correct and runnable
- [ ] Known gotchas are documented inline where they matter
- [ ] No commented-out code remains
- [ ] Rules files (CLAUDE.md, promptinclude files, etc.) are current and accurate
- [ ] Documentation is committed in the same PR as the code it documents
