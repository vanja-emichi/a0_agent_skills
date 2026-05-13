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

Write documentation that serves the reader, not the author. Good documentation answers the question the reader has at the moment they have it — not the question you wanted to answer. This skill covers README files, API documentation, Architecture Decision Records (ADRs), and inline documentation.

## When to Use

- Creating or updating a project README
- Documenting an API (endpoints, request/response shapes)
- Recording a significant architectural or technical decision
- Explaining a non-obvious implementation choice
- Setting up a new developer's onboarding experience

## Documentation Types

### 1. README

The README is the front door of your project. It answers three questions:

1. **What is this?** — One sentence description
2. **How do I start?** — Working setup instructions
3. **How do I use it?** — Common commands and patterns

```markdown
# Project Name

One sentence: what this is and who it's for.

## Quick Start

\`\`\`bash
npm install
npm run dev
# → App running at http://localhost:3000
\`\`\`

## Development

\`\`\`bash
npm test          # Run tests
npm run build     # Production build
npm run lint      # Check code style
npm run type-check  # TypeScript validation
\`\`\`

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SESSION_SECRET` | Yes | Random secret for session encryption |
| `STRIPE_API_KEY` | No | Stripe key (payment features only) |

Copy `.env.example` to `.env` and fill in the values.

## Project Structure

\`\`\`
src/
  api/        # API route handlers
  components/ # React components
  lib/        # Shared utilities
  types/      # TypeScript type definitions
\`\`\`

## Key Decisions

- **Database**: Prisma + PostgreSQL — see [ADR-001](./docs/adrs/001-database.md)
- **Authentication**: JWT sessions — see [ADR-002](./docs/adrs/002-auth.md)
- **Testing**: Vitest + Testing Library — see [ADR-003](./docs/adrs/003-testing.md)

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
```

### 2. Architecture Decision Records (ADRs)

ADRs are lightweight documents that record significant technical decisions. Write one whenever you make a choice that:
- Affects the overall system architecture
- Has meaningful alternatives you considered
- Will be hard to reverse later
- Future team members might question ("why did we do it this way?")

**When NOT to write an ADR:** Routine implementation choices, minor tech selections, things that are easy to change.

#### ADR Template

```markdown
# ADR-[number]: [Short title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-[X]
**Author**: [Name]

## Context

What situation led to this decision? What problem are we solving?
Include relevant constraints, requirements, and background.

## Decision

What did we decide? State it clearly and directly.

## Options Considered

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

## References

- [Link to relevant docs, issues, or discussions]
```

#### ADR Example

```markdown
# ADR-001: Use Prisma as the ORM

**Date**: 2025-03-15
**Status**: Accepted
**Author**: Engineering Team

## Context

We need a database access layer for our PostgreSQL database. We need:
- Type-safe queries
- Schema migrations
- Good TypeScript integration
- Active maintenance and documentation

## Decision

We will use Prisma as our ORM.

## Options Considered

### Option A: Raw SQL with `pg`
- **Pros**: Maximum flexibility, no abstraction layer
- **Cons**: No type safety, manual migration management, verbose

### Option B: TypeORM
- **Pros**: Mature, decorator-based schema definition
- **Cons**: Complex configuration, known TypeScript compatibility issues

### Option C: Prisma ← Chosen
- **Pros**: Excellent TypeScript integration, generated types, good migration tooling, clear docs
- **Cons**: Prisma Client can be opinionated, complex queries require raw SQL

## Rationale

Type safety is a priority for this project. Prisma's auto-generated TypeScript
client eliminates a whole class of bugs. The migration tooling is simpler than
TypeORM's and the documentation is comprehensive.

## Consequences

- Simpler: Schema is the single source of truth for types
- Harder: Complex queries (aggregations, CTEs) require raw SQL via `prisma.$queryRaw`
- Follow-up: Document the raw SQL escape hatch for complex queries
```

### 3. API Documentation

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
| `dueDate` | ISO 8601 datetime | No | When the task is due |

**Request Example**

```json
{
  "title": "Review API documentation",
  "priority": "high",
  "dueDate": "2025-03-20T17:00:00Z"
}
```

**Response: 201 Created**

```json
{
  "id": "task_abc123",
  "title": "Review API documentation",
  "priority": "high",
  "dueDate": "2025-03-20T17:00:00.000Z",
  "status": "pending",
  "createdAt": "2025-03-15T10:00:00.000Z",
  "createdBy": "user_xyz"
}
```

**Error Responses**

| Status | Code | Description |
|--------|------|-------------|
| 400 | `BAD_REQUEST` | Malformed JSON |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 422 | `VALIDATION_ERROR` | Invalid field values |
```

### 4. Inline Documentation

Rule: Document **why**, not **what**. The code explains what. Comments explain why.

```typescript
// BAD: Documents what (obvious from code)
// Increment the counter
count++;

// BAD: Restates the function signature
// Gets a user by ID
async function getUser(id: string): Promise<User> { ... }

// GOOD: Explains a non-obvious constraint
// Use bcrypt with 12 rounds minimum. Lower rounds are measurably
// vulnerable to GPU-accelerated cracking at current hardware prices.
const SALT_ROUNDS = 12;

// GOOD: Explains a workaround
// Prisma doesn't support lateral joins, so we fetch tasks separately
// and join in application code. See: https://github.com/prisma/prisma/issues/...
const users = await prisma.user.findMany(...);
const tasks = await prisma.task.findMany({ where: { userId: { in: userIds } } });

// GOOD: JSDoc for public APIs
/**
 * Creates a task and sends a notification to the assignee.
 *
 * @param input - Task creation data
 * @returns The created task with server-generated fields
 * @throws {ValidationError} If input is invalid
 * @throws {NotFoundError} If assignee doesn't exist
 */
export async function createTask(input: CreateTaskInput): Promise<Task> { ... }
```

## ADR File Organization

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
| "The code is self-documenting" | Code explains what. Documentation explains why, how to start, and what the trade-offs are. |
| "We'll write docs at the end" | Docs written at the end are incomplete. The context is freshest when the decision is made. |
| "ADRs take too long" | A 15-minute ADR saves hours of re-litigating the same decision in future meetings. |
| "No one reads the README" | People read READMEs that answer their questions. Write for the reader. |
| "The API is obvious" | It's obvious to you now. Document it for your future self and your teammates. |

## Red Flags

- README that doesn't have working setup instructions
- ADRs that only record the decision, not the alternatives considered
- API documentation without request/response examples
- Comments that explain what the code does instead of why
- Documentation that's months out of date with the implementation
- No ADRs for major architectural choices

## Verification

After writing documentation:

- [ ] README setup instructions work on a clean machine (test via `code_execution_tool`)
- [ ] Code examples in docs are syntactically correct and runnable
- [ ] ADR records: context, decision, alternatives considered, rationale, and consequences
- [ ] API docs include request body, response shape, and error cases
- [ ] Inline comments explain why, not what
- [ ] Documentation is committed in the same PR as the code it documents
